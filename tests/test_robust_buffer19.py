import pathlib,sys,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.robust_buffer19 import access,admit,null_update

def config():return dict(extensionSupported=True,extensionEnabled=True,coreSupported=True,coreEnabled=True,robust2Supported=True,robust2Enabled=True,nullSupported=True,nullEnabled=True,ordinarySSBO=True,pipelineOverrideAbsent=True,storageAlignment=1,descriptorRange=16,sourceBufferSize=32,sourceOffset=0,maxStorageRange=65536,maxStageStorageBuffers=8,maxSetStorageBuffers=8,readIndex=4,writeIndex=5,outputRange=16)
def test_admit():assert admit(config())['status']=='ROBUST2_BUFFER_WITHIN_SCOPE'
@pytest.mark.parametrize('offset,op,result',[(0,'load','IN_BOUNDS'),(12,'load','IN_BOUNDS'),(16,'load','ZERO_REQUIRED'),(20,'store','DISCARD_REQUIRED'),(20,'atomic','OUT_OF_SCOPE')])
def test_access(offset,op,result):assert access(descriptor_range=16,alignment=1,byte_offset=offset,operation=op)['status']==result
@pytest.mark.parametrize('op',['load','store'])
def test_padding(op):assert access(descriptor_range=16,alignment=32,byte_offset=16,operation=op)['status']=='PADDING_OR_PARTIAL_NO_STRICT_ORACLE'
def test_same_invocation():
 assert access(descriptor_range=16,alignment=1,byte_offset=20,operation='load',prior_same_address_store=True)['status']=='PRIOR_STORE_VALUE_PERMITTED'
 assert access(descriptor_range=16,alignment=1,byte_offset=20,operation='load',prior_same_address_store=True,volatile=True)['status']=='ZERO_REQUIRED'
@pytest.mark.parametrize('k,v,result',[('coreEnabled',False,'REJECTED'),('robust2Enabled',False,'NOT_ENABLED'),('nullEnabled',False,'NOT_ENABLED'),('nullSupported',False,'UNSUPPORTED'),('extensionEnabled',False,'NOT_ENABLED'),('ordinarySSBO',False,'OUT_OF_SCOPE'),('pipelineOverrideAbsent',False,'OUT_OF_SCOPE'),('sourceOffset',4,'OUT_OF_SCOPE'),('readIndex',3,'OUT_OF_SCOPE'),('writeIndex',4,'OUT_OF_SCOPE'),('sourceBufferSize',16,'OUT_OF_SCOPE'),('maxStageStorageBuffers',2,'OUT_OF_SCOPE'),('maxStorageRange',8,'OUT_OF_SCOPE')])
def test_gates(k,v,result):
 m=config();m[k]=v;assert admit(m)['status']==result
@pytest.mark.parametrize('k,v',[('coreEnabled',1),('readIndex',True),('descriptorRange',-1),('readIndex',1<<32),('sourceBufferSize',1<<64),('storageAlignment',3)])
def test_invalid(k,v):
 m=config();m[k]=v
 with pytest.raises(ValueError):admit(m)
def test_unknown():assert admit({})['status']=='UNKNOWN'
def test_null():
 assert null_update(enabled=True,is_null=True,offset=0,whole_size=True)['vuids']==[]
 assert null_update(enabled=False,is_null=True,offset=0,whole_size=True)['vuids']==['VUID-VkDescriptorBufferInfo-buffer-02998']
 assert null_update(enabled=True,is_null=True,offset=4,whole_size=True)['vuids']==['VUID-VkDescriptorBufferInfo-buffer-02999']
def test_storage_alignment_four():
 m=config();m['storageAlignment']=4;assert admit(m)['status']=='ROBUST2_BUFFER_WITHIN_SCOPE'
def test_not_uniform_alignment():
 m=config();m['storageAlignment']=64
 with pytest.raises(ValueError):admit(m)

@pytest.mark.parametrize('kw',[{'descriptor_range':0},{'alignment':0},{'alignment':3},{'byte_offset':2},{'byte_offset':True},{'prior_same_address_store':1}])
def test_bad_access_facts(kw):
 m=dict(descriptor_range=16,alignment=4,byte_offset=16,operation='load');m.update(kw)
 with pytest.raises(ValueError):access(**m)
def test_no_overflow():assert access(descriptor_range=(1<<64)-1,alignment=4,byte_offset=16,operation='load')['status']=='OUT_OF_SCOPE'
def test_partial_uint32_not_zero_oracle():assert access(descriptor_range=15,alignment=4,byte_offset=12,operation='load')['status']=='PADDING_OR_PARTIAL_NO_STRICT_ORACLE'
def test_unknown_extra_field():
 m=config();m['trusted']=True;assert admit(m)['status']=='UNKNOWN'
