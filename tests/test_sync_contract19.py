"""Host semantic-contract tests, not GPU executions or verified barrier scopes."""
import pytest
from tools import sync_contract19 as m

@pytest.fixture
def facts():
    d={k:False for k in m.BOOL_FIELDS}
    d.update(same_device=True, overlapping_memory=True, ordinary_accesses=True,
             first_access='WRITE', second_access='READ',
             execution_dependency_covers_both_operations=True,
             first_write_available=True, available_write_visible_to_second_access=True,
             availability_visibility_ordered_between_operations=True)
    return d

@pytest.mark.parametrize('pair,hazard',[ (('WRITE','READ'),'RAW'), (('WRITE','WRITE'),'WAW'), (('READ','WRITE'),'WAR')])
def test_scoped_sufficient(facts,pair,hazard):
    facts.update(first_access=pair[0],second_access=pair[1])
    r=m.evaluate(facts)
    assert r['status']=='CALLER_FACTS_SUFFICIENT' and r['hazard']==hazard
    assert r['evidence_authority']=='CALLER_DECLARED_NOT_VERIFIED' and r['vuids']==[]

@pytest.mark.parametrize('second',['READ','WRITE'])
@pytest.mark.parametrize('field',['execution_dependency_covers_both_operations','first_write_available','available_write_visible_to_second_access','availability_visibility_ordered_between_operations'])
def test_raw_waw_each_requirement(facts,second,field):
    facts['second_access']=second;facts[field]=False
    assert m.evaluate(facts)['status']=='INSUFFICIENT_DEPENDENCY'

def test_war_execution_only(facts):
    facts.update(first_access='READ',second_access='WRITE',first_write_available=False,
                 available_write_visible_to_second_access=False,
                 availability_visibility_ordered_between_operations=False)
    assert m.evaluate(facts)['status']=='CALLER_FACTS_SUFFICIENT'
    facts['execution_dependency_covers_both_operations']=False
    assert m.evaluate(facts)['status']=='INSUFFICIENT_DEPENDENCY'

@pytest.mark.parametrize('field',['same_queue','submission_order','host_fence_completed'])
def test_order_retirement_not_dependency(facts,field):
    for k in ['execution_dependency_covers_both_operations','first_write_available',
              'available_write_visible_to_second_access','availability_visibility_ordered_between_operations']:facts[k]=False
    facts[field]=True
    assert m.evaluate(facts)['status']=='INSUFFICIENT_DEPENDENCY'

def test_all_context_true_still_not_dependency(facts):
    facts.update(same_queue=True,submission_order=True,host_fence_completed=True,
                 execution_dependency_covers_both_operations=False)
    assert m.evaluate(facts)['status']=='INSUFFICIENT_DEPENDENCY'

@pytest.mark.parametrize('field',sorted(m.FIELDS))
def test_missing_unknown(facts,field):
    del facts[field]
    assert m.evaluate(facts)['status']=='UNKNOWN'

@pytest.mark.parametrize('value',[None,1,0,'true',[],{}])
def test_nonboolean_unknown(facts,value):
    facts['first_write_available']=value
    assert m.evaluate(facts)['status']=='UNKNOWN'

@pytest.mark.parametrize('obj',[None,[],True,{}])
def test_malformed(obj):assert m.evaluate(obj)['status']=='UNKNOWN'

def test_extra_field_not_silently_accepted(facts):
    facts['stage_mask']=123
    assert m.evaluate(facts)['status']=='UNKNOWN'

@pytest.mark.parametrize('field,value',[('same_device',False),('ordinary_accesses',False),('overlapping_memory',False),('layout_transition',True),('ownership_transfer',True),('memory_domain_transfer',True)])
def test_excluded_scope(facts,field,value):
    facts[field]=value
    assert m.evaluate(facts)['status']=='OUT_OF_SCOPE'

def test_read_read_bounded(facts):
    facts.update(first_access='READ',second_access='READ')
    assert m.evaluate(facts)['status']=='NO_DATA_HAZARD_IN_SCOPE'

def test_no_mutation(facts):
    before=facts.copy();m.evaluate(facts);assert facts==before

@pytest.mark.parametrize('offset,size,total,ids',[
    (3,5,9,[]),(0,'WHOLE_SIZE',8,[]),(7,m.UINT64_MAX,8,[]),
    (8,1,8,['01187','01189']),(0,0,8,['01188']),(3,6,8,['01189']),
    (m.UINT64_MAX-2,3,m.UINT64_MAX,['01189']),
])
def test_range(offset,size,total,ids):
    r=m.buffer_range(offset,size,total)
    assert [v[-5:] for v in r['vuids']]==ids
    assert (r['status']=='RANGE_WITHIN_SCOPE')==(not ids)

@pytest.mark.parametrize('args',[(True,1,8),(0,False,8),(0,1,True),(-1,1,8),(0,-1,8),(0,1,2**64),(0,'arbitrary',8)])
def test_range_unknown(args):assert m.buffer_range(*args)['status']=='UNKNOWN'

@pytest.fixture
def owner():return dict(sharing_mode='EXCLUSIVE',same_device=True,same_instance=True,ordinary_resource=True,preserve_contents=True,families_valid=True,baseline_no_implicit_transfer_exception=True,source_family=0,destination_family=0)

def test_ownership_same_family_other_queue_not_transfer(owner):
    assert m.ownership(owner)['status']=='NO_FAMILY_TRANSFER_REQUIRED'
    assert m.ownership(owner)['synchronization_still_required'] is True
    owner['destination_family']=1
    assert m.ownership(owner)['status']=='OWNERSHIP_TRANSFER_REQUIRED'

@pytest.mark.parametrize('field,value',[('sharing_mode','CONCURRENT'),('same_device',False),('same_instance',False),('families_valid',False),('source_family',True),('destination_family',0xffffffff),('preserve_contents',False)])
def test_ownership_unknown(owner,field,value):
    owner[field]=value;assert m.ownership(owner)['status']=='UNKNOWN'

@pytest.fixture
def host():return dict(ordinary_mapped_write=True,write_happens_before_submission=True,host_domain_available=True,host_coherent=True,required_flush_completed=False,host_memory_model_ordered=True,device_read_in_submission_scope=True,no_inflight_conflicting_access=True)

def test_coherent_and_flushed_paths(host):
    assert m.host_write_submission(host)['status'].startswith('EXPLICIT_HOST_WRITE_BARRIER_NOT_REQUIRED')
    host.update(host_coherent=False,required_flush_completed=True)
    assert m.host_write_submission(host)['status'].startswith('EXPLICIT_HOST_WRITE_BARRIER_NOT_REQUIRED')
    host['required_flush_completed']=False
    assert m.host_write_submission(host)['status']=='UNKNOWN'

@pytest.mark.parametrize('field',['ordinary_mapped_write','write_happens_before_submission','host_domain_available','host_memory_model_ordered','device_read_in_submission_scope','no_inflight_conflicting_access'])
def test_host_unproven_not_shortcut(host,field):
    host[field]=False;assert m.host_write_submission(host)['status']=='UNKNOWN'

@pytest.mark.parametrize('function,arg',[(m.ownership,None),(m.ownership,{}),(m.host_write_submission,None),(m.host_write_submission,{})])
def test_extra_functions_missing(function,arg):assert function(arg)['status']=='UNKNOWN'

@pytest.mark.parametrize('value',[False,None,1])
def test_ownership_implicit_exception_unknown(owner,value):
    owner['baseline_no_implicit_transfer_exception']=value
    assert m.ownership(owner)['status']=='UNKNOWN'

def test_ownership_missing_exception_fact(owner):
    del owner['baseline_no_implicit_transfer_exception']
    assert m.ownership(owner)['status']=='UNKNOWN'
