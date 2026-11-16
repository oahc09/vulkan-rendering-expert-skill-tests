import copy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from tools.resource_contract_chain19 import check,trace_subject
pytestmark=pytest.mark.candidate19

def example():
 events=[dict(id='bind',op='bind',buffer='B',generation=1,proof='bind-proof'),dict(id='write',op='write_descriptor',set='S',buffer='B',generation=1,offset=0,size=64,proof='write-proof'),dict(id='record',op='record_use',cb='C',set='S',access='READ',proof='record-proof'),dict(id='submit',op='submit',submission='T',cb='C'),dict(id='complete',op='complete',submission='T',proof='complete-proof'),dict(id='free',op='free',allocation='A',generation=1,proof='free-proof')]
 common=dict(buffer='B',generation=1,allocation='A',allocation_generation=1)
 def p(i,k,s):return dict(id=i,kind=k,subject=s,authority='CALLER_DECLARED',evidence_sha256='a'*64)
 proofs=[p('bind-proof','ORDINARY_ALLOCATION_VALID',dict(**common,event='bind')),p('write-proof','DESCRIPTOR_PAYLOAD_AND_LAYOUT_VALID',dict(**common,event='write',offset=0,size=64,set='S')),p('record-proof','PIPELINE_LAYOUT_AND_ACCESS_SCOPE',dict(**common,event='record',cb='C',set='S',offset=0,size=64,access='READ')),p('complete-proof','SUBMISSION_ALL_USES_COMPLETED',dict(event='complete',submission='T',record_event='record',buffer='B',generation=1,allocation='A',allocation_generation=1,submit_event='submit')),p('free-proof','HOST_ACCESS_COMPLETED_NO_CONCURRENT_ACCESS',dict(event='free',allocation='A',generation=1))]
 t=dict(schema=1,scope='ordinary-single-device-single-queue-nonalias-nondedicated-buffer',allocations=[dict(id='A',generation=1,size=128,memory_type_index=0)],buffers=[dict(id='B',generation=1,allocation='A',allocation_generation=1,buffer_size=64,requirements_size=80,alignment=16,type_bits=1,offset=0)],proofs=proofs,events=events);complete_inventory(t);return t

def complete_inventory(t):
 t['proofs']=[p for p in t['proofs'] if p['id']!='trace-complete']+[dict(id='trace-complete',kind='TRACE_AND_HOST_SCOPE',subject=trace_subject(t),authority='CALLER_DECLARED',evidence_sha256='b'*64)]
def addproof(t,i,k,subject):t['proofs'].append(dict(id=i,kind=k,subject=subject,authority='CALLER_DECLARED',evidence_sha256='c'*64))
def test_good_bound_free_allowed():
 r=check(example());assert r['status']=='CONSISTENT_DECLARED_TRACE';assert r['events'][-1]['result']['bound_resources_may_remain']is True
@pytest.mark.parametrize('kind',['missing','unresolved','wrong-generation','verified'])
def test_proofs(kind):
 t=example();assert check(t)['status']=='CONSISTENT_DECLARED_TRACE'
 if kind=='missing':t['proofs'].pop(0)
 elif kind=='unresolved':t['proofs'][0]['authority']='UNRESOLVED'
 elif kind=='wrong-generation':t['proofs'][0]['subject']['generation']=2
 else:t['proofs'][0]['authority']='VERIFIED_ADAPTER'
 assert check(t)['status']==('REJECTED_DECLARED_TRACE' if kind=='verified' else 'OBLIGATIONS_NOT_ESTABLISHED')
def test_pending_free():
 t=example();t['events'].pop(4);complete_inventory(t);assert check(t)['status']=='REJECTED_DECLARED_TRACE'
def test_wait_does_not_retire():
 t=example();t['events'][4]=dict(id='wait',op='timeline_snapshot',counter=9,target=8);complete_inventory(t);r=check(t);assert r['status']=='REJECTED_DECLARED_TRACE';assert r['events'][-1]['result']['satisfied']is True
def test_update_pending_rejected():
 t=example();e=copy.deepcopy(t['events'][1]);e['id']='update';e['proof']='update-proof';t['events'].insert(4,e);p=copy.deepcopy(t['proofs'][1]);p['id']='update-proof';p['subject']['event']='update';t['proofs'].append(p);complete_inventory(t);assert 'pending' in check(t)['reason']
def test_update_recorded_invalidates():
 t=example();e=copy.deepcopy(t['events'][1]);e['id']='update';e['proof']='update-proof';t['events'].insert(3,e);p=copy.deepcopy(t['proofs'][1]);p['id']='update-proof';p['subject']['event']='update';t['proofs'].append(p);complete_inventory(t);assert 'stale recording' in check(t)['reason']
def test_free_then_use():
 t=example();t['events'].append(dict(id='submit-again',op='submit',submission='T2',cb='C'));complete_inventory(t);assert check(t)['status']=='REJECTED_DECLARED_TRACE'
def test_undefined_copy_not_readable():
 t=example();t['events'] += [dict(id='copy',op='copy_descriptor',src='S',dst='D',proof='copy-proof'),dict(id='read-dead',op='record_use',cb='C2',set='D',access='READ',proof='unused')];addproof(t,'copy-proof','DESCRIPTOR_COPY_LAYOUT_VALID',dict(event='copy',src='S',dst='D'));complete_inventory(t);r=check(t);assert 'undefined/dead' in r['reason'];assert r['events'][-1]['result']['state_after']['D']['values'][0][0]['defined']is False
@pytest.mark.parametrize('kind',['duplicate-event','unknown-op','extra-field'])
def test_schema(kind):
 t=example()
 if kind=='duplicate-event':t['events'].append(t['events'][0])
 elif kind=='unknown-op':t['events'][0]['op']='execute_python';complete_inventory(t)
 else:t['unexpected']=True
 assert check(t)['status']=='REJECTED_DECLARED_TRACE'
def raw_trace(with_proof=True):
 t=example();t['events'][2]['access']='WRITE';t['proofs'][2]['subject']['access']='WRITE'
 t['events'].pop() # defer free
 e=dict(id='read2',op='record_use',cb='C2',set='S',access='READ',proof='read2-proof');t['events'].append(e);subject=dict(buffer='B',generation=1,allocation='A',allocation_generation=1,event='read2',cb='C2',set='S',offset=0,size=64,access='READ');addproof(t,'read2-proof','PIPELINE_LAYOUT_AND_ACCESS_SCOPE',subject)
 if with_proof:
  t['events'].append(dict(id='dep',op='sync_proof',first='record',second='read2',buffer='B',generation=1,offset=0,size=64,proof='dep-proof'));addproof(t,'dep-proof','SCOPED_GPU_DEPENDENCY',dict(buffer='B',generation=1,allocation='A',allocation_generation=1,event='dep',first='record',second='read2',offset=0,size=64))
 t['events'].append(dict(id='submit2',op='submit',submission='T2',cb='C2'));complete_inventory(t);return t
def test_scoped_dependency():assert check(raw_trace())['status']=='CONSISTENT_DECLARED_TRACE'
def test_completion_not_dependency():assert check(raw_trace(False))['status']=='OBLIGATIONS_NOT_ESTABLISHED'
def test_wrong_dependency_range():
 t=raw_trace();t['events'][-2]['size']=1;next(p for p in t['proofs'] if p['id']=='dep-proof')['subject']['size']=1;complete_inventory(t);assert 'range mismatch' in check(t)['reason']
def test_freed_memory_new_recording_rejected():
 t=example();t['events'].append(dict(id='new-record',op='record_use',cb='NEW',set='S',access='READ',proof='unused'));complete_inventory(t)
 r=check(t);assert r['event_index']==6 and 'undefined/dead' in r['reason']
def test_pending_cb_resubmit_rejected():
 t=example();t['events'].insert(4,dict(id='submit2',op='submit',submission='T2',cb='C'));complete_inventory(t);assert 'pending CB' in check(t)['reason']
def test_completed_recording_requires_new_record_event():
 t=example();t['events'].insert(5,dict(id='submit2',op='submit',submission='T2',cb='C'));complete_inventory(t);assert 'rerecord required' in check(t)['reason']
@pytest.mark.parametrize('value',[True,1.0])
def test_event_identity_exact_types(value):
 t=example();t['events'][0]['generation']=value;complete_inventory(t);assert check(t)['status']=='REJECTED_DECLARED_TRACE'
@pytest.mark.parametrize('value',[True,1.0])
def test_proof_identity_exact_types(value):
 t=example();t['proofs'][0]['subject']['generation']=value;assert check(t)['status']=='OBLIGATIONS_NOT_ESTABLISHED'
def test_trace_complete_binds_full_content_not_ids():
 t=example();t['events'][1]['size']=32
 assert check(t)['status']=='OBLIGATIONS_NOT_ESTABLISHED'
