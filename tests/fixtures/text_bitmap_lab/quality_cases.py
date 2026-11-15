"""Predeclared trusted-font translation regression, not universal font quality.
FT_Set_Transform delta is 26.6 pixel, after hinting:
https://freetype.org/freetype2/docs/reference/ft2-sizing_and_scaling.html
https://freetype.org/freetype2/docs/tutorial/step1.html
"""
import importlib.util,json,struct,subprocess,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
# Registered before measuring this fixture; never adjusted to observed results.
PHASES=(0,16,32,48)
SIZES=(12,20)
AREA_RELATIVE_LIMIT=.05
CENTROID_ERROR_LIMIT=.15

def moments(mask):
    area=sum(mask)
    if not area or not all(math.isfinite(x) and 0<=x<=1 for x in mask):raise ValueError('coverage')
    return area,sum(((i%65)+.5)*v for i,v in enumerate(mask))/area

def verify_translation(masks):
    if len(masks)!=4 or any(len(m)!=65*49 for m in masks):raise ValueError('phase count/size')
    a0,x0=moments(masks[0]);rows=[]
    for p,m in zip(PHASES,masks):
        a,x=moments(m);area=abs(a-a0)/a0;delta=abs(x-x0-p/64)
        if area>AREA_RELATIVE_LIMIT:raise ValueError('area drift')
        if delta>CENTROID_ERROR_LIMIT:raise ValueError('translation centroid')
        rows.append({'phase64':p,'area_relative_drift':area,'centroid_error_pixels':delta})
    return rows

def run_cases(build,out,font):
    spec=importlib.util.spec_from_file_location('bitmap_quality',HERE/'run_lab.py');bitmap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bitmap)
    rows=[]
    for size in SIZES:
        masks=[];run_identity=None
        for phase in PHASES:
            folder=out/f'quality-{size}-{phase}';folder.mkdir(exist_ok=False)
            mask,receipt=bitmap.raster(font,'O','ltr','en',pixel_size=size,phase64=phase)
            identity=(receipt['font_sha256'],receipt['glyphs'])
            if run_identity is not None and identity!=run_identity:raise ValueError('glyph run changed within phase sequence')
            run_identity=identity
            (folder/'shaped-run.json').write_text(json.dumps(receipt,indent=2)+'\n')
            (folder/'mask.f32').write_bytes(struct.pack('<3185f',*mask));masks.append(mask)
            r=subprocess.run([str(build/'bitmap_lab'),str(build/'shaders'),str(folder/'mask.f32'),str(folder/'gpu')],capture_output=True,text=True,timeout=120)
            log=r.stdout+r.stderr;(folder/'vulkan.log').write_text(log)
            if r.returncode or 'VALIDATION:' in log or 'validation_enabled=1' not in log:raise RuntimeError('quality GPU')
            numeric=bitmap.verify(folder);numeric.update(pixel_size=size,phase64=phase,validation_enabled=True);rows.append(numeric)
        temporal=verify_translation(masks)
        for row,t in zip(rows[-4:],temporal):row.update(t)
        repeat,_=bitmap.raster(font,'O','ltr','en',pixel_size=size,phase64=0)
        if repeat!=masks[0]:raise ValueError('repeat raster changed')
    return {'scope':'trusted single O at 12/20px, four post-hinting x phases; CPU moments and actual GPU composition', 'area_relative_limit':AREA_RELATIVE_LIMIT,'centroid_error_limit_pixels':CENTROID_ERROR_LIMIT,'cases':rows,'unverified':['outline ground truth','other fonts/glyphs','MSDF','rotation/perspective','platform typography','display quality']}
