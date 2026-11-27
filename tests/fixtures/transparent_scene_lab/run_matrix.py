#!/usr/bin/env python3
"""Immutable raw evidence, independent negative results, no device-performance claims."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);commands=[]
    def run(name,command,expected=0):
        start=time.monotonic()
        with (out/(name+'.log')).open('x') as log:
            try: code=subprocess.run(list(map(str,command)),cwd=REPO,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
            except subprocess.TimeoutExpired: code='TIMEOUT'
        commands.append(dict(label=name,command=list(map(str,command)),returncode=code,expected=expected,wall_seconds=time.monotonic()-start))
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        return code==expected
    ok=True
    for name,cmd in [('git-head',['git','rev-parse','HEAD','HEAD^{tree}']),('compiler-version',[os.environ.get('CXX','g++'),'--version']),('glslang-version',[os.environ.get('GLSLANG','glslangValidator'),'--version']),('spirv-val-version',[os.environ.get('SPIRV_VAL','spirv-val'),'--version'])]:ok=run(name,cmd) and ok
    sources=[p for folder in [HERE,HERE.parent/'engine_scale_lab'] for p in folder.rglob('*') if p.is_file() and not {'__pycache__','build'}.intersection(p.parts)]
    (out/'source-manifest.json').write_text(json.dumps({str(p.relative_to(REPO)):digest(p) for p in sorted(sources)},indent=2)+'\n')
    (out/'environment.json').write_text(json.dumps({k:os.environ.get(k) for k in ['VULKAN_SDK_PREFIX','LD_LIBRARY_PATH','VK_DRIVER_FILES','VK_LAYER_PATH','GLSLANG','SPIRV_VAL','MESA_SHADER_CACHE_DIR']},indent=2)+'\n')
    generated=run('generate',['python3',HERE/'generate.py','--out',out/'assets'])
    built=run('build',[HERE/'build.sh',out/'build'])
    if built and generated:
        exe=out/'build/transparent_scene_lab';shaders=out/'build/shaders'
        for mode,args in [('auto',[]),('fallback',['--disable-wboit'])]:
            ok=run(mode,[exe,shaders,out/mode,'--asset',out/'assets/synthetic.bin',*args]) and ok
        ok=run('overflow',[exe,shaders,out/'overflow','--overflow'],1) and ok
        ok='OVERFLOW: reject frame before upload (capacity=128)' in (out/'overflow.log').read_text() and ok
        before={str(p.relative_to(out/'auto')):digest(p) for p in (out/'auto').rglob('*') if p.is_file()}
        ok=run('reject-existing-run',[exe,shaders,out/'auto'],1) and ok
        after={str(p.relative_to(out/'auto')):digest(p) for p in (out/'auto').rglob('*') if p.is_file()}
        ok=bool(before) and before==after and (out/'reject-existing-run.log').read_text().strip()=='Refuse existing output directory' and ok
        ok=run('reject-existing-build',[HERE/'build.sh',out/'build'],1) and ok
        ok=(out/'reject-existing-build.log').read_text().strip()=='Refuse existing output directory' and ok
        ok=run('verify-images',['python3',HERE/'verify_artifacts.py',out]) and ok
    else:ok=False
    (out/'summary.json').write_text(json.dumps({'fixture_status':'PASS' if ok else 'FAIL','mobile_visual':'UNVERIFIED','mobile_performance':'UNMEASURED','resolution':[65,49],'limits':['orthographic diagonal covariance only; no perspective or rotation projection','host readback/upload between raster and resolve/effects; not an optimized all-GPU pass chain','no bounded fragment-list OIT implementation; overflow is pre-upload instance-capacity rejection','synthetic finite volume and soft particle formulas; no weather simulation or temporal history','two views sequential, no swapchain/lifetime stress; no Android execution','coverage estimates are CPU geometric samples, not hardware invocations','no sustained performance, timing-stage distribution, memory peak or background LOD claim']},indent=2)+'\n')
    (out/'artifact-manifest.json').write_text(json.dumps({str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()},indent=2)+'\n')
    print(out/'summary.json');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
