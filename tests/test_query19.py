import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
from tools.query19 import layout,consume,write_admission,query_range

def base():
 i=dict(run='r',device='d',pool='p',queue='q',generation=1)
 return dict(identity=i,observation={**i,'reset_completed':True,'writes_completed':True,'values':[250,4],'availability':[1,1]},valid_bits=8,period_ns=2,same_clock=True,upper_bound_ns=30,result_width=64)
def test_wrap():assert consume(**base())['nanoseconds']==20
@pytest.mark.parametrize('key,val,status',[('same_clock',False,'UNKNOWN_CLOCK'),('upper_bound_ns',None,'UNKNOWN_WRAP'),('upper_bound_ns',512,'UNKNOWN_WRAP'),('upper_bound_ns',10,'INCONSISTENT_BOUND'),('valid_bits',0,'UNSUPPORTED')])
def test_limits(key,val,status):
 x=base();x[key]=val;assert consume(**x)['status']==status
@pytest.mark.parametrize('key,val',[('run','old'),('device','other'),('pool','other'),('queue','other'),('generation',0)])
def test_stale(key,val):
 x=base();x['observation'][key]=val;assert consume(**x)['status']=='STALE_OR_DIFFERENT_SCOPE'
@pytest.mark.parametrize('key,val',[('reset_completed',False),('writes_completed',False),('availability',[1,0])])
def test_notready(key,val):
 x=base();x['observation'][key]=val;assert consume(**x)['status']=='NOT_READY'
@pytest.mark.parametrize('key,val',[('valid_bits',True),('valid_bits',65),('period_ns',float('nan')),('period_ns',False)])
def test_bad(key,val):
 x=base();x[key]=val
 with pytest.raises(ValueError):consume(**x)
@pytest.mark.parametrize('w,stride,size,avail,partial,ids',[(64,16,32,True,False,[]),(32,8,16,True,False,[]),(64,17,40,True,False,['flags-00815']),(64,16,24,True,False,['dataSize-00817']),(64,16,32,True,True,['queryType-09439']),(64,8,24,True,False,['stride-08993']),(32,5,16,False,False,['flags-02828'])])
def test_layout(w,stride,size,avail,partial,ids):assert layout(width=w,count=2,stride=stride,data_size=size,availability=avail,partial=partial)['vuids']==['VUID-vkGetQueryPoolResults-'+x for x in ids]
@pytest.mark.parametrize('key,value,suffix',[('valid_bits',0,'timestampValidBits-00829'),('pool_type','occlusion','queryPool-01416'),('query',2,'query-04904'),('reset_executed',False,'None-00830'),('already_written',True,'None-00830'),('stage_supported',False,'pipelineStage-04074')])
def test_write(key,value,suffix):
 x=dict(valid_bits=64,pool_type='timestamp',pool_count=2,query=0,reset_executed=True,already_written=False,stage_supported=True);assert write_admission(**x)['status']=='WRITE_WITHIN_SCOPE';x[key]=value;assert write_admission(**x)['vuids']==['VUID-vkCmdWriteTimestamp-'+suffix]

def test_32_decode_unknown():
 x=base();x['result_width']=32;assert consume(**x)['status']=='UNKNOWN_32BIT_REPRESENTATION'

@pytest.mark.parametrize('first,count,ids',[(0,2,[]),(1,1,[]),(1,2,['firstQuery-09437']),(2,1,['firstQuery-09436','firstQuery-09437'])])
def test_range(first,count,ids):assert query_range(pool_count=2,first_query=first,count=count)['vuids']==['VUID-vkGetQueryPoolResults-'+x for x in ids]
def test_zero_range_unknown():assert query_range(pool_count=2,first_query=0,count=0)['status']=='UNKNOWN'
def test_wide_result():
 x=base();x['observation']['values'][0]=1<<64
 with pytest.raises(ValueError):consume(**x)
def test_unknown_type():assert write_admission(valid_bits=64,pool_type='unknown',pool_count=2,query=0,reset_executed=True,already_written=False,stage_supported=True)['status']=='UNKNOWN'
@pytest.mark.parametrize('k',['valid_bits','period_ns'])
def test_missing_capability(k):
 x=base();x[k]=None;assert consume(**x)['status']=='UNKNOWN'

def test_recorded_actual_cohort_is_source_paired():
 import json,hashlib
 root=pathlib.Path(__file__).resolve().parents[1]
 report=json.loads((root/'coverage/v1.0.19/query-timestamp.json').read_text())
 for key,path in [('source_sha256','cases19/query_timestamp/probe.c'),('runner_sha256','cases19/query_timestamp/run.py'),('rules_sha256','tools/query19.py')]:
  assert report[key]==hashlib.sha256((root/path).read_bytes()).hexdigest()
 assert report['status']=='BOUNDED_QUERY_LIFECYCLE_PASS'
 assert report['spec_version']['api version']=='1.4.309'
 assert report['spec_sha256']=='f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'
 assert set(report['cases'])=={'good','stride','size','partial'}
 for mode,case in report['cases'].items():
  assert case['records']['unwritten']['result']==1
  assert case['records']['unwritten']['availability']==[0,0]
  assert case['records']['fill']['words']==1024
  assert case['interpretation']['status']=='UNKNOWN_WRAP'
  assert case['records']['identity']['deviceType']==4
  if mode!='good':
   assert case['records']['negative']['result']==-1000011001
   assert case['normative']['vuid'] in case['layout_rules']['vuids']
 # This is a retained-record/source contract, not a fresh device invocation.
