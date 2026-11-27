"""One registered HOST recipe for the known Tests AST serialization repair."""
import ast,copy,hashlib,json,subprocess,sys
from pathlib import Path
BASE='00c3b8b234576817989df116948a2eaa5af761e2'
CANDIDATE='3afa22d29f93a48c5012a968a5eba2085189bc66'
SKILL='3457cd3811d3a7acd5b31f63b8125d39e3f834fb'
DOCS='fa30d4e312e843193601be7cb926c7e25d9ec885'
PATCH_SHA='162f353bcd0b2bdc0786a29634f7f011f10678bd531d088cf2279a40823cb33c'
ALLOWED=['tests/fixtures/contract-registry19.json','tests/test_contract_registry19.py','tools/contract_registry19.py']
FAMILIES=['descriptor_update','image_copy','image_layout','layout','memory_binding','sync','timeline']
SOURCES=sorted(ALLOWED+[f'checks19/run_{f}_contracts.py' for f in FAMILIES]+[f'tools/{f}_contract19.py' for f in FAMILIES]+[f'tools/{f}_prose19.py' for f in FAMILIES if f!='sync']+['tools/normative_prose19.py','tools/diagnostic_spec19.py'])
DOC_PATHS=['chapters/synchronization.adoc','chapters/descriptorsets.adoc','chapters/commonvalidity/push_constants_common.adoc','chapters/formats.adoc','chapters/copies.adoc','chapters/commonvalidity/copy_image_common.adoc','chapters/resources.adoc','chapters/memory.adoc']
PYTHONS={'312':('/tmp/vulkan118-py/bin/python','fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7'),'313':('/usr/bin/python3.13','889c603f0d17cb54060951bcf4c4f9b8c9ebd9e52b392c70209bbb9755d797d9')}
VU_SHA='f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'
def need(x,msg):
 if not x:raise ValueError(msg)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
GIT_ENV={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_REPLACE_OBJECTS':'1'}
def git(repo,*args):return subprocess.check_output(['/usr/bin/git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-C',str(repo),*args],timeout=30,env=GIT_ENV)
def inventory(root):
 root=Path(root);need(root.is_dir() and not root.is_symlink(),'ordinary export root');out={}
 for p in root.rglob('*'):
  need(not p.is_symlink(),'export symlink')
  if p.is_dir():continue
  need(p.is_file(),'export special file');out[str(p.relative_to(root))]=sha(p.read_bytes())
 return out
def export(repo,head,paths,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=False);result={}
 for relative in sorted(paths):
  p=Path(relative);need(not p.is_absolute() and '..' not in p.parts,'export path')
  fields=git(repo,'ls-tree',head,'--',relative).decode().strip().split(None,3)
  need(len(fields)==4 and fields[0]in ('100644','100755') and fields[1]=='blob' and fields[3]==relative,'ordinary Git blob required')
  data=git(repo,'cat-file','blob',fields[2]);dest=out/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);result[relative]=sha(data)
 return result
def patch(repo,base,candidate,expected,allowed):
 need(base==BASE and candidate==CANDIDATE,'registered revisions only');need(expected==PATCH_SHA,'registered patch digest');need(sorted(allowed)==ALLOWED and len(allowed)==3,'exact approved paths')
 changed=git(repo,'diff','--no-color','--name-only','--no-renames',base,candidate).decode().splitlines();need(sorted(changed)==ALLOWED,'unexpected changed paths')
 raw=git(repo,'diff','--no-color','--no-ext-diff','--no-textconv','--no-renames','--full-index','--binary','--diff-algorithm=myers',base,candidate,'--',*ALLOWED)
 need(sha(raw)==expected==PATCH_SHA,'registered patch digest');return raw
def diffs(a,b,p=''):
 need(type(a)is type(b),'value type differs at '+p)
 if type(a)is dict:
  need(a.keys()==b.keys(),'keys differ at '+p);return sum((diffs(a[k],b[k],p+'/'+k) for k in a),[])
 if type(a)is list:
  need(len(a)==len(b),'list size differs at '+p);return sum((diffs(x,y,p+'/'+str(i)) for i,(x,y)in enumerate(zip(a,b))),[])
 return [] if a==b else [p]
def ast_paths(manifest):
 need(set(manifest['families'])==set(FAMILIES),'seven families');paths=[];counts=[0,0]
 for family,row in manifest['families'].items():
  for i,group in enumerate(('entries','excluded_helpers')):
   counts[i]+=len(row[group]);paths += ['/families/'+family+'/'+group+'/'+name+'/ast_sha256' for name in row[group]]
 need(counts==[23,21],'all 23 entries and 21 helpers');return sorted(paths)
def runtime_paths(version):
 key={'3.12.14':'312','3.13.5':'313'}[version]
 executable=Path(PYTHONS[key][0]).resolve()
 root=executable.parent.parent/'lib'/('python'+version.rsplit('.',1)[0])
 return str(executable),{name:str(root/relative) for name,relative in {'ast':'ast.py','json':'json/__init__.py','json.encoder':'json/encoder.py','json.decoder':'json/decoder.py','hashlib':'hashlib.py'}.items()}
def verify_worker(value,fixture,expect_mismatch,version):
 need(type(value)is dict and set(value)=={'python','scan','manifest','fixture_equal','changed_coordinates','semantic_mutation_changes_hash','runtime'},'worker schema')
 need(value['python']==version and value['semantic_mutation_changes_hash']is True,'actual interpreter/mutation control')
 need(value['runtime']['executable_sha256']==PYTHONS['312' if version=='3.12.14' else '313'][1],'interpreter binary identity')
 expected_executable,expected_paths=runtime_paths(version)
 need(value['runtime']['executable']==expected_executable,'registered executable path')
 need(type(value['runtime']['stdlib'])is dict and set(value['runtime']['stdlib'])=={'ast','json','json.encoder','json.decoder','hashlib'},'complete critical stdlib identity')
 need(all(type(item)is dict and set(item)=={'path','sha256'} and item['path']==expected_paths[name] for name,item in value['runtime']['stdlib'].items()),'registered stdlib paths before reads')
 need(all(sha(Path(v['path']).read_bytes())==v['sha256'] for v in value['runtime']['stdlib'].values()),'observed stdlib bytes changed')
 expected=ast_paths(fixture) if expect_mismatch else []
 need(sorted(diffs(fixture,value['manifest']))==expected and value['changed_coordinates']==expected,'exact fixture oracle')
 need(value['fixture_equal']is (not expect_mismatch),'fixture result')
 # Independently join the entire fixed scan shape, not only entries present.
 expected_scan={}
 for family,row in value['manifest']['families'].items():
  expected_scan[family]={k:row[k] for k in ('path','source_sha256','excluded_helpers')}
  expected_scan[family]['entries']={name:{k:item[k] for k in ('ast_sha256','signature','docstring')} for name,item in row['entries'].items()}
 need(canonical(value['scan'])==canonical(expected_scan),'exact scan/manifest inventory binding')
 return 'BASELINE_AST_MISMATCH_REPRODUCED' if expect_mismatch else 'EXACT_FIXTURE_MATCH'
def worker(root,skill,docs,vu):
 sys.path.insert(0,str(root));from tools import contract_registry19 as r
 fixture=r.parse((root/'tests/fixtures/contract-registry19.json').read_bytes());scan=r.scan(root);m=r.build_manifest(root,skill,docs,vu.read_bytes())
 tree=ast.parse((root/'tools/sync_contract19.py').read_bytes());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate');mutant=copy.deepcopy(node);mutant.body=[ast.Return(value=ast.Constant(value='SEMANTIC_MUTANT'))]
 fingerprint=(lambda n:canonical(r.canonical_ast(n))) if hasattr(r,'canonical_ast') else (lambda n:ast.dump(n,include_attributes=False).encode())
 changed=sorted(diffs(fixture,m));result=dict(python='.'.join(map(str,sys.version_info[:3])),scan=scan,manifest=m,fixture_equal=not changed,changed_coordinates=changed,semantic_mutation_changes_hash=sha(fingerprint(node))!=sha(fingerprint(mutant)))
 result['runtime']=dict(executable=str(Path(sys.executable).resolve()),executable_sha256=sha(Path(sys.executable).read_bytes()),stdlib={mod.__name__:dict(path=str(Path(mod.__file__).resolve()),sha256=sha(Path(mod.__file__).read_bytes())) for mod in (ast,json,json.encoder,json.decoder,hashlib)})
 print(json.dumps(result,sort_keys=True,ensure_ascii=False));return 42 if changed else 0
if __name__=='__main__':
 need(len(sys.argv)==6 and sys.argv[1]=='--fixed-worker','internal fixed worker arguments');sys.exit(worker(*map(Path,sys.argv[2:])))
