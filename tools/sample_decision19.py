"""Bounded sample-count decision, consumed only after independent actual A/B verification.
Allocation requests are NOT residency; endpoint equality is NOT edge quality/performance.
"""
def decide(baseline,candidate,policy):
 if not isinstance(policy,dict) or set(policy)!={'required_samples','requested_bytes_budget','require_edge_quality','require_performance_gain'}:raise ValueError('exact policy required')
 if type(policy['required_samples']) is not int or policy['required_samples'] not in (1,4):raise ValueError('sample requirement')
 if type(policy['requested_bytes_budget']) is not int or not 0<=policy['requested_bytes_budget']<=2**63-1:raise ValueError('request budget')
 if any(type(policy[k]) is not bool for k in ('require_edge_quality','require_performance_gain')):raise ValueError('boolean measurement requirements')
 for v,n in ((baseline,1),(candidate,4)):
  if not isinstance(v,dict) or set(v)!={'samples','requested_bytes','endpoint_error'}:raise ValueError('verified facts required')
  if any(type(v[k]) is not int for k in v) or v['samples']!=n or not 0<v['requested_bytes']<=2**63-1 or v['endpoint_error']<0:raise ValueError('invalid facts')
 budget=policy['requested_bytes_budget'];required=policy['required_samples']
 def rejects(v):
  return [reason for condition,reason in ((v['endpoint_error']!=0,'endpoint-output-mismatch'),(v['requested_bytes']>budget,'allocation-request-budget'),(v['samples']<required,'required-sample-count')) if condition]
 candidates=[{'samples':v['samples'],'requested_bytes':v['requested_bytes'],'rejections':rejects(v)} for v in (baseline,candidate)]
 eligible=[v['samples'] for v in candidates if not v['rejections']]
 unknown=[k for k in ('require_edge_quality','require_performance_gain') if policy[k]]
 result={'rule_id':'depth-endpoint-samples-v1','version_scope':'fixed CPU ICD depth-occlusion-endpoint scene; source/tool pair checked by caller','inputs':policy.copy(),'alternatives':candidates,'measured':{'endpoint_pixels':16,'requested_bytes_only':True},'unmeasured':['GPU/full-frame performance','thermal/power','residency/peak VRAM','edge antialiasing quality','present/input latency'],'selected_samples':None,'fallback_samples':None,'revisit_conditions':['source/device/driver/tool/scene change','budget or sample requirement change','new independently comparable quality/performance evidence'],'tests':'tests/test_sample_decision19.py'}
 if not eligible:result.update(status='NO_ADMISSIBLE_PATH',reason='all candidates violate explicit bounded requirements')
 elif unknown:result.update(status='NEEDS_MEASUREMENT',reason='requested objectives have no evidence',unknown_objectives=unknown,fallback_samples=1 if 1 in eligible else None)
 elif 1 in eligible:result.update(status='KEEP_BASELINE',selected_samples=1,fallback_samples=1,reason='baseline meets bounded contract; no measured reason to upgrade')
 else:result.update(status='SELECT_REQUIRED_SAMPLE_COUNT' if required==4 else 'SELECT_ONLY_ADMISSIBLE_PATH',selected_samples=4,reason='only 4x meets the explicit bounded contract; no performance/quality superiority claim')
 return result
