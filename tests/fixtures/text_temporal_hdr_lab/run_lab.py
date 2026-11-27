#!/usr/bin/env python3
import argparse,importlib.util,json,math,os,struct,subprocess,sys,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];N=3185

def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def read(p,n):
 b=p.read_bytes()
 if len(b)!=n*4:raise ValueError('readback size')
 a=struct.unpack('<'+'f'*n,b)
 if not all(math.isfinite(v) for v in a):raise ValueError('nonfinite')
 return a
def temporal_reference(frame,history):
 raw=[f32(f32(f32(.3)+f32(f32(.04)*(x%5)))+f32(f32(.01)*frame)) for y in range(49) for x in range(65)];result=[]
 for y in range(49):
  for x in range(65):
   i=y*65+x;j=y*65+x+(frame==1);weight=0;h=raw[i]
   if frame not in (0,3) and x+(frame==1)<65 and abs(raw[i]-history[j][0])<.25 and history[j][3]>0:weight=.8;h=history[j][0]
   neighborhood=[raw[max(0,min(48,y+dy))*65+max(0,min(64,x+dx))] for dy in (-1,0,1) for dx in (-1,0,1)]
   result.append([raw[i]*(1-weight)+min(max(h,min(neighborhood)),max(neighborhood))*weight,.5,0,weight])
 return result

def verify(folder,masks,variant):
 history=[[0,0,0,0] for i in range(N)];rows=[]
 for frame in range(4):
  ideal=temporal_reference(frame,history);acc=read(folder/f'accum{frame}.f32',N*4);actual_history=read(folder/f'history{frame}.f32',N*4)
  for name,values in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
   if any(v!=values[i%4] for i,v in enumerate(read(folder/f'{name}{frame}.f32',N*4))):raise ValueError('aux changed')
  if any(v!=.375 for v in read(folder/f'depth{frame}.f32',N)):raise ValueError('depth changed')
  te=max(abs(acc[4*i+k]-ideal[i][k]) for i in range(N) for k in range(4));he=max(abs(actual_history[4*i+k]-(ideal[i][k] if k<3 else 1)) for i in range(N) for k in range(4))
  mask=masks['F' if variant else 'O'] if frame==0 else masks['F'] if frame==2 else [0.]*N;color=read(folder/f'color{frame}.f32',N*4);ce=ie=0
  for i,cov in enumerate(mask):
   a=cov*.75
   for k in range(4):
    # Stage-local oracle uses validated GPU accum only diagnostically after execution.
    scene=1 if k==3 else (4,2,1)[k]*(.25+.75*acc[4*i]);perfect=1 if k==3 else (4,2,1)[k]*(.25+.75*ideal[i][0]);front=a if k==3 else (2,3,1)[k]*a
    ce=max(ce,abs(color[4*i+k]-(front+scene*(1-a))));ie=max(ie,abs(color[4*i+k]-(front+perfect*(1-a))))
  rows.append({'frame':frame,'temporal_error':te,'history_error':he,'consumer_error':ce,'ideal_end_to_end_error':ie,'max_linear_rgb':max(color[i] for i in range(len(color)) if i%4!=3),'accepted_history_pixels':sum(acc[4*i+3]>0 for i in range(N))})
  history=[[v[0],v[1],v[2],1] for v in ideal]
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(name+' failed')
  return log
 active=load(HERE.parent/'text_active_mrt_lab/run_lab.py','active');rep=active.replace
 run('prepare',[sys.executable,HERE.parent/'text_active_mrt_lab/run_lab.py','--out',out/'prepared']);build=out/'prepared/build';s=(build/'active_lab_reused.hpp').read_text();s=s[:s.index('int unused_vector_main')]
 s=rep(s,'static bool gBadMask=false,gBadDepth=false;','static bool gBadMask=false,gBadDepth=false,gTone=false;')
 s=rep(s,'VkPipeline textPipeline{};','VkPipeline textPipeline{},scenePipeline{};')
 s=rep(s,'VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BIT|VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BLEND_BIT|VK_FORMAT_FEATURE_TRANSFER_SRC_BIT|VK_FORMAT_FEATURE_TRANSFER_DST_BIT','VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BIT|VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BLEND_BIT|VK_FORMAT_FEATURE_TRANSFER_SRC_BIT|VK_FORMAT_FEATURE_TRANSFER_DST_BIT|VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT')
 s=rep(s,'auto usage=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT;','auto usage=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT;')
 s=rep(s,'sl.bindingCount=1;sl.pBindings=&binding;','VkDescriptorSetLayoutBinding bb[2]={binding,{1,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1,VK_SHADER_STAGE_FRAGMENT_BIT,nullptr}};sl.bindingCount=2;sl.pBindings=bb;')
 s=rep(s,'dp.poolSizeCount=1;dp.pPoolSizes=&size;','VkDescriptorPoolSize sizes[2]={size,{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1}};dp.poolSizeCount=2;dp.pPoolSizes=sizes;')
 s=rep(s,'vkUpdateDescriptorSets(device,1,&write,0,nullptr);','vkUpdateDescriptorSets(device,1,&write,0,nullptr);VkDescriptorBufferInfo bi{buffers[1].buffer,0,width*height*16};VkWriteDescriptorSet ww{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};ww.dstSet=textSet;ww.dstBinding=1;ww.descriptorCount=1;ww.descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;ww.pBufferInfo=&bi;vkUpdateDescriptorSets(device,1,&ww,0,nullptr);')
 s=rep(s,'vkDestroyShaderModule(device,vs,nullptr);vkDestroyShaderModule(device,fs,nullptr);VK(result);','auto sf=shader("scene-hdr.frag");stages[1].module=sf;VK(vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&scenePipeline));vkDestroyShaderModule(device,sf,nullptr);vkDestroyShaderModule(device,vs,nullptr);vkDestroyShaderModule(device,fs,nullptr);VK(result);')
 s=rep(s,'vkCmdBeginRenderPass(cb,&rp,VK_SUBPASS_CONTENTS_INLINE);vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,textPipeline);','vkCmdBeginRenderPass(cb,&rp,VK_SUBPASS_CONTENTS_INLINE);vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,scenePipeline);vkCmdBindDescriptorSets(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,textLayout,0,1,&textSet,0,nullptr);float sceneParams[]={gTone?1.f:0.f,0,0,0};vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_FRAGMENT_BIT,0,16,sceneParams);vkCmdDraw(cb,3,1,0,0);vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,textPipeline);')
 s=rep(s,'vkDestroyPipeline(device,textPipeline,nullptr);','vkDestroyPipeline(device,textPipeline,nullptr);vkDestroyPipeline(device,scenePipeline,nullptr);');(build/'temporal_text.hpp').write_text(s)
 # Restore original coverage shader overwritten by the preparatory active test.
 for src,dest in [(HERE.parent/'text_vector_lab/coverage.frag','coverage.frag'),(HERE/'scene.frag','scene-hdr.frag'),(HERE/'history.comp','history.comp'),(HERE.parent/'hybrid_quality_lab/shaders/temporal.comp','temporal.comp')]:
  run('compile-'+dest,[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',src,'-o',build/'shaders'/(dest+'.spv')]);run('validate-'+dest,[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',build/'shaders'/(dest+'.spv')])
 run('compile-main',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'temporal-text'])
 bitmap=load(HERE.parent/'text_bitmap_lab/run_lab.py','bitmap');guard=load(HERE.parent/'text_fallback_lab/adapter.py','guard');font=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');guard.guard(font,'sans');masks={};receipts={}
 for letter in ('O','F'):
  mask,r=bitmap.raster(font,letter,'ltr','en');masks[letter]=mask;receipts[letter]=r;(out/(letter+'.f32')).write_bytes(struct.pack('<3185f',*mask))
 rows={}
 for name,variant,mode in [('ui-O',0,'normal'),('ui-F',1,'normal'),('pollution',0,'pollution'),('tone',0,'tone')]:
  log=run(name,[build/'temporal-text',build/'shaders',out/'O.f32',out/'F.f32',out/name,variant,mode])
  if 'validation_enabled=1' not in log:raise ValueError('validation required')
  rows[name]=verify(out/name,masks,variant)
 for name in ('ui-O','ui-F'):
  if any(r['temporal_error']>1e-5 or r['history_error']>1e-5 or r['consumer_error']>1e-6 for r in rows[name]):raise ValueError('positive layered numerical gate')
 if (out/'ui-O/color0.f32').read_bytes()==(out/'ui-F/color0.f32').read_bytes():raise ValueError('paired UI was not visible')
 for frame in range(1,4):
  if (out/'ui-O'/f'color{frame}.f32').read_bytes()!=(out/'ui-F'/f'color{frame}.f32').read_bytes():raise ValueError('UI change contaminated later color')
 for frame in range(4):
  for field in ('accum','history'):
   if (out/'ui-O'/f'{field}{frame}.f32').read_bytes()!=(out/'ui-F'/f'{field}{frame}.f32').read_bytes():raise ValueError('UI leaked into temporal history')
 if max(r['temporal_error'] for r in rows['pollution'][1:])<=1e-5:raise ValueError('history pollution negative not detected')
 if any(r['temporal_error']>1e-5 or r['history_error']>1e-5 for r in rows['tone']):raise ValueError('tone negative temporal category')
 if max(r['consumer_error'] for r in rows['tone'])<=1e-6:raise ValueError('premature tone negative not detected')
 if min(r['max_linear_rgb'] for r in rows['ui-O'])<=1:raise ValueError('HDR numeric range absent')
 polluted=read(out/'pollution/history0.f32',N*4);clean=read(out/'ui-O/history0.f32',N*4)
 background_error=max(abs(polluted[4*i]-clean[4*i]) for i,c in enumerate(masks['O']) if c==0)
 ui_pollution=max(abs(polluted[4*i]-clean[4*i]) for i,c in enumerate(masks['O']) if c>0)
 if background_error>1e-6 or ui_pollution<=1e-6:raise ValueError('UI pollution isolation')
 for name in ('ui-O','ui-F'):
  run('preview-'+name,[sys.executable,HERE/'preview.py',out/name/'color0.f32',out/(name+'-preview.png')])
 summary={'status':'PASS','pollution_background_error':background_error,'pollution_ui_error':ui_pollution,'validation_enabled':True,'cases':rows,'paired_ui_history_byte_equal':True,'temporal_tolerance':1e-5,'consumer_tolerance':1e-6,'excluded_count':0,'scope':'same-device existing scalar visibility temporal compute -> linear HDR mapping -> real glyph UI, not RGB TAA/HDR display or world motion'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'font-receipts.json').write_text(json.dumps(receipts,indent=2));(out/'local-source-hashes.json').write_text(json.dumps({str(p):sha(p) for p in [*HERE.glob('*.py'),HERE/'main.cpp',HERE/'scene.frag',HERE/'history.comp',build/'temporal_text.hpp',build/'temporal-text',HERE.parent/'hybrid_quality_lab/shaders/temporal.comp']},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
