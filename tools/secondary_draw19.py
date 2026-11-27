"""One executable dynamic-rendering secondary, no pending reuse or concurrency proof."""
VUID='VUID-vkCmdExecuteCommands-imageView-06028'
def admit(inheritance,execute,attachment,pipeline):
 if not isinstance(attachment,dict) or not isinstance(pipeline,dict) or type(attachment.get('format')) is not int or type(pipeline.get('format')) is not int:return {'status':'UNKNOWN','vuids':[]}
 fields=('level','beginFlags','renderingFlags','viewMask','colorCount','colorFormat','samples','depthFormat','stencilFormat','queueFamily')
 if not isinstance(inheritance,dict) or any(type(inheritance.get(k)) is not int or not 0<=inheritance[k]<2**32 for k in fields):return {'status':'UNKNOWN','vuids':[]}
 if inheritance.get('renderPassNull') is not True or inheritance.get('secondaryExecutable') is not True:return {'status':'UNKNOWN','vuids':[]}
 if not isinstance(execute,dict) or any(type(execute.get(k)) is not int for k in ('primaryRenderingFlags','count','primaryQueueFamily')):return {'status':'UNKNOWN','vuids':[]}
 expected=dict(level=1,beginFlags=2,renderingFlags=0,viewMask=0,colorCount=1,samples=1,depthFormat=0,stencilFormat=0)
 if any(inheritance[k]!=v for k,v in expected.items()) or execute['primaryRenderingFlags']!=1 or execute['count']!=1 or execute['primaryQueueFamily']!=inheritance['queueFamily']:return {'status':'OUT_OF_SCOPE','vuids':[]}
 if type(attachment.get('format')) is not int or attachment['format']!=37 or pipeline.get('format')!=inheritance['colorFormat']:return {'status':'OUT_OF_SCOPE','vuids':[]}
 if inheritance['colorFormat']==44:return {'status':'REJECTED','vuids':[VUID]}
 if inheritance['colorFormat']!=37:return {'status':'OUT_OF_SCOPE','vuids':[]}
 return {'status':'SECONDARY_WITHIN_SCOPE','vuids':[]}
def reference():return [[255,0,0,255] if x<1+y%3 else [0,0,255,255] for y in range(4) for x in range(4)]

def second_reference():
 return [[255,0,255,255] if x>=2 else reference()[y*4+x] for y in range(4) for x in range(4)]

def lifecycle(rows):
 if not isinstance(rows,dict):return {'status':'UNKNOWN'}
 expected={'generation_dependency':dict(kind='generation_dependency',oldLayout=6,newLayout=2,srcAccess=2048,dstAccess=384,srcStage=4096,dstStage=1024,aspect=1,levels=1,layers=1),'generation_retired':dict(kind='generation_retired',generation=0,renderFenceSuccess=True),'generation_recorded':dict(kind='generation_recorded',generation=1,secondaryResetAfterFence=True,scissor=[0,0,2,4],pipelineOrdinal=1),'generation_identity':dict(kind='generation_identity',primaryBeginFlags=0,primaryRecordedGeneration=0,secondaryGeneration=1,samePrimary=True,sameSecondary=True,sameImage=True,sameReadback=True,sameFence=True),'stale_fence':dict(kind='stale_fence',status=1),'stale_attempt':dict(kind='stale_attempt',apiResult=-1000011001,newErrors=1,submitted=False),'primary_rebuilt':dict(kind='primary_rebuilt',recordedGeneration=1,secondaryGeneration=1,oldLayout=6)}
 def exact(a,b):return type(a) is type(b) and (all(k in a and exact(a[k],v) for k,v in b.items()) and len(a)==len(b) if isinstance(b,dict) else all(exact(x,y) for x,y in zip(a,b)) and len(a)==len(b) if isinstance(b,list) else a==b)
 if any(k not in rows or not exact(rows[k],v) for k,v in expected.items()):return {'status':'UNKNOWN'}
 result=rows.get('generation_execution',{});target=dict(kind='generation_execution',generation=1,primaryRerecorded=True,submitted=True,fenceCompleted=True,pixels=second_reference())
 if not exact(result,target):return {'status':'REJECTED'}
 return {'status':'RETIRED_SECONDARY_RERECORD_PRIMARY_REBUILD_VERIFIED','scope':'Serial two-generation authored CPU fixture, not pending reset or concurrent execution.'}
