"""pytest public fixtures for Vulkan rendering expert skill tests.

Tests live in this standalone repo (vulkan-rendering-expert-skill-tests) and
assert against the skill repo (vulkan-rendering-expert-skill), which must sit
next to this repo on disk.
"""

import os
import pytest
from pathlib import Path

TESTS_REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = Path(os.environ.get("VULKAN_SKILL_ROOT", TESTS_REPO_ROOT.parent / "skill")).resolve()
if not PROJECT_ROOT.is_dir() and "VULKAN_SKILL_ROOT" not in os.environ:
    PROJECT_ROOT = (TESTS_REPO_ROOT.parent / "vulkan-rendering-expert-skill").resolve()
if not PROJECT_ROOT.is_dir():
    raise RuntimeError(
        f"Skill repo not found at {PROJECT_ROOT}. "
        "Keep vulkan-rendering-expert-skill-tests next to "
        "vulkan-rendering-expert-skill."
    )
SKILL_DIR = PROJECT_ROOT / "references"

MODULES = [
    "00_expert_entry",
    "01_source_map_and_api_manual_strategy",
    "02_core_mental_model",
    "03_api_manual",
    "04_debug_playbooks",
    "05_workflows",
    "06_cases",
    "07_integration_pack",
]


@pytest.fixture
def skill_dir():
    return SKILL_DIR


@pytest.fixture
def all_md_files():
    """Return all .md files under the packaged skill references."""
    return sorted(SKILL_DIR.rglob("*.md"))


@pytest.fixture
def module_dirs():
    return {m: SKILL_DIR / m for m in MODULES}

def pytest_collection_modifyitems(items):
    """Every test belongs to one evidence layer; historical responses stay snapshots."""
    for item in items:
        if item.get_closest_marker("live") or item.get_closest_marker("snapshot"):
            continue
        item.add_marker(pytest.mark.static)
