"""Pinned raw layout prose and one explicitly resolved common-validity include."""
import hashlib,re
COMMIT='fa30d4e312e843193601be7cb926c7e25d9ec885'
CHAPTER='chapters/descriptorsets.adoc'
CHAPTER_SHA='3de692bf6e4f8579de50175be94c564a4580e1b8f0a59ed1e1267e1c3ca88950'
COMMON='chapters/commonvalidity/push_constants_common.adoc'
COMMON_SHA='103dd30346b9483a4c7326b6d49a1444257531577d93ee64ad8a6c14fb377dda'
ANCHORS=('descriptors-pipelinelayout','descriptors-compatibility','descriptors-push-constants')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def map_sources(chapter,common):
 if sha(chapter)!=CHAPTER_SHA or sha(common)!=COMMON_SHA:raise ValueError('wrong frozen layout normative bytes')
 lines=chapter.decode().splitlines(keepends=True);locations={}
 for i,line in enumerate(lines):
  m=re.fullmatch(r'\[\[([^\]]+)\]\]\s*',line)
  if m:locations.setdefault(m[1],[]).append(i)
 starts=sorted(i for v in locations.values() for i in v);slices=[]
 for anchor in ANCHORS:
  found=locations.get(anchor,[])
  if len(found)!=1:raise ValueError('missing/duplicate layout anchor')
  a=found[0];b=next((i for i in starts if i>a),len(lines));raw=''.join(lines[a:b]).encode()
  slices.append(dict(anchor=anchor,line_start=a+1,line_end=b,sha256=sha(raw),bytes=len(raw),conditional_directives=[l.strip() for l in lines[a:b] if re.match(r'\s*(ifdef|ifndef|ifeval|endif)::',l)]))
 include='include::{chapters}/commonvalidity/push_constants_common.adoc[]'
 sites=[i for i,l in enumerate(lines,1) if l.strip()==include]
 if not sites:raise ValueError('missing common-validity include site')
 return dict(status='PINNED_LAYOUT_PROSE_MAP',commit=COMMIT,api_version='1.4.368',license='CC-BY-4.0',copyright='Khronos Group',chapter=dict(path=CHAPTER,sha256=CHAPTER_SHA,slices=slices),resolved_common_include=dict(path=COMMON,sha256=COMMON_SHA,bytes=len(common),include_lines=sites,refpage_substitution='vkCmdPushConstants reviewed explicitly; other commands not inferred'),limitations=['Raw physical anchor slices, not complete transitive prose closure.','Only this one common-validity include is bound; other includes/macros/conditional variants are not resolved.','Distinct from pinned1.4.309 VUID data; no version equivalence, device validation or complete L1/L2 acceptance.'])
