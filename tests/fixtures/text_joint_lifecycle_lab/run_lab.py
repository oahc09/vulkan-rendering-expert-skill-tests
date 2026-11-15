#!/usr/bin/env python3
"""One actual pending packed-glyph path with shader clip and active MRT protection."""
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
# Fixed from CPU-only boundary analysis before first joint GPU execution.
DESTINATIONS=[(25,25),(11,19),(27,10)]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out):return load(HERE.parent/'text_combined_lifecycle_lab/run_lab.py','combined_oracle').verify(out)
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 def run(name,args,expected=0):
  r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode!=expected or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 combined=HERE.parent/'text_combined_lifecycle_lab';quad=load(HERE.parent/'text_packed_quad_lab/run_lab.py','quad');clip=load(HERE.parent/'text_clip_lab/run_lab.py','clip')
 run('prepare',[sys.executable,combined/'run_lab.py','--out',out/'prepared','--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']);build=out/'prepared/prepared/build';base_ref=json.loads((out/'prepared/prepared/reference.json').read_text());original=base_ref['glyphs'][0];w,h=original['size'];ax,ay,_,_=original['atlas_rect'];verts=[];glyphs=[];unclipped=[];bypass_effect=[0,0,0];visible=0
 for dx,dy in DESTINATIONS:
  g=json.loads(json.dumps(original));g['destination']=[dx,dy];unclipped.append(json.loads(json.dumps(g)))
  pixels=[]
  for y in range(h):
   for x in range(w):
    xx,yy=dx+x+.5,dy+y+.5;v=g['pixels'][y*w+x];bits=[12<=xx<43 and 10<=yy<37,(xx-30)**2+(yy-25)**2<=225,clip.inside_polygon(xx,yy)]
    for k in range(3):bypass_effect[k]+=int(v>0 and not bits[k] and all(bits[j] for j in range(3) if j!=k))
    keep=clip.predicate(xx,yy);pixels.append(v if keep else 0.);visible+=int(v>0 and keep)
  g['pixels']=pixels;glyphs.append(g)
  for x,y in [(0,0),(w,0),(0,h),(0,h),(w,0),(w,h)]:verts.extend([2*(dx+x)/65-1,2*(dy+y)/49-1,(ax+x)/65,(ay+y)/49])
 if min(bypass_effect)<=0 or visible<=0:raise ValueError('inactive clip coverage')
 prereg={'destinations':DESTINATIONS,'clip_bypass_nonzero_pixels':bypass_effect,'positive_nonzero_pixels':visible,'tolerance':1e-6,'gpu_atlas_unclipped':True};(out/'conditions.json').write_text(json.dumps(prereg,indent=2))
 (out/'source-glyph-reference.json').write_text(json.dumps({'glyphs':unclipped}));(out/'reference.json').write_text(json.dumps({'glyphs':glyphs}));new=json.loads(json.dumps(glyphs))
 for g in new:g['pixels']=[v*.5 for v in g['pixels']]
 (out/'new-reference').mkdir();(out/'new-reference/reference.json').write_text(json.dumps({'glyphs':new}));quad.raw(out/'vertices.f32',verts)
 engine=build/'combined_engine.hpp';s=engine.read_text();old='enabled.multiDrawIndirect = mdi;'
 if s.count(old)!=1:raise ValueError('engine hook drift')
 s=s.replace(old,old+'if(!f2.features.independentBlend)throw std::runtime_error("independentBlend unavailable");enabled.independentBlend=VK_TRUE;');engine.write_text(s)
 header=build/'combined_pipeline.hpp';s=header.read_text()
 def replace(old,new):
  nonlocal s
  if s.count(old)!=1:raise ValueError('pipeline hook drift '+old)
  s=s.replace(old,new)
 replace('VkAttachmentReference refs[3]={{0,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED},{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED}};', 'VkAttachmentReference refs[3]={{0,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{1,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{2,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL}};')
 replace('sub.preserveAttachmentCount=2;sub.pPreserveAttachments=preserved;','sub.preserveAttachmentCount=0;sub.pPreserveAttachments=nullptr;')
 replace('VkPipelineColorBlendStateCreateInfo bs{','for(int i=1;i<3;i++){blends[i].blendEnable=VK_FALSE;blends[i].colorWriteMask=JOINT_BAD_WRITE?15:0;}VkPipelineColorBlendStateCreateInfo bs{')
 header.write_text('#ifndef JOINT_BAD_WRITE\n#define JOINT_BAD_WRITE 0\n#endif\n'+s)
 cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
 run('compile',cmd+[combined/'main.cpp','-l:libvulkan.so.1','-o',build/'joint'])
 run('compile-write-negative',cmd+['-DJOINT_BAD_WRITE=1',combined/'main.cpp','-l:libvulkan.so.1','-o',build/'joint-write-negative'])
 variants=[]
 for bypass in range(4):
  folder=build/('joint-shaders-'+str(bypass));shutil.copytree(build/'shaders',folder);run('shader-'+str(bypass),[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2','-DBYPASS_CLIP='+str(bypass),HERE/'joint.frag','-o',folder/'coverage.frag.spv']);run('validate-'+str(bypass),[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',folder/'coverage.frag.spv']);variants.append(folder)
 args=[build/'joint',variants[0],out/'prepared/prepared/atlas.f32',out/'vertices.f32'];log=run('joint',args+[out/'frames'])
 if 'validation_enabled=1' not in log or 'COMBINED_RESOURCES_DESTROYED' not in log:raise ValueError('validation/cleanup evidence')
 rows=verify(out);negatives=[]
 for name,binary,shader,reason in [('bypass-'+str(k),build/'joint',variants[k],'composition mismatch') for k in range(1,4)]+[('bad-write',build/'joint-write-negative',variants[0],'sentinel mismatch')]:
  root=out/name;root.mkdir();shutil.copyfile(out/'reference.json',root/'reference.json');shutil.copytree(out/'new-reference',root/'new-reference');run(name,[binary,shader,out/'prepared/prepared/atlas.f32',out/'vertices.f32',root/'frames'])
  try:verify(root)
  except ValueError as e:
   if reason not in str(e):raise
  else:raise ValueError('negative accepted '+name)
  negatives.append(name)
 abort=run('abort-pending',args+[out/'aborted','--abort-pending'],1)
 if 'COMBINED_PENDING_CLEANUP_OK' not in abort or 'INTENTIONAL_COMBINED_PENDING_CLEANUP' not in abort:raise ValueError('pending cleanup evidence missing')
 summary=dict(status='PASS',validation_enabled=True,main_lifecycle_draws=4,positive_verified_images=3,diagnostic_wrong_route_draws=1,active_color_attachments=3,clip_layers=3,conditions=prereg,rows=rows,negative_checks=negatives+['actual canceled-route image rejected','controlled pending cleanup'],scope='same actual pending glyph submit: packed UV + three hard shader clips + active MRT protection + page cancellation/growth/retirement',limits=['software Vulkan','one queue gated at ALL_COMMANDS, no active shader or parallel claim','no depth/stencil/general path clip','no GPU mask producer pass','not production leak/multithread/target device acceptance']);(out/'summary.json').write_text(json.dumps(summary,indent=2))
 (out/'local-provenance.json').write_text(json.dumps({'sources':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'run_lab.py',HERE/'joint.frag',combined/'main.cpp',combined/'run_lab.py',HERE.parent/'text_clip_lab/run_lab.py',HERE.parent/'text_packed_quad_lab/run_lab.py']},'generated':{p.name:sha(p) for p in [engine,header,build/'joint',build/'joint-write-negative']},'shader_variants':{str(i):sha(p/'coverage.frag.spv') for i,p in enumerate(variants)},'prepared_receipt':json.loads((out/'prepared/local-provenance.json').read_text())},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
