"""Fixed Docs 368 all-Vulkan extraction checks, not universal semantic closure."""
import ast, collections, json, re
from html.parser import HTMLParser
from pathlib import PurePosixPath
from . import prose_denominator19 as p
from .asciidoc_execution19 import unique
VERSION={'schema version':2,'api version':'1.4.368','comment':'frozen-fa30d4e-source-replay','date':'2026-11-06T01:31:32Z'}
PAGES=('VkMemoryDedicatedRequirements','vkBindBufferMemory')

def literal_map(raw,name):
 p.need(len(raw)<16000000,'map size');tree=ast.parse(raw)
 p.need(len(tree.body)==1 and isinstance(tree.body[0],ast.Assign),'literal map only')
 stmt=tree.body[0];p.need(len(stmt.targets)==1 and isinstance(stmt.targets[0],ast.Name) and stmt.targets[0].id==name and isinstance(stmt.value,ast.Dict),'map assignment')
 keys=[ast.literal_eval(k) for k in stmt.value.keys];p.need(all(type(k)is str for k in keys) and len(keys)==len(set(keys)),'duplicate/nonstring map keys')
 result=ast.literal_eval(stmt.value);p.need(type(result)is dict and result,'nonempty map');return result

class Anchors(HTMLParser):
 def __init__(self):super().__init__();self.ids=collections.Counter()
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k=='id':self.ids[v]+=1

def safe_page(value):
 return type(value)is str and bool(re.fullmatch(r'[A-Za-z0-9_./-]+\.html',value)) and not value.startswith('/') and '..' not in PurePosixPath(value).parts

def inspect_vu(raw,xref_raw,page_raw,html):
 p.need(len(raw)<64000000 and len(html)<64000000,'output bound')
 obj=json.loads(raw,object_pairs_hook=unique);p.need(type(obj)is dict and set(obj)=={'version info','validation'},'VU top-level shape')
 p.need(p.canon(obj['version info'])==p.canon(VERSION),'exact extractor version metadata; draft4 const is not enforced')
 validation=obj['validation'];p.need(type(validation)is dict and 0<len(validation)<5000,'owner map')
 xref=literal_map(xref_raw,'xrefMap');pages=literal_map(page_raw,'pageMap');anchors=Anchors();anchors.feed(html.decode('utf-8'));rows=[];seen=set()
 for owner,groups in validation.items():
  p.need(re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',owner) is not None and type(groups)is dict and set(groups)=={'core'},'fixed extractor owner/core shape; core is legacy bucket not extension scope')
  values=groups['core'];p.need(type(values)is list and values,'nonempty VU list')
  for n,v in enumerate(values):
   p.need(type(v)is dict and set(v)=={'vuid','text','page'},'exact VU fields')
   vid=v['vuid'];p.need(type(vid)is str and re.fullmatch(r'VUID-[A-Za-z0-9_]+-[A-Za-z0-9_:-]+',vid) is not None,'exact VUID syntax')
   p.need(vid not in seen,'duplicate VUID rejected for this fixed observed cohort');seen.add(vid)
   p.need(type(v['text'])is str and v['text'].strip() and safe_page(v['page']),'text/page shape')
   coord=xref.get(vid);p.need(type(coord)is list and len(coord)==2 and all(type(x)is str for x in coord),'VUID missing xref')
   page=pages.get(coord[0]);p.need(type(page)is str and page.endswith('.adoc'),'VUID missing page map')
   p.need(v['page']==page[:-5]+'.html','page mapping differs')
   p.need(anchors.ids[vid]>=1,'VUID not present in independently rendered HTML')
   rows.append({'owner':owner,'bucket':'core','index':n,'vuid':vid,'text_sha256':p.sha(v['text'].encode()),'page':v['page'],'chapter_anchor':coord[0],'html_anchor_count':anchors.ids[vid]})
 p.need(len(rows)<=50000,'VU count limit')
 p.need(seen=={v for v in anchors.ids if type(v)is str and v.startswith('VUID-')},'HTML/VU sets differ')
 return {'status':'STRUCTURE_AND_PAGE_ASSOCIATIONS_RECHECKED','owners':len(validation),'vuid_count':len(rows),'rows':rows,'rows_sha256':p.sha(p.canon(rows)),'limitations':['legacy core bucket does not mean core-only','HTML association and fixed source hashes do not establish every normative condition','official draft4 schema is separately weak; this validator adds cohort obligations']}

def require_same(first,second):
 p.need(first==second,'independent fresh outputs differ');return p.sha(first)

def reference_page(raw,name):
 p.need(name in PAGES,'unregistered reference page');parser=Anchors();parser.feed(raw.decode())
 p.need(len(raw)>1000 and b'<html' in raw and name.encode() in raw and b'ERROR:' not in raw,'reference HTML content')
 expected='VUID-VkMemoryDedicatedRequirements-sType-sType' if name==PAGES[0] else 'VUID-vkBindBufferMemory-memory-01035'
 p.need(parser.ids[expected]>0,'reference expected VUID missing');return {'page':name,'html_sha256':p.sha(raw),'bytes':len(raw),'checked_vuid':expected}

ROWS_SHA='de91f1b08cfbaa56b957b0b37a72964bccf602a5da7d70bbd38d4033546e6e50'
def fixed_cohort(result):
 p.need(type(result)is dict and result.get('owners')==2251 and result.get('vuid_count')==27464 and p.sha(p.canon(result.get('rows')))==ROWS_SHA,'fixed reviewed owner/text/page/index matrix differs')
 p.need(result.get('rows_sha256')==ROWS_SHA,'self-reported row digest differs')
 return {'status':'FIXED_ALL_VULKAN_VU_MATRIX_MATCH','authority':'FIXED_OBSERVED_COHORT_RECHECK_NOT_INDEPENDENT_SEMANTIC_PROOF','rows_sha256':ROWS_SHA}

TRACE_SHA='be6c83c7bbc19d0fc270bc4d400222af5bcb18c6a64ccd59fa894941d87f943e'
def inspect_trace(raw,root,runtime_root):
 from pathlib import Path
 from .asciidoc_execution19 import normalized_trace
 p.need(len(raw)<32000000,'VU trace bound');rows=[json.loads(l,object_pairs_hook=unique) for l in raw.splitlines()]
 p.need(collections.Counter(r.get('kind') for r in rows)=={'condition':52537,'push':8349},'exact trace event matrix; missing is not success')
 p.need(p.sha(p.canon(normalized_trace(rows,root,runtime_root,Path(__file__).resolve().parents[1])))==TRACE_SHA,'fixed normalized observation differs')
 tags=0
 for row in rows:
  if row['kind']=='push':
   p.need(set(row)=={'kind','file','path','line','attributes','selected_sha256','whole_sha256'},'push fields')
   f=Path(row['file']);p.need(f.resolve().is_relative_to(root.resolve()) and f.is_file() and not f.is_symlink(),'selected source path')
   p.need(p.sha(f.read_bytes())==row['whole_sha256'],'selected source changed');p.need(type(row['line'])is int and row['line']>0 and type(row['attributes'])is dict,'push shape')
   tags+=int('tag'in row['attributes'] or 'tags'in row['attributes'])
  else:
   p.need(set(row)=={'kind','keyword','target','delimiter','text','before','after','result'},'condition fields')
   p.need(all(type(row[k])is bool for k in ('before','after','result')),'condition booleans')
 p.need(tags==477,'fixed selected tag count')
 return {'status':'FIXED_OBSERVATION_MATRIX_RECHECKED','events':60886,'push_events':8349,'condition_events':52537,'tag_selections':477,'quiet_missing':0,'normalized_sha256':TRACE_SHA,'boundary':'fixed observed cohort plus actual engine controls; not a general conditional/tag solver; no at_exit marker assumed'}
