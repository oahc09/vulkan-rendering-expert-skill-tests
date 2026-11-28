"""Exact candidate identity/packaging only; never a final capability acceptance seal."""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAIRS = {
    "historical-v1.0.19": "coverage/v1.0.19/pair.json",
    "postmerge16-v1.0.20": "coverage/v1.0.20/postmerge-pair.json",
    "current-v1.0.20": "coverage/v1.0.20/current-pair.json",
    "current-v1.0.21": "coverage/v1.0.21/current-pair.json",
}
CANDIDATE_PAIRS = {"current-v1.0.20", "current-v1.0.21"}
V21 = "current-v1.0.21"
G0_SKILL = "acd49f98d1243d8ebac6e8194848194d47e470a5"
G0_TESTS = "80a4f650ceebf182f9f83739e4cd76d1788b79fe"
FROZEN_PLAN = "b28086a1c1b5d390ad5826c10740fbced15a7e5d3efb5628922147d0a6fa955b"
FROZEN_TASKS = "9d908797e07a77910e778f1ab8e513e949a0fcf4de83b3f12302946561506c55"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(path, *args):
    return subprocess.check_output(["git", *args], cwd=path, text=True).strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_pair(pair):
    path = ROOT / PAIRS[pair]
    require(path.is_file(), f"exact manifest for {pair} has not been frozen")
    config = json.loads(path.read_text(encoding="utf-8"))
    validate_pair(pair, config)
    return config


def hex_pin(value, size):
    return isinstance(value, str) and re.fullmatch(rf"[0-9a-f]{{{size}}}", value) is not None


def validate_pair(pair, config):
    require(hex_pin(config["skill_sha"], 40), "Skill pin must be a full commit SHA")
    if pair in CANDIDATE_PAIRS:
        require(hex_pin(config["package_manifest_sha256"], 64),
                "package manifest pin must be a SHA-256")
        require(type(config["package_file_limit"]) is int and type(config["package_files"]) is int
                and 0 < config["package_files"] <= config["package_file_limit"],
                "invalid exact package size or budget")
    if pair == V21:
        require(config["skill_version"] == "1.0.21" and config["package_file_limit"] == 200,
                "v1.0.21 requires its own version and 200-file budget")
        require(hex_pin(config["skill_tree"], 40) and hex_pin(config["tests_baseline"], 40),
                "expected exact Skill tree and Tests base pins")
        require(config["plan_sha256"] == FROZEN_PLAN and config["task_registry_sha256"] == FROZEN_TASKS,
                "v1.0.21 must retain the frozen inherited plan and task registry")
    require(config["release_status"] == "BLOCKED", "pair is not a release seal")


def clean_revision(repo, name):
    require(not git(repo, "status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none"),
            f"{name} worktree is not clean")
    return git(repo, "rev-parse", "HEAD"), git(repo, "rev-parse", "HEAD^{tree}")


def ancestor(repo, base, head):
    return subprocess.run(["git", "merge-base", "--is-ancestor", base, head],
                          cwd=repo, check=False).returncode == 0


def verify(skill, pair, config, *, emit=True):
    actual = git(skill, "rev-parse", "HEAD")
    require(actual == config["skill_sha"], f"Skill SHA mismatch: expected {config['skill_sha']}, got {actual}")
    require(sha256(ROOT / "docs/v1.0.19-original-plan.md") == config["plan_sha256"], "inherited plan hash mismatch")
    version = "1.0.19" if pair == "historical-v1.0.19" else config["skill_version"]
    skill_doc = (skill / "SKILL.md").read_text(encoding="utf-8")
    if pair == V21:
        frontmatter = re.match(r"\A---\n(?P<yaml>[\s\S]*?)\n---\n", skill_doc)
        require(frontmatter is not None, "Skill is missing candidate frontmatter")
        skill_doc = frontmatter["yaml"] + "\n"
    require(f"  version: {version}\n" in skill_doc and "  release-status: candidate-blocked\n" in skill_doc,
            "Skill version or candidate status mismatch")
    if pair != "historical-v1.0.19":
        require(not git(skill, "status", "--porcelain", "--untracked-files=all"), "Skill worktree is not clean")
        require(not git(ROOT, "status", "--porcelain", "--untracked-files=all"), "Tests worktree is not clean")
        require(git(skill, "rev-parse", "HEAD^{tree}") == config["skill_tree"], "Skill tree mismatch")
        require(sha256(ROOT / "coverage/v1.0.19/tasks.json") == config["task_registry_sha256"], "inherited task registry hash mismatch")
        tests_head = git(ROOT, "rev-parse", "HEAD")
        require(ancestor(ROOT, config["tests_baseline"], tests_head), "Tests HEAD does not descend from reviewed base")
        if pair == V21:
            clean_revision(skill, "Skill")
            clean_revision(ROOT, "Tests")
            require(ancestor(ROOT, G0_TESTS, config["tests_baseline"]) and ancestor(skill, G0_SKILL, actual),
                    "candidate pair does not descend from both reviewed G0 bases")
        if emit:
            print(f"Tests checkout {tests_head}; Skill checkout {actual}")
    if emit:
        print("PASS exact candidate identity; final acceptance remains BLOCKED")

def prepare_v21(skill):
    """Produce a reviewable pin from clean committed inputs and the official audit."""
    skill_before = clean_revision(skill, "Skill")
    tests_before = clean_revision(ROOT, "Tests")
    require(ancestor(ROOT, G0_TESTS, tests_before[0]) and ancestor(skill, G0_SKILL, skill_before[0]),
            "candidate pair does not descend from both reviewed G0 bases")
    output = subprocess.run([sys.executable, str(skill / "scripts/agensi_audit_and_pack.py"), str(skill)],
                            cwd=skill, capture_output=True, encoding="utf-8", check=True)
    audit = json.loads(output.stdout)
    files = audit["files"]
    count = len(files)
    require(audit["status"] == "PASS" and audit["revision"] == skill_before[0]
            and len({row["path"] for row in files}) == count == audit["package_files"],
            "candidate audit or inventory mismatch")
    canonical = json.dumps(sorted(files, key=lambda row: row["path"]),
                           sort_keys=True, separators=(",", ":")).encode()
    config = dict(skill_sha=skill_before[0], skill_tree=skill_before[1], skill_version="1.0.21",
                  tests_baseline=tests_before[0], plan_sha256=FROZEN_PLAN, task_registry_sha256=FROZEN_TASKS,
                  release_status="BLOCKED", package_file_limit=200, package_files=count,
                  package_manifest_sha256=hashlib.sha256(canonical).hexdigest())
    validate_pair(V21, config)
    verify(skill, V21, config, emit=False)
    require(clean_revision(skill, "Skill") == skill_before and clean_revision(ROOT, "Tests") == tests_before,
            "candidate identity changed during audit")
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=pathlib.Path)
    parser.add_argument("--resolve", action="store_true")
    parser.add_argument("--prepare-v21", action="store_true", help="print a clean candidate pin for review")
    parser.add_argument("--pair", choices=PAIRS, default="historical-v1.0.19")
    args = parser.parse_args()
    if args.prepare_v21:
        if args.resolve or not args.skill or args.pair != V21:
            parser.error("--prepare-v21 requires --skill and --pair current-v1.0.21")
        try:
            print(json.dumps(prepare_v21(args.skill.resolve()), indent=2))
        except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
            parser.exit(1, f"Pair preparation failed: {error}\n")
        return
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
