"""SIM16 development structure, isolation and cohort checks, not Live acceptance.

Skill v1.0.15 merged; paired v1.0.15 test evidence publication remains pending.
These tests assert v1.0.16 candidate structure, not published acceptance.
"""
import hashlib
import json
import re
from pathlib import Path
import pytest
from conftest import PROJECT_ROOT,SKILL_DIR
from simulation_cases import SIM16_CASES
from run_live_model_behavior import CASES,V115_CASES,V114_CASES,ORIGINAL_CASES,read_context,select_section
ROOT=Path(__file__).resolve().parent.parent
ANCHORS={
 '02_core_mental_model/compute_graphics_relationship.md':'simulation-state-contract',
 '05_workflows/03_compute_workflows/add_compute_pass.md':'simulation-scheduling',
 '05_workflows/03_compute_workflows/compute_write_storage_buffer.md':'xpbd-deformation-contract',
 '05_workflows/03_compute_workflows/compute_write_storage_image.md':'heightfield-simulation-contract',
 '05_workflows/03_compute_workflows/compute_to_graphics_sync.md':'simulation-render-handoff',
 '03_api_manual/06_pipeline/compute_pipeline.md':'simulation-kernel-portability',
 '05_workflows/05_resource_management/manage_frame_resources.md':'simulation-snapshot-retirement',
 '05_workflows/07_optimization/optimize_frame_time.md':'simulation-cost-quality-budget',
}


def test_old104_frozen_and_sim16_exact_registration():
    frozen=json.loads((ROOT/'tests/v115-cohort.json').read_text())
    assert frozen['source_tests_sha']=='26bee411429f55cf8eab50326c5f92115b851e2c'
    assert list(frozen['cases'])==V115_CASES==CASES[:104]
    for case,digest in frozen['cases'].items():
        assert hashlib.sha256((ROOT/'tests/prompts'/f'{case}.txt').read_bytes()).hexdigest()==digest
    assert len(CASES)==len(set(CASES))==120
    assert list(SIM16_CASES)==CASES[104:] and len(SIM16_CASES)==16
    assert len(ORIGINAL_CASES)==12
    original=json.loads((ROOT/'tests/original-cohort.json').read_text())['cases']
    assert set(original)==set(ORIGINAL_CASES)
    assert all(frozen['cases'][c]==h for c,h in original.items())
    assert {v['id'] for v in SIM16_CASES.values()}=={f'SIM16-{i:02}' for i in range(1,17)}
    for case,v in SIM16_CASES.items():
        assert (ROOT/'tests/prompts'/f'{case}.txt').read_text().strip()==v['prompt']
        assert set(v['variants'])=={'primary','contrast'} and len(set(v['variants'].values()))==2
        assert all(x in v['prompt'] for x in v['variants'].values())
        assert len(v['rubric'])>100 and v['rubric'] not in v['prompt']
        for pattern in v['required']:re.compile(pattern)


@pytest.mark.parametrize('path,anchor',ANCHORS.items())
def test_development_authorities_are_section_loadable_not_startup(path,anchor):
    raw=(SKILL_DIR/path).read_text()
    assert raw.count(f'id="{anchor}"')==1
    selected,_,_=select_section(raw,'#'+anchor)
    assert len(selected)>200
    assert f'{path}#{anchor}' in (SKILL_DIR/'07_integration_pack/task_routing_rules.md').read_text()
    assert anchor not in (PROJECT_ROOT/'SKILL.md').read_text()


@pytest.mark.parametrize('path',['tests/simulation_cases.py','tests/simulation_host_contracts.py','tests/v115-cohort.json','tests/fixtures/simulation_lab/README.md','docs/update-plan-v1.0.16.md'])
def test_simulation_evaluation_is_not_runtime_context(path):
    with pytest.raises((ValueError,OSError)):read_context(ROOT,path,None)


def test_plan_bytes_source_strength_and_current_preconditions():
    raw=(ROOT/'docs/update-plan-v1.0.16.md').read_bytes();meta=json.loads((ROOT/'docs/v1.0.16-plan-source.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==meta['sha256'] and len(raw)==meta['bytes']
    assert meta['skill_predecessor']=='75b3dacdcb5e567c86c7ae6e97bcb248b6f46fc3'
    assert 'PENDING' in meta['test_publication']
    sources=json.loads((ROOT/'docs/v1.0.16-sources.json').read_text())
    assert sources['window']==['2026-08-10','2026-11-07']
    rows={s['id']:s for s in sources['sources']}
    assert len(rows)==14
    for key in ('S1','S2','S3','S7','S8','S9','S11','S14'):
        assert re.fullmatch('[0-9a-f]{40}',rows[key]['revision']) and re.fullmatch('[0-9a-f]{64}',rows[key]['sha256'])
    assert rows['S2']['commit_date'].startswith('2026-10-20') and rows['S2']['reported_measurement_date']=='2026-10-21'
    assert rows['S4']['year']==2016 and rows['S5']['year']==2019
    mapping=(ROOT/'docs/v1.0.16-requirement-map.md').read_text()
    assert all(s in mapping for s in ['C1','C2','C3','C4','UNIMPLEMENTED','NOT_RUN','104','120'])
