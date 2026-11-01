"""Mobile content/routing contracts; static smoke checks are not device evidence."""
import hashlib
import json
import re
from pathlib import Path
import pytest
from conftest import PROJECT_ROOT, SKILL_DIR
from behavior_cases import MOBILE_CASES
from run_live_model_behavior import CASES, LEGACY_CASES, ORIGINAL_CASES, select_section
from test_templates import _template_required_sections, _extract_h2_titles, _has_section

NEW_PATHS = {
 '03_api_manual/04_buffer_image_memory/external_resource_interop.md',
 '03_api_manual/07_rendering/mobile_tile_rendering.md',
 '05_workflows/04_android_integration/vulkan_opencl_interop.md',
 '05_workflows/02_render_pass_effects/mobile_neural_graphics.md',
}


def test_exact_mobile_release_scope():
    contract=json.loads((Path(__file__).parent.parent/'release-contract.json').read_text())
    assert contract['expected_version']=='1.0.11'
    assert contract['max_runtime_files']==200
    assert set(contract['allowed_new_knowledge'])=={'references/'+p for p in NEW_PATHS}
    assert contract['knowledge_baseline_sha']=='349dc35bd769ca6174afa5714450a4aa9f4cecf8'


def test_mobile_cases_are_registered_without_changing_old_cohorts():
    assert len(MOBILE_CASES)==12 and len(CASES)==28 and len(LEGACY_CASES)==16 and len(ORIGINAL_CASES)==12
    assert set(MOBILE_CASES).isdisjoint(LEGACY_CASES)
    assert CASES[:16]==LEGACY_CASES
    for case,spec in MOBILE_CASES.items():
        assert (Path(__file__).parent/'prompts'/f'{case}.txt').read_text().strip()==spec['prompt']
        assert len(spec['rubric'])>100 and len(spec['required'])>=4
        assert spec['rubric'] not in spec['prompt']


@pytest.mark.parametrize('path',sorted(NEW_PATHS))
def test_new_mobile_documents_follow_template_and_have_section_routes(path):
    text=(SKILL_DIR/path).read_text()
    api=path.startswith('03_api_manual/')
    template=SKILL_DIR/('03_api_manual/api_card_template.md' if api else '05_workflows/workflow_template.md')
    sections=_extract_h2_titles(text)
    assert all(_has_section(sections,s) for s in _template_required_sections(template))
    anchors=re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)["\']\s*></a>',text)
    assert anchors, 'Stable topic anchors required'
    for anchor in anchors:
        chunk,_,_=select_section(text,'#'+anchor)
        assert len(chunk.strip())>80, 'No empty mobile skeleton or anchor-only section'
    name=Path(path).name
    index=(SKILL_DIR/('03_api_manual/api_index.md' if api else '05_workflows/workflow_index.md')).read_text()
    assert name in index
    routes=(SKILL_DIR/'07_integration_pack/task_routing_rules.md').read_text()
    assert re.search(re.escape(name)+r'#[\w-]+',routes), 'Topic must be section-routable, not mandatory whole-file startup'
    assert name not in (PROJECT_ROOT/'SKILL.md').read_text(), 'Do not add all mobile cards to fixed startup'
    assert re.search(r'回退|fallback',text,re.I)
    assert re.search(r'查询|query',text,re.I)
    assert re.search(r'失败|不支持|unsupported',text,re.I)


@pytest.mark.parametrize('path,patterns',[
 ('03_api_manual/07_rendering/mobile_tile_rendering.md',['QCOM','depth|深度','sample|采样','邻域','同像素|same.pixel','回退|fallback']),
 ('03_api_manual/04_buffer_image_memory/external_resource_interop.md',['SYNC_FD','opaque|OPAQUE','AHardwareBuffer|AHB','driverUUID|driver UUID|驱动.*UUID','所有权|owner','失败']),
 ('05_workflows/04_android_integration/vulkan_opencl_interop.md',['UUID','owner|所有权','失败','往返|round.trip','现有|已有']),
 ('05_workflows/02_render_pass_effects/mobile_neural_graphics.md',['history|历史','jitter','motion','depth|深度','进程|process','VkDevice','仿真|emulat','回退|fallback']),
])
def test_capability_contracts_include_failure_and_standard_fallback(path,patterns):
    text=(SKILL_DIR/path).read_text()
    for pattern in patterns:
        assert re.search(pattern,text,re.I),f'{path} missing contract smoke criterion {pattern}'


def reject_invented_fault_api(text):
    # Negative prose is allowed, executable-looking calls and affirmative use are not.
    for line in text.splitlines():
        if 'vkGetDeviceFaultInfoKHR' in line:
            assert not re.search(r'vkGetDeviceFaultInfoKHR\s*\(',line)
            assert re.search(r'不存在|虚构|错误|不能|不得|不是|不要|invalid|nonexistent',line,re.I)


def test_fault_symbol_negative_example_is_not_treated_as_api_use():
    reject_invented_fault_api('错误反例：`vkGetDeviceFaultInfoKHR` 不存在，不能改后缀。')
    with pytest.raises(AssertionError):
        reject_invented_fault_api('调用 vkGetDeviceFaultInfoKHR 获取报告')
    with pytest.raises(AssertionError):
        reject_invented_fault_api('错误示例\nvkGetDeviceFaultInfoKHR(device, &report);')
    text=(SKILL_DIR/'04_debug_playbooks/02_crash_hang/device_lost.md').read_text()
    reject_invented_fault_api(text)
    for symbol in ['vkGetDeviceFaultInfoEXT','vkGetDeviceFaultReportsKHR','vkGetDeviceFaultDebugInfoKHR']:
        assert symbol in text
    assert re.search(r'generation|代际|代次',text,re.I)
    assert re.search(r'不能排除|不等于排除|不排除|不能.*排除',text)


def test_exact_plan_and_device_matrix_are_not_execution_evidence():
    root=Path(__file__).parent.parent
    source=json.loads((root/'docs/v1.0.11-plan-source.json').read_text())
    assert hashlib.sha256((root/'docs/update-plan-v1.0.11.md').read_bytes()).hexdigest()==source['sha256']
    matrix=json.loads((root/'docs/v1.0.11-device-matrix.json').read_text())
    assert len(matrix['targets'])==4
    for target in matrix['targets']:
        assert target['status']=='UNVERIFIED'
        assert target['measurements'] is None
        assert target['device_identity'] is None


def test_mobile_source_map_is_traceable_without_promoting_device_evidence():
    root=Path(__file__).parent.parent
    report=json.loads((root/'docs/v1.0.11-sources.json').read_text())
    assert len(report['research_bundle_hashes'])==3
    assert report['sources']
    for row in report['sources']:
        assert row['source_url'].startswith('https://')
        assert row['verification']=='source_read'
        assert row['build_tested'] is False and row['device_tested'] is False
        assert row['checked_at']=='2026-11-01'
        assert row['capability_requirements'] and row['recheck_trigger']
        assert set(row['runner_cases'])<=set(MOBILE_CASES)
        for mapping in row['mapped_skill_path']:
            path,_,anchor=mapping.partition('#')
            text=(PROJECT_ROOT/path).read_text()
            if anchor:
                assert select_section(text,'#'+anchor)[0].strip()
