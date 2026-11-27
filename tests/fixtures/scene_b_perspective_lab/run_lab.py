import argparse,hashlib,importlib.util,json,os,struct,subprocess,sys,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 def run(n,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(n+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(n+' failed '+log[-1200:])
  return log
 run('prepare',[sys.executable,HERE.parent/'scene_b_vector_overlay_lab/run_lab.py','--font',a.font,'--out',out/'prepared'])
 old=load(HERE.parent/'text_shadow_lab/run_lab.py','old');provider=load(HERE.parent/'text_msdf_lab/run_lab.py','provider');geom=load(HERE.parent/'scene_b_vector_overlay_lab/geometry.py','geom');ref=load(HERE/'reference.py','ref');builder=load(HERE/'build.py','builder')
 contours,r=provider.outlines(a.font,'L');poly=[(e[0][0]+.25,e[0][1]+.25) for e in contours[0]]
 inputs=out/'prepared/prepared';page=old.floats(inputs/'mask.f32',3185);g=[page[y*65+x] for y in range(15) for x in range(14)]
 boundary=ref.boundary_centers();assert boundary=={'offset0-mirror0':[{'axis':'x','source':43,'pixel':52,'included':False}],'offset0-mirror1':[{'axis':'x','source':43,'pixel':12,'included':False}],'offset2-mirror0':[],'offset2-mirror1':[]}
 (out/'boundary-preflight.json').write_text(json.dumps(boundary,indent=2))
 variants=[('baseline',1,False,1,False),('near-cross',22,False,22,False),('reflected',1,True,1,False),('wrong-near',22,False,1,False),('wrong-caster-model',1,True,1,True)]
 refs={};pre={}
 for name,near,mirror,actualnear,badshadow in variants:
  sourcepoly=[(65-x if mirror else x,y) for x,y in poly];shadow=old.shadow_reference(sourcepoly)
  frames={n:ref.frame(poly,g,shadow,offset,near,mirror) for n,offset in [('A',0),('B',2)]};refs[name]=(shadow,frames)
  if name in ('baseline','reflected'):
   assert all(all(v>0 for v in f[2].values()) for f in frames.values())
  if name=='near-cross':assert all(f[2]['cap']>0 and f[2]['side']>0 and f[2]['label_visible']>0 for f in frames.values())
  pre[name]={n:f[2] for n,f in frames.items()}
 (out/'preflight.json').write_text(json.dumps(pre,indent=2))
 names=['A','B','B-no-shadow','B-stale-label','B-no-rect','B-no-circle','B-no-rotated','B-filled-hole','B-butt','B-same-evenodd','B-same-nonzero','B-opposite-evenodd'];results={};ok=True
 for name,near,mirror,actualnear,badshadow in variants:
  b=builder.build(inputs/'prepared/build',out/(name+'-build'),actualnear,mirror,badshadow,run)
  log=run(name,[b/'combined',b/'shaders',inputs/'mesh.f32',inputs/'mask.f32',out/name]);assert 'validation_enabled=1' in log
  shadow,frames=refs[name];se=max(abs(x-y) for x,y in zip(old.floats(out/name/'shadow.f32',3185),shadow));rows={}
  for index,n in enumerate(names):
   d=out/name/n;f=frames['A' if n=='A' else 'B'];expected=geom.overlay(f[0],index-3 if index>=9 else 0)
   for key,sentinel in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
    if any(v!=sentinel[i%4] for i,v in enumerate(old.floats(d/(key+'.f32'),12740))):raise ValueError('aux')
   depth=old.floats(d/'depth.f32',3185);de=max(abs(x-y) for x,y in zip(depth,f[1]));c=old.floats(d/'color.f32',12740);ce=max(abs(x-y) for x,y in zip(c,expected));positive=index in (0,1,9,10,11)
   rows[n]=dict(color_error=ce,depth_error=de,positive_view=positive)
   if name not in ('wrong-near','wrong-caster-model'):ok&=de<=1e-6 and (ce<=1e-6)==positive
   raw=b''.join(b'\0'+bytes(round(max(0,min(1,c[(y*65+x)*4+j]))*255) for x in range(65) for j in range(3)) for y in range(49))
   def chunk(k,v):return struct.pack('>I',len(v))+k+v+struct.pack('>I',zlib.crc32(k+v))
   (d/'preview.png').write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',65,49,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
  if name=='wrong-near':ok&=se<=1e-6 and all(rows[n]['depth_error']>1e-6 and rows[n]['color_error']>1e-6 for n in ('A','B'))
  elif name=='wrong-caster-model':ok&=se>1e-6 and all(rows[n]['depth_error']<=1e-6 and rows[n]['color_error']>1e-6 for n in ('A','B'))
  else:ok&=se<=1e-6
  results[name]=dict(shadow_depth_error=se,views=rows)
 summary=dict(status='PASS' if ok else 'NOT_QUALIFIED',validation_enabled=True,excluded=0,tolerance=1e-6,variants=results,preflight=pre,boundary_centers=boundary,scope='True perspective w and fixed-function clip with specialized rational reconstruction; variants each independent Device internally shared world/vector/shadow scene.')
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'source-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*') if p.is_file()},indent=2));print(json.dumps(summary))
 if not ok:raise ValueError('perspective scene gate')
if __name__=='__main__':main()
