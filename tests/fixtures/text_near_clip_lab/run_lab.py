#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,math,os,struct,subprocess,sys,shutil
from pathlib import Path
from fractions import Fraction as F
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];FONT_SHA='57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e';TOL=1e-6
X0,X1,Y0,Y1=-1.,1.25,-1.125,1.375
OCC=(.125,1.625,-1.375,1.625,2.)
CASES=[dict(name='cross-near',z=.875,tilt=.5,mode='depth'),dict(name='on-near',z=1.,tilt=0.,mode='depth'),dict(name='behind-near',z=.5,tilt=.125,mode='depth')]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sample(g,c,x,y):
 # Camera ray=(nx,ny,1)*t; plane z=z0+case.tilt*x. Never reads uploaded vertex data.
 rx=F(2*x+1,65)-1;ry=F(2*y+1,49)-1;t=F(c['z'])/(1-F(c['tilt'])*rx);wx,wy=rx*t,ry*t
 cov=0
 if 1<=t<=10 and X0<=wx<X1 and Y0<=wy<Y1:
  w,h=g['size'];sx=math.floor((wx-F(X0))/(F(X1)-F(X0))*w);sy=math.floor((wy-F(Y0))/(F(Y1)-F(Y0))*h);cov=g['pixels'][sy*w+sx]
 ox0,ox1,oy0,oy1,oz=OCC;occluded=ox0<=rx*oz<ox1 and oy0<=ry*oz<oy1
 return cov,occluded,t

def verify(folder,g,c):
 def read(name,count):
  b=(folder/(name+'.f32')).read_bytes()
  if len(b)!=count*4:raise ValueError('size')
  a=struct.unpack('<'+'f'*count,b)
  if not all(math.isfinite(v) for v in a):raise ValueError('nonfinite')
  return a
 col=read('color',12740);depth=read('depth',3185);de=0;err=0;roi=hidden=visible=hole_screen=mismatch_count=0;mismatch_samples=[]
 for n,s in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  if any(v!=s[i%4] for i,v in enumerate(read(n,12740))):raise ValueError('auxiliary')
 for y in range(49):
  for x in range(65):
   cov,occ,t=sample(g,c,x,y);i=y*65+x;bg=(.2,.65,.1,1) if occ else (.1,.2,.3,.5);de=max(de,abs(depth[i]-(5/9 if occ else 1)))
   rx=F(2*x+1,65)-1;ry=F(2*y+1,49)-1;wx,wy=rx*t,ry*t
   if 1<=t<=10 and X0<=wx<X1 and Y0<=wy<Y1:
    w,h=g['size'];sx=math.floor((wx-F(X0))/(F(X1)-F(X0))*w);sy=math.floor((wy-F(Y0))/(F(Y1)-F(Y0))*h);hole_screen+=sy*w+sx in g['hole_indices']
   roi+=cov>0;hidden+=bool(cov and occ and t>2);visible+=bool(cov and not occ)
   if c['mode']=='depth' and occ and t>2:cov=0
   a=cov*.75;expected=[v*a+bg[k]*(1-a) for k,v in enumerate((.9,.5,.2,1))];pixel_error=max(abs(col[4*i+k]-expected[k]) for k in range(4));err=max(err,pixel_error)
   if pixel_error>TOL:
    mismatch_count+=1
    if len(mismatch_samples)<8:mismatch_samples.append({'x':x,'y':y,'error':pixel_error})
 if de>TOL:raise ValueError('depth preservation mismatch '+str(de))
 return dict(name=c['name'],max_composition_error=err,max_depth_preservation_error=de,glyph_roi_pixels=roi,occluded_nonzero_pixels=hidden,unoccluded_nonzero_pixels=visible,projected_zero_hole_pixels=hole_screen,mismatch_count=mismatch_count,first_mismatches=mismatch_samples,excluded_count=0)

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 if a.font.stat().st_size!=759720 or hashlib.sha256(a.font.read_bytes()).hexdigest()!=FONT_SHA:raise ValueError('trusted font')
 (out/'conditions.json').write_text(json.dumps(dict(cases=CASES,world_rectangle=[X0,X1,Y0,Y1],world_plane='z=z0+case.tilt*x',camera='clip=(x,y,(10/9)z-10/9,z); near1 far10',occluder=OCC,size_policy='constant world rectangle; same camera near-domain cases',tolerance=TOL,excluded_count=0),indent=2))
 bitmap=load(HERE.parent/'text_bitmap_lab/run_lab.py','bitmap');mask,receipt=bitmap.raster(a.font,'O','ltr','en')
 if receipt['font_sha256']!=FONT_SHA or [v['id'] for v in receipt['glyphs']]!=[50] or receipt['missing_glyphs'] or receipt['clipped_samples']:raise ValueError('glyph identity/crop mismatch')
 xy=[(i%65,i//65) for i,v in enumerate(mask) if v];x0=min(x for x,y in xy);x1=max(x for x,y in xy)+1;y0=min(y for x,y in xy);y1=max(y for x,y in xy)+1;w,h=x1-x0,y1-y0;g=dict(size=[w,h],pixels=[mask[y*65+x] for y in range(y0,y1) for x in range(x0,x1)])
 if not w or not h or not any(g['pixels']):raise ValueError('empty glyph crop')
 hole_helper=load(HERE.parent/'text_shaped_geometry_lab/run_lab.py','hole_helper');holes=hole_helper.hole_pixels(mask)
 if not holes:raise ValueError('missing O hole')
 g['hole_indices']=[(i//65-y0)*w+i%65-x0 for i in holes]
 sys.path.insert(0,str(ROOT/'tests'));from text_atlas_packing import ShelfAtlas
 atlas=ShelfAtlas(65,49,padding=1,max_pages=1);loc=atlas.publish(atlas.prepare([(w,h,g['pixels'])]))[0];page=atlas.snapshot()[0]
 (out/'atlas.f32').write_bytes(struct.pack('<3185f',*page));(out/'reference.json').write_text(json.dumps(g));(out/'provider-receipt.json').write_text(json.dumps(receipt,indent=2))
 # Register clipped-domain visibility before GPU setup; no hidden ROI required.
 pre=[]
 for c in CASES:
  samples=[sample(g,c,x,y) for y in range(49) for x in range(65)];hidden=sum(bool(v and occ and t>2) for v,occ,t in samples);visible=sum(bool(v and not occ) for v,occ,t in samples)
  count=sum(bool(v) for v,occ,t in samples)
  if (c['name']=='behind-near' and count!=0) or (c['name']!='behind-near' and count==0):raise ValueError('unobservable clip setup')
  pre.append(dict(name=c['name'],hidden=hidden,visible=visible,clipped_domain_nonzero_pixels=count))
 (out/'roi-preflight.json').write_text(json.dumps(pre,indent=2))
 def run(n,args,expected=0):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(n+'.log')).write_text(log)
  if r.returncode!=expected or 'VALIDATION:' in log:raise RuntimeError(n+' failed '+log[-1200:])
  return log
 active=HERE.parent/'text_active_mrt_lab';run('prepare',[sys.executable,active/'run_lab.py','--out',out/'prepared']);build=out/'prepared/build';s=(build/'active_lab_reused.hpp').read_text()
 if 'sc.magFilter = sc.minFilter = VK_FILTER_NEAREST;' not in (build/'engine_active.hpp').read_text():raise ValueError('nearest sampler drift')
 def replace(old,new):
  nonlocal s
  if s.count(old)!=1:raise ValueError('hook drift '+old)
  s=s.replace(old,new)
 replace('struct TextLab: Vulkan {','static bool gAlways=false;\nstruct TextLab: Vulkan {\nsize_t worldBuffer=0;VkPipeline scenePipeline{};')
 old='VkPipelineVertexInputStateCreateInfo vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};'
 replace(old,old+'VkVertexInputBindingDescription bind{0,20,VK_VERTEX_INPUT_RATE_VERTEX};VkVertexInputAttributeDescription attrs[2]={{0,0,VK_FORMAT_R32G32B32_SFLOAT,0},{1,0,VK_FORMAT_R32G32_SFLOAT,12}};vi.vertexBindingDescriptionCount=1;vi.pVertexBindingDescriptions=&bind;vi.vertexAttributeDescriptionCount=2;vi.pVertexAttributeDescriptions=attrs;')
 replace('ds.depthTestEnable=VK_TRUE;ds.depthWriteEnable=gBadDepth;ds.depthCompareOp=VK_COMPARE_OP_ALWAYS;','ds.depthTestEnable=VK_TRUE;ds.depthWriteEnable=VK_FALSE;ds.depthCompareOp=gAlways?VK_COMPARE_OP_ALWAYS:VK_COMPARE_OP_LESS;')
 replace('auto result=vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&textPipeline);','auto result=vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&textPipeline);VK(result);ds.depthWriteEnable=VK_TRUE;ds.depthCompareOp=VK_COMPARE_OP_LESS;VK(vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&scenePipeline));')
 replace('vkDestroyPipeline(device,textPipeline,nullptr);','vkDestroyPipeline(device,textPipeline,nullptr);vkDestroyPipeline(device,scenePipeline,nullptr);')
 replace('VkClearDepthStencilValue dv{.375f,0};','VkClearDepthStencilValue dv{1.f,0};')
 replace('begin();barrier(', 'begin();barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_VERTEX_INPUT_BIT,VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT);barrier(')
 replace('vkCmdDraw(cb,3,1,0,0);','VkDeviceSize offset=0;vkCmdBindVertexBuffers(cb,0,1,&buffers[worldBuffer].buffer,&offset);float scene[]={.2f,.65f,.1f,-1.f};vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,scenePipeline);vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_FRAGMENT_BIT,0,16,scene);vkCmdDraw(cb,6,1,0,0);vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,textPipeline);vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_FRAGMENT_BIT,0,16,rgba);vkCmdDraw(cb,6,1,6,0);')
 (build/'world_helper.hpp').write_text(s);run('compile',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'world'])
 # Verify integer arithmetic domain before compiling any stable sampling variant.
 integer_max=0
 for c in CASES:
  znum=int(c['z']*8);knum=int(c['tilt']*8)
  for yy in range(49):
   for xx in range(65):
    nx=2*xx-64;ny=2*yy-48;d=520-knum*nx
    values=[znum*nx+d,4*w*(znum*nx+d),9*d,8*znum*65*ny,9*49*d,h*(8*znum*65*ny+9*49*d),20*49*d]
    if d<=0 or any(abs(v)>=2**31 for v in values):raise ValueError('stable sampler int32 budget')
    integer_max=max(integer_max,*(abs(v) for v in values))
 folders={}
 modes=['normal','uv-debug']+['stable-'+c['name'] for c in CASES]+['stable-clamp-'+c['name'] for c in CASES]
 for mode in modes:
  folder=out/(mode+'-shaders');folder.mkdir();folders[mode]=folder
  for f in (build/'shaders').glob('*.spv'):shutil.copy2(f,folder/f.name)
  for name,target in [('world.vert','fullscreen.vert'),('world.frag','coverage.frag')]:
   src=(HERE/name).read_text();src=src.replace('// INTERPOLATION\nlayout(location=0)','layout(location=0)')
   if mode.startswith('stable-clamp-') and name=='world.vert':
    if src.count('uv=atlasUV;')!=1:raise ValueError('vertex hook drift')
    src=src.replace('uv=atlasUV;','if(atlasUV.x>0&&atlasUV.y>0)gl_Position.z=max(gl_Position.z,0.0);uv=atlasUV;')
   if mode.startswith('stable-') and name=='world.frag':
    c=next(c for c in CASES if mode.endswith(c['name']));znum=int(c['z']*8);knum=int(c['tilt']*8)
    function=f'''float stableCoverage(){{
 int nx=2*int(gl_FragCoord.x)-64,ny=2*int(gl_FragCoord.y)-48;
 int d=520-{knum}*nx;int ax=4*{w}*({znum}*nx+d),bx=9*d;
 int ay={h}*(8*{znum}*65*ny+9*49*d),by=20*49*d;
 if(d<=0||ax<0||ay<0)return 0;int ix=ax/bx,iy=ay/by;
 if(ix<0||ix>={w}||iy<0||iy>={h})return 0;
 return texelFetch(glyphCoverage,ivec2({loc.x}+ix,{loc.y}+iy),0).r;
 }}
'''
    if src.count('void main()')!=1 or src.count('texture(glyphCoverage,uv).r')!=1:raise ValueError('stable shader hook drift')
    src=src.replace('void main()',function+'void main()').replace('texture(glyphCoverage,uv).r','stableCoverage()')
   if mode=='uv-debug' and name=='world.frag':
    hook='float c=texture(glyphCoverage,uv).r;float a=c*p.ink.a;color=vec4(p.ink.rgb*a,a);'
    if src.count(hook)!=1:raise ValueError('UV debug hook drift')
    src=src.replace(hook,'color=vec4(uv,0,1);')
   file=folder/name;file.write_text(src);run(mode+'-'+name,[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',file,'-o',folder/(target+'.spv')]);run(mode+'-validate-'+name,[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',folder/(target+'.spv')])
 def vertices(c):
  values=[]
  for kind in (0,1):
   for u,v in [(0,0),(1,0),(0,1),(0,1),(1,0),(1,1)]:
    if kind:x=X0+u*(X1-X0);y=Y0+v*(Y1-Y0);z=c['z']+c['tilt']*x;uv=((loc.x+u*w)/65,(loc.y+v*h)/49)
    else:x=OCC[0]+u*(OCC[1]-OCC[0]);y=OCC[2]+v*(OCC[3]-OCC[2]);z=OCC[4];uv=(0.,0.)
    if kind and not (uv[0]>0 and uv[1]>0):raise ValueError('label marker must be positive')
    if not kind and uv!=(0.,0.):raise ValueError('scene marker must be zero')
    values.extend((x,y,z,*uv))
  return values
 def draw(name,c,shader='normal',mode=None):
  f=out/(name+'.vertices');f.write_bytes(struct.pack('<60f',*vertices(c)));log=run(name,[build/'world',folders[shader],out/'atlas.f32',f,out/name,mode or c['mode']])
  if 'validation_enabled=1' not in log:raise ValueError('validation absent')
 hardware=[]
 for c in CASES:
  name='hardware-'+c['name'];draw(name,c);hardware.append(verify(out/name,g,c))
 draw('uv-diagnostic',CASES[0],'uv-debug');uv_checks=verify(out/'uv-diagnostic',g,CASES[0])
 uv_col=struct.unpack('<12740f',(out/'uv-diagnostic/color.f32').read_bytes());index=4*(10*65+45);actual_uv=uv_col[index:index+2]
 rx=F(2*45+1,65)-1;ry=F(2*10+1,49)-1;t=F(CASES[0]['z'])/(1-F(CASES[0]['tilt'])*rx)
 exact_source=[(rx*t-F(X0))/(F(X1)-F(X0))*w,(ry*t-F(Y0))/(F(Y1)-F(Y0))*h]
 uv_diagnostic={'pixel':[45,10],'actual_uv':list(actual_uv),'actual_source_texel_coordinate':[actual_uv[0]*65-loc.x,actual_uv[1]*49-loc.y],'exact_source_texel_coordinate':[float(v) for v in exact_source],'exact_source_fractions':[str(v) for v in exact_source],'max_depth_preservation_error':uv_checks['max_depth_preservation_error'],'auxiliary_check':'exact','purpose':'separate actual UV readback; not a positive glyph composition'}
 rows=[]
 for c in CASES:
  draw(c['name'],c,'stable-'+c['name']);r=verify(out/c['name'],g,c)
  if c['name']!='behind-near' and not r['projected_zero_hole_pixels']:raise ValueError('projected hole absent')
  if r['max_composition_error']>TOL:raise ValueError('world oracle mismatch '+json.dumps(r))
  rows.append(r)
 neg=[]
 for name,c,shader,mode in [('wrong-clamp-cross',CASES[0],'stable-clamp-cross-near','depth'),('wrong-clamp-behind',CASES[2],'stable-clamp-behind-near','depth')]:
  draw(name,c,shader,mode);r=verify(out/name,g,c)
  if r['max_composition_error']<=TOL:raise ValueError('negative invisible')
  neg.append(dict(mode=name,**r))
 rejects=[]
 for name,value in [('nonpositive-w',0.0),('nonfinite',float('nan'))]:
  v=vertices(CASES[0]);v[6*5+2]=value;f=out/(name+'.vertices');f.write_bytes(struct.pack('<60f',*v));log=run(name,[build/'world',folders['normal'],out/'atlas.f32',f,out/name,'depth'],1)
  expected_reason='nonfinite' if name=='nonfinite' else 'positive-w/coordinate budget'
  if expected_reason not in log:raise ValueError('unexpected rejection reason')
  if (out/name).exists():raise ValueError('rejection reached GPU')
  rejects.append(name)
 summary=dict(status='BOUNDED_REAL_NEAR_CLIP_STABLE_SAMPLING_PASS',hardware_nearest_status='NOT_QUALIFIED' if any(r['max_composition_error']>TOL for r in hardware) else 'PASS_ON_THIS_RUN',hardware_nearest_cases=hardware,uv_diagnostic=uv_diagnostic,stable_sampler_max_integer_magnitude=integer_max,validation_enabled=True,tolerance=TOL,glyph_id=50,source_hole_pixels=len(holes),cases=rows,actual_gpu_negatives=neg,input_rejections_before_gpu=rejects,size_policy='fixed world extent, same camera, cross/on/outside near-domain',scope='fixed actual shaped O bitmap, hardware-nearest diagnosis plus integer-ray texelFetch fallback and real Vulkan clip of positive-w triangles at near1; no behind-eye/complex topology/shadow/general renderer')
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-provenance.json').write_text(json.dumps(dict(sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'main.cpp',HERE/'run_lab.py',HERE/'world.vert',HERE/'world.frag',HERE.parent/'text_bitmap_lab/run_lab.py',HERE.parent/'text_shaped_geometry_lab/run_lab.py',ROOT/'tests/text_atlas_packing.py']},generated_helper_sha=hashlib.sha256(s.encode()).hexdigest(),binary_sha=hashlib.sha256((build/'world').read_bytes()).hexdigest(),shader_sha={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.glob('*-shaders/*.spv')},provider_receipt=receipt,prepared=json.loads((out/'prepared/local-provenance.json').read_text())),indent=2))
 png=load(HERE.parent/'text_vector_lab/run_lab.py','png').png
 for c in CASES:
  vals=struct.unpack('<12740f',(out/c['name']/'color.f32').read_bytes());png(out/c['name']/'preview.png',65,49,bytes(round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055)) for i,v in enumerate(vals) if i%4!=3))
 print(json.dumps(summary))
if __name__=='__main__':main()
