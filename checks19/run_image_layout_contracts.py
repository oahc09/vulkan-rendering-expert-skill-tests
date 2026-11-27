#!/usr/bin/env python3
"""Fixed source-paired HOST image-layout controls, not device execution."""
import argparse,copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import image_layout_contract19 as rule,image_layout_prose19 as prose,diagnostic_spec19 as spec
ROOT=Path(__file__).resolve().parents[1]
IMPLEMENTATIONS=('checks19/run_image_layout_contracts.py','tools/image_layout_contract19.py','tools/image_layout_prose19.py','tools/diagnostic_spec19.py')
def run(raw,vu):
 mapping=prose.extract(raw);corpus=spec.load_pinned(vu)
 ids=[f'VUID-{owner}-{field}-{num}' for owner in ('VkImageMemoryBarrier','VkImageMemoryBarrier2') for field,num in [('oldLayout','01197'),('newLayout','01198')]]
 coordinates=[{k:e[k] for k in ('vuid','api_owner','condition_key','page')} for v in ids for e in corpus['entries'][v]]
 rows=[]
 state=[dict(mip=0,layer=0,layout='GENERAL',defined=True),dict(mip=1,layer=0,layout='TRANSFER_SRC_OPTIMAL',defined=False)]
 base=dict(api='barrier2',sync2_enabled=True,source_family=0xffffffff,destination_family=0xffffffff,old_layout='GENERAL',new_layout='TRANSFER_DST_OPTIMAL',subresources=[[0,0]])
 facts={k:True for k in rule.FACT_KEYS}
 def case(name,b,status,changes=None,details=None):
  f=dict(facts,**(changes or {}));r=rule.evaluate(state,b,f)
  if r['status']!=status or any(r.get(k)!=v for k,v in (details or {}).items()):raise ValueError('image-layout control failed: '+name)
  if 'state_after' in r and r['state_after'][1]!=state[1]:raise ValueError('untouched subresource changed')
  rows.append(dict(name=name,input=dict(state=copy.deepcopy(state),barrier=b,facts=f),result=r,expected=status,expected_details=details or {}))
 case('selected-cell-transition',base,'MODELED_TRANSITION')
 for api in ('legacy','barrier2'):
  for layout in ('UNDEFINED','TRANSFER_DST_OPTIMAL'):
   case(api+'-sync2-ignored-'+layout,dict(base,api=api,old_layout=layout,new_layout=layout),'MODELED_LAYOUTS_IGNORED',details={'state_after':state,'content_preservation_not_guaranteed':False})
 case('legacy-no-sync2-equal-mismatch',dict(base,api='legacy',sync2_enabled=False,old_layout='TRANSFER_DST_OPTIMAL',new_layout='TRANSFER_DST_OPTIMAL'),'REJECTED',details={'vuids':['VUID-VkImageMemoryBarrier-oldLayout-01197']})
 case('legacy-no-sync2-equal-current',dict(base,api='legacy',sync2_enabled=False,new_layout='GENERAL'),'MODELED_TRANSITION')
 case('different-families-not-ignored',dict(base,old_layout='UNDEFINED',new_layout='UNDEFINED',destination_family=0),'UNKNOWN')
 case('discard-definedness-not-clearing',dict(base,old_layout='UNDEFINED'),'MODELED_TRANSITION',details={'content_preservation_not_guaranteed':True,'state_after':[dict(state[0],layout='TRANSFER_DST_OPTIMAL',defined=False),state[1]]})
 for key in ('prior_accesses_ordered_before_transition','prior_writes_available','next_accesses_ordered_after_transition','transition_writes_visible_to_next_access'):
  case('discard-still-requires-'+key,dict(base,old_layout='UNDEFINED'),'INSUFFICIENT_DEPENDENCY',{key:False})
 case('ignored-layout-not-memory-proof',dict(base,new_layout='GENERAL'),'INSUFFICIENT_DEPENDENCY',{'ignored_barrier_dependencies_sufficient':False})
 case('mixed-cell-oldlayout-mismatch',dict(base,subresources=[[0,0],[1,0]]),'REJECTED',details={'vuids':['VUID-VkImageMemoryBarrier2-oldLayout-01197']})
 case('invalid-transition-new',dict(base,new_layout='UNDEFINED'),'REJECTED',details={'vuids':['VUID-VkImageMemoryBarrier2-newLayout-01198']})
 case('missing-caller-proof',base,'UNKNOWN',{'prior_writes_available':None})
 return dict(status='SOURCE_PAIRED_IMAGE_LAYOUT_HOST_CONTROLS',case_count=len(rows),cases=rows,prose=mapping,vuid_source=corpus['source'],vuid_coordinates=coordinates,implementation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in IMPLEMENTATIONS},evidence_kind='CALLER_FACTS_HOST_CONTROLS_NOT_GPU',semantic_completion='UNKNOWN_NOT_INFERRED',release_status='BLOCKED')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('synchronization','validusage','out'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();report=run(a.synchronization.read_bytes(),a.validusage.read_bytes());a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':report['status'],'case_count':report['case_count']}))
if __name__=='__main__':main()
