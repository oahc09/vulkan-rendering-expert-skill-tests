#!/usr/bin/env python3
"""Actual immutable descriptor-set sampled draws with host-timeline retirement gates."""
import argparse,hashlib,json,os,struct,subprocess,math,shutil,platform
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out):
    n=json.loads((out/'frames/numerics.json').read_text())
    if n!={'distinct_pages':2,'distinct_descriptor_sets':2,'pending_draws':2,'retired_draws':2,'validation_enabled':True}:raise ValueError('incomplete draw evidence')
    log=(out/'vulkan.log').read_text();rows=[json.loads(x) for x in log.splitlines() if x.startswith('{"descriptor"')]
    if rows!=[dict(descriptor=i,pending_fence_not_ready=True,retired_fence_success=True) for i in range(2)]:raise ValueError('retirement evidence mismatch')
    results=[]
    for gen in range(2):
        folder=out/'frames'/f'generation-{gen}'
        def floats(name,count):
            raw=(folder/name).read_bytes()
            if len(raw)!=count*4:raise ValueError('readback length')
            vals=struct.unpack('<'+'f'*count,raw)
            if not all(math.isfinite(x) for x in vals):raise ValueError('nonfinite')
            return vals
        mask=[((x+2*y)%5)/4 if gen else ((x+y)%3)/2 for y in range(49) for x in range(65)]
        if tuple(mask)!=floats('mask.f32',3185):raise ValueError('coverage mismatch')
        pixels=floats('color.rgba32f',3185*4);worst=0
        for i,cov in enumerate(mask):
            a=cov*.75
            for c in range(4):
                expected=(a if c==3 else (.9,.5,.2)[c]*a)+(.1,.2,.3,.5)[c]*(1-a)
                worst=max(worst,abs(pixels[i*4+c]-expected))
        if worst>1e-6:raise ValueError('wrong descriptor page composition')
        for name,expect in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
            if any(x!=expect[i%4] for i,x in enumerate(floats(name+'.rgba32f',3185*4))):raise ValueError('sentinel modified')
        results.append(dict(generation=gen,max_linear_error=worst,tolerance=1e-6))
    return results

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    def run(name,args,expected=0):
        r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
        if r.returncode!=expected or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
        return log
    base=HERE.parent/'text_vector_lab';build=out/'build';run('base-build',[base/'build.sh',build])
    engine=HERE.parent/'engine_scale_lab/main.cpp'
    helper=engine.read_text()
    needle='enabled12.drawIndirectCount = countEnabled;'
    if helper.count(needle)!=1:raise ValueError('helper feature setup changed')
    helper=helper.replace(needle,needle+'\n    if(!f12.timelineSemaphore)throw std::runtime_error("timeline unsupported");\n    enabled12.timelineSemaphore=VK_TRUE;')
    (build/'engine_timeline.hpp').write_text(helper)
    src=(base/'main.cpp').read_text();src=src.replace('int main(int argc,char** argv)','int unused_text_vector_main(int argc,char** argv)').replace('../engine_scale_lab/main.cpp',str(build/'engine_timeline.hpp'))
    src=src.replace('struct TextLab: Vulkan {','struct TextLab: Vulkan {\n'+(HERE/'gated_methods.inc').read_text()).replace('dp.maxSets=1;','dp.maxSets=2;').replace('VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1};','VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,2};').replace('begin();barrier(','gatedBegin();barrier(').replace('VK_ACCESS_HOST_READ_BIT);submit();','VK_ACCESS_HOST_READ_BIT);gatedSubmit();').replace('~TextLab(){','~TextLab(){if(drawGate)vkDestroySemaphore(device,drawGate,nullptr);')
    if src.count('gatedBegin();barrier(')!=1 or src.count('VK_ACCESS_HOST_READ_BIT);gatedSubmit();')!=1:raise ValueError('reused source changed')
    (build/'text_lab_reused.hpp').write_text(src)
    args=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build)]
    if os.environ.get('VULKAN_SDK_PREFIX'):args+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
    run('compile',args+[HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'descriptor_lab'])
    tools={}
    for key,default in [('CXX','g++'),('GLSLANG','glslangValidator'),('SPIRV_VAL','spirv-val')]:
        resolved=shutil.which(os.environ.get(key,default))
        if not resolved:raise ValueError('missing tool '+key)
        tools[key]={'sha256':sha(Path(resolved)),'version':run('version-'+key,[resolved,'--version'])}
    drivers={}
    for name in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep):
        if not name:continue
        path=Path(name);drivers[str(path)]=sha(path)
        lib=Path(json.loads(path.read_text())['ICD']['library_path'])
        if lib.is_absolute() and lib.is_file():drivers[str(lib)]=sha(lib)
    layers={}
    for name in os.environ.get('VK_LAYER_PATH','').split(os.pathsep):
        if name:
            for path in Path(name).glob('*.json'):layers[str(path)]=sha(path)
    receipt={'tools':tools,'driver_hashes':drivers,'validation_manifests':layers,'platform':platform.platform(),'tests_revision':run('tests-head',['git','rev-parse','HEAD','HEAD^{tree}']),'tests_status':run('tests-status',['git','status','--porcelain']),'binary_sha256':sha(build/'descriptor_lab'),'generated_helper_hashes':{p.name:sha(p) for p in [build/'engine_timeline.hpp',build/'text_lab_reused.hpp']}}
    if os.environ.get('VULKAN_SKILL_ROOT'):receipt['skill_revision']=run('skill-head',['git','-C',os.environ['VULKAN_SKILL_ROOT'],'rev-parse','HEAD','HEAD^{tree}'])
    (out/'local-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
    log=run('vulkan' ,[build/'descriptor_lab',build/'shaders',out/'frames']);results=verify(out)
    if 'DESCRIPTOR_RESOURCES_DESTROYED' not in log:raise ValueError('missing cleanup')
    abort=run('abort',[build/'descriptor_lab',build/'shaders',out/'aborted','--abort-pending'],1)
    if 'INTENTIONAL_PENDING_DRAW_CLEANED' not in abort:raise ValueError('wrong abort')
    before={str(p.relative_to(out/'frames')):sha(p) for p in (out/'frames').rglob('*') if p.is_file()}
    run('refuse-output',[build/'descriptor_lab',build/'shaders',out/'frames'],1)
    if before!={str(p.relative_to(out/'frames')):sha(p) for p in (out/'frames').rglob('*') if p.is_file()}:raise ValueError('output overwritten')
    summary={'status':'PASS','validation_enabled':True,'draws':results,'scope':'single-queue two immutable descriptor sets/pages; actual host-timeline-gated sampled fragment draws','limits':['controlled single-queue schedule','no UV packed-glyph extraction','no multidevice or mobile performance','no driver allocator leak claim']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    sources=[HERE/'main.cpp',HERE/'gated_methods.inc',HERE/'run_lab.py',base/'main.cpp',base/'coverage.frag',HERE.parent/'engine_scale_lab/main.cpp']
    (out/'source-hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in sources},indent=2)+'\n');print(json.dumps(summary));return 0
if __name__=='__main__':raise SystemExit(main())
