"""TEXT18 registry isolation and predecessor byte freeze, not behavior PASS."""
import hashlib,json
from pathlib import Path
import pytest
from run_live_model_behavior import CASES,read_context,build_prompt
ROOT=Path(__file__).resolve().parent

def test_old120_bytes_frozen():
    frozen=json.loads((ROOT/'v116-cohort.json').read_text())
    assert frozen['source_tests_sha']=='528ba9ea7b417684c1066aceabd9a79cae4cd05b'
    assert list(frozen['cases'])==CASES and len(CASES)==120
    for case,digest in frozen['cases'].items():
        assert hashlib.sha256((ROOT/'prompts'/f'{case}.txt').read_bytes()).hexdigest()==digest

def test_text18_twenty_pairs_and_rubric_separation():
    cases=json.loads((ROOT/'text18_cases.json').read_text())
    rubrics=json.loads((ROOT/'text18_rubrics.json').read_text())
    assert len(cases)==20 and cases.keys()==rubrics.keys()
    assert {v['id'] for v in cases.values()}=={f'TEXT18-{i:02}' for i in range(1,21)}
    assert not set(cases).intersection(CASES)
    for name,c in cases.items():
        assert len(set(c['variants'].values()))==2
        assert set(c)=={'id','variants','prompt'}
        assert (ROOT/'prompts'/f'{name}.txt').read_text().strip()==c['prompt']
        assert all(v in c['prompt'] for v in c['variants'].values())
        request=build_prompt('ENTRY',c['prompt'])
        assert rubrics[name]['evaluation'] not in request
        assert rubrics[name]['must_not'] not in request

@pytest.mark.parametrize('path',['tests/text18_cases.json','tests/text18_rubrics.json','tests/text_host_contracts.py','docs/v1.0.18-status.md'])
def test_private_material_not_context(path):
    with pytest.raises((ValueError,OSError)):read_context(ROOT.parent,path,None)

def test_live_adapter_reuses_provenance_not_old_gate():
    from run_text18_live import main
    with pytest.raises(ValueError):main(['--check'])

def test_candidate_skill_pin_and_on_demand_anchors():
    import subprocess
    from conftest import PROJECT_ROOT
    contract=json.loads((ROOT.parent/'text18-candidate-contract.json').read_text())
    assert subprocess.check_output(['git','-C',str(PROJECT_ROOT),'rev-parse','HEAD'],text=True).strip()==contract['skill_sha']
    authorities={
      '02_core_mental_model/engine_architecture.md':'text-provider-contract',
      '05_workflows/04_android_integration/integrate_surfaceview_anativewindow.md':'platform-text-resource-bridge',
      '05_workflows/02_render_pass_effects/add_texture_sampling_pass.md':'glyph-representation-quality',
      '03_api_manual/04_buffer_image_memory/sampler.md':'glyph-filtering-contract',
      '05_workflows/06_pipeline_descriptor/add_graphics_pipeline.md':'vector-and-extruded-text',
      '05_workflows/05_resource_management/add_texture_resource.md':'dynamic-glyph-atlas',
      '05_workflows/05_resource_management/manage_resource_lifetime.md':'glyph-generation-retirement',
      '05_workflows/02_render_pass_effects/add_postprocess_pass.md':'text-overlay-composition',
      '05_workflows/07_optimization/optimize_frame_time.md':'text-quality-cost-budget',
    }
    from run_live_model_behavior import select_section
    for path,anchor in authorities.items():
        text=(PROJECT_ROOT/'references'/path).read_text()
        selected,_,_=select_section(text,'#'+anchor)
        assert len(selected)>200 and text.count(f'id="{anchor}"')==1
        assert anchor not in (PROJECT_ROOT/'SKILL.md').read_text()
