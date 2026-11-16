import importlib.util,pathlib,pytest,json
P=pathlib.Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('secondary',P/'tools/secondary_draw19.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def args():return [dict(level=1,beginFlags=2,renderPassNull=True,renderingFlags=0,viewMask=0,colorCount=1,colorFormat=37,samples=1,depthFormat=0,stencilFormat=0,queueFamily=0,secondaryExecutable=True),dict(primaryRenderingFlags=1,count=1,primaryQueueFamily=0),dict(format=37),dict(format=37)]
def test_good_negative():
 a=args();assert m.admit(*a)==dict(status='SECONDARY_WITHIN_SCOPE',vuids=[]);a[0]['colorFormat']=44;a[3]['format']=44;assert m.admit(*a)==dict(status='REJECTED',vuids=[m.VUID])
@pytest.mark.parametrize('key',list(args()[0]))
def test_missing(key):
 a=args();a[0].pop(key);assert m.admit(*a)['status']=='UNKNOWN'
@pytest.mark.parametrize('key,value',[('level',0),('beginFlags',0),('samples',4),('viewMask',1),('colorCount',2),('colorFormat',999)])
def test_outside(key,value):
 a=args();a[0][key]=value;assert m.admit(*a)['status']=='OUT_OF_SCOPE'
@pytest.mark.parametrize('value',[True,-1,2**32,None,'1'])
def test_numeric(value):
 a=args();a[0]['samples']=value;assert m.admit(*a)['status']=='UNKNOWN'
def test_wrong_queue_and_pipeline():
 a=args();a[1]['primaryQueueFamily']=1;assert m.admit(*a)['status']=='OUT_OF_SCOPE';a=args();a[3]['format']=44;assert m.admit(*a)['status']=='OUT_OF_SCOPE'
def test_oracle_not_symmetric_or_constant():
 p=m.reference();assert len(p)==16 and p!=[p[x*4+y] for y in range(4) for x in range(4)] and p!=list(reversed(p)) and len({tuple(x) for x in p})==2
 assert p!=[[1,0,1,1]]*16
def test_normative():
 n=json.loads((P/'cases19/secondary_draw/normative.json').read_text());assert n['entry']['vuid']==m.VUID and n['owner']=='vkCmdExecuteCommands'
@pytest.mark.parametrize('index',[2,3])
@pytest.mark.parametrize('value',[None,[],{},dict(format=True),dict(format='37')])
def test_attachment_pipeline_shape(index,value):
 a=args();a[index]=value;assert m.admit(*a)==dict(status='UNKNOWN',vuids=[])
def runner():
 s=importlib.util.spec_from_file_location('secondary_run',P/'cases19/secondary_draw/run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r);return r
@pytest.mark.parametrize('field,value',[('stageMask',0),('samples',4),('vertexCount',0),('viewport',[0,0,3,4]),('blendEnable',True)])
def test_secondary_negative_common_fields(field,value):
 # Complete host configuration baseline, then mutate a single field.
 r=runner();p=dict(colorCount=1,samples=1,viewMask=0,vertexCount=3,instanceCount=1,blendEnable=0,writeMask=15,cullMode=0,rasterizerDiscard=0,stageCount=2,stageMask=17,topology=3,depthStencilPresent=0,firstVertex=0,firstInstance=0,attachmentFormat=37,format=44,unusedAttachmentsEnabled=False,maxColorAttachments=8,viewport=[0,0,4,4],scissor=[0,0,4,4]);rec={'pipeline':p,'inheritance':dict(colorFormat=44,samples=1,colorCount=1,viewMask=0),'limits':dict(framebufferWidth=4096,framebufferHeight=4096,viewportWidth=4096,viewportHeight=4096,viewportBoundsMin=-8192,viewportBoundsMax=8192)}
 assert r.validate_secondary_graphics(rec)['status']=='SECONDARY_GRAPHICS_FIXED_FIELDS_VALID';p[field]=value
 with pytest.raises(ValueError):r.validate_secondary_graphics(rec)
def lifecycle_fixture():
 return {'generation_retired':dict(kind='generation_retired',generation=0,renderFenceSuccess=True),'generation_recorded':dict(kind='generation_recorded',generation=1,secondaryResetAfterFence=True,scissor=[0,0,2,4],pipelineOrdinal=1),'generation_identity':dict(kind='generation_identity',primaryBeginFlags=0,primaryRecordedGeneration=0,secondaryGeneration=1,samePrimary=True,sameSecondary=True,sameImage=True,sameReadback=True,sameFence=True),'stale_fence':dict(kind='stale_fence',status=1),'stale_attempt':dict(kind='stale_attempt',apiResult=-1000011001,newErrors=1,submitted=False),'primary_rebuilt':dict(kind='primary_rebuilt',recordedGeneration=1,secondaryGeneration=1,oldLayout=6),'generation_execution':dict(kind='generation_execution',generation=1,primaryRerecorded=True,submitted=True,fenceCompleted=True,pixels=m.second_reference()),'generation_dependency':dict(kind='generation_dependency',oldLayout=6,newLayout=2,srcAccess=2048,dstAccess=384,srcStage=4096,dstStage=1024,aspect=1,levels=1,layers=1)}
def test_lifecycle_and_distinct_second_image():
 x=lifecycle_fixture();assert m.lifecycle(x)['status']=='RETIRED_SECONDARY_RERECORD_PRIMARY_REBUILD_VERIFIED';assert m.second_reference()!=m.reference();assert all(m.second_reference()[i]==[255,0,255,255] for i in range(16) if i%4>=2)
@pytest.mark.parametrize('kind',list(lifecycle_fixture()))
def test_missing_generation_evidence(kind):
 x=lifecycle_fixture();assert m.lifecycle(x)['status'].endswith('VERIFIED');x.pop(kind);assert m.lifecycle(x)['status'] in ('UNKNOWN','REJECTED')
@pytest.mark.parametrize('kind,key,value',[('generation_retired','renderFenceSuccess',False),('generation_identity','primaryBeginFlags',1),('generation_identity','sameSecondary',False),('generation_identity','secondaryGeneration',0),('stale_attempt','apiResult',0),('stale_attempt','submitted',True),('stale_fence','status',0),('primary_rebuilt','recordedGeneration',0),('generation_execution','primaryRerecorded',False),('generation_execution','fenceCompleted',False),('generation_dependency','oldLayout',0),('generation_dependency','srcAccess',0),('generation_recorded','generation',True)])
def test_lifecycle_mutations(kind,key,value):
 x=lifecycle_fixture();assert m.lifecycle(x)['status'].endswith('VERIFIED');x[kind][key]=value;assert m.lifecycle(x)['status'] in ('UNKNOWN','REJECTED')
def test_old_pixels_not_new_generation():
 x=lifecycle_fixture();x['generation_execution']['pixels']=m.reference();assert m.lifecycle(x)['status']=='REJECTED'

@pytest.mark.parametrize("bad",[None,[],True,0])
def test_lifecycle_badshape(bad):
 assert m.lifecycle(bad)=={"status":"UNKNOWN"}
