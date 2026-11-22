import pytest
from tools import msaa_sample19 as r
@pytest.fixture
def facts():
 m=dict(sourceFormat=37,resolveFormat=37,resolveMode=2,sourceLayout=1,resolveLayout=1,storeOp=0,resolveSamples=1,sourcePipelineSamples=4,sourceSampleShading=0,postPipelineSamples=1,distinctImages=True,sampledResolveView=True,sourceSamples=4)
 f=dict(format=37,usage=16,samples=4,supportedSamples=5,maxWidth=4096,maxHeight=4096,maxLayers=1);c=dict(colorSampleCounts=5)
 assert r.admit(m,f,c)==dict(status='WITHIN_SCOPE',vuids=[])
 return m,f,c
def test_positive(facts):assert r.admit(*facts)['status']=='WITHIN_SCOPE'
def test_actual_negative(facts):
 m,f,c=facts;m['sourceSamples']=f['samples']=1
 assert r.admit(m,f,c)==dict(status='REJECTED',vuids=[r.VUID])
@pytest.mark.parametrize('field',['sourceFormat','resolveFormat','resolveMode','sourceLayout','resolveLayout','storeOp','resolveSamples','sourcePipelineSamples','sourceSampleShading','postPipelineSamples','distinctImages','sampledResolveView','sourceSamples'])
def test_missing(facts,field):
 m,f,c=facts;del m[field];assert r.admit(m,f,c)['status']=='UNKNOWN'
@pytest.mark.parametrize('field,value',[('sourceSamples',True),('resolveSamples',4),('resolveMode',1),('sourceFormat',44),('distinctImages',False),('sampledResolveView',False),('sourceSampleShading',1)])
def test_wrong_fact(facts,field,value):
 m,f,c=facts;m[field]=value;assert r.admit(m,f,c)['status']=='UNKNOWN'
def test_unsupported(facts):
 m,f,c=facts;f['supportedSamples']=1;assert r.admit(m,f,c)['status']=='UNSUPPORTED'
@pytest.mark.parametrize('bad',[None,[],True,{}])
def test_shape(facts,bad):
 m,f,c=facts;assert r.admit(bad,f,c)['status']=='UNKNOWN'
