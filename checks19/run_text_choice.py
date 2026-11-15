"""One fresh original board/refined/budget chain, independently rechecked; no quality assumption."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OWN=['checks19/run_text_choice.py','tools/text_choice19.py','checks19/process_supervisor19.py','coverage/v1.0.19/pair.json','docs/v1.0.19-original-plan.md']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(c,s):
 if not c:raise ValueError(s)
def git(r,*args):return subprocess.check_output(['git','-C',str(r),*args],timeout=30).decode().strip()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def inventory(root):
 out={}
 for p in root.rglob('*'):
  require(not p.is_symlink() and p.resolve().is_relative_to(root),'artifact escape')
  if p.is_file() and p!=root/'report.json':out[str(p.relative_to(root))]=sha(p)
 return out
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('tools','include','loader','icd','libdir','layerdir','skill-root','output','variable-font','msdf-source'):p.add_argument('--'+k,type=Path,required=True)
 for k in ('expected-tests-head','expected-skill-head'):p.add_argument('--'+k,required=True)
 p.add_argument('--policy',type=Path);p.add_argument('--additional-policy',type=Path,action='append',default=[]);p.add_argument('--budget-seconds',type=int,default=3600);p.add_argument('--cancel-file',type=Path);a=p.parse_args()
 require(60<=a.budget_seconds<=7200,'bounded execution budget');a.output.mkdir(parents=True,exist_ok=False);a.output=a.output.resolve();report=dict(status='BLOCKED',run_id=str(uuid.uuid4()),steps=[],scope='one original three-lab software Vulkan execution; fixed crop quality observations, not performance or production qualification')
 try:
  def identity():return {k:dict(head=git(r,'rev-parse','HEAD'),dirty=git(r,'status','--porcelain')) for k,r in [('tests',ROOT),('skill',a.skill_root)]}
  before=identity();require(before=={'tests':dict(head=a.expected_tests_head,dirty=''),'skill':dict(head=a.expected_skill_head,dirty='')},'exact clean pair');pair=json.loads((ROOT/'coverage/v1.0.19/pair.json').read_text());require(pair['skill_sha']==a.expected_skill_head and pair['release_status']=='BLOCKED','pair');report.update(provenance=before,pair=pair)
  # Existing labs dynamically load one another. Bind the complete tracked fixture code/data closure,
  # not generated __pycache__, old workspaces, or caller-selected code.
  fixture_rels=[r for r in git(ROOT,'ls-files','tests/fixtures').splitlines() if r.split('/')[2].startswith(('text_','scene_a_')) or r.split('/')[2]=='engine_scale_lab']
  rels=sorted(set(OWN+fixture_rels+['tests/platform_text_probe.py']))
  sources={}
  for rel in rels:
   f=ROOT/rel;require(not f.is_symlink() and f.resolve().is_relative_to(ROOT),'source escape');raw=f.read_bytes();require(raw==subprocess.check_output(['git','-C',str(ROOT),'show',a.expected_tests_head+':'+rel]),'source differs');sources[rel]=sha(f)
  report['sources']=sources;rule=load('text_choice',ROOT/'tools/text_choice19.py');sup=load('text_supervisor',ROOT/'checks19/process_supervisor19.py')
  policy=json.loads(a.policy.read_text()) if a.policy else dict(baseline='board/bitmap',quality_targets=None,per_row_payload_budget=400000,require_performance=False);policyhash=sha(a.policy) if a.policy else None;report['policy']=policy;extra=[dict(name=p.name,sha256=sha(p),policy=rule.decode(p.read_text())) for p in a.additional_policy];require(len({x['name'] for x in extra})==len(extra),'duplicate extra policy names')
  paths=dict(cxx=Path('/usr/bin/g++'),python=Path(sys.executable).resolve(),png_python=Path('/usr/bin/python3').resolve(),shell=Path('/bin/sh').resolve(),env=Path('/usr/bin/env'),ldd=Path('/usr/bin/ldd'),loader=a.loader,icd=a.icd,icd_library=a.libdir/json.loads(a.icd.read_text())['ICD']['library_path'],layer_manifest=a.layerdir/'VkLayer_khronos_validation.json',layer_library=a.libdir/'libVkLayer_khronos_validation.so',glslang=a.tools/'glslangValidator',spirv_val=a.tools/'spirv-val')
  toolhash={k:sha(v) for k,v in paths.items()};headers={str(f.relative_to(a.include)):sha(f) for f in (a.include/'vulkan').rglob('*.h')}
  fonts=[a.variable_font,a.variable_font.parent/'OFL.txt',a.variable_font.parent/'receipt.json',Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'),Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),Path('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'),*[Path('/usr/share/doc')/n/'copyright' for n in ('fonts-dejavu-core','fonts-noto-cjk','fonts-noto-color-emoji')]]
  fontshash={str(f):sha(f) for f in fonts};require(git(a.msdf_source,'rev-parse','HEAD')=='1874bcf7d9624ccc85b4bc9a85d78116f690f35b' and not git(a.msdf_source,'status','--porcelain'),'generator pin/clean');generator={rel:sha(a.msdf_source/rel) for rel in git(a.msdf_source,'ls-files').splitlines() if (a.msdf_source/rel).is_file()}
  # Provider binaries and Python packages, not just version strings.
  libs={str(f):sha(f) for pattern in ('libfreetype.so.*','libharfbuzz.so.*','libfribidi.so.*','libicu*.so.*') for f in Path('/usr/lib/x86_64-linux-gnu').glob(pattern) if f.is_file() and not f.is_symlink()}
  import freetype
  packages=[Path(freetype.__file__).parent,Path('/usr/lib/python3/dist-packages/fontTools'),Path('/usr/lib/python3/dist-packages/PIL')]
  modules={str(f):sha(f) for d in packages for f in d.rglob('*') if f.is_file() and '__pycache__' not in str(f) and f.suffix in ('.py','.so')}
  report.update(tools=toolhash,headers=headers,fonts_licenses=fontshash,provider_libraries=libs,provider_modules=modules,generator=generator)
  env=dict(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',LD_LIBRARY_PATH=str(a.libdir.resolve()),VK_DRIVER_FILES=str(a.icd.resolve()),VK_LAYER_PATH=str(a.layerdir.resolve()),MESA_SHADER_CACHE_DISABLE='true',VULKAN_SDK_PREFIX=str(a.include.parent.resolve()),GLSLANG=str(paths['glslang'].resolve()),SPIRV_VAL=str(paths['spirv_val'].resolve()),CXX='/usr/bin/g++',TEXT18_FONTTOOLS_PYTHON='/usr/bin/python3');report['environment']=env
  probe_code="import ctypes,ctypes.util,freetype,json; [ctypes.CDLL(n) for n in (ctypes.util.find_library('harfbuzz'),'libfribidi.so.0','libicuuc.so.76')]; print(json.dumps(sorted({x.split()[-1] for x in open('/proc/self/maps') if any(k in x for k in ('libfreetype','libharfbuzz','libfribidi','libicu'))})))"
  provider_probe=subprocess.run([sys.executable,'-c',probe_code],env=env,capture_output=True,text=True,timeout=30);(a.output/'providers.stdout').write_text(provider_probe.stdout);(a.output/'providers.stderr').write_text(provider_probe.stderr);require(provider_probe.returncode==0,'provider resolution');libs={f:sha(Path(f)) for f in json.loads(provider_probe.stdout)};require(all(any(k in f for f in libs) for k in ('libfreetype','libharfbuzz','libfribidi','libicu')),'actual provider libraries');report['provider_libraries']=libs
  cancel=sup.Cancellation(a.cancel_file);cancel.install();deadline=time.monotonic()+a.budget_seconds
  try:
   for label,lab in zip(('board','refined','budget'),rule.LABS):
    argv=['/usr/bin/env','-i',*[k+'='+v for k,v in env.items()],sys.executable,str(ROOT/'tests/fixtures'/lab/'run_lab.py'),'--out',str(a.output/label),'--variable-font',str(a.variable_font.resolve()),'--msdf-source',str(a.msdf_source.resolve())]
    if label=='budget':argv+=['--source',str(a.output/'refined')]
    out=a.output/(label+'.stdout');err=a.output/(label+'.stderr');step=sup.run_step(argv,out,err,timeout=1200,total_deadline=deadline,cancellation=cancel);step.update(label=label,argv=argv,stdout_sha256=sha(out),stderr_sha256=sha(err));report['steps'].append(step)
    require(type(step['returncode'])is int and step['returncode']==0 and not any(step[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and step['group_cleanup']['group_gone']is True,'step failed '+label)
    binary=a.output/label/'build'/('compact_lab' if label=='budget' else 'board');linked=subprocess.run(['/usr/bin/ldd',str(binary)],env=env,capture_output=True,text=True,timeout=30);(a.output/(label+'-linked.stdout')).write_text(linked.stdout);(a.output/(label+'-linked.stderr')).write_text(linked.stderr);require(linked.returncode==0,'ldd failed');lines=[x for x in linked.stdout.splitlines() if 'libvulkan.so.1 =>' in x];require(len(lines)==1 and Path(lines[0].split('=>')[1].split()[0]).resolve()==a.loader.resolve(),'actual linked loader differs')
   before_analysis=inventory(a.output)
   code="import sys,json;sys.path.insert(0,sys.argv[1]);from tools.text_choice19 import analyze;print(json.dumps(analyze(*sys.argv[2:],progress=lambda x:print(x,file=sys.stderr,flush=True))))"
   argv=['/usr/bin/env','-i',*[k+'='+v for k,v in env.items()],sys.executable,'-c',code,str(ROOT),*[str(a.output/k) for k in ('board','refined','budget')]]
   out=a.output/'analyze.stdout';err=a.output/'analyze.stderr';step=sup.run_step(argv,out,err,timeout=1200,total_deadline=deadline,cancellation=cancel);step.update(label='analyze',argv=argv,stdout_sha256=sha(out),stderr_sha256=sha(err));report['steps'].append(step)
   require(type(step['returncode'])is int and step['returncode']==0 and not any(step[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and step['group_cleanup']['group_gone']is True,'step failed analyze')
   report['quality']=rule.decode(out.read_text());raw=inventory(a.output);require(all(raw.get(k)==v for k,v in before_analysis.items()),'raw changed during analysis')
  finally:cancel.restore()
  report['decision']=rule.decide(report['quality'],policy);require(report['decision']['status']!='UNKNOWN','policy/evidence invalid');report['additional_policy_decisions']=[dict(**x,decision=rule.decide(report['quality'],x['policy']),scope='same single execution, not independent GPU run') for x in extra];require(all(x['decision']['status']!='UNKNOWN' for x in report['additional_policy_decisions']),'invalid extra policy')
  require(inventory(a.output)==raw,'raw changed during verification');require(identity()==before and all(sha(ROOT/k)==v for k,v in sources.items()),'source/pair changed')
  require({k:sha(v) for k,v in paths.items()}==toolhash and all(sha(Path(k))==v for group in (fontshash,libs,modules) for k,v in group.items()),'tool/provider changed');require({str(f.relative_to(a.include)):sha(f) for f in (a.include/'vulkan').rglob('*.h')}==headers,'headers changed');require(all(sha(a.msdf_source/k)==v for k,v in generator.items()) and not git(a.msdf_source,'status','--porcelain'),'generator changed');require(a.policy is None or sha(a.policy)==policyhash,'policy changed');require(all(sha(p)==x['sha256'] for p,x in zip(a.additional_policy,extra)),'extra policy changed');report['artifacts']=raw;report['status']='TEXT_REGISTERED_CHAIN_VERIFIED_NOT_QUALIFIED'
 except (Exception,KeyboardInterrupt) as e:
  report['error']=type(e).__name__+': '+str(e)
  if isinstance(e,KeyboardInterrupt) or any(x.get('cancelled') for x in report['steps']):report['status']='CANCELLED'
 finally:(a.output/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':report['status'],'decision':report.get('decision',{}).get('status')}));return 0 if report['status']=='TEXT_REGISTERED_CHAIN_VERIFIED_NOT_QUALIFIED' else 2
if __name__=='__main__':sys.exit(main())
