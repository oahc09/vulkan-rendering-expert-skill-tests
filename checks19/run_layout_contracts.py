#!/usr/bin/env python3
"""Fixed-source layout/push HOST controls; no GPU object creation or execution."""
import argparse,copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import layout_prose19 as prose,layout_contract19 as rule,diagnostic_spec19 as spec

def run(chapter,common,validusage):
 mapping=prose.map_sources(chapter,common);corpus=spec.load_pinned(validusage)
 vuids=['VUID-VkPipelineLayoutCreateInfo-pPushConstantRanges-00292','VUID-vkCmdPushConstants-offset-01795','VUID-vkCmdPushConstants-offset-01796']
 vuids += ['VUID-VkPushConstantRange-'+x for x in ('offset-00294','offset-00295','size-00296','size-00297','size-00298')]
 coordinates=[{k:e[k] for k in ('vuid','api_owner','condition_key','page')} for v in vuids for e in corpus['entries'][v]]
 out=[]
 def case(name,fn,args,status,details=None):
  result=fn(*args)
  if result['status']!=status or any(result.get(k)!=v for k,v in (details or {}).items()):raise ValueError('layout control failed: '+name)
  out.append(dict(name=name,input=args,result=result,expected_status=status,expected_details=details or {}))
 ranges=[dict(offset=0,size=16,stages=1),dict(offset=0,size=16,stages=16)]
 a=dict(scope='ORDINARY_COMPLETE_LAYOUTS',set_definitions=['a'*64,'b'*64,'c'*64],push_ranges=ranges,max_push_constants=128,independent_sets=False)
 b=copy.deepcopy(a)
 case('different-declarations-identical-definitions',rule.compatible,[a,b,1],'COMPATIBLE')
 changed=copy.deepcopy(a);changed['set_definitions'][0]='d'*64
 case('set0-diff-even-if-set1-same',rule.compatible,[a,changed,1],'INCOMPATIBLE')
 case('push-compatible-despite-descriptor-difference',rule.push_compatible,[a,changed],'COMPATIBLE')
 pushchanged=copy.deepcopy(a);pushchanged['push_ranges'][0]['size']=12
 case('push-range-diff',rule.compatible,[a,pushchanged,1],'INCOMPATIBLE')
 case('independent-flag-diff',rule.compatible,[a,dict(a,independent_sets=True),1],'INCOMPATIBLE')
 case('unknown-special-layout',rule.compatible,[a,dict(a,scope='PARTIAL_LIBRARY'),1],'UNKNOWN')
 case('different-stage-byte-overlap-created',rule.push_ranges,[ranges,128],'RANGES_WITHIN_SCOPE')
 case('same-stage-disjoint-rejected',rule.push_ranges,[[dict(offset=0,size=4,stages=1),dict(offset=16,size=4,stages=1)],128],'REJECTED')
 case('unaligned-push-range-rejected',rule.push_ranges,[[dict(offset=1,size=4,stages=1)],128],'REJECTED')
 case('bound-overflow-rejected',rule.push_ranges,[[dict(offset=124,size=8,stages=1)],128],'REJECTED')
 case('overlap-update-both-stages',rule.push_update,[ranges,17,0,16,128],'UPDATE_WITHIN_SCOPE')
 case('overlap-update-only-vertex',rule.push_update,[ranges,1,0,16,128],'REJECTED',{'vuids':['VUID-vkCmdPushConstants-offset-01796']})
 case('update-uncovered-by-layout',rule.push_update,[ranges,17,16,4,128],'REJECTED',{'vuids':['VUID-vkCmdPushConstants-offset-01795']})
 case('update-unsupported-stage-unknown',rule.push_update,[ranges,256,0,16,128],'UNKNOWN')
 previous={0:a,1:a,2:a}
 case('bind-compatible-keeps-other-sets',rule.bind_disturbance,[previous,b,1],'DISTURBANCE_EVALUATED',{'disturbed':[],'requires_prebound_pipeline':False})
 case('bind-incompatible-prefix-disturbs-both-directions',rule.bind_disturbance,[previous,changed,1],'DISTURBANCE_EVALUATED',{'disturbed':[0,2]})
 case('pipeline-access-compatible',rule.pipeline_access,[a,b,1,True],'LAYOUT_ACCESS_PERMITTED',{'bindings_mutated':False})
 case('disturbed-binding-no-access',rule.pipeline_access,[a,b,1,False],'LAYOUT_ACCESS_NOT_ESTABLISHED',{'bindings_mutated':False})
 return dict(status='SOURCE_PAIRED_LAYOUT_HOST_CONTROLS',case_count=len(out),cases=out,prose=mapping,vuid_source=corpus['source'],vuid_coordinates=coordinates,implementation_sha256={p:hashlib.sha256((Path(__file__).resolve().parents[1]/p).read_bytes()).hexdigest() for p in ('checks19/run_layout_contracts.py','tools/layout_prose19.py','tools/layout_contract19.py','tools/diagnostic_spec19.py')},evidence_kind='CALLER_DECLARED_DEFINITION_HOST_CONTROLS_NOT_GPU',semantic_completion='UNKNOWN_NOT_INFERRED',release_status='BLOCKED')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for x in ('chapter','common','validusage','out'):p.add_argument('--'+x,type=Path,required=True)
 a=p.parse_args();report=run(a.chapter.read_bytes(),a.common.read_bytes(),a.validusage.read_bytes());a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':report['status'],'case_count':report['case_count']}))
if __name__=='__main__':main()
