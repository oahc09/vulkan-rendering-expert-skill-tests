#!/usr/bin/env python3
"""Bounded real-content single-device churn, not locale/variation certification."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
CASES=[('O','ltr','en',14),('ffi','ltr','en',20),('سلام','rtl','ar',14),('O','ltr','tr',24),('ffi','ltr','en',14),('سلام','rtl','ar',20),('O','ltr','en',20)]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out):
 quad=load(HERE.parent/'text_packed_quad_lab/run_lab.py','oracle');events=[];rows=[]
 for i in range(1,7):
  events.extend([dict(round=i,phase='pending_cancel',published=2*(i-1),live_pages=2,pending=2),dict(round=i,phase='retired',published=2*i,live_pages=1,submission_resources=0,page_objects=1)])
  for stage,index in [('old',i-1),('retained',i-1),('new',i)]:
   r=quad.verify(out/'inputs'/str(index),out/'frames'/str(i)/stage);r.update(round=i,stage=stage);rows.append(r)
 if [json.loads(s) for s in (out/'frames/events.jsonl').read_text().splitlines()]!=events:raise ValueError('lifecycle events mismatch')
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 def run(name,args,expected=0):
  r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode!=expected or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 # Prepare unchanged shared graphics pipeline; its separate run is not churn evidence.
 combined=HERE.parent/'text_combined_lifecycle_lab';run('prepare',[sys.executable,combined/'run_lab.py','--out',out/'prepared','--font',a.font]);build=out/'prepared/prepared/build'
 quad=load(HERE.parent/'text_packed_quad_lab/run_lab.py','quad');bitmap=load(HERE.parent/'text_bitmap_lab/run_lab.py','bitmap')
 import freetype
 face=freetype.Face(str(a.font));font_info={'font_sha256':sha(a.font),'has_multiple_masters':face.has_multiple_masters,'variation_status':'UNVERIFIED' if face.has_multiple_masters else 'BLOCKED_NO_AXES_IN_TRUSTED_FONT'}
 receipts=[]
 for i,(text,direction,language,size) in enumerate(CASES):
  folder=out/'inputs'/str(i);folder.mkdir(parents=True);mask,receipt=bitmap.raster(a.font,text,direction,language,pixel_size=size);receipts.append(receipt)
  xy=[(k%W,k//W) for k,v in enumerate(mask) if v];x0=min(x for x,y in xy);y0=min(y for x,y in xy);w=max(x for x,y in xy)+1-x0;h=max(y for x,y in xy)+1-y0
  pixels=[mask[(y0+y)*W+x0+x] for y in range(h) for x in range(w)];atlas=[0.]*(W*H)
  if w+2>W or h+2>H:raise ValueError('padding budget')
  for y in range(h):
   for x in range(w):atlas[(y+1)*W+x+1]=pixels[y*w+x]
  dx,dy=3+(i%3)*2,5+(i%2)*3;verts=[]
  for x,y in [(0,0),(w,0),(0,h),(0,h),(w,0),(w,h)]:verts.extend([2*(dx+x)/W-1,2*(dy+y)/H-1,(1+x)/W,(1+y)/H])
  quad.raw(folder/'atlas.f32',atlas);quad.raw(folder/'vertices.f32',verts);(folder/'reference.json').write_text(json.dumps({'glyphs':[dict(size=[w,h],pixels=pixels,destination=[dx,dy])]}))
 hashes=[sha(out/'inputs'/str(i)/'atlas.f32') for i in range(7)]
 if len(set(hashes))!=7:raise ValueError('content pages must differ')
 (out/'input-hashes.json').write_text(json.dumps(hashes))
 (out/'provider-receipts.json').write_text(json.dumps(receipts,indent=2));(out/'font-availability.json').write_text(json.dumps(font_info,indent=2))
 source=(combined/'main.cpp').read_text()
 if source.count('int main(int argc,char**argv)')!=1:raise ValueError('combined hook changed')
 (build/'combined_source.hpp').write_text(source.replace('int main(int argc,char**argv)','int original_combined_main(int argc,char**argv)'));cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build)]
 if os.environ.get('VULKAN_SDK_PREFIX'):cmd+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
 run('compile',cmd+[HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'content_churn']);args=[build/'content_churn',build/'shaders',out/'inputs',out/'frames'];log=run('vulkan',args)
 if 'validation_enabled=1' not in log or 'CONTENT_CHURN_DESTROYED' not in log:raise ValueError('validation/cleanup missing')
 rows=verify(out);before=sha(out/'frames/events.jsonl');run('refuse-overwrite',args,1)
 if before!=sha(out/'frames/events.jsonl'):raise ValueError('overwritten')
 summary={'status':'PASS','validation_enabled':True,'rounds':6,'actual_draw_count':18,'actual_upload_count':13,'rows':rows,'variation':font_info['variation_status'],'scope':'one Vulkan device and queue, actual differently shaped/rasterized content UV run-quads; bounded six transitions','locale':'language passed to HarfBuzz only; no locale-specific difference claim','limits':['composited run bitmap quad, not per-glyph geometry','nearest integer sampling','software Vulkan only','ALL_COMMANDS gate blocks queued work; not shader executing','fixture resource counts not driver leak proof','no full allocation/device-loss cleanup','no mobile/DirectWrite/MSDF/Live acceptance']}
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-provenance.json').write_text(json.dumps({'sources':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'main.cpp',HERE/'run_lab.py',combined/'main.cpp',combined/'run_lab.py',HERE.parent/'text_bitmap_lab/run_lab.py',ROOT/'tests/platform_text_probe.py',HERE.parent/'text_packed_quad_lab/run_lab.py']},'binary_sha256':sha(build/'content_churn'),'prepared_receipt':json.loads((out/'prepared/local-provenance.json').read_text())},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
