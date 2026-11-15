#!/usr/bin/env python3
"""Reconstruct mechanical Registry inventory; never semantic coverage or API support."""
import argparse, collections, hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET
SOURCE_COMMIT='fa30d4e312e843193601be7cb926c7e25d9ec885'
SOURCE_SHA256='d56ff7f1613c36b820998dbd8e184b79ec49dc44db63390185205fa15ebcd444'
SOURCE_URL=f'https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/{SOURCE_COMMIT}/xml/vk.xml'

def apis(value): return set((value or '').split(','))

def classify_extension(e):
    supported=apis(e.get('supported'))
    if 'disabled' in supported:return 'disabled'
    if 'vulkan' not in supported:return 'other_api_or_unspecified'
    if e.get('provisional')=='true':return 'vulkan_provisional'
    return 'vulkan_stable'

def requirements(element):
    result=[]
    for block in element.findall('require'):
        if block.get('api') and 'vulkan' not in apis(block.get('api')):continue
        # Preserve dependency expressions; do not claim they are evaluated here.
        for child in block:
            if child.tag not in ('type','command','enum') or not child.get('name'):continue
            if child.get('api') and 'vulkan' not in apis(child.get('api')):continue
            result.append({'kind':child.tag,'name':child.get('name'),
                           'condition':block.get('depends'), 'api':block.get('api'),
                           'alias':child.get('alias'),'extends':child.get('extends'),
                           'block_attributes':dict(block.attrib),'symbol_attributes':dict(child.attrib)})
    return result

def inventory(raw):
    root=ET.fromstring(raw)
    extensions=[]; seen=set()
    for e in root.findall('extensions/extension'):
        name=e.get('name')
        if not name or name in seen:raise ValueError('missing/duplicate extension identity')
        seen.add(name)
        extensions.append({'name':name,'classification':classify_extension(e),
          'supported':e.get('supported'),'provisional':e.get('provisional'),
          'depends':e.get('depends'),'platform':e.get('platform'),
          'promotedto':e.get('promotedto'),'deprecatedby':e.get('deprecatedby'),
          'obsoletedby':e.get('obsoletedby'),'requirements':requirements(e),
          'remove_blocks':[ET.tostring(x,encoding='unicode') for x in e.findall('remove')],
          'semantic_L1_L2':'UNREVIEWED'})
    features=[]
    for f in root.findall('feature'):
        number=tuple(map(int,f.get('number','0').split('.')))
        included='vulkan' in apis(f.get('api')) and (1,0)<=number<=(1,4)
        features.append({'name':f.get('name'),'api':f.get('api'),'number':f.get('number'),
                         'included_standard_vulkan':included,'depends':f.get('depends'),
                         'requirements':requirements(f), 'remove_blocks':[ET.tostring(x,encoding='unicode') for x in f.findall('remove')], 'semantic_L1_L2':'UNREVIEWED'})
    counts=dict(sorted(collections.Counter(e['classification'] for e in extensions).items()))
    included=[e for e in extensions if e['classification']=='vulkan_stable']+[f for f in features if f['included_standard_vulkan']]
    refs={(r['kind'],r['name']) for e in included for r in e['requirements']}
    summary={'extension_records':len(extensions),'classification_counts':counts,
             'feature_records':len(features),'included_feature_records':sum(f['included_standard_vulkan'] for f in features),
             'unique_direct_requirement_symbols':dict(sorted(collections.Counter(k for k,n in refs).items())),
             'semantic_reviewed_entries':0,'release_status':'BLOCKED'}
    return {'schema':1,'source_commit':SOURCE_COMMIT,'source_sha256':hashlib.sha256(raw).hexdigest(),
            'summary':summary,'features':features,'extensions':extensions,
            'limits':['direct require references only, not transitive type/member/enum dependency closure',
                      'dependency and protect attributes preserved but not evaluated; remove blocks recorded but not applied'
                      ,'global command/type aliases are not resolved; require-local aliases preserved',
                      'feature subdivisions retained; not counted as additional Vulkan versions',
                      'classification is not L0 routing, L1/L2 semantics, device support or Live acceptance']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--xml',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();raw=a.xml.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:raise ValueError('wrong frozen Registry bytes')
    report=inventory(raw);a.out.mkdir(parents=True,exist_ok=False)
    full=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n'
    (a.out/'inventory.json').write_bytes(full)
    summary={'source_url':SOURCE_URL,'source_sha256':SOURCE_SHA256,'inventory_sha256':hashlib.sha256(full).hexdigest(),**report['summary'],'limits':report['limits']}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
