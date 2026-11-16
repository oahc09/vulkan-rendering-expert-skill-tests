import pytest
from tools import render_sample19 as r
@pytest.fixture
def facts():return dict(kind='two_pass',sameSourceView=True,sourceLayout=1,descriptorLayout=1,srcStage=1024,dstStage=128,srcAccess=256,dstAccess=32,sourceHostFilled=False,dependencyRecorded=True)
def test_good(facts):assert r.admit(facts)['status']=='WITHIN_SCOPE'
def test_missing(facts):
 facts['dependencyRecorded']=False;assert r.admit(facts)['status']=='MISSING_DEPENDENCY'
@pytest.mark.parametrize('key',['sameSourceView','sourceLayout','descriptorLayout','srcStage','dstStage','srcAccess','dstAccess','sourceHostFilled','dependencyRecorded'])
def test_missing_fact(facts,key):
 del facts[key];assert r.admit(facts)['status']=='UNKNOWN'
@pytest.mark.parametrize('bad',[None,[],{},True])
def test_shape(bad):assert r.admit(bad)['status']=='UNKNOWN'
def test_oracle():
 out=r.reference();src=r.source_reference();assert out!=src and len(out)==16
 assert out!=[out[x*4+y] for y in range(4) for x in range(4)]
 assert out!=list(reversed(out));assert out==[[p[2],p[0],p[1],p[3]] for p in src]

@pytest.fixture
def graphics_facts():
 p=dict(format=37,attachmentFormat=37,colorCount=1,samples=1,viewMask=0,vertexCount=3,instanceCount=1,stageCount=2,stageMask=17,topology=3,depthStencilPresent=0,firstVertex=0,firstInstance=0,blendEnable=0,writeMask=15,cullMode=0,rasterizerDiscard=0,viewport=[0,0,4,4],scissor=[0,0,4,4],unusedAttachmentsEnabled=False,maxColorAttachments=1)
 a=dict(usage=21,format=37);l=dict(framebufferWidth=4,framebufferHeight=4,viewportWidth=4,viewportHeight=4,viewportBoundsMin=0,viewportBoundsMax=4)
 assert r.graphics(p,a,l)
 return p,a,l
@pytest.mark.parametrize('field,value',[('maxColorAttachments',True),('viewport',[False,0,4,4]),('stageMask',17.0)])
def test_bad_graphics(graphics_facts,field,value):
 p,a,l=graphics_facts;p[field]=value;assert not r.graphics(p,a,l)
@pytest.mark.parametrize('value',[float('inf'),float('nan'),True,None])
def test_bad_limits(graphics_facts,value):
 p,a,l=graphics_facts;l['viewportWidth']=value;assert not r.graphics(p,a,l)
def test_bad_graphics_shape():assert not r.graphics(None,{}, {})
