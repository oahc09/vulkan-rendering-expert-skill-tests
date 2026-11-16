"""Exact raw normative source slices, not preprocessed spec or semantic proof."""
import hashlib,re
COMMIT='fa30d4e312e843193601be7cb926c7e25d9ec885'
PATH='chapters/synchronization.adoc'
SHA256='7748c88e48007820179681ef4f82c1d2244afc5482b5bc0c13d370ef64821909'
ANCHORS=('synchronization-dependencies-execution','synchronization-dependencies-chains','synchronization-dependencies-available-and-visible','synchronization-dependencies-memory','synchronization-dependencies-access-scopes','synchronization-submission-order','synchronization-submission-host-writes','buffer-memory-barrier-ownership-transfer')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def extract(raw):
 if sha(raw)!=SHA256:raise ValueError('wrong frozen synchronization prose bytes')
 lines=raw.decode('utf-8').splitlines(keepends=True)
 occurrences={}
 for i,line in enumerate(lines):
  m=re.fullmatch(r'\[\[([^\]]+)\]\]\s*',line)
  if m:occurrences.setdefault(m[1],[]).append(i)
 out=[]
 all_starts=sorted(i for values in occurrences.values() for i in values)
 for anchor in ANCHORS:
  found=occurrences.get(anchor,[])
  if len(found)!=1:raise ValueError('missing/duplicate source anchor')
  start=found[0];end=next((x for x in all_starts if x>start),len(lines))
  content=''.join(lines[start:end]).encode()
  out.append(dict(anchor=anchor,line_start=start+1,line_end=end,raw_slice_sha256=sha(content),bytes=len(content),conditional_directives=[line.strip() for line in lines[start:end] if re.match(r'\s*(ifdef|ifndef|ifeval|endif)::',line)],semantic_status='REQUIRES_APPLICABILITY_REVIEW'))
 return dict(schema=1,status='EXACT_RAW_PROSE_SLICE_MAP',source=dict(commit=COMMIT,path=PATH,sha256=SHA256,source_url=f'https://github.com/KhronosGroup/Vulkan-Docs/blob/{COMMIT}/{PATH}',api_version='1.4.368',license='CC-BY-4.0',copyright='Khronos Group'),slices=out,limits=['Physical raw section slices terminate at the next explicit source anchor; not transitive normative dependency closure.','AsciiDoc includes/macros/conditionals are not expanded or evaluated.','No equivalence to separately frozen1.4.309 VUID corpus or actual CPU runtime is implied.','Source identity and slice hashes are traceability, not L1/L2 acceptance.'])
