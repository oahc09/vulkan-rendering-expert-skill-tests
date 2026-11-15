#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,math,os,shutil,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out):
 q=load(HERE.parent/'text_packed_quad_lab/run_lab.py','quad')
 expected=[]
 for phase,pending,completed,generation in [('A_gated',True,0,-1),('B_initial_completed_A_pending',True,1,0),('B_candidate_canceled_A_pending',True,2,0),('B_new_completed_A_pending',True,3,2),('A_pending_scope_cleaned',False,3,2),('B_continued_after_A_destroyed',False,4,2)]:expected.append(dict(phase=phase,A_pending=pending,B_completed_renders=completed,B_published_generation=generation))
 expected.append(dict(phase='all_destroyed',B_completed_renders=4))
 if [json.loads(x) for x in (out/'frames/events.jsonl').read_text().splitlines()]!=expected:raise ValueError('dual pending event mismatch')
 rows=[]
 for name,ref in [('B-initial-A-pending',out),('B-new-A-pending',out/'new-reference'),('B-after-A-destroyed',out/'new-reference')]:
  r=q.verify(ref,out/'frames'/name);r['stage']=name;rows.append(r)
 for name,expected_aux in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  data=(out/'frames/B-wrong-canceled-route'/(name+'.rgba32f')).read_bytes()
  if len(data)!=65*49*16:raise ValueError('negative auxiliary size')
  values=struct.unpack('<12740f',data)
  if any(not math.isfinite(v) or v!=expected_aux[i%4] for i,v in enumerate(values)):raise ValueError('negative auxiliary sentinel mismatch')
 try:q.verify(out,out/'frames/B-wrong-canceled-route')
 except ValueError as e:
  if str(e)!='quad UV composition mismatch':raise
 else:raise ValueError('wrong canceled route accepted')
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 def run(name,args,expected=0):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode!=expected or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 combined=HERE.parent/'text_combined_lifecycle_lab';run('prepare',[sys.executable,combined/'run_lab.py','--out',out/'prepared','--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']);build=out/'prepared/prepared/build'
 s=(combined/'main.cpp').read_text();marker='int main(int argc,char**argv)'
 if s.count(marker)!=1:raise ValueError('source hook drift')
 s=s[:s.index(marker)]
 def change(old,new):
  nonlocal s
  if s.count(old)!=1:raise ValueError('owner hook drift '+old)
  s=s.replace(old,new)
 change('struct PageResources {Image image{};', 'struct PageResources {VkDevice owner{};Image image{};')
 change('p->generation=gen;', 'p->generation=gen;p->owner=v.device;')
 change('if(!p.live||p.canceled||!p.uploadComplete', 'if(p.owner!=v.device||!p.live||p.canceled||!p.uploadComplete')
 change('void cancel(PageResources& p){', 'void cancel(PageResources& p){if(p.owner!=v.device)throw std::runtime_error("foreign device page");')
 change('void retire(PageResources& p){', 'void retire(PageResources& p){if(p.owner!=v.device)throw std::runtime_error("foreign device page");')
 change('const std::vector<float>& mask){auto& s=begin();', 'const std::vector<float>& mask){if(p.owner!=v.device)throw std::runtime_error("foreign device page");auto& s=begin();')
 change('if(!p.live)throw std::runtime_error("dead page route");', 'if(p.owner!=v.device)throw std::runtime_error("foreign device page");if(!p.live)throw std::runtime_error("dead page route");')
 (build/'dual_pending.hpp').write_text(s)
 run('compile',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'dual_pending'])
 shutil.copyfile(out/'prepared/reference.json',out/'reference.json');shutil.copytree(out/'prepared/new-reference',out/'new-reference')
 atlas=out/'prepared/prepared/atlas.f32';vertices=out/'prepared/prepared/vertices.f32';before=[sha(atlas),sha(vertices)]
 args=[build/'dual_pending',build/'shaders',atlas,vertices,out/'frames'];log=run('actual',args)
 if 'DUAL_PENDING_PASS validation_enabled=1' not in log or log.count('COMBINED_PENDING_CLEANUP_OK')!=2:raise ValueError('device cleanup evidence')
 if before!=[sha(atlas),sha(vertices)]:raise ValueError('input mutation')
 rows=verify(out)
 files={str(p.relative_to(out/'frames')):sha(p) for p in (out/'frames').rglob('*') if p.is_file()};run('refuse-overwrite',args,1)
 if files!={str(p.relative_to(out/'frames')):sha(p) for p in (out/'frames').rglob('*') if p.is_file()}:raise ValueError('evidence overwritten')
 summary={'status':'PASS','validation_enabled':True,'logical_devices':2,'A_pending_render_submissions':1,'B_completed_render_submissions':4,'B_positive_images':3,'B_diagnostic_images':1,'A_pending_checks':5,'rows':rows,'negative_checks':['foreign device publication/draw rejected before recording','actual canceled B route rejected','controlled A pending exception cleanup with gate release','existing output refused unchanged'],'limits':['same configured software Vulkan implementation, not different physical GPUs or real Surface','B completes while A gate un-signaled; no simultaneous shader execution assertion','A post-release image not read back; only bounded fence completion/cleanup verified','B candidate cancel occurs after its upload completion','UNUSED preserve auxiliary fallback, not active MRT/depth','no arbitrary allocation or device-loss cleanup/production leak assertion','target platform and Live unverified']};(out/'summary.json').write_text(json.dumps(summary,indent=2))
 (out/'local-provenance.json').write_text(json.dumps({'sources':{str(p):sha(p) for p in [HERE/'main.cpp',HERE/'run_lab.py',combined/'main.cpp',combined/'run_lab.py',HERE.parent/'text_packed_quad_lab/run_lab.py']},'generated':{str(p):sha(p) for p in [build/'dual_pending.hpp',build/'dual_pending',build/'combined_pipeline.hpp',build/'combined_engine.hpp']},'prepared_receipt':json.loads((out/'prepared/local-provenance.json').read_text()),'input_hashes_before_after':before},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
