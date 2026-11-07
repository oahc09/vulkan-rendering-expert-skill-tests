"""VIS14 source/registration/isolation tests, not semantic model acceptance."""
import hashlib,json,re
from pathlib import Path
import pytest
from conftest import PROJECT_ROOT, SKILL_DIR
from visual_cases import VIS14_CASES
from run_live_model_behavior import CASES,V113_CASES,ORIGINAL_CASES,read_context,select_section
ROOT=Path(__file__).resolve().parent.parent
ANCHORS={
 '02_core_mental_model/engine_architecture.md':['hybrid-lighting-decisions'],
 '02_core_mental_model/render_target_model.md':['lighting-temporal-data-contract'],
 '03_api_manual/06_pipeline/compute_pipeline.md':['ray-query-capability-contract'],
 '03_api_manual/04_buffer_image_memory/memory_allocation.md':['acceleration-structure-resource-contract'],
 '03_api_manual/08_synchronization/pipeline_barrier.md':['as-build-query-dependencies'],
 '05_workflows/02_render_pass_effects/add_depth_pass.md':['stable-shadow-workflow'],
 '05_workflows/03_compute_workflows/add_compute_pass.md':['hybrid-ray-query-workflow','opacity-micromap-fallback'],
 '05_workflows/02_render_pass_effects/add_postprocess_pass.md':['temporal-quality-workflow'],
 '05_workflows/02_render_pass_effects/mobile_neural_graphics.md':['temporal-sdk-adapters'],
 '04_debug_playbooks/01_visual_issues/flickering.md':['hybrid-temporal-diagnostics'],
 '05_workflows/07_optimization/optimize_frame_time.md':['quality-budget-tiers'],
 '06_cases/06_performance/case_performance.md':['hybrid-quality-evidence'],
}

def test_verbatim_plan_and_no_new_knowledge():
    raw=(ROOT/'docs/update-plan-v1.0.14.md').read_bytes()
    meta=json.loads((ROOT/'docs/v1.0.14-plan-source.json').read_text())
    assert len(raw)==meta['bytes']==46833 and hashlib.sha256(raw).hexdigest()==meta['sha256']
    c=json.loads((ROOT/'release-contract.json').read_text())
    assert c['expected_version']=='1.0.16' and c['max_runtime_files']==200 and c['allowed_new_knowledge']==[]

def test_frozen_old64_and_separate20():
    frozen=json.loads((ROOT/'tests/v113-cohort.json').read_text())
    assert frozen['source_tests_sha']=='9c4cba3a3985b709ccdbec182c79a6988bfc721e'
    assert list(frozen['cases'])==V113_CASES==CASES[:64]
    for c,h in frozen['cases'].items():assert hashlib.sha256((ROOT/'tests/prompts'/f'{c}.txt').read_bytes()).hexdigest()==h
    assert len(CASES)==120 and len(set(CASES))==120 and len(ORIGINAL_CASES)==12
    assert list(VIS14_CASES)==CASES[64:84] and len(VIS14_CASES)==20
    assert {v['id'] for v in VIS14_CASES.values()}=={f'VIS14-{i:02}' for i in range(1,21)}
    for c,v in VIS14_CASES.items():
        assert (ROOT/'tests/prompts'/f'{c}.txt').read_text().strip()==v['prompt']
        assert set(v['variants'])=={'primary','contrast'}
        assert all(x in v['prompt'] for x in v['variants'].values())
        assert len(set(v['variants'].values()))==2 and len(v['rubric'])>100
        for pattern in v['required']:re.compile(pattern)

@pytest.mark.parametrize('path,anchor',[(p,a) for p,aa in ANCHORS.items() for a in aa])
def test_unique_independently_loaded_authority_routes(path,anchor):
    raw=(SKILL_DIR/path).read_text()
    assert raw.count(f'id="{anchor}"')==1
    selected,_,_=select_section(raw,'#'+anchor)
    assert len(selected)>100
    assert f'{path}#{anchor}' in (SKILL_DIR/'07_integration_pack/task_routing_rules.md').read_text()
    assert anchor not in (PROJECT_ROOT/'SKILL.md').read_text()

@pytest.mark.parametrize('path',['tests/visual_cases.py','tests/visual_host_contracts.py','docs/update-plan-v1.0.14.md','tests/fixtures/hybrid_quality_lab/README.md','reports/v1.0.14/acceptance.json'])
def test_model_cannot_read_evaluation_or_lab(path):
    with pytest.raises((ValueError,OSError)):read_context(ROOT,path,None)

def invalid_positive_wsi(text):
    # Deliberately scoped former invalid example shapes, not all prose negations.
    return bool(re.search(r'acquire image[（(]wait timeline|present[（(]wait timeline',text))

def test_summary_and_body_do_not_reintroduce_wsi_depth_examples():
    modern=(SKILL_DIR/'02_core_mental_model/modern_patterns.md').read_text()
    assert not invalid_positive_wsi(modern)
    assert invalid_positive_wsi('present(wait timeline N)')
    assert not invalid_positive_wsi('present wait binary renderFinished')
    assert 'binary imageAvailable' in modern and 'binary renderFinished[imageIndex]' in modern
    assert '无需运行时查询' not in modern
    depth=(SKILL_DIR/'05_workflows/02_render_pass_effects/add_depth_pass.md').read_text()
    assert '仅当 depth 直接 present' not in depth and '| Fragment output |' not in depth
    assert 'EARLY_FRAGMENT_TESTS' in depth and 'LATE_FRAGMENT_TESTS' in depth
    assert 'DEPTH_ATTACHMENT_OPTIMAL' in depth and '不能直接 present' in depth

def test_source_ledger_dates_revisions_and_claim_boundaries():
    ledger=json.loads((ROOT/'docs/v1.0.14-sources.json').read_text())
    assert ledger['window']==['2026-08-05','2026-11-02']
    for row in ledger['sources']:
        assert {'event_date','published_at','updated_at','checked_at','verification','license_boundary'}<=row.keys()
        assert row['device']=='NOT_RUN' and row['live']=='NOT_RUN'
        if row['verification']=='source_read':
            assert re.fullmatch('[0-9a-f]{40}',row['revision'])
            assert re.fullmatch('[0-9a-f]{64}',row['sha256'])
        assert row['mapped_skill_paths']
        for path in row['mapped_skill_paths']:
            file,anchor=path.split('#');assert select_section((PROJECT_ROOT/file).read_text(),'#'+anchor)[0]
