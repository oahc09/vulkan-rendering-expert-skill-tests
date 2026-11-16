"""Fixed upstream class HOST reproducer. Not full engine, GPU, or blind repair."""
import uuid
import hashlib
import json
import pathlib
import shutil
import subprocess
import os
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
HEADER_TREE_SHA256 = '635e119b4680a1a72fce93ff876a170278e73b5872597ebf6961477ef185c636'
FIX = '02d3010a3517620e7eedd919217e169c4a188de3'
PARENT = 'dca8e0842417ef14440135ee48a09870a05d5bff'
SOURCES = {
 'before': {'fence_pool.cpp':'03ad9609ac150e6eefbacd43a2fdaf7ce74f06f3e0f953150f1e3ce59228ff7c','fence_pool.h':'6851e19669e1ec42fe3badb8de276d22699a799d9d874c5f160075ed7903e3f7'},
 'after': {'fence_pool.cpp':'9afd43ff1b20d0cbc3111fbe6184e86a388667d95d52f5412388b38bac295cb3','fence_pool.h':'34bea176d8e5a36ad3a21dbe9642540ffa8a3f9c8c2c46e53d56f30577fc0b5f'}}
OWN = ['tools/external_fence19.py','checks19/run_external_fence_task.py','cases19/external_fence/harness.cpp','cases19/external_fence/stubs/common/helpers.h','cases19/external_fence/stubs/core/device.h']

def sha(data): return hashlib.sha256(data).hexdigest()
def require(ok, message):
 if not ok: raise ValueError(message)
def filehash(p): return sha(pathlib.Path(p).read_bytes())
def source_bytes(repo, label, name):
 require(label in SOURCES and name in SOURCES[label], 'unknown source selector')
 rev = PARENT if label == 'before' else FIX
 raw = subprocess.check_output(['git','-C',str(repo),'show',rev+':framework/'+name], timeout=15)
 require(sha(raw)==SOURCES[label][name], 'upstream source hash mismatch')
 return raw

def expected(fixed):
 m=(1<<64)-1 if fixed else (1<<32)-1
 lines=['empty wait=0 calls=0',f'default timeout={m} result=0 calls=1']
 for i,t in enumerate([0,(1<<32)-1,1<<32,(1<<64)-1],2):
  lines.append(f'explicit timeout={t if fixed else t&0xffffffff} result=0 calls={i}')
 lines.extend([f'result-propagation timeout={m} result=2 calls=6',f'result-propagation timeout={m} result=-4 calls=7','reset-empty no-extra-wait'])
 return '\n'.join(lines)+'\n'

def verify_output(label, mode, code, stdout, stderr):
 require(type(code) is int, 'exit code type')
 if mode=='invalid':
  require(label=='after' and code==2 and stdout=='' and stderr=='INVALID_MODE\n','invalid-mode control')
 elif label=='before' and mode=='fixed':
  require(code==6 and stdout=='empty wait=0 calls=0\ndefault timeout=4294967295 result=0 calls=1\n' and stderr=='ORACLE_MISMATCH\n','historical fixed oracle control')
 else:
  require((label,mode) in [('before','old'),('after','fixed')], 'unknown run selector')
  require(code==0 and stdout==expected(label=='after') and stderr=='','behavior output mismatch')

def git_state(repo):
 return {'head':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True,timeout=15).strip(),
         'porcelain':subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True,timeout=15).splitlines()}

def verify_parent(repo):
 parent=subprocess.check_output(['git','-C',str(repo),'rev-parse',FIX+'^'],text=True,timeout=15).strip()
 require(parent==PARENT,'upstream parent mismatch')

def run(repo, headers, out, run_id=None):
 run_id=str(uuid.uuid4()) if run_id is None else run_id
 if not isinstance(run_id,str) or str(uuid.UUID(run_id))!=run_id:raise ValueError('canonical run UUID required')
 repo=pathlib.Path(repo).resolve();headers=pathlib.Path(headers).resolve();out=pathlib.Path(out)
 require(not out.exists(),'output must be fresh')
 require((headers/'vulkan/vulkan_core.h').is_file(),'official headers missing')
 compiler=pathlib.Path(shutil.which('g++') or '/nonexistent').resolve()
 require(compiler.is_file(),'g++ missing')
 before={p:filehash(ROOT/p) for p in OWN}
 # Capture the complete header tree actually available to the include path.
 header_hashes={p.relative_to(headers).as_posix():filehash(p) for p in sorted(headers.rglob('*.h'))}
 require(sha(json.dumps(header_hashes,sort_keys=True,separators=(',',':')).encode())==HEADER_TREE_SHA256,'official header cohort mismatch')
 toolhash=filehash(compiler)
 verify_parent(repo)
 raw={(label,n):source_bytes(repo,label,n) for label in SOURCES for n in SOURCES[label]}
 provenance={'tests':git_state(ROOT),'skill':git_state(pathlib.Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))),'pair_file_sha256':filehash(ROOT/'coverage/v1.0.19/pair.json'),'pair':json.loads((ROOT/'coverage/v1.0.19/pair.json').read_text()),'release_status':'BLOCKED','interpretation':'Executed implementation hashes are authoritative; dirty/untracked state is explicit, not a committed release claim.'}
 out.mkdir(parents=True)
 report={'schema':1,'run_id':run_id,'output_root':str(out.resolve()),'status':'BLOCKED','scope':'Unmodified complete upstream FencePool class with explicit Device/helpers and Vulkan-call HOST test doubles. No GPU wait, driver, full engine build, or blind repair. VK_ERROR_DEVICE_LOST here is a supplied return value, not actual device loss.', 'upstream':{'repository':'KhronosGroup/Vulkan-Samples','before':PARENT,'after':FIX,'source_sha256':SOURCES},'implementation_sha256':before,'compiler_sha256':toolhash,'header_tree_sha256':header_hashes,'runs':{},'steps':[],'provenance':provenance}
 def execute(argv, prefix, timeout):
  start=time.monotonic()
  step={'label':prefix,'argv':argv,'timeout_seconds':timeout,'start_monotonic':start}
  try:
   p=subprocess.run(argv,capture_output=True,timeout=timeout)
   step.update(returncode=p.returncode,timed_out=False)
   stdout,stderr=p.stdout,p.stderr
  except subprocess.TimeoutExpired as e:
   stdout,stderr=e.stdout or b'',e.stderr or b''
   step.update(returncode=None,timed_out=True)
   raise
  finally:
   step['end_monotonic']=time.monotonic()
   if 'stdout' in locals():
    (out/(prefix+'.stdout')).write_bytes(stdout);(out/(prefix+'.stderr')).write_bytes(stderr)
    step.update(stdout_sha256=sha(stdout),stderr_sha256=sha(stderr))
   report['steps'].append(step)
  return p

 try:
  version=execute([str(compiler),'--version'],'compiler-version',10)
  require(version.returncode==0,'compiler version failed')
  for label in SOURCES:
   d=out/label;d.mkdir()
   for n in SOURCES[label]: (d/n).write_bytes(raw[label,n])
   cmd=[str(compiler),'-std=c++17','-Wall','-Wextra','-I'+str(d),'-I'+str(ROOT/'cases19/external_fence/stubs'),'-I'+str(headers),str(d/'fence_pool.cpp'),str(ROOT/'cases19/external_fence/harness.cpp'),'-o',str(d/'test')]
   c=execute(cmd,label+'/compile',60);require(c.returncode==0,'compile failed '+label)
   mode='old' if label=='before' else 'fixed'
   p=execute([str(d/'test'),mode],label+'/run',10)
   verify_output(label,mode,p.returncode,p.stdout.decode(),p.stderr.decode())
   report['runs'][label]={'mode':mode,'exit_code':p.returncode,'binary_sha256':filehash(d/'test')}
  for label,mode,key in [('before','fixed','historical-fixed-oracle'),('after','invalid','invalid-mode')]:
   p=execute([str(out/label/'test'),mode],key,10)
   verify_output(label,mode,p.returncode,p.stdout.decode(),p.stderr.decode())
   report['runs'][key]={'mode':mode,'exit_code':p.returncode}
  require(before=={p:filehash(ROOT/p) for p in OWN},'implementation changed')
  require(header_hashes=={p.relative_to(headers).as_posix():filehash(p) for p in sorted(headers.rglob('*.h'))},'headers changed')
  require(filehash(compiler)==toolhash,'compiler changed')
  for label in SOURCES:
   for n in SOURCES[label]: require(source_bytes(repo,label,n)==raw[label,n] and filehash(out/label/n)==SOURCES[label][n], 'source changed')
  report['status']='VERIFIED_EXTERNAL_CLASS_HOST_REPRODUCTION'
 except Exception as e:
  report['failure_type']=type(e).__name__
  raise
 finally:
  report['artifacts']={p.relative_to(out).as_posix():filehash(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'report.json'}
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 return report
