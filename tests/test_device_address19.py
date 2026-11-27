import pathlib,sys,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.device_address19 import admit,validate_range,retire,special_availability

def facts():return dict(supported=True,enabled=True,shader_int64_enabled=True,usage=0x20020,allocation_flags=2,bound=True,api_version=4202496)
def span():return dict(base=4096,size=256,address=4112,length=64,alignment=16,live=True,retired=False)
def test_good():assert admit(**facts())['status']=='BDA_PREREQUISITES_WITHIN_SCOPE'
@pytest.mark.parametrize('key,value,status',[('supported',False,'UNSUPPORTED'),('enabled',False,'FEATURE_NOT_ENABLED'),('shader_int64_enabled',False,'FEATURE_NOT_ENABLED'),('usage',32,'MISSING_ADDRESS_USAGE'),('allocation_flags',0,'MISSING_ADDRESS_ALLOCATION'),('bound',False,'BUFFER_NOT_BOUND'),('api_version',4198400,'OUT_OF_SCOPE_CORE_1_2'),('api_version',1<<29|4202496,'OUT_OF_SCOPE_CORE_1_2')])
def test_admission(key,value,status):
 f=facts();f[key]=value;assert admit(**f)['status']==status
@pytest.mark.parametrize('key,value',[('supported',1),('usage',True),('allocation_flags',-1),('api_version',1<<32)])
def test_bad_type(key,value):
 f=facts();f[key]=value
 with pytest.raises(ValueError):admit(**f)
def test_valid_range():assert validate_range(**span())['status']=='ADDRESS_WITHIN_KNOWN_LIVE_BUFFER'
@pytest.mark.parametrize('key,value,status',[('live',False,'DEAD_ALLOCATION'),('retired',True,'RETIRED_GENERATION'),('address',4113,'MISALIGNED_ADDRESS'),('address',4080,'OUT_OF_BOUNDS'),('length',256,'OUT_OF_BOUNDS'),('size',0,'INVALID_RANGE'),('address',0,'INVALID_RANGE'),('length',0,'INVALID_RANGE'),('base',(1<<64)-16,'ADDRESS_OVERFLOW'),('length',(1<<64)-1,'ADDRESS_OVERFLOW')])
def test_range_failure(key,value,status):
 f=span();f[key]=value;assert validate_range(**f)['status']==status
@pytest.mark.parametrize('key,value',[('size',True),('length',-1),('base',1<<64),('alignment',3),('alignment',0),('live',1)])
def test_range_type(key,value):
 f=span();f[key]=value
 with pytest.raises(ValueError):validate_range(**f)
def test_boundary():
 f=span();f.update(address=4288,length=64);assert validate_range(**f)['status']=='ADDRESS_WITHIN_KNOWN_LIVE_BUFFER'
@pytest.mark.parametrize('s,v,f,status',[(False,False,False,'NOT_SUBMITTED'),(True,True,False,'KEEP_BUFFERS_AND_POINTER_TABLE_LIVE'),(True,False,True,'HOST_VISIBILITY_NOT_PROVEN'),(True,True,True,'BOUNDED_READBACK_READY')])
def test_retire(s,v,f,status):assert retire(submitted=s,write_visible=v,fence_complete=f)['status']==status
def test_no_robustness_inheritance():assert validate_range(**span())['robustness_guarantee'] is False
def test_special_unknown():assert special_availability({},['VK_KHR_video_queue'])['status']=='NOT_QUERIED'
def test_special_absent():assert special_availability({'VK_KHR_video_queue':False},['VK_KHR_video_queue'])['status']=='UNSUPPORTED_EXTENSION'
def test_special_not_execution():assert special_availability({'VK_KHR_video_queue':True},['VK_KHR_video_queue'])=={'status':'FEATURE_PROFILE_QUERY_REQUIRED','executed':False}
def test_special_invalid():
 with pytest.raises(ValueError):special_availability({'VK_FOO':1},['VK_FOO'])
def test_preserve_table_until_fence():assert retire(submitted=True,write_visible=True,fence_complete=False)['status']=='KEEP_BUFFERS_AND_POINTER_TABLE_LIVE'

def test_pointer_member_alignment_is_not_base_alignment():
 f=span();f.update(base=4096,size=16,address=4104,length=8,alignment=8)
 assert validate_range(**f)['status']=='ADDRESS_WITHIN_KNOWN_LIVE_BUFFER'
 f['alignment']=16
 assert validate_range(**f)['status']=='MISALIGNED_ADDRESS'
def test_uint_array_stride_access():
 f=span();f.update(address=4100,length=4,alignment=4)
 assert validate_range(**f)['status']=='ADDRESS_WITHIN_KNOWN_LIVE_BUFFER'
def test_zero_address_even_with_large_buffer():
 f=span();f.update(base=0,address=16)
 assert validate_range(**f)['status']=='INVALID_RANGE'
def test_feature_support_not_enable():
 f=facts();f['enabled']=False
 assert admit(**f)['status']=='FEATURE_NOT_ENABLED'
def test_unknown_special_owner_is_not_missing_support():
 assert special_availability({'VK_KHR_video_queue':False},['VK_KHR_video_decode_queue'])['status']=='NOT_QUERIED'
