"""Host oracles for cost admission, never production measurements."""
import hashlib
import json

import pytest

from tools.business_cost21 import report
from tools.delivery19 import compare_ab


def write(root, name, body):
    raw = json.dumps(body).encode()
    (root / name).write_bytes(raw)
    return {"path": name, "sha256": hashlib.sha256(raw).hexdigest()}


def fixture(root, repeats=3, slow=False, **override):
    scope = dict(scene="synthetic", seed=3, camera="overview", resolution=[640, 480],
                 device="host-oracle", driver="v1", cache="warm", instrumentation="timer",
                 thermal="stable", power_mode="fixed", quality="pinned",
                 input_sha256="e" * 64)
    paths = {"baseline": "cpu_instancing", "candidate": "gpu_count"}
    renderers = {"baseline": "a" * 64, "candidate": "b" * 64}
    plan = write(root, "plan.json", {
        "schema": "business-cost-plan-v21", "registered_unix_ns": 1000,
        "minimum_seconds": 1, "minimum_frames": 4, "max_delta": {"frame_p95_ms": 2},
        "cases": [{"id": update, "update": update, "boundary": "multiview" if update == "full" else None,
                   "scope": scope, "render_path": paths, "renderer_sha256": renderers}
                  for update in ("static", "sparse", "full")],
    })
    diagnostic = write(root, "diagnostic.json", {
        "mode": "diagnostic", "case": "static", "scope": scope, "plan_sha256": plan["sha256"],
        "renderer_sha256": renderers, "render_path": paths, "contracts": {
            key: "PASS" for key in ("visible_ids", "image", "capacity", "low_capability")
        },
    })
    pairs = []
    for i in range(repeats):
        pair = {}
        for j, arm in enumerate(("baseline", "candidate")):
            start = (i * 2 + j + 1) * 2_000_000_000
            run_id = f"{arm}-{i}"
            run = {
                "run_id": run_id, "mode": "business", "case": "static", "arm": arm,
                "scope": scope, "plan_sha256": plan["sha256"], "renderer_sha256": renderers[arm],
                "render_path": paths[arm], "diagnostic_readback": False, "business_readback": False,
                "elapsed_seconds": 1, "failures": 0, "captured_frame_count": 4,
                "started_unix_ns": start, "ended_unix_ns": start + 1_000_000_000,
                "frame_ms": [3, 5, 7, 9] if arm == "baseline" else [3, 5, 7, 10 if slow else 8],
                "cpu_submit_ms": 1, "gpu_critical_ms": 2, "queue_wait_ms": 4,
            }
            if i == 0 and arm == "candidate":
                run.update(override)
            pair[arm] = write(root, f"{run_id}.json", run)
        pairs.append(pair)
    return {"plan": plan, "cases": {"static": {"diagnostic": diagnostic, "pairs": pairs}}}


def test_three_measured_pairs_and_unmeasured_cases_remain_scoped(tmp_path):
    result = report(tmp_path, fixture(tmp_path), compare_ab)
    static, sparse, full = result["cases"]
    assert static["decision"] == "WITHIN_DECLARED_MEASURED_SCOPE"
    first = static["comparisons"][0]["runs"]["baseline"]
    assert first["frame"] == {"samples": 4, "p50": 5, "p95": 9, "p99": 9}
    assert first["costs"]["gpu_critical_ms"] == 2 and first["costs"]["queue_wait_ms"] == 4
    assert first["presentation"] is None
    assert sparse["decision"] == full["decision"] == "NEEDS_MEASUREMENT"
    assert result["acceptance"] == "UNVERIFIED"


@pytest.mark.parametrize(("options", "decision"), [
    ({"repeats": 2}, "NEEDS_MEASUREMENT"),
    ({"slow": True}, "KEEP_BASELINE"),
    ({"failures": 1}, "KEEP_BASELINE"),
])
def test_insufficient_repeats_slower_or_failed_candidate(tmp_path, options, decision):
    assert report(tmp_path, fixture(tmp_path, **options), compare_ab)["cases"][0]["decision"] == decision


@pytest.mark.parametrize(("options", "reason"), [
    ({"diagnostic_readback": True}, "business scope"),
    ({"captured_frame_count": 5}, "raw samples"),
    ({"started_unix_ns": 2_000_000_000, "ended_unix_ns": 3_000_000_000}, "overlap"),
])
def test_invalid_measurement_does_not_enter_business_ab(tmp_path, options, reason):
    with pytest.raises(ValueError, match=reason):
        report(tmp_path, fixture(tmp_path, **options), compare_ab)
