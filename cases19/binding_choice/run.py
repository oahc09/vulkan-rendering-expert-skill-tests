#!/usr/bin/env python3
"""Fixed descriptor-set/push/set comparison; call counts do not prove speedup."""
import argparse,hashlib,json,os,subprocess,sys,uuid,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools import binding_choice19 as rule,upload_choice19 as common

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(c,s):
 if not c:raise ValueError(s)
def source_paths():
 src=Path(__file__).resolve().parent
 return [src/'probe.c',src/'compute.comp',src/'normative.json',Path(__file__).resolve(),Path(rule.__file__).resolve(),Path(common.__file__).resolve()]
def provenance():
 out={}
 for name,path in [('tests',ROOT),('skill',Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill')))]:
  out[name]={}
  for k,args in [('head',['rev-parse','HEAD']),('dirty',['status','--porcelain'])]:
   p=subprocess.run(['git','-C',str(path),*args],capture_output=True,text=True);out[name][k]=p.stdout.strip() if p.returncode==0 else None
 return out
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('tools','include','loader','icd','libdir','layerdir','spec-root','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--max-set-allocations',type=int,default=1);p.add_argument('--require-performance',action='store_true');a=p.parse_args()
 require(0<=a.max_set_allocations<2**32,'application allocation-count policy');a.output.mkdir(parents=True,exist_ok=False);src=Path(__file__).resolve().parent
 env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','VK_DRIVER_FILES':str(a.icd.resolve()),'VK_LAYER_PATH':str(a.layerdir.resolve()),'LD_LIBRARY_PATH':str(a.libdir.resolve()),'MESA_SHADER_CACHE_DISABLE':'true'}
 report=dict(provenance=provenance(),status='BLOCKED',run_id=str(uuid.uuid4()),environment=env,steps=[],runs=[],scope='single CPU ICD two-generation binding comparison; API call counts not driver memory/performance')
 files=source_paths();before={str(x.relative_to(ROOT)):sha(x) for x in files};report['source_sha256']=before
 paths={'gcc':Path('/usr/bin/gcc'),'glslangValidator':a.tools/'glslangValidator','spirv-val':a.tools/'spirv-val','spirv-dis':a.tools/'spirv-dis','loader':a.loader,'icd_manifest':a.icd,'icd_library':a.libdir/json.loads(a.icd.read_text())['ICD']['library_path'],'layer_manifest':a.layerdir/'VkLayer_khronos_validation.json','layer_library':a.libdir/'libVkLayer_khronos_validation.so'};tools={k:sha(v) for k,v in paths.items()};report['tools_sha256']=tools
 headers={str(x.relative_to(a.include)):sha(x) for x in sorted((a.include/'vulkan').rglob('*.h'))};report['headers_sha256']=headers
 def execute(label,argv,expected=0):
  argv=list(map(str,argv));r=subprocess.run(argv,env=env,capture_output=True,timeout=60);(a.output/(label+'.stdout')).write_bytes(r.stdout);(a.output/(label+'.stderr')).write_bytes(r.stderr);entry=dict(name=label,argv=argv,exit_code=r.returncode,stdout_sha256=sha(a.output/(label+'.stdout')),stderr_sha256=sha(a.output/(label+'.stderr')));report['steps'].append(entry);require(r.returncode==expected,'unexpected exit '+label);return r
 try:
  normative=json.loads((src/'normative.json').read_text());sourceproof=[]
  for ref in normative['sources']:
   raw=(a.spec_root/ref['path']).read_bytes();require(hashlib.sha256(raw).hexdigest()==ref['sha256'],'fixed normative source');lines=raw.decode().splitlines(keepends=True);pos={m.group(1):i for i,l in enumerate(lines) if (m:=re.fullmatch(r'\[\[([^\]]+)\]\]\s*',l))};slices=[]
   for anchor in ref['anchors']:
    start=pos[anchor];end=min([x for x in pos.values() if x>start] or [len(lines)]);slices.append(dict(anchor=anchor,line_start=start+1,line_end=end,sha256=hashlib.sha256(''.join(lines[start:end]).encode()).hexdigest()))
   sourceproof.append(dict(**ref,slices=slices))
  report['normative']=dict(**{k:v for k,v in normative.items() if k!='sources'},sources=sourceproof)
  for k in ('gcc','glslangValidator','spirv-val','spirv-dis'):execute(k+'-version',[paths[k],'--version'])
  spv=a.output/'compute.spv';asm=a.output/'compute.spvasm';exe=a.output/'probe'
  execute('shader-compile',[paths['glslangValidator'],'-V','--target-env','vulkan1.1',src/'compute.comp','-o',spv]);execute('shader-val',[paths['spirv-val'],'--target-env','vulkan1.1',spv]);execute('shader-dis',[paths['spirv-dis'],spv,'-o',asm]);execute('compile',[paths['gcc'],'-std=c11','-Wall','-Wextra','-Werror','-I'+str(a.include),src/'probe.c',a.loader,'-o',exe])
  text=asm.read_text();require('LocalSize 64 1 1' in text and 'OpIMul' in text and 'OpIAdd' in text and 'OpStore' in text,'limited shader structure check')
  report['artifacts']={x.name:sha(x) for x in (spv,asm,exe)}
  for label,path,wrong in [('baseline','set',False),('push','push',False),('recovery','set',False),('set-wrong','set',True),('push-wrong','push',True)]:
   r=execute(label,[exe,path,'wrong-output' if wrong else 'good',spv],6 if wrong else 0);require(r.stderr==b'','unexpected diagnostic');records=[json.loads(l) for l in r.stdout.splitlines()];checked=rule.check(records,path,wrong);report['runs'].append(dict(label=label,records=records,verification=checked))
  baseline,pushed,recovery=[x['verification'] for x in report['runs'][:3]]
  require(baseline==recovery,'baseline restoration full receipt');require(all(x['verification']['identity']==baseline['identity'] for x in report['runs']),'all run device/queue identity')
  baseline_raw=report['runs'][0]['records'];push_raw=report['runs'][1]['records']
  report['decision']=rule.decide(baseline_raw,push_raw,a.max_set_allocations,a.require_performance);report['policy']=dict(max_set_allocations=a.max_set_allocations,require_performance=a.require_performance)
  report['policy_controls']={str(b):rule.decide(baseline_raw,push_raw,b) for b in (0,1,2)};report['performance_request_control']=rule.decide(baseline_raw,push_raw,a.max_set_allocations,True)
  require({str(x.relative_to(ROOT)):sha(x) for x in files}==before and {k:sha(v) for k,v in paths.items()}==tools,'source/tools changed')
  require({str(x.relative_to(a.include)):sha(x) for x in sorted((a.include/'vulkan').rglob('*.h'))}==headers,'headers changed')
  require(all(sha(a.spec_root/ref['path'])==ref['sha256'] for ref in normative['sources']),'normative source changed')
  require(all(sha(a.output/k)==v for k,v in report['artifacts'].items()),'artifact changed')
  for step in report['steps']:
   for stream in ('stdout','stderr'):require(sha(a.output/(step['name']+'.'+stream))==step[stream+'_sha256'],'log changed')
  report['provenance_end']=provenance()
  report['status']='BINDING_PATH_ABA_VERIFIED_NOT_PERFORMANCE'
 except Exception as e:report['error']=type(e).__name__+': '+str(e)
 finally:(a.output/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':report['status'],'decision':report.get('decision')}));return 0 if report['status']!='BLOCKED' else 2
if __name__=='__main__':sys.exit(main())
