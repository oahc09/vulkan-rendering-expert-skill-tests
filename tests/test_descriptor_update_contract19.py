import copy,pytest
from tools import descriptor_update_contract19 as m

def b(i,n=2,**kw):return dict(binding=i,count=n,type='UNIFORM_BUFFER',stages=1,flags=0,immutable_reference_signature=None,**kw)
def t(name='old',live=True,defined=True):return dict(reference=name,resource_live=live,defined=defined)
@pytest.fixture
def layout():return [b(0),b(1,0),b(2)]
@pytest.fixture
def sets(layout):return {n:dict(layout=copy.deepcopy(layout),values=[[t(),t()],[],[t(),t()]]) for n in ['A','B','C']}
def cp(src='A',dst='B',**kw):
 c=dict(src_set=src,src_binding=0,src_element=0,dst_set=dst,dst_binding=0,dst_element=0,count=1);c.update(kw);return c

def test_spill_skip_zero(layout):assert m.spill(layout,0,1,3)['coordinates']==[[0,1],[2,0],[2,1]]
@pytest.mark.parametrize('key,value',[('type','STORAGE_BUFFER'),('stages',16),('flags',1)])
def test_mismatch(layout,key,value):
 layout[2][key]=value;assert m.spill(layout,0,1,2)['status']=='REJECTED'
def test_immutable_references():
 a=[dict(b(i),type='SAMPLER',immutable_reference_signature='a'*64) for i in range(2)]
 assert m.spill(a,0,1,2)['status']=='ROUTE_WITHIN_SCOPE'
 a[1]['immutable_reference_signature']='b'*64
 assert m.spill(a,0,1,2)['status']=='REJECTED'
def test_capacity(layout):assert m.spill(layout,0,1,4)['status']=='REJECTED'
@pytest.mark.parametrize('args',[(True,0,1),(0,True,1),(0,0,True),(1,0,1),(0,2,1),(0,0,0),(0,0,2**32)])
def test_unknown_route(layout,args):assert m.spill(layout,*args)['status']=='UNKNOWN'
def test_sparse_unknown(layout):layout.pop(1);assert m.spill(layout,0,1,2)['status']=='UNKNOWN'
def test_writes_before_copies_and_order(sets):
 w=[dict(set='A',binding=0,element=0,type='UNIFORM_BUFFER',values=[t('first')]),dict(set='A',binding=0,element=0,type='UNIFORM_BUFFER',values=[t('last')])]
 r=m.apply(sets,w,[cp(),cp('B','C')],True)
 assert r['state_after']['C']['values'][0][0]['reference']=='last'
 assert [e['operation'] for e in r['events']]==['WRITE','WRITE','COPY','COPY']
 assert sets['A']['values'][0][0]['reference']=='old'
def test_overlap_spans_bindings(sets):assert m.apply(sets,[],[cp('A','A',src_element=1,dst_binding=2,count=2)],True)['vuids']==['VUID-VkCopyDescriptorSet-srcSet-00349']
def test_nonoverlap_same_set(sets):assert m.apply(sets,[],[cp('A','A',dst_binding=2)],True)['status']=='MODELED_UPDATES'
@pytest.mark.parametrize('live,defined',[(False,True),(True,False)])
def test_undefined_copy_not_resource_use(sets,live,defined):
 sets['A']['values'][0][0]=t('gone',live,defined);r=m.apply(sets,[],[cp()],True)
 assert r['state_after']['B']['values'][0][0]['defined'] is False and r['resource_use_performed'] is False

def test_type_mismatch(sets):
 for x in sets['B']['layout']:x['type']='STORAGE_BUFFER'
 assert m.apply(sets,[],[cp()],True)['vuids']==['VUID-VkCopyDescriptorSet-dstBinding-02632']
def test_unproven_safe_input(sets):assert m.apply(sets,[],[],False)['status']=='UNKNOWN'
def test_wrong_write_type(sets):assert m.apply(sets,[dict(set='A',binding=0,element=0,type='STORAGE_BUFFER',values=[t()])],[],True)['vuids']==['VUID-VkWriteDescriptorSet-descriptorType-00319']

@pytest.mark.parametrize('field',['resource_live','defined'])
def test_dead_or_undefined_write_not_copy_semantics(sets,field):
 w=dict(set='A',binding=0,element=0,type='UNIFORM_BUFFER',values=[t('new')])
 assert m.apply(sets,[w],[],True)['status']=='MODELED_UPDATES'
 w['values'][0][field]=False
 r=m.apply(sets,[w],[],True)
 assert r['status']=='UNKNOWN' and 'state_after' not in r
