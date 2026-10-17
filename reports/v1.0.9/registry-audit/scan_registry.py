#!/usr/bin/env python3
"""Read-only API-manual lexical audit. Not a semantic validator. Python standard library only."""
import argparse, collections, datetime, hashlib, json, pathlib, re, xml.etree.ElementTree as ET
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=pathlib.Path, required=True, help='Exact Skill repository root containing references/03_api_manual (not its parent)')
p.add_argument('--output', type=pathlib.Path, default=pathlib.Path('registry-scan-results.json'))
p.add_argument('--registry-dir', type=pathlib.Path, required=True, help='Directory containing official validusage.json and vulkan_core.h')
p.add_argument('--vk-xml', type=pathlib.Path, required=True, help='Official vk.xml path')
a=p.parse_args(); base=a.root.resolve(); evidence=a.registry_dir; xml_path=a.vk_xml
manual=base/'references/03_api_manual'
if not manual.is_dir():
 p.error(f'--root must be the exact Skill repository root: missing {manual}')
files=sorted(manual.rglob('*.md'))
if not files:
 p.error(f'No API manual Markdown files found under {manual}; refusing an empty audit')

r=ET.parse(xml_path).getroot()
known={x.get('name') for x in r.iter() if x.get('name')}|{x.text for x in r.iter('name')}
core=(evidence/'vulkan_core.h').read_text();known.update(re.findall(r'\b(?:VK_\w+|Vk[A-Z]\w*|vk[A-Z]\w*)\b',core))
types={x.get('name',x.findtext('name')):x for x in r.findall('./types/type')}
v=json.loads((evidence/'validusage.json').read_text()); vuids={};
def walk(x):
 if isinstance(x,dict):
  if 'vuid' in x:vuids[x['vuid']]=x.get('text','')
  for z in x.values():walk(z)
 elif isinstance(x,list):
  for z in x:walk(z)
walk(v)
unknown=collections.defaultdict(list); members=[]; vunknown=collections.defaultdict(list); vmatches=collections.defaultdict(list); hashes={}; counts=collections.Counter()
for f in files:
 data=f.read_bytes(); path=str(f.relative_to(base)); hashes[path]=hashlib.sha256(data).hexdigest(); counts['files']+=1
 for n,line in enumerate(data.decode().splitlines(),1):
  loc={'path':path,'line':n,'context':line}
  for s in set(re.findall(r'\b(?:vk[A-Z][A-Za-z0-9_]*|Vk[A-Z][A-Za-z0-9_]*|VK_[A-Za-z0-9_]+)\b',line)):
   counts['symbol_occurrences']+=1
   if s not in known:unknown[s].append(loc)
  for typ,member in re.findall(r'\b(Vk[A-Z]\w*)(?:\.|::)(\w+)',line):
   if member in ('html','md'): continue
   t=types.get(typ)
   if t is None:continue
   while t.get('alias'):t=types[t.get('alias')]
   counts['qualified_member_occurrences']+=1
   if member not in {m.findtext('name') for m in t.findall('member')}:members.append(dict(loc,symbol=typ+'.'+member,category=t.get('category')))
  for s in set(re.findall(r'\bVUID-[A-Za-z0-9_-]+',line)):
   counts['vuid_occurrences']+=1
   if s not in vuids:
    vunknown[s].append(dict(loc,kind='concrete_numeric' if re.search(r'-\d+$',s) else 'partial_or_placeholder',same_numeric_suffix=[{'vuid':k,'text':txt} for k,txt in vuids.items() if re.search(r'-\d+$',s) and k.endswith(s[-6:])]))
   else:vmatches[s].append(dict(loc,registry_text=vuids[s]))
result={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_path_base':'--root (exact Skill repository root)','target':v['version info'],'scope':'Read-only lexical existence scan; no semantic proof, no type inference for unqualified/local-variable fields, no extension/version feature legality proof. Missing VUIDs may be obsolete; matching VUID existence does not validate the prose interpretation.','counts':dict(counts),'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [xml_path,evidence/'vulkan_core.h',evidence/'validusage.json']},'input_sha256':hashes,'unknown_symbols':dict(sorted(unknown.items())),'unknown_qualified_members':members,'unknown_vuids':dict(sorted(vunknown.items())),'matched_vuids_for_semantic_review':dict(sorted(vmatches.items()))}
out=a.output;out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'output':str(out),'counts':result['counts'],'unknown_symbols':len(unknown),'unknown_qualified_members':len(members),'unknown_vuids':len(vunknown),'unknown_concrete_vuids':sum(bool(re.search(r'-\d+$',s)) for s in vunknown)},indent=2))
