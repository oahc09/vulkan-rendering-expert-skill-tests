#!/usr/bin/env python3
"""Fixed consecutive-binding and write/copy ordering HOST controls."""
import argparse,copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import descriptor_update_contract19 as rule,descriptor_update_prose19 as prose,diagnostic_spec19 as spec
ROOT=Path(__file__).resolve().parents[1]
FILES=('checks19/run_descriptor_update_contracts.py','tools/descriptor_update_contract19.py','tools/descriptor_update_prose19.py','tools/diagnostic_spec19.py')
def run(raw,vu):
 mapping=prose.extract(raw);corpus=spec.load_pinned(vu)
 ids=['VUID-VkWriteDescriptorSet-descriptorCount-00317','VUID-VkWriteDescriptorSet-descriptorCount-00318','VUID-VkWriteDescriptorSet-descriptorType-00319','VUID-VkWriteDescriptorSet-dstArrayElement-00321','VUID-VkCopyDescriptorSet-dstBinding-02632','VUID-VkCopyDescriptorSet-srcSet-00349']
 coordinates=[dict(e) for v in ids for e in corpus['entries'][v]]
 rows=[]
 def case(name,fn,args,status,details=None):
  r=fn(*args)
  if r['status']!=status or any(r.get(k)!=v for k,v in (details or {}).items()):raise ValueError('descriptor-update control failed: '+name)
  rows.append(dict(name=name,input=args,result=r,expected=status,expected_details=details or {}));return r
 layout=[dict(binding=i,count=0 if i==1 else 2,type='UNIFORM_BUFFER',stages=1,flags=0,immutable_reference_signature=None) for i in range(3)]
 case('spill-skips-zero',rule.spill,[layout,0,1,3],'ROUTE_WITHIN_SCOPE',{'coordinates':[[0,1],[2,0],[2,1]]})
 for key,value in [('type','STORAGE_BUFFER'),('stages',16),('flags',1)]:
  changed=copy.deepcopy(layout);changed[2][key]=value
  case('consecutive-'+key+'-mismatch',rule.spill,[changed,0,1,2],'REJECTED')
 samplers=[dict(b,type='SAMPLER',immutable_reference_signature='a'*64) for b in layout]
 case('immutable-references-match',rule.spill,[samplers,0,1,2],'ROUTE_WITHIN_SCOPE')
 changed=copy.deepcopy(samplers);changed[2]['immutable_reference_signature']='b'*64
 case('immutable-references-differ',rule.spill,[changed,0,1,2],'REJECTED')
 case('insufficient-capacity',rule.spill,[layout,0,1,4],'REJECTED')
 case('start-at-count-unknown',rule.spill,[layout,0,2,1],'UNKNOWN')
 token=lambda name,live=True:dict(reference=name,defined=True,resource_live=live)
 sets={n:dict(layout=copy.deepcopy(layout),values=[[token('old'),token('old')],[],[token('old'),token('old')]]) for n in ('A','B','C')}
 writes=[dict(set='A',binding=0,element=0,type='UNIFORM_BUFFER',values=[token(n)]) for n in ('first','last')]
 cp=lambda s,d:dict(src_set=s,src_binding=0,src_element=0,dst_set=d,dst_binding=0,dst_element=0,count=1)
 r=case('all-writes-before-copies-in-order',rule.apply,[sets,writes,[cp('A','B'),cp('B','C')],True],'MODELED_UPDATES')
 if r['state_after']['C']['values'][0][0]['reference']!='last' or [e['operation'] for e in r['events']]!=['WRITE','WRITE','COPY','COPY']:raise ValueError('write/copy ordering oracle failed')
 case('cross-binding-same-set-overlap',rule.apply,[sets,[],[dict(cp('A','A'),src_element=1,dst_binding=2,count=2)],True],'REJECTED',{'vuids':['VUID-VkCopyDescriptorSet-srcSet-00349']})
 gone=copy.deepcopy(sets);gone['A']['values'][0][0]=token('destroyed',False)
 r=case('destroyed-reference-copy-is-undefined',rule.apply,[gone,[],[cp('A','B')],True],'MODELED_UPDATES',{'resource_use_performed':False})
 if r['state_after']['B']['values'][0][0]['defined'] is not False:raise ValueError('undefined propagation failed')
 return dict(status='SOURCE_PAIRED_DESCRIPTOR_UPDATE_HOST_CONTROLS',case_count=len(rows),cases=rows,prose=mapping,vuid_source=corpus['source'],vuid_coordinates=coordinates,version_difference='30900317 combines type/stage; 368 separates stage10776 and flags10777. Immutable-reference proof uses368 prose; not claimed equivalent to30900318 presence-only wording.',implementation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},evidence_kind='TOKEN_MODEL_HOST_CONTROLS_NOT_GPU',semantic_completion='UNKNOWN_NOT_INFERRED',release_status='BLOCKED')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('descriptors','validusage','out'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();r=run(a.descriptors.read_bytes(),a.validusage.read_bytes());a.out.mkdir(parents=True,exist_ok=False);(a.out/'report.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':r['status'],'case_count':r['case_count']}))
if __name__=='__main__':main()
