import sys,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
pytestmark=pytest.mark.candidate19
from tools import upload_choice19 as r
FIX=Path(__file__).parent/'fixtures/upload-choice19.json'
def rows(name='baseline'):return json.loads(FIX.read_text())[name]
def pair():return r.check(rows(),'direct'),r.check(rows('staging'),'staging')
def test_original_positive():
 d,s=pair();assert d['requested_bytes']==512 and s['requested_bytes']==768
 assert d==r.check(rows('recovery'),'direct')
 assert r.check(rows('direct-wrong'),'direct',True)['output']==d['output']
 assert r.check(rows('staging-wrong'),'staging',True)['output']==d['output']
@pytest.mark.parametrize('kind,key,value',[
 ('identity','deviceType',2),('identity','maxLocalX',1),('identity','layerSpec',0),
 ('allocation','typeBits',0),('allocation','requestedBytes',128),('allocation','mapped',False),('allocation','flags',1),('allocation','usage',34),('allocation','heapSize',1),('allocation','bindOffset',16),
 ('dependency','dstAccess',0),('dependency','size',128),('dispatch','groups',[2,1,1]),('result','fenceCompleted',False),('result','requestedBytesTotal',1024),('result','errors',1),('readback','mismatches',1)])
def test_coordinate_mutation(kind,key,value):
 x=rows();r.check(x,'direct');next(z for z in x if z['kind']==kind)[key]=value
 with pytest.raises(ValueError):r.check(x,'direct')
def test_output_and_input_oracle():
 for kind in ('input','readback'):
  x=rows();next(z for z in x if z['kind']==kind)['values'][31]+=1
  with pytest.raises(ValueError):r.check(x,'direct')
def test_copy_must_match():
 x=rows('staging');next(z for z in x if z['kind']=='copy')['bytes']=128
 with pytest.raises(ValueError):r.check(x,'staging')
def test_omitted_extra_records():
 x=rows()
 for y in (x[:-1],x+[x[-1]]):
  with pytest.raises(ValueError):r.check(y,'direct')
@pytest.mark.parametrize('budget,status',[(0,'NO_ADMISSIBLE_PATH'),(511,'NO_ADMISSIBLE_PATH'),(512,'KEEP_BASELINE'),(767,'KEEP_BASELINE'),(768,'KEEP_BASELINE')])
def test_actual_budget(budget,status):assert r.decide(*pair(),budget)['status']==status
def test_no_performance_claim():assert r.decide(*pair(),1000,True)['status']=='NEEDS_MEASUREMENT'
@pytest.mark.parametrize('budget',[True,-1,2**63,None])
def test_bad_budget(budget):assert r.decide(*pair(),budget)['status']=='UNKNOWN'
def test_different_device_no_comparison():
 d,s=pair();s['identity']['driver']+=1;assert r.decide(d,s,1000)['status']=='UNKNOWN'

@pytest.mark.parametrize('field',['output','identity'])
def test_incomplete_evidence(field):
 d,s=pair();del s[field];assert r.decide(d,s,1000)['status']=='UNKNOWN'
def test_boolean_final():
 x=rows();x[-1]['errors']=False
 with pytest.raises(ValueError):r.check(x,'direct')
def test_record_wrong_shape():
 with pytest.raises(ValueError):r.check([None],'direct')

def test_absolute_symlink_entry_sources():
 import importlib.util
 root=Path(__file__).resolve().parents[1]
 path=Path('/tmp/vulkan119-tests/cases19/upload_choice/run.py')
 if not path.exists():pytest.skip('local compatibility symlink absent')
 spec=importlib.util.spec_from_file_location('upload_symlink_entry',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 assert all(p.is_absolute() and p==p.resolve() and p.is_relative_to(root) for p in m.source_paths())

@pytest.mark.parametrize('kind,key,value', [('dependency','size',256.0),('allocation','index',False),('readback','mismatches',False),('dispatch','groups',[True,True,True]),('identity','vendor',2**32),('allocation','flags',2**32)])
def test_strict_raw_types(kind,key,value):
 x=rows();r.check(x,'direct');next(v for v in x if v['kind']==kind)[key]=value
 with pytest.raises(ValueError):r.check(x,'direct')
def test_wrong_parameter_type():
 with pytest.raises(ValueError):r.check(rows(),'direct',0)
