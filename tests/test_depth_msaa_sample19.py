import pytest
from tools import depth_msaa_sample19 as r
@pytest.fixture
def facts():
 m=dict(viewFormat=126,pipelineFormat=126,samples=4,testEnable=1,writeEnable=1,compareOp=1,boundsEnable=0,stencilEnable=0,layout=3,loadOp=1,storeOp=0,resolveMode=0,aspect=2,pushStage=16,pushSize=4,maxPushSize=128,unusedAttachmentsEnabled=False,clearDepth=1.)
 f=dict(format=126,usage=32,samples=4,supportedSamples=5,maxWidth=4096,maxHeight=4096,maxLayers=1);c=dict(depthSampleCounts=5)
 assert r.admit(m,f,c)==dict(status='WITHIN_SCOPE',vuids=[])
 return m,f,c
def test_good(facts):assert r.admit(*facts)['status']=='WITHIN_SCOPE'
def test_mismatch(facts):
 m,f,c=facts;m['pipelineFormat']=124;assert r.admit(m,f,c)==dict(status='REJECTED',vuids=[r.VUID])
def test_disabled(facts):
 m,f,c=facts;m['testEnable']=0;assert r.admit(m,f,c)==dict(status='DEPTH_DISABLED_CONTROL',vuids=[])
@pytest.mark.parametrize('key',['viewFormat','samples','writeEnable','compareOp','boundsEnable','stencilEnable','layout','loadOp','storeOp','resolveMode','aspect','pushStage','pushSize','maxPushSize','unusedAttachmentsEnabled','clearDepth','pipelineFormat','testEnable'])
def test_missing(facts,key):
 m,f,c=facts;del m[key];assert r.admit(m,f,c)['status']=='UNKNOWN'
@pytest.mark.parametrize('value',[True,float('nan'),float('inf'),None])
def test_bad_clear(facts,value):
 m,f,c=facts;m['clearDepth']=value;assert r.admit(m,f,c)['status']=='UNKNOWN'
def test_unsupported(facts):
 m,f,c=facts;f['supportedSamples']=1;assert r.admit(m,f,c)['status']=='UNSUPPORTED'
@pytest.mark.parametrize('bad',[None,[],True,{}])
def test_shape(facts,bad):
 m,f,c=facts;assert r.admit(bad,f,c)['status']=='UNKNOWN'
def test_oracle():
 good=r.reference();disabled=r.reference(False)
 assert len(good)==16 and good!=disabled
 assert disabled==[[255,0,255,255]]*16
 assert good!=[good[x*4+y] for y in range(4) for x in range(4)]
 assert good!=list(reversed(good))
 assert sum(p==[0,255,0,255] for p in good)==7
