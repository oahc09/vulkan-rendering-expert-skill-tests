"""Fixed all-Vulkan368 reference rendering inventory; not semantic equivalence."""
import ast,re
from pathlib import Path
from html.parser import HTMLParser
from . import prose_denominator19 as p
from . import asciidoc_execution19 as a
SOURCE_TREE_SHA='39681837283249fea7741fa5b0c2b9fd3bf77082e169f850a5823f9770f0a6fa'
APIMAP_SHA='81a4aad9ed84dfd776b0f8a4875cb77d41512efd69e9536d713a1aaf3d70b1ab'
def source(root):
 inventory=a.tree(root);p.need(p.sha(p.canon(inventory))==SOURCE_TREE_SHA,'wrong fixed P4 source/generated cohort');return inventory

def expected(root):
 raw=(root/'gen/apimap.py').read_bytes();p.need(p.sha(raw)==APIMAP_SHA,'fixed API map mismatch')
 module=ast.parse(raw);values={}
 for node in module.body:
  p.need(isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name),'literal apimap assignments only')
  name=node.targets[0].id;p.need(name not in values,'duplicate apimap assignment')
  p.need(isinstance(node.value,ast.Dict),'literal dictionary')
  keys=[ast.literal_eval(k) for k in node.value.keys];p.need(len(keys)==len(set(keys)),'duplicate map keys');values[name]=ast.literal_eval(node.value)
 alias=values['alias'];skip={k:v for k,v in alias.items() if k.endswith(('_EXTENSION_NAME','_SPEC_VERSION'))};links={k:v for k,v in alias.items() if k not in skip}
 refs={};contents={}
 for f in sorted((root/'gen/refpage').glob('*.adoc')):
  raw=f.read_bytes();refs[f.stem]=p.sha(raw);text=raw.decode('utf-8');parts=text.split('== Name\n');p.need(len(parts)==2,'exact source Name section')
  name=parts[1].split('\n\n',1)[0].strip();p.need(name.startswith(f.stem+' - '),'source Name identity')
  # The fixed official manpage renderer preserves Name inline macro tokens.
  # Only this registered attribute is expanded into inline subscripts here.
  name=name.replace('{YCbCr}','Y′C<sub>B</sub>C<sub>R</sub>')
  p.need('{' not in name and '}' not in name,'unhandled source Name attribute')
  contents[f.stem]={'name_html':' '.join(name.split()),'required_sections':re.findall(r'^== (.+)$',text,re.M)}
  if f.stem=='VkPipelineCacheCreateInfo':
   span=b''.join(raw.splitlines(keepends=True)[46:75]);p.need(p.sha(raw)=='3a4b4f0c386c73856e8b23e3fcda11f3f2837657f75cfca12df073990e888cee' and p.sha(span)=='a6fd8bb41db915545e33f8d55c85e212d6acde770fd854de213c9a6931725646','fixed SC-only section context')
   contents[f.stem]['required_sections'].remove('Description');contents[f.stem]['excluded_section']={'heading':'Description','condition':'VKSC_VERSION_1_0','source_lines':[47,75],'source_span_sha256':p.sha(span),'authority':'MANUALLY_REGISTERED_FIXED_SOURCE_SCOPE'}
 p.need((len(refs),len(alias),len(skip),len(links))==(3553,487,10,477),'fixed matrix cardinality')
 p.need(all(re.fullmatch(r'[A-Za-z0-9_-]+',n) for n in refs),'entity identifier')
 p.need(not set(refs)&set(links) and set(links.values())<=set(refs),'aliases are distinct direct entities')
 p.need(len({n.casefold() for n in set(refs)|set(links)})==len(refs)+len(links),'case-fold collision')
 return {'entities':refs,'aliases':links,'excluded_metadata':skip,'content_contracts':contents}

class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,data):self.parts.append(data)

def visible_text(markup):
 parser=Text();parser.feed(markup);return ''.join(parser.parts)

class Page(HTMLParser):
 def __init__(self):super().__init__();self.in_title=False;self.title=[];self.start=[];self.end=[]
 def handle_starttag(self,tag,attrs):
  self.start.append(tag)
  if tag=='title':self.in_title=True
 def handle_endtag(self,tag):
  self.end.append(tag)
  if tag=='title':self.in_title=False
 def handle_data(self,data):
  if self.in_title:self.title.append(data)

def inspect_output(directory,matrix,checkpoint=None):
 p.need(directory.is_dir() and not directory.is_symlink(),'HTML output directory')
 names={f.name for f in directory.iterdir()};expected_names={n+'.html' for n in set(matrix['entities'])|set(matrix['aliases'])};p.need(names==expected_names,'exact entity and alias file set')
 entities={};aliases={};empty_sections=[];c_specifications=0
 for name,source_sha in matrix['entities'].items():
  if checkpoint:checkpoint()
  f=directory/(name+'.html');p.need(f.is_file() and not f.is_symlink(),'entity must be regular HTML')
  raw=f.read_bytes();p.need(1000<len(raw)<16000000,'HTML size bounds');html=Page();html.feed(raw.decode('utf-8'))
  p.need(''.join(html.title)==name+'(3)' and all(html.start.count(k)==1 and html.end.count(k)==1 for k in ('html','head','body','title')),'complete HTML/entity title')
  p.need(b'include file not found:' not in raw and b'Unresolved directive' not in raw,'unresolved directive in output')
  text=raw.decode('utf-8');name_match=re.search(r'<h2 id="_name">Name</h2>\s*<div class="sectionbody">\s*<p>(.*?)</p>',text,re.S)
  contract=matrix['content_contracts'][name]
  p.need(name_match is not None and ' '.join(name_match.group(1).split())==contract['name_html'],'source-derived Name body mismatch')
  headings=[visible_text(v) for v in re.findall(r'<h2(?: [^>]*)?>(.*?)</h2>',text,re.S)]
  p.need(all(section in headings for section in contract['required_sections']),'source-derived required section missing')
  matches=list(re.finditer(r'<h2(?: [^>]*)?>(.*?)</h2>',text,re.S));sections={visible_text(m.group(1)):text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)] for i,m in enumerate(matches)}
  for section in contract['required_sections']:
   body=sections[section]
   if not visible_text(body).strip():empty_sections.append({'entity':name,'section':section,'reason':'OBSERVED_EMPTY_FIXED_OUTPUT; INDIVIDUAL_SEMANTIC_REASON_NOT_FULLY_AUDITED'})
   if section=='C Specification':
    code=' '.join(visible_text(x) for x in re.findall(r'<code(?: [^>]*)?>(.*?)</code>',body,re.S));p.need(re.search(r'(?<![A-Za-z0-9_])'+re.escape(name)+r'(?![A-Za-z0-9_])',code) is not None,'C Specification missing entity identifier');c_specifications+=1
  entities[name]={'source_name_and_sections_checked':True,'source_sha256':source_sha,'html_sha256':p.sha(raw),'bytes':len(raw)}
 for name,target in matrix['aliases'].items():
  if checkpoint:checkpoint()
  f=directory/(name+'.html');p.need(f.is_symlink() and str(f.readlink())==target+'.html','alias must be exact relative symlink')
  p.need(f.resolve().parent==directory.resolve() and f.resolve().is_file() and not (directory/(target+'.html')).is_symlink(),'alias target direct regular entity in output root');aliases[name]=target
 return {'status':'FIXED_REFERENCE_RENDER_AND_ALIAS_INVENTORY','entities':entities,'aliases':aliases,'entity_count':len(entities),'alias_count':len(aliases),'c_specification_entity_identifiers_checked':c_specifications,'empty_other_sections':empty_sections,'semantic_review':False,'internal_cross_page_link_check':'NOT_RUN'}
