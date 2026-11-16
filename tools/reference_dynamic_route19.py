"""Registered two-anchor repair; source-cohort evidence, not per-xref provenance."""
import json,re
from pathlib import Path
from . import prose_denominator19 as p
from . import reference_links19 as links
FIXTURE=Path(__file__).resolve().parents[1]/'tests/fixtures/reference-dynamic-route19.json'
BASELINE_SHA='d94a79e2aa8a747ecdc85fa06261f2142bc34571cecc187841f2cae4d14fd02a'
def config():return json.loads(FIXTURE.read_bytes())
def preflight(root,c):
 for path,expected in c['sources'].items():p.need(p.sha((root/path).read_bytes())==expected,'fixed original source')
 for name,item in c['pages'].items():p.need(p.sha((root/'gen/refpage'/(name+'.adoc')).read_bytes())==item['source_sha256'],'fixed generated reference')
 raw=(root/'gen/out/html/vkspec.html').read_bytes();p.need(p.sha(raw)==c['full_spec_html_sha256'],'fixed full specification');doc=links.Document();doc.feed(raw.decode())
 for target in c['counts']:p.need(doc.ids[target]==1,'unique fullspec anchor')
 for span in c['definition_spans']:
  raw=(root/'chapters/pipelines.adoc').read_bytes();a,b=span['lines'];p.need(p.sha(b''.join(raw.splitlines(keepends=True)[a-1:b]))==span['sha256'],'target definition span')
def check_page(name,before,after,c):
 expected=before;counts={}
 for target in c['counts']:
  old=('href="#'+target+'"').encode();new=('href="../../html/vkspec.html#'+target+'"').encode();count=before.count(old);counts[target]=count
  p.need(count==c['pages'].get(name,{}).get('counts',{}).get(target,0),'registered page occurrence count')
  if count:
   doc=links.Document();doc.feed(before.decode());p.need(doc.ids[target]==0,'existing local target must not route');expected=expected.replace(old,new)
 p.need(after==expected,'only registered href replacements allowed');return counts
