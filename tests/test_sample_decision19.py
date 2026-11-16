import pathlib,sys,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.sample_decision19 import decide
B=dict(samples=1,requested_bytes=128,endpoint_error=0)
C=dict(samples=4,requested_bytes=512,endpoint_error=0)
def policy(**kw):return dict(required_samples=1,requested_bytes_budget=1024,require_edge_quality=False,require_performance_gain=False,**kw)
def test_baseline():assert decide(B,C,policy())['status']=='KEEP_BASELINE'
def test_same_device_different_requirement():
 p=policy();p['required_samples']=4
 r=decide(B,C,p);assert r['status']=='SELECT_REQUIRED_SAMPLE_COUNT' and r['selected_samples']==4 and r['fallback_samples'] is None
def test_budget_rejects_candidate():
 p=policy();p['requested_bytes_budget']=128
 r=decide(B,C,p);assert r['status']=='KEEP_BASELINE' and r['alternatives'][1]['rejections']==['allocation-request-budget']
def test_no_silent_fallback_below_requirement():
 p=policy();p.update(required_samples=4,requested_bytes_budget=128)
 assert decide(B,C,p)['status']=='NO_ADMISSIBLE_PATH'
@pytest.mark.parametrize('key',['require_edge_quality','require_performance_gain'])
def test_unknown_objective_not_pass(key):
 p=policy();p[key]=True;r=decide(B,C,p)
 assert r['status']=='NEEDS_MEASUREMENT' and r['selected_samples'] is None and r['fallback_samples']==1
def test_output_mismatch_not_ignored():
 b=dict(B,endpoint_error=1);c=dict(C,endpoint_error=1)
 assert decide(b,c,policy())['status']=='NO_ADMISSIBLE_PATH'
@pytest.mark.parametrize('value',[True,-1,1.5,float('nan'),None,2**64])
def test_bad_budget(value):
 p=policy();p['requested_bytes_budget']=value
 with pytest.raises(ValueError):decide(B,C,p)
@pytest.mark.parametrize('key',['required_samples','requested_bytes_budget','require_edge_quality','require_performance_gain'])
def test_missing_policy(key):
 p=policy();del p[key]
 with pytest.raises(ValueError):decide(B,C,p)
@pytest.mark.parametrize('bad',[None,[],{},dict(B,requested_bytes=True),dict(B,samples=4),dict(B,endpoint_error=-1),dict(B,extra=0)])
def test_bad_facts(bad):
 with pytest.raises(ValueError):decide(bad,C,policy())
def test_not_brand_or_score_based():
 r=decide(B,C,policy());assert 'score' not in r and len(r['unmeasured'])==5

def test_candidate_only_correct_path_not_false_sample_requirement():
 r=decide(dict(B,endpoint_error=1),C,policy())
 assert r['status']=='SELECT_ONLY_ADMISSIBLE_PATH' and r['selected_samples']==4
def test_candidate_error_keeps_valid_baseline():
 assert decide(B,dict(C,endpoint_error=1),policy())['status']=='KEEP_BASELINE'
def test_both_over_budget():
 p=policy();p['requested_bytes_budget']=1
 assert decide(B,C,p)['status']=='NO_ADMISSIBLE_PATH'
def test_required4_unknown_no_baseline_fallback():
 p=policy();p.update(required_samples=4,require_edge_quality=True)
 r=decide(B,C,p);assert r['status']=='NEEDS_MEASUREMENT' and r['fallback_samples'] is None
