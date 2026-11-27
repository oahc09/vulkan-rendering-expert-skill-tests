"""Single CPU device admission; queries describe support, never enable features."""
import math
IDENTITY=('deviceType','deviceID','vendorID','driverVersion','apiVersion')
def select(caps,profile='indirect-checker-v1'):
 if profile!='indirect-checker-v1':return {'status':'REJECTED_PROFILE'}
 if not isinstance(caps,dict) or not isinstance(caps.get('devices'),list):return {'status':'UNKNOWN'}
 if len(caps['devices'])!=1:return {'status':'REJECTED_DEVICE_SCOPE','reason':'exactly one device required; no silent pd0 selection'}
 d=caps['devices'][0]
 if not isinstance(d,dict):return {'status':'UNKNOWN'}
 need=IDENTITY+('dynamicRenderingSupported','formatResult','formatWidth','formatHeight','formatSamples','maxDrawIndirectCount','maxColorAttachments','maxFramebufferWidth','maxFramebufferHeight','maxViewportWidth','maxViewportHeight','maxComputeInvocations','maxLocalX','maxGroupsX','coherentHostTypeExists')
 if any(type(d.get(k)) is not int for k in need) or type(caps.get('loaderApi')) is not int:return {'status':'UNKNOWN'}
 if any(d[k]<0 for k in need if k!='formatResult') or caps['loaderApi']<0:return {'status':'UNKNOWN'}
 if (d['apiVersion']>>29) or (caps['loaderApi']>>29):return {'status':'UNKNOWN','reason':'non-Vulkan variant'}
 if any(d[k]>0xffffffff for k in need if k!='formatResult') or caps['loaderApi']>0xffffffff:return {'status':'UNKNOWN'}
 for k in ('viewportBoundsMin','viewportBoundsMax'):
  if type(d.get(k)) not in (int,float) or not math.isfinite(d[k]):return {'status':'UNKNOWN'}
 if d['deviceType']!=4:return {'status':'REJECTED_DEVICE_SCOPE'}
 checks={'loader-core13':caps['loaderApi']>=4206592,'physical-core13':d['apiVersion']>=4206592,'dynamicRendering-supported':d['dynamicRenderingSupported']==1,'format-query':d['formatResult']==0,'format-extent':min(d['formatWidth'],d['formatHeight'])>=4,'sample1':bool(d['formatSamples']&1),'indirect-limit':d['maxDrawIndirectCount']>=1,'color-limit':d['maxColorAttachments']>=1,'framebuffer-extent':min(d['maxFramebufferWidth'],d['maxFramebufferHeight'])>=4,'viewport-extent':min(d['maxViewportWidth'],d['maxViewportHeight'])>=4,'compute-limit':min(d['maxComputeInvocations'],d['maxLocalX'],d['maxGroupsX'])>=1,'viewport-bounds':d['viewportBoundsMin']<=0 and d['viewportBoundsMax']>=4,'host-coherent-type':d['coherentHostTypeExists']==1}
 if not isinstance(d.get('queues'),list):return {'status':'UNKNOWN'}
 for q in d['queues']:
  if not isinstance(q,dict):return {'status':'UNKNOWN'}
  if any(type(q.get(k)) is not int or q[k]<0 or q[k]>0xffffffff for k in ('family','flags','count')):return {'status':'UNKNOWN'}
 if [q['family'] for q in d['queues']]!=list(range(len(d['queues']))):return {'status':'UNKNOWN','reason':'queue enumeration indices must be unique and ordered'}
 qs=[q for q in d['queues'] if q['count'] and q['flags']&3==3];checks['joint-queue']=bool(qs)
 return {'status':'ADMITTED_SUPPORT_ONLY' if all(checks.values()) else 'UNAVAILABLE_REQUIREMENTS','checks':checks,'identity':{k:d[k] for k in IDENTITY},'queue':qs[0] if qs else None,'enabled_features_proven':False,'remaining':['actual scene enable manifest','image/buffer memoryTypeBits compatible allocations','actual shaders/limits/layout/dependency/pixels']}
def match(admission,identity):
 if admission.get('status')!='ADMITTED_SUPPORT_ONLY':raise ValueError('not admitted')
 if any(type(identity.get(k)) is not int or identity[k]!=admission['identity'][k] for k in IDENTITY):raise ValueError('different physical identity')
 q=admission['queue']
 if type(identity.get('queueFamily')) is not int or type(identity.get('queueFlags')) is not int:raise ValueError('queue identity integers required')
 if identity.get('queueFamily')!=q['family'] or identity.get('queueFlags')!=q['flags']:raise ValueError('different queue')
