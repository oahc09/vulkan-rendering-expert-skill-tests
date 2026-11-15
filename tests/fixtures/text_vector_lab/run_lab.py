#!/usr/bin/env python3
"""Run actual Vulkan coverage upload/draw/readback and verify raw artifacts.

Uses existing Engine Scale Lab device/resource helpers, not CPU emulation.
No fonts, shaper or platform bridge: generated masks have synthetic provenance.
"""
import argparse,hashlib,json,math,os,struct,subprocess,time,zlib,shutil,platform
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def png(path,width,height,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    rows=b''.join(b'\0'+rgb[y*width*3:(y+1)*width*3] for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def verify(out):
    width,height=65,49
    rows=[json.loads(line) for line in (out/'frames/metrics.jsonl').read_text().splitlines()]
    if len(rows)!=5 or [r['frame'] for r in rows]!=list(range(5)):raise ValueError('incomplete frame set')
    findings=[]
    for frame in range(5):
        prefix=out/'frames'/f'frame-{frame}'
        def floats(ext,n):
            raw=Path(str(prefix)+ext).read_bytes()
            if len(raw)!=n*4:raise ValueError('truncated readback')
            values=struct.unpack('<'+'f'*n,raw)
            if not all(math.isfinite(x) for x in values):raise ValueError('nonfinite readback')
            return values
        mask=floats('.coverage32f',width*height)
        actual=floats('.rgba32f',width*height*4)
        velocity=floats('.velocity32f',width*height*4)
        ids=floats('.id32f',width*height*4)
        # Independent numerical reference, not the C++ reported verdict.
        max_error=max(abs(actual[i*4+c]-(1 if c==3 else .2+mask[i]*.8*.8)) for i in range(width*height) for c in range(4))
        if max_error>1e-6:raise ValueError('linear reference mismatch')
        for values,expected in [(velocity,(.125,-.25,.5,1)),(ids,(37,91,12,1))]:
            if any(value!=expected[i%4] for i,value in enumerate(values)):raise ValueError('non-target sentinel changed')
        if frame==0 and any(c!=.5 for c in mask):raise ValueError('constant reference missing')
        if frame:
            if mask[24*width+32]!=0 or mask[24*width+16]!=1:raise ValueError('synthetic hole/stroke lost')
            if actual[(24*width+32)*4]>.200001:raise ValueError('hole erroneously filled')
        # Preview explicitly sRGB encodes linear readback for ordinary viewers.
        def encode(v):
            v=max(0.,min(1.,v));return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
        rgb=bytes(encode(actual[i*4+c]) for i in range(width*height) for c in range(3))
        png(Path(str(prefix)+'.png'),width,height,rgb)
        findings.append({'frame':frame,'max_linear_error':max_error,'tolerance':1e-6,'hole_verified':frame>0,'sentinels':'UNCHANGED'})
    return findings

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args(argv)
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    commands=[]
    def run(name,command,expected=0):
        start=time.monotonic()
        try:
            with (out/(name+'.log')).open('x') as log:
                p=subprocess.run(list(map(str,command)),cwd=REPO,stdout=log,stderr=subprocess.STDOUT,timeout=180)
            code=p.returncode
        except (OSError,subprocess.TimeoutExpired) as exc:
            code=str(exc)
        commands.append({'name':name,'argv':list(map(str,command)),'returncode':code,'expected':expected,'wall_seconds':time.monotonic()-start})
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if code!=expected:raise RuntimeError(f'{name}: {code}')
    status='FAIL';error=None
    try:
        source_paths=[HERE/'main.cpp',HERE/'build.sh',HERE/'run_lab.py',HERE/'coverage.frag',HERE/'fullscreen.vert',HERE.parent/'engine_scale_lab/main.cpp',*sorted((HERE.parent/'engine_scale_lab/shaders').glob('*'))]
        (out/'source-manifest.json').write_text(json.dumps({str(p.relative_to(REPO)):sha(p) for p in source_paths if p.is_file()},indent=2)+'\n')
        (out/'environment.json').write_text(json.dumps({k:os.environ.get(k) for k in ['VULKAN_SDK_PREFIX','VK_DRIVER_FILES','VK_LAYER_PATH','LD_LIBRARY_PATH','GLSLANG','SPIRV_VAL']},indent=2)+'\n')
        binaries={}
        for label,default in [('GLSLANG','glslangValidator'),('SPIRV_VAL','spirv-val'),('CXX','g++')]:
            resolved=shutil.which(os.environ.get(label,default))
            if resolved:binaries[label]={'path':str(Path(resolved).resolve()),'sha256':sha(Path(resolved))}
        driver_files=[]
        for name in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep):
            if not name:continue
            path=Path(name);entry={'manifest':str(path),'manifest_sha256':sha(path)}
            library=Path(json.loads(path.read_text())['ICD']['library_path'])
            if library.is_absolute() and library.is_file():entry.update(library=str(library),library_sha256=sha(library))
            driver_files.append(entry)
        layer_files={}
        for folder in os.environ.get('VK_LAYER_PATH','').split(os.pathsep):
            if not folder:continue
            for path in Path(folder).glob('*.json'):
                layer_files[str(path)]=sha(path)
        (out/'toolchain-provenance.json').write_text(json.dumps({'system':platform.platform(),'tools':binaries,'drivers':driver_files,'layer_manifests':layer_files},indent=2)+'\n')
        for label,command in [('tests-head',['git','rev-parse','HEAD','HEAD^{tree}']),('tests-status',['git','status','--porcelain']),('compiler',[os.environ.get('CXX','g++'),'--version']),('glslang',[os.environ.get('GLSLANG','glslangValidator'),'--version']),('spirv-val',[os.environ.get('SPIRV_VAL','spirv-val'),'--version'])]:run(label,command)
        skill=os.environ.get('VULKAN_SKILL_ROOT')
        if skill:run('skill-head',['git','-C',skill,'rev-parse','HEAD','HEAD^{tree}'])
        run('build',[HERE/'build.sh',out/'build'])
        run('vulkan',[out/'build/text_vector_lab',out/'build/shaders',out/'frames'])
        log=(out/'vulkan.log').read_text()
        if 'VALIDATION:' in log:raise RuntimeError('validation diagnostics present; inspect raw log')
        findings=verify(out)
        (out/'pixel-verification.json').write_text(json.dumps(findings,indent=2)+'\n')
        snapshot={str(p.relative_to(out/'frames')):sha(p) for p in (out/'frames').iterdir()}
        run('refuse-overwrite',[out/'build/text_vector_lab',out/'build/shaders',out/'frames'],1)
        if snapshot!={str(p.relative_to(out/'frames')):sha(p) for p in (out/'frames').iterdir()}:raise ValueError('overwritten evidence')
        run('refuse-rebuild',[HERE/'build.sh',out/'build'],1)
        status='PASS'
    except Exception as exc:error=f'{type(exc).__name__}: {exc}'
    summary={'validation_enabled': 'validation_enabled=1' in (out/'vulkan.log').read_text() if (out/'vulkan.log').exists() else False, 'status':status,'error':error,'layer':'actual Vulkan integration','size':[65,49],'scope':'synthetic coverage upload/sample/blend/readback; five serialized page updates; explicit preserved non-target overlay fallback','unverified':['system font shaping','MSDF/MTSDF','vector tessellation/extrusion','active MRT independentBlend','depth/stencil sentinel','concurrent atlas generation stress','Android/Windows hardware','sustained performance','platform typography quality']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'artifact-manifest.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()},indent=2)+'\n')
    print(json.dumps(summary));return 0 if status=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
