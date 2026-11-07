"""TRAN15 registry, source anchors, frozen predecessor and evaluation isolation."""
import hashlib,json,re
from pathlib import Path
import pytest
from conftest import PROJECT_ROOT, SKILL_DIR
from transparency_cases import TRAN15_CASES
from run_live_model_behavior import CASES,V114_CASES,ORIGINAL_CASES,read_context,select_section
ROOT=Path(__file__).resolve().parent.parent
ANCHORS={
 '02_core_mental_model/render_target_model.md':['transparent-composition-contract'],
 '02_core_mental_model/engine_architecture.md':['transparent-gaussian-budget-decision'],
 '03_api_manual/06_pipeline/graphics_pipeline.md':['blend-format-capability'],
 '03_api_manual/07_rendering/render_target_layout.md':['refraction-read-write-boundary'],
 '03_api_manual/04_buffer_image_memory/image.md':['transparent-target-precision'],
 '05_workflows/02_render_pass_effects/add_postprocess_pass.md':['transparency-resolve','local-volume-composite'],
 '05_workflows/02_render_pass_effects/add_texture_sampling_pass.md':['screen-space-refraction'],
 '05_workflows/03_compute_workflows/add_compute_pass.md':['gaussian-preproject-sort'],
 '05_workflows/03_compute_workflows/compute_to_graphics_sync.md':['gaussian-consumer-dependencies'],
 '05_workflows/07_optimization/optimize_mobile_bandwidth.md':['coverage-budget'],
}

def test_plan_original_bytes_and_current_predecessor():
    raw=(ROOT/'docs/update-plan-v1.0.15.md').read_bytes();meta=json.loads((ROOT/'docs/v1.0.15-plan-source.json').read_text())
    assert len(raw)==meta['bytes']==45601
    assert hashlib.sha256(raw).hexdigest()==meta['sha256']
    c=json.loads((ROOT/'release-contract.json').read_text())
    assert c['expected_version']=='1.0.15' and c['max_runtime_files']==200 and c['allowed_new_knowledge']==[]
    assert c['knowledge_baseline_sha']=='4a7ff82372648c4a9df91e76848cbc9c95de51a3'

def test_frozen_old84_and_new20():
    f=json.loads((ROOT/'tests/v114-cohort.json').read_text())
    assert f['source_tests_sha'].startswith('f8cadd3')
    assert list(f['cases'])==V114_CASES==CASES[:84]
    for name,digest in f['cases'].items():assert hashlib.sha256((ROOT/'tests/prompts'/f'{name}.txt').read_bytes()).hexdigest()==digest
    assert len(CASES)==len(set(CASES))==104 and len(ORIGINAL_CASES)==12
    assert list(TRAN15_CASES)==CASES[84:] and {x['id'] for x in TRAN15_CASES.values()}=={f'TRAN15-{i:02}' for i in range(1,21)}
    for name,c in TRAN15_CASES.items():
        assert (ROOT/'tests/prompts'/f'{name}.txt').read_text().strip()==c['prompt']
        assert set(c['variants'])=={'primary','contrast'} and len(set(c['variants'].values()))==2
        assert all(v in c['prompt'] for v in c['variants'].values()) and len(c['rubric'])>100
        for pattern in c['required']:re.compile(pattern)

@pytest.mark.parametrize('path,anchor',[(p,a) for p,anchors in ANCHORS.items() for a in anchors])
def test_unique_independent_authority(path,anchor):
    raw=(SKILL_DIR/path).read_text()
    assert raw.count(f'id="{anchor}"')==1
    selected,_,_=select_section(raw,'#'+anchor);assert len(selected)>150
    assert f'{path}#{anchor}' in (SKILL_DIR/'07_integration_pack/task_routing_rules.md').read_text()
    assert anchor not in (PROJECT_ROOT/'SKILL.md').read_text()

@pytest.mark.parametrize('path',['tests/transparency_cases.py','tests/transparency_host_contracts.py','docs/update-plan-v1.0.15.md','tests/fixtures/transparent_scene_lab/README.md','reports/v1.0.15/acceptance.json'])
def test_eval_context_isolation(path):
    with pytest.raises((ValueError,OSError)):read_context(ROOT,path,None)

def test_source_license_and_claim_boundaries():
    ledger=json.loads((ROOT/'docs/v1.0.15-sources.json').read_text());assert ledger['window']==['2026-08-10','2026-11-07']
    for row in ledger['sources']:
        assert {'source_id','canonical_url','event_date','published_at','updated_at','checked_at','revision','claim','evidence_level','unverified_scope','license_boundary'}<=row.keys()
        assert row['unverified_scope'] and row['license_boundary']
        if row['verification']=='source_read':
            assert re.fullmatch('[0-9a-f]{40}',row['revision']) and re.fullmatch('[0-9a-f]{64}',row['sha256'])
            assert row['mapped_skill_paths']
        for target in row['mapped_skill_paths']:
            path,_,anchor=target.partition('#');assert (PROJECT_ROOT/path).is_file()
            if anchor:assert select_section((PROJECT_ROOT/path).read_text(),'#'+anchor)[0]
