from pathlib import Path
import argparse,hashlib,importlib.util,json,math,sys
from time import perf_counter_ns
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from cache import Cache

def load(p):
 s=importlib.util.spec_from_file_location('trusted_adapter',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def digest(result):
 r,gs=result
 return hashlib.sha256(json.dumps(r,sort_keys=True).encode()+b''.join(json.dumps({k:v for k,v in g.items() if k!='pixels'},sort_keys=True).encode()+g['pixels'] for g in gs)).hexdigest()

class Provider:
 def __init__(self,path):
  import freetype
  self.ft=freetype;self.path=path;self.a=load(HERE.parent/'text_fallback_lab/adapter.py');self.a.guard(path,'sans')
  self.identity=(self.a.FACES['sans'][0],0,self.a.api().hb_version_string().decode(),tuple(freetype.version()))
  self.calls={'hb':0,'ft':0}
 def shape(self,text,language,generation):
  self.calls['hb']+=1
  return self.a.shape(self.path,text,key='sans',language=language,face_generation=generation)
 def raster(self,gid,px):
  self.calls['ft']+=1
  face=self.ft.Face(self.path);face.set_pixel_sizes(0,px);face.load_glyph(gid,self.ft.FT_LOAD_RENDER|self.ft.FT_LOAD_TARGET_NORMAL)
  b=face.glyph.bitmap
  if b.pixel_mode!=self.ft.FT_PIXEL_MODE_GRAY or b.pitch<0:raise ValueError('gray positive pitch required')
  raw=bytes(b.buffer);pixels=b''.join(raw[y*b.pitch:y*b.pitch+b.width] for y in range(b.rows))
  return {'pixels':pixels,'width':b.width,'height':b.rows,'left':face.glyph.bitmap_left,'top':face.glyph.bitmap_top}

def stats(xs):
 a=sorted(xs)
 return {'count':len(a),**{f'p{p}_ns':a[max(0,math.ceil(len(a)*p/100)-1)] if a else None for p in (50,95,99)}}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--font',default='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 from unittest.mock import Mock
 p=Provider(a.font);p.shape=Mock(wraps=p.shape);p.raster=Mock(wraps=p.raster);c=Cache(p);rounds=[];cold_ns=[];hot_ns=[]
 for i in range(12):
  c.clear();spy0=(p.shape.call_count,p.raster.call_count);stage0={k:len(v) for k,v in c.times.items()};before=p.calls.copy();t=perf_counter_ns();cold=c.request('OFF');cold_ns.append(perf_counter_ns()-t);after=p.calls.copy();spy1=(p.shape.call_count,p.raster.call_count);stage1={k:len(v) for k,v in c.times.items()};t=perf_counter_ns();hot=c.request('OFF');hot_ns.append(perf_counter_ns()-t);end=p.calls.copy();spy2=(p.shape.call_count,p.raster.call_count)
  assert spy1[0]-spy0[0]==1 and spy1[1]-spy0[1]==2 and spy2==spy1
  assert len(c.times['shape'])==stage1['shape'] and len(c.times['raster'])==stage1['raster']
  assert digest(cold)==digest(hot) and end==after and after['hb']-before['hb']==1 and after['ft']-before['ft']==2
  # Independent direct production outside cache checks both HB receipt and bitmap bytes.
  oracle=p.shape('OFF','en',1);expected=(oracle,[p.raster(g['id'],20) for g in oracle['glyphs']]);assert digest(cold)==digest(expected)
  rounds.append({'cold_hb_calls':after['hb']-before['hb'],'cold_ft_calls':after['ft']-before['ft'],'hot_hb_calls':end['hb']-after['hb'],'hot_ft_calls':end['ft']-after['ft'],'entries':len(c.glyphs),'owned_bytes':c.bytes,'cold_shape_ns':c.times['shape'][stage0['shape']:stage1['shape']],'cold_raster_ns':c.times['raster'][stage0['raster']:stage1['raster']],'hot_shape_samples':0,'hot_raster_samples':0})
 before=p.calls.copy();sized=c.request('OFF',24);assert p.calls['hb']==before['hb'] and p.calls['ft']==before['ft']+2 and digest(sized)!=digest(hot)
 before=p.calls.copy();c.request('OFF',24,'fr');assert p.calls['hb']==before['hb']+1 and p.calls['ft']==before['ft']
 before=p.calls.copy();c.request('OFF',24,'fr',2);assert p.calls['hb']==before['hb']+1 and p.calls['ft']==before['ft']+2
 # Legal stale-cache simulation: old size pixels must not match direct new size production.
 ref=p.shape('OFF','en',1);fresh=(ref,[p.raster(g['id'],24) for g in ref['glyphs']]);assert digest(hot)!=digest(fresh)
 # Deliberately bypass the production cache key and poison actual 24px entries.
 bad=Cache(p);bad.request('OFF',24)
 for key in list(bad.glyphs):
  gid=key[2];old=next(value for g,value in zip(hot[0]['glyphs'],hot[1]) if g['id']==gid);bad.glyphs[key]=old
 assert digest(bad.request('OFF',24))!=digest(fresh) # independent fresh oracle rejects bad key routing

 tiny=Cache(p,byte_budget=1)
 try:tiny.request('O')
 except ValueError as e:assert str(e)=='coverage byte budget exceeded'
 else:raise AssertionError('budget not rejected')
 assert tiny.bytes==0 and not tiny.glyphs
 # Eviction requires real production again, not just count edits.
 ev=Cache(p,entries=1);ev.request('O');ev.request('F');before=p.calls.copy();ev.request('O');assert p.calls['hb']==before['hb']+1 and p.calls['ft']==before['ft']+1
 # Returned receipts/pixels are isolated from stored entries.
 snapshot=c.request('OFF');original=digest(snapshot);snapshot[0]['glyphs'][0]['id']=0;snapshot[1][0]['pixels']=b'bad'
 assert digest(c.request('OFF'))==original
 peak=c.peak;c.clear();assert c.bytes==0 and not c.layouts and not c.glyphs
 assert p.shape.call_count==p.calls['hb'] and p.raster.call_count==p.calls['ft']
 summary={'status':'PASS','rounds':rounds,'peak_owned_coverage_bytes':peak,'final_owned_coverage_bytes':c.bytes,'final_layout_entries':len(c.layouts),'final_glyph_entries':len(c.glyphs),'timings':{k:stats(v) for k,v in c.times.items()},'cold_request_timings':stats(cold_ns),'hot_request_timings':stats(hot_ns),'size_invalidation':True,'locale_layout_invalidation':True,'generation_invalidation':True,'stale_size_negative_rejected':True,'oversize_no_glyph_publish':True,'eviction_reproduces':True,'caller_mutation_isolated':True,'unmeasured':['JNI','GPU upload','draw','total frame','native heap','power/thermal'],'scope':'application cache cold/hot; CPU HB/FT only; no process/OS cold or GPU/native allocator measurement'}
 (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(a.out/'receipt.json').write_text(json.dumps({'identity':p.identity,'calls_including_direct_oracles':p.calls,'font':a.font},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
