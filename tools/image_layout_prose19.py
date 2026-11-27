"""Frozen raw image-layout source slices, not expanded AsciiDoc or semantic proof."""
import hashlib,re
COMMIT='fa30d4e312e843193601be7cb926c7e25d9ec885'
PATH='chapters/synchronization.adoc'
SHA256='7748c88e48007820179681ef4f82c1d2244afc5482b5bc0c13d370ef64821909'
ANCHORS=('synchronization-image-layout-transitions','synchronization-image-memory-barriers','synchronization-image-barrier2-ignored-layout','synchronization-image-barrier-ignored-layout')
def extract(raw):
 if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=SHA256:raise ValueError('wrong frozen synchronization prose')
 lines=raw.decode().splitlines(keepends=True);positions={}
 for i,line in enumerate(lines):
  match=re.fullmatch(r'\[\[([^\]]+)\]\]\s*',line)
  if match:positions.setdefault(match[1],[]).append(i)
 starts=sorted(i for values in positions.values() for i in values);slices=[]
 for anchor in ANCHORS:
  if len(positions.get(anchor,[]))!=1:raise ValueError('missing or duplicate anchor')
  start=positions[anchor][0];end=next((i for i in starts if i>start),len(lines));data=''.join(lines[start:end]).encode()
  slices.append({'anchor':anchor,'line_start':start+1,'line_end':end,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'conditional_directives':[line.strip() for line in lines[start:end] if re.match(r'\s*(ifdef|ifndef|ifeval|endif)::',line)]})
 return {'status':'EXACT_RAW_PROSE_SLICE_MAP','source':{'commit':COMMIT,'path':PATH,'sha256':SHA256,'api_version':'1.4.368','license':'CC-BY-4.0','copyright':'Khronos Group'},'slices':slices,'limits':['Raw slices end at next explicit anchor; outer conditionals and includes are not expanded or evaluated.','Not transitive dependency closure or proof of caller facts; separate from validusage1.4.309.']}
