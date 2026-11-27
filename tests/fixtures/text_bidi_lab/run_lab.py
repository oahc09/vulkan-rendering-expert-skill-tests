#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,math,os,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
UNICODE_SHA='18507f7ec57ec8155b7771dbc88f3e3201ad08eba4dba70e4e095ef628020fa8'
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unicode_check(bidi,path):
 if sha(path)!=UNICODE_SHA:raise ValueError('fixed official Unicode source hash')
 prefix='0061 0062 0063 0020 0028 0064 0065 0066 0020 0627 0628 062C 0029 0020 05D0 05D1 05D2;';count=0
 for line in path.read_text().splitlines():
  if not line.startswith(prefix):continue
  cp,base,_,levels,visual=line.split(';');m=bidi.resolve(''.join(chr(int(x,16)) for x in cp.split()),int(base))
  if m['levels']!=list(map(int,levels.split())) or m['visual_to_logical']!=list(map(int,visual.split())):raise ValueError('official bidi vector mismatch')
  count+=1
 if count!=2:raise ValueError('official vector count')
 return count
def raster_run(fallback,adapter,item,force_ltr=False):
 import freetype
 direction='ltr' if force_ltr and item['direction']=='rtl' else item['direction']
 key,r,attempts=fallback.fallback(adapter,item['text'],direction,item['language'])
 digest,_,index=adapter.FACES[key]
 if r['font_sha256']!=digest or r['face_index']!=index:raise ValueError('face receipt mismatch')
 face=freetype.Face(str(fallback.FONTS[key]),index=adapter.guard(fallback.FONTS[key],key));face.set_pixel_sizes(0,10)
 pixels={};pen=0.;scale=10/r['upem'];placements=[]
 for g in r['glyphs']:
  face.load_glyph(g['id'],freetype.FT_LOAD_RENDER|freetype.FT_LOAD_TARGET_NORMAL);slot=face.glyph;b=slot.bitmap
  if b.pixel_mode!=freetype.FT_PIXEL_MODE_GRAY or b.num_grays!=256 or b.pitch<0:raise ValueError('gray bitmap only')
  x=round(pen+g['x_offset']*scale)+slot.bitmap_left;y=round(-g['y_offset']*scale)-slot.bitmap_top
  for yy in range(b.rows):
   for xx in range(b.width):
    c=b.buffer[yy*b.pitch+xx]/255
    if c:pixels[x+xx,y+yy]=c+pixels.get((x+xx,y+yy),0)*(1-c)
  placements.append({'glyph':g['id'],'x':x,'y':y});pen+=g['x_advance']*scale
 if not pixels or not 0<pen<60:raise ValueError('fixed run blank/advance budget')
 x0=min(x for x,y in pixels);y0=min(y for x,y in pixels);w=max(x for x,y in pixels)-x0+1;h=max(y for x,y in pixels)-y0+1
 byte_start=len('A سلام 12!'[:item['start']].encode('utf-8'))
 r['global_clusters_utf8']=[byte_start+g['cluster_utf8_byte'] for g in r['glyphs']]
 return {'size':[w,h],'pixels':[pixels.get((x+x0,y+y0),0) for y in range(h) for x in range(w)],'crop_offset':[x0,y0],'advance':pen,'source':item,'face':key,'shape':r,'placements':placements,'attempts':attempts}
def layout(glyphs,baseline):
 pen=3.;output=[]
 for g in glyphs:
  g=dict(g);g['destination']=[round(pen)+g['crop_offset'][0],baseline+g['crop_offset'][1]];output.append(g);pen+=g['advance']
 if pen>62:raise ValueError('preregistered line width exceeded')
 for g in output:
  x,y=g['destination'];w,h=g['size']
  if x<0 or y<0 or x+w>65 or y+h>49:raise ValueError('no clipping permitted')
 return output,pen-3

def reference_from_icu(glyphs,independent,baseline):
 # Derive logical intervals anew from ICU levels, then walk ICU visual indices.
 levels=independent['levels'];spans=[];start=0
 for end in range(1,len(levels)+1):
  if end==len(levels) or levels[end]!=levels[start]:spans.append((start,end));start=end
 order=[]
 for logical in independent['visual_to_logical']:
  span=next((a,b) for a,b in spans if a<=logical<b)
  if span not in order:order.append(span)
 cursor=3.;refs=[]
 for start,end in order:
  candidates=[g for g in glyphs if (g['source']['start'],g['source']['end'])==(start,end)]
  if len(candidates)!=1:raise ValueError('ICU run/source mismatch')
  original=candidates[0];g=dict(original)
  g['destination']=[round(cursor)+g['crop_offset'][0],baseline+g['crop_offset'][1]]
  refs.append(g);cursor+=sum(v['x_advance'] for v in g['shape']['glyphs'])*10/g['shape']['upem']
 return refs

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--unicode-data',type=Path,default=Path('/usr/share/unicode/BidiCharacterTest.txt'));a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 bidi=load(HERE/'bidi.py','bidi');fb=load(HERE.parent/'text_fallback_lab/run_lab.py','fallback');adapter=load(HERE.parent/'text_fallback_lab/adapter.py','adapter');q=load(HERE.parent/'text_packed_quad_lab/run_lab.py','quad')
 count=unicode_check(bidi,a.unicode_data)
 for key,path in fb.FONTS.items():adapter.guard(path,key)
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(name+' failed')
  return log
 # All layout conditions and independent maps fixed before building/running GPU.
 cases=[]
 for base,baseline in [(0,16),(1,36)]:
  items,mapping=bidi.runs(bidi.TEXT,base);glyphs=[raster_run(fb,adapter,item) for item in items];positive,width=layout(glyphs,baseline)
  wrong_order,_=layout(sorted(glyphs,key=lambda g:g['source']['start']),baseline)
  wrong_direction,_=layout([raster_run(fb,adapter,item,True) for item in items],baseline)
  reference=reference_from_icu(glyphs,bidi.icu(bidi.TEXT,base),baseline)
  cases.append((base,mapping,positive,wrong_order,wrong_direction,width,reference))
 run('prepare',[sys.executable,HERE.parent/'text_packed_quad_lab/run_lab.py','--out',out/'prepared','--font',fb.FONTS['sans']]);build=out/'prepared/build'
 sys.path.insert(0,str(ROOT/'tests'))
 try:from text_atlas_packing import ShelfAtlas
 finally:sys.path.pop(0)
 rows=[];receipts=[]
 for base,mapping,positive,wrong_order,wrong_direction,width,reference in cases:
  folder=out/('base'+str(base));folder.mkdir();(folder/'reference.json').write_text(json.dumps({'glyphs':reference}));receipts.append({'base':base,'mapping':mapping,'runs':positive,'text':bidi.TEXT})
  row={'base':base,'line_advance':width,'run_count':len(positive),'negative_checks':[]}
  for mode,glyphs in [('normal',positive),('logical-order',wrong_order),('rtl-as-ltr',wrong_direction)]:
   atlas=ShelfAtlas(W,H,padding=1,max_pages=1);places=atlas.publish(atlas.prepare([(g['size'][0],g['size'][1],g['pixels']) for g in glyphs]));vs=[]
   for g,loc in zip(glyphs,places):
    w,h=g['size'];dx,dy=g['destination']
    for x,y in [(0,0),(w,0),(0,h),(0,h),(w,0),(w,h)]:vs.extend([2*(dx+x)/W-1,2*(dy+y)/H-1,(loc.x+x)/W,(loc.y+y)/H])
   q.raw(folder/(mode+'.atlas'),atlas.snapshot()[0]);q.raw(folder/(mode+'.vertices'),vs)
   log=run(str(base)+'-'+mode,[build/'quad_lab',build/'shaders',folder/(mode+'.atlas'),folder/(mode+'.vertices'),folder/mode])
   if 'validation_enabled=1' not in log:raise ValueError('validation required')
   fb.aux(folder/mode)
   if mode=='normal':row['numeric']=q.verify(folder,folder/mode)
   else:
    try:q.verify(folder,folder/mode)
    except ValueError as e:
     if str(e)!='quad UV composition mismatch':raise
    else:raise ValueError('actual bidi negative accepted')
    row['negative_checks'].append(mode)
  rows.append(row)
 (out/'layout-receipts.json').write_text(json.dumps(receipts,indent=2))
 libs=[Path('/usr/lib/x86_64-linux-gnu/libfribidi.so.0.4.0'),Path('/usr/lib/x86_64-linux-gnu/libicuuc.so.76')]
 (out/'local-provenance.json').write_text(json.dumps({'library_hashes':{str(p):sha(p) for p in libs},'source_hashes':{str(p):sha(p) for p in list(HERE.glob('*.py'))+[HERE.parent/'text_fallback_lab/adapter.py',HERE.parent/'text_packed_quad_lab/run_lab.py']},'official_unicode_hash':sha(a.unicode_data)},indent=2))
 summary={'status':'PASS','validation_enabled':True,'cases':rows,'official_unicode_vectors':count,'independent_icu_map_cases':2,'scope':'fixed single BMP paragraph, two base directions; library bidi plus bounded level/script runs and whole-run fallback; no general layout certification'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
