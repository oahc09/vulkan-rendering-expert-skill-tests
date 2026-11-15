#!/usr/bin/env python3
"""Execute unchanged CORE17 gate in its independent exact pair; never merge pins."""
import argparse,hashlib,json,os,re,subprocess,sys
from pathlib import Path
MANIFEST=Path(__file__).resolve().parents[1]/'core17-dependency-manifest.json'
def git(root,*args):
 return subprocess.check_output(['git','-C',str(root),*args],text=True,stderr=subprocess.DEVNULL,timeout=30).strip()
def manifest(path=MANIFEST):
 c=json.loads(Path(path).read_text())
 for k in ('tests_sha','skill_sha','tests_base_sha'):
  if not re.fullmatch('[0-9a-f]{40}',c[k]):raise ValueError('immutable SHA required')
 for k in ('contract_sha256','gate_sha256'):
  if not re.fullmatch('[0-9a-f]{64}',c[k]):raise ValueError('immutable file digest required')
 if c['tests_repository']!='oahc09/vulkan-rendering-expert-skill-tests' or c['skill_repository']!='oahc09/vulkan-rendering-expert-skill':raise ValueError('repository scope mismatch')
 if c['schema']!=1 or c['cohort']!='core17' or c['release_status']!='BLOCKED' or c['equivalent_reuse']!=0 or c['partial_legacy_links']!=6:raise ValueError('dependency scope mismatch')
 return c

def inspect(skill,tests,c):
 for root,key in ((skill,'skill_sha'),(tests,'tests_sha')):
  if git(root,'rev-parse','HEAD')!=c[key]:raise ValueError('wrong exact '+key)
  if git(root,'rev-parse','--is-shallow-repository')!='false':raise ValueError('shallow history')
  if git(root,'status','--porcelain','--untracked-files=all','--ignore-submodules=none'):raise ValueError('dirty checkout')
  if any(x and (x[0].islower() or x[0]=='S') for x in git(root,'ls-files','-v').splitlines()):raise ValueError('hidden index flags')
  if any(x.startswith('160000 ') for x in git(root,'ls-files','--stage').splitlines()):raise ValueError('unverified submodule')
 git(tests,'cat-file','-e',c['tests_base_sha']+'^{commit}')
 p=subprocess.run(['git','-C',str(tests),'merge-base','--is-ancestor',c['tests_base_sha'],c['tests_sha']],capture_output=True,timeout=30)
 if p.returncode!=0:raise ValueError('base ancestry not proven')
 for name,key in [('core17-candidate-contract.json','contract_sha256'),('tests/run_versioned_gate.py','gate_sha256')]:
  path=Path(tests)/name
  if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=c[key]:raise ValueError('original source digest mismatch')
 contract=json.loads((Path(tests)/'core17-candidate-contract.json').read_text())
 for key in ('skill_sha','tests_base_sha','release_status','equivalent_reuse','partial_legacy_links'):
  if contract[key]!=c[key]:raise ValueError('original contract mismatch')
 if contract['candidate_version']!='1.0.17-reconstructed-tests':raise ValueError('original cohort mismatch')
 return dict(pair_status='PASS',tests_sha=c['tests_sha'],skill_sha=c['skill_sha'],tests_base_sha=c['tests_base_sha'],scope=c['scope'],release_status='BLOCKED',equivalent_reuse=0,partial_legacy_links=6)

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--skill',type=Path);p.add_argument('--tests',type=Path);p.add_argument('--resolve',choices=['tests_sha','skill_sha']);p.add_argument('--output',type=Path)
 a=p.parse_args(argv);c=manifest()
 if a.resolve:print(c[a.resolve]);return 0
 if not a.skill or not a.tests:p.error('--skill and --tests required')
 if a.output and a.output.exists():raise ValueError('existing output')
 result=inspect(a.skill,a.tests,c)
 env=dict(os.environ,VULKAN_SKILL_ROOT=str(a.skill.resolve()))
 # No imports/test selection rewrites: execute the pinned original version-scoped gate.
 r=subprocess.run([sys.executable,str(a.tests.resolve()/'tests/run_versioned_gate.py'),'--cohort','core17','--skill',str(a.skill.resolve())],env=env,timeout=360)
 # Audit again after tests so tracked modifications cannot masquerade as an exact run.
 inspect(a.skill,a.tests,c)
 result.update(status='DEPENDENCY_STATIC_PAIR_PASS' if r.returncode==0 else 'DEPENDENCY_STATIC_PAIR_FAIL',gate_exit=r.returncode,semantic_acceptance='UNVERIFIED',merged_into_text18=False)
 if a.output:a.output.write_text(json.dumps(result,indent=2))
 print(json.dumps(result,indent=2));return 0 if r.returncode==0 else 1
if __name__=='__main__':raise SystemExit(main())
