"""Fixed official core 1.4 generated target; not Asciidoctor expansion."""
import hashlib,json,re,posixpath
from pathlib import Path
from . import prose_denominator19 as p
MARKERS={x+'/timeMarker' for x in ('api','validity','hostsynctable','meta','interfaces','spirvcap','formats','sync','dynamicstate')}
REQUIRED=MARKERS|{'apimap.py','apimap.rb','specattribs.adoc','featurerequirements.adoc','api/structs/VkMemoryDedicatedRequirements.adoc','validity/structs/VkMemoryDedicatedRequirements.adoc'}
ATTRIBUTES=['VK_'+prefix+'VERSION_1_'+str(v) for prefix in ('BASE_','COMPUTE_','GRAPHICS_','') for v in range(5)]
def inventory(root):
 out={}
 for f in sorted(root.rglob('*')):
  p.need(not f.is_symlink(),'generated symlink forbidden')
  if f.is_file():out[f.relative_to(root).as_posix()]=p.sha(f.read_bytes())
  else:p.need(f.is_dir(),'nonregular output')
 return out
def validate(root):
 inv=inventory(root);p.need(REQUIRED<=set(inv),'missing generated target')
 p.need(not any('__pycache__' in x or x.endswith('.pyc') for x in inv),'unexpected compiled Python cache')
 attrs=(root/'specattribs.adoc').read_text();actual=re.findall(r'^:(VK_[A-Za-z0-9_]+):$',attrs,re.M)
 p.need(actual==ATTRIBUTES and ':SPECREVISION: 1.4.368' in attrs,'wrong effective core configuration')
 symbol=(root/'api/structs/VkMemoryDedicatedRequirements.adoc').read_text()
 p.need('[[VkMemoryDedicatedRequirements]]' in symbol and 'VkBool32           prefersDedicatedAllocation;' in symbol and 'VkBool32           requiresDedicatedAllocation;' in symbol,'dedicated symbol generated incorrectly')
 p.need(all((root/x).read_bytes()==b'' for x in MARKERS),'unexpected marker content')
 return inv
def include_observations(files,generated):
 out=[]
 for path,f in sorted(files.items()):
  if not path.endswith('.adoc'):continue
  for number,line in enumerate(f['raw'].decode().splitlines(),1):
   m=re.match(r'\s*include::([^\[]+)\[(.*)\]',line)
   if not m:continue
   expression,options=m.groups();target=expression;domain='source'
   if target.startswith('{generated}/'):target=target[len('{generated}/'):];domain='generated'
   elif target.startswith('{chapters}/'):target='chapters/'+target[len('{chapters}/'):]
   elif target.startswith('{appendices}/'):target='appendices/'+target[len('{appendices}/'):]
   elif '{' not in target:target=posixpath.normpath(posixpath.join(posixpath.dirname(path),target))
   known='{' not in target and not target.startswith('/') and '://' not in target and not target.startswith('../')
   exists=known and target in (generated if domain=='generated' else files)
   out.append({'source':path,'line':number,'expression':expression,'options_raw':options,'domain':domain,'candidate':target if known else None,'status':'FILE_EXISTS_NOT_EXPANDED' if exists else 'MISSING_OR_UNRESOLVED_NOT_PROVEN_ACTIVE','conditions':'NOT_EVALUATED','tag_ranges':'NOT_EXPANDED'})
 return out
def compare(a,b):
 p.need(a==b,'independent generated inventories differ');return 'EXACT_GENERATED_BYTES_EQUAL_INCLUDING_EMPTY_MARKERS'
