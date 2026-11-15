#!/usr/bin/env python3
"""Trusted local font -> HarfBuzz -> FreeType bitmap -> actual Vulkan -> readback.

Neither font shaping nor bitmap coverage is independently certified by this lab.
The independent oracle validates composition, not platform typography quality.
"""
import argparse,hashlib,importlib.util,json,math,os,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WIDTH,HEIGHT=65,49

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def raster(font,text,direction,language,*,pixel_size=20,phase64=0):
    import freetype
    if type(pixel_size)!=int or not 1<=pixel_size<=28 or type(phase64)!=int or not 0<=phase64<64:raise ValueError('raster size/phase budget')
    provider=load(ROOT/'tests/platform_text_probe.py','provider')
    run=provider.shape(font,text,direction=direction,language=language)
    if run['missing_glyphs'] or not 0<len(run['glyphs'])<=16:raise ValueError('unsupported glyph run')
    face=freetype.Face(str(font));face.set_pixel_sizes(0,pixel_size)
    face.set_transform(freetype.Matrix(65536,0,0,65536),freetype.Vector(phase64,0))
    penx=4.;peny=32.;scale=pixel_size/run['upem'];mask=[0.]*(WIDTH*HEIGHT);placements=[];clipped=0
    for g in run['glyphs']:
        # True shaped glyph IDs, never codepoint substitution. Integer placement
        # deliberately defines this bitmap path; no fractional hinting claim.
        face.load_glyph(g['id'],freetype.FT_LOAD_RENDER|freetype.FT_LOAD_TARGET_NORMAL)
        slot=face.glyph;b=slot.bitmap
        if b.pixel_mode!=freetype.FT_PIXEL_MODE_GRAY or b.num_grays!=256 or b.pitch<0:raise ValueError('unsupported bitmap format')
        x=round(penx+g['x_offset']*scale)+slot.bitmap_left
        y=round(peny-g['y_offset']*scale)-slot.bitmap_top
        data=b.buffer
        for row in range(b.rows):
            for col in range(b.width):
                coverage=data[row*b.pitch+col]/255
                if not coverage:continue
                xx,yy=x+col,y+row
                if not (0<=xx<WIDTH and 0<=yy<HEIGHT):clipped+=1;continue
                i=yy*WIDTH+xx;mask[i]=coverage+mask[i]*(1-coverage)
        placements.append({'glyph_id':g['id'],'x':x,'y':y,'bitmap_width':b.width,'bitmap_rows':b.rows})
        penx+=g['x_advance']*scale;peny-=g['y_advance']*scale
    if clipped or not any(mask):raise ValueError('fixture clipped or blank')
    if text=='ffi' and len(run['glyphs'])>=3:raise ValueError('fixture requires real ligature')
    if direction=='rtl' and [g['cluster_utf8_byte'] for g in run['glyphs']]!=sorted((g['cluster_utf8_byte'] for g in run['glyphs']),reverse=True):raise ValueError('RTL cluster order')
    run.update(placements=placements,raster_provider='freetype-py',freetype_version=list(freetype.version()),freetype_library_sha256=sha(Path(freetype.raw._lib._name)),pixel_size=pixel_size,phase64=phase64,position_policy='round shaped positions to integer pixels; FT normal grayscale',clipped_samples=clipped)
    return mask,run

def verify(folder):
    def floats(p,n):
        b=p.read_bytes()
        if len(b)!=4*n:raise ValueError('bad readback size')
        a=struct.unpack('<'+'f'*n,b)
        if not all(math.isfinite(v) for v in a):raise ValueError('nonfinite readback')
        return a
    mask=floats(folder/'mask.f32',WIDTH*HEIGHT)
    if any(x<0 or x>1 for x in mask) or not any(mask):raise ValueError('invalid coverage')
    color=floats(folder/'gpu/color.rgba32f',WIDTH*HEIGHT*4);errors=[];roi=[]
    for i,cov in enumerate(mask):
        a=cov*.75
        for c in range(4):
            expected=(a if c==3 else (.9,.5,.2)[c]*a)+(.1,.2,.3,.5)[c]*(1-a)
            e=abs(color[4*i+c]-expected);errors.append(e)
            if cov:roi.append(e)
    if max(errors)>1e-6:raise ValueError('composition mismatch')
    for file,expected in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
        values=floats(folder/f'gpu/{file}.rgba32f',WIDTH*HEIGHT*4)
        if any(v!=expected[i%4] for i,v in enumerate(values)):raise ValueError('sentinel changed')
    preview=load(HERE.parent/'text_vector_lab/run_lab.py','preview')
    def encode(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
    preview.png(folder/'preview.png',WIDTH,HEIGHT,bytes(encode(color[4*i+c]) for i in range(WIDTH*HEIGHT) for c in range(3)))
    return {'max_linear_error':max(errors),'max_roi_error':max(roi),'roi_pixels':sum(c>0 for c in mask),'partial_pixels':sum(0<c<1 for c in mask),'tolerance':1e-6,'sentinels':'UNCHANGED'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--quality',action='store_true');a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    def run(name,args,expected=0):
        r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=120)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode!=expected or 'VALIDATION:' in r.stdout+r.stderr:raise RuntimeError(name+' failed')
        return r.stdout+r.stderr
    # No downloads. Only caller supplied, trusted font is parsed.
    if not a.font.is_file() or a.font.stat().st_size>16*1024*1024:raise ValueError('font budget')
    old=HERE.parent/'text_vector_lab';build=out/'build'
    run('base-build',[old/'build.sh',build])
    src=(old/'main.cpp').read_text();needle='int main(int argc,char** argv)'
    if src.count(needle)!=1:raise ValueError('unexpected reused source')
    src=src.replace(needle,'int text_vector_fixture_main(int argc,char** argv)').replace('../engine_scale_lab/main.cpp',str(HERE.parent/'engine_scale_lab/main.cpp'))
    (build/'text_lab_reused.hpp').write_text(src)
    command=[os.environ.get('CXX','g++'),'-std=c++17','-O2',f'-I{build}']
    if os.environ.get('VULKAN_SDK_PREFIX'):command += ['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
    run('compile',command+[HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'bitmap_lab'])
    rows=[]
    for name,text,direction,language in [('O','O','ltr','en'),('ffi','ffi','ltr','en'),('Arabic','سلام','rtl','ar')]:
        folder=out/name;folder.mkdir();mask,receipt=raster(a.font,text,direction,language)
        (folder/'mask.f32').write_bytes(struct.pack('<'+'f'*len(mask),*mask))
        (folder/'shaped-run.json').write_text(json.dumps(receipt,indent=2)+'\n')
        log=run('vulkan-'+name,[build/'bitmap_lab',build/'shaders',folder/'mask.f32',folder/'gpu'])
        row=verify(folder);row.update(case=name,glyph_count=len(receipt['glyphs']),validation_enabled='validation_enabled=1' in log);rows.append(row)
    existing=out/'O/gpu'
    before={p.name:sha(p) for p in existing.iterdir()}
    run('refuse-output',[build/'bitmap_lab',build/'shaders',out/'O/mask.f32',existing],1)
    if before!={p.name:sha(p) for p in existing.iterdir()}:raise ValueError('overwritten GPU evidence')
    vector_rows=load(HERE/'vector_cases.py','vector_cases').run_cases(build,out)
    for name,data in [('short',b'x'),('nan',struct.pack('<f',float('nan'))*(WIDTH*HEIGHT)),('range',struct.pack('<f',2.)*(WIDTH*HEIGHT))]:
        bad=out/(name+'.f32');bad.write_bytes(data)
        run('reject-'+name,[build/'bitmap_lab',build/'shaders',bad,out/('bad-'+name)],1)
        if (out/('bad-'+name)).exists():raise ValueError('bad mask created GPU output')
    quality=load(HERE/'quality_cases.py','quality_cases').run_cases(build,out,a.font) if a.quality else None
    summary={'quality':quality,'status':'PASS','scope':'Linux single-run shaping + FreeType grayscale bitmap + actual software Vulkan composition','cases':rows,'vector_cases':vector_rows,'unverified':['font raster quality reference','Android/Windows','MSDF/MTSDF','paragraph bidi/fallback','vector geometry','hardware/performance'],'source_hashes':{str(f.relative_to(ROOT)):sha(f) for f in [HERE/'main.cpp',HERE/'run_lab.py',HERE/'vector_cases.py',HERE/'quality_cases.py',ROOT/'tests/bounded_vector_mask.py',old/'main.cpp',old/'coverage.frag',ROOT/'tests/platform_text_probe.py']},'binary_sha256':sha(build/'bitmap_lab')}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));return 0
if __name__=='__main__':raise SystemExit(main())
