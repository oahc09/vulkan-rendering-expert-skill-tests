"""Offline evidence infrastructure; does not certify the R3 gates."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECKS = ROOT / "checks19"
sys.path.insert(0, str(CHECKS))
from run_current_receipt import junit_counts, package_identity  # noqa: E402
sys.path.pop(0)


def ids(prefix, size):
    return {f"{prefix}-{i:02d}" for i in range(1, size + 1)}


def test_r3_index_maps_scope_without_marking_original_tasks_complete():
    index = json.loads((ROOT / "coverage/v1.0.20/r3-execution-index.json").read_text())
    assert index["schema"] == 2
    assert index["scope"] == "R3_EXECUTION_INDEX_NOT_ACCEPTANCE"
    assert index["plan"]["sha256"] == "3c321d8b577afae6ee7edfdbe29e76a98dc85863e7b5b735e1f05c48947938c3"
    assert index["plan"]["implementation_prompt_sha256"] == "9c91255a3543bd657bbace38c7bb1dcf7be149801ebdbdc366c84facbb2ec259"
    registry = (ROOT / index["inherited"]["path"]).read_bytes()
    assert hashlib.sha256(registry).hexdigest() == index["inherited"]["sha256"]
    tasks = {row["id"]: row for row in json.loads(registry)}
    assert set(tasks) == ids("ALL19", 24) | ids("E2E19", 12)
    assert {row["status"] for row in tasks.values()} == {"UNVERIFIED"}
    for key, prefix, size in [("main", "V20", 28), ("content", "CONTENT20", 14), ("combo", "COMBO20", 8)]:
        assert len(index[key]) == size
        assert {row[0] for row in index[key]} == ids(prefix, size)
    for _, title, path, gate in index["main"]:
        assert title and gate and (ROOT / path).is_file()
    for _, title, refs, gate in index["content"]:
        assert title and refs and gate and set(refs) <= ids("V20", 28)
    for _, title, refs, gate in index["combo"]:
        assert title and refs and gate and set(refs) <= tasks.keys()
    assert len(set(row[0] for row in index["engines"])) == len(index["engines"]) == 6
    planned = {
        "UE Mobile 5.7": {4},
        "UE RDG 5.7": {4, 8},
        "UE GPUScene / Unity BRG and GPU Resident Drawer": {2, 3, 8},
        "Godot 4.5 rendering methods": {4, 7},
        "Filament async loader and pacing": {1, 7, 8},
        "Cocos Creator 3.8 Native batching": {5, 7},
    }
    assert {row[0] for row in index["engines"]} == set(planned)
    for title, refs, combos, gate in index["engines"]:
        assert title and gate and refs and set(refs) <= ids("CONTENT20", 14)
        assert len(combos) == len(set(combos))
        assert set(combos) == {f"COMBO20-{n:02d}" for n in planned[title]}
    assert len(set(row[0] for row in index["gpus"])) == len(index["gpus"]) == 9
    assert [row[0] for row in index["experiments"]] == list("ABCD")
    for _, refs, navigation, gate in index["experiments"]:
        assert gate and refs and set(refs) <= ids("COMBO20", 8)
        assert set(navigation) == {"primary", "supporting"} and navigation["primary"]
        paths = navigation["primary"] + navigation["supporting"]
        assert len(paths) == len(set(paths)) and all((ROOT / path).is_file() for path in paths)
    lab_b = next(row[2] for row in index["experiments"] if row[0] == "B")
    assert {Path(path).parent.name for path in lab_b["primary"]} == {
        "transparent_scene_lab", "text_temporal_hdr_lab", "scene_c_service_lab",
    }
    assert [Path(path).parent.name for path in lab_b["supporting"]] == ["hybrid_quality_lab"]


def test_junit_preserves_skips_and_rejects_empty_reports(tmp_path):
    xml = tmp_path / "results.xml"
    xml.write_text('<testsuites><testsuite tests="2" skipped="1"><testcase name="pass"/>'
                   '<testcase name="skip"><skipped message="device absent"/></testcase></testsuite></testsuites>')
    assert junit_counts(xml) == {"tests": 2, "passed": 1, "skipped": 1, "failures": 0, "errors": 0}
    xml.write_text('<testsuite tests="0"/>')
    with pytest.raises(ValueError, match="missing/inconsistent"):
        junit_counts(xml)


def test_package_identity_rejects_manifest_drift(tmp_path):
    path = tmp_path / "package.json"
    (tmp_path / "candidate.zip").write_bytes(b"hash binding only")
    files = [{"path": "SKILL.md", "sha256": "1" * 64}]
    pair = {"skill_sha": "a" * 40, "package_files": 1, "package_manifest_sha256": hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
    report = {"status": "PASS", "revision": pair["skill_sha"], "package_files": 1, "files": files,
              "zip": {"crc_verified": True}}
    path.write_text(json.dumps(report))
    assert package_identity(path, tmp_path, pair)["files"] == 1
    files[0]["sha256"] = "2" * 64
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="does not match"):
        package_identity(path, tmp_path, pair)
