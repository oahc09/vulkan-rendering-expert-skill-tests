"""Exercise the delivery entry point against predeclared scoped changes."""
import hashlib
import json
from pathlib import Path

import pytest

from tools.delivery19 import plan_revalidation

ORACLE = Path(__file__).resolve().parents[1] / "coverage/v1.0.21/change-expectations.json"
CASES = json.loads(ORACLE.read_text(encoding="utf-8"))["cases"]
DEPENDENCIES = {
    "descriptor": ["shader_interface", "shader_compile"],
    "pipeline": ["shader_interface", "attachment", "shader_compile"],
    "visual": ["shader_interface", "attachment"],
    "hot_update": ["shader_interface"],
    "compositing": ["attachment"],
    "lifetime": ["retirement"],
    "pending": ["retirement"],
    "cancel": ["retirement"],
    "surface_recreate": ["retirement"],
    "artifact": ["shader_compile"],
    "cache": ["shader_compile"],
    "target_platform": ["shader_compile"],
    "device_execution": ["driver"],
    "tool_diagnostic": ["validation_layer"],
    "recommendation": ["spec_rule"],
    "workaround": ["spec_rule", "experience"],
}


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_predeclared_scope(case):
    before = {key: "v1" for keys in DEPENDENCIES.values() for key in keys}
    before.update(documentation="v1", experience="reviewed")
    after = dict(before, **case["after"])
    claims = [
        {"id": name, "depends_on": keys, "checks": [name],
         "evidence_sha256": hashlib.sha256(name.encode()).hexdigest()}
        for name, keys in DEPENDENCIES.items()
    ]
    result = plan_revalidation(before, after, claims)
    assert set(result["ordered_checks"]) == set(case["required"])
    statuses = {row["id"]: row["status"] for row in result["claims"]}
    assert {key for key, state in statuses.items() if state == "INSUFFICIENT_ASSOCIATION"} == set(case["insufficient"])
    assert {key for key, state in statuses.items() if state == "HISTORICAL_ONLY"} == set(case["historical"])
    assert bool(result["package_changes"]) == case["package_recheck"]
    assert result["execution"] == "NOT_RUN"


def test_known_shader_change_does_not_explain_the_whole_source_delta():
    before = {"project_source": "source-a", "shader_interface": "layout-a", "retirement": "retirement-a"}
    after = before | {"project_source": "source-b", "shader_interface": "layout-b"}
    claims = [
        {"id": "descriptor", "depends_on": ["shader_interface"], "checks": ["reflect_descriptor"],
         "evidence_sha256": "a" * 64},
        {"id": "retirement", "depends_on": ["retirement"], "checks": ["exercise_retirement"],
         "evidence_sha256": "b" * 64},
    ]
    result = plan_revalidation(before, after, claims)
    assert result["unclassified_changes"] == ["project_source"]
    assert result["ordered_checks"] == ["reflect_descriptor"]
    assert [(item["status"], item["manual_review_required"]) for item in result["claims"]] == [
        ("REVALIDATE", True), ("INSUFFICIENT_ASSOCIATION", True),
    ]
    assert result["execution"] == "NOT_RUN"
