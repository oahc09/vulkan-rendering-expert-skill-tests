"""Ordinary Vulkan pipeline-cache persistence policy, not opaque payload validation."""
import hashlib,math,statistics,struct

def digest(s,n=64):return type(s) is str and len(s)==n and all(c in '0123456789abcdef' for c in s)
def u32(v):return type(v) is int and 0<=v<2**32

def inspect_cache(blob,device,lineage):
 """Application-side conservative reuse filter. Does not execute Vulkan.
 A header match does not establish arbitrary opaque payload legality. Lineage is
 caller-attested vkGetPipelineCacheData provenance plus exact complete-byte hash.
 Driver equality is an extra application policy, not a header member.
 """
 out=dict(status='UNKNOWN',reuse=False,opaque_payload_validated=False,vuids=[],scope='ordinary Vulkan header version1 only; not Vulkan SC/pipeline binaries/GPL/shader objects')
 def fail(reason,status='REJECT_CACHE_USE'):return dict(out,status=status,reason=reason)
 if type(blob) is not bytes:return fail('cache bytes required','UNKNOWN')
 dk={'vendor_id','device_id','driver_version','pipeline_cache_uuid'}
 if type(device) is not dict or set(device)!=dk or any(not u32(device[k]) for k in dk-{'pipeline_cache_uuid'}) or not digest(device['pipeline_cache_uuid'],32):return fail('exact device identity required','UNKNOWN')
 lk={'producer','sha256','bytes','device','complete_export','unmodified','source_record_sha256'}
 if type(lineage) is not dict or set(lineage)!=lk:return fail('explicit complete-byte export provenance required','UNKNOWN')
 if lineage['producer']!='vkGetPipelineCacheData' or lineage['complete_export'] is not True or lineage['unmodified'] is not True or not digest(lineage['source_record_sha256']):return fail('unestablished export origin','UNKNOWN')
 if type(lineage['bytes']) is not int or lineage['bytes']!=len(blob) or not digest(lineage['sha256']) or hashlib.sha256(blob).hexdigest()!=lineage['sha256']:return fail('complete blob length/hash mismatch')
 if lineage['device']!=device:return fail('producer device/driver policy mismatch')
 if len(blob)<32:return fail('truncated header')
 size,version,vendor,dev=struct.unpack_from('<4I',blob)
 uuid=blob[16:32].hex();out['header']=dict(header_size=size,header_version=version,vendor_id=vendor,device_id=dev,pipeline_cache_uuid=uuid)
 if version!=1 or size!=32:return fail('unsupported ordinary version1 header shape')
 if vendor!=device['vendor_id'] or dev!=device['device_id'] or uuid!=device['pipeline_cache_uuid']:return fail('cache header identity mismatch')
 return dict(out,status='REUSE_ELIGIBLE_BY_DECLARED_PROVENANCE',reuse=True,reason='exact opaque bytes and declared export provenance match; not payload validation',evidence_authority='CALLER_ATTESTED_NOT_AUTHENTICATED')

def finite(v):
 try:return type(v) in (int,float) and math.isfinite(v)
 except OverflowError:return False

def decide(cache,measurement,policy):
 """Creation-only timings never establish first-frame or steady-state benefit."""
 def result(s,reason,selected='COLD_BASELINE'):return dict(rule_id='ordinary-pipeline-cache-cost-v1',version_scope='ordinary Vulkan1 cache header; fixed368 prose; caller performance evidence',status=s,reason=reason,selected=selected,fallback='COLD_BASELINE' if selected is not None else None,revisit_conditions=['device/driver/cacheUUID change','shader/workload/tool/protocol change','first/steady frame regression','storage or other objective change'],overlap_or_cache_hit_proven=False,evidence_authority='CALLER_DECLARED_NOT_AUTHENTICATED',limitations=['Cache retrieval/pipeline creation are not pipeline execution or output correctness.','CPU API timing is not GPU time or proof of cache hit.','Sequential cold/warm calls can share implicit driver caches and warmup; not a controlled A/B.','Cache byte size is serialized storage, not resident/peak GPU memory.','No cross-driver portability, full C2 or release acceptance.'])
 pk={'baseline_verified','candidate_active','max_cache_bytes','minimum_first_frame_gain','max_steady_regression','other_objectives_satisfied'}
 if type(policy) is not dict or set(policy)!=pk or any(type(policy[k]) is not bool for k in ('baseline_verified','candidate_active','other_objectives_satisfied')) or type(policy['max_cache_bytes']) is not int or not 0<=policy['max_cache_bytes']<2**63:return result('UNKNOWN','invalid explicit policy',None)
 if any(not finite(policy[k]) or not 0<=policy[k]<1 for k in ('minimum_first_frame_gain','max_steady_regression')):return result('UNKNOWN','invalid cost tolerance',None)
 if not policy['baseline_verified']:return result('UNKNOWN','baseline correctness not established',None)
 if type(cache) is not dict or set(cache)!={'admission','bytes'} or type(cache['bytes']) is not int or cache['bytes']<0 or type(cache['admission']) is not dict:return result('UNKNOWN','cache evidence required')
 if cache['admission'].get('status')!='REUSE_ELIGIBLE_BY_DECLARED_PROVENANCE' or cache['admission'].get('reuse') is not True or cache['bytes']>policy['max_cache_bytes']:return result('REVOKE_TO_BASELINE' if policy['candidate_active'] else 'KEEP_BASELINE','cache policy or storage budget rejected')
 if measurement is None:return result('NEEDS_MEASUREMENT','missing comparable first-frame/steady/output/other-cost evidence')
 keys={'cohort_equal','paired_protocol','output_equal','baseline','candidate','source_sha256'}
 if type(measurement) is not dict or set(measurement)!=keys or not digest(measurement['source_sha256']):return result('NEEDS_MEASUREMENT','bounded paired measurement schema missing')
 if any(measurement[k] is not True for k in ('cohort_equal','paired_protocol','output_equal')):return result('REVOKE_TO_BASELINE' if policy['candidate_active'] else 'NEEDS_MEASUREMENT','cohort/protocol/correctness not established')
 for k in ('baseline','candidate'):
  v=measurement[k]
  if type(v) is not dict or set(v)!={'creation_cpu_ns','first_frame_ns','steady_frame_ns','cohort'}:return result('NEEDS_MEASUREMENT','creation alone is not whole-frame evidence')
  co=v['cohort'];ck={'device','driver','workload','shader','tools','input','resolution','clock_domain','thermal','warmup_protocol','run_order_protocol'}
  if type(co) is not dict or set(co)!=ck or any(type(x) is not str or not x for x in co.values()):return result('NEEDS_MEASUREMENT','exact cohort labels required')
  for field in ('creation_cpu_ns','first_frame_ns','steady_frame_ns'):
   a=v[field]
   if type(a) is not list or not 3<=len(a)<=4096 or any(not finite(x) or not 0<x<2**63 for x in a):return result('NEEDS_MEASUREMENT','at least three finite positive paired trials required')
  if len({len(v[k]) for k in ('creation_cpu_ns','first_frame_ns','steady_frame_ns')})!=1:return result('NEEDS_MEASUREMENT','within-path paired metric counts differ')
 b,c=measurement['baseline'],measurement['candidate']
 if b['cohort']!=c['cohort'] or any(len(b[k])!=len(c[k]) for k in ('creation_cpu_ns','first_frame_ns','steady_frame_ns')):return result('NEEDS_MEASUREMENT','noncomparable cohort/trials')
 bm,cm=statistics.median(b['first_frame_ns']),statistics.median(c['first_frame_ns'])
 if cm>bm or max(c['first_frame_ns'])>max(b['first_frame_ns']) or max(c['steady_frame_ns'])>max(b['steady_frame_ns'])*(1+policy['max_steady_regression']):return result('REVOKE_TO_BASELINE','first-frame/observed worst-frame regression outweighs creation speed')
 if not policy['other_objectives_satisfied']:return result('NEEDS_MEASUREMENT','memory/quality/latency/power tradeoffs unresolved')
 if cm>=bm or (bm-cm)/bm<policy['minimum_first_frame_gain']:return result('KEEP_BASELINE','no qualified first-frame improvement')
 return result('SELECT_DECLARED_PERSISTED_CACHE','declared paired full costs satisfy bounded policy; no general speed guarantee','PERSISTED_CACHE')
