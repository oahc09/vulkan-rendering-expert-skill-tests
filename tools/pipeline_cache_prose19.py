"""Pinned ordinary pipeline-cache raw source; no expanded SC/extension conditions."""
import hashlib,re
SHA='2375781805093fb79a19fea888f183e99928e7af05af71e95a06b09371f70e62'
def extract(raw):
 if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('fixed pipelines368 mismatch')
 lines=raw.decode().splitlines(keepends=True);pos={}
 for i,l in enumerate(lines):
  m=re.fullmatch(r'\[\[([^\]]+)\]\]\s*',l)
  if m:pos[m[1]]=i
 rows=[]
 for a in ('pipelines-cache','pipelines-cache-create','pipelines-cache-retrieval','pipelines-cache-header'):
  start=pos[a];end=min([i for i in pos.values() if i>start] or [len(lines)])
  rows.append(dict(anchor=a,line_start=start+1,line_end=end,sha256=hashlib.sha256(''.join(lines[start:end]).encode()).hexdigest()))
 return dict(commit='fa30d4e312e843193601be7cb926c7e25d9ec885',path='chapters/pipelines.adoc',sha256=SHA,version='1.4.368',slices=rows,limits='Raw slices retain conditionals, not expanded; ordinary Vulkan only. Header mismatch is application reject policy, not a claimed validation diagnostic.')
