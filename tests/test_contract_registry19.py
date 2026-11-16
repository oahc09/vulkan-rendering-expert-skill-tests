import copy,importlib.util,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from tools import contract_registry19 as r
ROOT=Path(__file__).resolve().parents[1]
pytestmark=pytest.mark.candidate19

def test_fixed_registry():
 m=r.parse((ROOT/'tests/fixtures/contract-registry19.json').read_bytes());actual=r.scan(ROOT)
 assert sum(len(x['entries']) for x in actual.values())==23
 for family,f in actual.items():
  assert f['source_sha256']==m['families'][family]['source_sha256']
  assert f['excluded_helpers']==m['families'][family]['excluded_helpers']
  assert all(m['families'][family]['entries'][n]['controls'] for n in f['entries'])
 assert sum(x['case_count'] for x in m['families'].values())==125

def test_duplicate_json_rejected():
 with pytest.raises(ValueError,match='duplicate'):r.parse('{"a":1,"a":2}')

def test_ast_source_change(tmp_path):
 import shutil
 (tmp_path/'tools').mkdir()
 for family in r.FUNCTIONS:shutil.copyfile(ROOT/f'tools/{family}_contract19.py',tmp_path/f'tools/{family}_contract19.py')
 m=r.parse((ROOT/'tests/fixtures/contract-registry19.json').read_bytes());p=tmp_path/'tools/sync_contract19.py';p.write_text(p.read_text()+'\ndef new_unregistered(x):return x\n')
 with pytest.raises(ValueError,match='unregistered'):r.scan(tmp_path)
 with pytest.raises(ValueError,match='unregistered'):r.verify(m,tmp_path,Path('/tmp/vulkan119-skill'))

def test_report_content_not_status(monkeypatch):
 original={'case_count':1,'cases':[{'name':'negative','result':{'status':'REJECTED'}}],'semantic_completion':'UNKNOWN_NOT_INFERRED','release_status':'BLOCKED'}
 snapshot={'families':{'sync':{'report_sha256':r.digest(original)}}}
 monkeypatch.setattr(r,'replay',lambda *a:(copy.deepcopy(original),[{}]))
 assert r.verify_report(snapshot,'sync',original,None,b'')['cases']==1
 for kind in ('missing-case','pass-spoof','promote','wrong-diagnostic'):
  changed=copy.deepcopy(original)
  if kind=='missing-case':changed['cases']=[]
  elif kind=='pass-spoof':changed['status']='PASS'
  elif kind=='promote':changed['semantic_completion']='COMPLETE'
  else:changed['cases'][0]['result']['status']='ACCEPTED'
  with pytest.raises(ValueError,match='content mismatch'):r.verify_report(snapshot,'sync',changed,None,b'')

def test_replay_restores_functions_on_source_failure(tmp_path):
 from checks19 import run_sync_contracts as c
 original=c.rule.evaluate
 with pytest.raises(FileNotFoundError):r.replay('sync',tmp_path,b'')
 assert c.rule.evaluate is original
@pytest.mark.parametrize('mutation',['precondition','control','version'])
def test_full_rebuild_rejects_metadata(mutation,monkeypatch):
 original=r.parse((ROOT/'tests/fixtures/contract-registry19.json').read_bytes());monkeypatch.setattr(r,'build_manifest',lambda *a:copy.deepcopy(original))
 assert r.verify_rebuilt(original,None,None,None,b'')['status']=='EXACT_23_ENTRY_MANIFEST_REBUILT'
 changed=copy.deepcopy(original)
 if mutation=='precondition':changed['families']['memory_binding']['entries']['free_obligations']['preconditions']=[]
 elif mutation=='control':changed['families']['sync']['entries']['evaluate']['controls'].pop()
 else:changed['families']['layout']['normative_309_source']['api_version']='1.4.368'
 with pytest.raises(ValueError,match='full frozen'):r.verify_rebuilt(changed,None,None,None,b'')
