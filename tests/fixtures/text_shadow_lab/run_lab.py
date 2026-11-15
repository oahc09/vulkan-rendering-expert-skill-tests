#!/usr/bin/env python3
"""Finite true depth producer -> sampled hard-shadow receiver, no CPU reupload."""
import argparse,hashlib,importlib.util,json,math,os,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];TOL=1e-6
FONT_SHA='57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e'
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inside(p,poly):
 x,y=p;yes=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:yes=not yes
 return yes
def shadow_reference(poly):
 # Independent ray against source contour cap/side planes, never mesh triangles.
 def cross(a,b):return a[0]*b[1]-a[1]*b[0]
 result=[]
 for y in range(49):
  for x in range(65):
   q=(x+.5,y+.5);hits=[]
   for z in (0,6):
    if inside((q[0]-.5*z,q[1]-.25*z),poly):hits.append(z)
   for a,b in zip(poly,poly[1:]+poly[:1]):
    e=(b[0]-a[0],b[1]-a[1]);v=(.5,.25);den=cross(v,e)
    if den==0:continue
    z=cross((q[0]-a[0],q[1]-a[1]),e)/den
    u=((q[0]-.5*z-a[0])*e[0]+(q[1]-.25*z-a[1])*e[1])/(e[0]**2+e[1]**2)
    if 0<=z<=6 and 0<=u<=1:hits.append(z)
   result.append(min(hits)/16 if hits else 1.)
 return result
def floats(p,n):
 b=p.read_bytes()
 if len(b)!=n*4:raise ValueError('readback size')
 a=struct.unpack('<'+'f'*n,b)
 if not all(math.isfinite(v) for v in a):raise ValueError('nonfinite readback')
 return a
def verify(folder,ref):
 for name,exp in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  if any(v!=exp[i%4] for i,v in enumerate(floats(folder/(name+'.f32'),12740))):raise ValueError('auxiliary preservation')
 depth_error=max(abs(v-.375) for v in floats(folder/'depth.f32',3185))
 if depth_error>TOL:raise ValueError('receiver depth preservation')
 actual=floats(folder/'shadow.f32',3185);de=max(abs(a-b) for a,b in zip(actual,ref))
 expected=[];dark=0
 for y in range(49):
  for x in range(65):
   # floor(pixelcenter + fixed receiver light offset), NOT implicit clamp.
   xx=x+5;yy=y+3;blocked=xx<65 and yy<49 and .625>ref[yy*65+xx];dark+=blocked
   expected.extend((.2,.15,.1,1) if blocked else (.8,.6,.4,1))
 color=floats(folder/'color.f32',12740);ce=max(abs(a-b) for a,b in zip(color,expected))
 bad=[{'x':i%65,'y':i//65,'expected':b,'actual':a} for i,(a,b) in enumerate(zip(actual,ref)) if abs(a-b)>TOL]
 return {'max_shadow_depth_error':de,'max_composition_error':ce,'receiver_depth_error':depth_error,'shadowed_receiver_pixels':dark,'shadow_depth_mismatches':bad,'excluded_count':0}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);a=p.parse_args()
 if not a.font.is_file() or a.font.stat().st_size!=759720 or sha(a.font)!=FONT_SHA:raise ValueError('trusted font before parse')
 out=a.out.resolve();out.mkdir(exist_ok=False)
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(name+' failed')
  return log
 run('prepare',[sys.executable,HERE.parent/'text_active_mrt_lab/run_lab.py','--out',out/'prepared'])
 build=out/'prepared/build'
 helper=(build/'active_lab_reused.hpp').read_text()
 for required in ['ds.depthCompareOp=VK_COMPARE_OP_ALWAYS','ds.depthWriteEnable=gBadDepth','static bool gBadMask=false,gBadDepth=false','blends[i].colorWriteMask=gBadMask?15:0']:
  if helper.count(required)!=1:raise ValueError('receiver state hook changed: '+required)
 for src,dest in [('shadow.vert','shadow.vert'),('receiver.frag','coverage.frag')]:
  run('compile-'+src,[os.environ.get('GLSLANG','glslangValidator'),'-V','--target-env','vulkan1.2',HERE/src,'-o',build/'shaders'/(dest+'.spv')]);run('validate-'+src,[os.environ.get('SPIRV_VAL','spirv-val'),'--target-env','vulkan1.2',build/'shaders'/(dest+'.spv')])
 cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build)]
 if os.environ.get('VULKAN_SDK_PREFIX'):cmd+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
 run('compile-main',cmd+[HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'shadow'])
 provider=load(HERE.parent/'text_msdf_lab/run_lab.py','provider');shaped=load(HERE.parent/'text_shaped_geometry_lab/run_lab.py','shaped')
 sys.path.insert(0,str(ROOT/'tests'))
 try:from bounded_vector_mesh import triangulate
 finally:sys.path.pop(0)
 polys={};receipts={};tri_counts={}
 for letter,gid in [('L',47),('F',41)]:
  contours,receipt=provider.outlines(a.font,letter)
  if len(contours)!=1 or [g['id'] for g in receipt['glyphs']]!=[gid] or any(len(e)!=2 for e in contours[0]):raise ValueError('actual shaped identity/line subset')
  contours=[[[[x+.25,y+.25] for x,y in edge] for edge in contour] for contour in contours]
  poly,tris=triangulate(shaped.paths(contours));vertices,count=shaped.closed_mesh(poly,tris,[(1,1,1)]*3)
  # Oracle uses original contour, not triangulate output.
  polys[letter]=[tuple(e[0]) for e in contours[0]];receipts[letter]=receipt;tri_counts[letter]=count
  (out/(letter+'.vertices')).write_bytes(struct.pack('<'+'f'*len(vertices),*vertices))
 (out/'provider-receipts.json').write_text(json.dumps(receipts,indent=2));(out/'source-polygons.json').write_text(json.dumps(polys))
 ref=shadow_reference(polys['L']);rows={}
 for name,letter,mode in [('normal','L','normal'),('bypass','L','bypass'),('wrong-caster','F','normal')]:
  log=run(name,[build/'shadow',build/'shaders',out/(letter+'.vertices'),out/name,mode])
  if 'validation_enabled=1' not in log:raise ValueError('validation required')
  rows[name]=verify(out/name,ref)
 negative_ok=rows['bypass']['max_shadow_depth_error']<=TOL and rows['bypass']['max_composition_error']>TOL and rows['wrong-caster']['max_shadow_depth_error']>TOL and rows['wrong-caster']['max_composition_error']>TOL
 summary={'status':'PASS' if negative_ok and rows['normal']['max_shadow_depth_error']<=TOL and rows['normal']['max_composition_error']<=TOL else 'NOT_QUALIFIED','validation_enabled':True,'tolerance':TOL,'excluded_count':0,'device_instances_per_case':1,'passes_per_case':2,'cases':rows,'glyph_ids':{'positive':47,'wrong_caster':41},'triangles':tri_counts,'receiver_z':10,'bias':0,'scope':'fixed orthographic hard shadow, actual D32 producer sampled directly; no visible caster lighting or full Scene B'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 # Local provenance only; inherited preparation captures tool/driver versions/hashes.
 sources=[*HERE.glob('*')]+[HERE.parent/'text_shaped_geometry_lab/run_lab.py',HERE.parent/'text_msdf_lab/run_lab.py',ROOT/'tests/bounded_vector_mesh.py']
 (out/'source-hashes.json').write_text(json.dumps({str(p):sha(p) for p in sources if p.is_file()},indent=2))
 (out/'binary-hash.json').write_text(json.dumps({'sha256':sha(build/'shadow')}))
 import zlib
 c=floats(out/'normal/color.f32',12740)
 raw=b''.join(b'\0'+bytes(round(max(0,min(1,c[(y*65+x)*4+j]))*255) for x in range(65) for j in range(3)) for y in range(49))
 def chunk(k,v):return struct.pack('>I',len(v))+k+v+struct.pack('>I',zlib.crc32(k+v))
 (out/'receiver.png').write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',65,49,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
 print(json.dumps(summary))
 if summary['status']!='PASS':raise ValueError('positive shadow not qualified; evidence retained')
 if rows['bypass']['max_shadow_depth_error']>TOL or rows['bypass']['max_composition_error']<=TOL:raise ValueError('bypass negative category')
 if rows['wrong-caster']['max_shadow_depth_error']<=TOL or rows['wrong-caster']['max_composition_error']<=TOL:raise ValueError('wrong caster negative category')
if __name__=='__main__':main()
