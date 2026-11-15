#!/usr/bin/env python3
"""Bounded hard nested clips, executed in fragment shader, not CPU premasking."""
import argparse,hashlib,importlib.util,json,os,struct,subprocess,shutil,platform
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def inside_polygon(x,y):
    points=[(18,8),(48,18),(40,42),(10,32)];inside=False
    for (ax,ay),(bx,by) in zip(points,points[1:]+points[:1]):
        if (x-ax)*(by-ay)==(y-ay)*(bx-ax) and min(ax,bx)<=x<=max(ax,bx) and min(ay,by)<=y<=max(ay,by):return True
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:inside=not inside
    return inside

def predicate(x,y):
    return 12<=x<43 and 10<=y<37 and (x-30)**2+(y-25)**2<=225 and inside_polygon(x,y)

def verify(folder):
    # Bitmap oracle receives independent clipped reference only. The GPU used
    # the full unmodified source mask, and clip decisions occur in its shader.
    return load(HERE.parent/'text_bitmap_lab/run_lab.py','clip_bitmap').verify(folder)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    def run(name,args):
        r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
        if r.returncode or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
        return log
    vector=HERE.parent/'text_vector_lab';bitmap=HERE.parent/'text_bitmap_lab';build=out/'build'
    run('base-build',[vector/'build.sh',build])
    src=(vector/'main.cpp').read_text()
    for old,new in [('int main(int argc,char** argv)','int original_text_main(int argc,char** argv)'),('../engine_scale_lab/main.cpp',str(HERE.parent/'engine_scale_lab/main.cpp'))]:
        if src.count(old)!=1:raise ValueError('source hook changed')
        src=src.replace(old,new)
    (build/'text_lab_reused.hpp').write_text(src)
    cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build)]
    if os.environ.get('VULKAN_SDK_PREFIX'):cmd+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
    run('compile',cmd+[bitmap/'main.cpp','-l:libvulkan.so.1','-o',build/'clip_lab'])
    source=struct.pack('<3185f',*[((x*3+y)%7)/6 for y in range(H) for x in range(W)]);(out/'source.f32').write_bytes(source)
    values=struct.unpack('<3185f',source);expected=[v if predicate(i%W+.5,i//W+.5) else 0. for i,v in enumerate(values)]
    rows=[]
    for bypass in range(4):
        spv=build/'shaders/coverage.frag.spv';run('shader-'+str(bypass),[os.environ.get('GLSLANG','glslangValidator'),'-V','--target-env','vulkan1.2','-DBYPASS_CLIP='+str(bypass),HERE/'clip.frag','-o',spv]);run('validate-'+str(bypass),[os.environ.get('SPIRV_VAL','spirv-val'),'--target-env','vulkan1.2',spv])
        shutil.copyfile(spv,out/('clip-bypass-'+str(bypass)+'.spv'))
        folder=out/('correct' if not bypass else 'bypass-'+str(bypass));folder.mkdir();(folder/'mask.f32').write_bytes(struct.pack('<3185f',*expected))
        log=run('draw-'+str(bypass),[build/'clip_lab',build/'shaders',out/'source.f32',folder/'gpu'])
        if 'validation_enabled=1' not in log:raise ValueError('validation required')
        if not bypass:rows.append(verify(folder))
        else:
            try:verify(folder)
            except ValueError as e:
                if 'composition mismatch' not in str(e):raise
            else:raise ValueError('bypassed nested clip not detected')
    summary={'status':'PASS','validation_enabled':True,'clip_layers':3,'draws':4,'numeric':rows[0],'negative_checks':['bypass outer rectangle','bypass circle','bypass rotated rectangle'],'scope':'pixel-center hard rectangle/circle/rotated-rectangle intersection in fragment shader; independent CPU polygon ray-crossing reference','unverified':['arbitrary path clip','clip antialiasing','stencil','active MRT/depth','combined asynchronous glyph renderer','target device']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    files=[HERE/'run_lab.py',HERE/'clip.frag',bitmap/'main.cpp',bitmap/'run_lab.py',vector/'main.cpp',vector/'build.sh',HERE.parent/'engine_scale_lab/main.cpp']
    provenance={'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'generated_sha256':hashlib.sha256((build/'text_lab_reused.hpp').read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256((build/'clip_lab').read_bytes()).hexdigest(),'tests_head':run('head',['git','rev-parse','HEAD','HEAD^{tree}']),'tests_status':run('status',['git','status','--porcelain'])}
    provenance['variant_spirv_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.glob('clip-bypass-*.spv')}
    provenance['tools']={}
    for key,default in [('CXX','g++'),('GLSLANG','glslangValidator'),('SPIRV_VAL','spirv-val')]:
        exe=shutil.which(os.environ.get(key,default))
        if not exe:raise ValueError('missing tool')
        provenance['tools'][key]={'sha256':hashlib.sha256(Path(exe).read_bytes()).hexdigest(),'version':run('version-'+key,[exe,'--version'])}
    provenance['platform']=platform.platform();provenance['driver_files']={}
    for filename in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep):
        if not filename:continue
        path=Path(filename);provenance['driver_files'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        library=Path(json.loads(path.read_text())['ICD']['library_path'])
        if library.is_absolute() and library.is_file():provenance['driver_files'][str(library)]=hashlib.sha256(library.read_bytes()).hexdigest()
    provenance['validation_manifests']={}
    for dirname in os.environ.get('VK_LAYER_PATH','').split(os.pathsep):
        if dirname:
            for path in Path(dirname).glob('*.json'):provenance['validation_manifests'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    if os.environ.get('VULKAN_SKILL_ROOT'):provenance['skill_revision']=run('skill-head',['git','-C',os.environ['VULKAN_SKILL_ROOT'],'rev-parse','HEAD','HEAD^{tree}'])
    (out/'local-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
