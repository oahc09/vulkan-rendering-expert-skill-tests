"""Frozen raw binding, dedicated requirement, granularity and free source sections."""
import hashlib,re
COMMIT='fa30d4e312e843193601be7cb926c7e25d9ec885'
HASHES={'resources':'de7c50943e022c508b369a605ce05b20cc7376274d1e4ecb1d67234698732a7a','memory':'a7f291992b45e3c783afd7f379361a1b20471c0d0675267b841e24395c3c593d'}
MARKERS={'resources':["[open,refpage='VkMemoryRequirements',","[open,refpage='VkMemoryDedicatedRequirements',",'[[resources-bufferimagegranularity]]'], 'memory':["[open,refpage='VkMemoryDedicatedAllocateInfo',","[open,refpage='vkFreeMemory',"]}
def extract(inputs):
 if type(inputs) is not dict or set(inputs)!=set(HASHES):raise ValueError('exact source inputs required')
 out=[]
 for name,h in HASHES.items():
  raw=inputs[name]
  if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=h:raise ValueError('wrong frozen '+name)
  lines=raw.decode().splitlines(keepends=True)
  for marker in MARKERS[name]:
   found=[i for i,l in enumerate(lines) if l.startswith(marker)]
   if len(found)!=1:raise ValueError('missing/duplicate marker')
   start=found[0]
   end=next((i for i in range(start+1,len(lines)) if lines[i].startswith('[[resources-') or lines[i].startswith('[open,refpage=')),len(lines))
   data=''.join(lines[start:end]).encode()
   out.append(dict(source=name,marker=marker,line_start=start+1,line_end=end,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),conditional_directives=[l.strip() for l in lines[start:end] if re.match(r'\s*(ifdef|ifndef|ifeval|endif)::',l)]))
 return dict(status='EXACT_RAW_PROSE_SLICE_MAP',source_commit=COMMIT,sources={n:dict(path='chapters/'+n+'.adoc',sha256=h,api_version='1.4.368',license='CC-BY-4.0') for n,h in HASHES.items()},slices=out,limits=['Raw bounded sections, not evaluated includes/outer conditional applicability.','Separate from fixed309 VUID coordinates; not full normative closure.'])
