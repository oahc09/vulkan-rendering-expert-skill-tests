#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,math,os,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;TOL=1e-6
CAMERAS={'A':dict(origin=(0,0,0),right=(1,0,0),up=(0,1,0),forward=(0,0,1)),'B':dict(origin=(.5,.125,-.25),right=(24/25,0,7/25),up=(0,1,0),forward=(-7/25,0,24/25))}
CASES=[dict(name=f'{c}-{mode}',camera=c,mode=mode) for c in ('A','B') for mode in ('depth','top')]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def reference(g,c,x,y):
 cam=CAMERAS[c['camera']];o=cam['origin'];nx=2*(x+.5)/65-1;ny=2*(y+.5)/49-1;d=[cam['forward'][i]+nx*cam['right'][i]+ny*cam['up'][i] for i in range(3)]
 # Independent camera ray, not multiplication by the GPU view matrix.
 t=(2.75+.25*o[0]-o[2])/(d[2]-.25*d[0]);wx,wy=o[0]+t*d[0],o[1]+t*d[1];cov=0;hole=False
 if 1<=t<=10 and -1<=wx<1.25 and -1.125<=wy<1.375:
  w,h=g['size'];sx=math.floor((wx+1)/2.25*w);sy=math.floor((wy+1.125)/2.5*h);cov=g['pixels'][sy*w+sx];hole=sy*w+sx in g['hole_indices']
 to=(2-o[2])/d[2];ox,oy=o[0]+to*d[0],o[1]+to*d[1];occ=1<=to<=10 and .125<=ox<1.625 and -1.375<=oy<1.625
 bg=(.2,.65,.1,1) if occ else (.1,.2,.3,.5);dep=10/9-10/(9*to) if occ else 1
 hidden=bool(cov and occ and t>to);visible=bool(cov and not hidden)
 if c['mode']=='depth' and hidden:cov=0
 a=cov*.75;rgba=[v*a+bg[k]*(1-a) for k,v in enumerate((.9,.5,.2,1))]
 return rgba,dep,hidden,visible,hole

def verify(folder,g,c):
 def read(n,count):
  b=(folder/(n+'.f32')).read_bytes()
  if len(b)!=count*4:raise ValueError('readback size')
  v=struct.unpack('<'+'f'*count,b)
  if not all(math.isfinite(a) for a in v):raise ValueError('nonfinite readback')
  return v
 col=read('color',12740);depth=read('depth',3185)
 for n,s in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  if any(v!=s[i%4] for i,v in enumerate(read(n,12740))):raise ValueError('auxiliary')
 err=de=0;hidden=visible=holes=0
 for y in range(49):
  for x in range(65):
   rgba,d,h,v,ho=reference(g,c,x,y);i=y*65+x;err=max(err,*(abs(col[4*i+k]-rgba[k]) for k in range(4)));de=max(de,abs(depth[i]-d));hidden+=h;visible+=v;holes+=ho
 if de>TOL:raise ValueError('independent scene depth mismatch '+str(de))
 return dict(name=c['name'],max_composition_error=err,max_depth_error=de,hidden_nonzero_pixels=hidden,visible_nonzero_pixels=visible,projected_hole_pixels=holes,excluded_count=0)

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 (out/'conditions.json').write_text(json.dumps(dict(cameras=CAMERAS,cases=CASES,world_plane='z=2.75+.25x',world_rectangle=[-1,1.25,-1.125,1.375],near=1,far=10,tolerance=TOL,excluded_count=0,resource_scope='one VkDevice, shared atlas and vertex buffer, serial views'),indent=2))
 def run(n,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(n+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise RuntimeError(n+' failed '+log[-1000:])
  return log
 world=HERE.parent/'text_world_label_lab';run('prepare',[sys.executable,world/'run_lab.py','--font',a.font,'--out',out/'prepared']);build=out/'prepared/prepared/build';g=json.loads((out/'prepared/reference.json').read_text())
 pre=[]
 for c in CASES:
  r=[reference(g,c,x,y) for y in range(49) for x in range(65)];hidden=sum(x[2] for x in r);visible=sum(x[3] for x in r)
  if not hidden or not visible:raise ValueError('nonobservable camera ROI')
  pre.append(dict(name=c['name'],hidden=hidden,visible=visible))
 (out/'roi-preflight.json').write_text(json.dumps(pre,indent=2))
 s=(build/'world_helper.hpp').read_text()
 def replace(old,new,count=1):
  nonlocal s
  if s.count(old)!=count:raise ValueError('helper drift '+old)
  s=s.replace(old,new)
 replace('static bool gAlways=false;','static const std::array<float,16> IDENTITY_VIEW={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};static bool gAlways=false;')
 replace('VkPipeline scenePipeline{};','VkPipeline scenePipeline{},topPipeline{};')
 replace('VkPushConstantRange range{VK_SHADER_STAGE_FRAGMENT_BIT,0,16};','VkPushConstantRange range{VK_SHADER_STAGE_FRAGMENT_BIT|VK_SHADER_STAGE_VERTEX_BIT,0,80};')
 hook='VK(vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&scenePipeline));'
 replace(hook,hook+'ds.depthWriteEnable=VK_FALSE;ds.depthCompareOp=VK_COMPARE_OP_ALWAYS;VK(vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&topPipeline));')
 replace('vkDestroyPipeline(device,scenePipeline,nullptr);','vkDestroyPipeline(device,scenePipeline,nullptr);vkDestroyPipeline(device,topPipeline,nullptr);')
 replace('const std::array<float,4>& ink){','const std::array<float,4>& ink,const std::array<float,16>& view=IDENTITY_VIEW,bool top=false,bool stale=false){')
 replace('float rgba[]={ink[0],ink[1],ink[2],ink[3]};','float rgba[20]={ink[0],ink[1],ink[2],ink[3]};memcpy(rgba+4,view.data(),64);')
 replace('float scene[]={.2f,.65f,.1f,-1.f};','float scene[20]={.2f,.65f,.1f,-1.f};memcpy(scene+4,view.data(),64);')
 replace('vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_FRAGMENT_BIT,0,16,rgba);','vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_FRAGMENT_BIT|VK_SHADER_STAGE_VERTEX_BIT,0,80,rgba);',2)
 replace('vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_FRAGMENT_BIT,0,16,scene);','vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_FRAGMENT_BIT|VK_SHADER_STAGE_VERTEX_BIT,0,80,scene);')
 replace('vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,textPipeline);vkCmdPushConstants','vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,top?topPipeline:textPipeline);if(stale)memcpy(rgba+4,IDENTITY_VIEW.data(),64);vkCmdPushConstants')
 (build/'second_helper.hpp').write_text(s)
 run('vertex',[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',HERE/'view.vert','-o',build/'shaders/fullscreen.vert.spv']);run('spirv',[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',build/'shaders/fullscreen.vert.spv'])
 # Preparation helper's shaders directory contains original active shader; compile actual world fragment explicitly.
 run('fragment',[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',world/'world.frag','-o',build/'shaders/coverage.frag.spv']);run('fragment-spirv',[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',build/'shaders/coverage.frag.spv'])
 run('compile',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'second'])
 atlas=out/'prepared/atlas.f32';verts=out/'prepared/z2.75-depth.vertices';before=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (atlas,verts)]
 log=run('views',[build/'second',build/'shaders',atlas,verts,out/'gpu'])
 if 'SECOND_CAMERA_PASS validation_enabled=1 device_instances=1 world_vertex_buffers=1 shared_atlas_images=1 completed_draw_calls=10' not in log:raise ValueError('device/validation evidence')
 if before!=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (atlas,verts)]:raise ValueError('input mutation')
 rows=[]
 for c in CASES:
  r=verify(out/'gpu'/c['name'],g,c)
  if r['max_composition_error']>TOL:raise ValueError('second camera oracle mismatch '+json.dumps(r))
  rows.append(r)
 neg=verify(out/'gpu/B-stale-label-A',g,CASES[2])
 if neg['max_composition_error']<=TOL:raise ValueError('stale camera negative invisible')
 summary=dict(status='BOUNDED_SECOND_CAMERA_PASS',validation_enabled=True,tolerance=TOL,cases=rows,actual_gpu_negative=neg,device_instances=1,world_vertex_buffers=1,shared_atlas_images=1,limits=['one software VkDevice serial views, not parallel surfaces','actual camera translation and yaw; world geometry/atlas unchanged','no shadow or full SceneB qualification'])
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-provenance.json').write_text(json.dumps(dict(input_hashes=dict(atlas=before[0],world_vertices=before[1]),sources={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [HERE/'main.cpp',HERE/'view.vert',HERE/'run_lab.py',world/'world.frag']},binary=hashlib.sha256((build/'second').read_bytes()).hexdigest(),helper=hashlib.sha256(s.encode()).hexdigest(),shaders={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (build/'shaders').glob('*.spv')},prepared=json.loads((out/'prepared/local-provenance.json').read_text())),indent=2))
 png=load(HERE.parent/'text_vector_lab/run_lab.py','png').png
 for c in CASES:
  v=struct.unpack('<12740f',(out/'gpu'/c['name']/'color.f32').read_bytes());png(out/'gpu'/c['name']/'preview.png',65,49,bytes(round(255*(12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055)) for i,x in enumerate(v) if i%4!=3))
 print(json.dumps(summary))
if __name__=='__main__':main()
