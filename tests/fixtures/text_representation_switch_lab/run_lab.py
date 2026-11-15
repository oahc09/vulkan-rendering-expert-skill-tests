#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,os,shutil,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'text_msdf_lab/run_lab.py'
s=importlib.util.spec_from_file_location('integration',HERE.parent/'text_msdf_integration_lab/run_lab.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q);m=q.m
SCALES=[.75,.95,1.05,1.15,1.05,.95,.85,.95,1.05,1.15]
# Match float32 push constants, not ideal real-valued scales.
SCALES=[struct.unpack('<f',struct.pack('<f',v))[0] for v in SCALES]
BITMAP_TOLERANCE=1e-6
MSDF_TOLERANCE=.004
def routes():
 state=0;rows=[]
 for i,v in enumerate(SCALES):
  old=state
  if v<=.9:state=0
  elif v>=1.1:state=1
  rows.append(dict(frame=i,previous=old,selected=state))
 return rows
def replace(s,a,b):
 if s.count(a)!=1:raise ValueError('upstream helper changed')
 return s.replace(a,b)
def error(rgba,coverage):
 return max(abs(rgba[i*4+c]-((a*.75 if c==3 else (.9,.5,.2)[c]*a*.75)+(.1,.2,.3,.5)[c]*(1-a*.75))) for i,a in enumerate(coverage) for c in range(4))
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--font',required=True,type=Path);p.add_argument('--msdf-source',required=True,type=Path);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 (out/'conditions.json').write_text(json.dumps(dict(scales=SCALES,phases=[i%4*.25 for i in range(10)],bitmap_threshold=.9,msdf_threshold=1.1,initial='bitmap',sampling_composition_tolerance={'bitmap':BITMAP_TOLERANCE,'msdf-linear4':MSDF_TOLERANCE},hold_rule='retain preceding representation for .9 < scale < 1.1',negative_frame=2,negative_actual='msdf',negative_expected='bitmap',status='MEASURED_NOT_QUALIFIED'),indent=2))
 prep=out/'baseline'
 with (out/'prepare.log').open('w') as log:subprocess.run([sys.executable,str(BASE),'--out',str(prep),'--font',str(a.font),'--msdf-source',str(a.msdf_source)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=360)
 build=prep/'build';contours=json.loads((prep/'A/outline.json').read_text())
 if any(len(e)!=2 for c in contours for e in c):raise ValueError('linear A outline required')
 inputs=out/'inputs';inputs.mkdir();shutil.copyfile(prep/'A/atlas.rgba32f',inputs/'msdf.rgba32f');references=[]
 for i,scale in enumerate(SCALES):
  phase=i%4*.25;m.check_bounds(contours,scale,phase)
  polys=[[((e[0][0]-m.W/2)*scale+m.W/2+phase,(e[0][1]-m.H/2)*scale+m.H/2) for e in c] for c in contours]
  reference=[q.exact(polys,x,y) for y in range(m.H) for x in range(m.W)]
  if any(v< -1e-9 or v>1+1e-9 for v in reference):raise ValueError('area out of range')
  reference=[min(1,max(0,v)) for v in reference];references.append(reference)
  rgba=[v for coverage in reference for v in (coverage,coverage,coverage,1.)];(inputs/(str(i)+'.rgba32f')).write_bytes(struct.pack('<'+str(len(rgba))+'f',*rgba))
 header=(build/'msdf_lab_reused.hpp').read_text()
 header=replace(header,'  Image target, velocity, ids, coverage;','  Image target, velocity, ids, coverage, bitmapCoverage;\n  VkDescriptorSet bitmapSet{};VkPipeline bitmapPipeline{};')
 needle='coverage=image(VK_FORMAT_R32G32B32A32_SFLOAT,VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT,VK_IMAGE_ASPECT_COLOR_BIT);'
 header=replace(header,needle,needle+'\n bitmapCoverage=image(VK_FORMAT_R32G32B32A32_SFLOAT,VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT,VK_IMAGE_ASPECT_COLOR_BIT);')
 header=replace(header,'VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1};','VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,2};')
 header=replace(header,'dp.maxSets=1;','dp.maxSets=2;')
 header=replace(header,'    VkAttachmentDescription attachments[3]{};','    VK(vkAllocateDescriptorSets(device,&sa,&bitmapSet));imageInfo.imageView=bitmapCoverage.view;write.dstSet=bitmapSet;vkUpdateDescriptorSets(device,1,&write,0,nullptr);\n    VkAttachmentDescription attachments[3]{};')
 needle='vkDestroyShaderModule(device,vs,nullptr);vkDestroyShaderModule(device,fs,nullptr);VK(result);'
 header=replace(header,needle,'VK(result);auto bfrag=shader("bitmap.frag");stages[1].module=bfrag;VK(vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&bitmapPipeline));vkDestroyShaderModule(device,bfrag,nullptr);'+needle)
 header=replace(header,'vkDestroyPipeline(device,textPipeline,nullptr);','vkDestroyPipeline(device,textPipeline,nullptr);vkDestroyPipeline(device,bitmapPipeline,nullptr);')
 header=replace(header,'for(auto im:{target,velocity,ids,coverage})','for(auto im:{target,velocity,ids,coverage,bitmapCoverage})')
 (out/'switch_helper.hpp').write_text(header);shaders=out/'shaders';shutil.copytree(build/'correct',shaders)
 for source,name,flags in [(HERE/'bitmap.frag','bitmap.frag',[]),(HERE.parent/'text_msdf_integration_lab/integrate.frag','coverage.frag',['-DLINEAR4=1'])]:
  subprocess.run([os.environ.get('GLSLANG','glslangValidator'),'-V','--target-env','vulkan1.2',*flags,str(source),'-o',str(shaders/(name+'.spv'))],check=True,timeout=30)
  subprocess.run([os.environ.get('SPIRV_VAL','spirv-val'),'--target-env','vulkan1.2',str(shaders/(name+'.spv'))],check=True,timeout=30)
 command=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(out),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',str(HERE/'main.cpp'),'-l:libvulkan.so.1','-o',str(out/'switch_lab')];subprocess.run(command,check=True,timeout=180)
 r=subprocess.run([str(out/'switch_lab'),str(shaders),str(inputs),str(out/'frames')],capture_output=True,text=True,timeout=120);(out/'run.log').write_text(r.stdout+r.stderr)
 if r.returncode or 'VALIDATION:' in r.stderr or 'validation_enabled=1' not in r.stdout:raise ValueError('draw/validation failed')
 events=[json.loads(line) for line in (out/'frames/events.jsonl').read_text().splitlines()];expected_routes=routes()
 if events[:10]!=expected_routes:raise ValueError('stateful route mismatch')
 atlas=m.floats(inputs/'msdf.rgba32f',m.W*m.H*4);rows=[];actual_frames=[];preview=m.load(HERE.parent/'text_vector_lab/run_lab.py','preview_switch')
 for i,state in enumerate(expected_routes):
  folder=out/'frames'/str(i);rgba=m.floats(folder/'color.rgba32f',m.W*m.H*4)
  expected=q.sampled(atlas,SCALES[i],i%4*.25,'linear4') if state['selected'] else references[i]
  sample_error=error(rgba,expected)
  if sample_error>(MSDF_TOLERANCE if state['selected'] else BITMAP_TOLERANCE):raise ValueError('representation sampling/composition mismatch')
  actual=[(rgba[4*j+3]-.5)/.375 for j in range(m.W*m.H)]
  actual_frames.append(actual)
  def encode(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
  preview.png(folder/'preview.png',m.W,m.H,bytes(encode(rgba[j*4+c]) for j in range(m.W*m.H) for c in range(3)))
  diff=[abs(x-y) for x,y in zip(actual,references[i])];roi=[j for j,(x,y) in enumerate(zip(actual,references[i])) if x>1e-5 or y>1e-5]
  for file,sentinel in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
   if any(v!=sentinel[j%4] for j,v in enumerate(m.floats(folder/(file+'.rgba32f'),m.W*m.H*4))):raise ValueError('UNUSED sentinel changed')
  rows.append(dict(frame=i,mode='msdf-linear4' if state['selected'] else 'outline-area-bitmap',sample_error=sample_error,exact_area_max_error=max(diff),exact_area_roi_mae=sum(diff[j] for j in roi)/len(roi)))
 bad=m.floats(out/'frames/wrong-hold/color.rgba32f',m.W*m.H*4);negative_error=error(bad,references[2]);negative=events[-1]
 if negative!={'frame':2,'expected':0,'actual':1,'negative':True} or negative['actual']==expected_routes[2]['selected'] or negative_error<=BITMAP_TOLERANCE:raise ValueError('wrong hold route/pixels not detected')
 temporal=[]
 for i in range(1,len(actual_frames)):
  residual=[abs((actual_frames[i][j]-actual_frames[i-1][j])-(references[i][j]-references[i-1][j])) for j in range(m.W*m.H)]
  roi=[j for j in range(m.W*m.H) if max(actual_frames[i][j],actual_frames[i-1][j],references[i][j],references[i-1][j])>1e-5]
  temporal.append(dict(from_frame=i-1,to_frame=i,representation_changed=expected_routes[i]['selected']!=expected_routes[i-1]['selected'],coverage_delta_residual_max=max(residual),coverage_delta_residual_roi_mae=sum(residual[j] for j in roi)/len(roi)))
 result=dict(temporal_delta_residual=temporal,temporal_scope='same-pixel coverage delta minus exact geometric-reference delta; measured only, not perceptual flicker or motion-compensated quality',status='MEASURED_NOT_QUALIFIED',sampling_composition_tolerance={'bitmap':BITMAP_TOLERANCE,'msdf-linear4':MSDF_TOLERANCE},frames=rows,routes=expected_routes,wrong_hold_pixel_error=negative_error,scope='one A glyph shared normalized outline/layout; same-device persistent separate legal bitmap/MSDF images descriptors pipelines; scale/phase only',limits=['bitmap is unhinted exact-outline area, not platform hinted','thresholds are fixed experimental routing not general quality gates','no cache service or asynchronous reuse','no rotation/perspective/target device acceptance'])
 (out/'summary.json').write_text(json.dumps(result,indent=2));(out/'local-provenance.json').write_text(json.dumps(dict(baseline_provenance='baseline/local-provenance.json',sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'main.cpp',HERE/'bitmap.frag',HERE/'run_lab.py',HERE.parent/'text_msdf_integration_lab/run_lab.py',HERE.parent/'text_msdf_integration_lab/integrate.frag']}),indent=2));print(json.dumps(result))
if __name__=='__main__':main()
