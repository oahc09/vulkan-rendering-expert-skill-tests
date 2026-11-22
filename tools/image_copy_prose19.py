"""Exact selected copy/format prose and common validity source identity."""
import hashlib,re
COMMIT='fa30d4e312e843193601be7cb926c7e25d9ec885'
SOURCES={
 'formats':('chapters/formats.adoc','9360d12ae4c69c9eb7cf374dc3c99c061b6386f1551b9b4648d14728101cb7f1',('formats-size-compatibility',)),
 'copies':('chapters/copies.adoc','b821b4b219c3e7e691332b651c40cd169b74017d7212aad9d1ddbeef8acbec05',('copies-images','copies-images-addressing')),
 'common':('chapters/commonvalidity/copy_image_common.adoc','7251d3047441e1be6bf16f4669393ae31b957dea61b3a737ef6a35998b1ef6e0',())}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def map_sources(inputs):
 if type(inputs) is not dict or set(inputs)!=set(SOURCES):raise ValueError('exact source set required')
 out={}
 for name,(path,digest,anchors) in SOURCES.items():
  raw=inputs[name]
  if sha(raw)!=digest:raise ValueError('wrong frozen image copy source: '+name)
  lines=raw.decode().splitlines(keepends=True);positions={}
  for i,line in enumerate(lines):
   m=re.fullmatch(r'\[\[([^\]]+)\]\]\s*',line)
   if m:positions.setdefault(m[1],[]).append(i)
  starts=sorted(i for xs in positions.values() for i in xs);slices=[]
  for anchor in anchors:
   found=positions.get(anchor,[])
   if len(found)!=1:raise ValueError('missing/duplicate copy anchor')
   a=found[0];b=next((i for i in starts if i>a),len(lines));blob=''.join(lines[a:b]).encode()
   slices.append(dict(anchor=anchor,line_start=a+1,line_end=b,sha256=sha(blob),bytes=len(blob),conditional_directives=[l.strip() for l in lines[a:b] if re.match(r'\s*(ifdef|ifndef|ifeval|endif)::',l)]))
  out[name]=dict(path=path,sha256=digest,bytes=len(raw),slices=slices)
 marker='include::{chapters}/commonvalidity/copy_image_common.adoc[]'
 sites=[i for i,line in enumerate(inputs['copies'].decode().splitlines(),1) if line.strip()==marker]
 if not sites:raise ValueError('missing fixed common include')
 return dict(status='PINNED_IMAGE_COPY_PROSE_MAP',commit=COMMIT,api_version='1.4.368',license='CC-BY-4.0',copyright='Khronos Group',sources=out,common_include_lines=sites,limitations=['Raw physical slices, not preprocessed complete specification.','Only listed common validity include is resolved; remaining includes and feature conditions require review.','Size-representation block-count equality is not a unique command coordinate transformation.','Separate1.4.309 VUID cohort is not treated as the same version or GPU acceptance.'])
