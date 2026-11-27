#!/usr/bin/env python3
"""Actual Vulkan single-queue multi-inflight retirement experiment."""
import argparse,hashlib,json,os,platform,shutil,struct,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out):
    results=json.loads((out/'frames/numerics.json').read_text())
    if results!={'generations':64,'readbacks':128,'final_counter':128,'validation_enabled':True,'max_error':0}:raise ValueError('incomplete GPU result or validation disabled')
    rows=[json.loads(x) for x in (out/'frames/generations.jsonl').read_text().splitlines()]
    if len(rows)!=64:raise ValueError('incomplete generations')
    for gen,row in enumerate(rows):
        expected={'generation':gen,'pending':2*gen,'partial':2*gen+1,'complete':2*gen+2,'reuse_before_A':False,'reuse_before_B':False,'reuse_after_B':True,'image_slots':1,'buffers':5,'commands':3,'fences':3,'semaphores':3,'pending_fences_after_wait':0}
        if row!=expected:raise ValueError('retirement/resource boundary mismatch')
        for consumer in range(2):
            raw=(out/f'frames/g{gen}-c{consumer}.f32').read_bytes()
            if len(raw)!=768*4:raise ValueError('truncated readback')
            actual=struct.unpack('<768f',raw)
            if actual!=tuple((gen+1)*.25+(i%17)/1024 for i in range(768)):raise ValueError('wrong generation readback')
    return results

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args(argv)
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);commands=[]
    def run(label,args,expected=0):
        start=time.monotonic()
        try:
            with (out/f'{label}.log').open('x') as log:code=subprocess.run(list(map(str,args)),cwd=REPO,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
        except (OSError,subprocess.TimeoutExpired) as exc:code=str(exc)
        commands.append({'label':label,'argv':list(map(str,args)),'returncode':code,'expected':expected,'wall_seconds':time.monotonic()-start})
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if code!=expected:raise RuntimeError(f'{label}: {code}')
    status='FAIL';error=None;numeric=None
    try:
        source={str(x.relative_to(REPO)):sha(x) for x in [HERE/'main.cpp',HERE/'run_lab.py',HERE.parent/'text_inflight_lab/main.cpp']}
        (out/'source-manifest.json').write_text(json.dumps(source,indent=2)+'\n')
        run('tests-head',['git','rev-parse','HEAD','HEAD^{tree}']);run('tests-status',['git','status','--porcelain'])
        if os.environ.get('VULKAN_SKILL_ROOT'):run('skill-head',['git','-C',os.environ['VULKAN_SKILL_ROOT'],'rev-parse','HEAD','HEAD^{tree}'])
        cxx=os.environ.get('CXX','g++');run('compiler-version',[cxx,'--version'])
        env={x:os.environ.get(x) for x in ['VULKAN_SDK_PREFIX','VK_DRIVER_FILES','VK_LAYER_PATH','LD_LIBRARY_PATH']}
        driver_hashes={}
        for name in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep):
            if not name:continue
            path=Path(name);driver_hashes[str(path)]=sha(path)
            library=Path(json.loads(path.read_text())['ICD']['library_path'])
            if library.is_absolute() and library.is_file():driver_hashes[str(library)]=sha(library)
        (out/'environment.json').write_text(json.dumps({'environment':env,'system':platform.platform(),'compiler_sha256':sha(Path(shutil.which(cxx))),'driver_sha256':driver_hashes},indent=2)+'\n')
        include=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include'] if os.environ.get('VULKAN_SDK_PREFIX') else []
        run('build',[cxx,'-std=c++17','-O2','-Wall','-Wextra','-Wno-missing-field-initializers',*include,HERE/'main.cpp','-l:libvulkan.so.1','-o',out/'churn_lab'])
        run('vulkan',[out/'churn_lab',out/'frames'])
        if 'VALIDATION:' in (out/'vulkan.log').read_text():raise ValueError('validation diagnostics')
        numeric=verify(out)
        if 'CHURN_RESOURCES_DESTROYED' not in (out/'vulkan.log').read_text():raise ValueError('cleanup marker missing')
        run('abort-pending',[out/'churn_lab',out/'aborted','--abort-pending'],1)
        aborted=(out/'abort-pending.log').read_text()
        if 'INTENTIONAL_ABORT_PENDING_GENERATION_31' not in aborted or 'VALIDATION:' in aborted or 'CLEANUP_TIMEOUT' in aborted:raise ValueError('pending cleanup did not terminate cleanly')
        before={x.name:sha(x) for x in (out/'frames').iterdir()}
        run('refuse-overwrite',[out/'churn_lab',out/'frames'],1)
        if before!={x.name:sha(x) for x in (out/'frames').iterdir()}:raise ValueError('evidence overwrite')
        status='PASS'
    except Exception as exc:error=f'{type(exc).__name__}: {exc}'
    summary={'status':status,'error':error,'layer':'actual Vulkan image-transfer retirement','numeric':numeric,'limits':['single queue, multiple in-flight submissions, not multi-queue parallel hardware','transfer read consumers, not sampled draw/descriptor retirement','64 generations of one fixture slot with persistent commands/fences/buffers; not production atlas packing or GPU allocator leak proof','no Android/Windows target device validation or performance claim']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'artifact-manifest.json').write_text(json.dumps({str(x.relative_to(out)):sha(x) for x in sorted(out.rglob('*')) if x.is_file()},indent=2)+'\n')
    print(json.dumps(summary));return 0 if status=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
