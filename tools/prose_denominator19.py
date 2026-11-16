"""Frozen tracked-source graph, deliberately not expanded normative closure."""
import hashlib,json,posixpath,re,subprocess
from pathlib import Path
COMMIT='fa30d4e312e843193601be7cb926c7e25d9ec885'
ENV={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','GIT_NO_REPLACE_OBJECTS':'1','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def need(v,m):
 if not v:raise ValueError(m)
def git(repo,*args):return subprocess.check_output(['/usr/bin/git','-c','core.fsmonitor=false','-C',str(repo),*args],env=ENV,timeout=60)
def validate_blob(raw,oid,size):
 need(len(raw)==size and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()==oid,'corrupt Git blob bytes')
 return raw
def load(repo):
 need(git(repo,'rev-parse',COMMIT+'^{tree}').decode().strip()=='1ef6d54d3efbcf53308f45ccf31d04f61049ea65','wrong fixed tree')
 records=[];total=0
 for row in git(repo,'ls-tree','-rz',COMMIT).split(b'\0'):
  if not row:continue
  meta,path=row.split(b'\t',1);mode,kind,oid=meta.decode().split();records.append((path.decode(),mode,kind,oid))
 # Batch object reads avoid 1340 shell/process launches; no input-selected commands.
 need(len(records)==1340 and all(x[2]=='blob' and x[1] in ('100644','100755') for x in records),'exact ordinary fixed tree required')
 ids=[x[3] for x in records if x[2]=='blob']
 sizes=subprocess.run(['/usr/bin/git','-C',str(repo),'cat-file','--batch-check'],input=('\n'.join(ids)+'\n').encode(),stdout=subprocess.PIPE,check=True,env=ENV,timeout=60).stdout.splitlines()
 need(len(sizes)==len(ids),'size count')
 for oid,line in zip(ids,sizes):
  fields=line.decode().split();need(len(fields)==3 and fields[0]==oid and fields[1]=='blob' and int(fields[2])<=16000000,'blob size preflight');total+=int(fields[2])
 need(total<=64000000,'total source bound');total=0
 result=subprocess.run(['/usr/bin/git','-C',str(repo),'cat-file','--batch'],input=('\n'.join(ids)+'\n').encode(),stdout=subprocess.PIPE,check=True,env=ENV,timeout=60).stdout
 data={};offset=0
 for oid in ids:
  end=result.index(b'\n',offset);header=result[offset:end].decode().split();need(header[0]==oid and header[1]=='blob','object identity');size=int(header[2]);total+=size;need(size<=16000000 and total<=64000000,'blob byte bounds');offset=end+1;data[oid]=validate_blob(result[offset:offset+size],oid,size);need(result[offset+size:offset+size+1]==b'\n','batch delimiter');offset+=size+1
 need(offset==len(result),'batch framing')
 return {p:{'mode':m,'kind':k,'blob':o,'raw':data.get(o,b'')} for p,m,k,o in records}
def category(p):
 if p.endswith('.adoc'):return 'NORMATIVE_OR_DOCUMENTATION_ADOC'
 if p.startswith(('scripts/','config/','build_tests/')) or p.endswith(('.py','.sh','.mk')) or Path(p).name.startswith(('Makefile','make')):return 'GENERATION_OR_BUILD_INPUT'
 if p.startswith('xml/'):return 'REGISTRY_OR_SCHEMA'
 if p.startswith(('images/','katex/','antora/')):return 'PRESENTATION_ASSET_OR_CONFIG'
 if 'LICENSE' in p or Path(p).name in ('COPYING.adoc','REUSE.toml'):return 'LICENSE_OR_ATTRIBUTION'
 return 'OTHER_UNCLASSIFIED_RETAINED'
DIRECTIVE=re.compile(r'^\s*(include|ifdef|ifndef|ifeval|endif)::(.*)$')
def build(files):
 inventory={};graph=[];generation=[];spans=[]
 for p,f in sorted(files.items()):
  raw=f['raw'];inventory[p]={'mode':f['mode'],'kind':f['kind'],'git_object':f['blob'],'sha256':sha(raw),'bytes':len(raw),'category':category(p),'review_status':'UNREVIEWED'}
  if f['mode'] not in ('100644','100755') or f['kind']!='blob':continue
  try:text=raw.decode('utf8')
  except UnicodeDecodeError:continue
  lines=text.splitlines(keepends=True);stack=[];anchor=None;anchor_start=0;anchor_context=[];contexts={}
  for i,line in enumerate(lines,1):
   contexts[i]=list(stack)
   m=DIRECTIVE.match(line);a=re.fullmatch(r'\[\[([^\]]+)\]\]\s*',line)
   if a:
    if anchor and p=='chapters/resources.adoc' and ('dedicated' in anchor.lower()):spans.append({'source':p,'anchor':anchor,'line_start':anchor_start,'line_end':i-1,'sha256':sha(''.join(lines[anchor_start-1:i-1]).encode()),'outer_conditions':anchor_context,'mapping':'MANUAL_CANDIDATE_memory_binding_contract19.bind_NOT_REVIEW_ACCEPTANCE'})
    anchor=a[1];anchor_start=i;anchor_context=list(stack)
   if p.endswith('.adoc') and (m or re.match(r'^:[^:]+:',line) or re.search(r'\{[^{}\n]+\}',line)):
    row={'source':p,'line':i,'raw':line.rstrip('\r\n'),'line_sha256':sha(line.encode()),'outer_conditions':list(stack),'kind':m[1] if m else 'ATTRIBUTE_OR_MACRO_TEXT'}
    if m and m[1]=='include':
     target=m[2].split('[',1)[0];row['target_expression']=target;row['options_raw']=m[2][len(target):]
     resolved=posixpath.normpath(posixpath.join(posixpath.dirname(p),target))
     if '{' not in target and '://' not in target and not target.startswith('/') and resolved in files:row.update(resolution='TRACKED_LITERAL_TARGET_ONLY',target=resolved)
     else:row.update(resolution='UNRESOLVED_GENERATED_MACRO_OR_MISSING')
    graph.append(row)
   if m:
    if m[1] in ('ifdef','ifndef','ifeval'):
     # Nonempty trailing brackets on ifdef/ifndef are inline bodies, not scopes.
     inline=m[1] in ('ifdef','ifndef') and not m[2].rstrip().endswith('[]')
     if not inline:stack.append({'line':i,'directive':line.rstrip('\r\n')})
    elif m[1]=='endif':
     if stack:stack.pop()
     else:graph.append({'source':p,'line':i,'kind':'UNMATCHED_ENDIF','raw':line.rstrip('\r\n')})
   if inventory[p]['category']=='GENERATION_OR_BUILD_INPUT' and (re.search(r'(generate|genvk|genRef|python|include|generated|\.py\b)',line,re.I) or re.match(r'^[^#\s][^=]*:',line)):
    generation.append({'source':p,'line':i,'raw':line.rstrip('\r\n'),'sha256':sha(line.encode()),'status':'LEXICAL_BUILD_REFERENCE_NOT_EXECUTED_OR_RESOLVED'})
  if p=='chapters/resources.adoc':
   starts=[i for i,l in enumerate(lines,1) if "refpage='VkMemoryDedicatedRequirements'" in l]
   need(len(starts)==1,'dedicated refpage unique');start=starts[0];end=next(i for i in range(start+2,len(lines)+1) if lines[i-1].strip()=='--')
   spans.append({'source':p,'refpage':'VkMemoryDedicatedRequirements','line_start':start,'line_end':end,'sha256':sha(''.join(lines[start-1:end]).encode()),'outer_conditions':contexts[start],'mapping':'MANUAL_BIND_PREFERS_REQUIRES_HOST_ONLY','generated_includes':[x for x in graph if x.get('source')==p and x.get('kind')=='include' and start<=x['line']<=end]})
  if stack:graph.append({'source':p,'kind':'OPEN_LOCAL_CONDITIONAL_CONTEXT','conditions':stack,'meaning':'May depend on include context; not automatically malformed'})
 return {'schema':1,'commit':COMMIT,'status':'P_SOURCE_GRAPH_INDEXED','closure_status':'BLOCKED','tracked_sources':inventory,'adoc_graph':graph,'generation_references':generation,'manual_span_candidates':spans,'closure_blockers':['Vulkan/SC/platform configurations not evaluated','Generated includes and reference outputs not produced or reconciled','Macro expansion and transitive include condition composition not evaluated','Build dependency references are lexical, not a complete executable dependency graph','OTHER_UNCLASSIFIED entries require purpose review','All semantic review remains UNREVIEWED'],'limits':['Raw Git bytes anchor every tracked entry; symlinks/submodules are inventoried, not followed.','Condition stacks are source-local lexical context, not evaluated applicability.','No equivalence with separate validusage 1.4.309 or runtime feature enablement.']}
def verify(report,files):need(canon(report)==canon(build(files)),'source graph differs from reconstruction');return True

def semantic_bridge(repo):
 # Fixed existing helper, not commands or paths selected by report contents.
 import types
 need(Path(repo).resolve()==Path(__file__).resolve().parents[1],'fixed helper repository required')
 path=Path(repo)/'tools/memory_binding_contract19.py';raw=path.read_bytes();testpath=Path(repo)/'tests/test_memory_binding_contract19.py';testbytes=testpath.read_bytes()
 need(sha(raw)=='8502442043761a11a09c6929d9742ba5f3eba8741a809e9e4618d6a08d71868a' and sha(testbytes)=='89c9a88c23289a499e956206e38fe39ff4a529da6a9569df325f341c1e5719c3','wrong pinned bridge source')
 m=types.ModuleType('memory_binding_contract19_bridge');exec(compile(raw,str(path),'exec'),m.__dict__)
 base=dict(kind='buffer',resource_id='A',ordinary_scope_proven=True,allocation_creation_valid=True,same_device=True,requirements_size=256,requirements_alignment=64,memory_type_bits=2,memory_type_index=1,allocation_size=1024,offset=64,already_bound=False,requires_dedicated=False,prefers_dedicated=False,dedicated=None)
 results={}
 for name,change in [('preference_only',{'prefers_dedicated':True}),('required_missing',{'requires_dedicated':True}),('required_matching',{'offset':0,'requires_dedicated':True,'dedicated':{'kind':'buffer','resource_id':'A'}})]:results[name]=m.bind({**base,**change})
 need(results['preference_only']['status']=='BIND_CONDITIONS_WITHIN_SCOPE' and results['required_matching']['status']=='BIND_CONDITIONS_WITHIN_SCOPE' and results['required_missing']['status']=='REJECTED','existing bind controls')
 need(results['required_missing']['vuids']==['VUID-vkBindBufferMemory-buffer-01444'] and results['preference_only']['vuids']==[] and results['required_matching']['vuids']==[],'exact dedicated obligation controls')
 need(path.read_bytes()==raw and testpath.read_bytes()==testbytes,'helper/test changed')
 return {'authority':'EXPLICIT_MANUAL_MAPPING_HOST_CONTROLS_NOT_DEVICE_OR_L1_ACCEPTANCE','helper_sha256':sha(raw),'tests_sha256':sha(testbytes),'results':results,'scope':'Existing ordinary bind contract; 368 prose meaning with separately scoped 309 VUID coordinates, not version equivalence.'}
