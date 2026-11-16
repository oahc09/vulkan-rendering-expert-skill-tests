"""Fail-closed Vulkan SC1.0 core migration audit, not an SC conformance tool."""
import argparse,hashlib,json,re,subprocess,xml.etree.ElementTree as E
from pathlib import Path
from core17_registry_inventory import SOURCE_SHA256

def extract(raw):
 if len(raw)>20_000_000 or b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:raise ValueError('XML budget/entity refused')
 if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:raise ValueError('wrong frozen source')
 root=E.fromstring(raw);features=[f for f in root.findall('feature') if f.get('name')=='VKSC_VERSION_1_0']
 if len(features)!=1 or features[0].get('api')!='vulkansc':raise ValueError('SC feature missing/ambiguous')
 f=features[0];records=[]
 for bi,block in enumerate(f):
  if block.tag not in ('require','remove'):continue
  for ei,item in enumerate(block):
   if item.tag not in ('command','type','enum','feature'):continue
   records.append(dict(operation=block.tag,kind=item.tag,name=item.get('name'),struct=item.get('struct'),block_attributes=dict(block.attrib),item_attributes=dict(item.attrib),source_path=f"/registry/feature[@name='VKSC_VERSION_1_0']/*[{bi+1}]/*[{ei+1}]"))
 return dict(source_sha256=SOURCE_SHA256,variant='vulkansc',core='1.0',base_dependency=f.get('depends'),records=records,limitations=['core delta only, not complete inherited symbol resolution','extension/platform conditions preserved but not evaluated','not full semantic review or certification'])

def assess(audit,symbols):
 # Internal API: records must come from extract() or an integrity-checked snapshot.
 if audit.get('source_sha256')!=SOURCE_SHA256 or audit.get('variant')!='vulkansc':raise ValueError('wrong audit provenance')
 if not isinstance(symbols,list) or any(not isinstance(s,str) or not re.fullmatch(r'vk[A-Za-z0-9_]+',s) for s in symbols):raise ValueError('Vulkan command symbol list required')
 removed={r['name']:r for r in audit['records'] if r['operation']=='remove' and r['kind']=='command'}
 hits=[dict(symbol=s,source_path=removed[s]['source_path'],conditions=removed[s]['block_attributes']) for s in sorted(set(symbols)&removed.keys())]
 return dict(status='REQUIRES_SC_REDESIGN' if hits else 'UNVERIFIED',core_removed_references=hits,observed_symbols=sorted(set(symbols)),limitations=['symbol presence cannot prove execution','dynamic function pointers/inlined dispatch may be absent','no removed reference does not imply API support or correct lifetime','no SC device execution, extension overrides require separate review'])

def nm_symbols(raw):
 return sorted({s.decode() for s in re.findall(rb'\b(vk[A-Za-z0-9_]+)(?:@[^\s]+)?\s*$',raw,re.M)})

def main():
 p=argparse.ArgumentParser();p.add_argument('--xml',type=Path,required=True);p.add_argument('--binary',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 with a.xml.open('rb') as f:raw=f.read(20_000_001)
 result=extract(raw)
 if a.binary:
  raw=subprocess.check_output(['nm','-u',str(a.binary)],timeout=20)
  symbols=nm_symbols(raw)
  result['binary_audit']=assess(result,symbols);result['binary_sha256']=hashlib.sha256(a.binary.read_bytes()).hexdigest()
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
