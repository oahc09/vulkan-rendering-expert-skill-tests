#!/usr/bin/env python3
"""Source-paired HOST contract cases; not GPU execution or full API validation."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import normative_prose19 as prose, sync_contract19 as rule, diagnostic_spec19 as spec

def run(raw_prose,raw_vu):
 mapping=prose.extract(raw_prose);corpus=spec.load_pinned(raw_vu)
 vuids=['VUID-VkBufferMemoryBarrier-offset-01187','VUID-VkBufferMemoryBarrier-size-01188','VUID-VkBufferMemoryBarrier-size-01189']
 normative=[corpus['entries'][v] for v in vuids]
 cases=[]
 def case(name,fn,args,expected):
  result=fn(*args)
  if result['status']!=expected:raise ValueError('contract control failed: '+name)
  cases.append(dict(name=name,input=args,result=result,expected_status=expected))
 base={k:False for k in rule.BOOL_FIELDS};base.update(same_device=True,overlapping_memory=True,ordinary_accesses=True,same_queue=True,submission_order=True,first_access='WRITE',second_access='READ',execution_dependency_covers_both_operations=True,first_write_available=True,available_write_visible_to_second_access=True,availability_visibility_ordered_between_operations=True)
 case('raw-complete',rule.evaluate,[base],'CALLER_FACTS_SUFFICIENT')
 case('waw-complete',rule.evaluate,[dict(base,second_access='WRITE')],'CALLER_FACTS_SUFFICIENT')
 case('raw-only-order-and-fence',rule.evaluate,[dict(base,host_fence_completed=True,execution_dependency_covers_both_operations=False,first_write_available=False,available_write_visible_to_second_access=False,availability_visibility_ordered_between_operations=False)],'INSUFFICIENT_DEPENDENCY')
 case('raw-execution-only',rule.evaluate,[dict(base,first_write_available=False)],'INSUFFICIENT_DEPENDENCY')
 case('war-execution-only',rule.evaluate,[dict(base,first_access='READ',second_access='WRITE',first_write_available=False,available_write_visible_to_second_access=False,availability_visibility_ordered_between_operations=False)],'CALLER_FACTS_SUFFICIENT')
 case('raw-unknown-scope',rule.evaluate,[dict(base,execution_dependency_covers_both_operations=None)],'UNKNOWN')
 for name,args in [('unaligned-valid',(1,3,16)),('whole-valid',(1,'WHOLE_SIZE',16)),('zero-size',(1,0,16)),('overrun',(15,2,16)),('offset-at-end',(16,1,16))]:
  expected='RANGE_WITHIN_SCOPE' if name in ('unaligned-valid','whole-valid') else 'REJECTED'
  case(name,rule.buffer_range,list(args),expected)
 own=dict(sharing_mode='EXCLUSIVE',baseline_no_implicit_transfer_exception=True,same_device=True,same_instance=True,ordinary_resource=True,preserve_contents=True,families_valid=True,source_family=0,destination_family=0)
 case('same-family',rule.ownership,[own],'NO_FAMILY_TRANSFER_REQUIRED')
 case('cross-family',rule.ownership,[dict(own,destination_family=1)],'OWNERSHIP_TRANSFER_REQUIRED')
 case('concurrent-not-inferred',rule.ownership,[dict(own,sharing_mode='CONCURRENT')],'UNKNOWN')
 host=dict(ordinary_mapped_write=True,write_happens_before_submission=True,host_domain_available=True,host_coherent=False,required_flush_completed=True,host_memory_model_ordered=True,device_read_in_submission_scope=True,no_inflight_conflicting_access=True)
 ok='EXPLICIT_HOST_WRITE_BARRIER_NOT_REQUIRED_FOR_THIS_DEPENDENCY'
 case('flushed-prior-host-write',rule.host_write_submission,[host],ok)
 case('coherent-prior-host-write',rule.host_write_submission,[dict(host,host_coherent=True,required_flush_completed=False)],ok)
 for field in ('required_flush_completed','write_happens_before_submission','host_memory_model_ordered','no_inflight_conflicting_access'):
  case('host-missing-'+field,rule.host_write_submission,[dict(host,**{field:False})],'UNKNOWN')
 return dict(implementation_sha256={name:hashlib.sha256((Path(__file__).resolve().parents[1]/name).read_bytes()).hexdigest() for name in ('checks19/run_sync_contracts.py','tools/sync_contract19.py','tools/normative_prose19.py','tools/diagnostic_spec19.py')},status='SOURCE_PAIRED_HOST_CONTRACT_CONTROLS',prose=mapping,range_normative_source=corpus['source'],range_normative_coordinates=[{k:e[k] for k in ('vuid','api_owner','condition_key','page')} for es in normative for e in es],cases=cases,case_count=len(cases),evidence_kind='DECLARED_FACTS_HOST_CONTROLS_NOT_GPU',semantic_completion='UNKNOWN_NOT_INFERRED',release_status='BLOCKED')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prose',type=Path,required=True);p.add_argument('--validusage',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 result=run(a.prose.read_bytes(),a.validusage.read_bytes());a.out.mkdir(parents=True,exist_ok=False)
 (a.out/'report.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'case_count':result['case_count']}))
if __name__=='__main__':main()
