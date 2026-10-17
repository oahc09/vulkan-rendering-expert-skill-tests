"""TC8: project hygiene tests."""

import re
from pathlib import Path

import pytest

from conftest import SKILL_DIR, PROJECT_ROOT


def _is_template(path: Path) -> bool:
    return "template" in path.name.lower()


# TC8.1 original/ 目录下无 .py 文件
def test_original_tree_no_python_files():
    py_files = list(SKILL_DIR.rglob("*.py"))
    assert not py_files, f"Python files found in original/: {py_files}"


# TC8.2 项目根目录无临时文件（排除 tests/ 目录）
def test_project_root_no_temp_files():
    tmp_files = []
    py_files = []
    for p in PROJECT_ROOT.iterdir():
        if p.is_dir():
            continue
        if p.name.startswith(".tmp"):
            tmp_files.append(p.name)
        if p.suffix == ".py":
            py_files.append(p.name)
    assert not tmp_files, f".tmp* files in project root: {tmp_files}"
    assert not py_files, f".py files in project root (excluding tests/): {py_files}"


# TC8.3 非模板文件中无 TODO/FIXME/XXX 标记（排除 change_log.md）
def test_no_todo_fixme_in_non_templates():
    pattern = re.compile(r"\b(TODO|FIXME|XXX)\b", re.I)
    failures = []
    for path in SKILL_DIR.rglob("*.md"):
        if _is_template(path):
            continue
        if path.name == "change_log.md":
            continue
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            failures.append(f"{path.relative_to(SKILL_DIR)}: {match.group(0)}")
    assert not failures, "TODO/FIXME/XXX found:\n" + "\n".join(failures[:50])


# TC8.4 非模板文件中无占位符内容
def test_no_placeholder_content_in_non_templates():
    pattern = re.compile(r"(?<![a-zA-Z0-9_])xxx(?![a-zA-Z0-9_])", re.I)
    failures = []
    for path in SKILL_DIR.rglob("*.md"):
        if _is_template(path):
            continue
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            failures.append(f"{path.relative_to(SKILL_DIR)}: {match.group(0)}")
    assert not failures, "Placeholder 'xxx' found:\n" + "\n".join(failures[:50])


# TC8.5 release_checklist 条目可操作
def test_release_checklist_items_are_actionable():
    # v1.0.6 consolidated the checklist; absence must fail rather than skip.
    path = SKILL_DIR / "07_integration_pack" / "maintenance_release_token_policy.md"
    assert path.is_file(), "Consolidated maintenance/release policy missing"
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^## Part 2\. Release Checklist[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert match, "Part 2 Release Checklist section missing"
    checkboxes = re.findall(r"^\s*- \[[ xX]\](.*)$", match.group(1), re.M)
    assert checkboxes, "Release Checklist must contain actionable checkbox items"
    assert all(item.strip() for item in checkboxes), "Empty Release Checklist checkbox"
