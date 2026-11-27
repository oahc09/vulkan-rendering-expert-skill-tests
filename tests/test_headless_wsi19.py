import pathlib,sys,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.headless_wsi19 import admit,acquired,retirement

def config():return dict(minImages=4,maxImages=0,requestedImages=4,usage=3,supportedUsage=3,presentMode=2,format=37,colorSpace=0,selectedTransform=1,supportedTransforms=1,selectedCompositeAlpha=1,supportedCompositeAlpha=1,maxLayers=1,extent=[4,4],minExtent=[1,1],maxExtent=[16384,16384],currentExtent=[0xffffffff,0xffffffff],presentModes=[2],formats=[[37,0]],presentSupported=True,swapchainEnabled=True,maintenanceSupported=True,maintenanceEnabled=True)
def test_good():assert admit(config())['status']=='HEADLESS_WSI_WITHIN_SCOPE'
@pytest.mark.parametrize('k,v,status',[('requestedImages',3,'INVALID_IMAGE_COUNT'),('maxImages',3,'INVALID_IMAGE_COUNT'),('extent',[0,4],'INVALID_EXTENT'),('extent',[16385,4],'INVALID_EXTENT'),('currentExtent',[8,8],'FIXED_SURFACE_EXTENT'),('supportedUsage',2,'UNSUPPORTED_CONFIGURATION'),('maintenanceEnabled',False,'PRESENT_RETIREMENT_UNAVAILABLE'),('maintenanceSupported',False,'PRESENT_RETIREMENT_UNAVAILABLE'),('presentSupported',False,'UNSUPPORTED_PRESENT'),('selectedTransform',3,'UNSUPPORTED_CONFIGURATION'),('selectedCompositeAlpha',2,'UNSUPPORTED_CONFIGURATION'),('presentModes',[],'UNSUPPORTED_CONFIGURATION'),('formats',[],'UNSUPPORTED_CONFIGURATION'),('usage',16,'OUT_OF_SCOPE')])
def test_reject(k,v,status):
 m=config();m[k]=v;assert admit(m)['status']==status
@pytest.mark.parametrize('k,v',[('usage',True),('presentSupported',1),('extent',[False,4]),('maxImages',-1),('formats',[37])])
def test_types(k,v):
 m=config();m[k]=v
 with pytest.raises(ValueError):admit(m)
def test_unknown():assert admit({})['status']=='UNKNOWN'
@pytest.mark.parametrize('r',[0,1000001003])
def test_usable(r):assert acquired(r)['usable_image'] is True
@pytest.mark.parametrize('r',[1,2,-1000001004,-1000000000,-4,-999])
def test_no_index(r):assert acquired(r)['usable_image'] is False
def test_retire():assert retirement(generation=1,current_generation=1,render_fence=True,present_fence=True)['status']=='SERIAL_PRESENT_RETIRED'
def test_idle_not_present_proof():assert retirement(generation=1,current_generation=1,render_fence=True,present_fence=False,queue_idle=True)['status']=='WAIT_RETIREMENT'
def test_present_not_render_proof():assert retirement(generation=1,current_generation=1,render_fence=False,present_fence=True)['status']=='WAIT_RETIREMENT'
def test_stale():assert retirement(generation=0,current_generation=1,render_fence=True,present_fence=True)['status']=='STALE_GENERATION'

def test_bgra():
 m=config();m.update(format=44,formats=[[44,0]]);assert admit(m)['status']=='HEADLESS_WSI_WITHIN_SCOPE'
def test_finite_max():
 m=config();m.update(maxImages=5,requestedImages=5);assert admit(m)['status']=='HEADLESS_WSI_WITHIN_SCOPE'
def test_no_zero_count():
 m=config();m.update(minImages=0,requestedImages=0);assert admit(m)['status']=='INVALID_IMAGE_COUNT'
def test_fixed_extent_match():
 m=config();m['currentExtent']=[4,4];assert admit(m)['status']=='HEADLESS_WSI_WITHIN_SCOPE'
def test_bad_mode_enum():
 m=config();m['presentModes']=[-1]
 with pytest.raises(ValueError):admit(m)

def test_suboptimal_usable_but_recreate():assert acquired(1000001003)=={'usable_image':True,'recreate_after_retirement':True}
@pytest.mark.parametrize('r,action',[(1,'RETRY_WITHOUT_WAIT'),(2,'RETRY_WITHOUT_WAIT'),(-1000001004,'RECREATE'),(-1000000000,'RECREATE_SURFACE'),(-4,'DEVICE_LOST'),(-999,'STOP_UNKNOWN')])
def test_error_actions(r,action):assert acquired(r)['action']==action
@pytest.mark.parametrize('kwargs',[{'generation':True},{'render_fence':1},{'current_generation':-1}])
def test_retirement_types(kwargs):
 m=dict(generation=0,current_generation=0,render_fence=True,present_fence=True);m.update(kwargs)
 with pytest.raises(ValueError):retirement(**m)
