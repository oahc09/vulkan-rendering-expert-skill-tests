#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,math,os,struct,subprocess,sys,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def image_from_bgra(data,provider,decode=True):
 result=[0.]*12740
 # Registered whole 136x128 strike -> 34x32 nearest source pixel centers.
 for y in range(32):
  for x in range(34):
   k=((4*y+2)*136+4*x+2)*4;dest=((y+8)*65+x+15)*4
   result[dest:dest+4]=provider.linear_pixel(data[k:k+4],decode)
 return result
def independent_png_reference(raw):
 result=[0.]*12740
 for y in range(32):
  for x in range(34):
   k=((y*4+2)*136+x*4+2)*4;r,g,b,a=raw[k:k+4];alpha=a/255
   encoded=[((v*a+127)//255)/a if a else 0 for v in (r,g,b)]
   linear=[v/12.92 if v<=.04045 else math.exp(2.4*math.log((v+.055)/1.055)) for v in encoded]
   d=((y+8)*65+x+15)*4;result[d:d+4]=[v*alpha for v in linear]+[alpha]
 return result
def verify(gpu,reference,fb):
 fb.aux(gpu);raw=(gpu/'color.rgba32f').read_bytes()
 if len(raw)!=12740*4:raise ValueError('output size')
 actual=struct.unpack('<12740f',raw)
 if not all(math.isfinite(v) for v in actual):raise ValueError('nonfinite')
 errors=[];partial=[]
 for i in range(3185):
  alpha=reference[4*i+3]*.75
  for c in range(4):
   e=abs(actual[4*i+c]-(reference[4*i+c]*.75+(.1,.2,.3,.5)[c]*(1-alpha)));errors.append(e)
   if 0<reference[4*i+3]<1:partial.append(e)
 preview=load(HERE.parent/'text_vector_lab/run_lab.py','preview')
 def enc(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
 preview.png(gpu/'preview.png',W,H,bytes(enc(actual[4*i+c]) for i in range(3185) for c in range(3)))
 return {'max_composition_error':max(errors),'max_partial_error':max(partial,default=0),'partial_pixels':sum(0<reference[4*i+3]<1 for i in range(3185)),'roi_pixels':sum(reference[4*i+3]>0 for i in range(3185)),'tolerance':1e-6,'excluded_count':0}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 provider=load(HERE/'provider.py','provider');provider.guard();fb=load(HERE.parent/'text_fallback_lab/run_lab.py','fallback');bitmap=load(HERE.parent/'text_bitmap_lab/run_lab.py','bitmap');hb=load(ROOT/'tests/platform_text_probe.py','hb')
 fb.load(HERE.parent/'text_fallback_lab/adapter.py','font_guard').guard(fb.FONTS['sans'],'sans')
 seq=Path('/usr/share/unicode/emoji/emoji-variation-sequences.txt')
 if sha(seq)!='8a67d0429a5831d91e744bc5170d43dc66ddccd42c6f532cbe421dc406b571fd':raise ValueError('official VS source hash')
 for text,code,expected in [('❤\ufe0e','FE0E','text'),('❤\ufe0f','FE0F','emoji')]:
  line=next(l for l in seq.read_text().splitlines() if l.startswith('2764 '+code))
  if ('; '+expected+' style;') not in line or provider.policy(text)!=expected:raise ValueError('presentation policy')
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(name+' failed')
  return log
 run('png-reference',[os.environ.get('TEXT18_FONTTOOLS_PYTHON','python'),HERE/'png_reference.py',provider.FONT,out/'source.rgba']);png=(out/'source.rgba').read_bytes()
 def dispatch(request_cluster):
  route=provider.policy(request_cluster)
  font=provider.FONT if route=='emoji' else fb.FONTS['sans']
  shaped=hb.shape(font,request_cluster)
  if route=='emoji':
   if [g['id'] for g in shaped['glyphs']]!=[168] or shaped['missing_glyphs']:raise ValueError('emoji shaped identity')
   bytes_bgra=provider.decode(shaped['glyphs'][0]['id'])
   return {'route':route,'shape':shaped,'bytes':bytes_bgra,'pixels':image_from_bgra(bytes_bgra,provider)}
  if [g['id'] for g in shaped['glyphs']]!=[4076,3] or shaped['glyphs'][1]['x_advance']!=0:raise ValueError('text/default ignorable identity')
  mask,receipt=bitmap.raster(font,request_cluster,'ltr','en')
  if receipt['glyphs']!=shaped['glyphs'] or receipt['font_sha256']!=shaped['font_sha256']:raise ValueError('repeated text shape mismatch')
  return {'route':route,'shape':shaped,'raster':receipt,'pixels':[v for c in mask for v in (.9*c,.9*c,.9*c,c)]}
 requests={name:dispatch(cluster) for name,cluster in [('vs16','❤\ufe0f'),('vs15','❤\ufe0e')]}
 emoji=requests['vs16']['pixels'];text=requests['vs15']['pixels'];bgra=requests['vs16']['bytes'];er=requests['vs16']['shape'];tr=requests['vs15']['shape'];treceipt=requests['vs15']['raster']
 (out/'provider.bgra').write_bytes(bgra)
 if len(png)!=len(bgra):raise ValueError('PNG size')
 # Fixed nearest-integer encoded premultiplication determined in prior local audit.
 diff=max(abs(bgra[i+c]-(png[i+2-c]*png[i+3]+127)//255) for i in range(0,len(png),4) for c in range(3))
 if diff!=0 or any(bgra[i]!=png[i] for i in range(3,len(png),4)):raise ValueError('independent PNG premultiplied bytes mismatch')
 oracle=independent_png_reference(png);undecoded=image_from_bgra(bgra,provider,False)
 base=HERE.parent/'text_vector_lab';build=out/'build';run('build',[base/'build.sh',build]);s=(base/'main.cpp').read_text();s=s[:s.index('int main(int argc,char** argv)')]
 for old,new,count in [('../engine_scale_lab/main.cpp',str(HERE.parent/'engine_scale_lab/main.cpp'),1),('VK_FORMAT_R32_SFLOAT','VK_FORMAT_R32G32B32A32_SFLOAT',2),('buffer(width*height*4,VK_BUFFER_USAGE_TRANSFER_SRC_BIT)','buffer(width*height*16,VK_BUFFER_USAGE_TRANSFER_SRC_BIT)',1),('mask.size()!=width*height','mask.size()!=width*height*4',1)]:
  if s.count(old)!=count:raise ValueError('helper drift')
  s=s.replace(old,new)
 (build/'emoji_helper.hpp').write_text(s)
 run('shader',[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',HERE/'emoji.frag','-o',build/'shaders/coverage.frag.spv']);run('spirv',[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',build/'shaders/coverage.frag.spv'])
 run('compile',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'emoji'])
 rows={}
 for name,pixels,reference in [('vs16',emoji,oracle),('vs15',text,text),('skip-decode',undecoded,oracle),('wrong-text-route',text,oracle)]:
  path=out/(name+'.f32');path.write_bytes(struct.pack('<12740f',*pixels));log=run(name,[build/'emoji',build/'shaders',path,out/name])
  if 'validation_enabled=1' not in log:raise ValueError('validation required')
  rows[name]=verify(out/name,reference,fb)
 if any(rows[n]['max_composition_error']>1e-6 for n in ['vs15','vs16']) or any(rows[n]['max_composition_error']<=1e-6 for n in ['skip-decode','wrong-text-route']):raise ValueError('color positive/negative category')
 (out/'shaping-receipts.json').write_text(json.dumps({'emoji':er,'text':tr,'text-raster':treceipt},indent=2))
 paths=[Path('/lib/x86_64-linux-gnu/libfreetype.so.6'),*HERE.glob('*.py'),HERE/'emoji.frag',HERE/'main.cpp',build/'emoji',build/'emoji_helper.hpp']
 paths += [Path(p) for p in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep) if p]
 (out/'local-provenance.json').write_text(json.dumps({'hashes':{str(p):sha(p) for p in paths},'tool_versions':{k:run(k+'-version',[os.environ.get(k,d),'--version']) for k,d in [('CXX','g++'),('GLSLANG','glslangValidator'),('SPIRV_VAL','spirv-val'),('TEXT18_FONTTOOLS_PYTHON','python')]}}))
 summary={'status':'PASS','validation_enabled':True,'cases':rows,'png_to_ft_premult_byte_error':diff,'source_size':[136,128],'display_size':[34,32],'text_opacity':.75,'official_selector_cases':2,'request_routes':{k:v['route'] for k,v in requests.items()},'scope':'fixed real heart VS15/text and VS16/color cluster policy; independently decoded CBDT PNG and actual system FT; not full emoji Unicode or bitmap scaling quality'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
