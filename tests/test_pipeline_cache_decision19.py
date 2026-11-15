import sys,hashlib,struct,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
pytestmark=pytest.mark.candidate19
from tools import pipeline_cache_decision19 as r,pipeline_cache_prose19 as prose

def fixture():
 d=dict(vendor_id=1,device_id=2,driver_version=3,pipeline_cache_uuid='11'*16)
 b=struct.pack('<4I',32,1,1,2)+bytes.fromhex(d['pipeline_cache_uuid'])+b'opaque'
 l=dict(producer='vkGetPipelineCacheData',sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),device=d.copy(),complete_export=True,unmodified=True,source_record_sha256='a'*64)
 return b,d,l
def policy():return dict(baseline_verified=True,candidate_active=True,max_cache_bytes=1000,minimum_first_frame_gain=.05,max_steady_regression=0.,other_objectives_satisfied=True)
def cache():
 b,d,l=fixture();return dict(admission=r.inspect_cache(b,d,l),bytes=len(b))
def measure():
 co={k:'same' for k in ('device','driver','workload','shader','tools','input','resolution','clock_domain','thermal','warmup_protocol','run_order_protocol')}
 return dict(cohort_equal=True,paired_protocol=True,output_equal=True,source_sha256='f'*64,baseline=dict(creation_cpu_ns=[50]*3,first_frame_ns=[100]*3,steady_frame_ns=[40]*3,cohort=co.copy()),candidate=dict(creation_cpu_ns=[20]*3,first_frame_ns=[80]*3,steady_frame_ns=[35]*3,cohort=co.copy()))
def test_good():
 b,d,l=fixture();assert r.inspect_cache(b,d,l)['reuse']
 assert r.decide(cache(),measure(),policy())['status']=='SELECT_DECLARED_PERSISTED_CACHE'
@pytest.mark.parametrize('offset',[0,4,8,12,16])
def test_coordinated_header_tamper(offset):
 b,d,l=fixture();x=bytearray(b);x[offset]^=1;b=bytes(x);l['sha256']=hashlib.sha256(b).hexdigest()
 assert not r.inspect_cache(b,d,l)['reuse']
def test_opaque_hash_not_just_header():
 b,d,l=fixture();assert not r.inspect_cache(b+b'x',d,l)['reuse']
@pytest.mark.parametrize('field',['complete_export','unmodified'])
def test_origin(field):
 b,d,l=fixture();l[field]=False;assert not r.inspect_cache(b,d,l)['reuse']
def test_driver_policy():
 b,d,l=fixture();d['driver_version']=4;assert not r.inspect_cache(b,d,l)['reuse']
def test_untrusted_payload_claim():
 b,d,l=fixture();x=r.inspect_cache(b,d,l);assert x['opaque_payload_validated'] is False
@pytest.mark.parametrize('field',['first_frame_ns','steady_frame_ns'])
def test_fast_creation_does_not_hide_frame_regression(field):
 m=measure();m['candidate'][field]=[200]*3;assert r.decide(cache(),m,policy())['status']=='REVOKE_TO_BASELINE'
def test_no_measured_frames():assert r.decide(cache(),None,policy())['status']=='NEEDS_MEASUREMENT'
def test_unverified_baseline():
 p=policy();p['baseline_verified']=False;assert r.decide(cache(),None,p)['selected'] is None
def test_storage_budget():
 p=policy();p['max_cache_bytes']=0;assert r.decide(cache(),measure(),p)['status']=='REVOKE_TO_BASELINE'
@pytest.mark.parametrize('bad',[True,0,-1,float('nan'),float('inf'),10**1000,1e308,2**63])
def test_invalid_timing(bad):
 m=measure();m['candidate']['first_frame_ns'][0]=bad;assert r.decide(cache(),m,policy())['status']=='NEEDS_MEASUREMENT'
@pytest.mark.parametrize('key',['device','driver','workload','shader','tools','input','resolution','clock_domain','thermal','warmup_protocol','run_order_protocol'])
def test_cohort(key):
 m=measure();m['candidate']['cohort'][key]='changed';assert r.decide(cache(),m,policy())['status']=='NEEDS_MEASUREMENT'
def test_prose():
 p=Path('/workspace/scratch/62d43a81bbde/cts-src/external/vulkan-docs/src/chapters/pipelines.adoc')
 if not p.exists():pytest.skip('fixed source absent')
 assert len(prose.extract(p.read_bytes())['slices'])==4
 with pytest.raises(ValueError):prose.extract(b'changed')

def test_within_path_pairing():
 m=measure();m['candidate']['creation_cpu_ns']=[20]*4;m['baseline']['creation_cpu_ns']=[50]*4
 assert r.decide(cache(),m,policy())['status']=='NEEDS_MEASUREMENT'
def test_trial_bound():
 m=measure();m['candidate']['first_frame_ns']=[20]*4097;assert r.decide(cache(),m,policy())['status']=='NEEDS_MEASUREMENT'
def test_json_duplicate_and_nonfinite():
 from checks19.run_pipeline_cache_cost import read_json
 for raw in ('{"a":1,"a":2}','{"a":NaN}'):
  with pytest.raises(ValueError):read_json(raw)

@pytest.mark.parametrize('field',['creation_cpu_ns','first_frame_ns','steady_frame_ns'])
@pytest.mark.parametrize('value',[None,1])
def test_malformed_metric(field,value):
 m=measure();m['candidate'][field]=value
 assert r.decide(cache(),m,policy())['status']=='NEEDS_MEASUREMENT'
