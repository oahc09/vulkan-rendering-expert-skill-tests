"""Exact raw update/copy sections, with version-separated conditional applicability."""
import hashlib,re
COMMIT='fa30d4e312e843193601be7cb926c7e25d9ec885'
SHA256='3de692bf6e4f8579de50175be94c564a4580e1b8f0a59ed1e1267e1c3ca88950'
def extract(raw):
 if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=SHA256:raise ValueError('wrong frozen descriptor prose')
 lines=raw.decode().splitlines(keepends=True)
 markers={'updates':'[[descriptors-sets-updates]]','consecutive':'[[descriptors-sets-updates-consecutive]]','copy':"[open,refpage='VkCopyDescriptorSet',desc='Structure specifying a copy descriptor set operation',type='structs']"}
 slices=[]
 for name,marker in markers.items():
  loc=[i for i,l in enumerate(lines) if l.strip()==marker]
  if len(loc)!=1:raise ValueError('missing/duplicate section')
  start=loc[0]
  if name=='updates':end=next(i for i in range(start+1,len(lines)) if lines[i].strip()=='.Valid Usage')
  elif name=='consecutive':end=next(i for i in range(start+1,len(lines)) if lines[i].strip()=='.Valid Usage')
  else:end=next(i for i in range(start+1,len(lines)) if lines[i].strip()=='.Valid Usage')
  data=''.join(lines[start:end]).encode()
  slices.append(dict(section=name,line_start=start+1,line_end=end,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),conditional_directives=[l.strip() for l in lines[start:end] if re.match(r'\s*(ifdef|ifndef|ifeval|endif)::',l)]))
 return dict(status='EXACT_RAW_PROSE_SLICE_MAP',source=dict(commit=COMMIT,path='chapters/descriptorsets.adoc',sha256=SHA256,api_version='1.4.368',license='CC-BY-4.0'),slices=slices,limits=['Raw prose before Valid Usage only; includes/outer conditions not expanded.','368 stageFlags/bindingFlags standalone clauses are not identified as309 VUIDs.'])
