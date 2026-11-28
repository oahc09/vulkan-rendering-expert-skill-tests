#!/usr/bin/env python3
"""Run the current exact offline pair; save inspectable logs even on failure."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from check_pair import CANDIDATE_PAIRS, ROOT, git, load_pair

PAIR = "current-v1.0.20"
OFFLINE_MODE = "offline-candidate"
OFFLINE_DISABLED_PREFIXES = ("VULKAN_", "VK_")
OFFLINE_DISABLED_KEYS = {"PYTEST_ADDOPTS", "PYTEST_PLUGINS"}
OUTPUTS = {"pair-final.log",
    "pair.log", "skill-static.log", "skill-host.log", "skill-unittest.log",
    "regression.log", "regression.xml", "package.json", "candidate.zip",
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def offline_environment(source):
    removed = sorted(key for key in source
                     if key.upper() in OFFLINE_DISABLED_KEYS
                     or key.upper().startswith(OFFLINE_DISABLED_PREFIXES))
    env = {key: value for key, value in source.items() if key not in removed}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    return env, removed


def checkout_identity(root):
    return {
        "sha": git(root, "rev-parse", "HEAD"),
        "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "clean": not git(root, "status", "--porcelain=v1", "--untracked-files=all",
                         "--ignore-submodules=none"),
    }


def require_unchanged(before, after):
    for repo, initial in before.items():
        current = after[repo]
        if not current["clean"]:
            raise ValueError(f"{repo} checkout is not clean at receipt completion")
        if current != initial:
            raise ValueError(f"{repo} identity changed during candidate run")


def junit_counts(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    counts = {k: sum(int(s.attrib.get(k, "0")) for s in suites)
              for k in ("tests", "errors", "failures", "skipped")}
    cases = root.findall(".//testcase")
    if not suites or not cases or len(cases) != counts["tests"]:
        raise ValueError("JUnit cases or counts are missing/inconsistent")
    counts["passed"] = counts["tests"] - sum(counts[k] for k in ("errors", "failures", "skipped"))
    return counts


def package_identity(path, out, pair):
    report = json.loads(path.read_text())
    files = report["files"]
    by_path = {entry["path"]: entry["sha256"] for entry in files}
    canonical = json.dumps(sorted(files, key=lambda item: item["path"]), sort_keys=True, separators=(",", ":")).encode()
    manifest_hash = hashlib.sha256(canonical).hexdigest()
    if not (report["status"] == "PASS" and report["revision"] == pair["skill_sha"]
            and len(files) == len(by_path) == report["package_files"] == pair["package_files"]
            and manifest_hash == pair["package_manifest_sha256"]
            and report["zip"]["crc_verified"]):
        raise ValueError("Package identity does not match the current pair")
    return {"files": len(files), "manifest_sha256": manifest_hash, "zip_sha256": digest(out / "candidate.zip")}


def run(skill, tests_sha, out, pair=PAIR, mode=OFFLINE_MODE):
    if pair not in CANDIDATE_PAIRS or mode != OFFLINE_MODE:
        raise ValueError("exact offline candidate pair and supported mode required")
    skill = skill.resolve(strict=True)
    out = out.resolve()
    if any(out == root or root in out.parents for root in (ROOT, skill)):
        raise ValueError("Output directory must be outside both checkouts")
    out.mkdir(parents=True, exist_ok=False)
    env, removed = offline_environment(os.environ)
    receipt = {"schema": 2, "scope": "OFFLINE_CANDIDATE_REGRESSION_ONLY", "pair": pair,
               "requested_mode": mode, "effective_mode": OFFLINE_MODE,
               "removed_opt_in_variable_names": removed, "pytest_plugin_autoload": False,
               "status": "FAILED_OR_INCOMPLETE", "release_status": "BLOCKED",
               "live_execution": "NOT_RUN", "physical_device_acceptance": "NOT_RUN",
               "expected_tests_sha": tests_sha, "runner": platform.platform(), "python": platform.python_version(),
               "github_run_id": os.getenv("GITHUB_RUN_ID"), "github_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
               "commands": []}

    def launch(name, argv, cwd):
        start = time.monotonic()
        target = out / name
        with target.open("xb") as handle:
            rc = subprocess.run(argv, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT,
                                check=False).returncode
        receipt["commands"].append({"log": name, "exit": rc, "elapsed_seconds": round(time.monotonic() - start, 3)})
        print(f"{name}: exit {rc}", flush=True)
        if rc:
            raise ValueError(f"{name} failed (exit {rc})")

    try:
        config = load_pair(pair)
        initial = receipt["initial_identity"] = {
            "tests": checkout_identity(ROOT), "skill": checkout_identity(skill),
        }
        for repo, identity in initial.items():
            receipt[f"{repo}_sha"] = identity["sha"]
            receipt[f"{repo}_tree"] = identity["tree"]
            if not identity["clean"]:
                raise ValueError(f"{repo} checkout is not clean at receipt start")
        if receipt["tests_sha"] != tests_sha:
            raise ValueError("Tests SHA does not match requested checkout")
        pair_args = ["--skill", str(skill), "--pair", pair]
        launch("pair.log", [sys.executable, "checks19/check_pair.py", *pair_args], ROOT)
        launch("skill-static.log", ["node", "scripts/check-skill.mjs"], skill)
        launch("skill-host.log", [sys.executable, "scripts/host_contract.py"], skill)
        launch("skill-unittest.log", [sys.executable, "-m", "unittest", "discover", "-s", "scripts"], skill)
        launch("regression.log", [sys.executable, "checks19/run_regression.py", *pair_args,
                                  "--junit", str(out / "regression.xml")], ROOT)
        receipt["junit"] = junit_counts(out / "regression.xml")
        if receipt["junit"]["errors"] or receipt["junit"]["failures"] or not receipt["junit"]["passed"]:
            raise ValueError("Non-green or empty candidate JUnit")
        launch("package.json", [sys.executable, "scripts/agensi_audit_and_pack.py", str(skill),
                                "--out", str(out / "candidate.zip")], skill)
        receipt["package"] = package_identity(out / "package.json", out, config)
        launch("pair-final.log", [sys.executable, "checks19/check_pair.py", *pair_args], ROOT)
        final = receipt["final_identity"] = {
            "tests": checkout_identity(ROOT), "skill": checkout_identity(skill),
        }
        require_unchanged(initial, final)
        receipt["status"] = "PASSED_OFFLINE_CANDIDATE"
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError, ET.ParseError) as exc:
        receipt["error"] = str(exc)
        print(str(exc), file=sys.stderr)
    finally:
        if "initial_identity" in receipt and "final_identity" not in receipt:
            try:
                receipt["final_identity"] = {
                    "tests": checkout_identity(ROOT), "skill": checkout_identity(skill),
                }
            except (OSError, subprocess.CalledProcessError) as exc:
                receipt["final_identity_error"] = str(exc)
        if "junit" not in receipt and (out / "regression.xml").is_file():
            try:
                receipt["junit"] = junit_counts(out / "regression.xml")
            except (ValueError, OSError, ET.ParseError):
                pass
        receipt["sha256"] = {n: digest(out / n) for n in sorted(OUTPUTS) if (out / n).is_file()}
        (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return int(receipt["status"] != "PASSED_OFFLINE_CANDIDATE")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--skill", type=Path, required=True)
    cli.add_argument("--tests-sha", required=True)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--pair", choices=sorted(CANDIDATE_PAIRS), default=PAIR)
    cli.add_argument("--mode", choices=[OFFLINE_MODE], default=OFFLINE_MODE)
    args = cli.parse_args()
    raise SystemExit(run(args.skill, args.tests_sha, args.out, args.pair, args.mode))
