#!/usr/bin/env python3
"""User-facing bounded compute scheduling decision over explicit JSON evidence."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import compute_schedule19 as rule,compute_schedule_prose19 as prose
ROOT=Path(__file__).resolve().parents[1]
def load(raw):
 def pairs(items):
  d={}
  for k,v in items:
   if k in d:raise ValueError('duplicate JSON key')
   d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def bind_capability(request,raw,expected_sha):
 if type(expected_sha) is not str or len(expected_sha)!=64 or hashlib.sha256(raw).hexdigest()!=expected_sha:raise ValueError('capability digest mismatch')
 cap=load(raw)
 if type(cap) is not dict or cap.get('schema')!=1 or cap.get('status')!='QUEUE_CREATION_OBSERVED' or cap.get('gpu_work_submitted') is not False or cap.get('get_queue_nonnull') is not True:raise ValueError('unsupported capability observation')
 if cap.get('enabled_features')!=[] or cap.get('enabled_extensions')!=[] or cap.get('physical_device_count')!=1:raise ValueError('only single-device core probe supported')
 f=request['facts']
 if f['families']!=cap['families'] or f['created']!=cap['created'] or f['requirements']!=[]:raise ValueError('request capability/created facts differ from observation')
 # Selection remains the caller request, so a nonexistent second queue is rejected.
 return dict(sha256=expected_sha,device=cap['device'],families=cap['families'],created=cap['created'],gpu_work_submitted=False,scope='Observed capability/creation only; no timing or dependency evidence; caller-supplied digest is not authentication')
def run(request,devraw,syncraw,resources=None,features=None,fundamentals=None):
 if type(request) is not dict or set(request)!={'facts','measurement','policy'}:raise ValueError('exact request schema')
 sources=[prose.extract(name,raw) for name,raw in [('devsandqueues',devraw),('synchronization',syncraw),('resources',resources),('features',features),('fundamentals',fundamentals)]]
 return dict(status='BOUNDED_CALLER_EVIDENCE_DECISION',decision=rule.decide(**request),sources=sources,
 implementation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('tools/compute_schedule19.py','tools/compute_schedule_prose19.py','checks19/decide_compute_schedule.py')},release_status='BLOCKED',actual_async_benchmark=False)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('request','devsandqueues','synchronization','resources','features','fundamentals','out'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--capability',type=Path);p.add_argument('--expected-capability-sha256')
 a=p.parse_args();data=a.request.read_bytes();request=load(data)
 if bool(a.capability)!=bool(a.expected_capability_sha256):raise ValueError('capability and expected digest required together')
 cap=bind_capability(request,a.capability.read_bytes(),a.expected_capability_sha256) if a.capability else None
 r=run(request,a.devsandqueues.read_bytes(),a.synchronization.read_bytes(),a.resources.read_bytes(),a.features.read_bytes(),a.fundamentals.read_bytes());r['request_sha256']=hashlib.sha256(data).hexdigest();r['actual_capability_observation']=cap
 a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
 d=r['decision'];(a.out/'SUMMARY.md').write_text('# Compute scheduling / 计算调度\n\n'+d['status']+'\n\n'+d['reason']+'\n\n仅调用者事实合同，不代表真实异步 GPU 性能测试。Multiple queues do not guarantee overlap.\n')
 print(json.dumps({'status':d['status'],'selected':d['selected']}))
if __name__=='__main__':main()
