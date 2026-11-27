"""Bounded color MSAA resolve + sampled postprocess. No depth/edge-quality claim."""
VUID='VUID-VkRenderingAttachmentInfo-imageView-06861'
def admit(m,f,c):
 if not all(isinstance(x,dict) for x in (m,f,c)):return {'status':'UNKNOWN','vuids':[]}
 fixed={'sourceFormat':37,'resolveFormat':37,'resolveMode':2,'sourceLayout':1,'resolveLayout':1,'storeOp':0,'resolveSamples':1,'sourcePipelineSamples':4,'sourceSampleShading':0,'postPipelineSamples':1,'distinctImages':True,'sampledResolveView':True}
 if any(type(m.get(k)) is not type(v) or m[k]!=v for k,v in fixed.items()):return {'status':'UNKNOWN','vuids':[]}
 for obj,keys in ((m,('sourceSamples',)),(f,('format','usage','samples','supportedSamples','maxWidth','maxHeight','maxLayers')),(c,('colorSampleCounts',))):
  if any(type(obj.get(k)) is not int or not 0<=obj[k]<=2**32-1 for k in keys):return {'status':'UNKNOWN','vuids':[]}
 if f['format']!=37 or f['usage']!=16 or m['sourceSamples']!=f['samples'] or m['sourceSamples'] not in (1,4):return {'status':'UNKNOWN','vuids':[]}
 if not f['supportedSamples']&4 or not c['colorSampleCounts']&4 or min(f['maxWidth'],f['maxHeight'])<4 or f['maxLayers']<1:return {'status':'UNSUPPORTED','vuids':[]}
 return {'status':'REJECTED','vuids':[VUID]} if m['sourceSamples']==1 else {'status':'WITHIN_SCOPE','vuids':[]}
