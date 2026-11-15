"""Declared consecutive binding routing and ordered buffer-token HOST model.
No Vulkan descriptor structure, handle validity, resource access or command-buffer
lifetime is verified. Limits are deliberate model bounds, not Vulkan limits.
"""
import copy,re
TYPES={'UNIFORM_BUFFER','STORAGE_BUFFER','SAMPLER','COMBINED_IMAGE_SAMPLER'}
def u32(x):return type(x) is int and 0<=x<2**32
def result(status,**kw):return {'status':status,'authority':'CALLER_DECLARED_NOT_VERIFIED','complete_update_validity':'NOT_INFERRED',**kw}
def layout_valid(layout):
 if type(layout) is not list or not layout or len(layout)>128:return False
 for i,b in enumerate(layout):
  if type(b) is not dict or set(b)!={'binding','count','type','stages','flags','immutable_reference_signature'}:return False
  if not u32(b['binding']) or b['binding']!=i or not u32(b['count']) or b['count']>4096:return False
  if type(b['type']) is not str or b['type'] not in TYPES or not u32(b['stages']) or not 0<b['stages']<=63 or not u32(b['flags']):return False
  sig=b['immutable_reference_signature']
  if sig is not None and (type(sig) is not str or re.fullmatch('[0-9a-f]{64}',sig) is None or b['type'] not in {'SAMPLER','COMBINED_IMAGE_SAMPLER'}):return False
 return True

def spill(layout,binding,array_element,count):
 """Explicit dense binding table including zero-count holes; first slot must exist.
 Signature means caller-proven identical immutable sampler references, not their
 creation parameters. Extension flag validity is an independent precondition.
 """
 if not layout_valid(layout) or not all(u32(v) for v in (binding,array_element,count)) or count==0 or count>4096:return result('UNKNOWN')
 if binding>=len(layout) or layout[binding]['count']==0 or array_element>=layout[binding]['count']:return result('UNKNOWN')
 first=layout[binding];coords=[];reasons=[]
 for i in range(binding,len(layout)):
  b=layout[i]
  if b['count']==0:continue
  for key in ('type','stages','flags','immutable_reference_signature'):
   if b[key]!=first[key]:reasons.append('CONSECUTIVE_'+key.upper()+'_MISMATCH')
  if reasons:return result('REJECTED',reasons=sorted(set(reasons)),source_contract='368 descriptors-sets-updates-consecutive',vuids=[])
  start=array_element if i==binding else 0
  take=min(count-len(coords),b['count']-start)
  coords.extend([i,j] for j in range(start,start+take))
  if len(coords)==count:return result('ROUTE_WITHIN_SCOPE',coordinates=coords,descriptor_type=first['type'])
 return result('REJECTED',reasons=['INSUFFICIENT_CONSECUTIVE_CAPACITY'],vuids=[])

def token(t):return type(t) is dict and set(t)=={'reference','defined','resource_live'} and type(t['reference']) is str and re.fullmatch('[A-Za-z0-9_.:-]{1,80}',t['reference']) and type(t['defined']) is bool and type(t['resource_live']) is bool

def apply(sets,writes,copies,preconditions_proven):
 """Apply ordered writes then ordered copies to ordinary UBO/SSBO reference tokens.
 All input safety/descriptor payload validity, synchronization and layout flags
 must be established separately. Rejection returns no partial modeled state.
 """
 if preconditions_proven is not True or type(preconditions_proven) is not bool or type(sets) is not dict or not sets or type(writes) is not list or type(copies) is not list or len(writes)+len(copies)>128:return result('UNKNOWN')
 for name,s in sets.items():
  if type(name) is not str or re.fullmatch('[A-Za-z0-9_.:-]{1,80}',name) is None or type(s) is not dict or set(s)!={'layout','values'} or not layout_valid(s['layout']):return result('UNKNOWN')
  if any(b['type'] not in {'UNIFORM_BUFFER','STORAGE_BUFFER'} or b['flags']!=0 for b in s['layout']):return result('UNKNOWN')
  if type(s['values']) is not list or len(s['values'])!=len(s['layout']):return result('UNKNOWN')
  if any(type(v) is not list or len(v)!=b['count'] or any(not token(t) for t in v) for b,v in zip(s['layout'],s['values'])):return result('UNKNOWN')
 out=copy.deepcopy(sets);events=[]
 def route(name,binding,element,count):
  if type(name) is not str or name not in out:return result('UNKNOWN')
  return spill(out[name]['layout'],binding,element,count)
 for index,w in enumerate(writes):
  if type(w) is not dict or set(w)!={'set','binding','element','type','values'} or type(w['values']) is not list or any(not token(t) for t in w['values']):return result('UNKNOWN')
  # Dead/undefined source copies are allowed, not newly written invalid payloads.
  if any(not t['resource_live'] or not t['defined'] for t in w['values']):return result('UNKNOWN')
  r=route(w['set'],w['binding'],w['element'],len(w['values']))
  if r['status']!='ROUTE_WITHIN_SCOPE':return r
  if w['type']!=r['descriptor_type']:return result('REJECTED',vuids=['VUID-VkWriteDescriptorSet-descriptorType-00319'])
  for (b,e),v in zip(r['coordinates'],w['values']):out[w['set']]['values'][b][e]=copy.deepcopy(v)
  events.append({'operation':'WRITE','index':index,'set':w['set'],'coordinates':r['coordinates']})
 for index,c in enumerate(copies):
  if type(c) is not dict or set(c)!={'src_set','src_binding','src_element','dst_set','dst_binding','dst_element','count'}:return result('UNKNOWN')
  a=route(c['src_set'],c['src_binding'],c['src_element'],c['count']);b=route(c['dst_set'],c['dst_binding'],c['dst_element'],c['count'])
  if a['status']!='ROUTE_WITHIN_SCOPE':return a
  if b['status']!='ROUTE_WITHIN_SCOPE':return b
  if a['descriptor_type']!=b['descriptor_type']:return result('REJECTED',vuids=['VUID-VkCopyDescriptorSet-dstBinding-02632'])
  if c['src_set']==c['dst_set'] and set(map(tuple,a['coordinates']))&set(map(tuple,b['coordinates'])):return result('REJECTED',vuids=['VUID-VkCopyDescriptorSet-srcSet-00349'])
  values=[copy.deepcopy(out[c['src_set']]['values'][i][j]) for i,j in a['coordinates']]
  for (i,j),v in zip(b['coordinates'],values):
   v['defined']=v['defined'] and v['resource_live'];out[c['dst_set']]['values'][i][j]=v
  events.append({'operation':'COPY','index':index,'src_set':c['src_set'],'dst_set':c['dst_set'],'source_coordinates':a['coordinates'],'destination_coordinates':b['coordinates']})
 return result('MODELED_UPDATES',state_after=out,events=events,resource_use_performed=False,
               limits=['Tokens represent references, not fetched resource contents.','Copying undefined or destroyed references leaves destination undefined.','No actual Vulkan update or GPU execution; no immutable sampler write/copy payload semantics modeled.'])
