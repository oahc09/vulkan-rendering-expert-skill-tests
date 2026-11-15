"""Bounded static depth occlusion, MSAA color resolve and sampled postprocess."""
import math
VUID='VUID-vkCmdDraw-dynamicRenderingUnusedAttachments-08914'
def admit(m,f,c):
 if not all(isinstance(x,dict) for x in (m,f,c)):return {'status':'UNKNOWN','vuids':[]}
 fixed={'viewFormat':126,'samples':4,'writeEnable':1,'compareOp':1,'boundsEnable':0,'stencilEnable':0,'layout':3,'loadOp':1,'storeOp':0,'resolveMode':0,'aspect':2,'pushStage':16,'pushSize':4,'unusedAttachmentsEnabled':False}
 if any(type(m.get(k)) is not type(v) or m[k]!=v for k,v in fixed.items()):return {'status':'UNKNOWN','vuids':[]}
 if type(m.get('clearDepth')) not in (int,float) or not math.isfinite(m['clearDepth']) or m['clearDepth']!=1:return {'status':'UNKNOWN','vuids':[]}
 for o,ks in ((m,('pipelineFormat','testEnable','maxPushSize')),(f,('format','usage','samples','supportedSamples','maxWidth','maxHeight','maxLayers')),(c,('depthSampleCounts',))):
  if any(type(o.get(k)) is not int or not 0<=o[k]<=2**32-1 for k in ks):return {'status':'UNKNOWN','vuids':[]}
 if m['pipelineFormat'] not in (124,126) or m['testEnable'] not in (0,1) or f['format']!=126 or f['usage']!=32 or f['samples']!=4:return {'status':'UNKNOWN','vuids':[]}
 if m['maxPushSize']<4 or not f['supportedSamples']&4 or not c['depthSampleCounts']&4 or min(f['maxWidth'],f['maxHeight'])<4 or f['maxLayers']<1:return {'status':'UNSUPPORTED','vuids':[]}
 if m['pipelineFormat']!=m['viewFormat']:return {'status':'REJECTED','vuids':[VUID]}
 return {'status':'DEPTH_DISABLED_CONTROL' if not m['testEnable'] else 'WITHIN_SCOPE','vuids':[]}
def reference(depth_enabled=True):
 # Independently simulate per-pixel clear=1, near partial draw then far full draw.
 out=[]
 for y in range(4):
  for x in range(4):
   z=1.;color=[1,0,1,1]
   for incoming,rgb,covered in ((.25,[1,0,0,1],x<1+y%3),(.75,[0,1,1,1],True)):
    if covered and (not depth_enabled or incoming<z):
     color=rgb
     if depth_enabled:z=incoming
   out.append([255*color[k] for k in (2,0,1,3)])
 return out
