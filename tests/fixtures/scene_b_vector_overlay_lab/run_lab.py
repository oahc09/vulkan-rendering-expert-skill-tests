import argparse,hashlib,importlib.util,json,math,os,struct,subprocess,sys,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 geom=load(HERE/'geometry.py','geom');counts=geom.preflight();assert counts==dict(negative_1=36,negative_2=91,negative_3=35,negative_4=256,negative_5=12,path_only=297,stroke_only=68,hole_kept=256)
 (out/'preflight.json').write_text(json.dumps(counts,indent=2))
 def run(n,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(n+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(n+' failed '+log[-1600:])
  return log
 base=load(HERE.parent/'scene_b_shared_world_lab/run_lab.py','base');old=load(HERE.parent/'text_shadow_lab/run_lab.py','old')
 run('prepare-shared',[sys.executable,HERE.parent/'scene_b_shared_world_lab/run_lab.py','--font',a.font,'--out',out/'prepared'])
 b=out/'prepared/prepared/build';load(HERE/'build.py','build').build(b,run)
 provider=load(HERE.parent/'text_msdf_lab/run_lab.py','provider');contours,r=provider.outlines(a.font,'L');poly=[(e[0][0]+.25,e[0][1]+.25) for e in contours[0]]
 page=old.floats(out/'prepared/mask.f32',3185);g=[page[y*65+x] for y in range(15) for x in range(14)];shadow=old.shadow_reference(poly)
 refs={n:base.reference(poly,g,shadow,k,l) for n,k,l in [('A',.25,.125),('B',-.25,.25)]}
 # Preflight overlay cannot hide earlier world failures.
 olderrors={}
 for n in ['B-no-shadow','B-stale-label']:
  baseline=old.floats(out/'prepared/gpu'/n/'color.f32',12740);olderrors[n]=max(abs(x-y) for x,y in zip(geom.overlay(baseline),geom.overlay(refs['B'][0])))
 assert all(v>1e-6 for v in olderrors.values())
 log=run('actual',[b/'combined',b/'shaders',out/'prepared/mesh.f32',out/'prepared/mask.f32',out/'gpu']);assert 'validation_enabled=1' in log
 se=max(abs(x-y) for x,y in zip(old.floats(out/'gpu/shadow.f32',3185),shadow));rows={}
 names=['A','B','B-no-shadow','B-stale-label','B-no-rect','B-no-circle','B-no-rotated','B-filled-hole','B-butt','B-same-evenodd','B-same-nonzero','B-opposite-evenodd']
 for index,n in enumerate(names):
  d=out/'gpu'/n;ref=refs['A' if n=='A' else 'B'];mode=index-3 if index>=9 else 0;expected=geom.overlay(ref[0],mode)
  for key,sentinel in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
   if any(v!=sentinel[i%4] for i,v in enumerate(old.floats(d/(key+'.f32'),12740))):raise ValueError('aux preservation')
  depth=old.floats(d/'depth.f32',3185);de=max(abs(x-y) for x,y in zip(depth,ref[1]));assert de<=1e-6
  c=old.floats(d/'color.f32',12740);err=max(abs(x-y) for x,y in zip(c,expected));rows[n]=dict(color_error=err,depth_error=de,positive=index in (0,1,9,10,11))
  raw=b''.join(b'\0'+bytes(round(max(0,min(1,c[(y*65+x)*4+j]))*255) for x in range(65) for j in range(3)) for y in range(49))
  def chunk(k,v):return struct.pack('>I',len(v))+k+v+struct.pack('>I',zlib.crc32(k+v))
  (d/'preview.png').write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',65,49,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
 ok=se<=1e-6 and all((r['color_error']<=1e-6)==r['positive'] for r in rows.values())
 summary=dict(status='PASS' if ok else 'NOT_QUALIFIED',validation_enabled=True,tolerance=1e-6,excluded=0,shadow_depth_error=se,cases=rows,preflight=counts,world_negative_post_overlay_errors=olderrors,positive_views=5,negative_views=7,camera_pass_draws=5,light_producers=1)
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'source-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*HERE.glob('*'),* (HERE.parent/'scene_b_shared_world_lab').glob('*'),b/'combined'] if p.is_file()},indent=2));print(json.dumps(summary))
 if not ok:raise ValueError('shared vector scene numerical gate')
if __name__=='__main__':main()
