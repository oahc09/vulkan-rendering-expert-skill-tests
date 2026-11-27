import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import render_organization19 as r
pytestmark=pytest.mark.candidate19
F=json.loads((ROOT/'tests/fixtures/render-organization19.json').read_text())
def test_full_baseline():
 for label,path,wrong in [('baseline','renderpass',False),('dynamic','dynamic',False),('recovery','renderpass',False),('renderpass-wrong','renderpass',True),('dynamic-wrong','dynamic',True)]:r.check(F[label],path,wrong)
 assert r.check(F['baseline'],'renderpass')==r.check(F['recovery'],'renderpass')
@pytest.mark.parametrize('kind,key,value',[('organization','renderPassObjects',0),('manifest','enabled',1),('manifest','samples',4),('renderpass_attachment','finalLayout',6),('execution','fenceCompleted',False),('execution','pixels',[[0]*4]*16),('image_dependency','dstAccess',0),('host_dependency','srcStage',1),('pipeline','format',44),('identity','deviceType',2),('final','errors',True),('buffer_allocation','selectedType',False),('limits','framebufferWidth',float('inf')),('identity','driverVersion',10**1000)])
def test_tamper(kind,key,value):
 r.check(F['baseline'],'renderpass');rows=copy.deepcopy(F['baseline']);next(x for x in rows if x['kind']==kind)[key]=value
 with pytest.raises(ValueError):r.check(rows,'renderpass')
@pytest.mark.parametrize('budget,status,selected',[(1,'KEEP_BASELINE','renderpass'),(0,'SELECT_ONLY_POLICY_ADMISSIBLE_PATH','dynamic')])
def test_policy(budget,status,selected):
 a=r.decide(F['baseline'],F['dynamic'],budget);assert (a['status'],a['selected'])==(status,selected)
def test_unknown_performance():assert r.decide(F['baseline'],F['dynamic'],1,True)['status']=='NEEDS_MEASUREMENT'
@pytest.mark.parametrize('bad',[None,{},[],{'status':'PASS'}])
def test_no_fake_receipt(bad):assert r.decide(bad,F['dynamic'])['status']=='UNKNOWN'
def test_reordered():
 rows=copy.deepcopy(F['baseline']);rows[0],rows[1]=rows[1],rows[0]
 with pytest.raises(ValueError):r.check(rows,'renderpass')
def test_asymmetry():
 a=r.reference();assert a!=[a[x*4+y] for y in range(4) for x in range(4)];assert a!=list(reversed(a))
def test_resolved_source_paths():
 import importlib.util
 spec=importlib.util.spec_from_file_location('render_org_run',ROOT/'cases19/render_organization/run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 assert all(p==p.resolve() and p.is_relative_to(ROOT) for p in m.source_paths())
def test_legacy_does_not_require_dynamic_support():
 rows=copy.deepcopy(F['baseline']);next(x for x in rows if x['kind']=='manifest')['supported']=0
 r.check(rows,'renderpass')
def test_dynamic_requires_supported():
 rows=copy.deepcopy(F['dynamic']);next(x for x in rows if x['kind']=='manifest')['supported']=0
 with pytest.raises(ValueError):r.check(rows,'dynamic')
def test_image_memory_identity():
 rows=copy.deepcopy(F['baseline']);next(x for x in rows if x['kind']=='manifest')['memoryFlags']=0
 with pytest.raises(ValueError):r.check(rows,'renderpass')
