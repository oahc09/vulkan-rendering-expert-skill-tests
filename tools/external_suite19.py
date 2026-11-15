"""Independent child evidence gates; imported only after suite source checks."""
import json,pathlib,shutil,uuid
from tools import external_fence19 as f,external_amber95119 as a,external_related19 as r
TASKS=('fence_host','amber_gpu','related_gpu')
def inventory(root):
 a.require(not root.is_symlink(),'artifact symlink');out={}
 for p in root.rglob('*'):
  a.require(not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),'artifact escape')
  if p.is_file() and p!=root/'report.json':out[p.relative_to(root).as_posix()]=a.fh(p)
 return out
def read_report(root):
 files=inventory(root);p=root/'report.json';a.require(not p.is_symlink(),'report symlink')
 d=json.loads(p.read_text(),object_pairs_hook=a.unique);a.require(d['artifacts']==files,'child artifact inventory mismatch');return d

def report_identity(d,root,run_id):
 a.require(isinstance(run_id,str) and str(uuid.UUID(run_id))==run_id,'expected child UUID')
 a.require(d['run_id']==run_id and d['output_root']==str(root.resolve()),'old/copied child report identity')

def provenance(d,config):
 p=d['provenance']
 for name in ('tests','skill'):
  a.require(p[name]['head']==config['_expected_'+name+'_head'] and p[name]['porcelain']==[],'child provenance head/dirty mismatch')
 a.require(p.get('pair_sha256',p.get('pair_file_sha256'))==config['_expected_pair_sha256'],'child pair digest mismatch')
 a.require(p['pair']==json.loads((a.ROOT/'coverage/v1.0.19/pair.json').read_text()),'child pair contents mismatch')

def environment(d,base):
 m=a.verify_artifacts(base)
 a.require(d['environment']=={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C',**m['environment']},'child environment mismatch')

def verify_fence(root,config,run_id):
 d=read_report(root);report_identity(d,root,run_id);a.require(d['status']=='VERIFIED_EXTERNAL_CLASS_HOST_REPRODUCTION','fence status');provenance(d,config)
 a.require(d['implementation_sha256']=={p:a.fh(a.ROOT/p) for p in f.OWN},'fence implementation mismatch')
 a.require(d['upstream']['source_sha256']==f.SOURCES and d['upstream']['before']==f.PARENT and d['upstream']['after']==f.FIX,'fence commits')
 headers=pathlib.Path(config['headers']);hh={p.relative_to(headers).as_posix():a.fh(p) for p in sorted(headers.rglob('*.h'))}
 a.require(d['header_tree_sha256']==hh and a.sha(json.dumps(hh,sort_keys=True,separators=(',',':')).encode())==f.HEADER_TREE_SHA256,'header cohort')
 compiler=pathlib.Path(shutil.which('g++',path='/usr/bin:/bin')).resolve();a.require(d['compiler_sha256']==a.fh(compiler),'fence compiler')
 order=['compiler-version','before/compile','before/run','after/compile','after/run','historical-fixed-oracle','invalid-mode']
 a.require([s['label'] for s in d['steps']]==order,'fence step order')
 expected={x+'.'+stream for x in order for stream in ('stdout','stderr')}|{label+'/'+name for label in ('before','after') for name in ('fence_pool.cpp','fence_pool.h','test')}
 a.require(set(d['artifacts'])==expected,'fence unexpected artifacts')
 for step in d['steps']:
  label=step['label'];a.require(step['timed_out'] is False and type(step['returncode'])is int,'fence step invalid')
  for stream in ('stdout','stderr'):a.require(step[stream+'_sha256']==a.fh(root/(label+'.'+stream)),'fence log hash')
  if label in ('compiler-version','before/compile','after/compile'):a.require(step['returncode']==0,'fence build failure')
 for label,mode,prefix in [('before','old','before/run'),('after','fixed','after/run'),('before','fixed','historical-fixed-oracle'),('after','invalid','invalid-mode')]:
  step=next(s for s in d['steps'] if s['label']==prefix)
  a.require(step['argv']==[str(root/label/'test'),mode],'fence fixed invocation')
  f.verify_output(label,mode,step['returncode'],(root/(prefix+'.stdout')).read_text(),(root/(prefix+'.stderr')).read_text())
 for label in f.SOURCES:
  for name in f.SOURCES[label]:a.require((root/label/name).read_bytes()==f.source_bytes(config['fence_repo'],label,name),'fence upstream bytes')
  a.require(d['runs'][label]['binary_sha256']==a.fh(root/label/'test'),'fence binary')
  cmd=[str(compiler),'-std=c++17','-Wall','-Wextra','-I'+str(root/label),'-I'+str(a.ROOT/'cases19/external_fence/stubs'),'-I'+str(headers),str(root/label/'fence_pool.cpp'),str(a.ROOT/'cases19/external_fence/harness.cpp'),'-o',str(root/label/'test')]
  a.require(next(s for s in d['steps'] if s['label']==label+'/compile')['argv']==cmd,'fence compile invocation')
 return {'task':'fence_host','classification':'ORIGINAL_CLASS_HOST_TEST_DOUBLE','original_bugs':1,'gpu_executed':False,'report_sha256':a.fh(root/'report.json')}

def verify_amber(root,config,run_id):
 d=read_report(root);report_identity(d,root,run_id);a.require(d['status']=='ORIGINAL_EXTERNAL_GPU_REGRESSION_REPRODUCED','amber task classification');provenance(d,config);base=pathlib.Path(config['artifact_root']);environment(d,base)
 a.require(d['source_commits']=={'before':a.BEFORE,'after':a.AFTER},'amber commits')
 a.require(d['runtime_library_sha256']==a.RUNTIME_LIBS,'amber runtime identities')
 a.require(d['status']=='ORIGINAL_EXTERNAL_GPU_REGRESSION_REPRODUCED' and d['fixed_manifest_sha256']==a.MANIFEST,'amber status/manifest')
 a.require(d['implementation_sha256']=={p:a.fh(a.ROOT/p) for p in a.OWN},'amber implementation')
 order=[('before','before','original.amber'),('after','after','original.amber'),('rollback','before','original.amber'),('wrong-expect','after','wrong-expect.amber')]
 a.require([s['name'] for s in d['steps']]==[x[0] for x in order],'amber steps')
 a.require(set(d['artifacts'])=={x[0]+'.'+stream for x in order for stream in ('stdout','stderr')},'amber unexpected artifacts')
 for s,(name,v,case) in zip(d['steps'],order):
  cmd=[str(base/f'amber951-{v}-build/amber/amber'),'-D','0','-v','1.2','--log-execute-calls',str(base/'amber951-build-support'/case)]
  a.require(s['argv']==cmd and s['timed_out'] is False and s['input_sha256']==a.fh(cmd[-1]) and s['binary_sha256']==a.fh(cmd[0]),'amber input/invocation')
  for stream in ('stdout','stderr'):a.require(s[stream+'_sha256']==a.fh(root/(name+'.'+stream)),'amber log hash')
  a.verify_result(name,s['exit_code'],(root/(name+'.stdout')).read_text(),(root/(name+'.stderr')).read_text())
 return {'task':'amber_gpu','classification':'ORIGINAL_ENGINE_SOFTWARE_VULKAN_BUG','original_bugs':1,'gpu_executed':True,'report_sha256':a.fh(root/'report.json')}

def verify_related(root,config,run_id):
 d=read_report(root);report_identity(d,root,run_id);base=pathlib.Path(config['artifact_root']);r.verify_inputs(base)
 a.require(d['source_commits']=={'before':a.BEFORE,'after':a.AFTER},'related commits')
 a.require(d['status']=='RELATED_ORIGINAL_REGRESSIONS_PASSED' and d['manifest_sha256']==a.MANIFEST,'related status');provenance(d,config);environment(d,base)
 a.require(d['implementation_sha256']=={p:a.fh(a.ROOT/p) for p in r.OWN},'related implementation')
 a.require([(s['case'],s['variant']) for s in d['steps']]==r.ORDER,'related step order')
 a.require(set(d['artifacts'])=={str(i)+'.'+stream for i in range(6) for stream in ('stdout','stderr')},'related unexpected artifacts')
 for i,(s,(case,v)) in enumerate(zip(d['steps'],r.ORDER)):
  cmd=r.argv(base,case,v);a.require(s['argv']==cmd and s['timed_out'] is False and s['source_sha256']==r.CASES[case][0] and s['binary_sha256']==a.fh(cmd[0]),'related source/invocation')
  for stream in ('stdout','stderr'):a.require(s[stream+'_sha256']==a.fh(root/f'{i}.{stream}'),'related raw hash')
  r.verify_result(case,s['returncode'],(root/f'{i}.stdout').read_text(),(root/f'{i}.stderr').read_text())
 return {'task':'related_gpu','classification':'ORIGINAL_NEIGHBOR_REGRESSIONS_NOT_NEW_BUGS','original_bugs':0,'gpu_executed':True,'regression_executions':6,'report_sha256':a.fh(root/'report.json')}
def verify(task,root,config,run_id):
 a.require(task in TASKS,'unknown task');return {'fence_host':verify_fence,'amber_gpu':verify_amber,'related_gpu':verify_related}[task](root,config,run_id)
