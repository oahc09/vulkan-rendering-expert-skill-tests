"""Bounded declared buffer trace joins. Never actual Vulkan/GPU proof.
No evidence digest or declared authority authenticates a fact or reviewer.
"""
import copy,re,json
from . import memory_binding_contract19 as memory, sync_contract19 as sync, timeline_contract19 as timeline, descriptor_update_contract19 as update
TOKEN=re.compile(r'[A-Za-z0-9_.:-]{1,80}')
def require(x,why):
 if not x:raise ValueError(why)
def uint(x):return type(x)is int and 0<=x<2**64
def token(x):return type(x)is str and TOKEN.fullmatch(x) is not None
def exact(x,keys):return type(x)is dict and set(x)==set(keys)
def trace_subject(trace):
 body={k:trace[k] for k in ('schema','scope','allocations','buffers','events')}
 import hashlib
 return {'trace_sha256':hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()}
def check(trace):
 if type(trace)is dict and type(trace.get("schema"))is int and trace["schema"]==2:
  from .resource_capture19 import check_v2
  return check_v2(trace)
 rows=[];position=None
 def result(status,reason=None):return dict(status=status,event_index=position,reason=reason,events=rows,authority='CALLER_DECLARED_TRACE_NOT_DEVICE_PROOF',composed=['memory_binding','descriptor_reference_lifetime','sync','timeline_snapshot'],not_composed=['pipeline_layout_compatibility','image_copy','image_layout'],release_status='BLOCKED',semantic_L1_L2_completion='NOT_INFERRED')
 try:
  require(len(json.dumps(trace,allow_nan=False))<=262144,'bounded trace bytes')
  require(exact(trace,{'schema','scope','allocations','buffers','proofs','events'}),'trace schema')
  require(trace['schema']==1 and type(trace['schema'])is int and trace['scope']=='ordinary-single-device-single-queue-nonalias-nondedicated-buffer','scope')
  for k in ('allocations','buffers','proofs','events'):require(type(trace[k])is list and 0<len(trace[k])<=128,'bounded '+k)
  allocations={};buffers={};proofs={};eventids=set()
  for a in trace['allocations']:
   require(exact(a,{'id','generation','size','memory_type_index'}) and token(a['id']) and all(uint(a[k]) for k in ('generation','size','memory_type_index')) and a['size']>0 and a['memory_type_index']<32,'allocation schema')
   key=(a['id'],a['generation']);require(key not in allocations,'duplicate allocation generation');allocations[key]={**a,'live':True}
  for b in trace['buffers']:
   require(exact(b,{'id','generation','allocation','allocation_generation','buffer_size','requirements_size','alignment','type_bits','offset'}) and token(b['id']) and token(b['allocation']) and all(uint(b[k]) for k in ('generation','allocation_generation','buffer_size','requirements_size','alignment','type_bits','offset')),'buffer schema')
   key=(b['id'],b['generation']);require(key not in buffers,'duplicate buffer generation');require(0<b['buffer_size']<=b['requirements_size'],'buffer versus requirement size');require((b['allocation'],b['allocation_generation'])in allocations,'missing allocation identity');buffers[key]={**b,'bound':False}
  for p in trace['proofs']:
   require(exact(p,{'id','authority','kind','subject','evidence_sha256'}) and token(p['id']) and p['authority']in ('CALLER_DECLARED','UNRESOLVED') and type(p['kind'])is str and type(p['subject'])is dict and type(p['evidence_sha256'])is str and re.fullmatch('[0-9a-f]{64}',p['evidence_sha256']),'proof schema; no VERIFIED authority')
   require(p['id']not in proofs,'duplicate proof');proofs[p['id']]=p
  for e in trace['events']:require(type(e)is dict and token(e.get('id')) and e['id']not in eventids,'event ID');eventids.add(e['id'])
  def proof(ref,kind,subject):
   p=proofs.get(ref)
   if p is None or p['authority']=='UNRESOLVED' or p['kind']!=kind or json.dumps(p['subject'],sort_keys=True,separators=(',',':'),allow_nan=False)!=json.dumps(subject,sort_keys=True,separators=(',',':'),allow_nan=False):raise LookupError('obligation not established: '+kind)
  proof('trace-complete','TRACE_AND_HOST_SCOPE',trace_subject(trace))
  descriptors={};recordings={};submissions={};accesses=[];dependencies={}
  def buffer(e):
   require(token(e['buffer']) and uint(e['generation']),'exact buffer identity types');key=(e['buffer'],e['generation']);require(key in buffers,'unknown buffer generation');return buffers[key]
  def allocation(b):return allocations[b['allocation'],b['allocation_generation']]
  def subject(b,e):return dict(buffer=b['id'],generation=b['generation'],allocation=b['allocation'],allocation_generation=b['allocation_generation'],event=e['id'])
  for position,e in enumerate(trace['events']):
   op=e.get('op');local=None
   if op=='bind':
    require(exact(e,{'id','op','buffer','generation','proof'}),'bind event');b=buffer(e);a=allocation(b);require(a['live'],'bind freed allocation');proof(e['proof'],'ORDINARY_ALLOCATION_VALID',subject(b,e))
    local=memory.bind(dict(kind='buffer',resource_id=b['id'],ordinary_scope_proven=True,allocation_creation_valid=True,same_device=True,requirements_size=b['requirements_size'],requirements_alignment=b['alignment'],memory_type_bits=b['type_bits'],memory_type_index=a['memory_type_index'],allocation_size=a['size'],offset=b['offset'],already_bound=b['bound'],requires_dedicated=False,prefers_dedicated=False,dedicated=None));require(local['status']=='BIND_CONDITIONS_WITHIN_SCOPE','binding conditions');b['bound']=True
    for other in buffers.values():
     if other is b or not other['bound'] or (other['allocation'],other['allocation_generation'])!=(b['allocation'],b['allocation_generation']):continue
     if max(other['offset'],b['offset'])<min(other['offset']+other['requirements_size'],b['offset']+b['requirements_size']):raise LookupError('aliasing excluded from this trace scope')
   elif op=='write_descriptor':
    require(exact(e,{'id','op','set','buffer','generation','offset','size','proof'}) and token(e['set']) and uint(e['offset']) and uint(e['size']),'write schema');b=buffer(e);require(b['bound'] and allocation(b)['live'],'descriptor resource not live/bound');require(e['size']>0 and e['offset']+e['size']<=b['buffer_size'],'descriptor range');proof(e['proof'],'DESCRIPTOR_PAYLOAD_AND_LAYOUT_VALID',dict(**subject(b,e),offset=e['offset'],size=e['size'],set=e['set']))
    require(not any(not s['complete'] and s['set']==e['set'] for s in submissions.values()),'ordinary descriptor update while consumer pending')
    layout=[dict(binding=0,count=1,type='STORAGE_BUFFER',stages=32,flags=0,immutable_reference_signature=None)]
    empty=dict(reference='empty',defined=False,resource_live=True)
    local=update.apply({'D':dict(layout=layout,values=[[empty]])},[dict(set='D',binding=0,element=0,type='STORAGE_BUFFER',values=[dict(reference=b['id']+':'+str(b['generation']),defined=True,resource_live=True)])],[],True);require(local['status']=='MODELED_UPDATES','descriptor write local contract')
    descriptors[e['set']]=dict(buffer=b['id'],generation=b['generation'],offset=e['offset'],size=e['size'],defined=True)
    for r in recordings.values():
     if r['set']==e['set']:r['valid']=False
   elif op=='copy_descriptor':
    require(exact(e,{'id','op','src','dst','proof'}) and token(e['src']) and token(e['dst']) and e['src']!=e['dst'],'copy schema');require(e['src']in descriptors,'copy source missing');proof(e['proof'],'DESCRIPTOR_COPY_LAYOUT_VALID',dict(event=e['id'],src=e['src'],dst=e['dst']))
    require(not any(not s['complete'] and s['set']==e['dst'] for s in submissions.values()),'copy destination pending')
    d=copy.deepcopy(descriptors[e['src']]);b=buffers[d['buffer'],d['generation']];layout=[dict(binding=0,count=1,type='STORAGE_BUFFER',stages=32,flags=0,immutable_reference_signature=None)]
    src=dict(reference=b['id']+':'+str(b['generation']),defined=d['defined'],resource_live=allocation(b)['live']);empty=dict(reference='empty',defined=False,resource_live=True)
    local=update.apply({'S':dict(layout=layout,values=[[src]]),'D':dict(layout=layout,values=[[empty]])},[],[dict(src_set='S',src_binding=0,src_element=0,dst_set='D',dst_binding=0,dst_element=0,count=1)],True);require(local['status']=='MODELED_UPDATES','descriptor copy local contract');d['defined']=local['state_after']['D']['values'][0][0]['defined'];descriptors[e['dst']]=d
    for r in recordings.values():
     if r['set']==e['dst']:r['valid']=False
   elif op=='record_use':
    require(exact(e,{'id','op','cb','set','access','proof'}) and token(e['cb']) and token(e['set']) and e['access']in ('READ','WRITE'),'record schema');require(e['set']in descriptors,'descriptor missing');d=descriptors[e['set']];b=buffers[d['buffer'],d['generation']];require(d['defined'] and allocation(b)['live'],'undefined/dead descriptor cannot be used');require(not any(not s['complete'] and s['cb']==e['cb'] for s in submissions.values()),'record pending CB');proof(e['proof'],'PIPELINE_LAYOUT_AND_ACCESS_SCOPE',dict(**subject(b,e),cb=e['cb'],set=e['set'],offset=d['offset'],size=d['size'],access=e['access']))
    recordings[e['cb']]=dict(**d,cb=e['cb'],set=e['set'],access=e['access'],record_event=e['id'],valid=True)
   elif op=='sync_proof':
    require(exact(e,{'id','op','first','second','buffer','generation','offset','size','proof'}),'sync schema');b=buffer(e);require(uint(e['offset']) and uint(e['size']) and e['size']>0 and e['offset']+e['size']<=b['buffer_size'],'sync range');proof(e['proof'],'SCOPED_GPU_DEPENDENCY',dict(**subject(b,e),first=e['first'],second=e['second'],offset=e['offset'],size=e['size']));dependencies[e['first'],e['second']]=copy.deepcopy(e)
   elif op=='submit':
    require(exact(e,{'id','op','submission','cb'}) and token(e['submission']) and token(e['cb']) and e['submission']not in submissions,'submit schema');require(e['cb']in recordings,'unrecorded CB');r=recordings[e['cb']];require(not any(not s['complete'] and s['cb']==e['cb'] for s in submissions.values()),'pending CB resubmit outside scope');require(not any(s['record_event']==r['record_event'] for s in submissions.values()),'recording already submitted; rerecord required');b=buffers[r['buffer'],r['generation']];require(r['valid'] and allocation(b)['live'],'stale recording or freed memory')
    for previous in accesses:
     if (previous['buffer'],previous['generation'])!=(r['buffer'],r['generation']):continue
     if max(previous['offset'],r['offset'])>=min(previous['offset']+previous['size'],r['offset']+r['size']):continue
     if previous['access']==r['access']=='READ':continue
     d=dependencies.get((previous['record_event'],r['record_event']))
     if d is None:raise LookupError('binding/completion/order is not a scoped GPU dependency')
     require(d['buffer']==r['buffer'] and d['generation']==r['generation'] and d['offset']<=max(previous['offset'],r['offset']) and d['offset']+d['size']>=min(previous['offset']+previous['size'],r['offset']+r['size']),'dependency identity/range mismatch')
     f={k:True for k in sync.BOOL_FIELDS};f.update(layout_transition=False,ownership_transfer=False,memory_domain_transfer=False,host_fence_completed=False,first_access=previous['access'],second_access=r['access']);local=sync.evaluate(f);require(local['status']=='CALLER_FACTS_SUFFICIENT','sync contract')
    submissions[e['submission']]={**copy.deepcopy(r),'submit_event':e['id'],'complete':False};accesses.append(copy.deepcopy(r))
   elif op=='complete':
    require(exact(e,{'id','op','submission','proof'}) and e['submission']in submissions,'completion subject');s=submissions[e['submission']];proof(e['proof'],'SUBMISSION_ALL_USES_COMPLETED',dict(event=e['id'],submission=e['submission'],record_event=s['record_event'],buffer=s['buffer'],generation=s['generation'],allocation=buffers[s['buffer'],s['generation']]['allocation'],allocation_generation=buffers[s['buffer'],s['generation']]['allocation_generation'],submit_event=s['submit_event']));s['complete']=True
   elif op=='timeline_snapshot':
    require(exact(e,{'id','op','counter','target'}),'timeline event');local=timeline.wait_condition([e['counter']],[e['target']],'ALL');require(local['status']=='SNAPSHOT_PREDICATE_ONLY','timeline values')
   elif op=='free':
    require(exact(e,{'id','op','allocation','generation','proof'}) and token(e['allocation']) and uint(e['generation']),'free schema');key=(e['allocation'],e['generation']);require(key in allocations and allocations[key]['live'],'free identity');proof(e['proof'],'HOST_ACCESS_COMPLETED_NO_CONCURRENT_ACCESS',dict(event=e['id'],allocation=e['allocation'],generation=e['generation']))
    refs=[s for s in submissions.values() if (buffers[s['buffer'],s['generation']]['allocation'],buffers[s['buffer'],s['generation']]['allocation_generation'])==key]
    local=memory.free_obligations(dict(bound_object_count=sum(b['bound'] and (b['allocation'],b['allocation_generation'])==key for b in buffers.values()),all_submitted_uses_retired=all(s['complete'] for s in refs),host_accesses_completed=True,no_future_bound_resource_use=True,reference_inventory_complete=True));require(local['status']=='FREE_LIFETIME_OBLIGATIONS_DECLARED','pending references forbid free');allocations[key]['live']=False
   else:raise ValueError('unknown operation')
   rows.append(dict(id=e['id'],op=op,result=local or {'status':'MODELED_REFERENCE_EVENT'}))
  return result('CONSISTENT_DECLARED_TRACE')
 except LookupError as e:return result('OBLIGATIONS_NOT_ESTABLISHED',str(e))
 except (ValueError,KeyError,TypeError,OverflowError) as e:return result('REJECTED_DECLARED_TRACE',str(e))
