import pytest
from tools import timeline_contract19 as m
@pytest.fixture
def facts():return dict(ordinary_timeline_enabled=True,at_call_state_proven=True,pending_set_complete=True,host_calls_serialized=True,current=2,value=3,max_difference=10,pending_signals=[dict(value=5,happens_after_host_signal=True)],pending_waits=[1,4])
def test_host_signal(facts):assert m.host_signal(facts)['status']=='HOST_SIGNAL_CONDITIONS_WITHIN_SCOPE'
@pytest.mark.parametrize('v',[1,2])
def test_nonmonotonic(facts,v):
 facts['value']=v;assert 'VUID-VkSemaphoreSignalInfo-value-03258' in m.host_signal(facts)['vuids']
@pytest.mark.parametrize('v',[5,6])
def test_pending_signal_lower_required(facts,v):
 facts['value']=v;assert 'VUID-VkSemaphoreSignalInfo-value-03259' in m.host_signal(facts)['vuids']
@pytest.mark.parametrize('field,value',[('current',20),('pending_waits',[20]),('pending_signals',[dict(value=20,happens_after_host_signal=True)])])
def test_difference_each_source(facts,field,value):
 facts[field]=value;assert 'VUID-VkSemaphoreSignalInfo-value-03260' in m.host_signal(facts)['vuids']
def test_exact_difference_boundary(facts):
 facts['pending_waits']=[13];assert 'VUID-VkSemaphoreSignalInfo-value-03260' not in m.host_signal(facts)['vuids']
def test_numeric_not_order(facts):
 facts['pending_signals'][0]['happens_after_host_signal']=False
 assert m.host_signal(facts)['status']=='ORDER_NOT_ESTABLISHED'
@pytest.mark.parametrize('field',['ordinary_timeline_enabled','at_call_state_proven','pending_set_complete','host_calls_serialized'])
def test_unknown_state(facts,field):
 facts[field]=False;assert m.host_signal(facts)['status']=='UNKNOWN'
@pytest.mark.parametrize('value',[True,-1,2**64,None,3.0])
def test_uint64(facts,value):
 facts['value']=value;assert m.host_signal(facts)['status']=='UNKNOWN'
def test_max_uint_no_wrap(facts):
 facts.update(current=m.U64,value=m.U64,max_difference=m.U64,pending_signals=[],pending_waits=[])
 assert m.host_signal(facts)['vuids']==['VUID-VkSemaphoreSignalInfo-value-03258']
def test_zero_is_valid_wait_value():assert m.wait_condition([0],[0],'ALL')['satisfied'] is True
def test_any_all():
 assert m.wait_condition([2,9],[3,8],'ANY')['satisfied'] is True
 assert m.wait_condition([2,9],[3,8],'ALL')['satisfied'] is False
def test_unsatisfied_not_deadlock():
 r=m.wait_condition([0],[5],'ALL');assert not r['satisfied'] and r['predicts_deadlock'] is False and r['predicts_vkresult'] is False
@pytest.mark.parametrize('args',[([],[],'ALL'),([True],[1],'ALL'),([1],[2,3],'ANY'),([1],[2],'other'),([1],[2**64],'ALL')])
def test_wait_unknown(args):assert m.wait_condition(*args)['status']=='UNKNOWN'
@pytest.mark.parametrize('wait',[True,False])
def test_wait_not_retirement(wait):
 assert m.retirement(dict(wait_satisfied=wait,reference_set_complete=True,relevant_host_calls_completed=True,no_concurrent_host_access=True,all_submitted_references_completed=False))['status']=='RETIREMENT_NOT_ESTABLISHED'
def test_complete_reference_proof():assert m.retirement(dict(wait_satisfied=False,reference_set_complete=True,relevant_host_calls_completed=True,no_concurrent_host_access=True,all_submitted_references_completed=True))['status']=='RETIREMENT_OBLIGATIONS_DECLARED'
def test_missing_reference_set():assert m.retirement(dict(wait_satisfied=True,reference_set_complete=False,relevant_host_calls_completed=True,no_concurrent_host_access=True,all_submitted_references_completed=True))['status']=='UNKNOWN'
@pytest.mark.parametrize('fn,arg',[(m.host_signal,None),(m.host_signal,{}),(m.retirement,None),(m.retirement,{})])
def test_malformed(fn,arg):assert fn(arg)['status']=='UNKNOWN'

@pytest.mark.parametrize('field',['relevant_host_calls_completed','no_concurrent_host_access'])
def test_host_retirement_also_required(field):
 f=dict(wait_satisfied=True,reference_set_complete=True,all_submitted_references_completed=True,relevant_host_calls_completed=True,no_concurrent_host_access=True)
 f[field]=False
 assert m.retirement(f)['status']=='RETIREMENT_NOT_ESTABLISHED'
