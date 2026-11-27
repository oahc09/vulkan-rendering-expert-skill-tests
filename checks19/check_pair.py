"""Exact candidate identity/packaging only; never a final capability acceptance seal."""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAIRS = {
    "historical-v1.0.19": "coverage/v1.0.19/pair.json",
    "postmerge16-v1.0.20": "coverage/v1.0.20/postmerge-pair.json",
    "current-v1.0.20": "coverage/v1.0.20/current-pair.json",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(path, *args):
    return subprocess.check_output(["git", *args], cwd=path, text=True).strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_pair(pair):
    config = json.loads((ROOT / PAIRS[pair]).read_text())
    require(bool(re.fullmatch(r"[0-9a-f]{40}", config["skill_sha"])), "Skill pin must be a full commit SHA")
    if pair == "current-v1.0.20":
        require(bool(re.fullmatch(r"[0-9a-f]{64}", config["package_manifest_sha256"])),
                "package manifest pin must be a SHA-256")
        require(type(config["package_files"]) is int and 0 < config["package_files"] <= config["package_file_limit"],
                "invalid exact package size or budget")
    require(config["release_status"] == "BLOCKED", "pair is not a release seal")
    return config


def verify(skill, pair, config):
    actual = git(skill, "rev-parse", "HEAD")
    require(actual == config["skill_sha"], f"Skill SHA mismatch: expected {config['skill_sha']}, got {actual}")
    require(sha256(ROOT / "docs/v1.0.19-original-plan.md") == config["plan_sha256"], "inherited plan hash mismatch")
    version = "1.0.19" if pair == "historical-v1.0.19" else config["skill_version"]
    skill_doc = (skill / "SKILL.md").read_text()
    require(f"  version: {version}\n" in skill_doc and "  release-status: candidate-blocked\n" in skill_doc,
            "Skill version or candidate status mismatch")
    if pair != "historical-v1.0.19":
        require(not git(skill, "status", "--porcelain", "--untracked-files=all"), "Skill worktree is not clean")
        require(not git(ROOT, "status", "--porcelain", "--untracked-files=all"), "Tests worktree is not clean")
        require(git(skill, "rev-parse", "HEAD^{tree}") == config["skill_tree"], "Skill tree mismatch")
        require(sha256(ROOT / "coverage/v1.0.19/tasks.json") == config["task_registry_sha256"], "inherited task registry hash mismatch")
        tests_head = git(ROOT, "rev-parse", "HEAD")
        require(subprocess.run(["git", "merge-base", "--is-ancestor", config["tests_baseline"], tests_head],
                               cwd=ROOT, check=False).returncode == 0, "Tests HEAD does not descend from reviewed base")
        print(f"Tests checkout {tests_head}; Skill checkout {actual}")
    print("PASS exact candidate identity; final acceptance remains BLOCKED")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=pathlib.Path)
    parser.add_argument("--resolve", action="store_true")
    parser.add_argument("--pair", choices=PAIRS, default="historical-v1.0.19")
    args = parser.parse_args()
    if args.resolve == bool(args.skill):
        parser.error("provide either --resolve or --skill")
    try:
        config = load_pair(args.pair)
        if args.resolve:
            print(config["skill_sha"])
        else:
            verify(args.skill.resolve(), args.pair, config)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Pair verification failed: {error}\n")


if __name__ == "__main__":
    main()
