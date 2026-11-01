"""System content and cohort static contracts; lexical checks require human review."""
import hashlib
import json
import re
from pathlib import Path
import pytest
from conftest import PROJECT_ROOT
from system_cases import SYSTEM_CASES
from run_live_model_behavior import CASES, V111_CASES, ORIGINAL_CASES, select_section

ROOT = Path(__file__).parent.parent
TOPICS = {
 'references/02_core_mental_model/android_surface_swapchain_lifecycle.md': 'multi-instance-ownership',
 'references/05_workflows/04_android_integration/handle_android_lifecycle.md': 'multi-surface-lifecycle',
 'references/05_workflows/04_android_integration/integrate_surfaceview_anativewindow.md': 'android-host-contract',
 'references/03_api_manual/10_android_platform/android_surface.md': 'surface-host-boundaries',
 'references/03_api_manual/04_buffer_image_memory/external_resource_interop.md': 'android-media-frame-contract',
 'references/03_api_manual/05_descriptor/sampled_image_descriptor.md': 'android-media-ycbcr',
 'references/05_workflows/02_render_pass_effects/add_texture_sampling_pass.md': 'android-media-sampling',
 'references/02_core_mental_model/render_target_model.md': 'color-output-contract',
 'references/03_api_manual/02_surface_swapchain/swapchain.md': 'android-color-presentation',
 'references/05_workflows/02_render_pass_effects/add_postprocess_pass.md': 'color-output-workflow',
}


def test_system_release_contract_has_zero_new_runtime_knowledge():
    contract=json.loads((ROOT/'release-contract.json').read_text())
    assert contract['expected_version']=='1.0.13'
    assert contract['allowed_new_knowledge']==[]
    assert contract['max_runtime_files']==200
    assert contract['knowledge_baseline_sha']=='d049afefaec8539cecca5f8e37c4cd66ec9da728'


def test_all_28_historical_prompts_and_original_denominator_frozen():
    frozen=json.loads((ROOT/'tests/v1.0.11-cohort.json').read_text())
    assert frozen['source_tests_sha']=='3a8ea8b0f2f848d7b5380bc334633786c01e9248'
    assert list(frozen['cases'])==V111_CASES and CASES[:28]==V111_CASES
    assert len(ORIGINAL_CASES)==12
    for case, sha in frozen['cases'].items():
        assert hashlib.sha256((ROOT/'tests/prompts'/f'{case}.txt').read_bytes()).hexdigest()==sha


def test_system_selector_contains_paired_inputs_but_not_rubrics():
    assert len(CASES)==64 and len(SYSTEM_CASES)==12
    assert CASES[28:40]==list(SYSTEM_CASES)
    assert {s['id'] for s in SYSTEM_CASES.values()}=={f'SYS-{n:02d}' for n in range(1,13)}
    for case,spec in SYSTEM_CASES.items():
        prompt=(ROOT/'tests/prompts'/f'{case}.txt').read_text().strip()
        assert prompt==spec['prompt'] and len(spec['rubric'])>100
        assert spec['rubric'] not in prompt and len(spec['required'])>=4
        assert set(spec['variants'])=={'primary','contrast'}
        for variant in spec['variants'].values():
            assert variant in prompt and len(variant)>20
        for pattern in spec['required']:
            re.compile(pattern)


@pytest.mark.parametrize('path,anchor',TOPICS.items())
def test_system_sections_remain_selectively_loadable(path,anchor):
    text=(PROJECT_ROOT/path).read_text()
    chunk,_,_=select_section(text,'#'+anchor)
    assert len(chunk)>100
    routes=(PROJECT_ROOT/'references/07_integration_pack/task_routing_rules.md').read_text()
    assert Path(path).name+'#'+anchor in routes
    assert anchor not in (PROJECT_ROOT/'SKILL.md').read_text(), 'Not mandatory startup load'


def test_media_section_smoke_requires_lease_failure_and_two_consumers():
    path='references/03_api_manual/04_buffer_image_memory/external_resource_interop.md'
    text=select_section((PROJECT_ROOT/path).read_text(),'#android-media-frame-contract')[0]
    for pattern in ['lease|租约','AHardwareBuffer_acquire','FOREIGN','所有|全部','maxImages','失败','generation|代际','VkFence','-1','void','FD']:
        assert re.search(pattern,text), pattern


def test_exact_plan_sources_and_device_boundaries():
    source=json.loads((ROOT/'docs/v1.0.12-plan-source.json').read_text())
    assert hashlib.sha256((ROOT/'docs/update-plan-v1.0.12.md').read_bytes()).hexdigest()==source['sha256']
    assert source['sha256']=='2688a82c7c9c40f87e9fe3cfbdebfb780a86e55c7c776f1fb983cdc301f230a1'
    matrix=json.loads((ROOT/'docs/v1.0.12-device-matrix.json').read_text())
    assert matrix['status']=='NOT RUN'
    assert len(matrix['targets'])>=4
    for row in matrix['targets']:
        assert row['status']=='UNVERIFIED' and row['device_identity'] is None and row['measurements'] is None
    report=json.loads((ROOT/'docs/v1.0.12-sources.json').read_text())
    assert report['sources']
    for row in report['sources']:
        assert row['url'].startswith('https://')
        assert row['source_read'] is True and row['build'] is False and row['device'] is False
        assert row['checked_at']=='2026-11-01'
        assert row['mapped_skill_path'] and row['recheck_trigger']
        for mapping in row['mapped_skill_path']:
            path,anchor=mapping.split('#',1)
            assert select_section((PROJECT_ROOT/path).read_text(),'#'+anchor)[0].strip()
    trace=json.loads((ROOT/'docs/v1.0.12-traceability.json').read_text())
    assert {r['requirement'] for r in trace['requirements']}=={'C1','C2','C3','M3'}
    assert all(r['live']=='BLOCKED' and r['device']=='NOT RUN' for r in trace['requirements'])
