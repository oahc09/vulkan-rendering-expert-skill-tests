#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import prose_denominator19 as r
def main():
 p=argparse.ArgumentParser();p.add_argument('--docs-git',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 files=r.load(a.docs_git);report=r.build(files);r.verify(report,files)
 a.output.mkdir(parents=True,exist_ok=False);(a.output/'summary.json').write_text('{"status":"BLOCKED_PARTIAL_OUTPUT"}\n')
 raw=r.canon(report)+b'\n';(a.output/'source-graph.json').write_bytes(raw)
 r.need(r.canon(r.build(r.load(a.docs_git)))==r.canon(report),'source objects changed')
 bridge=r.semantic_bridge(Path(__file__).resolve().parents[1])
 summary={'semantic_bridge':bridge,'status':report['status'],'closure_status':'BLOCKED','commit':r.COMMIT,'tracked_source_count':len(files),'graph_records':len(report['adoc_graph']),'generation_reference_count':len(report['generation_references']),'manual_spans':report['manual_span_candidates'],'graph_sha256':r.sha(raw),'implementation_sha256':r.sha(Path(r.__file__).read_bytes()),'blockers':report['closure_blockers']}
 (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
