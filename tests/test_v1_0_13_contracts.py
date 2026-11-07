"""ENG13 source/route contracts; never substitute for shader or GPU execution."""
import hashlib
import json
import re
from pathlib import Path
import pytest
from conftest import PROJECT_ROOT, SKILL_DIR
from engine_cases import ENG13_CASES
from run_live_model_behavior import CASES, V112_CASES, ORIGINAL_CASES, select_section, read_context

ROOT=Path(__file__).parent.parent
ANCHORS={
 '03_api_manual/06_pipeline/shader_module.md':['shader-artifact-contract'],
 '05_workflows/06_pipeline_descriptor/shader_binding_workflow.md':['shader-interface-validation','shader-hot-reload'],
 '03_api_manual/06_pipeline/specialization_constants.md':['variant-cost-boundary'],
 '03_api_manual/06_pipeline/pipeline_cache.md':['cache-compatibility','pipeline-binary-path'],
 '05_workflows/07_optimization/reduce_pipeline_creation_stutter.md':['pipeline-build-scheduler'],
 '05_workflows/05_resource_management/add_texture_resource.md':['texture-streaming-residency'],
 '05_workflows/05_resource_management/manage_resource_lifetime.md':['geometry-streaming-retirement'],
 '03_api_manual/04_buffer_image_memory/vma_usage.md':['streaming-budget-policy'],
 '02_core_mental_model/compute_graphics_relationship.md':['gpu-scene-contract'],
 '03_api_manual/03_command_buffer/indirect_commands.md':['indirect-capability-fallback','indirect-capacity-safety'],
 '05_workflows/03_compute_workflows/add_compute_pass.md':['gpu-driven-rendering','gpu-lod-residency','hiz-occlusion','multi-view-culling'],
 '05_workflows/03_compute_workflows/compute_to_graphics_sync.md':['gpu-produced-draw-sync'],
 '03_api_manual/06_pipeline/mesh_shader.md':['mesh-path-fallback'],
 '05_workflows/07_optimization/optimize_frame_time.md':['scaled-rendering-ab'],
}


def section(path,anchor):
    text=(SKILL_DIR/path).read_text()
    assert text.count(f'id="{anchor}"')+text.count(f"id='{anchor}'")==1
    chunk,_,_=select_section(text,'#'+anchor)
    assert len(chunk.strip())>80
    return chunk


def test_exact_plan_and_zero_net_new_knowledge_contract():
    raw=(ROOT/'docs/update-plan-v1.0.13.md').read_bytes()
    meta=json.loads((ROOT/'docs/v1.0.13-plan-source.json').read_text())
    assert len(raw)==58967 and hashlib.sha256(raw).hexdigest()==meta['sha256']=='fb37cdb63da98144cc251b97f49ffac3742b8d4e4be262ad9e264f2df4415060'
    c=json.loads((ROOT/'release-contract.json').read_text())
    assert c['expected_version']=='1.0.16' and c['max_runtime_files']==200
    assert c['allowed_new_knowledge']==[]
    assert c['knowledge_baseline_sha']=='75b3dacdcb5e567c86c7ae6e97bcb248b6f46fc3'


def test_original_forty_prompts_and_twelve_denominator_unchanged():
    frozen=json.loads((ROOT/'tests/v112-cohort.json').read_text())
    assert frozen['source_tests_sha']=='9278d9be3a7a4d4e919ac36927ee165a433450a9'
    assert list(frozen['cases'])==V112_CASES==CASES[:40]
    assert len(ORIGINAL_CASES)==12
    for case,sha in frozen['cases'].items():
        assert hashlib.sha256((ROOT/'tests/prompts'/f'{case}.txt').read_bytes()).hexdigest()==sha


def test_twenty_four_engine_scenarios_include_contrasting_conditions():
    assert len(CASES)==120 and len(ENG13_CASES)==24 and list(ENG13_CASES)==CASES[40:64]
    assert {v['id'] for v in ENG13_CASES.values()}=={f'ENG13-{n:02}' for n in range(1,25)}
    for case,spec in ENG13_CASES.items():
        prompt=(ROOT/'tests/prompts'/f'{case}.txt').read_text().strip()
        assert prompt==spec['prompt'] and spec['rubric'] not in prompt
        assert set(spec['variants'])=={'primary','contrast'}
        assert spec['variants']['primary']!=spec['variants']['contrast']
        assert all(v in prompt and len(v)>20 for v in spec['variants'].values())
        assert len(spec['rubric'])>100 and len(spec['required'])>=3
        for regex in spec['required']:re.compile(regex)


@pytest.mark.parametrize('path,anchor',[(p,a) for p,anchors in ANCHORS.items() for a in anchors])
def test_authority_anchors_are_unique_and_independently_readable(path,anchor):
    section(path,anchor)


def test_gpu_driven_route_is_conditional_not_fixed_startup():
    routes=(SKILL_DIR/'07_integration_pack/task_routing_rules.md').read_text()
    assert 'add_compute_pass.md#gpu-driven-rendering' in routes
    entry=(PROJECT_ROOT/'SKILL.md').read_text()
    assert 'gpu-driven-rendering' not in entry
    assert 'shader-artifact-contract' not in entry


def reject_fake_dispatch_stage(text):
    # Allow explicitly labeled counterexamples; never accept affirmative API use.
    for paragraph in re.split(r'\n\s*\n',text):
        if 'DISPATCH_INDIRECT_BIT' in paragraph:
            assert re.search(r'不存在|虚构|错误|禁止|不能|不是|不得|不要|invalid|nonexistent',paragraph,re.I)


def test_indirect_known_error_and_negative_example_boundaries():
    reject_fake_dispatch_stage('错误反例：DISPATCH_INDIRECT_BIT 不存在。')
    with pytest.raises(AssertionError):reject_fake_dispatch_stage('dstStageMask = VK_PIPELINE_STAGE_2_DISPATCH_INDIRECT_BIT;')
    text=(SKILL_DIR/'03_api_manual/03_command_buffer/indirect_commands.md').read_text()
    reject_fake_dispatch_stage(text)
    for symbol in ['DRAW_INDIRECT','maxComputeWorkGroupCount','vertexOffset','VK_EXT_transform_feedback']:
        assert symbol in text
    assert re.search(r'每维|各维|x.*y.*z',text)
    assert re.search(r'LocalSize|local size|maxComputeWorkGroupInvocations|local invocation',text)


@pytest.mark.parametrize('path,anchor,patterns',[
 ('03_api_manual/06_pipeline/shader_module.md','shader-artifact-contract',['sourceHash','compiler','target','reflection','bytecodeHash']),
 ('05_workflows/06_pipeline_descriptor/shader_binding_workflow.md','shader-interface-validation',['offset','stride','动态|DYNAMIC','兼容']),
 ('05_workflows/06_pipeline_descriptor/shader_binding_workflow.md','shader-hot-reload',['generation|代际','失败','旧','退休|退役']),
 ('05_workflows/07_optimization/reduce_pipeline_creation_stutter.md','pipeline-build-scheduler',['generation|代际','取消|Canceled','输入|create.info','CPU','GPU']),
 ('05_workflows/05_resource_management/add_texture_resource.md','texture-streaming-residency',['mip','LOD','分配|allocation','descriptor','回退|fallback|替代|降级']),
 ('03_api_manual/03_command_buffer/indirect_commands.md','indirect-capability-fallback',['multiDrawIndirect','drawIndirectFirstInstance','Count','回退|fallback|退路']),
 ('03_api_manual/03_command_buffer/indirect_commands.md','indirect-capacity-safety',['容量|capacity','写入|write','前缀|prefix','overflow|溢出']),
 ('05_workflows/03_compute_workflows/compute_to_graphics_sync.md','gpu-produced-draw-sync',['DRAW_INDIRECT','count','VERTEX|vertex','INDEX|index','CLEAR|ALL_TRANSFER','queue|Queue']),
 ('05_workflows/03_compute_workflows/add_compute_pass.md','gpu-lod-residency',['驻留|resident','滞回|hysteresis','旧|退休|退役']),
 ('05_workflows/03_compute_workflows/add_compute_pass.md','hiz-occlusion',['max','min','clear','保守','NPOT','历史|history']),
 ('05_workflows/03_compute_workflows/add_compute_pass.md','multi-view-culling',['view|视图','共享','独立','completion|完成|consumer']),
 ('03_api_manual/06_pipeline/mesh_shader.md','mesh-path-fallback',['task','mesh','limits|限制','回退|fallback']),
])
def test_core_contracts_survive_section_only_loading(path,anchor,patterns):
    text=section(path,anchor)
    for pattern in patterns:
        assert re.search(pattern,text,re.I),f'{path}#{anchor} missing {pattern}'


@pytest.mark.parametrize('path',['tests/engine_cases.py','tests/engine_cases.md','tests/fixtures/engine_scale_lab/README.md','reports/v1.0.13/live.md','docs/v1.0.13-traceability.md'])
def test_evaluation_and_experiment_material_cannot_be_model_context(tmp_path,path):
    target=tmp_path/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('hidden fixture/rubric')
    with pytest.raises(ValueError):read_context(tmp_path,path)


def test_indirect_abi_fields_are_readable_separately_from_append_capacity():
    text=(SKILL_DIR/'03_api_manual/03_command_buffer/indirect_commands.md').read_text()
    fields,_,_=select_section(text,'5. 关键字段')
    for pattern in ['stride','offset','vertexOffset','int32|有符号|signed','20','maxComputeWorkGroupCount']:
        assert re.search(pattern,fields,re.I)


def test_binary_section_preserves_empty_info_positive_case_and_capture_condition():
    text=section('03_api_manual/06_pipeline/pipeline_cache.md','pipeline-binary-path')
    for token in ['binaryCount','CAPTURE_DATA','VkPipelineCache','NULL']:
        assert token in text
    assert re.search(r'binaryCount[^\n]{0,80}(?:0|零)',text)
    assert re.search(r'独立|另一个|单独|或设置',text)


def test_engine_sources_bind_fixed_revisions_to_readable_authority_sections():
    report=json.loads((ROOT/'docs/v1.0.13-sources.json').read_text())
    assert len(report['sources'])==16 and len(report['bundles'])==2
    for source in report['sources']:
        assert source['verification']=='source_read'
        assert re.fullmatch('[0-9a-f]{40}',source['revision'])
        assert source['build']=='NOT_RUN' and source['device']=='NOT_RUN'
        assert source['source_url'].startswith('https://')
        for mapping in source['mapped_skill_paths']:
            path,anchor=mapping.split('#')
            assert select_section((PROJECT_ROOT/path).read_text(),'#'+anchor)[0].strip()
