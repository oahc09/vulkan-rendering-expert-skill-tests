import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import copy
import pytest
pytestmark = pytest.mark.candidate19
from tools import compute_schedule19 as r
from checks19 import decide_compute_schedule as cli

def facts():
 return dict(families=[dict(family=0,flags=3,count=2)],created=[dict(family=0,index=0),dict(family=0,index=1)],graphics=dict(family=0,index=0),compute=dict(family=0,index=1),requirements=[],ordinary_single_device=True,dependency_proven=True,resource_sharing='EXCLUSIVE',ownership_transfer_proven=False,lifetime_proven=True,baseline_no_implicit_transfer_exception=True,concurrent_families=[])
def policy():return dict(baseline_verified=True,candidate_active=True,minimum_gain_fraction=.05,max_observed_frame_regression_fraction=0.,other_objectives_satisfied=True)
def measure():
 co={x:'fixed' for x in ('device','driver','workload','resolution','shader','tools','clock_domain','thermal_regime','input','warmup_protocol','paired_run_order_protocol')}
 return dict(baseline=dict(cohort=co.copy(),full_frame_ns=[100,101,99],compute_pass_ns=[50,51,49]),candidate=dict(cohort=co.copy(),full_frame_ns=[80,81,79],compute_pass_ns=[40,41,39]),paired_trials=True,full_frame_boundaries_equal=True,all_queue_completion_included=True,measurement_method='FULL_FRAME_GPU_CLOCK',output_equal=True,source_sha256='a'*64)
def test_positive():
 assert r.admission(facts())['status']=='MULTI_QUEUE_ADMISSIBLE'
 assert r.decide(facts(),measure(),policy())['status']=='SELECT_MEASURED_CANDIDATE'
def test_pass_gain_frame_loss_revoke():
 m=measure();m['candidate']['full_frame_ns']=[110]*3;m['candidate']['compute_pass_ns']=[20]*3
 assert r.decide(facts(),m,policy())['status']=='REVOKE_TO_BASELINE'
def test_no_measurement_keeps_baseline():
 x=r.decide(facts(),None,policy());assert x['status']=='NEEDS_MEASUREMENT' and x['selected']=='BASELINE'
@pytest.mark.parametrize('key',['dependency_proven','lifetime_proven'])
def test_required_proof(key):
 f=facts();f[key]=False;assert r.admission(f)['status']=='NEEDS_PROOF'
def test_not_created():
 f=facts();f['created'].pop();assert r.admission(f)['status']=='NOT_ADMISSIBLE'
def test_single_queue():
 f=facts();f['compute']['index']=0;assert r.admission(f)['status']=='SINGLE_QUEUE'
def test_cross_family():
 f=facts();f['families'].append(dict(family=1,flags=2,count=1));f['created'].append(dict(family=1,index=0));f['compute']=dict(family=1,index=0)
 assert r.admission(f)['status']=='NEEDS_PROOF'
 f['ownership_transfer_proven']=True;assert r.admission(f)['status']=='MULTI_QUEUE_ADMISSIBLE'
 f['resource_sharing']='CONCURRENT';f['concurrent_families']=[0];assert r.admission(f)['status']=='NOT_ADMISSIBLE'
 f['concurrent_families']=[0,1];assert r.admission(f)['status']=='MULTI_QUEUE_ADMISSIBLE'
@pytest.mark.parametrize('enabled,supported',[(False,True),(True,False),(False,False)])
def test_supported_not_enabled(enabled,supported):
 f=facts();f['requirements']=[dict(name='workload-feature',supported=supported,enabled=enabled)]
 assert r.admission(f)['status']=='NOT_ADMISSIBLE'
@pytest.mark.parametrize('change',[None,[],{},dict(family=True,flags=3,count=2),dict(family=0,flags=3,count=2**32)])
def test_family_shape(change):
 f=facts();f['families']=[change];assert r.admission(f)['status']=='UNKNOWN'
@pytest.mark.parametrize('field',['device','driver','workload','resolution','shader','tools','clock_domain','thermal_regime'])
def test_cohort(field):
 m=measure();m['candidate']['cohort'][field]='different';assert r.decide(facts(),m,policy())['status']=='NEEDS_MEASUREMENT'
@pytest.mark.parametrize('bad',[True,float('nan'),float('inf'),0,-1])
def test_bad_timing(bad):
 m=measure();m['candidate']['full_frame_ns'][0]=bad;assert r.decide(facts(),m,policy())['status']=='NEEDS_MEASUREMENT'
@pytest.mark.parametrize('key',['paired_trials','full_frame_boundaries_equal','all_queue_completion_included','output_equal'])
def test_comparison_obligations(key):
 m=measure();m[key]=False;assert r.decide(facts(),m,policy())['status']=='REVOKE_TO_BASELINE'
def test_unverified_fallback():
 p=policy();p['baseline_verified']=False;assert r.decide(facts(),measure(),p)['selected'] is None
def test_other_objectives():
 p=policy();p['other_objectives_satisfied']=False;assert r.decide(facts(),measure(),p)['status']=='NEEDS_MEASUREMENT'
def test_no_overlap_inference():assert r.decide(facts(),measure(),policy())['overlap_proven'] is False
def test_duplicate_json():
 with pytest.raises(ValueError):cli.load('{"x":1,"x":2}')
def test_wrong_prose():
 with pytest.raises(ValueError):cli.run(dict(facts=facts(),measurement=measure(),policy=policy()),b'wrong',b'wrong')
def test_implicit_transfer_unknown():
 f=facts();f['baseline_no_implicit_transfer_exception']=False;assert r.admission(f)['status']=='OUT_OF_SCOPE'

def test_worst_frame_regression():
 m=measure();m['candidate']['full_frame_ns']=[70,70,120]
 assert r.decide(facts(),m,policy())['status']=='REVOKE_TO_BASELINE'
def test_concurrent_single_family():
 f=facts();f['resource_sharing']='CONCURRENT';f['concurrent_families']=[0]
 assert r.admission(f)['status']=='NOT_ADMISSIBLE'

def test_real_frozen_prose():
 from pathlib import Path
 root=Path('/workspace/scratch/62d43a81bbde/cts-src/external/vulkan-docs/src/chapters')
 if not root.exists():pytest.skip('fixed local prose source absent')
 out=cli.run(dict(facts=facts(),measurement=measure(),policy=policy()),(root/'devsandqueues.adoc').read_bytes(),(root/'synchronization.adoc').read_bytes(),*[ (root/(n+'.adoc')).read_bytes() for n in ('resources','features','fundamentals')])
 assert len(out['sources'][0]['slices'])==3 and len(out['sources'][1]['slices'])==2

def test_capability_binding():
 import hashlib,json
 f=facts();cap=dict(schema=1,status='QUEUE_CREATION_OBSERVED',gpu_work_submitted=False,get_queue_nonnull=True,enabled_features=[],enabled_extensions=[],physical_device_count=1,device={'name':'fixture'},families=f['families'],created=f['created'])
 raw=json.dumps(cap).encode();digest=hashlib.sha256(raw).hexdigest();req=dict(facts=f,measurement=None,policy=policy())
 assert cli.bind_capability(req,raw,digest)['gpu_work_submitted'] is False
 with pytest.raises(ValueError):cli.bind_capability(req,raw,'0'*64)
 req['facts']['created']=[]
 with pytest.raises(ValueError):cli.bind_capability(req,raw,digest)

@pytest.mark.parametrize('key',['minimum_gain_fraction','max_observed_frame_regression_fraction'])
def test_huge_policy(key):
 p=policy();p[key]=10**1000;assert r.decide(facts(),measure(),p)['status']=='UNKNOWN'
def test_huge_timing():
 m=measure();m['candidate']['full_frame_ns'][0]=10**1000;assert r.decide(facts(),m,policy())['status']=='NEEDS_MEASUREMENT'

@pytest.mark.parametrize('mode,expected',[('declared','SELECT_MEASURED_CANDIDATE'),('regression','REVOKE_TO_BASELINE')])
def test_real_cli(tmp_path,mode,expected):
 import json,subprocess,sys
 root=Path(__file__).resolve().parents[1];src=Path('/workspace/scratch/62d43a81bbde/cts-src/external/vulkan-docs/src/chapters')
 if not src.exists():pytest.skip('fixed source absent')
 m=measure()
 if mode=='regression':m['candidate']['full_frame_ns']=[120]*3;m['candidate']['compute_pass_ns']=[20]*3
 request=tmp_path/'input.json';request.write_text(json.dumps(dict(facts=facts(),measurement=m,policy=policy())))
 cmd=[sys.executable,str(root/'checks19/decide_compute_schedule.py'),'--request',str(request),'--out',str(tmp_path/'out')]
 for n in ('devsandqueues','synchronization','resources','features','fundamentals'):cmd+=['--'+n,str(src/(n+'.adoc'))]
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 assert json.loads((tmp_path/'out/report.json').read_text())['decision']['status']==expected
 assert subprocess.run(cmd,capture_output=True).returncode!=0
