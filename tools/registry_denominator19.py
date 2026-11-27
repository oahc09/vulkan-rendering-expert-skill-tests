"""Lossless element-coordinate inventory of two pinned XML documents, not semantics."""
import hashlib,json,os,stat,xml.etree.ElementTree as ET
COMMIT='fa30d4e312e843193601be7cb926c7e25d9ec885'
HASHES={'vk.xml':'d56ff7f1613c36b820998dbd8e184b79ec49dc44db63390185205fa15ebcd444','video.xml':'1b6ed670bd1a4e1abb04b40a324f54d60e2a2ab5938fe72e99cb8223d298873f'}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def read_source(path):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  st=os.fstat(fd);need(stat.S_ISREG(st.st_mode) and st.st_size<=16000000,'bounded regular XML required')
  with os.fdopen(fd,'rb',closefd=False) as f:raw=f.read(16000001)
  need(len(raw)<=16000000,'XML too large');return raw
 finally:os.close(fd)
def _document(raw,name):
 need(isinstance(raw,bytes) and len(raw)<=16000000,'bounded XML bytes required')
 need(b'<!ENTITY' not in raw and b'<!DOCTYPE' not in raw,'DTD/entity declarations unsupported')
 root=ET.fromstring(raw);nodes={};definitions={};relations=[]
 def visit(e,path,ancestors):
  attrs=dict(sorted(e.attrib.items()));children=[path+'/'+str(i) for i in range(len(e))]
  rec={'coordinate':path,'tag':e.tag,'attributes':attrs,'text':e.text,'tail':e.tail,'children':children,'context':ancestors,'semantic_status':'UNREVIEWED'}
  rec['subtree_sha256']=sha(canonical({'tag':e.tag,'attributes':attrs,'text':e.text,'tail':e.tail,'children':[ET.tostring(c,encoding='unicode') for c in e]}));nodes[path]=rec
  # Definition roles are deliberately separate from same-name require references.
  parent=ancestors[-1]['tag'] if ancestors else None
  symbol=attrs.get('name')
  if not symbol and e.tag in ('type','command'):
   n=e.find('name') if e.tag=='type' else e.find('proto/name');symbol=n.text if n is not None else None
  if symbol and ((e.tag=='type' and parent=='types') or(e.tag=='command' and parent=='commands') or e.tag=='enum' or e.tag in ('feature','extension','enums')):
   if parent not in ('require','remove') or e.tag=='enum' and any(k in attrs for k in ('value','offset','alias','bitpos')):definitions.setdefault(symbol,[]).append(path)
  for key in ('alias','structextends','extends'):
   if key in attrs:
    for target in attrs[key].split(','):relations.append({'source':path,'kind':key,'target':target,'context':ancestors+[{'tag':e.tag,'attributes':attrs}]})
  if e.tag in ('type','command','enum') and parent in ('require','remove') and symbol:relations.append({'source':path,'kind':parent,'target':symbol,'context':ancestors+[{'tag':e.tag,'attributes':attrs}]})
  if e.tag=='type' and parent in ('member','param','proto') and e.text:relations.append({'source':path,'kind':'type_use','target':e.text,'context':ancestors})
  for key in ('depends','requires','protect','api','supported','platform','provisional'):
   if key in attrs:relations.append({'source':path,'kind':'condition:'+key,'expression':attrs[key],'context':ancestors})
  for i,c in enumerate(e):visit(c,children[i],ancestors+[{'tag':e.tag,'attributes':attrs}])
 visit(root,'0',[])
 for r in relations:
  if 'target'in r:
   candidates=definitions.get(r['target'],[]);r['candidates']=candidates;r['resolution']='UNRESOLVED_OR_EXTERNAL' if not candidates else 'UNIQUE_STRUCTURAL_CANDIDATE' if len(candidates)==1 else 'CONDITIONAL_OR_MULTIPLE_CANDIDATES'
 return {'name':name,'source_sha256':sha(raw),'nodes':nodes,'definitions':definitions,'relations':relations,'element_count':len(nodes),'relation_count':len(relations)}
def build(sources):
 need(type(sources)is dict and set(sources)==set(HASHES),'exact two source files required')
 for n,b in sources.items():need(type(b)is bytes and sha(b)==HASHES[n],'wrong frozen '+n)
 return {'schema':1,'status':'COMPLETE_PINNED_XML_ELEMENT_STRUCTURE_ONLY','commit':COMMIT,'version':'1.4.368','documents':{n:_document(sources[n],n) for n in sorted(sources)},'semantic_status':'UNREVIEWED','limits':['Every XML element/attribute/text/tail is retained; comments and processing instructions are not element coordinates and remain in hashed original bytes.','Conditions and dependency expressions are preserved, not evaluated; remove blocks are not applied.','Reference candidates are lexical, not API applicability, feature enablement or semantic equivalence.','309 VUIDs, expanded specification prose, Headers and SPIR-V remain separate unfinished denominators.','No L1/L2, device support or runtime execution follows from indexing.']}
def verify(report,sources):
 need(canonical(report)==canonical(build(sources)),'inventory differs from exact reconstruction');return True
def alias_applicability(report,sources,document,coordinate,source_scope,target_scope):
 """Verify frozen relation first; caller scope matching is not applicability proof."""
 verify(report,sources)
 keys={'api','api_version','registry_revision','conditions'}
 def valid(s):return type(s)is dict and set(s)==keys and s['api']=='vulkan' and s['api_version']=='1.4' and s['registry_revision']=='1.4.368' and type(s['conditions'])is list and all(type(x)is str and x for x in s['conditions']) and s['conditions']==sorted(set(s['conditions']))
 if not valid(source_scope) or not valid(target_scope):return 'APPLICABILITY_UNRESOLVED'
 if type(document)is not str or document not in report['documents'] or type(coordinate)is not str:return 'APPLICABILITY_UNRESOLVED'
 rows=[r for r in report['documents'][document]['relations'] if r['source']==coordinate and r['kind']=='alias']
 if len(rows)!=1 or rows[0]['resolution']!='UNIQUE_STRUCTURAL_CANDIDATE':return 'APPLICABILITY_UNRESOLVED'
 if canonical(source_scope)!=canonical(target_scope):return 'APPLICABILITY_UNRESOLVED'
 nodes=report['documents'][document]['nodes']
 for c in (coordinate,rows[0]['candidates'][0]):
  n=nodes[c]
  for ctx in n['context']+[{'attributes':n['attributes']}]:
   attrs=ctx['attributes']
   for key in ('api','supported'):
    if key in attrs and 'vulkan' not in attrs[key].split(','):return 'APPLICABILITY_UNRESOLVED'
 return 'STRUCTURAL_ALIAS_TARGET_ONLY_NOT_ENABLED_OR_INTERCHANGEABLE'
