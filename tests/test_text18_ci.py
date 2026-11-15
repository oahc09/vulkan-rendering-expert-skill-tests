"""Fail-closed cohort orchestration negatives, not model or GPU acceptance."""
import json,subprocess
from pathlib import Path
import pytest
import run_text18_versioned_gate as gate

@pytest.mark.parametrize('cohort,version',[('legacy16','1.0.16'),('text18','1.0.18')])
def test_manifest_resolution_rejects_mutable_sha(tmp_path,cohort,version):
    f='release-contract.json' if cohort=='legacy16' else 'text18-candidate-contract.json'
    data={'skill_sha':'main','candidate_version':version,'release_status':'BLOCKED'}
    (tmp_path/f).write_text(json.dumps(data))
    with pytest.raises(ValueError,match='immutable'):gate.select(cohort,tmp_path)

@pytest.mark.parametrize('bad',['1.0.19','1.0.16','1.0.17'])
def test_wrong_core_contract_version_rejected(tmp_path,bad):
    (tmp_path/'text18-candidate-contract.json').write_text(json.dumps({'skill_sha':'a'*40,'candidate_version':bad,'release_status':'BLOCKED'}))
    with pytest.raises(ValueError,match='wrong cohort'):gate.select('text18',tmp_path)

def test_claimed_release_pass_rejected(tmp_path):
    (tmp_path/'text18-candidate-contract.json').write_text(json.dumps({'skill_sha':'a'*40,'candidate_version':'1.0.18','release_status':'PASS'}))
    with pytest.raises(ValueError,match='not certified'):gate.select('text18',tmp_path)

def test_no_implicit_cohort_fallback():
    with pytest.raises(ValueError):gate.test_args('latest')
    assert all(f'--ignore={gate.ROOT}/tests/{f}' in gate.test_args('legacy16') for f in gate.CORE_FILES)
    assert all(f'--deselect={node}' in gate.test_args('text18') for node in gate.LEGACY_PIN_ONLY)
    assert not any('--deselect' in arg for arg in gate.test_args('legacy16'))

@pytest.mark.parametrize('failure',['wrong','dirty','hidden'])
def test_pair_guards_reject_before_pytest(monkeypatch,tmp_path,failure):
    sha=gate.select('text18')
    def output(args,**kwargs):
        if 'rev-parse' in args:return ('b'*40 if failure=='wrong' else sha)+'\n'
        if 'status' in args:return '?? rogue\n' if failure=='dirty' else ''
        if 'ls-files' in args:return 'h tracked\n' if failure=='hidden' else 'H tracked\n'
        raise AssertionError(args)
    monkeypatch.setattr(subprocess,'check_output',output)
    with pytest.raises(ValueError):gate.check_pair('text18',tmp_path)

def test_workflow_has_explicit_two_pins_and_no_write_permissions():
    import yaml
    w=yaml.safe_load((gate.ROOT/'.github/workflows/test-skill-branch.yml').read_text())
    j=w['jobs']['pytest']
    assert j['strategy']['matrix']['cohort']==['legacy16','text18']
    assert w['permissions']=={'contents':'read'}
    assert any('run_text18_versioned_gate.py' in s.get('run','') and '--resolve' in s['run'] for s in j['steps'])
    assert any('run_text18_versioned_gate.py' in s.get('run','') and '--skill' in s['run'] for s in j['steps'])

@pytest.mark.parametrize('cohort',['legacy16','text18'])
def test_actual_collection_keeps_only_the_intended_version_scope(cohort):
    import sys,os
    from conftest import PROJECT_ROOT
    p=subprocess.run([sys.executable,'-m','pytest','--collect-only','-q','-c',str(gate.ROOT/'tests/pytest.ini'),*gate.test_args(cohort)],capture_output=True,text=True,timeout=60,env=dict(os.environ,VULKAN_SKILL_ROOT=str(PROJECT_ROOT)))
    assert p.returncode==0,p.stdout+p.stderr
    selected=set(line.strip() for line in p.stdout.splitlines() if '::test_' in line)
    assert selected
    assert not any(node.startswith('test_core17_pair.py::') for node in selected)
    for node in gate.LEGACY_PIN_ONLY:assert (node in selected)==(cohort=='legacy16')
    assert 'test_v1_0_8_project_diagnosis.py::test_project_diagnosis_workflow_exists_and_follows_template' in selected
    assert 'test_v1_0_9_regression.py::test_registered_cases_and_rubrics' in selected
    assert ('test_text18_package_pair.py::test_text18_reproducible_package_and_unchanged_knowledge_budget' in selected)==(cohort=='text18')

@pytest.mark.parametrize('cohort', ['legacy16','text18'])
def test_other_version_contracts_are_isolated(cohort):
    assert all(f'--ignore={gate.ROOT}/tests/{f}' in gate.test_args(cohort) for f in gate.OTHER_VERSION_FILES)
