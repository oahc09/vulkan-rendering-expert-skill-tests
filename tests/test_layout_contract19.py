import copy
import pytest
from tools import layout_contract19 as m

@pytest.fixture
def layout():return dict(scope='ORDINARY_COMPLETE_LAYOUTS',set_definitions=['1'*64,'2'*64,'3'*64],push_ranges=[dict(offset=0,size=16,stages=1)],max_push_constants=128,independent_sets=False)

def test_same_definitions_not_handles(layout):
    b=copy.deepcopy(layout)
    assert b is not layout and m.compatible(layout,b,2)['status']=='COMPATIBLE'

def test_prefix_not_just_n(layout):
    b=copy.deepcopy(layout);b['set_definitions'][0]='a'*64
    assert m.compatible(layout,b,2)['status']=='INCOMPATIBLE'

def test_suffix_irrelevant(layout):
    b=copy.deepcopy(layout);b['set_definitions'][2]='a'*64
    assert m.compatible(layout,b,1)['status']=='COMPATIBLE'

@pytest.mark.parametrize('field,value',[('independent_sets',True),('push_ranges',[dict(offset=4,size=16,stages=1)])])
def test_other_compat_requirements(layout,field,value):
    b=copy.deepcopy(layout);b[field]=value
    assert m.compatible(layout,b,1)['status']=='INCOMPATIBLE'

def test_push_only_ranges(layout):
    b=copy.deepcopy(layout);b.update(set_definitions=['a'*64],independent_sets=True)
    assert m.push_compatible(layout,b)['status']=='COMPATIBLE'

def test_ranges_order_irrelevant(layout):
    layout['push_ranges'].append(dict(offset=0,size=16,stages=16))
    b=copy.deepcopy(layout);b['push_ranges'].reverse()
    assert m.compatible(layout,b,0)['status']=='COMPATIBLE'

@pytest.mark.parametrize('off',[0,16])
def test_same_stage_forbidden_even_disjoint(off):
    r=m.push_ranges([dict(offset=0,size=16,stages=1),dict(offset=off,size=16,stages=1)],128)
    assert r['vuids']==['VUID-VkPipelineLayoutCreateInfo-pPushConstantRanges-00292']

def test_diff_stage_overlap():
    assert m.push_ranges([dict(offset=0,size=16,stages=1),dict(offset=0,size=16,stages=16)],128)['status']=='RANGES_WITHIN_SCOPE'

@pytest.mark.parametrize('offset,size,suffix',[(128,4,'00294'),(1,4,'00295'),(0,0,'00296'),(0,3,'00297'),(124,8,'00298')])
def test_range_vuids(offset,size,suffix):
    assert any(v.endswith(suffix) for v in m.push_ranges([dict(offset=offset,size=size,stages=1)],128)['vuids'])

@pytest.mark.parametrize('mutation',[{'scope':'PARTIAL_LIBRARY'},{'independent_sets':1},{'set_definitions':[None]},{'max_push_constants':True},{'push_ranges':None}])
def test_unknown(layout,mutation):
    b=copy.deepcopy(layout);b.update(mutation)
    assert m.compatible(layout,b,0)['status']=='UNKNOWN'

@pytest.mark.parametrize('number',[True,-1,3,2**32,None])
def test_unknown_set(layout,number):assert m.compatible(layout,layout,number)['status']=='UNKNOWN'

def test_lower_disturbance(layout):
    old=copy.deepcopy(layout);old['set_definitions'][0]='a'*64
    r=m.bind_disturbance({0:old,2:layout},layout,1)
    assert r['disturbed']==[0] and r['requires_prebound_pipeline'] is False

def test_old_n_incompat_disturbs_all_higher(layout):
    old=copy.deepcopy(layout);old['set_definitions'][1]='a'*64
    assert m.bind_disturbance({0:layout,1:old,2:layout},layout,1)['disturbed']==[2]

def test_compatible_old_n_higher_kept(layout):
    assert m.bind_disturbance({0:layout,1:layout,2:layout},layout,1)['disturbed']==[]

def test_pipeline_switch_does_not_mutate(layout):
    before=copy.deepcopy(layout)
    r=m.pipeline_access(layout,copy.deepcopy(layout),1,True)
    assert r['status']=='LAYOUT_ACCESS_PERMITTED' and r['bindings_mutated'] is False and layout==before
    assert m.pipeline_access(layout,layout,1,False)['status']=='LAYOUT_ACCESS_NOT_ESTABLISHED'

def test_update_bidirectional():
    ranges=[dict(offset=0,size=16,stages=1),dict(offset=8,size=16,stages=16)]
    assert m.push_update(ranges,1,0,8,128)['status']=='UPDATE_WITHIN_SCOPE'
    assert m.push_update(ranges,17,8,8,128)['status']=='UPDATE_WITHIN_SCOPE'
    assert m.push_update(ranges,1,8,8,128)['vuids']==['VUID-vkCmdPushConstants-offset-01796']
    assert m.push_update(ranges,17,0,8,128)['vuids']==['VUID-vkCmdPushConstants-offset-01795']
    assert m.push_update(ranges,32,8,8,128)['vuids']==['VUID-vkCmdPushConstants-offset-01795','VUID-vkCmdPushConstants-offset-01796']

@pytest.mark.parametrize('mask,offset,size',[(True,0,4),(0,0,4),(64,0,4),(1,True,4),(1,0,False),(1,1,4),(1,0,3),(1,128,4),(1,0,2**32)])
def test_update_unknown(layout,mask,offset,size):assert m.push_update(layout['push_ranges'],mask,offset,size,128)['status']=='UNKNOWN'

def test_empty_ranges_cannot_update():assert m.push_update([],1,0,4,128)['vuids']==['VUID-vkCmdPushConstants-offset-01795']
