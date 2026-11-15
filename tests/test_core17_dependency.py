"""Synthetic dependency negatives, not six-partial semantic certification."""
import hashlib,json,subprocess
from pathlib import Path
import pytest
import run_core17_dependency as gate
pytestmark=pytest.mark.host_unit

def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True).strip()
def commit(p):
 git(p,'add','.');git(p,'-c','user.name=Fixture','-c','user.email=f@example.invalid','commit','-qm','fixture');return git(p,'rev-parse','HEAD')
@pytest.fixture
def pair(tmp_path):
 skill=tmp_path/'skill';tests=tmp_path/'tests'
 for p in (skill,tests):p.mkdir();git(p,'init','-q');(p/'base').write_text('base')
 skillsha=commit(skill);base=commit(tests)
 c=gate.manifest();c.update(skill_sha=skillsha,tests_base_sha=base)
 contract={k:c[k] for k in ('skill_sha','tests_base_sha','release_status','equivalent_reuse','partial_legacy_links')};contract['candidate_version']='1.0.17-reconstructed-tests'
 (tests/'core17-candidate-contract.json').write_text(json.dumps(contract));(tests/'tests').mkdir();(tests/'tests/run_versioned_gate.py').write_text('raise SystemExit(0)\n')
 c['tests_sha']=commit(tests)
 for name,key in [('core17-candidate-contract.json','contract_sha256'),('tests/run_versioned_gate.py','gate_sha256')]:c[key]=hashlib.sha256((tests/name).read_bytes()).hexdigest()
 return skill,tests,c

def test_independent_clean_pair_keeps_partial_and_blocked(pair):
 s,t,c=pair;r=gate.inspect(s,t,c)
 assert r['pair_status']=='PASS' and r['release_status']=='BLOCKED' and r['equivalent_reuse']==0 and r['partial_legacy_links']==6
@pytest.mark.parametrize('repo',['skill','tests'])
def test_wrong_heads(pair,repo):
 s,t,c=pair;p=s if repo=='skill' else t;(p/'extra').write_text('extra');commit(p)
 with pytest.raises(ValueError,match='wrong exact'):gate.inspect(s,t,c)
@pytest.mark.parametrize('name',['core17-candidate-contract.json','tests/run_versioned_gate.py'])
def test_committed_source_tamper(pair,name):
 s,t,c=pair;(t/name).write_text('tampered');c['tests_sha']=commit(t)
 with pytest.raises(ValueError,match='digest'):gate.inspect(s,t,c)
@pytest.mark.parametrize('flag',['--assume-unchanged','--skip-worktree'])
def test_hidden_index(pair,flag):
 s,t,c=pair;git(t,'update-index',flag,'base');(t/'base').write_text('hidden')
 with pytest.raises(ValueError,match='hidden'):gate.inspect(s,t,c)
def test_dirty_ignores_show_untracked_setting(pair):
 s,t,c=pair;git(s,'config','status.showUntrackedFiles','no');(s/'dirty').write_text('dirty')
 with pytest.raises(ValueError,match='dirty'):gate.inspect(s,t,c)
def test_unrelated_ancestor(pair):
 s,t,c=pair;head=c['tests_sha'];git(t,'checkout','-q','--orphan','other');(t/'other').write_text('other');c['tests_base_sha']=commit(t);git(t,'checkout','-q',head)
 with pytest.raises(ValueError,match='ancestry'):gate.inspect(s,t,c)
def test_missing_ancestor(pair):
 s,t,c=pair;c['tests_base_sha']='1'*40
 with pytest.raises(subprocess.CalledProcessError):gate.inspect(s,t,c)
@pytest.mark.parametrize('field,value',[('release_status','PASS'),('equivalent_reuse',6),('partial_legacy_links',0),('tests_sha','main'),('cohort','text18')])
def test_manifest_cannot_upgrade_scope(tmp_path,field,value):
 c=gate.manifest();c[field]=value;p=tmp_path/'manifest.json';p.write_text(json.dumps(c))
 with pytest.raises(ValueError):gate.manifest(p)
def test_workflow_adds_independent_job_not_replacement():
 import yaml
 w=yaml.safe_load((gate.MANIFEST.parent/'.github/workflows/test-skill-branch.yml').read_text());assert w['jobs']['pytest']['strategy']['matrix']['cohort']==['legacy16','text18']
 j=w['jobs']['core17-dependency'];steps=j['steps'];assert any('run_core17_dependency.py' in s.get('run','') and '--tests core17-tests --skill core17-skill' in s['run'] for s in steps)
 checkouts=[s for s in steps if s.get('uses')=='actions/checkout@v4'];assert len(checkouts)==3 and all(s['with']['persist-credentials'] is False and s['with']['fetch-depth']==0 for s in checkouts)
 assert w['permissions']=={'contents':'read'}
def test_original_contract_scope_mismatch_even_with_matching_digest(pair):
 s,t,c=pair;p=t/'core17-candidate-contract.json';v=json.loads(p.read_text());v['equivalent_reuse']=6;p.write_text(json.dumps(v));c['tests_sha']=commit(t);c['contract_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 with pytest.raises(ValueError,match='contract mismatch'):gate.inspect(s,t,c)
@pytest.mark.parametrize('exit_code',[0,1])
def test_gate_result_never_upgrades_release(pair,tmp_path,monkeypatch,exit_code):
 s,t,c=pair;p=t/'tests/run_versioned_gate.py';p.write_text('# distinct execution fixture\nraise SystemExit('+str(exit_code)+')\n');c['tests_sha']=commit(t);c['gate_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();monkeypatch.setattr(gate,'manifest',lambda:c)
 output=tmp_path/'result.json';assert gate.main(['--tests',str(t),'--skill',str(s),'--output',str(output)])==exit_code
 r=json.loads(output.read_text());assert r['release_status']=='BLOCKED' and r['semantic_acceptance']=='UNVERIFIED' and not r['merged_into_text18']
 assert r['status']==('DEPENDENCY_STATIC_PAIR_PASS' if exit_code==0 else 'DEPENDENCY_STATIC_PAIR_FAIL')
