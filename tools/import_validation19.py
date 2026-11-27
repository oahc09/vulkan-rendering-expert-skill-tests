"""Local callback import. Byte integrity and declared tool versions are not runtime proof."""
import json,re,hashlib,math,html
from html.parser import HTMLParser
from . import diagnostic_spec19 as spec
MAX_BYTES=2_000_000
ROUTES={
 'VUID-vkUpdateDescriptorSets-None-03047':('05_descriptor/descriptor_update.md','PENDING_DESCRIPTOR_USE',
  'A destination descriptor may still be referenced by pending work. The message alone does not establish binding flags, the consumer set, or the offending update.',
  ['Record actual destination set/binding/array element, binding flags and update operation.','Collect submissions referencing that set and their completion evidence; include resources retained by older consumers.'],
  'Do not update or free pending resources as a diagnostic experiment. First distinguish ordinary bindings from applicable update-after-bind exceptions.'),
 'VUID-vkQueueSubmit-pCommandBuffers-00070':('03_command_buffer/command_buffer.md','COMMAND_BUFFER_STATE',
  'The submitted command buffer may not be executable at this call. A stale recording is one possibility, not a diagnosed cause.',
  ['Collect Begin/End/reset results and primary/secondary recording identities for the submitted command buffer.','Check descriptor updates, destroyed referenced objects and secondary reset events that could invalidate that recording.'],
  'Do not resubmit a known-invalid command buffer. Missing recording/lifetime events leave the mechanism unproven.'),
 'SYNC-HAZARD-READ-AFTER-WRITE':('08_synchronization/pipeline_barrier.md','READ_AFTER_WRITE_DEPENDENCY',
  'The tool reports a read-after-write hazard. The particular producer, consumer, subresource/range and applicable dependency are not established by the identifier alone.',
  ['Collect the two accesses, queue/submission identities, stages/access masks and exact resource ranges or subresources.','Record SyncVal settings including shader-access heuristic ON/OFF, and relevant barriers/semaphores; ownership applies only where required by the resource-sharing scope.'],
  'Do not insert arbitrary waits/barriers or inject a GPU race. A WaitIdle workaround or a silent validation run does not establish a repair; shader-access heuristic OFF can miss this fixture class.')}
def digest(raw):return hashlib.sha256(raw).hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def bounded(value,depth=0,count=None):
 if count is None:count=[0]
 count[0]+=1;need(depth<=16 and count[0]<=100000,'JSON structure limit')
 if type(value)is dict:
  for k,v in value.items():need(type(k)is str,'JSON key');bounded(v,depth+1,count)
 elif type(value)is list:
  for v in value:bounded(v,depth+1,count)
 elif type(value)is float:need(math.isfinite(value),'nonfinite JSON')
 else:need(value is None or type(value)in (str,int,bool),'JSON scalar')
def parse(raw):
 need(type(raw)is bytes and len(raw)<=MAX_BYTES,'input bytes budget')
 try:d=json.loads(raw,object_pairs_hook=spec.reject_duplicate_keys,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
 except (UnicodeError,RecursionError) as e:raise ValueError('invalid encoding or nesting') from e
 bounded(d);return d
def uint(v,bits=32):return type(v)is int and 0<=v<2**bits
def callbacks(raw):
 data=parse(raw);need(type(data)is list and len(data)<=1000,'callback list limit')
 for row in data:
  need(type(row)is dict and {'pMessage','objectCount','pObjects'}<=set(row)<= {'pMessageIdName','pMessage','objectCount','pObjects','messageIdNumber'},'supported callback fields')
  mid=row.get('pMessageIdName');need(mid is None or type(mid)is str and len(mid)<=256,'identifier size/type')
  need(type(row['pMessage'])is str and len(row['pMessage'])<=65536,'message size/type')
  need(uint(row['objectCount']) and type(row['pObjects'])is list and row['objectCount']==len(row['pObjects'])<=64,'object count')
  if 'messageIdNumber'in row:need(type(row['messageIdNumber'])is int and -2**31<=row['messageIdNumber']<2**31,'message number')
  for obj in row['pObjects']:
   need(type(obj)is dict and {'objectType','objectHandle'}<=set(obj)<={'objectType','objectHandle','pObjectName'},'object schema')
   need(uint(obj['objectType']) and uint(obj['objectHandle'],64),'object numeric fields')
   if 'pObjectName'in obj:need(obj['pObjectName']is None or type(obj['pObjectName'])is str and len(obj['pObjectName'])<=4096,'object name')
 return data
def metadata(raw):
 m=parse(raw);need(type(m)is dict and set(m)=={'schema','origin','layer_spec','settings','source_tests_head','source_skill_head'},'metadata schema')
 need(type(m['schema'])is int and m['schema']==1 and m['origin']in ('USER_SUPPLIED','SYNTHETIC_FIXTURE','HISTORICAL_LOCAL_CAPTURE'),'metadata origin')
 need(m['layer_spec']is None or uint(m['layer_spec']) and m['layer_spec']>>29==0,'Vulkan layer version encoding')
 need(type(m['settings'])is dict and set(m['settings'])=={'validation','sync_validation','gpu_assisted'},'settings schema')
 need(all(v is None or type(v)is bool for v in m['settings'].values()),'settings values')
 for k in ('source_tests_head','source_skill_head'):need(m[k]is None or type(m[k])is str and re.fullmatch('[0-9a-f]{40}',m[k]),'historical source head')
 return m
def plain(text):
 class Parser(HTMLParser):
  def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
  def handle_data(self,s):self.parts.append(s)
 p=Parser();p.feed(text);p.close();return ''.join(p.parts)
def analyze(raw,meta_raw,corpus):
 rows=callbacks(raw);m=metadata(meta_raw);observations=[];import_id='import-'+digest((digest(raw)+':'+digest(meta_raw)).encode())
 for i,row in enumerate(rows):
  mid=row.get('pMessageIdName');recognized=type(mid)is str and (mid in corpus['entries'] or mid=='SYNC-HAZARD-READ-AFTER-WRITE')
  if not recognized:lookup=dict(status='UNKNOWN',reason='identifier absent or not recognized in fixed corpus/curated tool allowlist')
  elif m['layer_spec']is None:lookup=dict(status='UNKNOWN',reason='missing declared validation-layer version')
  else:lookup=spec.lookup(corpus,mid,m['layer_spec'])
  # Do not copy generic routes or untrusted callback text/object identifiers.
  entry=dict(evidence_id=import_id+'/callback/'+str(i),json_pointer='/'+str(i)+'/pMessageIdName',diagnostic=mid if recognized else 'UNMATCHED_IDENTIFIER',identifier_sha256=digest(mid.encode()) if type(mid)is str else None,object_count=row['objectCount'],lookup_status=lookup['status'],version_basis='CALLER_DECLARED_NOT_RUNTIME_VERIFIED',condition_applicability='NOT_ESTABLISHED',resource_identity=None,source_location=None,submission=None)
  if 'reason'in lookup:entry['lookup_reason']=lookup['reason']
  if 'normative_entries'in lookup:entry['normative_entries']=[dict(vuid=x['vuid'],api_owner=x['api_owner'],condition_key=x['condition_key'],page=x['page'],text=plain(x['text_html'])) for x in lookup['normative_entries']]
  if recognized and mid in ROUTES and lookup['status']in ('MATCHED_SPEC_ENTRY','TOOL_DIAGNOSTIC'):
   route,kind,hypothesis,steps,stop=ROUTES[mid];entry['triage']=dict(status='UNCONFIRMED_HYPOTHESIS',kind=kind,knowledge_path='references/03_api_manual/'+route,hypothesis=hypothesis,support=['Only this imported diagnostic identifier; not independently verified offending behavior.'],counterevidence=[],counterevidence_state='NOT_YET_EXAMINED',next_steps=steps,stop_condition=stop,patch='NOT_PROPOSED',experiment='NOT_EXECUTED')
  else:entry['triage']=dict(status='NO_CURATED_HYPOTHESIS',next_steps=['Supply the missing declared tool version or review the exact conditional specification entry; do not infer a root cause.'])
  observations.append(entry)
 return dict(schema=1,import_id=import_id,import_identity_scope='Content-pair identity, not runtime identity; identical bytes do not prove the same execution',run_id=None,device_scope=None,status='IMPORTED_READ_ONLY_TRIAGE',callback_sha256=digest(raw),metadata_sha256=digest(meta_raw),metadata=m,metadata_authority='CALLER_DECLARED_NOT_AUTHENTICATED',normative_source=corpus['source'],observations=observations,counts={k:sum(x['lookup_status']==k for x in observations) for k in ('MATCHED_SPEC_ENTRY','TOOL_DIAGNOSTIC','UNKNOWN')},limitations=['No runtime, project, experiment or repair was executed.','Raw messages, handles, object names and user file paths are deliberately omitted.','Hashes bind input bytes; neither hashes nor declared revisions authenticate their origin.','Layer version match is conditional on supplied metadata; device API version is not a layer version.','SyncVal identifiers are tool diagnostics, not invented VUID clauses.','Empty log, indexing success or absent counterevidence does not establish correctness.','No run/device identity is collected by this importer; even matching historical heads do not join observations into a run.','Only three exact identifiers have curated unconfirmed triage; no full C3/C4 or release acceptance.'])
def render(report):
 def safe(v):return html.escape(str(v)).replace('`','&#96;').replace('\n',' ')
 lines=['# Imported validation triage / 导入诊断分诊','', 'Only imported observations and unconfirmed hypotheses. 未执行用户程序，未证明根因或修复。','', 'Version and settings are caller declarations, not runtime verification.','']
 for o in report['observations']:
  lines+=['## '+safe(o['diagnostic']),safe(o['json_pointer'])+' · '+safe(o['lookup_status'])]
  for clause in o.get('normative_entries',[]):lines+=['- Conditional specification: '+safe(clause['text']),'  Condition: '+safe(clause['condition_key'])]
  t=o['triage']
  if 'hypothesis'in t:lines+=['Unconfirmed: '+safe(t['hypothesis'])]
  lines+=['- '+safe(s) for s in t['next_steps']]
  if 'stop_condition'in t:lines+=['Stop: '+safe(t['stop_condition'])]
  lines+=['']
 if not report['observations']:lines+=['No callback records. This is not evidence of program correctness.']
 return '\n'.join(lines)+'\n'
