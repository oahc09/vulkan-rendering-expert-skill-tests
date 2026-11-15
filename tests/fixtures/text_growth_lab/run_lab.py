#!/usr/bin/env python3
"""Actual Vulkan single-queue multi-inflight retirement experiment."""
import argparse,hashlib,json,os,platform,shutil,struct,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out):
    results=json.loads((out/'frames/numerics.json').read_text())
    expected={'validation_enabled':True,'page_creates':3,'pages_destroyed_before_final_cleanup':2,'peak_live_pages':2,'final_route_generation':2,'readbacks':5,'max_error':0}
    if results!=expected:raise ValueError('incomplete growth result')
    rows=[json.loads(x) for x in (out/'frames/events.jsonl').read_text().splitlines()]
    expected_rows=[('cancel_pending',0,2,1),('A_done_B_pending',0,2,2),('canceled_reclaimed',0,1,5),('new_published_old_retired',2,1,6)]
    if rows!=[dict(phase=p,published=g,live_pages=n,completed=c) for p,g,n,c in expected_rows]:raise ValueError('publication or retirement boundary mismatch')
    for name,gen in [('old-A',0),('old-B',0),('cancel-diagnostic',1),('route-after-cancel',0),('published-new',2)]:
        raw=(out/f'frames/{name}.f32').read_bytes()
        if len(raw)!=768*4:raise ValueError('truncated readback')
        if struct.unpack('<768f',raw)!=tuple((gen+1)*.25+(i%17)/1024 for i in range(768)):raise ValueError('wrong generation readback')
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
        run('build',[cxx,'-std=c++17','-O2','-Wall','-Wextra','-Wno-missing-field-initializers',*include,HERE/'main.cpp','-l:libvulkan.so.1','-o',out/'growth_lab'])
        run('vulkan',[out/'growth_lab',out/'frames'])
        if 'VALIDATION:' in (out/'vulkan.log').read_text():raise ValueError('validation diagnostics')
        numeric=verify(out)
        if 'GROWTH_RESOURCES_DESTROYED' not in (out/'vulkan.log').read_text():raise ValueError('cleanup marker missing')
        run('abort-pending',[out/'growth_lab',out/'aborted','--abort-pending'],1)
        aborted=(out/'abort-pending.log').read_text()
        if 'INTENTIONAL_GROWTH_CANCEL_PENDING' not in aborted or 'VALIDATION:' in aborted or 'CLEANUP_TIMEOUT' in aborted:raise ValueError('pending cleanup did not terminate cleanly')
        run('abort-recording',[out/'growth_lab',out/'record-aborted','--abort-recording'],1)
        recorded=(out/'abort-recording.log').read_text()
        if 'INTENTIONAL_RECORD_FAILURE_RESTORED' not in recorded or any(x in recorded for x in ['VALIDATION:','SLOT_NOT_RESTORED','CLEANUP_TIMEOUT']):raise ValueError('record failure cleanup did not restore slot')
        before={x.name:sha(x) for x in (out/'frames').iterdir()}
        run('refuse-overwrite',[out/'growth_lab',out/'frames'],1)
        if before!={x.name:sha(x) for x in (out/'frames').iterdir()}:raise ValueError('evidence overwrite')
        status='PASS'
    except Exception as exc:error=f'{type(exc).__name__}: {exc}'
    summary={'status':status,'error':error,'layer':'actual Vulkan image-transfer retirement','numeric':numeric,'limits':['single queue, multiple in-flight submissions, not multi-queue parallel hardware','transfer read consumers, not sampled draw/descriptor retirement','bounded two-page growth/cancel/reclaim cycle; fixture handles, not production packing or GPU allocator leak proof','no Android/Windows target device validation or performance claim']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'artifact-manifest.json').write_text(json.dumps({str(x.relative_to(out)):sha(x) for x in sorted(out.rglob('*')) if x.is_file()},indent=2)+'\n')
    print(json.dumps(summary));return 0 if status=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
