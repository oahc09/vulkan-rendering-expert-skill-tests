"""Bounded caller-evidence compute scheduling decision; no overlap or timing probe.
Queue flags are capabilities, created queue records are separate facts. No brand rules.
"""
import math
import statistics

LIMITS = ['Caller declarations are not authenticated captures or Vulkan validation.',
 'Ordinary unprotected single-device queues only; complete stage/access and resource legality are caller-proven.',
 'A second queue does not guarantee overlap, independent hardware or a performance benefit.',
 'No thermal/power/latency/quality objective is silently inferred from full-frame duration.',
 'HOST decision contract, not executed async GPU benchmark or whole C2 acceptance.']

def finite(v):
 try:return type(v) in (int,float) and math.isfinite(v)
 except (OverflowError,ValueError):return False

def uint(v): return type(v) is int and 0 <= v < 2**32

def admission(f):
 """Exact facts for a graphics baseline and a chosen compute queue on one device."""
 def r(s,why): return dict(status=s,reason=why,overlap_proven=False)
 keys={'families','created','graphics','compute','requirements','ordinary_single_device','dependency_proven','resource_sharing','ownership_transfer_proven','lifetime_proven','baseline_no_implicit_transfer_exception','concurrent_families'}
 if type(f) is not dict or set(f)!=keys:return r('UNKNOWN','exact facts required')
 for k in ('ordinary_single_device','dependency_proven','ownership_transfer_proven','lifetime_proven','baseline_no_implicit_transfer_exception'):
  if type(f[k]) is not bool:return r('UNKNOWN','boolean facts required')
 if not f['ordinary_single_device']:return r('OUT_OF_SCOPE','protected/external/device-group paths excluded')
 if type(f['concurrent_families']) is not list or any(not uint(x) for x in f['concurrent_families']) or len(set(f['concurrent_families']))!=len(f['concurrent_families']):return r('UNKNOWN','invalid concurrent family list')
 if not f['baseline_no_implicit_transfer_exception']:return r('OUT_OF_SCOPE','implicit ownership exceptions not modeled')
 if f['resource_sharing'] not in ('EXCLUSIVE','CONCURRENT'):return r('UNKNOWN','resource sharing unspecified')
 fam=f['families'];created=f['created'];req=f['requirements']
 if type(fam) is not list or not 1<=len(fam)<=256 or type(created) is not list or len(created)>1024 or type(req) is not list or len(req)>256:return r('UNKNOWN','queue/requirement inventories required')
 fs={};qs=set();names=set()
 for x in fam:
  if type(x) is not dict or set(x)!={'family','flags','count'} or not all(uint(x[k]) for k in x) or not x['count'] or x['family'] in fs:return r('UNKNOWN','invalid/duplicate family')
  fs[x['family']]=x
 if f['resource_sharing']=='CONCURRENT' and (len(f['concurrent_families'])<2 or not set(f['concurrent_families']).issubset(fs)):return r('NOT_ADMISSIBLE','concurrent creation needs at least two known unique families')
 for x in created:
  if type(x) is not dict or set(x)!={'family','index'} or not all(uint(x[k]) for k in x):return r('UNKNOWN','invalid created queue')
  q=(x['family'],x['index'])
  if q in qs or q[0] not in fs or q[1]>=fs[q[0]]['count']:return r('UNKNOWN','created queue outside advertised inventory')
  qs.add(q)
 for x in req:
  if type(x) is not dict or set(x)!={'name','supported','enabled'} or type(x['name']) is not str or not x['name'] or x['name'] in names or any(type(x[k]) is not bool for k in ('supported','enabled')):return r('UNKNOWN','invalid feature requirements')
  names.add(x['name'])
  if not x['supported'] or not x['enabled']:return r('NOT_ADMISSIBLE','required feature unsupported or not enabled')
 picks=[]
 for name,flag in [('graphics',1),('compute',2)]:
  x=f[name]
  if type(x) is not dict or set(x)!={'family','index'} or not all(uint(x[k]) for k in x):return r('UNKNOWN','invalid queue selection')
  q=(x['family'],x['index']);picks.append(q)
  if q not in qs:return r('NOT_ADMISSIBLE','selected queue was not created')
  if not fs[q[0]]['flags']&flag:return r('NOT_ADMISSIBLE','selected queue lacks operation capability')
 if f['resource_sharing']=='CONCURRENT' and not set(q[0] for q in picks).issubset(set(f['concurrent_families'])):return r('NOT_ADMISSIBLE','resource concurrent creation does not include selected families')
 if not f['dependency_proven'] or not f['lifetime_proven']:return r('NEEDS_PROOF','dependency/lifetime not established; submission order/fence alone is insufficient')
 if picks[0][0]!=picks[1][0] and f['resource_sharing']=='EXCLUSIVE' and not f['ownership_transfer_proven']:return r('NEEDS_PROOF','cross-family exclusive ownership must be independently established in this baseline')
 return r('SINGLE_QUEUE' if picks[0]==picks[1] else 'MULTI_QUEUE_ADMISSIBLE','declared baseline obligations met; no overlap guarantee')


def decide(facts,measurement,policy):
 """Measured policy over declared paired trials, not a benchmark collector.

 full_frame includes identical frame boundaries and all relevant queue completion;
 pass durations are explanatory only. Median threshold is a caller policy, not
 statistical significance. Baseline is only fallback when explicitly verified.
 """
 out=dict(rule_id='ordinary-compute-scheduling-v1',admission=admission(facts),limitations=LIMITS.copy(),selected='BASELINE',overlap_proven=False,
          evidence_authority='CALLER_DECLARED_NOT_AUTHENTICATED',revisit_conditions=['device/driver/workload/tool change','dependency/ownership/feature change','full-frame regression or new measurement'])
 def r(s,why):return dict(out,status=s,reason=why)
 pk={'baseline_verified','candidate_active','minimum_gain_fraction','max_observed_frame_regression_fraction','other_objectives_satisfied'}
 if type(policy) is not dict or set(policy)!=pk or any(type(policy[k]) is not bool for k in pk-{'minimum_gain_fraction','max_observed_frame_regression_fraction'}):out['selected']=None;return r('UNKNOWN','exact policy required')
 gain=policy['minimum_gain_fraction']
 if not finite(gain) or not 0<=gain<1:out['selected']=None;return r('UNKNOWN','gain threshold invalid')
 tail=policy['max_observed_frame_regression_fraction']
 if not finite(tail) or not 0<=tail<1:out['selected']=None;return r('UNKNOWN','observed worst-frame tolerance invalid')
 if not policy['baseline_verified']:out['selected']=None;return r('UNKNOWN','baseline fallback has not been verified')
 if out['admission']['status']!='MULTI_QUEUE_ADMISSIBLE':return r('REVOKE_TO_BASELINE' if policy['candidate_active'] else 'KEEP_BASELINE','multi-queue candidate lacks bounded admission')
 if measurement is None:return r('NEEDS_MEASUREMENT','no comparable full-frame evidence; retain baseline')
 mk={'baseline','candidate','paired_trials','full_frame_boundaries_equal','all_queue_completion_included','measurement_method','output_equal','source_sha256'}
 if type(measurement) is not dict or set(measurement)!=mk:return r('NEEDS_MEASUREMENT','exact measurement schema required')
 if any(type(measurement[k]) is not bool or not measurement[k] for k in ('paired_trials','full_frame_boundaries_equal','all_queue_completion_included','output_equal')):return r('REVOKE_TO_BASELINE' if policy['candidate_active'] else 'NEEDS_MEASUREMENT','comparison/output obligations not established')
 h=measurement['source_sha256']
 if type(h) is not str or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):return r('NEEDS_MEASUREMENT','capture digest required (not authenticated)')
 if measurement['measurement_method'] not in ('FULL_FRAME_GPU_CLOCK','FULL_FRAME_END_TO_END'):return r('NEEDS_MEASUREMENT','pass-only or mixed clock measurement excluded')
 cohort={'device','driver','workload','resolution','shader','tools','clock_domain','thermal_regime','input','warmup_protocol','paired_run_order_protocol'}
 for n in ('baseline','candidate'):
  v=measurement[n]
  if type(v) is not dict or set(v)!={'cohort','full_frame_ns','compute_pass_ns'}:return r('NEEDS_MEASUREMENT','missing full-frame profile')
  if type(v['cohort']) is not dict or set(v['cohort'])!=cohort or any(type(x) is not str or not x for x in v['cohort'].values()):return r('NEEDS_MEASUREMENT','cohort missing')
  for key in ('full_frame_ns','compute_pass_ns'):
   a=v[key]
   if type(a) is not list or len(a)<3 or any(not finite(x) or not 0<x<2**63 for x in a):return r('NEEDS_MEASUREMENT','at least three finite positive trials required')
  if len(v['full_frame_ns'])!=len(v['compute_pass_ns']):return r('NEEDS_MEASUREMENT','trial counts differ')
 b,c=measurement['baseline'],measurement['candidate']
 if b['cohort']!=c['cohort'] or len(b['full_frame_ns'])!=len(c['full_frame_ns']):return r('NEEDS_MEASUREMENT','cohort or paired trial count mismatch')
 bm,cm=statistics.median(b['full_frame_ns']),statistics.median(c['full_frame_ns'])
 out['observed_declared_medians_ns']={'baseline_full_frame':bm,'candidate_full_frame':cm,'baseline_pass':statistics.median(b['compute_pass_ns']),'candidate_pass':statistics.median(c['compute_pass_ns'])}
 out['observed_worst_frame_ns']={'baseline':max(b['full_frame_ns']),'candidate':max(c['full_frame_ns'])}
 if max(c['full_frame_ns'])>max(b['full_frame_ns'])*(1+tail):return r('REVOKE_TO_BASELINE','observed worst frame exceeds explicit tolerance; no percentile inference')
 if cm>bm:return r('REVOKE_TO_BASELINE','candidate full frame regresses regardless of pass speed')
 if not policy['other_objectives_satisfied']:return r('NEEDS_MEASUREMENT','latency/power/quality/memory tradeoffs not resolved')
 if cm>=bm or (bm-cm)/bm<gain:return r('KEEP_BASELINE','no policy-qualified full-frame improvement')
 out['selected']='MULTI_QUEUE'
 return r('SELECT_MEASURED_CANDIDATE','declared paired full-frame median meets explicit policy; no general or statistically proven benefit')
