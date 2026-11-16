"""Host contract tests only: no Live or GPU acceptance."""
import copy, importlib.util,json,math
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
d=load('delivery19');e=load('evidence19')
pytestmark=pytest.mark.host_unit
RULE={'rule_id':'async','requires':{'supported':['queue'],'enabled':['sync2'],'parameters':['ownership'],'lifecycle':['retired']},'budgets':{'memory':100},'alternatives':['single_queue'],'fallback':'single_queue','revisit_conditions':['new workload']}
P={'scope':{'device':'d','driver':'1','scene':'s'},'supported':{'queue':True},'enabled':{'sync2':True},'parameters':{'ownership':True},'lifecycle':{'retired':True},'costs':{'memory':50}}

def status(p):return d.decide(p,[RULE])[0]['status']
def test_unknown_not_support():
    assert status({})=='UNKNOWN'
    assert status(P)=='NEEDS_MEASUREMENT'
@pytest.mark.parametrize('group,key', [('supported','queue'),('enabled','sync2'),('parameters','ownership'),('lifecycle','retired')])
def test_hard_reject(group,key):
    p=copy.deepcopy(P);p[group][key]=False;assert status(p)=='REJECTED'
@pytest.mark.parametrize('value',['true',1,[],{}])
def test_bad_capability(value):
    p=copy.deepcopy(P);p['enabled']['sync2']=value
    with pytest.raises(ValueError):status(p)
@pytest.mark.parametrize('value',[float('nan'),float('inf'),'10'])
def test_bad_cost(value):
    p=copy.deepcopy(P);p['costs']['memory']=value
    with pytest.raises(ValueError):status(p)
def measured():
    p=copy.deepcopy(P);p['measurements']={'async':{'scope':p['scope'],'comparable':True,'artifact_sha256':'a'*64,'objectives':{'full_frame':True,'quality':True}}};return p
def test_measured_not_brand():
    p=measured();assert status(p)=='ELIGIBLE_WITHIN_SCOPE'
    p['vendor']='other';assert status(p)=='ELIGIBLE_WITHIN_SCOPE'
    p['measurements']['async']['objectives']['full_frame']=False;assert status(p)=='KEEP_BASELINE'
@pytest.mark.parametrize('field,value',[('scope',{}),('comparable',False),('artifact_sha256','bad'),('objectives',{})])
def test_missing_evidence(field,value):
    p=measured();p['measurements']['async'][field]=value
    assert status(p)=='NEEDS_MEASUREMENT'
def test_resource_join_never_handle_only():
    records=[{'evidence_id':str(i),'run_id':'r','device_scope':'d','object':{'id':'h','generation':i%2}} for i in range(4)]
    assert len(d.correlate(records))==2
    records[0]['device_scope']='other';assert len(d.correlate(records))==3
    records[0]['object']['generation']=None;assert len(d.correlate(records))==2

def test_waitidle_not_root_cause():
    h={'mechanism':'reuse','support':['ev'],'counterevidence':[],'stop_condition':'timeout','experiment':{'kind':'wait_idle_workaround','discriminates':['reuse'],'result':'supports','evidence_id':'ev'}}
    assert d.hypothesis_status(h,{'ev'})=='INSUFFICIENT'
    h['experiment']['kind']='generation';assert d.hypothesis_status(h,{'ev'})=='SUPPORTED_NOT_PROVEN'
    h['support']=['fabricated']
    with pytest.raises(ValueError):d.hypothesis_status(h,{'ev'})
def patch():return {'before_evidence':['ev'],'mechanism':'fence reset before failed acquire','allowed_paths':['f.py'],'changed_paths':['f.py'],'regressions':{'failure':'PASS'},'rollback':'revert','remaining_risks':['GPU not run']}
def test_patch_scope_and_blocked():
    p=patch();assert d.validate_patch(p)=='VALIDATED_WITHIN_DECLARED_SCOPE'
    p['regressions']['device']='BLOCKED';assert d.validate_patch(p)=='NOT_VERIFIED'
    p['changed_paths'].append('unrelated')
    with pytest.raises(ValueError):d.validate_patch(p)
def ab():
    a={k:'same' for k in ('scene','seed','camera','resolution','device','driver','cache','instrumentation','thermal','power_mode')};a['metrics']={'frame_ms':10,'error':0};return a
def test_ab_joint_quality():
    a=ab();b=ab();b['metrics']={'frame_ms':8,'error':.2}
    assert d.compare_ab(a,b,{'frame_ms':0,'error':.1})['status']=='KEEP_BASELINE'
    b['thermal']='different';assert d.compare_ab(a,b,{'frame_ms':0})['status']=='NOT_COMPARABLE'
    del b['thermal'];assert d.compare_ab(a,b,{'frame_ms':0})['status']=='NOT_COMPARABLE'
def test_experience_review_revoke():
    c={'id':'x','state':'candidate','sanitized':True,'scope':{'driver':'1'},'evidence':['a'],'revisit_conditions':['driver change']}
    assert d.retrieve_experience([c],{'driver':'1'})==[]
    c=d.transition_case(c,'review','review-evidence','reviewer');assert len(d.retrieve_experience([c],{'driver':'1'}))==1
    assert d.retrieve_experience([c],{'driver':'2'})==[]
    c=d.transition_case(c,'revoke','counterexample');assert d.retrieve_experience([c],{'driver':'1'})==[]
    assert len(c['history'])==2
@pytest.mark.parametrize('sanitized,reviewer',[(False,'r'),(True,None)])
def test_experience_no_automatic_promotion(sanitized,reviewer):
    with pytest.raises(ValueError):d.transition_case({'state':'candidate','sanitized':sanitized},'review','e',reviewer)
def test_four_seals():
    x={k:{'status':'BLOCKED','reason':'not run'} for k in ('knowledge','expert_delivery','support_matrix','release')}
    assert d.seal(x)==x
    x['knowledge']['status']='PASS'
    with pytest.raises(ValueError):d.seal(x)
def test_callback_preserves_unknown_generation():
    raw=json.dumps([{'pMessageIdName':'SYNC-HAZARD-WRITE_AFTER_READ','pMessage':'private path','objectCount':1,'pObjects':[{'objectHandle':'0x1'}]}]).encode()
    r=e.validation(raw,'r','v','d')[0]
    assert r['object'] is None and r['source'] is None and r['hazard']=='SYNC-HAZARD-WRITE_AFTER_READ'
    assert 'private path' not in json.dumps(r)
def test_callback_bad_count():
    with pytest.raises(ValueError):e.validation(b'[{"pMessageIdName":"x","objectCount":1,"pObjects":[]}]','r','v','d')
def test_trace_csv():
    r=e.perfetto_csv(b'id,ts,dur,track_id,name\n1,2,-1,3,private\n','r','v','d')[0]
    assert r['duration_ns'] is None and r['frame_submit_event'] is None
    assert 'private' not in json.dumps(r)
@pytest.mark.parametrize('raw',[b'id,ts,dur,track_id,name\n1,2,-2,3,x\n',b'id,ts,dur,track_id,name\n1,2,3,4,x\n1,2,3,4,x\n',b'bad\n1\n'])
def test_trace_rejects(raw):
    with pytest.raises(ValueError):e.perfetto_csv(raw,'r','v','d')
def test_adapter_budget():
    with pytest.raises(ValueError):e.validation(b' '*2000001,'r','v','d')

def test_authored_fence_failure_before_after():
    from fence19_fixture import Frame,broken_frame,fixed_frame
    old=Frame();assert broken_frame(old,False)=='RECREATE'
    with pytest.raises(TimeoutError):broken_frame(old,True)
    new=Frame()
    for _ in range(3):assert fixed_frame(new,False)=='RECREATE'
    assert fixed_frame(new,True)=='SUBMITTED'
    with pytest.raises(TimeoutError):new.wait()
    new.complete();assert fixed_frame(new,True)=='SUBMITTED';new.complete()
