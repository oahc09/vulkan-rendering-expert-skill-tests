import copy
import pytest
from tools import image_layout_contract19 as m
from tools import image_layout_prose19 as p
@pytest.fixture
def state():return [dict(mip=0,layer=0,layout='GENERAL',defined=True),dict(mip=1,layer=0,layout='TRANSFER_SRC_OPTIMAL',defined=True)]
@pytest.fixture
def barrier():return dict(api='barrier2',sync2_enabled=True,source_family=0xffffffff,destination_family=0xffffffff,old_layout='GENERAL',new_layout='TRANSFER_DST_OPTIMAL',subresources=[[0,0]])
@pytest.fixture
def facts():return {k:True for k in m.FACT_KEYS}

def test_selected_state_only(state,barrier,facts):
 before=copy.deepcopy(state);r=m.evaluate(state,barrier,facts)
 assert r['status']=='MODELED_TRANSITION' and r['state_after'][0]['layout']=='TRANSFER_DST_OPTIMAL'
 assert r['state_after'][1]==state[1] and state==before

@pytest.mark.parametrize('api',['legacy','barrier2'])
@pytest.mark.parametrize('layout',['UNDEFINED','GENERAL','TRANSFER_DST_OPTIMAL'])
def test_sync2_equal_ignored_not_actual(state,barrier,facts,api,layout):
 barrier.update(api=api,old_layout=layout,new_layout=layout,subresources=[[0,0],[1,0]])
 r=m.evaluate(state,barrier,facts)
 assert r['status']=='MODELED_LAYOUTS_IGNORED' and r['state_after']==state and r['content_preservation_not_guaranteed'] is False

def test_legacy_no_feature_same_layout_checks_old(state,barrier,facts):
 barrier.update(api='legacy',sync2_enabled=False,old_layout='TRANSFER_DST_OPTIMAL',new_layout='TRANSFER_DST_OPTIMAL')
 assert m.evaluate(state,barrier,facts)['vuids']==['VUID-VkImageMemoryBarrier-oldLayout-01197']

def test_legacy_equal_matching_is_transition(state,barrier,facts):
 barrier.update(api='legacy',sync2_enabled=False,new_layout='GENERAL')
 assert m.evaluate(state,barrier,facts)['status']=='MODELED_TRANSITION'

def test_discard_not_preserve(state,barrier,facts):
 barrier['old_layout']='UNDEFINED'
 r=m.evaluate(state,barrier,facts)
 assert r['status']=='MODELED_TRANSITION' and r['state_after'][0]['defined'] is False
 assert r['state_after'][1]['defined'] is True

@pytest.mark.parametrize('key',['prior_accesses_ordered_before_transition','prior_writes_available','next_accesses_ordered_after_transition','transition_writes_visible_to_next_access'])
def test_discard_still_needs_dependency(state,barrier,facts,key):
 barrier['old_layout']='UNDEFINED';facts[key]=False
 r=m.evaluate(state,barrier,facts)
 assert r['status']=='INSUFFICIENT_DEPENDENCY' and 'state_after' not in r

def test_equal_ignored_not_sync_success(state,barrier,facts):
 barrier['new_layout']='GENERAL';facts['ignored_barrier_dependencies_sufficient']=False
 assert m.evaluate(state,barrier,facts)['status']=='INSUFFICIENT_DEPENDENCY'

def test_all_cells_old_match(state,barrier,facts):
 barrier['subresources']=[[0,0],[1,0]]
 assert m.evaluate(state,barrier,facts)['vuids']==['VUID-VkImageMemoryBarrier2-oldLayout-01197']

@pytest.mark.parametrize('new',['UNDEFINED','PREINITIALIZED'])
def test_transition_invalid_new(state,barrier,facts,new):
 barrier['new_layout']=new
 assert m.evaluate(state,barrier,facts)['vuids']==['VUID-VkImageMemoryBarrier2-newLayout-01198']

@pytest.mark.parametrize('key,value',[('api','unknown'),('sync2_enabled',False),('sync2_enabled',1),('source_family',True),('destination_family',1),('source_family',0xfffffffe),('subresources',[]),('subresources',[[0,0],[0,0]]),('subresources',[[3,0]]),('subresources',[[True,0]])])
def test_unknown_barrier(state,barrier,facts,key,value):
 barrier[key]=value;assert m.evaluate(state,barrier,facts)['status']=='UNKNOWN'

@pytest.mark.parametrize('key',sorted(m.FACT_KEYS))
def test_missing_facts(state,barrier,facts,key):
 del facts[key];assert m.evaluate(state,barrier,facts)['status']=='UNKNOWN'

def test_malformed(state,barrier,facts):
 assert m.evaluate(None,barrier,facts)['status']=='UNKNOWN'
 state.append(copy.deepcopy(state[0]));assert m.evaluate(state,barrier,facts)['status']=='UNKNOWN'

def test_wrong_prose():
 with pytest.raises(ValueError):p.extract(b'not official pinned source')
