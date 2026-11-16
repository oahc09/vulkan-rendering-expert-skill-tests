import ast,copy,hashlib,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import project_patch_replay19 as r
pytestmark=pytest.mark.candidate19
@pytest.fixture(autouse=True)
def synthetic_runtime_paths(monkeypatch):
 # HOST oracle fixtures use this test process's files, not a claimed 3.12 run.
 monkeypatch.setattr(r,'runtime_paths',lambda version:(str(Path(r.PYTHONS['312'][0]).resolve()),{mod.__name__:str(Path(mod.__file__).resolve()) for mod in (ast,json,json.encoder,json.decoder,hashlib)}))
def fixture():return json.loads((ROOT/'tests/fixtures/contract-registry19.json').read_text())
def value(mismatch=False):
 f=fixture();m=copy.deepcopy(f)
 if mismatch:
  for row in m['families'].values():
   for group in ('entries','excluded_helpers'):
    for v in row[group].values():v['ast_sha256']='f'*64
 scan={family:{k:copy.deepcopy(row[k]) for k in ('path','source_sha256','excluded_helpers')} for family,row in m['families'].items()}
 for family,row in m['families'].items():scan[family]['entries']={name:{k:entry[k] for k in ('ast_sha256','signature','docstring')} for name,entry in row['entries'].items()}
 runtime=dict(executable=str(Path(r.PYTHONS['312'][0]).resolve()),executable_sha256=r.PYTHONS['312'][1],stdlib={mod.__name__:dict(path=str(Path(mod.__file__).resolve()),sha256=r.sha(Path(mod.__file__).read_bytes())) for mod in (ast,json,json.encoder,json.decoder,hashlib)})
 return dict(python='3.12.14',scan=scan,manifest=m,fixture_equal=not mismatch,changed_coordinates=sorted(r.diffs(f,m)),semantic_mutation_changes_hash=True,runtime=runtime)
def test_full_positive_and_registered_mismatch():
 f=fixture();assert len(r.ast_paths(f))==44
 assert r.verify_worker(value(),f,False,'3.12.14')=='EXACT_FIXTURE_MATCH'
 assert r.verify_worker(value(True),f,True,'3.12.14')=='BASELINE_AST_MISMATCH_REPRODUCED'
@pytest.mark.parametrize('kind',['pass-string','non-ast','missing-entry','missed-one','scan-tamper','wrong-python','constant-hash','empty-stdlib','untrusted-path','empty-scan-entries','extra-scan-family','scan-path'])
def test_failures_are_not_baseline_reproduction(kind):
 f=fixture();v=value(True);assert r.verify_worker(v,f,True,'3.12.14')
 if kind=='pass-string':v['fixture_equal']=True
 elif kind=='non-ast':v['manifest']['release_status']='PASS'
 elif kind=='missing-entry':v['manifest']['families']['sync']['entries'].pop('evaluate')
 elif kind=='missed-one':v['manifest']['families']['sync']['entries']['evaluate']['ast_sha256']=f['families']['sync']['entries']['evaluate']['ast_sha256']
 elif kind=='scan-tamper':v['scan']['sync']['entries']['evaluate']['ast_sha256']='0'*64
 elif kind=='wrong-python':v['python']='3.12.99'
 elif kind=='constant-hash':v['semantic_mutation_changes_hash']=False
 elif kind=='empty-stdlib':v['runtime']['stdlib']={}
 elif kind=='untrusted-path':v['runtime']['stdlib']['ast']['path']='/not/authorized/private'
 elif kind=='empty-scan-entries':v['scan']['sync']['entries']={}
 elif kind=='extra-scan-family':v['scan']['extra']=copy.deepcopy(v['scan']['sync'])
 else:v['scan']['sync']['path']='tools/other.py'
 with pytest.raises(ValueError):r.verify_worker(v,f,True,'3.12.14')
@pytest.mark.parametrize('kind',['base','candidate','digest','paths'])
def test_registration_rejects(kind):
 base,candidate,digest,allowed=r.BASE,r.CANDIDATE,r.PATCH_SHA,r.ALLOWED
 if kind=='base':base='0'*40
 elif kind=='candidate':candidate='0'*40
 elif kind=='digest':digest='0'*64
 else:allowed=['../../secret']
 with pytest.raises(ValueError):r.patch(ROOT,base,candidate,digest,allowed)
def test_real_registered_diff_and_non_ast_fixture_invariance():
 try:p=r.patch(ROOT,r.BASE,r.CANDIDATE,r.PATCH_SHA,r.ALLOWED)
 except __import__('subprocess').CalledProcessError:pytest.skip('historical Git objects unavailable in shallow checkout')
 assert r.sha(p)==r.PATCH_SHA
 a=json.loads(r.git(ROOT,'show',r.BASE+':tests/fixtures/contract-registry19.json'));b=json.loads(r.git(ROOT,'show',r.CANDIDATE+':tests/fixtures/contract-registry19.json'))
 assert sorted(r.diffs(a,b))==r.ast_paths(a)
def test_export_rejects_symlink_blob(tmp_path,monkeypatch):
 monkeypatch.setattr(r,'git',lambda *a:b'120000 blob '+b'a'*40+b'\tlink\n')
 with pytest.raises(ValueError,match='ordinary Git blob'):r.export(tmp_path,r.BASE,['link'],tmp_path/'out')
def test_export_rejects_path_escape(tmp_path):
 with pytest.raises(ValueError,match='export path'):r.export(tmp_path,r.BASE,['../bad'],tmp_path/'out')

def test_extra_import_file_cannot_hide_in_export(tmp_path):
 (tmp_path/'tools').mkdir();(tmp_path/'tools/a.py').write_text('pass\n');expected=r.inventory(tmp_path)
 (tmp_path/'tools/__init__.py').write_text('raise RuntimeError()\n');assert r.inventory(tmp_path)!=expected
 (tmp_path/'tools/__init__.py').unlink();(tmp_path/'tools/hidden.pyc').write_bytes(b'fake');assert r.inventory(tmp_path)!=expected
 (tmp_path/'tools/link').symlink_to(tmp_path/'tools/a.py')
 with pytest.raises(ValueError,match='symlink'):r.inventory(tmp_path)

def test_git_uses_controlled_environment_without_replace(monkeypatch,tmp_path):
 seen={}
 def call(argv,**kw):seen.update(argv=argv,**kw);return b'bytes'
 monkeypatch.setattr(r.subprocess,'check_output',call)
 assert r.git(tmp_path,'show','HEAD:x')==b'bytes'
 assert seen['env']['GIT_NO_REPLACE_OBJECTS']=='1'
 assert seen['env']['GIT_CONFIG_GLOBAL']=='/dev/null'
 assert 'core.fsmonitor=false' in seen['argv']

def test_cli_wrong_project_never_invokes_tools(tmp_path,monkeypatch):
 import importlib.util
 spec=importlib.util.spec_from_file_location('entry',ROOT/'checks19/replay_project_patch.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 def forbidden(*a,**k):raise AssertionError('no tools should run')
 monkeypatch.setattr(m.subprocess,'check_output',forbidden)
 args=['entry']
 for k,v in {'project-root':tmp_path,'skill-root':tmp_path,'docs-root':tmp_path,'validusage':tmp_path/'vu','output':tmp_path/'out','base':r.BASE,'candidate':r.CANDIDATE,'expected-patch-sha256':r.PATCH_SHA,'expected-tests-head':'a'*40,'expected-skill-head':'b'*40,'allowed-path':r.ALLOWED[0]}.items():args+=['--'+k,str(v)]
 monkeypatch.setattr(sys,'argv',args);assert m.main()==2
 report=json.loads((tmp_path/'out/replay-index.json').read_text());assert report['steps']==[] and len(report['pending'])==6
