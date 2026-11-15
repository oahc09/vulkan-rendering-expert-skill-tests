#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,math,os,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
FONTS={'serif':Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'),'sans':Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),'cjk':Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')}
RUNS=[('ffi','ltr','en',(2,2)),('a\u0301','ltr','en',(38,2)),('سلام','rtl','ar',(2,20)),('中文','ltr','zh',(2,35))]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fallback(adapter,text,direction,language,fonts=FONTS):
 attempts=[]
 for key,path in fonts.items():
  r=adapter.shape(path,text,direction=direction,language=language,key=key)
  attempts.append({'face':key,'missing':r['missing_glyphs'],'glyph_ids':[g['id'] for g in r['glyphs']]})
  if r['glyphs'] and not r['missing_glyphs']:return key,r,attempts
 raise ValueError('no fallback face covers complete run')
def raster(adapter,key,r):
 expected_sha,_,expected_index=adapter.FACES[key]
 if r['font_sha256']!=expected_sha or r['face_index']!=expected_index:raise ValueError('shape face identity mismatch before raster')
 import freetype
 face=freetype.Face(str(FONTS[key]),index=adapter.guard(FONTS[key],key));face.set_pixel_sizes(0,14)
 if key=='cjk' and face.family_name!=b'Noto Sans CJK SC':raise ValueError('CJK SC face identity')
 pixels={};penx=0.;peny=0.;scale=14/r['upem'];placements=[]
 for g in r['glyphs']:
  if not 0<g['id']<face.num_glyphs:raise ValueError('glyph face range')
  face.load_glyph(g['id'],freetype.FT_LOAD_RENDER|freetype.FT_LOAD_TARGET_NORMAL);slot=face.glyph;b=slot.bitmap
  if b.pixel_mode!=freetype.FT_PIXEL_MODE_GRAY or b.pitch<0 or b.num_grays!=256:raise ValueError('gray bitmap only')
  x=round(penx+g['x_offset']*scale)+slot.bitmap_left;y=round(peny-g['y_offset']*scale)-slot.bitmap_top
  for yy in range(b.rows):
   for xx in range(b.width):
    c=b.buffer[yy*b.pitch+xx]/255
    if c:pixels[x+xx,y+yy]=c+pixels.get((x+xx,y+yy),0)*(1-c)
  placements.append({'glyph':g['id'],'x':x,'y':y,'face':key,'face_index':r['face_index']});penx+=g['x_advance']*scale;peny-=g['y_advance']*scale
 if not pixels:raise ValueError('blank run')
 x0=min(x for x,y in pixels);y0=min(y for x,y in pixels);w=max(x for x,y in pixels)-x0+1;h=max(y for x,y in pixels)-y0+1
 if w>60 or h>18:raise ValueError('run bitmap budget')
 return {'size':[w,h],'pixels':[pixels.get((x+x0,y+y0),0) for y in range(h) for x in range(w)],'placements':placements,'face':key,'face_index':r['face_index'],'font_sha256':r['font_sha256']}
def aux(gpu):
 for name,exp in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  b=(gpu/(name+'.rgba32f')).read_bytes()
  if len(b)!=12740*4:raise ValueError('aux size')
  if any(v!=exp[i%4] for i,v in enumerate(struct.unpack('<12740f',b))):raise ValueError('aux changed')
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 adapter=load(HERE/'adapter.py','fallback_adapter');q=load(HERE.parent/'text_packed_quad_lab/run_lab.py','quad')
 for key,path in FONTS.items():adapter.guard(path,key)
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(name+' failed')
  return log
 # Fixed source name table proof recorded locally, no extra runtime parser dependency.
 import freetype
 f=freetype.Face(str(FONTS['cjk']),index=2)
 if f.family_name!=b'Noto Sans CJK SC':raise ValueError('TTC index2 is not SC')
 source_text='\n'.join(r[0] for r in RUNS)
 (out/'source-text.txt').write_text(source_text)
 golden=json.loads((HERE/'expected-shaping.json').read_text())['runs']
 glyphs=[];receipts=[];source_offset=0
 for text,direction,language,destination in RUNS:
  key,r,attempts=fallback(adapter,text,direction,language)
  if {k:r[k] for k in golden[text]}!=golden[text]:raise ValueError('frozen shaping regression mismatch')
  g=raster(adapter,key,r);g.update(destination=list(destination),text=text);glyphs.append(g)
  receipts.append({'text':text,'source_utf8_range':[source_offset,source_offset+len(text.encode('utf-8'))],'selected_face':key,'attempts':attempts,'shape':r,'global_clusters':[source_offset+g['cluster_utf8_byte'] for g in r['glyphs']]});source_offset+=len(text.encode('utf-8'))+1
 for receipt in receipts:
  start,end=receipt['source_utf8_range']
  if source_text.encode('utf-8')[start:end].decode('utf-8')!=receipt['text']:raise ValueError('source run byte mapping')
  if any(not start<=c<end for c in receipt['global_clusters']):raise ValueError('source cluster bounds')
 if [r['selected_face'] for r in receipts]!=['serif','serif','sans','cjk']:raise ValueError('fallback routing changed')
 if [g['id'] for g in receipts[0]['shape']['glyphs']]!=[3314,76] or [g['cluster_utf8_byte'] for g in receipts[0]['shape']['glyphs']]!=[0,2]:raise ValueError('ffi shaping changed')
 if [g['id'] for g in receipts[1]['shape']['glyphs']]!=[163]:raise ValueError('combining composition changed')
 if [(g['id'],g['cluster_utf8_byte']) for g in receipts[2]['shape']['glyphs']]!=[(1390,6),(5366,2),(5293,0)]:raise ValueError('Arabic joining/RTL cluster changed')
 canonical=adapter.shape(FONTS['serif'],'á',key='serif')
 if canonical['glyphs']!=receipts[1]['shape']['glyphs']:raise ValueError('canonical combining mismatch')
 for text in ['\U0010ffff']:
  try:fallback(adapter,text,'ltr','en')
  except ValueError as e:
   if str(e)!='no fallback face covers complete run':raise
  else:raise ValueError('missing run accepted')
 sys.path.insert(0,str(ROOT/'tests'))
 try:from text_atlas_packing import ShelfAtlas
 finally:sys.path.pop(0)
 atlas=ShelfAtlas(W,H,padding=1,max_pages=1);locs=atlas.publish(atlas.prepare([(g['size'][0],g['size'][1],g['pixels']) for g in glyphs]));page=atlas.snapshot()[0]
 def vertices(route):
  vs=[]
  for g,loc in zip(glyphs,route):
   w,h=g['size'];dx,dy=g['destination']
   for x,y in [(0,0),(w,0),(0,h),(0,h),(w,0),(w,h)]:vs.extend([2*(dx+x)/W-1,2*(dy+y)/H-1,(loc.x+x)/W,(loc.y+y)/H])
  return vs
 q.raw(out/'atlas.f32',page);q.raw(out/'vertices.f32',vertices(locs));(out/'reference.json').write_text(json.dumps({'glyphs':glyphs}));(out/'receipts.json').write_text(json.dumps(receipts,indent=2))
 run('prepare',[sys.executable,HERE.parent/'text_packed_quad_lab/run_lab.py','--out',out/'prepared','--font',FONTS['sans']]);build=out/'prepared/build'
 for name,vs in [('normal',vertices(locs)),('wrong-route',vertices([locs[0],locs[1],locs[0],locs[3]]))]:
  q.raw(out/(name+'.vertices'),vs);log=run(name,[build/'quad_lab',build/'shaders',out/'atlas.f32',out/(name+'.vertices'),out/name])
  if 'validation_enabled=1' not in log:raise ValueError('validation required')
  aux(out/name)
  if name=='normal':result=q.verify(out,out/name)
  else:
   try:q.verify(out,out/name)
   except ValueError as e:
    if str(e)!='quad UV composition mismatch':raise
   else:raise ValueError('wrong face run route accepted')
 # Explicit extra identity case, not an invented natural fallback collision.
 collision=out/'same-id';collision.mkdir();og={}
 for key in ('serif','sans'):
  r=adapter.shape(FONTS[key],'O',key=key)
  if [g['id'] for g in r['glyphs']]!=[50]:raise ValueError('fixed same-ID fixture changed')
  og[key]=raster(adapter,key,r);og[key]['destination']=[20,15]
 if og['serif']['font_sha256']==og['sans']['font_sha256'] or og['serif']['pixels']==og['sans']['pixels']:raise ValueError('same-ID negative not meaningful')
 (collision/'reference.json').write_text(json.dumps({'glyphs':[og['sans']]}))
 for key in ('sans','serif'):
  g=og[key];w,h=g['size'];one=ShelfAtlas(W,H,padding=1,max_pages=1);loc=one.publish(one.prepare([(w,h,g['pixels'])]))[0];vs=[]
  for x,y in [(0,0),(w,0),(0,h),(0,h),(w,0),(w,h)]:vs.extend([2*(20+x)/W-1,2*(15+y)/H-1,(loc.x+x)/W,(loc.y+y)/H])
  q.raw(collision/(key+'.atlas'),one.snapshot()[0]);q.raw(collision/(key+'.vertices'),vs)
  log=run('same-id-'+key,[build/'quad_lab',build/'shaders',collision/(key+'.atlas'),collision/(key+'.vertices'),collision/key])
  if 'validation_enabled=1' not in log:raise ValueError('same ID validation')
  aux(collision/key)
  if key=='sans':collision_numeric=q.verify(collision,collision/key)
  else:
   try:q.verify(collision,collision/key)
   except ValueError as e:
    if str(e)!='quad UV composition mismatch':raise
   else:raise ValueError('same glyph ID wrong face accepted')
 summary={'status':'PASS','validation_enabled':True,'numeric':result,'selected_face_count':3,'run_count':4,'cjk_face_index':2,'missing_final_rejected':True,'actual_wrong_route_rejected':True,'actual_same_id_wrong_face_rejected':True,'same_id_positive':collision_numeric,'canonical_combining_equivalent':True,'scope':'fixed whole-run fallback, explicit directions and positions; not paragraph bidi or independent typography quality'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-source-hashes.json').write_text(json.dumps({str(p):sha(p) for p in list(HERE.glob('*.py'))+[HERE/'expected-shaping.json']+[HERE.parent/'text_packed_quad_lab/run_lab.py',ROOT/'tests/text_atlas_packing.py']},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
