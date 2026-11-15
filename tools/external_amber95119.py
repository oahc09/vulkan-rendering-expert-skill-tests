"""Pinned external Amber #951 GPU replay, not a generic test/command runner."""
import hashlib,json,os,pathlib,re,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST='948c2f1a10e3269b2742fa4f046a420a510e11d9a2c1cc76c0de0a7ef2fc58f7'
BEFORE='aaac58d5009e8f6b33e2723258dc1542854d09a4'
AFTER='8c3bfef40c2387944fdc81746e2e3249e4da5566'
SCOPE='Full upstream Amber runtime/CLI, original test, common modern dependencies, software Vulkan. Known historical fix, not blind solve/full CTS/full release. Old failure is output aggregation before EXPECT, not numerical EXPECT failure. Warnings and historical cleanup errors retained; not a zero-diagnostic or SyncVal proof.'
RUNTIME_LIBS={'libvulkan_lvp.so':'0004262f4dc95585492d55925face67a79a7c869ad8760b42ae01bd0bdb807a2','libVkLayer_khronos_validation.so':'25002892d69ff2719fdd7a92a454a15c2d271a17186bc70b625aafaf2df49a05'}
OWN=['tools/external_amber95119.py','checks19/run_external_amber951.py']
def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def fh(p):return sha(pathlib.Path(p).read_bytes())
def unique(pairs):
 d={}
 for k,v in pairs:
  require(k not in d,'duplicate JSON key');d[k]=v
 return d

def local(root,rel):
 require(isinstance(rel,str) and not pathlib.PurePosixPath(rel).is_absolute() and '..' not in pathlib.PurePosixPath(rel).parts,'unsafe artifact path')
 p=root/rel
 require(p.resolve().is_relative_to(root.resolve()),'artifact escape')
 return p

def verify_artifacts(root):
 p=root/'amber951-build-support/final-manifest.json';raw=p.read_bytes()
 require(sha(raw)==MANIFEST,'manifest mismatch')
 m=json.loads(raw,object_pairs_hook=unique)
 require(m['upstream']['before']['commit']==BEFORE and m['upstream']['after']['commit']==AFTER,'commit mismatch')
 for rel,digest in m['execution_inputs'].items():require(fh(local(root,rel))==digest,'input changed: '+rel)
 for label in ('before','after'):
  for rel,digest in m['upstream'][label]['tracked_sha256'].items():require(fh(local(root,f'amber951-{label}-src/'+rel))==digest,'upstream source changed')
 for path,digest in m['external_tool_hashes'].items():require(fh(path)==digest,'external tool changed')
 for name,digest in RUNTIME_LIBS.items():require(fh(pathlib.Path(m['environment']['LD_LIBRARY_PATH'])/name)==digest,'runtime library changed')
 return m

def verify_result(name,code,out,err):
 require(type(code)is int,'invalid exit type')
 require(out.count('90: ComputeCommand')==1 and out.count('Summary:')==1,'compute/summary cardinality')
 require(err.count('[WARNING]')==1 and 'Image Type operand of OpTypeSampledImage should not have a Dim of Buffer.' in err,'driver warning cohort changed')
 if name in ('before','rollback'):
  require(code==1 and out.count('90: ComputeCommand')==1 and 'ProbeSSBOCommand' not in out and 'Summary: 0 pass, 1 fail' in out,'historical execution mismatch')
  require(err.count('output buffer is not empty')==1 and err.count('[ERROR]')==2 and err.count('VUID-vkDestroyDevice-device-05137')==2,'historical runtime/cleanup mismatch')
 elif name=='after':
  require(code==0 and all(out.count(f'{n}: ProbeSSBOCommand')==1 for n in (92,93,94)) and out.count('ProbeSSBOCommand')==3 and 'Summary: 1 pass, 0 fail' in out,'fixed original oracle mismatch')
  require('[ERROR]' not in err and 'Verifier failed' not in err,'fixed unexpected error')
 elif name=='wrong-expect':
  require(code==1 and out.count('92: ProbeSSBOCommand')==1 and out.count('ProbeSSBOCommand')==1 and 'Summary: 0 pass, 1 fail' in out,'mutant did not execute verifier')
  require(err.count('Verifier failed: 2.000000 == 3.000000, at index 0')==1 and '[ERROR]' not in err,'mutant oracle mismatch')
 else:raise ValueError('unknown case')
 # Any new normative diagnosis must be investigated, not silently accepted.
 ids=set(re.findall(r'VUID-[A-Za-z0-9_-]+',err))
 require(ids==({'VUID-vkDestroyDevice-device-05137'} if name in ('before','rollback') else set()),'unexpected VUID')

def provenance_state():
 def state(repo):
  return {'head':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True,timeout=15).strip(),'porcelain':subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True,timeout=15).splitlines()}
 return {'tests':state(ROOT),'skill':state(pathlib.Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))),'pair':json.loads((ROOT/'coverage/v1.0.19/pair.json').read_text()),'pair_sha256':fh(ROOT/'coverage/v1.0.19/pair.json'),'interpretation':'Explicit dirty/untracked state and implementation hashes; no committed release claim.'}

def run(root,out,timeout=30):
 root=pathlib.Path(root).resolve();out=pathlib.Path(out)
 require(type(timeout)is int and 1<=timeout<=120,'timeout outside 1..120')
 require(not out.exists() and not out.is_symlink(),'output must be fresh')
 m=verify_artifacts(root);own={p:fh(ROOT/p) for p in OWN}
 # Deliberate clean child environment. No inherited LD_PRELOAD/VK overrides.
 env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C',**m['environment']}
 require(set(m['environment'])=={'VK_DRIVER_FILES','VK_LAYER_PATH','LD_LIBRARY_PATH','MESA_SHADER_CACHE_DISABLE'},'unexpected environment schema')
 provenance=provenance_state()
 out.mkdir(parents=True)
 report={'schema':1,'status':'BLOCKED','release_status':'BLOCKED','scope':SCOPE,'fixed_manifest_sha256':MANIFEST,'implementation_sha256':own,'source_commits':{'before':BEFORE,'after':AFTER},'steps':[],'environment':env,'runtime_library_sha256':RUNTIME_LIBS,'provenance':provenance}
 try:
  for name,v,case in [('before','before','original.amber'),('after','after','original.amber'),('rollback','before','original.amber'),('wrong-expect','after','wrong-expect.amber')]:
   exe=local(root,f'amber951-{v}-build/amber/amber');inp=local(root,'amber951-build-support/'+case)
   argv=[str(exe),'-D','0','-v','1.2','--log-execute-calls',str(inp)]
   step={'name':name,'argv':argv,'binary_sha256':fh(exe),'input_sha256':fh(inp),'timeout_seconds':timeout,'start_monotonic':time.monotonic()}
   stdout=stderr=None
   try:
    p=subprocess.run(argv,env=env,capture_output=True,timeout=timeout)
    stdout,stderr=p.stdout,p.stderr;step.update(exit_code=p.returncode,timed_out=False)
   except subprocess.TimeoutExpired as e:
    stdout,stderr=e.stdout or b'',e.stderr or b'';step.update(exit_code=None,timed_out=True);raise
   finally:
    step['end_monotonic']=time.monotonic()
    if stdout is not None:
     (out/(name+'.stdout')).write_bytes(stdout);(out/(name+'.stderr')).write_bytes(stderr);step.update(stdout_sha256=sha(stdout),stderr_sha256=sha(stderr))
    report['steps'].append(step)
   verify_result(name,p.returncode,stdout.decode(),stderr.decode())
  verify_artifacts(root);require(own=={p:fh(ROOT/p) for p in OWN},'implementation changed')
  report['status']='ORIGINAL_EXTERNAL_GPU_REGRESSION_REPRODUCED'
 except Exception as e:
  report['failure_type']=type(e).__name__;raise
 finally:
  report['artifacts']={p.name:fh(p) for p in out.iterdir() if p.is_file() and p.name!='report.json'}
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 return report
