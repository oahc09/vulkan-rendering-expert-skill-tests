"""Explicit 1x vs 4x topology + requested allocation receipt, no performance ranking."""
from msaa_sample19 import admit as resolve_admit

def topology(samples,m,f,c):
 if type(samples) is not int or samples not in (1,4):return False
 if samples==4:return resolve_admit(m,f,c)=={'status':'WITHIN_SCOPE','vuids':[]}
 if not all(isinstance(x,dict) for x in (m,f,c)):return False
 fixed={'sourceSamples':1,'resolveSamples':1,'sourceFormat':37,'resolveFormat':37,'resolveMode':0,'sourceLayout':1,'resolveLayout':0,'storeOp':0,'distinctImages':True,'sampledResolveView':True,'sourcePipelineSamples':1,'sourceSampleShading':0,'postPipelineSamples':1}
 if any(type(m.get(k)) is not type(v) or m[k]!=v for k,v in fixed.items()):return False
 for obj,keys in ((f,('format','usage','samples','supportedSamples','maxWidth','maxHeight','maxLayers')),(c,('colorSampleCounts',))):
  if any(type(obj.get(k)) is not int or not 0<=obj[k]<=2**32-1 for k in keys):return False
 return f['format']==37 and f['usage']==21 and f['samples']==1 and bool(f['supportedSamples']&1) and bool(c['colorSampleCounts']&1) and min(f['maxWidth'],f['maxHeight'])>=4 and f['maxLayers']>=1

def allocations(samples,records):
 if type(samples) is not int or samples not in (1,4) or not isinstance(records,dict):raise ValueError('unknown allocation variant')
 mapping={'output':'image_allocation','sampled_source':'source_allocation','depth':'depth_allocation','readback':'buffer_allocation'}
 if samples==4:mapping['multisample_color']='multi_allocation'
 elif 'multi_allocation' in records or 'multisample_color_request' in records:raise ValueError('unused 1x allocation')
 expected_requests={x+'_request' for x in mapping};expected_allocations=set(mapping.values())
 if {k for k in records if k.endswith('_request')}!=expected_requests or {k for k in records if k.endswith('_allocation')}!=expected_allocations:raise ValueError('unexpected or missing allocation receipt')
 items=[]
 for name,key in mapping.items():
  req=records.get(name+'_request');mem=records.get(key)
  if not isinstance(req,dict) or not isinstance(mem,dict):raise ValueError('missing allocation receipt')
  if req.get('kind')!=name+'_request' or req.get('object')!=name:raise ValueError('allocation identity')
  size=req.get('requestedBytes');index=req.get('memoryTypeIndex')
  if type(size) is not int or not 0<size<2**64 or type(index) is not int or not 0<=index<32:raise ValueError('allocation bounds')
  if size!=mem.get('size') or index!=mem.get('selectedType'):raise ValueError('allocation requirement mismatch')
  items.append({'object':name,'requested_bytes':size,'memory_type_index':index})
 total=sum(x['requested_bytes'] for x in items)
 if total>=2**64:raise ValueError('sum overflow')
 expected=dict(kind='allocation_budget',samples=samples,allocationCount=len(items),requestedBytes=total,residentBytesKnown=False,driverInternalBytesKnown=False,performanceKnown=False)
 actual=records.get('allocation_budget')
 if not isinstance(actual,dict) or actual.keys()!=expected.keys() or any(type(actual[k]) is not type(v) or actual[k]!=v for k,v in expected.items()):raise ValueError('allocation total mismatch')
 return {'samples':samples,'allocation_requests':items,'total_requested_bytes':total,'resident_bytes':None,'driver_internal_bytes':None,'gpu_time':None,'thermal_state':None}
