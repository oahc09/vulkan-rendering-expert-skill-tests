"""Pinned raw timeline source sections; includes/outer conditionals not evaluated."""
import hashlib,re
COMMIT='fa30d4e312e843193601be7cb926c7e25d9ec885'
SHA256='7748c88e48007820179681ef4f82c1d2244afc5482b5bc0c13d370ef64821909'
ANCHORS=('synchronization-signal-operation-order','synchronization-semaphores-hostops')
def extract(raw):
 if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=SHA256:raise ValueError('wrong frozen synchronization prose')
 lines=raw.decode().splitlines(keepends=True);positions={}
 for i,line in enumerate(lines):
  m=re.fullmatch(r'\[\[([^\]]+)\]\]\s*',line)
  if m:positions.setdefault(m[1],[]).append(i)
 starts=sorted(i for vals in positions.values() for i in vals);out=[]
 for a in ANCHORS:
  if len(positions.get(a,[]))!=1:raise ValueError('missing/duplicate anchor')
  start=positions[a][0];end=next((i for i in starts if i>start),len(lines));data=''.join(lines[start:end]).encode()
  out.append(dict(anchor=a,line_start=start+1,line_end=end,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),conditional_directives=[line.strip() for line in lines[start:end] if re.match(r'\s*(ifdef|ifndef|ifeval|endif)::',line)]))
 return dict(status='EXACT_RAW_PROSE_SLICE_MAP',source=dict(commit=COMMIT,path='chapters/synchronization.adoc',sha256=SHA256,api_version='1.4.368',license='CC-BY-4.0',copyright='Khronos Group'),slices=out,limits=['Raw slice boundaries are next explicit anchor, not complete dependency closure.','Includes/outer conditionals are not evaluated; separate from309 normative VUIDs.'])
