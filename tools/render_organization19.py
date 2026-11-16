"""Bounded CPU rendering organization receipts, not a performance model."""
from tools import dynamic_draw19, dynamic_color19

def require(c,m):
 if not c: raise ValueError(m)
def reference():
 return [[0,0,255,255] if x < (1,2,3,1)[y] else [255,0,0,255] for y in range(4) for x in range(4)]
def scalar_types(v):
 if isinstance(v,dict):
  for k,x in v.items():
   if k in ('submitted','fenceCompleted','unusedAttachmentsEnabled'):require(type(x) is bool,'boolean fact')
   else:scalar_types(x)
 elif isinstance(v,list):
  for x in v:scalar_types(x)
 elif isinstance(v,(int,float)):
  import math
  require(type(v) in (int,float) and abs(v)<2**64 and math.isfinite(v),'numeric fact')
 elif type(v) is bool:raise ValueError('unexpected bool')
def check(rows,path,wrong=False):
 require(path in ('renderpass','dynamic') and type(wrong)is bool,'mode')
 require(type(rows)is list and all(type(x)is dict for x in rows),'rows')
 order=['identity','limits','image_allocation','buffer_allocation',*(['renderpass_attachment'] if path=='renderpass' else []),'pipeline','image_dependency','manifest','image_dependency','host_dependency','execution','organization','final']
 require([x.get('kind') for x in rows]==order,'record order')
 deps=[x for x in rows if x['kind']=='image_dependency']
 for d,fields in zip(deps,[(1,1024,0,2,0,384),(1024,4096,2,6,256,2048)]):
  require(d==dict(kind='image_dependency',**dict(zip(('srcStage','dstStage','oldLayout','newLayout','srcAccess','dstAccess'),fields)),aspect=1,baseMip=0,levels=1,baseLayer=0,layers=1),'image dependency')
 r={x['kind']:x for x in rows};scalar_types(r)
 require(r['host_dependency']==dict(kind='host_dependency',srcStage=4096,dstStage=16384,srcAccess=4096,dstAccess=8192,copyExtent=[4,4,1]),'host dependency')
 if path=='renderpass':require(r['renderpass_attachment']==dict(kind='renderpass_attachment',format=37,samples=1,loadOp=1,storeOp=0,initialLayout=2,finalLayout=2,subpassLayout=2),'renderpass attachment')
 for d in deps+[r['host_dependency']]+([r['renderpass_attachment']] if path=='renderpass' else []):
  require(all(type(v)is int if not isinstance(v,list) else all(type(x)is int for x in v) for k,v in d.items() if k!='kind'),'dependency exact types')
 # Every integer-bearing field is exact, including nested pixel and pipeline arrays.
 float_keys={'timestampPeriod','viewportBoundsMin','viewportBoundsMax','viewport','viewportBoundsMin','viewportBoundsMax'}
 for name in ('identity','limits','image_allocation','buffer_allocation','pipeline','manifest','organization','final'):
  for k,v in r[name].items():
   if k in ('kind','path','unusedAttachmentsEnabled') or k in float_keys:continue
   if isinstance(v,list):require(all(type(x)is int for x in v),'integer vector')
   else:require(type(v)is int and 0<=v<2**64,'integer field')
 i=r['identity'];require(i['deviceType']==4 and i['apiVersion']>>29==0 and i['apiVersion']>=4206592 and i['layerSpec']==4210997 and i['layerImplementation']==1,'CPU cohort')
 m=r['manifest'];require(m['supported'] in (0,1) and m['enabled']==(path=='dynamic') and (path=='renderpass' or m['supported']==1),'support/enable')
 # Traditional attachment facts are checked using the same ordinary attachment
 # constraints; enabled is separately validated above, never evidence of dynamic use.
 projected=dict(m,enabled=1,supported=1)
 require(dynamic_color19.admit(projected)['status']=='CONFIG_WITHIN_SCOPE','attachment')
 require(dynamic_draw19.admit(r['pipeline'],projected,r['limits'])['status']=='DRAW_CONFIG_WITHIN_SCOPE','graphics')
 for k in ('image_allocation','buffer_allocation'):
  a=r[k];require(a['selectedType']<32 and a['memoryTypeBits']&(1<<a['selectedType']) and a['size']>0 and a['alignment']>0,'memory')
 require(r['buffer_allocation']['selectedFlags']&6==6,'coherent readback');require(m['memoryFlags']==r['image_allocation']['selectedFlags'],'image memory identity')
 e=r['execution'];require(set(e)=={'kind','submitted','fenceCompleted','pixels'} and e['submitted']is True and e['fenceCompleted']is True,'retirement')
 require(e['pixels']==reference() and all(type(v)is int for pixel in e['pixels'] for v in pixel),'complete oracle')
 require(r['final']==dict(kind='final',errors=0,rc=6 if wrong else 0),'final')
 expected=dict(kind='organization',path=path,renderPassObjects=int(path=='renderpass'),framebufferObjects=int(path=='renderpass'),pipelineObjects=1,renderPassBeginCalls=int(path=='renderpass'),dynamicBeginCalls=int(path=='dynamic'),drawCalls=1)
 require(r['organization']==expected,'actual object/call facts')
 return dict(identity=i,pixels=e['pixels'],cost=expected,allocations=[r['image_allocation'],r['buffer_allocation']])
def decide(baseline,candidate,max_renderpass_objects=1,performance_required=False):
 out=dict(rule_id='C2.render-organization.bounded19',limitations=['Application object-count policy, not driver memory or speed.','CPU endpoint scene only; no tile/local-read/whole-frame performance.'])
 try:
  require(type(max_renderpass_objects)is int and 0<=max_renderpass_objects<2**32 and type(performance_required)is bool,'policy')
  b=check(baseline,'renderpass');c=check(candidate,'dynamic')
  require(b['identity']==c['identity'] and b['pixels']==c['pixels'] and b['allocations']==c['allocations'],'paired facts')
 except (ValueError,TypeError,KeyError,OverflowError):return dict(out,status='UNKNOWN',selected=None)
 if performance_required:return dict(out,status='NEEDS_MEASUREMENT',selected=None,fallback='renderpass' if max_renderpass_objects else None)
 return dict(out,status='KEEP_BASELINE' if max_renderpass_objects else 'SELECT_ONLY_POLICY_ADMISSIBLE_PATH',selected='renderpass' if max_renderpass_objects else 'dynamic')
