#!/usr/bin/env python3
"""Run the compiled fixture without changing machines, installing tools or claiming mobile evidence."""
import argparse,hashlib,json,os,pathlib,statistics,subprocess,time
p=argparse.ArgumentParser()
p.add_argument('--build',type=pathlib.Path,required=True)
p.add_argument('--out',type=pathlib.Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=pathlib.Path(__file__).resolve().parent
repo=root.parents[2]
sha=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
dirty=subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip()
sha256=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
manifest={'layer':'VulkanIntegration','source_sha':sha,'source_dirty':bool(dirty),
 'binary_sha256':sha256(a.build/'engine_scale_lab'),'fixture_files':{str(f.relative_to(root)):sha256(f) for f in sorted(root.rglob('*')) if f.is_file() and 'build' not in f.relative_to(root).parts},
 'environment':{k:os.environ.get(k) for k in ['VK_ICD_FILENAMES','VK_LAYER_PATH','VK_LAYER_ENABLES']},
 'mobile_status':'NOT_RUN','performance_claim':'Diagnostic synchronized correctness run includes readbacks; no speedup or thermal claim',
 'runs':[]}
try:
 for name,args in [('host',['host_contracts']),('1k',['engine_scale_lab','--instances','1000']),('10k',['engine_scale_lab','--instances','10000']),('100k',['engine_scale_lab','--instances','100000']),('forced-low',['engine_scale_lab','--instances','1000','--force-low'])]:
  cmd=[str(a.build/args[0]),*args[1:]]
  if name!='host':cmd+=['--shaders',str(a.build/'shaders'),'--artifacts',str(a.out/(name+'-images'))]
  start=time.monotonic()
  with (a.out/(name+'.jsonl')).open('w') as stdout,(a.out/(name+'.stderr')).open('w') as stderr:
   result=subprocess.run(cmd,stdout=stdout,stderr=stderr,timeout=600,check=False)
  rows=[json.loads(line) for line in (a.out/(name+'.jsonl')).read_text().splitlines() if line.startswith('{')]
  status='PASS' if result.returncode==0 and rows and rows[-1].get('status')=='PASS' else 'FAIL'
  timings=[r['host_wall_ms_with_readbacks'] for r in rows if 'host_wall_ms_with_readbacks' in r]
  rec={'name':name,'command':cmd,'exit_code':result.returncode,'status':status,'elapsed_seconds':time.monotonic()-start,'stdout_sha256':sha256(a.out/(name+'.jsonl')),'stderr_sha256':sha256(a.out/(name+'.stderr')),'device':next((r for r in rows if 'device' in r),None)}
  if timings:
   values=sorted(timings);rec['diagnostic_mixed_path_wall_ms']={'p50':statistics.median(values),'p95':values[min(len(values)-1,int(len(values)*.95))],'p99':values[min(len(values)-1,int(len(values)*.99))],'not_fair_performance_comparison':True}
  manifest['runs'].append(rec)
  if status!='PASS':raise RuntimeError('Failed '+name+'; original output retained')
 manifest['status']='PASS'
except Exception as exc:
 manifest['status']='FAIL';manifest['error']=str(exc)
finally:
 manifest['artifacts']={str(f.relative_to(a.out)):sha256(f) for f in sorted(a.out.rglob('*')) if f.is_file()}
 (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'status':manifest['status'],'runs':[{k:r[k] for k in ['name','status','exit_code']} for r in manifest['runs']]}))
raise SystemExit(manifest['status']!='PASS')
