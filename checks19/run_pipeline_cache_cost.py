#!/usr/bin/env python3
"""Actual CPU-ICD cache persistence/creation observation, not a speedup benchmark."""
import argparse,hashlib,json,os,subprocess,sys,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import pipeline_cache_decision19 as rule,pipeline_cache_prose19 as prose
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(c,s):
 if not c:raise ValueError(s)
def read_json(raw):
 def pairs(items):
  d={}
  for k,v in items:
   if k in d:raise ValueError('duplicate JSON key')
   d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def provenance():
 result={}
 for name,path in [('tests',ROOT),('skill',Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill')))]:
  result[name]={}
  for key,args in [('head',['rev-parse','HEAD']),('dirty',['status','--porcelain'])]:
   p=subprocess.run(['git','-C',str(path),*args],capture_output=True,text=True)
   result[name][key]=p.stdout.strip() if p.returncode==0 else None
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('tools','include','loader','icd','libdir','pipelines','out'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--policy',type=Path);p.add_argument('--measurement',type=Path)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);src=ROOT/'cases19/pipeline_cost'
 env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','VK_DRIVER_FILES':str(a.icd.resolve()),'LD_LIBRARY_PATH':str(a.libdir.resolve()),'MESA_SHADER_CACHE_DISABLE':'true'}
 report=dict(provenance=provenance(),status='BLOCKED',run_id=str(uuid.uuid4()),steps=[],environment=env,limitations=['No queue submission, output verification, first/steady frame or GPU timestamps.','Sequential CPU API intervals not comparable cold/warm performance; implicit driver caches may apply.','No Validation layer enabled; successful calls do not certify all Vulkan validity.'])
 sources=[src/'cache_probe.c',src/'noop.comp',Path(__file__),Path(rule.__file__),Path(prose.__file__)]
 before={str(x.relative_to(ROOT)):sha(x) for x in sources};report['source_sha256']=before
 toolpaths={'gcc':Path('/usr/bin/gcc'),'glslangValidator':a.tools/'glslangValidator','spirv-val':a.tools/'spirv-val','spirv-dis':a.tools/'spirv-dis','loader':a.loader,'vulkan_core.h':a.include/'vulkan/vulkan_core.h','icd_manifest':a.icd}
 icd=json.loads(a.icd.read_text())['ICD']['library_path'];icdlib=Path(icd) if Path(icd).is_absolute() else a.libdir/icd
 toolpaths['icd_library']=icdlib
 toolhash={k:sha(v) for k,v in toolpaths.items()};report['tool_sha256']=toolhash
 headers={str(p.relative_to(a.include)):sha(p) for p in sorted((a.include/'vulkan').rglob('*.h'))};report['headers_sha256']=headers
 policy_bytes=a.policy.read_bytes() if a.policy else None;measurement_bytes=a.measurement.read_bytes() if a.measurement else None
 def step(name,cmd):
  cmd=list(map(str,cmd));r=subprocess.run(cmd,env=env,capture_output=True,timeout=60)
  (a.out/(name+'.stdout')).write_bytes(r.stdout);(a.out/(name+'.stderr')).write_bytes(r.stderr)
  report['steps'].append(dict(name=name,argv=cmd,exit_code=r.returncode,stdout_sha256=sha(a.out/(name+'.stdout')),stderr_sha256=sha(a.out/(name+'.stderr'))))
  require(r.returncode==0,'step failed '+name);return r
 try:
  report['prose']=prose.extract(a.pipelines.read_bytes())
  for k in ('gcc','glslangValidator','spirv-val','spirv-dis'):step(k+'-version',[toolpaths[k],'--version'])
  spv=a.out/'noop.spv';asm=a.out/'noop.spvasm';exe=a.out/'probe';blobpath=a.out/'cache.bin'
  step('shader-compile',[toolpaths['glslangValidator'],'-V','--target-env','vulkan1.0',src/'noop.comp','-o',spv]);step('shader-val',[toolpaths['spirv-val'],'--target-env','vulkan1.0',spv]);step('shader-dis',[toolpaths['spirv-dis'],spv,'-o',asm])
  step('compile',[toolpaths['gcc'],'-std=c11','-Wall','-Wextra','-Werror','-I'+str(a.include),src/'cache_probe.c',a.loader,'-o',exe])
  r=step('observe',[exe,spv,blobpath]);obs=read_json(r.stdout);report['observation']=obs
  require(obs['status']=='CACHE_ROUNDTRIP_CREATED' and obs['device_type']==4 and obs['api']>>29==0 and obs['gpu_work_submitted'] is False and obs['performance_comparison_valid'] is False and obs['cache_hit_observed'] is False,'actual scope')
  require(r.stderr==b'','unexpected stderr');blob=blobpath.read_bytes();require(obs['cache_bytes']==len(blob),'actual export size')
  for k in ('empty_cache_create_cpu_ns','restored_cache_create_cpu_ns'):require(type(obs[k]) is int and obs[k]>=0,'CPU call interval')
  device=dict(vendor_id=obs['vendor_id'],device_id=obs['device_id'],driver_version=obs['driver'],pipeline_cache_uuid=obs['pipeline_cache_uuid'])
  lineage=dict(producer='vkGetPipelineCacheData',sha256=sha(blobpath),bytes=len(blob),device=device,complete_export=True,unmodified=True,source_record_sha256=sha(a.out/'observe.stdout'))
  admission=rule.inspect_cache(blob,device,lineage);require(admission['reuse'] is True,'actual cache filter')
  report.update(cache_lineage=lineage,cache_admission=admission,artifacts={p.name:sha(p) for p in (spv,asm,exe,blobpath)})
  negatives=[]
  for name,offset in [('header-version',4),('vendor',8),('device',12),('uuid',16)]:
   changed=bytearray(blob);changed[offset]^=1
   # Coordinated hash update tests header gate independently, never sends mutated data to Vulkan.
   lin=dict(lineage,sha256=hashlib.sha256(changed).hexdigest());x=rule.inspect_cache(bytes(changed),device,lin);require(not x['reuse'],'header mutant accepted');negatives.append(dict(name=name,result=x,submitted_to_vulkan=False))
  report['host_negative_controls']=negatives
  policy=dict(baseline_verified=False,candidate_active=False,max_cache_bytes=16777216,minimum_first_frame_gain=.05,max_steady_regression=0.,other_objectives_satisfied=False)
  if a.policy:policy=read_json(policy_bytes);report['caller_policy_sha256']=hashlib.sha256(policy_bytes).hexdigest()
  measurement=read_json(measurement_bytes) if a.measurement else None
  if a.measurement:report['caller_measurement_sha256']=hashlib.sha256(measurement_bytes).hexdigest()
  report['decision']=rule.decide(dict(admission=admission,bytes=len(blob)),measurement,policy)
  report['caller_measurement_not_derived_from_probe']=bool(a.measurement)
  require({str(x.relative_to(ROOT)):sha(x) for x in sources}==before and {k:sha(v) for k,v in toolpaths.items()}==toolhash,'source/tool changed')
  require({str(p.relative_to(a.include)):sha(p) for p in sorted((a.include/'vulkan').rglob('*.h'))}==headers,'headers changed')
  require((not a.policy or a.policy.read_bytes()==policy_bytes) and (not a.measurement or a.measurement.read_bytes()==measurement_bytes),'caller input changed')
  require(all(sha(a.out/name)==digest for name,digest in report['artifacts'].items()),'artifact changed')
  for record in report['steps']:
   for stream in ('stdout','stderr'):require(sha(a.out/(record['name']+'.'+stream))==record[stream+'_sha256'],'step log changed')
  report['provenance_end']=provenance()
  report['status']='CACHE_PERSISTENCE_OBSERVED_NOT_PERFORMANCE_VERIFIED'
 except Exception as e:report['error']=type(e).__name__+': '+str(e)
 finally:
  (a.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':report['status'],'decision':report.get('decision',{}).get('status')}));return 0 if report['status']!='BLOCKED' else 2
if __name__=='__main__':sys.exit(main())
