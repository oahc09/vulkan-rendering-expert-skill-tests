#!/usr/bin/env python3
import argparse,importlib.util,json,math,os,struct,subprocess,sys,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
P=[(8,8),(40,8),(40,32),(30,32),(30,18),(18,18),(18,32),(8,32)]
COLORS=[(.9,.2,.1),(.1,.2,.9),(.2,.8,.3)]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def inside(x,y):
 yes=False
 for a,b in zip(P,P[1:]+P[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:yes=not yes
 return yes
def reference(x,y):
 hits=[]
 for z,kind in [(0,0),(6,1)]:
  if inside(x-z,y-.5*z):hits.append((z,kind))
 # Ray intersects original boundary extruded along z; independent of triangles.
 for a,b in zip(P,P[1:]+P[:1]):
  ex,ey=b[0]-a[0],b[1]-a[1];det=ey-.5*ex
  if not det:continue
  z=((x-a[0])*ey-(y-a[1])*ex)/det
  t=((y-a[1])-.5*(x-a[0]))/det
  if 0<=z<=6 and 0<=t<=1:hits.append((z,2))
 if not hits:return (.1,.2,.3,1),1.,'background'
 z,kind=min(hits);return (*COLORS[kind],1),.2+.05*z,['front','back','side'][kind]
def verify(folder):
 def read(name,n):
  data=(folder/(name+'.f32')).read_bytes()
  if len(data)!=n*4:raise ValueError('readback size')
  v=struct.unpack('<'+'f'*n,data)
  if not all(math.isfinite(x) for x in v):raise ValueError('nonfinite')
  return v
 color=read('color',W*H*4);depth=read('depth',W*H);ce=de=0;counts={}
 for y in range(H):
  for x in range(W):
   c,d,k=reference(x+.5,y+.5);i=y*W+x;counts[k]=counts.get(k,0)+1;ce=max(ce,*(abs(color[4*i+j]-c[j]) for j in range(4)));de=max(de,abs(depth[i]-d))
 if ce>1e-6 or de>1e-6:raise ValueError('extrusion color/depth mismatch '+str((ce,de)))
 for name,c in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  if any(v!=c[i%4] for i,v in enumerate(read(name,W*H*4))):raise ValueError('MRT sentinel')
 png=load(HERE.parent/'text_vector_lab/run_lab.py','png').png
 def enc(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
 png(folder/'preview.png',W,H,bytes(enc(color[4*i+c]) for i in range(W*H) for c in range(3)))
 return dict(max_color_error=ce,max_depth_error=de,tolerance=1e-6,surface_pixels=counts)
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 active=HERE.parent/'text_active_mrt_lab';run('prepare',[sys.executable,active/'run_lab.py','--out',out/'prepared']);build=out/'prepared/build';s=(build/'active_lab_reused.hpp').read_text()
 def replace(old,new):
  nonlocal s
  if s.count(old)!=1:raise ValueError('helper drift '+old)
  s=s.replace(old,new)
 replace('Image depth;size_t readDepth;','Image depth;size_t readDepth;size_t vertexBuffer=0;uint32_t vertexCount=0;')
 old='VkPipelineVertexInputStateCreateInfo vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};'
 replace(old,old+'VkVertexInputBindingDescription vertexBinding{0,24,VK_VERTEX_INPUT_RATE_VERTEX};VkVertexInputAttributeDescription attrs[2]={{0,0,VK_FORMAT_R32G32B32_SFLOAT,0},{1,0,VK_FORMAT_R32G32B32_SFLOAT,12}};vi.vertexBindingDescriptionCount=1;vi.pVertexBindingDescriptions=&vertexBinding;vi.vertexAttributeDescriptionCount=2;vi.pVertexAttributeDescriptions=attrs;')
 replace('ds.depthTestEnable=VK_TRUE;ds.depthWriteEnable=gBadDepth;ds.depthCompareOp=VK_COMPARE_OP_ALWAYS;','ds.depthTestEnable=!gBadDepth;ds.depthWriteEnable=VK_TRUE;ds.depthCompareOp=VK_COMPARE_OP_LESS;')
 replace('VkClearDepthStencilValue dv{.375f,0};','VkClearDepthStencilValue dv{1.f,0};')
 replace('vkCmdDraw(cb,3,1,0,0);','VkDeviceSize offset=0;vkCmdBindVertexBuffers(cb,0,1,&buffers[vertexBuffer].buffer,&offset);vkCmdDraw(cb,vertexCount,1,0,0);')
 replace('begin();barrier(', 'begin();barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_VERTEX_INPUT_BIT,VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT);barrier(')
 (build/'extrusion_helper.hpp').write_text(s)
 for name,stage in [('extrude.vert','fullscreen.vert'),('extrude.frag','coverage.frag')]:
  run('compile-'+name,[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',HERE/name,'-o',build/'shaders'/(stage+'.spv')]);run('validate-'+name,[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',build/'shaders'/(stage+'.spv')])
 run('compile',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'extrusion'])
 sys.path.insert(0,str(ROOT/'tests'));from bounded_vector_mesh import triangulate
 points,tris=triangulate([[('M',*P[0])]+[('L',*p) for p in P[1:]]+[('Z',)]])
 triangles=[]
 for z,kind in [(0,0),(6,1)]:
  for t in tris:triangles.append([(*points[i],z,*COLORS[kind]) for i in (t[::-1] if kind==0 else t)])
 for a,b in zip(points,points[1:]+points[:1]):
  q=[(*a,0),(*b,0),(*b,6),(*a,6)]
  for t in [(0,1,2),(0,2,3)]:triangles.append([(*q[i],*COLORS[2]) for i in t])
 # Closed-edge count from emitted geometry, independent of face colors.
 edges={};directed={}
 for tri in triangles:
  for a,b in zip(tri,tri[1:]+tri[:1]):
   edge=tuple(sorted((tuple(a[:3]),tuple(b[:3]))));edges[edge]=edges.get(edge,0)+1
   direction=(tuple(a[:3]),tuple(b[:3]));directed[direction]=directed.get(direction,0)+1
 if any(n!=2 for n in edges.values()):raise ValueError('nonclosed extrusion mesh')
 if any(directed.get((a,b),0)!=1 or directed.get((b,a),0)!=1 for a,b in edges):raise ValueError('inconsistent solid winding')
 rows=[]
 for name,ts,mode in [('normal',triangles,'normal'),('reverse',triangles[::-1],'normal'),('no-depth',triangles,'no-depth')]:
  v=[n for t in ts for p in t for n in p];path=out/(name+'.vertices');path.write_bytes(struct.pack('<'+'f'*len(v),*v));log=run(name,[build/'extrusion',build/'shaders',path,out/name,mode])
  if 'validation_enabled=1' not in log:raise ValueError('validation required')
  if mode=='normal':r=verify(out/name);r['case']=name;rows.append(r)
  else:
   try:verify(out/name)
   except ValueError as e:
    if 'color/depth mismatch' not in str(e):raise
   else:raise ValueError('disabled depth not detected')
 summary=dict(status='PASS',validation_enabled=True,triangles=len(triangles),cases=rows,negative='actual disabled depth test rejected',scope='one concave contour finite extrusion with affine oblique projection and actual D32 LESS/write; not world/shadow/bevel pipeline');(out/'summary.json').write_text(json.dumps(summary,indent=2))
 (out/'local-provenance.json').write_text(json.dumps({'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'run_lab.py',HERE/'main.cpp',HERE/'extrude.vert',HERE/'extrude.frag',ROOT/'tests/bounded_vector_mesh.py']},'binary_sha256':hashlib.sha256((build/'extrusion').read_bytes()).hexdigest(),'prepared_provenance':json.loads((out/'prepared/local-provenance.json').read_text()),'generated_helper_sha256':hashlib.sha256((build/'extrusion_helper.hpp').read_bytes()).hexdigest(),'shader_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (build/'shaders').glob('*.spv')}},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
