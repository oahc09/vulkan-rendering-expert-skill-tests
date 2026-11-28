"""Current-pair equivalents of useful checks inside historical-only nodes.
Historical SHA/version assertions remain unchanged in their original cohorts.
These checks establish packaging/routing integrity, not capability acceptance.
"""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import PROJECT_ROOT
from run_live_model_behavior import select_section

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.candidate19
AUTHORITIES = {
    '02_core_mental_model/engine_architecture.md': 'text-provider-contract',
    '05_workflows/04_android_integration/integrate_surfaceview_anativewindow.md': 'platform-text-resource-bridge',
    '05_workflows/02_render_pass_effects/add_texture_sampling_pass.md': 'glyph-representation-quality',
    '03_api_manual/04_buffer_image_memory/sampler.md': 'glyph-filtering-contract',
    '05_workflows/06_pipeline_descriptor/add_graphics_pipeline.md': 'vector-and-extruded-text',
    '05_workflows/05_resource_management/add_texture_resource.md': 'dynamic-glyph-atlas',
    '05_workflows/05_resource_management/manage_resource_lifetime.md': 'glyph-generation-retirement',
    '05_workflows/02_render_pass_effects/add_postprocess_pass.md': 'text-overlay-composition',
    '05_workflows/07_optimization/optimize_frame_time.md': 'text-quality-cost-budget',
}


def git(*args):
    return subprocess.check_output(['git', '-C', str(PROJECT_ROOT), *args], text=True).strip()


def selected_pair():
    name = os.environ.get('VULKAN_REGRESSION_PAIR', 'historical-v1.0.19')
    sys.path.insert(0, str(ROOT / 'checks19'))
    try:
        from check_pair import load_pair
        pair = load_pair(name)
    finally:
        sys.path.pop(0)
    return pair, '1.0.19' if name == 'historical-v1.0.19' else pair['skill_version']


def test_current19_identity_and_preserved_diagnosis_routing():
    pair, expected_version = selected_pair()
    assert git('rev-parse', 'HEAD') == pair['skill_sha']
    skill = (PROJECT_ROOT / 'SKILL.md').read_text()
    assert re.search(r'^\s*version:\s*' + re.escape(expected_version) + r'\s*$', skill, re.M)
    assert 'task_routing_rules.md' in skill
    routing = (PROJECT_ROOT / 'references/07_integration_pack/task_routing_rules.md').read_text()
    assert 'project_diagnosis.md' in routing
    workflow = (PROJECT_ROOT / 'references/05_workflows/01_renderer_setup/project_diagnosis.md').read_text()
    assert '[CODE]' in workflow and 'Architecture Map' in workflow


@pytest.mark.parametrize('path,anchor', sorted(AUTHORITIES.items()))
def test_current19_retains_text18_on_demand_authority(path, anchor):
    text = (PROJECT_ROOT / 'references' / path).read_text()
    selected, _, _ = select_section(text, '#' + anchor)
    assert len(selected) > 200
    assert text.count(f'id="{anchor}"') == 1
    assert anchor not in (PROJECT_ROOT / 'SKILL.md').read_text()


def test_current19_reproducible_package_crc_and_knowledge_budget(tmp_path):
    pair, _ = selected_pair()
    baseline_contract = json.loads((ROOT / 'release-contract.json').read_text())
    sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
    try:
        spec = importlib.util.spec_from_file_location('equivalence19_packer', PROJECT_ROOT / 'scripts/agensi_audit_and_pack.py')
        packer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packer)
        a = packer.check(PROJECT_ROOT, tmp_path / 'a.zip')
        b = packer.check(PROJECT_ROOT, tmp_path / 'b.zip')
    finally:
        sys.path.pop(0)
    assert a['status'] == b['status'] == 'PASS'
    assert a['revision'] == b['revision'] == pair['skill_sha'] == git('rev-parse', 'HEAD')
    assert (tmp_path / 'a.zip').read_bytes() == (tmp_path / 'b.zip').read_bytes()
    tracked = set(git('ls-files').splitlines())
    packaged = {item['path'] for item in a['files']}
    assert a['tracked_files'] == b['tracked_files'] == len(tracked)
    assert a['package_files'] == b['package_files'] == len(packaged) <= baseline_contract['max_runtime_files']
    assert packaged == {item['path'] for item in b['files']}
    assert packaged == {p for p in tracked if p in packer.REQUIRED or p.startswith('references/')}
    if 'package_manifest_sha256' in pair:
        assert a['package_files'] == b['package_files'] == pair['package_files'] <= pair['package_file_limit']
        for report in (a, b):
            canonical = json.dumps(sorted(report['files'], key=lambda item: item['path']),
                                   sort_keys=True, separators=(',', ':')).encode()
            assert hashlib.sha256(canonical).hexdigest() == pair['package_manifest_sha256']
    assert a['zip']['crc_verified'] and b['zip']['crc_verified']
    baseline = set(git('ls-tree', '-r', '--name-only', baseline_contract['knowledge_baseline_sha']).splitlines())
    assert {p for p in tracked if p.startswith('references/')} == (
        {p for p in baseline if p.startswith('references/')} | set(baseline_contract['allowed_new_knowledge'])
    )
