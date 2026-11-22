"""Offline fixed-output href audit. Never fetches URLs or repairs a link."""
import collections,json,posixpath,re,stat
from html.parser import HTMLParser
from pathlib import Path,PurePosixPath
from urllib.parse import urlsplit,unquote
from . import prose_denominator19 as p

class Document(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.links=[];self.ids=collections.Counter();self.base=[];self.out_of_scope=collections.Counter()
 def handle_starttag(self,tag,attrs):
  values=dict(attrs)
  if tag=='base':self.base.append(values.get('href'))
  for key,value in attrs:
   if key=='id' and value is not None:self.ids[value]+=1
   elif tag=='a' and key=='name' and value is not None:self.ids[value]+=1
   if key=='href' and value is not None and tag!='base':self.links.append({'tag':tag,'href':value,'line':self.getpos()[0],'column':self.getpos()[1]})
   if key in ('src','srcset'):self.out_of_scope[tag+'/'+key]+=1

def address(page,href,has_base=False):
 if type(href)is not str or any(ord(c)<32 for c in href) or '\\'in href or re.search(r'%(?![0-9A-Fa-f]{2})',href):return {'status':'MALFORMED_OR_AMBIGUOUS_URL'}
 try:
  u=urlsplit(href)
  if u.scheme or u.netloc:return {'status':'EXTERNAL_NOT_FETCHED' if u.scheme in ('','http','https','mailto') else 'UNSUPPORTED_SCHEME_NOT_EXECUTED','scheme':u.scheme or 'network-path'}
  if has_base:return {'status':'BASE_CONTEXT_NOT_EVALUATED'}
  path=unquote(u.path,errors='strict');fragment=unquote(u.fragment,errors='strict')
 except (ValueError,UnicodeError):return {'status':'MALFORMED_OR_AMBIGUOUS_URL'}
 if '\x00'in path or '\x00'in fragment:return {'status':'MALFORMED_OR_AMBIGUOUS_URL'}
 if path.startswith('/'):return {'status':'ROOT_ABSOLUTE_WITHOUT_ORIGIN'}
 target=posixpath.normpath(posixpath.join(posixpath.dirname(page),path)) if path else page
 if target=='..' or target.startswith('../'):return {'status':'OUTSIDE_FIXED_OUTPUT_ROOT'}
 return {'status':'LOCAL_CANDIDATE','target':target,'fragment':fragment,'query':u.query,'query_semantics':'NOT_EVALUATED' if u.query else 'NONE'}

def local_file(root,target,aliases):
 parts=PurePosixPath(target).parts;current=root
 for i,part in enumerate(parts):
  current=current/part
  try:mode=current.lstat().st_mode
  except FileNotFoundError:return None,'MISSING_LOCAL_TARGET',None
  if stat.S_ISLNK(mode):
   # Only registered final-component reference aliases may be followed.
   expected=aliases.get(target)
   if i!=len(parts)-1 or expected is None or str(current.readlink())!=expected:return None,'UNREGISTERED_OR_WRONG_ALIAS',None
   destination=posixpath.join(posixpath.dirname(target),expected)
   if '..'in PurePosixPath(expected).parts or expected.startswith('/'):return None,'UNREGISTERED_OR_WRONG_ALIAS',None
   result,status,_=local_file(root,destination,{})
   return result,status,{'alias':target,'literal_target':expected,'entity':destination}
  if i<len(parts)-1 and not stat.S_ISDIR(mode):return None,'NON_DIRECTORY_PATH_COMPONENT',None
 if not stat.S_ISREG(mode):return None,'NONREGULAR_LOCAL_TARGET',None
 return current,'REGULAR_LOCAL_FILE',None

def audit(root,pages,aliases,checkpoint=None):
 root=root.resolve();cache={};inputs={};all_rows=[];counts=collections.Counter();distinct=collections.defaultdict(set);omitted=collections.Counter();base_pages=[]
 def read(name):
  if name not in cache:
   path,status,_=local_file(root,name,{})
   p.need(status=='REGULAR_LOCAL_FILE','document must be regular under fixed output root');p.need(path.stat().st_size<=64000000,'document bound');raw=path.read_bytes();doc=Document();doc.feed(raw.decode('utf-8'));cache[name]=doc;inputs[name]=p.sha(raw)
  return cache[name]
 spec=read('html/vkspec.html')
 for page in sorted(pages):
  if checkpoint:checkpoint()
  doc=read(page);omitted.update(doc.out_of_scope)
  if doc.base:base_pages.append(page)
  for index,link in enumerate(doc.links):
   row={'page':page,'ordinal':index,**link,'role':'NAVIGATION' if link['tag']in ('a','area') else 'ASSET' if link['tag']=='link' else 'OTHER_HREF_NOT_CLASSIFIED'}
   result=address(page,link['href'],bool(doc.base));row.update(result)
   if result['status']=='LOCAL_CANDIDATE':
    path,status,alias=local_file(root,result['target'],aliases);row['alias_followed']=alias
    if status!='REGULAR_LOCAL_FILE':row['status']=status
    else:
     canonical=str(path.relative_to(root));row['resolved_file']=canonical
     if result['fragment'] and path.suffix.lower()=='.html':
      target=read(canonical);count=target.ids[result['fragment']];row['fragment_occurrences']=count
      row['status']='LOCAL_RESOLVED' if count else 'MISSING_FRAGMENT'
      if not count:row['same_fragment_in_full_spec']=result['fragment']in spec.ids;row['full_spec_match_is_only_candidate_not_resolution']=True
     elif result['fragment']:row['status']='NON_HTML_FRAGMENT_NOT_EVALUATED'
     else:row['status']='LOCAL_RESOLVED'
   counts[row['status']]+=1
   key=(row.get('target',row['href']),row.get('fragment',''));distinct[row['status']].add(key);all_rows.append(row)
  p.need(len(all_rows)<=500000,'href occurrence bound')
 for name,digest in inputs.items():
  path,status,_=local_file(root,name,{});p.need(status=='REGULAR_LOCAL_FILE' and p.sha(path.read_bytes())==digest,'document changed during audit')
 unresolved=sum(n for k,n in counts.items() if k not in ('LOCAL_RESOLVED','EXTERNAL_NOT_FETCHED'))
 return {'status':'PARTIAL_WITH_FINDINGS' if unresolved else 'LOCAL_HREFS_RESOLVED_EXTERNAL_UNVERIFIED','pages':len(pages),'href_occurrences':len(all_rows),'counts':dict(counts),'distinct_targets_by_status':{k:len(v) for k,v in distinct.items()},'base_pages_not_evaluated':base_pages,'out_of_scope_src_attributes':dict(omitted),'input_html_sha256':inputs,'rows':all_rows,'scope':'static HTML href only; no network/CSS url()/src/JS navigation/visual or semantic validation'}
