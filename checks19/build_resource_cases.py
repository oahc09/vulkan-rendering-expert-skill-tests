"""Strict resource evidence to local candidate records; never auto-promote."""
import argparse,hashlib,importlib.util,json,pathlib,subprocess,sys,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
OWN=('checks19/build_resource_cases.py','tools/resource_cases19.py')
def require(x,m):
 if not x:raise ValueError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(path):
 def unique(pairs):
  out={}
  for k,v in pairs:
   require(k not in out,'duplicate JSON key');out[k]=v
  return out
 return json.loads(path.read_text(),object_pairs_hook=unique)
def git(root,*a):return subprocess.check_output(['git','-C',str(root),*a],timeout=30)
def checked(rel,head):
 p=ROOT/rel;require(not p.is_symlink() and p.resolve().is_relative_to(ROOT),'source escape');require(p.read_bytes()==git(ROOT,'show',head+':'+rel),'source not at expected commit '+rel)
def load(rel):
 s=importlib.util.spec_from_file_location(pathlib.Path(rel).stem,ROOT/rel);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def build(a):
 require(sha(a.suite/'resource-index.json')==a.expected_index_sha256,'external index digest mismatch');index=parse(a.suite/'resource-index.json')
 require(index['status']=='BOUNDED_RESOURCE_SUITE_VERIFIED' and index['development'] is False,'strict completed suite required');head=a.expected_tests_head;skill=a.expected_skill_head
 require(index['tests_head']==head and index['skill_head']==skill and git(ROOT,'rev-parse','HEAD').decode().strip()==head and git(a.skill_root,'rev-parse','HEAD').decode().strip()==skill,'explicit pair mismatch')
 own_hashes={rel:sha(ROOT/rel) for rel in OWN}
 for rel in OWN:
  if not a.development:checked(rel,head)
 for rel in ('checks19/run_resource_suite.py','checks19/resource_suite19.py'):checked(rel,head)
 # Validate every executed dependency BEFORE importing verifier or rules.
 for rel in index['source_manifest']:checked(rel,head)
 gate=load('checks19/run_resource_suite.py');require(index['source_manifest']==gate.source_manifest(head),'source inventory mismatch');gate.require_complete(index)
 require(not git(a.skill_root,'status','--porcelain','--untracked-files=no'),'Skill dirty');pair=parse(ROOT/'coverage/v1.0.19/pair.json');require(pair['skill_sha']==skill and pair['release_status']=='BLOCKED','pair mismatch')
 t=gate.config(a.toolchain);require(sha(a.toolchain)==index['toolchain_sha256'],'toolchain changed')
 paths=[pathlib.Path(shutil.which('gcc')),pathlib.Path(sys.executable),pathlib.Path(t['loader']),pathlib.Path(t['icd']),pathlib.Path(t['validusage']),pathlib.Path(t['layer_path'])/'VkLayer_khronos_validation.json']+[pathlib.Path(t['tools'])/n for n in ('glslangValidator','spirv-val','spirv-dis')]+list((pathlib.Path(t['include'])/'vulkan').glob('*.h'))
 require(index['tool_hashes']=={str(p):sha(p) for p in paths},'exact tool cohort mismatch')
 require(gate.inventory(a.suite)==index['artifacts'],'suite artifact inventory changed');verifier=load('checks19/resource_suite19.py')
 for f in index['families']:require(f==verifier.verify_family(f['family'],a.suite/f['family'],t),'raw evidence changed')
 helper=load('tools/resource_cases19.py');records=[helper.candidate(index,f,a.expected_index_sha256) for f in gate.FAMILIES]
 require(sha(a.suite/'resource-index.json')==a.expected_index_sha256 and gate.inventory(a.suite)==index['artifacts'] and gate.source_manifest(head)==index['source_manifest'],'evidence/source changed during conversion')
 require(not git(a.skill_root,'status','--porcelain','--untracked-files=no') and git(a.skill_root,'rev-parse','HEAD').decode().strip()==skill and git(ROOT,'rev-parse','HEAD').decode().strip()==head,'pair changed during conversion')
 require(index['tool_hashes']=={str(p):sha(p) for p in paths} and sha(a.toolchain)==index['toolchain_sha256'] and own_hashes=={rel:sha(ROOT/rel) for rel in OWN},'tools/config/converter changed during conversion')
 for record in records:helper.validate(record)
 return {'status':'DEVELOPMENT_CANDIDATES_ONLY' if a.development else 'SANITIZED_CANDIDATES_ONLY','records':records,'notice':'Local authored fixtures only; review is not inferred from execution success. Hashes are integrity not authenticity; no full-release promotion.'}
def verify_failure_commands(index,t,suite,families):
 for step in index['steps']:
  require(step['label'] in families,'unknown executed family');expected=[sys.executable,'-O',str(ROOT/'cases19'/step['label']/'run.py'),'--include',t['include'],'--loader',t['loader'],'--validusage',t['validusage'],'--output',str(suite.resolve()/step['label'])]
  if step['label']!='headless_wsi':expected+=['--tools',t['tools']]
  require(step['argv']==expected,'executed argv differs from fixed family command')
def fail_import(a):
 require(sha(a.suite/'resource-index.json')==a.expected_index_sha256,'external index digest mismatch');index=parse(a.suite/'resource-index.json')
 require(index['status'] in ('CANCELLED','BLOCKED') and index['development'] is False,'strict controlled incomplete suite required');head=a.expected_tests_head;skill=a.expected_skill_head
 require(index['tests_head']==head and index['skill_head']==skill and git(ROOT,'rev-parse','HEAD').decode().strip()==head and git(a.skill_root,'rev-parse','HEAD').decode().strip()==skill,'explicit pair mismatch')
 own_hashes={rel:sha(ROOT/rel) for rel in OWN}
 for rel in OWN:
  if not a.development:checked(rel,head)
 for rel in ('checks19/run_resource_suite.py','checks19/resource_suite19.py'):checked(rel,head)
 # Validate every executed dependency BEFORE importing verifier or rules.
 for rel in index['source_manifest']:checked(rel,head)
 gate=load('checks19/run_resource_suite.py');require(index['source_manifest']==gate.source_manifest(head),'source inventory mismatch')
 require(not git(a.skill_root,'status','--porcelain','--untracked-files=no'),'Skill dirty');pair=parse(ROOT/'coverage/v1.0.19/pair.json');require(pair['skill_sha']==skill and pair['release_status']=='BLOCKED','pair mismatch')
 t=gate.config(a.toolchain);require(sha(a.toolchain)==index['toolchain_sha256'],'toolchain changed')
 verify_failure_commands(index,t,a.suite,gate.FAMILIES)
 paths=[pathlib.Path(shutil.which('gcc')),pathlib.Path(sys.executable),pathlib.Path(t['loader']),pathlib.Path(t['icd']),pathlib.Path(t['validusage']),pathlib.Path(t['layer_path'])/'VkLayer_khronos_validation.json']+[pathlib.Path(t['tools'])/n for n in ('glslangValidator','spirv-val','spirv-dis')]+list((pathlib.Path(t['include'])/'vulkan').glob('*.h'))
 require(index['tool_hashes']=={str(p):sha(p) for p in paths},'exact tool cohort mismatch')
 require(gate.inventory(a.suite)==index['artifacts'],'suite artifact inventory changed');verifier=load('checks19/resource_suite19.py')
 for f in index['families']:require(f==verifier.verify_family(f['family'],a.suite/f['family'],t),'raw evidence changed')
 helper=load('tools/resource_cases19.py');observation=helper.failure_observation(index,a.expected_index_sha256)
 require(sha(a.suite/'resource-index.json')==a.expected_index_sha256 and gate.inventory(a.suite)==index['artifacts'] and gate.source_manifest(head)==index['source_manifest'],'evidence/source changed during conversion')
 require(not git(a.skill_root,'status','--porcelain','--untracked-files=no') and git(a.skill_root,'rev-parse','HEAD').decode().strip()==skill and git(ROOT,'rev-parse','HEAD').decode().strip()==head,'pair changed during conversion')
 require(index['tool_hashes']=={str(p):sha(p) for p in paths} and sha(a.toolchain)==index['toolchain_sha256'] and own_hashes=={rel:sha(ROOT/rel) for rel in OWN},'tools/config/converter changed during conversion')
 require(observation==helper.failure_observation(index,a.expected_index_sha256),'failure observation instability')
 return {'status':'DEVELOPMENT_FAILURE_OBSERVATION' if a.development else 'NON_RECOMMENDABLE_FAILURE_OBSERVATION','record':observation,'notice':'Process cancellation/budget evidence only. Never eligible for candidate review or recommendation.'}
def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='op',required=True);b=sub.add_parser('build')
 for name in ('suite','skill-root','toolchain'):b.add_argument('--'+name,type=pathlib.Path,required=True)
 for name in ('expected-index-sha256','expected-tests-head','expected-skill-head'):b.add_argument('--'+name,required=True)
 b.add_argument('--development',action='store_true')
 f=sub.add_parser('fail-import')
 for name in ('suite','skill-root','toolchain'):f.add_argument('--'+name,type=pathlib.Path,required=True)
 for name in ('expected-index-sha256','expected-tests-head','expected-skill-head'):f.add_argument('--'+name,required=True)
 f.add_argument('--development',action='store_true')
 for op in ('retrieve','transition'):
  q=sub.add_parser(op);q.add_argument('--input',type=pathlib.Path,required=True);q.add_argument('--expected-input-sha256',required=True);q.add_argument('--request',type=pathlib.Path,required=True)
 p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 try:
  require(not a.output.exists(),'fresh output required')
  if a.op=='build':result=build(a)
  elif a.op=='fail-import':result=fail_import(a)
  else:
   head=git(ROOT,'rev-parse','HEAD').decode().strip()
   for rel in OWN:checked(rel,head)
   require(sha(a.input)==a.expected_input_sha256,'external record digest mismatch');helper=load('tools/resource_cases19.py');request_sha=sha(a.request);data=parse(a.input);req=parse(a.request)
   require(data.get('status') not in ('NON_RECOMMENDABLE_FAILURE_OBSERVATION','DEVELOPMENT_FAILURE_OBSERVATION') and 'observation' not in data,'failure observations cannot be reviewed or recommended')
   result=helper.retrieve(data['records'] if 'records' in data else [data],req['scope'],req['now']) if a.op=='retrieve' else helper.transition(data,**req)
   require(sha(a.input)==a.expected_input_sha256 and sha(a.request)==request_sha and git(ROOT,'rev-parse','HEAD').decode().strip()==head,'record/request/head changed during conversion')
   for rel in OWN:checked(rel,head)
  a.output.parent.mkdir(parents=True,exist_ok=True)
  with a.output.open('x') as out:out.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  print(sha(a.output));return 0
 except Exception as e:print('BLOCKED:',str(e),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
