import pathlib,sys,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.external_memory19 import admit,transition

def config():
 return dict(handleType=1,usage=3,flags=0,exportFeatures=6,importFeatures=6,exportCompatible=1,importCompatible=1,exportTypes=3,importTypes=1,memoryTypeIndex=0,importMemoryTypeIndex=0,exportRequirementSize=256,importRequirementSize=256,exportBufferSize=256,importBufferSize=256,exportSharingMode=0,importSharingMode=0,exportHandleTypes=1,importHandleTypes=1,exportSize=256,importSize=256,exportRequiresDedicated=False,importRequiresDedicated=False,exportDedicated=False,importDedicated=False,sameDeviceUUID=True,sameDriverUUID=True,memoryFdEnabled=True)
def test_admission_is_not_execution():
 r=admit(config());assert r['status']=='MEMORY_IMPORT_WITHIN_SCOPE';assert r['execution_visibility']=='NOT_PROVEN'
@pytest.mark.parametrize('k,v,status', [('handleType',512,'OUT_OF_SCOPE'),('usage',35,'OUT_OF_SCOPE'),('flags',1,'OUT_OF_SCOPE'),('exportFeatures',4,'UNSUPPORTED_HANDLE'),('importFeatures',2,'UNSUPPORTED_HANDLE'),('exportCompatible',0,'UNSUPPORTED_HANDLE'),('importCompatible',0,'UNSUPPORTED_HANDLE'),('memoryFdEnabled',False,'UNSUPPORTED_HANDLE'),('sameDeviceUUID',False,'INCOMPATIBLE_IDENTITY'),('sameDriverUUID',False,'INCOMPATIBLE_IDENTITY'),('memoryTypeIndex',32,'INCOMPATIBLE_MEMORY_TYPE'),('importTypes',2,'INCOMPATIBLE_MEMORY_TYPE'),('importSize',128,'INCOMPATIBLE_ALLOCATION'),('exportSize',0,'INCOMPATIBLE_ALLOCATION'),('exportRequiresDedicated',True,'DEDICATED_REQUIRED'),('importFeatures',7,'DEDICATED_REQUIRED')])
def test_reject(k,v,status):
 m=config();m[k]=v;assert admit(m)['status']==status
@pytest.mark.parametrize('k,v',[('usage',True),('memoryFdEnabled',1),('exportSize',1<<64),('exportTypes',-1)])
def test_types(k,v):
 m=config();m[k]=v
 with pytest.raises(ValueError):admit(m)
def test_unknown():
 assert admit({})['status']=='UNKNOWN';m=config();m['invented']=1;assert admit(m)['status']=='UNKNOWN'
def test_dedicated():
 m=config();m.update(exportDedicated=True,importDedicated=True,exportRequiresDedicated=True,importFeatures=7);assert admit(m)['status']=='MEMORY_IMPORT_WITHIN_SCOPE'
def test_transfer():
 assert transition('ABSENT','export_success')['state']=='APP_OWNED';assert transition('APP_OWNED','import_success')['state']=='IMPLEMENTATION_OWNED'
@pytest.mark.parametrize('event',['close','import_success','query_aborted','export_success'])
def test_no_use_after_transfer(event):assert transition('IMPLEMENTATION_OWNED',event)['status']=='REJECTED_OWNERSHIP_TRANSITION'
def test_failure_does_not_consume():
 assert transition('APP_OWNED','import_failure')['state']=='APP_OWNED';assert transition('APP_OWNED','query_aborted')['state']=='APP_OWNED'
def test_unique_close():
 assert transition('APP_OWNED','close')['state']=='CLOSED';assert transition('CLOSED','close')['status']=='REJECTED_OWNERSHIP_TRANSITION'

@pytest.mark.parametrize('k,v,status',[('importMemoryTypeIndex',1,'INCOMPATIBLE_MEMORY_TYPE'),('importBufferSize',128,'OUT_OF_SCOPE'),('importSharingMode',1,'OUT_OF_SCOPE'),('exportHandleTypes',0,'OUT_OF_SCOPE'),('importRequirementSize',512,'INCOMPATIBLE_ALLOCATION')])
def test_paired_facts(k,v,status):
 m=config();m[k]=v;assert admit(m)['status']==status
def test_dedicated_requires_exact_size():
 m=config();m.update(exportSize=512,importSize=512,exportDedicated=True,importDedicated=True);assert admit(m)['status']=='INCOMPATIBLE_ALLOCATION'
