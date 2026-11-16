import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
pytestmark=pytest.mark.candidate19
from tools import binding_choice19 as r
FIX=Path(__file__).parent/'fixtures/binding-choice19.json'
def rows(label='baseline'):return json.loads(FIX.read_text())[label]
def rawpair():return rows(),rows('push')
def pair():return r.check(rows(),'set'),r.check(rows('push'),'push')
def test_positive_two_generations():
 s,p=pair();assert s['generations']==p['generations']
 assert s==r.check(rows('recovery'),'set')
 assert s['cost']['descriptorSetAllocations']==1 and s['cost']['bindCalls']==2 and p['cost']['pushCalls']==2
 assert s['generations'][0]['output']!=s['generations'][1]['output']
 assert r.check(rows('set-wrong'),'set',True)['generations']==s['generations']
 assert r.check(rows('push-wrong'),'push',True)['generations']==p['generations']
@pytest.mark.parametrize('key,value',[('pushSupported',False),('pushEnabled',False),('layoutFlags',0),('maxPushDescriptors',1),('descriptorCount',1),('maxPushDescriptors',True)])
def test_push_support_enable_configuration(key,value):
 x=rows('push');r.check(x,'push');x[1][key]=value
 with pytest.raises(ValueError):r.check(x,'push')
@pytest.mark.parametrize('key,value',[('descriptorSetAllocations',2),('updateCalls',2),('bindCalls',False),('dispatches',1)])
def test_counts(key,value):
 x=rows();x[-1][key]=value
 with pytest.raises(ValueError):r.check(x,'set')
def test_generation_retirement():
 x=rows();x[11]['priorFenceCompleted']=False
 with pytest.raises(ValueError):r.check(x,'set')
def test_generation_wrong_oracle():
 for gen in (0,1):
  x=rows();x[4+7*gen+5]['values'][24]+=1
  with pytest.raises(ValueError):r.check(x,'set')
def test_input_changed():
 x=rows();x[12]['values'][0]=3
 with pytest.raises(ValueError):r.check(x,'set')
def test_pending_fence():
 x=rows();x[17]['fenceCompleted']=False
 with pytest.raises(ValueError):r.check(x,'set')
def test_missing_generation():
 with pytest.raises(ValueError):r.check(rows()[:-8]+[rows()[-1]],'set')
@pytest.mark.parametrize('budget,expected,selection',[(0,'SELECT_ONLY_POLICY_ADMISSIBLE_PATH','push'),(1,'KEEP_BASELINE','set'),(2,'KEEP_BASELINE','set')])
def test_explicit_allocation_policy(budget,expected,selection):
 d=r.decide(*rawpair(),budget);assert (d['status'],d['selected'])==(expected,selection)
def test_no_performance_claim():assert r.decide(*rawpair(),0,True)['status']=='NEEDS_MEASUREMENT'
def test_push_unavailable_fallback():
 s=rows();assert r.decide(s,None,1)['selected']=='set';assert r.decide(s,None,0)['status']=='NO_ADMISSIBLE_PATH'
@pytest.mark.parametrize('bad',[True,-1,2**32,None])
def test_invalid_budget(bad):assert r.decide(*rawpair(),bad)['status']=='UNKNOWN'
def test_other_device():
 s,p=rawpair();p[0]['driver']+=1;assert r.decide(s,p,1)['status']=='UNKNOWN'
def test_absolute_symlink_sources():
 import importlib.util
 path=Path('/tmp/vulkan119-tests/cases19/binding_choice/run.py')
 if not path.exists():pytest.skip('local alias absent')
 spec=importlib.util.spec_from_file_location('binding_runner',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 assert all(p==p.resolve() and p.is_relative_to(Path(__file__).resolve().parents[1]) for p in m.source_paths())

def test_fake_verified_summary_rejected():
 x={'status':'BINDING_PATH_VERIFIED','path':'set'}
 assert r.decide(x,None,1)['status']=='UNKNOWN'
def test_missing_push_performance_unknown():
 assert r.decide(rows(),None,1,True)['status']=='NEEDS_MEASUREMENT'
def test_coordinated_false_cost_rejected():
 a,b=rawpair();a[-1]['descriptorSetAllocations']=0
 assert r.decide(a,b,0)['status']=='UNKNOWN'
