"""Host associations with fixed counterexamples. These are synthetic exports."""
import hashlib
import json

import pytest

from tools.delivery19 import correlate_engine_export
from tools.evidence19 import legacy_probe_summary


def fixture():
    project_sha = "1" * 40
    stages = ("record", "submit", "complete", "present_request", "display_feedback", "cpu_span")
    sources = {
        stage: {"role": stage, "path": "renderer.cpp", "symbol": stage,
                "line": i + 3, "file_sha256": "2" * 64}
        for i, stage in enumerate(stages)
    }
    profile = json.dumps({
        "schema": 1, "scope": "SOURCE_BINDINGS_ONLY", "project": "host-oracle",
        "checkout": {"sha": project_sha},
        "bindings": [
            {"binding": {"role": stage, "path": source["path"], "symbol": source["symbol"]},
             "state": "OBSERVED", "disposition": "REUSED",
             "file_sha256": source["file_sha256"], "lines": [source["line"]]}
            for stage, source in sources.items()
        ],
    }).encode()
    events = []
    for i, stage in enumerate(stages, 1):
        events.append(dict(
            stage=stage, seq=i, event_id=stage, run_id="run", device_scope="device",
            engine_id="engine", output_id="output", object_type="image", object_id="image-1",
            generation=7, frame_id="frame", submission_id="submit-a", source=sources[stage],
            result="accepted" if stage in ("submit", "present_request") else "observed",
        ))
    events[1]["predecessor"] = "record"
    events[2]["predecessor"] = "submit"
    # The queue can accept a present request before completion is observed.
    events[3]["predecessor"] = "submit"
    events[4].update(predecessor="present_request", observation="display_feedback")
    return {"schema": "engine-events-v21", "project": "host-oracle", "project_sha": project_sha,
            "source_profile_sha256": hashlib.sha256(profile).hexdigest(), "events": events}, profile


def test_scoped_chain_keeps_observation_distinct_from_causality():
    document, profile = fixture()
    raw = json.dumps(document).encode()
    report = correlate_engine_export(raw, profile)
    assert report["artifact_sha256"] == hashlib.sha256(raw).hexdigest()
    assert report["root_cause"] == "UNVERIFIED"
    assert all(row["state"] == "ASSOCIATED" for row in report["events"])
    assert report["events"][3]["predecessor"] == "submit"
    assert report["events"][4]["predecessor"] == "present_request"
    assert report["events"][5]["predecessor"] is None


@pytest.mark.parametrize(("field", "value"), [
    ("run_id", "another"), ("device_scope", "another"), ("output_id", "another"),
    ("generation", 8), ("generation", None), ("submission_id", "another"),
    ("seq", 1), ("seq", 9), ("event_id", "record"), ("result", "rejected"),
])
def test_bad_submit_cannot_support_the_rest_of_the_observation_chain(field, value):
    document, profile = fixture()
    document["events"][1][field] = value
    report = correlate_engine_export(json.dumps(document).encode(), profile)
    assert all(row["state"] == "UNKNOWN" for row in report["events"][1:5])
    assert all(row["predecessor"] is None for row in report["events"][1:5])


def test_present_acceptance_cannot_supply_display_feedback_or_unreviewed_source():
    document, profile = fixture()
    del document["events"][4]["observation"]
    assert correlate_engine_export(json.dumps(document).encode(), profile)["events"][4]["state"] == "UNKNOWN"
    document["events"][1]["source"]["line"] += 1
    assert correlate_engine_export(json.dumps(document).encode(), profile)["events"][1]["state"] == "UNKNOWN"
    with pytest.raises(ValueError, match="exact project profile"):
        correlate_engine_export(json.dumps(document).encode(), profile + b"\n")


def test_legacy_present_marker_preserves_unknown_identity(tmp_path):
    path = tmp_path / "probe.log"
    raw = b"PROBE INSTALLED\nDRAW #1 cb=ABCD\nPRESENT\nPRESENT bad suffix\n"
    path.write_bytes(raw)
    summary = legacy_probe_summary(path)
    assert summary["artifact_sha256"] == hashlib.sha256(raw).hexdigest()
    assert summary["markers"]["present_marker"] == {"count": 1, "first_line": 3, "last_line": 3}
    assert summary["unparsed_lines"] == 1
    assert summary["run_id"] is None and not summary["joined_events"]
    assert summary["status"] == "INSUFFICIENT_ASSOCIATION"
