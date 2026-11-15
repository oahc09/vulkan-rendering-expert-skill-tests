#!/usr/bin/env python3
"""Reproduce two bounded descriptor card repairs; not exhaustive prose reasoning."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import semantic_inventory19 as s
OLD='b1a3f72e03c9a9621224746146e12a7d5beab81b'
PREFIX='references/03_api_manual/05_descriptor/'
# Exact reviewed repaired cohort, not a generic absence-of-bad-words detector.
REPAIRED_CARD_SHA256={'references/03_api_manual/05_descriptor/descriptor_update.md': 'a7e988f7d41b9af314e82a63a001f35925f69b53b530cada5d3a44cf8b1b6626', 'references/03_api_manual/05_descriptor/uniform_buffer_descriptor.md': '7ea12f21c89a07c78d962a0d43426a3f8caf36771b8162aa776a891c7468bb31', 'references/03_api_manual/05_descriptor/descriptor_indexing.md': 'b012062d106f7451c2174ed25afcca7173af7281336bf3b651d0b1806211d682'}
def sha(b):return hashlib.sha256(b).hexdigest()
def build(inv,skill):
 paths=[PREFIX+n for n in ('descriptor_update.md','uniform_buffer_descriptor.md','descriptor_indexing.md')]
 raw={p:(skill/p).read_bytes() for p in paths}
 for path,blob in raw.items():
  if sha(blob)!=REPAIRED_CARD_SHA256[path]:raise ValueError('card differs from exact reviewed repair cohort: '+path)
 old=subprocess.check_output(['git','-C',str(skill),'show',OLD+':'+paths[0]])
 oldline='资源销毁前是否已更新 descriptor 指向新资源或等待 GPU idle？'
 if oldline not in old.decode():raise ValueError('historical defect no longer matches')
 if oldline in raw[paths[0]].decode() or 'descriptorBindingUpdateAfterBind' in raw[paths[2]].decode() or 'maxDescriptorArrayLength' in raw[paths[2]].decode():raise ValueError('known card regression')
 unit=next(x for x in inv['units'].values() if x['vuid']=='VUID-vkDestroyBuffer-buffer-00922')
 scope=next(x for x in inv['scopes'].values() if x['name']=='VK_VERSION_1_0')
 scopefacts=dict(registry_scope_id=scope['scope_id'],registry_record_sha256=scope['record_sha256'],normative_api_version='1.4.309',registry_api_version='1.4.368',api_variant='Vulkan',platform='any',profile='ordinary-buffer-consumers',enabled_features=[])
 authority=paths[1]+'#delivery19-ordinary-ubo-lifetime'
 def claim(cid,path,blob,assertion,anchor):
  return dict(claim_id=cid,unit_id=unit['unit_id'],entry_sha256=unit['entry_sha256'],scope=scopefacts,predicate='descriptor-replacement-alone-permits-pending-buffer-destruction',assertion=assertion,card_anchor=path+'#'+anchor,card_sha256=sha(blob),authority_anchor=authority,authority_sha256=sha(raw[paths[1]]),version_mapping='MANUAL_309_CLAUSE_TO_368_SCOPE')
 before=[claim('historical-update-card',paths[0],old,True,'销毁阶段'),claim('ubo-contract',paths[1],raw[paths[1]],False,'delivery19-ordinary-ubo-lifetime')]
 # Use ASCII explicit stable anchor for historical manually selected line location.
 before[0]['card_anchor']=paths[0]+'#historical-destruction-checklist'
 after=[claim('repaired-update-card',paths[0],raw[paths[0]],False,'delivery19-descriptor-retirement-contract'),before[1]]
 conflict=s.audit(inv,before,[]);fixed=s.audit(inv,after,[])
 if not any(f['kind']=='SAME_SCOPE_OPPOSED_ASSERTIONS' for f in conflict['findings']) or fixed['findings']:raise ValueError('bounded conflict control failed')
 return {'status':'BOUNDED_SOURCE_CARD_AUDIT','sources':inv['sources'],'denominators':inv['denominators'],'historical_commit':OLD,'historical_line':oldline,'historical_line_number':next(i for i,line in enumerate(old.decode().splitlines(),1) if oldline in line),'historical_card_sha256':sha(old),'current_card_sha256':{p:sha(b) for p,b in raw.items()},'claim_interpretation':'Manually authored predicate interpretation of exact quoted source; not automatic prose extraction. Historical anchor is a labeled location, not a claimed extant Markdown heading.','before_claims':before,'after_claims':after,'before_findings':conflict['findings'],'after_findings':fixed['findings'],'review_declarations':0,'semantic_L1_L2_completion':'UNKNOWN_NOT_INFERRED','release_status':'BLOCKED'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--validusage',type=Path,required=True);p.add_argument('--registry',type=Path,required=True);p.add_argument('--skill',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 inv=s.load(a.validusage.read_bytes(),a.registry.read_bytes());report=build(inv,a.skill.resolve())
 a.out.mkdir(parents=True,exist_ok=False)
 for name,value in [('inventory',inv),('card-audit',report),('unreviewed-audit',s.audit(inv,[],[]))]:
  (a.out/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'denominators':inv['denominators'],'before_findings':report['before_findings'],'after_findings':report['after_findings']}))
if __name__=='__main__':main()
