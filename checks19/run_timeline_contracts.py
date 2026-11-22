#!/usr/bin/env python3
"""Fixed ordinary timeline HOST controls with frozen prose/VUID source pairing."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import timeline_contract19 as rule,timeline_prose19 as prose,diagnostic_spec19 as spec
ROOT=Path(__file__).resolve().parents[1]
FILES=('checks19/run_timeline_contracts.py','tools/timeline_contract19.py','tools/timeline_prose19.py','tools/diagnostic_spec19.py')
def run(raw,vu):
 mapping=prose.extract(raw);corpus=spec.load_pinned(vu)
 ids=[f'VUID-VkSemaphoreSignalInfo-value-{v}' for v in ('03258','03259','03260')]+['VUID-vkDestroySemaphore-semaphore-05149']
 coordinates=[{k:e[k] for k in ('vuid','api_owner','condition_key','page')} for v in ids for e in corpus['entries'][v]]
 rows=[]
 def case(name,fn,args,status,details=None):
  r=fn(*args)
  if r['status']!=status or any(r.get(k)!=v for k,v in (details or {}).items()):raise ValueError('timeline control failed: '+name)
  rows.append(dict(name=name,input=args,result=r,expected=status,expected_details=details or {}))
 base=dict(ordinary_timeline_enabled=True,at_call_state_proven=True,pending_set_complete=True,host_calls_serialized=True,current=2,value=3,max_difference=10,pending_signals=[dict(value=5,happens_after_host_signal=True)],pending_waits=[1,4])
 case('host-before-pending-ordered',rule.host_signal,[base],'HOST_SIGNAL_CONDITIONS_WITHIN_SCOPE')
 for name,change,vuid in [('equal-current',{'value':2},'03258'),('equal-pending',{'value':5},'03259'),('wait-value-difference',{'pending_waits':[14]},'03260')]:case(name,rule.host_signal,[dict(base,**change)],'REJECTED',{'vuids':['VUID-VkSemaphoreSignalInfo-value-'+vuid]})
 case('numeric-order-not-execution-order',rule.host_signal,[dict(base,pending_signals=[dict(value=5,happens_after_host_signal=False)])],'ORDER_NOT_ESTABLISHED')
 for key in ('at_call_state_proven','pending_set_complete','host_calls_serialized'):case('unknown-'+key,rule.host_signal,[dict(base,**{key:False})],'UNKNOWN')
 case('uint64-overflow',rule.host_signal,[dict(base,value=2**64)],'UNKNOWN')
 case('wait-any-snapshot',rule.wait_condition,[[2,9],[3,8],'ANY'],'SNAPSHOT_PREDICATE_ONLY',{'satisfied':True,'predicts_vkresult':False})
 case('wait-all-snapshot',rule.wait_condition,[[2,9],[3,8],'ALL'],'SNAPSHOT_PREDICATE_ONLY',{'satisfied':False,'predicts_deadlock':False})
 case('wait-before-signal-not-deadlock-proof',rule.wait_condition,[[0],[10],'ALL'],'SNAPSHOT_PREDICATE_ONLY',{'satisfied':False,'predicts_deadlock':False})
 case('wait-success-not-retirement',rule.retirement,[dict(wait_satisfied=True,reference_set_complete=True,relevant_host_calls_completed=True,no_concurrent_host_access=True,all_submitted_references_completed=False)],'RETIREMENT_NOT_ESTABLISHED')
 case('all-reference-retirement-declared',rule.retirement,[dict(wait_satisfied=True,reference_set_complete=True,relevant_host_calls_completed=True,no_concurrent_host_access=True,all_submitted_references_completed=True)],'RETIREMENT_OBLIGATIONS_DECLARED')
 return dict(status='SOURCE_PAIRED_TIMELINE_HOST_CONTROLS',case_count=len(rows),cases=rows,prose=mapping,vuid_source=corpus['source'],vuid_coordinates=coordinates,implementation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},evidence_kind='CALLER_FACTS_HOST_CONTROLS_NOT_GPU',semantic_completion='UNKNOWN_NOT_INFERRED',release_status='BLOCKED')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('synchronization','validusage','out'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();r=run(a.synchronization.read_bytes(),a.validusage.read_bytes());a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':r['status'],'case_count':r['case_count']}))
if __name__=='__main__':main()
