"""Exact fixed Skill pairing; does not certify gates K/B/P."""
import json,subprocess
from pathlib import Path
from conftest import PROJECT_ROOT
ROOT=Path(__file__).parents[1]
def test_exact_skill_and_base_contract():
    c=json.loads((ROOT/'core17-candidate-contract.json').read_text())
    assert subprocess.check_output(['git','-C',str(PROJECT_ROOT),'rev-parse','HEAD'],text=True).strip()==c['skill_sha']
    assert c['release_status']=='BLOCKED' and c['new_prompts']==24 and c['equivalent_reuse']==0
    subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',c['tests_base_sha'],'HEAD'],check=True)
def test_independent_old_release_contract_not_relabelled():
    c=json.loads((ROOT/'release-contract.json').read_text())
    assert c['expected_version']=='1.0.16'
    assert c['skill_sha']=='416f4a6c0c887dee72bcc6dca13ce9c857d7957f'
def test_private_rubric_refused_as_runtime_context():
    import pytest
    from run_live_model_behavior import read_context
    with pytest.raises((ValueError,OSError)):
        read_context(ROOT,'tests/core17_rubrics.json',None)

def test_core17_version_and_preserved_routing():
    import re
    skill=(PROJECT_ROOT/'SKILL.md').read_text()
    assert re.search(r'^\s*version:\s*1\.0\.17\s*$',skill,re.M)
    assert 'task_routing_rules.md' in skill
    routing=(PROJECT_ROOT/'references/07_integration_pack/task_routing_rules.md').read_text()
    assert 'project_diagnosis.md' in routing
    workflow=(PROJECT_ROOT/'references/05_workflows/01_renderer_setup/project_diagnosis.md').read_text()
    assert '[CODE]' in workflow and 'Architecture Map' in workflow

def test_core17_reproducible_package_and_unchanged_knowledge_budget(tmp_path):
    import importlib.util,sys,hashlib
    c=json.loads((ROOT/'core17-candidate-contract.json').read_text())
    old=json.loads((ROOT/'release-contract.json').read_text())
    sys.path.insert(0,str(PROJECT_ROOT/'scripts'))
    try:
        spec=importlib.util.spec_from_file_location('core17_packer',PROJECT_ROOT/'scripts/agensi_audit_and_pack.py')
        packer=importlib.util.module_from_spec(spec);spec.loader.exec_module(packer)
        a=packer.check(PROJECT_ROOT,tmp_path/'a.zip');b=packer.check(PROJECT_ROOT,tmp_path/'b.zip')
    finally:sys.path.pop(0)
    assert a['status']==b['status']=='PASS' and a['revision']==b['revision']==c['skill_sha']
    assert (tmp_path/'a.zip').read_bytes()==(tmp_path/'b.zip').read_bytes()
    tracked=set(subprocess.check_output(['git','-C',str(PROJECT_ROOT),'ls-files'],text=True).splitlines())
    packaged={item['path'] for item in a['files']}
    assert a['tracked_files']==len(tracked)
    assert a['package_files']==len(packaged)<=old['max_runtime_files']
    assert packaged=={p for p in tracked if p in packer.REQUIRED or p.startswith('references/')}
    assert a['zip']['crc_verified'] and b['zip']['crc_verified']
    baseline=set(subprocess.check_output(['git','-C',str(PROJECT_ROOT),'ls-tree','-r','--name-only',old['knowledge_baseline_sha']],text=True).splitlines())
    assert {p for p in tracked if p.startswith('references/')}=={p for p in baseline if p.startswith('references/')}|set(old['allowed_new_knowledge'])
