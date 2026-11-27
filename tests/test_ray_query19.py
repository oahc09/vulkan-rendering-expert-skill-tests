import pathlib,sys,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.ray_query19 import scratch,create,triangle_reference

def sc():return dict(address=4096,buffer_address=4096,buffer_size=264,required_size=256,alignment=8,storage_usage=True,bda_usage=True)
def test_scratch():assert scratch(**sc())['status']=='SCRATCH_WITHIN_SCOPE'
@pytest.mark.parametrize('k,v,suffix',[('address',4097,'03710'),('buffer_size',255,'03671'),('address',4088,'03671'),('storage_usage',False,'03674')])
def test_scratch_negative(k,v,suffix):
 m=sc();m[k]=v;assert scratch(**m)['vuids']==['VUID-vkCmdBuildAccelerationStructuresKHR-pInfos-'+suffix]
def test_overflow():
 m=sc();m.update(buffer_address=(1<<64)-8,address=(1<<64)-8);assert scratch(**m)['status']=='REJECTED'
@pytest.mark.parametrize('k,v',[('alignment',True),('buffer_size',-1),('bda_usage',1)])
def test_bad_types(k,v):
 m=sc();m[k]=v
 with pytest.raises(ValueError):scratch(**m)
def test_unknown_alignment():
 m=sc();m['alignment']=0;assert scratch(**m)['status']=='UNKNOWN'
def test_create_offset():assert create(offset=1,size=256,buffer_size=512,storage_usage=True)['vuids']==['VUID-VkAccelerationStructureCreateInfoKHR-offset-03734']
def test_create_range():assert create(offset=0,size=512,buffer_size=512,storage_usage=True)['vuids']==['VUID-VkAccelerationStructureCreateInfoKHR-offset-03616']
def test_create_good():assert create(offset=0,size=256,buffer_size=512,storage_usage=True)['status']=='CREATE_WITHIN_SCOPE'
@pytest.mark.parametrize('o,d,lo,hi,hit',[([0,0,1],[0,0,-1],.1,10,True),([3,0,1],[0,0,-1],.1,10,False),([0,0,1],[1,0,0],.1,10,False),([0,0,1],[0,0,-1],.1,.5,False),([0,0,-1],[0,0,1],.1,10,True)])
def test_oracle(o,d,lo,hi,hit):assert triangle_reference(o,d,lo,hi)['hit']==hit
def test_hit_values():assert triangle_reference([0,0,1],[0,0,-1],.1,10)==dict(hit=True,t=1.,primitive=0,customIndex=7)
@pytest.mark.parametrize('o,d,lo,hi',[([0,0,1],[0,0,0],.1,10),([float('nan'),0,1],[0,0,-1],.1,10),([0,0,1],[0,0,-1],10,.1),([0,0,1],[0,0,-1],-1,10)])
def test_invalid_ray(o,d,lo,hi):
 with pytest.raises(ValueError):triangle_reference(o,d,lo,hi)

def test_null_address():
 m=sc();m.update(address=0,buffer_address=0);assert scratch(**m)['status']=='UNKNOWN'
def test_empty_as_out_of_scope():assert create(offset=0,size=0,buffer_size=512,storage_usage=True)['status']=='OUT_OF_SCOPE'
def test_aligned_end_range_allowed():
 m=sc();m.update(address=4104);assert scratch(**m)['status']=='SCRATCH_WITHIN_SCOPE'
def test_one_byte_short():
 m=sc();m.update(address=4104,buffer_size=263);assert scratch(**m)['vuids']==['VUID-vkCmdBuildAccelerationStructuresKHR-pInfos-03671']
