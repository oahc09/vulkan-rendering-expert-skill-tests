"""Bounded observed official core1.4 HTML execution; not all normative closure."""
import collections,hashlib,json,os,re
from pathlib import Path
from . import prose_denominator19 as p
from . import prose_generation19 as g
RUNTIME_SHA='e671705e714c0ccbd9113a18a97c8d22a18d0af4326dc4108940b72e3bb2e709'
GENERATED_SHA='398484391ee5a424fc4cfe2064a8926f97f2d73814f02036224d3ee61d860550'
HTML_SHA='cf34d8bfae4b032e02a3bfee25b81fb39c613b65ce531d56d256f39eedb2b550'
COUNTS={'conditional':28092,'resolve':1983,'push_include':1983,'include_directive':1983,'observer_end':1}
def execution_path(path):
 path=Path(path).resolve();p.need(re.fullmatch(r'/[A-Za-z0-9_./-]+',str(path)) is not None,'fixed make recipe requires shell-neutral paths');return path
def tree(root):
 result={}
 for f in sorted(root.rglob('*')):
  name=f.relative_to(root).as_posix()
  if f.is_symlink():result[name]={'symlink':str(f.readlink())}
  elif f.is_file():result[name]={'sha256':p.sha(f.read_bytes())}
  else:p.need(f.is_dir(),'nonregular tree entry')
 return result
def runtime(root):
 r=tree(root);p.need(p.sha(p.canon(r))==RUNTIME_SHA,'wrong extracted official package cohort');return r
def generated(root):
 r=g.validate(root);p.need(p.sha(p.canon(r))==GENERATED_SHA,'wrong original generated cohort');return r
def unique(pairs):
 r={}
 for k,v in pairs:p.need(k not in r,'duplicate JSON key');r[k]=v
 return r
def normalized_trace(rows,root,runtime_root,tools_root):
 def transform(v):
  if type(v)is str:
   for before,after in ((str(root),'$SOURCE'),(str(runtime_root),'$RUNTIME'),(str(tools_root),'$TOOLS'),('/tmp/vulkan119-tests','$TOOLS')):v=v.replace(before,after)
   return v
  if type(v)is list:return [transform(x) for x in v]
  if type(v)is dict:return {k:transform(x) for k,x in v.items()}
  return v
 return transform(rows)
TRACE_SHA='b9f6d91c59992ad119117d589a6e0d08e78db9b7a82a2242cf6910d0ee6ef96d'
def analyze(trace,root,baseline,observed,runtime_root):
 p.need(baseline==observed and p.sha(observed)==HTML_SHA,'official HTML bytes differ')
 p.need(len(trace)<=64000000,'trace bound');rows=[json.loads(l,object_pairs_hook=unique) for l in trace.splitlines()];p.need(len(rows)==34042,'trace count')
 tools_root=Path(__file__).resolve().parents[1]
 p.need(p.sha(p.canon(normalized_trace(rows,root,runtime_root,tools_root)))==TRACE_SHA,'fixed normalized observation matrix differs')
 for feature in rows[-1].get('loaded_features',[]):
  f=Path(feature['path']);p.need(f.is_relative_to(root) or f.is_relative_to(runtime_root) or f==tools_root/'tools/asciidoc_observer19.rb','unexpected Ruby loaded feature')
  p.need(f.is_file() and p.sha(f.read_bytes())==feature['sha256'],'Ruby loaded feature changed')
 counts=dict(collections.Counter(r.get('kind') for r in rows));p.need(counts==COUNTS and rows[-1]['kind']=='observer_end','exact fixed core trace matrix')
 includes=[];tag_count=0;pending=[]
 for r in rows:
  if r['kind']!='observer_end':
   location=r['source'];source_file=Path(location['file']);p.need(source_file.resolve().is_relative_to(root.resolve()) and source_file.is_file() and type(location['line'])is int and location['line']>0,'source observation location')
  if r['kind']=='push_include':
   f=Path(r['file']);p.need(pending and pending.pop(0)==str(f),'resolve/push association');p.need(f.is_relative_to(root) and not f.is_symlink() and f.is_file(),'include outside source copy')
   p.need(p.sha(f.read_bytes())==r['whole_file_sha256'],'included source changed')
   pieces=r['selected_pieces'];p.need(type(pieces)is list and all(type(x)is str for x in pieces),'selected piece schema')
   p.need(p.sha(json.dumps(pieces,ensure_ascii=False,separators=(',',':')).encode())==r['selected_sha256'],'selected data changed')
   tag_count+=int('tag'in r['attributes'] or 'tags'in r['attributes'])
   includes.append({'file':str(f.relative_to(root)),'whole_file_sha256':r['whole_file_sha256'],'selected_sha256':r['selected_sha256'],'options':r['attributes'],'engine_start_line':r['engine_start_line']})
  elif r['kind']=='resolve':
   p.need(type(r['resolved'])is list and len(r['resolved'])==3 and r['resolved'][1]=='file','missing/remote include resolution');target=Path(r['resolved'][0]);p.need(target.resolve().is_relative_to(root.resolve()) and target.is_file(),'resolved include outside source');pending.append(str(target))
 p.need(not pending,'unconsumed include resolution')
 p.need(tag_count>0,'no actual tag selections');p.need(any(r.get('skipping_after') is True for r in rows if r['kind']=='conditional'),'no skipped condition observed')
 return {'status':'FIXED_CORE_HTML_OBSERVED_MATCH','closure_status':'PARTIAL_SINGLE_CONFIGURATION_NOT_ALL_P','html_sha256':p.sha(observed),'html_bytes':len(observed),'event_counts':counts,'tag_selection_count':tag_count,'selected_includes':includes,'limits':['Selected strings are actual engine push_include input before normalization.','engine_start_line is not a complete source interval map: upstream skips tag lines without preserving all line positions.','No Reference/validusage/SC/platform/all-extension closure; no semantic L1/L2 acceptance.']}
