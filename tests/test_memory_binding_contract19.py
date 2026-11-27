import pytest
from tools import memory_binding_contract19 as m
@pytest.fixture
def f():return dict(kind='buffer',resource_id='A',ordinary_scope_proven=True,allocation_creation_valid=True,same_device=True,requirements_size=256,requirements_alignment=64,memory_type_bits=2,memory_type_index=1,allocation_size=1024,offset=64,already_bound=False,requires_dedicated=False,prefers_dedicated=False,dedicated=None)
@pytest.mark.parametrize('kind',['buffer','image'])
def test_valid(f,kind):f['kind']=kind;assert m.bind(f)['status']=='BIND_CONDITIONS_WITHIN_SCOPE'
@pytest.mark.parametrize('key,value,suffix',[('offset',1,'01036'),('offset',1024,'01031'),('requirements_size',1024,'01037'),('memory_type_index',0,'01035'),('already_bound',True,'07459'),('requires_dedicated',True,'01444')])
def test_negative(f,key,value,suffix):f[key]=value;assert any(v.endswith(suffix) for v in m.bind(f)['vuids'])
def test_prefers_not_requires(f):f['prefers_dedicated']=True;assert m.bind(f)['status']=='BIND_CONDITIONS_WITHIN_SCOPE'
def test_dedicated(f):
 f.update(offset=0,requires_dedicated=True,dedicated=dict(kind='buffer',resource_id='A'))
 assert m.bind(f)['status']=='BIND_CONDITIONS_WITHIN_SCOPE'
 f['offset']=64;assert 'VUID-vkBindBufferMemory-memory-01508' in m.bind(f)['vuids']
def test_wrong_dedicated_resource(f):
 f.update(offset=0,dedicated=dict(kind='buffer',resource_id='B'))
 assert 'VUID-vkBindBufferMemory-memory-01508' in m.bind(f)['vuids']
@pytest.mark.parametrize('key,value',[('offset',True),('allocation_size',2**64),('requirements_alignment',3),('memory_type_index',32),('memory_type_bits',True),('ordinary_scope_proven',False),('same_device',False)])
def test_unknown(f,key,value):f[key]=value;assert m.bind(f)['status']=='UNKNOWN'
def pair(a_size,b_start):return dict(allocation_id='M',offset=0,requirements_size=a_size,linear=True),dict(allocation_id='M',offset=b_start,requirements_size=64,linear=False)
def test_page_not_distance():
 a,b=pair(255,256);assert m.granularity(a,b,256,True)['status']=='MIXED_PAGE_SEPARATION_SATISFIED'
def test_disjoint_but_same_page():
 a,b=pair(64,128);assert m.granularity(a,b,256,True)['status']=='ALIASING_RISK_NOT_BIND_VUID'
def test_same_class_or_serial():
 a,b=pair(64,128)
 assert m.granularity(a,b,256,False)['status']=='NO_MIXED_SIMULTANEOUS_PAGE_CONDITION'
 b['linear']=True;assert m.granularity(a,b,256,True)['status']=='NO_MIXED_SIMULTANEOUS_PAGE_CONDITION'
def test_granularity_one():
 a,b=pair(64,64);assert m.granularity(a,b,1,True)['status']=='MIXED_PAGE_SEPARATION_SATISFIED'
def test_overlap():
 a,b=pair(256,64);assert m.granularity(a,b,256,True)['status']=='OUT_OF_SCOPE_OVERLAPPING_RANGES'
def test_free_bound_allowed():
 f=dict(bound_object_count=2,all_submitted_uses_retired=True,host_accesses_completed=True,no_future_bound_resource_use=True,reference_inventory_complete=True)
 assert m.free_obligations(f)['status']=='FREE_LIFETIME_OBLIGATIONS_DECLARED'
 f['all_submitted_uses_retired']=False;assert m.free_obligations(f)['vuids']==['VUID-vkFreeMemory-memory-00677']
def test_free_future_use_not_allowed():
 f=dict(bound_object_count=1,all_submitted_uses_retired=True,host_accesses_completed=True,no_future_bound_resource_use=False,reference_inventory_complete=True)
 assert m.free_obligations(f)['status']=='LIFETIME_OBLIGATIONS_NOT_ESTABLISHED'
@pytest.mark.parametrize('kind',['buffer','image'])
def test_dedicated_version_split(kind):
 assert m.dedicated_allocation_size(kind,512,256,'1.4.309',True)['status']=='REJECTED'
 assert m.dedicated_allocation_size(kind,512,256,'1.4.368',True)['status']=='DEDICATED_SIZE_CONDITION_SATISFIED'
 for v in ('1.4.309','1.4.368'):
  assert m.dedicated_allocation_size(kind,256,256,v,True)['status']=='DEDICATED_SIZE_CONDITION_SATISFIED'
  assert m.dedicated_allocation_size(kind,128,256,v,True)['status']=='REJECTED'
def test_bind_does_not_assume_allocation_creation(f):
 f['allocation_creation_valid']=False
 assert m.bind(f)['status']=='UNKNOWN'

@pytest.mark.parametrize('change,expected',[
 ({'offset':1},['VUID-vkBindImageMemory-memoryOffset-01048']),
 ({'offset':1024},['VUID-vkBindImageMemory-memoryOffset-01046','VUID-vkBindImageMemory-size-01049']),
 ({'requirements_size':1024},['VUID-vkBindImageMemory-size-01049']),
 ({'memory_type_index':0},['VUID-vkBindImageMemory-memory-01047']),
 ({'already_bound':True},['VUID-vkBindImageMemory-image-07460']),
 ({'requires_dedicated':True},['VUID-vkBindImageMemory-image-01445']),
 ({'dedicated':{'kind':'image','resource_id':'A'}},['VUID-vkBindImageMemory-memory-02628']),
 ({'offset':0,'dedicated':{'kind':'image','resource_id':'B'}},['VUID-vkBindImageMemory-memory-02628']),
])
def test_image_negative_exact_reason(f,change,expected):
 f['kind']='image'
 assert m.bind(f)['status']=='BIND_CONDITIONS_WITHIN_SCOPE'
 f.update(change);r=m.bind(f)
 assert r['status']=='REJECTED' and r['vuids']==expected

@pytest.mark.parametrize('kind,owner_id',[('buffer','buffer-02965'),('image','image-02964')])
@pytest.mark.parametrize('version',['1.4.309','1.4.368'])
def test_dedicated_size_exact_reason(kind,owner_id,version):
 assert m.dedicated_allocation_size(kind,256,256,version,True)['vuids']==[]
 r=m.dedicated_allocation_size(kind,128,256,version,True)
 assert r['status']=='REJECTED' and r['vuids']==['VUID-VkMemoryDedicatedAllocateInfo-'+owner_id]
