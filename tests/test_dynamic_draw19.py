import sys,pathlib,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.dynamic_draw19 import admit,reference,VUID

def inputs():return (dict(format=37,attachmentFormat=37,colorCount=1,samples=1,viewMask=0,unusedAttachmentsEnabled=False,vertexCount=3,instanceCount=1,viewport=[0,0,4,4],scissor=[0,0,4,4],maxColorAttachments=8,blendEnable=0,writeMask=15,cullMode=0,rasterizerDiscard=0,stageCount=2,stageMask=17,topology=3,depthStencilPresent=0,firstVertex=0,firstInstance=0),dict(format=37,samples=1,viewMask=0,enabled=1,layers=1,resolveMode=0,usage=17,width=4,height=4,viewWidth=4,viewHeight=4,layout=2,offsetX=0,offsetY=0,loadOp=1,storeOp=0),dict(framebufferWidth=16,framebufferHeight=16,viewportWidth=16,viewportHeight=16,viewportBoundsMin=-16,viewportBoundsMax=16))
def test_good():assert admit(*inputs())['status']=='DRAW_CONFIG_WITHIN_SCOPE'
def test_mismatch():
 p,a,l=inputs();p['format']=44;assert admit(p,a,l)['vuids']==[VUID]
@pytest.mark.parametrize('key,val',[('samples',4),('colorCount',2),('viewMask',1),('unusedAttachmentsEnabled',True),('vertexCount',4),('instanceCount',2),('viewport',[1,0,4,4]),('scissor',[0,0,2,4]),('blendEnable',1),('writeMask',3),('cullMode',1),('rasterizerDiscard',1),('stageCount',1)])
def test_scope(key,val):
 p,a,l=inputs();p[key]=val;assert admit(p,a,l)['status']=='OUT_OF_SCOPE'
@pytest.mark.parametrize('index',[0,1,2])
def test_missing(index):
 args=list(inputs());args[index]={};assert admit(*args)['status']=='UNKNOWN'
@pytest.mark.parametrize('key',['framebufferWidth','framebufferHeight','viewportWidth','viewportHeight'])
def test_limit(key):
 p,a,l=inputs();l[key]=3;assert admit(p,a,l)['status']=='UNSUPPORTED_LIMITS'
def test_reference_nonconstant():
 r=reference();assert len(r)==16;assert r!=[[255,0,255,255]]*16;assert r!=[[0,0,255,255] if x==[255,0,0,255] else [255,0,0,255] for x in r]
def test_reference_flipped_y():
 r=reference();assert r!=sum([r[y*4:y*4+4] for y in reversed(range(4))],[])

@pytest.mark.parametrize('index,key,value',[(1,'enabled',True),(2,'viewportBoundsMin',float('nan')),(0,'viewport',[False,0,4,4])])
def test_untrusted_numeric(index,key,value):
 args=list(inputs());args[index][key]=value
 with pytest.raises(ValueError):admit(*args)

def test_unknown_matching_format():
 p,a,l=inputs();p['format']=p['attachmentFormat']=a['format']=999;assert admit(p,a,l)['status']=='OUT_OF_SCOPE'

@pytest.mark.parametrize('k,v',[('layers',2),('resolveMode',1),('usage',1),('width',2),('layout',1)])
def test_attachment_scope(k,v):
 p,a,l=inputs();a[k]=v;assert admit(p,a,l)['status']=='OUT_OF_SCOPE'

@pytest.mark.parametrize('k,v',[('stageMask',1),('topology',0),('depthStencilPresent',1),('firstVertex',1),('firstInstance',1)])
def test_actual_pipeline_fields(k,v):
 p,a,l=inputs();p[k]=v;assert admit(p,a,l)['status']=='OUT_OF_SCOPE'
