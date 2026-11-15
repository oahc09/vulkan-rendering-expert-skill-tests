"""CPU obligations; actual pending experiment is recorded separately."""
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));import descriptor_lifetime19 as d
pytestmark=pytest.mark.host_unit
ID=dict(run='r',device_id='device-a',set_id='set-a',device_generation=1,set_generation=2)
def plan(state=None,**kwargs):
 args=dict(binding_model='ordinary',identity=ID,references=[] if state is None else [dict(ID,command_buffer='c',state=state)],inventory_complete=True,host_exclusive=True);args.update(kwargs);return d.plan(**args)
def test_pending_not_update_permission():assert plan('pending')['status']=='WAIT_RETIREMENT'
@pytest.mark.parametrize('state',['recording','executable'])
def test_fence_retirement_still_needs_rerecord(state):assert plan(state)['status']=='UPDATE_REQUIRES_RERECORD'
@pytest.mark.parametrize('state',[None,'initial','invalid'])
def test_no_pending_or_recorded_reference(state):assert plan(state)['status']=='UPDATE_WITHIN_SCOPE'
def test_missing_reference_inventory():assert plan(inventory_complete=False)['status']=='UNKNOWN'
def test_host_race():assert plan(host_exclusive=False)['status']=='REJECTED_HOST_RACE'
def test_new_generation_not_old_completion():assert plan(references=[dict(ID,device_generation=2,command_buffer='c',state='executable')])['status']=='UNKNOWN'
def test_advanced_binding_not_silently_accepted():assert plan(binding_model='update-after-bind')['status']=='OUT_OF_SCOPE'
def test_multiple_queues_pending_wins():assert plan(references=[dict(ID,command_buffer='old',state='executable'),dict(ID,command_buffer='other-queue',state='pending')])['status']=='WAIT_RETIREMENT'
def test_bad_state():
 with pytest.raises(ValueError):plan('completed')

@pytest.mark.parametrize('value',[{},None,''])
def test_wrong_reference_container(value):
 with pytest.raises(ValueError):plan(references=value)
@pytest.mark.parametrize('field',['device_id','set_id'])
def test_same_generation_wrong_object(field):
 ref=dict(ID,command_buffer='c',state='executable');ref[field]='other'
 assert plan(references=[ref])['status']=='UNKNOWN'
def test_bool_generation():
 with pytest.raises(ValueError):plan(identity=dict(ID,device_generation=True))
 assert plan(references=[dict(ID,device_generation=True,command_buffer='c',state='executable')])['status']=='UNKNOWN'

def test_recorded_joint_case_provenance():
 import hashlib,json
 record=json.loads((ROOT/'coverage/v1.0.19/descriptor-lifetime.json').read_text())
 for name,expected in record['sources'].items():
  assert hashlib.sha256((ROOT/'cases19/descriptor_lifetime'/name).read_bytes()).hexdigest()==expected
 assert record['runtime_identity']['device_type']==4
 for mode,c in record['cases'].items():
  r=c['result'];assert r['fence_not_ready'] and r['first']==42 and r['second']==99
  assert r['exit_code']==(6 if mode=='wrong-output' else 0)
 assert record['cases']['bad']['diagnostics']==['VUID phase=pending-update id=VUID-vkUpdateDescriptorSets-None-03047']
 assert record['cases']['good']['diagnostics']==[]
