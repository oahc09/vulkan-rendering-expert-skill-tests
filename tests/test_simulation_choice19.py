import copy,gzip,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import simulation_choice19 as r
pytestmark=pytest.mark.candidate19
RAW=json.loads(gzip.decompress((ROOT/'tests/fixtures/simulation-choice19.json.gz').read_bytes()))
def policy(target=None,perf=False):return dict(baseline='colored',quality_targets=target,require_performance=perf)
def target(residual):return {s:dict(max_absolute_residual=residual,max_penetration=1e-5) for s in r.SCENES}
def test_actual_baseline():
 m=r.analyze(RAW);assert len(r.expected_edges('rope'))==31 and len(r.expected_edges('cloth'))==306
 assert m['cloth']['jacobi']['max_absolute_residual']>.5 and m['cloth']['jacobi']['max_cpu_match_error']<5e-5
 assert r.decide(RAW,policy())['status']=='NEEDS_QUALITY_TARGET'
@pytest.mark.parametrize('mutation',['missing','duplicate','edge_missing','edge_duplicate','edge_order','rest','tick','name','generation','gpu','normal','residual','lambda','absolute','fixed','nan'])
def test_positive_then_corruption(mutation):
 r.analyze(RAW);a=copy.deepcopy(RAW);p=a[0];d=p['state'];c=p['constraints']
 if mutation=='missing':a.pop()
 elif mutation=='duplicate':a[-1]=copy.deepcopy(a[0])
 elif mutation=='edge_missing':c['edges'].pop()
 elif mutation=='edge_duplicate':c['edges'][-1]=c['edges'][0][:]
 elif mutation=='edge_order':c['edges'].reverse()
 elif mutation=='rest':c['edges'][0][2]+=.01
 elif mutation=='tick':p['tick']=True
 elif mutation=='name':d['name']='rope-jacobi-tick1'
 elif mutation=='generation':d['bounds'][7]=0
 elif mutation=='gpu':d['gpu'][0][0]+=1
 elif mutation=='normal':d['normals'][0][0]+=1
 elif mutation=='residual':c['edges'][0][4]+=1
 elif mutation=='lambda':c['edges'][0][6]+=1
 elif mutation=='absolute':c['max_absolute_residual_observed']=0
 elif mutation=='fixed':c['max_fixed_error']=1
 elif mutation=='nan':d['gpu'][0][0]=float('nan')
 with pytest.raises(ValueError):r.analyze(a)
def test_synthetic_product_policies_not_acceptance_thresholds():
 assert r.decide(RAW,policy(target(1)))['status']=='KEEP_BASELINE'
 assert r.decide(RAW,policy(target(0)))['status']=='NO_QUALITY_ADMISSIBLE_PATH'
 assert r.decide(RAW,policy(target(1),True))['status']=='NEEDS_MEASUREMENT'
@pytest.mark.parametrize('bad',[None,[],{},dict(status='PASS')])
def test_no_status_spoof(bad):assert r.decide(bad,policy())['status']=='UNKNOWN'
@pytest.mark.parametrize('bad',[True,-1,float('nan'),10**1000])
def test_bad_product_numeric(bad):assert r.decide(RAW,policy(target(bad)))['status']=='UNKNOWN'
def test_negative_control_manifest_is_complete():
 text=(ROOT/'checks19/run_simulation_choice.py').read_text()
 assert "corruptions[kind]='REJECTED_HOST_CORRUPTION'" in text
 assert "set(corruptions)=={'missing_snapshot','duplicate_snapshot','missing_edge','duplicate_edge','stale_generation','residual_tamper','gpu_tamper'}" in text
