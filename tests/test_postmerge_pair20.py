"""Scope and fail-closed controls for the independent postmerge pair."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "checks19/check_pair.py"
pytestmark = pytest.mark.host_unit


def check(*args, optimized=False):
    return subprocess.run([sys.executable, *(["-O"] if optimized else []), str(CHECK), *args],
                          capture_output=True, text=True, check=False, timeout=5)


def test_resolve_discriminates_history_and_current():
    historical = json.loads((ROOT / "coverage/v1.0.19/pair.json").read_text())
    postmerge16 = json.loads((ROOT / "coverage/v1.0.20/postmerge-pair.json").read_text())
    current = json.loads((ROOT / "coverage/v1.0.20/current-pair.json").read_text())
    assert len({historical["skill_sha"], postmerge16["skill_sha"], current["skill_sha"]}) == 3
    assert postmerge16["skill_sha"] == "77c702cb7810e05e49c0499ab960295374442f8c"
    assert check("--resolve", "--pair", "postmerge16-v1.0.20").stdout.strip() == postmerge16["skill_sha"]
    assert check("--resolve").stdout.strip() == historical["skill_sha"]
    assert check("--resolve", "--pair", "current-v1.0.20").stdout.strip() == current["skill_sha"]
    assert check("--resolve", "--pair", "main").returncode == 2


def test_wrong_checkout_rejected_even_with_python_optimization():
    result = check("--pair", "current-v1.0.20", "--skill", str(ROOT), optimized=True)
    assert result.returncode == 1
    assert "Skill SHA mismatch" in result.stderr
    assert "PASS" not in result.stdout


def test_current_pair_does_not_promote_original_task_acceptance():
    rows = json.loads((ROOT / "coverage/v1.0.19/tasks.json").read_text())
    assert sum(row["id"].startswith("ALL19-") for row in rows) == 24
    assert sum(row["id"].startswith("E2E19-") for row in rows) == 12
    assert all(row["status"] == "UNVERIFIED" for row in rows)
