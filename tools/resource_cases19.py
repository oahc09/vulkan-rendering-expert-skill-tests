"""Offline scoped candidate ledger. Digests are not signatures or reviewer identity proof."""
import copy,hashlib,json,re,datetime,uuid
FAMILIES=('device_address','ray_query','robust_buffer','headless_wsi')
PROFILES={'device_address':['bufferDeviceAddress','shaderInt64','coherent-host-memory','physical-storage-address-chain'], 'ray_query':['bufferDeviceAddress','accelerationStructure','rayQuery','coherent-host-memory'], 'robust_buffer':['robustBufferAccess','robustBufferAccess2','nullDescriptor','coherent-host-memory'], 'headless_wsi':['headlessSurface','swapchain','swapchainMaintenance1','present-fence']}
def require(ok,msg):
 if not ok:raise ValueError(msg)
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def hashcheck(v):require(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v),'SHA256 required')
def instant(v):
 require(isinstance(v,str),'UTC timestamp required');d=datetime.datetime.fromisoformat(v.replace('Z','+00:00'));require(d.tzinfo==datetime.timezone.utc,'UTC required');return d

def candidate(index,family,index_sha):
 hashcheck(index_sha);require(family in FAMILIES,'unknown family');f=next(x for x in index['families'] if x['family']==family)
 refs=[{'kind':'raw-or-source','path':family+'/'+p,'sha256':h} for p,h in sorted(f['artifacts'].items()) if p.endswith(('.stdout','.stderr','summary.json'))]
 refs += [{'kind':'repository-source','path':p,'sha256':h} for p,h in sorted(index['source_manifest'].items()) if p.startswith('cases19/'+family+'/') or p=='tools/'+family+'19.py']
 base={'schema':1,'author':'repository-authored-fixture','origin':'Controlled authored fixture, not external production bug','sanitized':True,'scope':{'family':family,'cpu_identity':f['cpu_identity'],'required_feature_profile':PROFILES[family],'access_profile':family+'-fixed-fixture-v1','tests_head':index['tests_head'],'skill_head':index['skill_head'],'tool_cohort_sha256':digest(index['tool_hashes']),'toolchain_sha256':index['toolchain_sha256'],'normative_sha256':'f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7','normative_version':'1.4.309'},'bundle_index_sha256':index_sha,'run_id':f['run_id'],'observed_status':f['status'],'evidence':refs,'minimal_fix':'NOT_DEMONSTRATED: these are behavior fixtures, not repair patches','interpretation':'Positive output, expected API rejection and deliberately wrong oracle are distinct; no automatic root-cause or patch claim.','revisit_conditions':['Any device, driver, API, feature, source, access-pattern or tool change','New contradictory evidence or expiration'],'authority':'Scoped experience candidate, never specification or full release acceptance'}
 return {'id':digest(base),'base':base,'state':'candidate','history':[]}

def scopecheck(scope):
 require(isinstance(scope,dict) and set(scope)=={'family','cpu_identity','required_feature_profile','access_profile','tests_head','skill_head','tool_cohort_sha256','toolchain_sha256','normative_sha256','normative_version'},'scope schema')
 for k in ('tool_cohort_sha256','toolchain_sha256','normative_sha256'):hashcheck(scope[k])
 require(scope['normative_version']=='1.4.309' and scope['normative_sha256']=='f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7','normative cohort')
 family=scope['family'];require(family in FAMILIES and scope['required_feature_profile']==PROFILES[family] and scope['access_profile']==family+'-fixed-fixture-v1','feature/access scope')
 identity=scope['cpu_identity'];keys={'deviceType','apiVersion','vendorID','deviceID','driverVersion','layerSpec','layerImplementation'}
 require(isinstance(identity,dict) and set(identity)==keys and all(type(v) is int and 0<=v<2**32 for v in identity.values()),'identity scope')
 require(identity['deviceType']==4 and identity['apiVersion']>>29==0 and identity['layerSpec']>>29==0,'CPU Vulkan variant scope')
 for k in ('tests_head','skill_head'):require(isinstance(scope[k],str) and re.fullmatch('[0-9a-f]{40}',scope[k]),'source head scope')
def review_evidence(base):
 family=base['scope']['family'];refs={r['path']:r['sha256'] for r in base['evidence']};negative={'device_address':'missing-usage','ray_query':'offset','robust_buffer':'null-disabled','headless_wsi':'invalid-acquire'}[family]
 return {'reproduction':refs[family+'/good.stdout'],'counterexample_review':digest({p:refs[p] for p in (family+'/wrong-output.stdout',family+'/wrong-output.stderr',family+'/'+negative+'.stdout',family+'/'+negative+'.stderr')})}
def validate(record):
 require(set(record)=={'id','base','state','history'},'record schema');scopecheck(record['base']['scope'])
 base=record['base'];require(record['id']==digest(base),'candidate content changed');require(base['schema']==1 and base['sanitized'] is True and base['scope']['family'] in FAMILIES,'invalid candidate')
 base=record['base'];require(set(base)=={'schema','author','origin','sanitized','scope','bundle_index_sha256','run_id','observed_status','evidence','minimal_fix','interpretation','revisit_conditions','authority'},'base allowlist')
 constants={'author':'repository-authored-fixture','origin':'Controlled authored fixture, not external production bug','minimal_fix':'NOT_DEMONSTRATED: these are behavior fixtures, not repair patches','interpretation':'Positive output, expected API rejection and deliberately wrong oracle are distinct; no automatic root-cause or patch claim.','revisit_conditions':['Any device, driver, API, feature, source, access-pattern or tool change','New contradictory evidence or expiration'],'authority':'Scoped experience candidate, never specification or full release acceptance'}
 require(all(base[k]==v for k,v in constants.items()),'fixed sanitized text required');hashcheck(base['bundle_index_sha256']);require(str(uuid.UUID(base['run_id']))==base['run_id'],'canonical UUID required')
 family=base['scope']['family'];statuses={'device_address':'BOUNDED_PHYSICAL_STORAGE_ADDRESS_PASS','ray_query':'BOUNDED_BLAS_TLAS_RAY_QUERY_PASS','robust_buffer':'BOUNDED_ROBUST2_BUFFER_PASS','headless_wsi':'BOUNDED_HEADLESS_WSI_PASS'};require(base['observed_status']==statuses[family],'bounded status')
 refs=base['evidence'];require(isinstance(refs,list) and len(refs)>0,'evidence required');seen=set()
 allowed_sources={f'cases19/{family}/{f}' for f in ('probe.c','run.py','normative.json')}|{'tools/'+family+'19.py'}
 if family!='headless_wsi':allowed_sources.add(f'cases19/{family}/compute.comp')
 if family=='device_address':allowed_sources.add(f'cases19/{family}/capability_inventory.c')
 labels={'good','wrong-output',{'device_address':'missing-usage','ray_query':'offset','robust_buffer':'null-disabled','headless_wsi':'invalid-acquire'}[family],'build','compile','validate','disassemble','inventory','inventory-build','glslangValidator-version','shader-compile','shader-val','shader-dis','spirv-val-version','spirv-dis-version'}
 allowed_raw={family+'/summary.json'}|{family+'/'+label+'.'+ext for label in labels for ext in ('stdout','stderr')}
 for ref in refs:
  require(isinstance(ref,dict) and set(ref)=={'kind','path','sha256'},'reference schema');hashcheck(ref['sha256']);require(ref['kind'] in ('raw-or-source','repository-source'),'reference kind');require(ref['path'] in (allowed_sources if ref['kind']=='repository-source' else allowed_raw),'reference path allowlist');require(ref['path'] not in seen,'duplicate reference');seen.add(ref['path'])
 required_raw={family+'/summary.json'}|{family+'/'+label+'.'+ext for label in ('good','wrong-output',{'device_address':'missing-usage','ray_query':'offset','robust_buffer':'null-disabled','headless_wsi':'invalid-acquire'}[family]) for ext in ('stdout','stderr')}
 require((allowed_sources|required_raw)<=seen,'required source/case/summary evidence missing')
 state='candidate';previous=record['id'];last=None
 for event in record['history']:
  require(set(event)=={'action','at','reviewer','scope_sha256','evidence','expires_at','previous','sha256'},'event keys')
  value={k:v for k,v in event.items() if k!='sha256'};require(event['sha256']==digest(value) and event['previous']==previous,'history chain changed');now=instant(event['at']);require(last is None or now>=last,'history reversed');last=now
  require(event['scope_sha256']==digest(base['scope']),'scope elevation');require(state in ('candidate','reviewed'),'inactive record')
  require(isinstance(event['reviewer'],str) and re.fullmatch('[A-Za-z0-9_.@-]{1,100}',event['reviewer']) and event['reviewer']!=base['author'],'distinct declared reviewer required; identity not authenticated')
  ev=event['evidence'];require(isinstance(ev,dict),'evidence map required')
  if event['action']=='review':
   require(state=='candidate' and set(ev)=={'reproduction','counterexample_review','review_report'},'concrete review evidence required');require(instant(event['expires_at'])>now,'review already expired');expected=review_evidence(base);require(all(ev[k]==v for k,v in expected.items()),'review evidence not bound to actual positive and negatives');state='reviewed'
  else:
   require(event['action'] in ('revoke','expire') and set(ev)=={'decision_report'} and event['expires_at'] is None,'revocation evidence required');state='revoked' if event['action']=='revoke' else 'expired'
  for h in ev.values():hashcheck(h)
  previous=event['sha256']
 require(record['state']==state,'state not derived from history');return state

def transition(record,action,at,reviewer,evidence,scope,expires_at=None):
 validate(record);require(scope==record['base']['scope'],'scope must match exactly');out=copy.deepcopy(record)
 ev={'action':action,'at':at,'reviewer':reviewer,'scope_sha256':digest(scope),'evidence':evidence,'expires_at':expires_at,'previous':out['history'][-1]['sha256'] if out['history'] else out['id']};ev['sha256']=digest(ev);out['history'].append(ev);out['state']={'review':'reviewed','revoke':'revoked','expire':'expired'}.get(action,'invalid');validate(out);return out

def retrieve(records,scope,now):
 at=instant(now);scopecheck(scope);hits=[];excluded=[];require(len({r['id'] for r in records})==len(records),'duplicate candidate IDs: select one anchored latest ledger version')
 for record in records:
  state=validate(record);reason=None
  if state!='reviewed':reason=state
  elif record['base']['scope']!=scope:reason='scope mismatch'
  elif at<instant(record['history'][-1]['at']):reason='review is in future'
  elif at>=instant(record['history'][-1]['expires_at']):reason='expired'
  if reason:excluded.append({'id':record['id'],'reason':reason});continue
  hits.append({'id':record['id'],'matched_scope':copy.deepcopy(scope),'evidence':record['base']['evidence'],'next_validation':record['base']['revisit_conditions'],'authority':record['base']['authority']})
 return {'hits':hits,'excluded':excluded,'trust':'Reviewer/evidence digests are caller attestations, not authenticated identities. Caller must anchor the latest ledger digest externally; selecting an old anchor can replay an old state.'}
