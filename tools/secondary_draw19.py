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
