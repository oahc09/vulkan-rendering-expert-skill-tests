#!/usr/bin/env python3
"""Fixed ordinary memory-binding HOST controls with explicit309/368 size split."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import memory_binding_contract19 as rule,memory_binding_prose19 as prose,diagnostic_spec19 as spec
ROOT=Path(__file__).resolve().parents[1]
FILES=('checks19/run_memory_binding_contracts.py','tools/memory_binding_contract19.py','tools/memory_binding_prose19.py','tools/diagnostic_spec19.py')
def run(inputs,vu):
 mapping=prose.extract(inputs);corpus=spec.load_pinned(vu);ids=[]
 for kind,nums in rule.IDS.items():
  owner='vkBind'+kind.title()+'Memory'
  for key,n in nums.items():
   field={'offset':'memoryOffset','type':'memory','alignment':'memoryOffset','size':'size','bound':kind,'required':kind,'dedicated':'memory'}[key]
   ids.append(f'VUID-{owner}-{field}-{n}')
 ids+=['VUID-vkFreeMemory-memory-00677','VUID-VkMemoryDedicatedAllocateInfo-image-02964','VUID-VkMemoryDedicatedAllocateInfo-buffer-02965']
 coords=[dict(e) for v in ids for e in corpus['entries'][v]];rows=[]
 def case(name,fn,args,status):
  r=fn(*args)
  if r['status']!=status:raise ValueError('memory-binding control failed: '+name)
  rows.append(dict(name=name,input=args,result=r,expected=status))
 base=dict(kind='buffer',resource_id='A',ordinary_scope_proven=True,allocation_creation_valid=True,same_device=True,requirements_size=256,requirements_alignment=64,memory_type_bits=2,memory_type_index=1,allocation_size=1024,offset=64,already_bound=False,requires_dedicated=False,prefers_dedicated=False,dedicated=None)
 for kind in ('buffer','image'):
  f=dict(base,kind=kind)
  case(kind+'-valid-requirements',rule.bind,[f],'BIND_CONDITIONS_WITHIN_SCOPE')
  for key,value in [('offset',1),('memory_type_index',0),('requirements_size',1024),('already_bound',True),('requires_dedicated',True)]:case(kind+'-'+key,rule.bind,[dict(f,**{key:value})],'REJECTED')
  case(kind+'-prefers-not-required',rule.bind,[dict(f,prefers_dedicated=True)],'BIND_CONDITIONS_WITHIN_SCOPE')
  case(kind+'-dedicated-correct',rule.bind,[dict(f,offset=0,allocation_size=256,requires_dedicated=True,dedicated=dict(kind=kind,resource_id='A'))],'BIND_CONDITIONS_WITHIN_SCOPE')
  for version,status in [('1.4.309','REJECTED'),('1.4.368','DEDICATED_SIZE_CONDITION_SATISFIED')]:case(kind+'-oversized-dedicated-'+version,rule.dedicated_allocation_size,[kind,512,256,version,True],status)
 a=dict(allocation_id='M',offset=0,requirements_size=64,linear=True);b=dict(allocation_id='M',offset=128,requirements_size=64,linear=False)
 case('disjoint-same-page-aliasing',rule.granularity,[a,b,256,True],'ALIASING_RISK_NOT_BIND_VUID')
 case('page-boundary-not-min-distance',rule.granularity,[dict(a,requirements_size=255),dict(b,offset=256),256,True],'MIXED_PAGE_SEPARATION_SATISFIED')
 case('not-simultaneous',rule.granularity,[a,b,256,False],'NO_MIXED_SIMULTANEOUS_PAGE_CONDITION')
 f=dict(bound_object_count=2,all_submitted_uses_retired=True,host_accesses_completed=True,no_future_bound_resource_use=True,reference_inventory_complete=True)
 case('bound-objects-do-not-forbid-free',rule.free_obligations,[f],'FREE_LIFETIME_OBLIGATIONS_DECLARED')
 case('pending-uses-forbid-free',rule.free_obligations,[dict(f,all_submitted_uses_retired=False)],'REJECTED')
 case('future-bound-use-not-proven',rule.free_obligations,[dict(f,no_future_bound_resource_use=False)],'LIFETIME_OBLIGATIONS_NOT_ESTABLISHED')
 return dict(status='SOURCE_PAIRED_MEMORY_BINDING_HOST_CONTROLS',case_count=len(rows),cases=rows,prose=mapping,vuid_source=corpus['source'],vuid_coordinates=coords,implementation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},evidence_kind='CALLER_FACTS_HOST_CONTROLS_NOT_GPU',semantic_completion='UNKNOWN_NOT_INFERRED',release_status='BLOCKED')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('resources','memory','validusage','out'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();r=run({n:getattr(a,n).read_bytes() for n in prose.HASHES},a.validusage.read_bytes());a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':r['status'],'case_count':r['case_count']}))
if __name__=='__main__':main()
