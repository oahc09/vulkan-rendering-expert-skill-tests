"""TC11: v1.0.8 Project Diagnosis regression tests."""

import re
import subprocess
from pathlib import Path

from conftest import PROJECT_ROOT, SKILL_DIR


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _h2_titles(text: str):
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", text, re.M)]


def _resolve_backtick_refs(text: str, source: Path):
    refs = []
    for match in re.finditer(r"`([^`]*\.md(?:#[^`\s]*)?)`", text):
        ref = match.group(1).split("#", 1)[0]
        if "xxx" in ref.lower():
            continue
        local = (source.parent / ref).resolve()
        if local.is_file():
            refs.append((ref, local))
            continue
        rooted = (SKILL_DIR / ref).resolve()
        refs.append((ref, rooted))
    return refs


def test_v1_0_8_version_and_entry_routing():
    skill = _read(PROJECT_ROOT / "SKILL.md")
    assert re.search(r"^\s*version:\s*1\.0\.8\s*$", skill, re.M)
    assert "project_diagnosis.md" in skill
    assert "[CODE]" in skill


def test_project_diagnosis_workflow_exists_and_follows_template():
    workflow = SKILL_DIR / "05_workflows" / "01_renderer_setup" / "project_diagnosis.md"
    assert workflow.is_file()

    text = _read(workflow)
    sections = _h2_titles(text)
    required = [
        "0. 适用范围",
        "1. 任务目标",
        "2. 输入条件",
        "3. 前置检查",
        "4. Vulkan 对象链路",
        "5. 资源设计",
        "6. Pipeline / Descriptor 设计",
        "7. 同步与 Layout 设计",
        "8. 实现步骤",
        "9. Android 注意点",
        "10. 验证方式",
    ]
    missing = [s for s in required if not any(x.startswith(s) for x in sections)]
    assert not missing, f"project_diagnosis workflow missing sections: {missing}"

    validation = text.split("## 10. 验证方式", 1)[1].split("\n## ", 1)[0]
    checks = re.findall(r"- \[[ xX]\]", validation)
    assert len(checks) >= 3, f"project_diagnosis has only {len(checks)} validation checks"


def test_code_source_tag_is_consistent():
    source_tags = _read(SKILL_DIR / "01_source_map_and_api_manual_strategy" / "source_tags.md")
    accuracy = _read(SKILL_DIR / "00_expert_entry" / "accuracy_check.md")

    assert "[CODE]" in source_tags
    assert "[CODE]" in accuracy
    assert "当前目标项目源码直接证据" in source_tags
    assert "不能覆盖" in source_tags or "不能覆盖" in accuracy
    assert "[SPEC]" in source_tags


def test_project_diagnosis_is_wired_through_routing_stack():
    files = {
        "classifier": SKILL_DIR / "00_expert_entry" / "task_classifier.md",
        "formats": SKILL_DIR / "00_expert_entry" / "response_formats.md",
        "retrieval_loop": SKILL_DIR / "00_expert_entry" / "progressive_retrieval.md",
        "routing": SKILL_DIR / "07_integration_pack" / "task_routing_rules.md",
        "retrieval_policy": SKILL_DIR / "07_integration_pack" / "retrieval_policy.md",
        "workflow_index": SKILL_DIR / "05_workflows" / "workflow_index.md",
    }

    missing = []
    for name, path in files.items():
        text = _read(path)
        if "project_diagnosis" not in text and "项目诊断" not in text:
            missing.append(name)
    assert not missing, f"project diagnosis not wired in: {missing}"


def test_source_level_impact_categories_exist():
    text = _read(SKILL_DIR / "02_core_mental_model" / "regression_reasoning.md")
    for phrase in [
        "[CODE]",
        "Must Change",
        "Should Change",
        "Can Defer",
        "Do Not Change",
        "源码级影响面",
    ]:
        assert phrase in text, f"missing source-level impact concept: {phrase}"


def test_project_diagnosis_internal_references_exist():
    workflow = SKILL_DIR / "05_workflows" / "01_renderer_setup" / "project_diagnosis.md"
    refs = _resolve_backtick_refs(_read(workflow), workflow)
    broken = [f"{ref} -> {resolved}" for ref, resolved in refs if not resolved.is_file()]
    assert not broken, "broken project_diagnosis references:\n" + "\n".join(broken)


def test_v1_0_8_integration_scenarios_exist():
    text = _read(SKILL_DIR / "07_integration_pack" / "integration_test_plan.md")
    for heading in [
        "测试 8：陌生仓库 Architecture Map",
        "测试 9：Vulkan 1.1 → 1.3 源码影响面",
        "测试 10：Android rotation crash 源码映射",
        "测试 11：已有引擎新增 Compute Pass",
    ]:
        assert heading in text, f"missing integration scenario: {heading}"


def test_module_summary_matches_project_diagnosis_file_count():
    summary = _read(SKILL_DIR / "MODULE_SUMMARY.md")
    match = re.search(r"- `05_workflows`: (\d+) files", summary)
    assert match, "05_workflows count missing from MODULE_SUMMARY.md"

    actual = len(list((SKILL_DIR / "05_workflows").rglob("*.md")))
    assert int(match.group(1)) == actual
    assert actual == 46


def test_clawhub_tracked_file_limit():
    try:
        output = subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "ls-files"],
            text=True,
            stderr=subprocess.STDOUT,
        )
        tracked = [line for line in output.splitlines() if line.strip()]
        count = len(tracked)
    except Exception:
        # Fallback for materialized/non-git test environments.
        count = sum(1 for p in PROJECT_ROOT.rglob("*") if p.is_file())

    assert count <= 200, f"ClawHub tracked file limit exceeded: {count}/200"
