#!/usr/bin/env python3
import argparse,ctypes as C,hashlib,importlib.util,json,math,os,struct,subprocess,sys,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
PALETTES=[[(1,0,0,128/255),(0,0,1,192/255)],[(0,1,0,192/255),(1,1,0,128/255)],[(51/255,102/255,153/255,128/255),(204/255,51/255,102/255,192/255)]]
def raw(p,v):p.write_bytes(struct.pack('<'+'f'*len(v),*v))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out,palette,folder=None):
 folder=folder or out/('gpu'+str(palette));data=(folder/'color.rgba32f').read_bytes()
 if len(data)!=65*49*16:raise ValueError('readback size')
 actual=struct.unpack('<12740f',data);errors=[]
 for y in range(H):
  for x in range(W):
   expected=[.1,.2,.3,.5]
   for (x0,y0,x1,y1),color in zip([(5,18,17,30),(11,12,23,24)],PALETTES[palette]):
    a=color[3] if x0<=x<x1 and y0<=y<y1 else 0
    # Independent reference from fixed raw CPAL constants, never shader inputs.
    linear=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in color[:3]]
    expected=[(a if k==3 else linear[k]*a)+expected[k]*(1-a) for k in range(4)]
   errors.extend(abs(actual[(y*W+x)*4+k]-expected[k]) for k in range(4))
 if not all(math.isfinite(v) for v in actual) or max(errors)>1e-6:raise ValueError('color layer composition mismatch')
 for name,c in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  v=struct.unpack('<12740f',(folder/(name+'.rgba32f')).read_bytes())
  if any(x!=c[i%4] for i,x in enumerate(v)):raise ValueError('sentinel mismatch')
 spec=importlib.util.spec_from_file_location('preview',HERE.parent/'text_vector_lab/run_lab.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 def enc(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
 m.png(folder/'preview.png',W,H,bytes(enc(actual[4*i+k]) for i in range(W*H) for k in range(3)))
 return {'max_linear_error':max(errors),'tolerance':1e-6,'palette':palette,'sentinels':'UNCHANGED'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 def run(name,args,expected=0):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode!=expected or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 run('generate',[os.environ.get('TEXT18_FONTTOOLS_PYTHON','python'),HERE/'generate_font.py',out/'synthetic.ttf'])
 import freetype
 face=freetype.Face(str(out/'synthetic.ttf'));face.set_pixel_sizes(0,20);h=freetype.raw._lib
 class Color(C.Structure):_fields_=[('blue',C.c_ubyte),('green',C.c_ubyte),('red',C.c_ubyte),('alpha',C.c_ubyte)]
 class Iter(C.Structure):_fields_=[('num_layers',C.c_uint),('layer',C.c_uint),('p',C.c_void_p)]
 layer=h.FT_Get_Color_Glyph_Layer;layer.argtypes=[type(face._FT_Face),C.c_uint,C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(Iter)];layer.restype=C.c_ubyte
 select=h.FT_Palette_Select;select.argtypes=[type(face._FT_Face),C.c_ushort,C.POINTER(C.POINTER(Color))];select.restype=C.c_int
 class PaletteData(C.Structure):_fields_=[('num_palettes',C.c_ushort),('palette_name_ids',C.POINTER(C.c_ushort)),('palette_flags',C.POINTER(C.c_ushort)),('num_palette_entries',C.c_ushort),('palette_entry_name_ids',C.POINTER(C.c_ushort))]
 pd=PaletteData();getdata=h.FT_Palette_Data_Get;getdata.argtypes=[type(face._FT_Face),C.POINTER(PaletteData)];getdata.restype=C.c_int
 if getdata(face._FT_Face,C.byref(pd)) or pd.num_palettes!=len(PALETTES) or pd.num_palette_entries!=2:raise ValueError('palette bounds')
 masks=[];indices=[];it=Iter();gid=C.c_uint();ci=C.c_uint()
 while layer(face._FT_Face,face.get_char_index('A'),C.byref(gid),C.byref(ci),C.byref(it)):
  if len(masks)>=2 or ci.value>=2:raise ValueError('layer budget/index')
  face.load_glyph(gid.value,freetype.FT_LOAD_RENDER);b=face.glyph.bitmap
  if b.pixel_mode!=freetype.FT_PIXEL_MODE_GRAY or b.pitch<0 or b.num_grays!=256:raise ValueError('bitmap format')
  mask=[0.]*(W*H)
  for y in range(b.rows):
   for x in range(b.width):
    xx=5+face.glyph.bitmap_left+x;yy=30-face.glyph.bitmap_top+y
    if not(0<=xx<W and 0<=yy<H):raise ValueError('clip')
    mask[yy*W+xx]=b.buffer[y*b.pitch+x]/255
  masks.append(mask);indices.append((gid.value,ci.value))
 if indices!=[(2,0),(3,1)]:raise ValueError('layer order')
 raw(out/'masks.f32',[v for i in range(W*H) for v in (masks[0][i],masks[1][i],0.,0.)])
 base=HERE.parent/'text_vector_lab';build=out/'build';run('build',[base/'build.sh',build]);source=(base/'main.cpp').read_text()
 replacements=[('int main(int argc,char** argv)','int old_main(int argc,char** argv)'),('../engine_scale_lab/main.cpp',str(HERE.parent/'engine_scale_lab/main.cpp')),('range.size=16','range.size=32'),('0,16};','0,32};'),('VK_FORMAT_R32_SFLOAT','VK_FORMAT_R32G32B32A32_SFLOAT'),('buffer(width*height*4,VK_BUFFER_USAGE_TRANSFER_SRC_BIT)','buffer(width*height*16,VK_BUFFER_USAGE_TRANSFER_SRC_BIT)'),('const std::array<float,4>& ink','const std::array<float,8>& ink'),('mask.size()!=width*height','mask.size()!=width*height*4'),('float rgba[]={ink[0],ink[1],ink[2],ink[3]};','float rgba[]={ink[0],ink[1],ink[2],ink[3],ink[4],ink[5],ink[6],ink[7]};'),('0,16,rgba','0,32,rgba')]
 # Reuse class only; discard old synthetic entry point and its four-float callers.
 source=source[:source.index('int main(int argc,char** argv)')]
 for old,new in replacements[1:]:
  if old=='range.size=16':continue
  expected_count=2 if old=='VK_FORMAT_R32_SFLOAT' else 1
  if source.count(old)!=expected_count:raise ValueError('helper drift '+old)
  source=source.replace(old,new)
 (build/'color_helper.hpp').write_text(source)
 run('shader',[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',HERE/'color.frag','-o',build/'shaders/coverage.frag.spv']);run('spirv',[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',build/'shaders/coverage.frag.spv'])
 cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'color_lab'];run('compile',cmd)
 rows=[];receipts=[]
 for palette in range(pd.num_palettes):
  colors=C.POINTER(Color)()
  if select(face._FT_Face,palette,C.byref(colors)):raise ValueError('palette select')
  rgba=[v for _,idx in indices for v in (colors[idx].red/255,colors[idx].green/255,colors[idx].blue/255,colors[idx].alpha/255)]
  if rgba!=[v for color in PALETTES[palette] for v in color]:raise ValueError('palette decoding')
  # Decode actual provider CPAL RGB from sRGB; alpha is linear coverage opacity.
  linear_rgba=[(v if i%4==3 else (v/12.92 if v<=0.04045 else pow((v+0.055)/1.055,2.4))) for i,v in enumerate(rgba)]
  raw(out/'colors.f32',linear_rgba);log=run('draw'+str(palette),[build/'color_lab',build/'shaders',out/'masks.f32',out/'colors.f32',out/('gpu'+str(palette))])
  if 'validation_enabled=1' not in log:raise ValueError('validation required')
  rows.append(verify(out,palette));receipts.append(rgba)
 wrong=receipts[0][4:]+receipts[0][:4];raw(out/'wrong.f32',wrong);run('wrong-palette',[build/'color_lab',build/'shaders',out/'masks.f32',out/'wrong.f32',out/'wrong'])
 try:verify(out,0,out/'wrong')
 except ValueError as e:
  if 'composition mismatch' not in str(e):raise
 else:raise ValueError('wrong colors accepted')
 raw(out/'undecoded.f32',receipts[2]);run('skip-srgb-decode',[build/'color_lab',build/'shaders',out/'masks.f32',out/'undecoded.f32',out/'undecoded'])
 try:verify(out,2,out/'undecoded')
 except ValueError as e:
  if 'composition mismatch' not in str(e):raise
 else:raise ValueError('missing sRGB decode accepted')
 raw(out/'invalid-size.f32',[0.]);raw(out/'invalid-range.f32',[2.]*8)
 run('reject-size',[build/'color_lab',build/'shaders',out/'invalid-size.f32',out/'colors.f32',out/'bad-size'],1)
 run('reject-range',[build/'color_lab',build/'shaders',out/'masks.f32',out/'invalid-range.f32',out/'bad-range'],1)
 if (out/'bad-size').exists() or (out/'bad-range').exists():raise ValueError('invalid input reached GPU')
 summary={'status':'PASS','validation_enabled':True,'cases':rows,'scope':'synthetic COLRv0 two-layer FT palette/coverage provider to actual Vulkan composition; not production color-font certification','negative_checks':['actual swapped layer colors rejected','actual missing sRGB decode rejected','invalid size/range rejected before GPU'],'palette_count':pd.num_palettes,'text_opacity':'not separately tested; CPAL alpha only'};(out/'summary.json').write_text(json.dumps(summary,indent=2))
 tools={}
 for key,default in [('CXX','g++'),('GLSLANG','glslangValidator'),('SPIRV_VAL','spirv-val'),('TEXT18_FONTTOOLS_PYTHON','python')]:
  path=Path(shutil.which(os.environ.get(key,default)));tools[key]={'sha256':sha(path),'version':run('version-'+key,[path,'--version'])}
 driver={}
 for path in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep):
  if path:
   p=Path(path);driver[path]=sha(p);lib=Path(json.loads(p.read_text())['ICD']['library_path'])
   if lib.is_absolute():driver[str(lib)]=sha(lib)
 (out/'tools-driver.json').write_text(json.dumps({'tools':tools,'drivers':driver,'fonttools_version':run('fonttools-version',[os.environ.get('TEXT18_FONTTOOLS_PYTHON','python'),'-c','import fontTools;print(fontTools.__version__)'])},indent=2))
 (out/'local-provenance.json').write_text(json.dumps({'synthetic_font_sha256':sha(out/'synthetic.ttf'),'freetype_version':freetype.version(),'ft_library_sha256':sha(Path(freetype.raw._lib._name)),'layers':indices,'palettes':receipts,'sources':{str(p):sha(p) for p in [HERE/'run_lab.py',HERE/'main.cpp',HERE/'color.frag',HERE/'generate_font.py',base/'main.cpp',HERE.parent/'engine_scale_lab/main.cpp']},'binary_sha256':sha(build/'color_lab')},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
