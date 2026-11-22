#!/usr/bin/env python3
"""Read-only fixed XML inventory; fresh output, no user commands."""
import argparse,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import registry_denominator19 as r
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 sources={n:r.read_source(a.source_dir/n) for n in r.HASHES};result=r.build(sources);r.verify(result,sources)
 alias=next(x for x in result['documents']['vk.xml']['relations'] if x['kind']=='alias' and x['resolution']=='UNIQUE_STRUCTURAL_CANDIDATE')
 scope={'api':'vulkan','api_version':'1.4','registry_revision':'1.4.368','conditions':[]}
 positive=r.alias_applicability(result,sources,'vk.xml',alias['source'],scope,scope)
 negative=r.alias_applicability(result,sources,'vk.xml',alias['source'],scope,{**scope,'api':'vulkansc'})
 r.need(positive=='STRUCTURAL_ALIAS_TARGET_ONLY_NOT_ENABLED_OR_INTERCHANGEABLE' and negative=='APPLICABILITY_UNRESOLVED','alias boundary controls failed')
 for n,b in sources.items():r.need(r.read_source(a.source_dir/n)==b,'source changed')
 a.output.mkdir(parents=True,exist_ok=False)
 (a.output/'summary.json').write_text('{"status":"BLOCKED_PARTIAL_OUTPUT"}\n')
 raw=r.canonical(result)+b'\n';(a.output/'inventory.json').write_bytes(raw)
 summary={'alias_host_controls':{'source_coordinate':alias['source'],'target':alias['target'],'same_declared_scope':positive,'cross_api':negative,'authority':'CALLER_DECLARED_SCOPE_NOT_AUTHENTICATED'},'status':result['status'],'semantic_status':'UNREVIEWED','source_sha256':r.HASHES,'inventory_sha256':r.sha(raw),'implementation_sha256':r.sha(Path(r.__file__).read_bytes()),'documents':{n:{k:d[k] for k in ('element_count','relation_count')} for n,d in result['documents'].items()},'limits':result['limits']}
 for n,b in sources.items():r.need(r.read_source(a.source_dir/n)==b,'source changed')
 (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
