#!/usr/bin/env python3
"""Source-paired partial color image-copy HOST controls, never whole-copy admission."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import image_copy_contract19 as rule,image_copy_prose19 as prose,diagnostic_spec19 as spec

def run(inputs,vu):
 mapping=prose.map_sources(inputs);corpus=spec.load_pinned(vu)
 ids=['VUID-vkCmdCopyImage-srcImage-01548','VUID-vkCmdCopyImage-srcImage-09247']+[f'VUID-vkCmdCopyImage-pRegions-{i:05}' for i in range(7278,7284)]+[f'VUID-vkCmdCopyImage-{side}Image-{i:05}' for side,ns in [('src',range(1728,1731)),('dst',range(1732,1735))] for i in ns]
 coordinates=[{k:e[k] for k in ('vuid','api_owner','condition_key','page')} for v in ids for e in corpus['entries'][v]]
 rows=[]
 def case(name,fn,args,expected,details=None):
  result=fn(*args)
  if result['status']!=expected or any(result.get(k)!=v for k,v in (details or {}).items()):raise ValueError('image-copy control failed: '+name)
  rows.append(dict(name=name,input=args,result=result,expected=expected,expected_details=details or {}))
 def fmt(block,size,compressed):return dict(color=True,single_plane=True,alpha_only_format=False,supported=True,compressed=compressed,block_extent=block,block_bytes=size)
 bc1=fmt([4,4,1],8,True);rg32=fmt([1,1,1],8,False);rgba=fmt([1,1,1],4,False);astc4=fmt([4,4,1],16,True);astc85=fmt([8,5,1],16,True)
 case('bc1-to-rg32',rule.format_admit,[bc1,rg32],'FORMAT_CONDITIONS_WITHIN_SCOPE')
 case('rg32-to-bc1',rule.format_admit,[rg32,bc1],'FORMAT_CONDITIONS_WITHIN_SCOPE')
 case('different-block-bytes',rule.format_admit,[bc1,rgba],'REJECTED',{'vuids':['VUID-vkCmdCopyImage-srcImage-01548']})
 case('both-compressed-different-extents',rule.format_admit,[astc4,astc85],'REJECTED',{'vuids':['VUID-vkCmdCopyImage-srcImage-09247']})
 case('alpha-only-outside-scope',rule.format_admit,[dict(rgba,alpha_only_format=True),rgba],'UNKNOWN')
 case('unknown-support',rule.format_admit,[dict(bc1,supported=False),rg32],'UNKNOWN')
 case('astc-small-mip-block-representation',rule.representation_blocks_equal,[[7,3,1],[1,1,1],[8,5,1],[1,1,1]],'BLOCK_COUNTS_EQUAL',{'unique_destination_extent_inferred':False})
 for width in (5,6,7,8):case('nonunique-edge-representation-'+str(width),rule.representation_blocks_equal,[[2,1,1],[width,1,1],[1,1,1],[4,1,1]],'BLOCK_COUNTS_EQUAL',{'unique_destination_extent_inferred':False})
 case('different-block-counts',rule.representation_blocks_equal,[[7,3,1],[2,1,1],[8,5,1],[1,1,1]],'BLOCK_COUNTS_DIFFER')
 for side in ('src','dst'):
  case(side+'-aligned-offset-partial-edge-extent',rule.image_region,[bc1,[4,0,0],[3,4,1],[7,4,1],side],'LOCAL_REGION_CONDITIONS_WITHIN_SCOPE',{'complete_copy_admission':False})
  case(side+'-edge-does-not-excuse-offset',rule.image_region,[bc1,[3,0,0],[4,4,1],[7,4,1],side],'REJECTED')
  case(side+'-unaligned-extent-not-at-edge',rule.image_region,[bc1,[4,0,0],[2,4,1],[7,4,1],side],'REJECTED')
 case('region-out-of-bounds',rule.image_region,[bc1,[4,0,0],[4,4,1],[7,4,1],'src'],'REJECTED',{'out_of_bounds_axes':[0]})
 return dict(status='SOURCE_PAIRED_PARTIAL_IMAGE_COPY_HOST_CONTROLS',case_count=len(rows),cases=rows,prose=mapping,vuid_source=corpus['source'],vuid_coordinates=coordinates,implementation_sha256={p:hashlib.sha256((Path(__file__).resolve().parents[1]/p).read_bytes()).hexdigest() for p in ('checks19/run_image_copy_contracts.py','tools/image_copy_contract19.py','tools/image_copy_prose19.py','tools/diagnostic_spec19.py')},evidence_kind='CALLER_METADATA_HOST_CONTROLS_NOT_GPU',whole_copy_admission='NOT_INFERRED',semantic_completion='UNKNOWN_NOT_INFERRED',release_status='BLOCKED')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('formats','copies','common','validusage','out'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();report=run({name:getattr(a,name).read_bytes() for name in prose.SOURCES},a.validusage.read_bytes());a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':report['status'],'case_count':report['case_count']}))
if __name__=='__main__':main()
