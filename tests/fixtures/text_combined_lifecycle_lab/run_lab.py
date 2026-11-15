#!/usr/bin/env python3
"""One-device integrated packed-quad publication/cancel/retirement fixture."""
import argparse,importlib.util,json,os,subprocess,shutil,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p,name):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def verify(out):
    quad=load(HERE.parent/'text_packed_quad_lab/run_lab.py','quad_oracle')
    phases=[dict(phase='cancel_B_pending',published=0,A_pending=True,B_upload_pending=True,live_pages=2),dict(phase='cancel_B_retired',published=0,live_pages=1),dict(phase='new_B_published_pending',published=2,live_pages=2),dict(phase='old_A_retired',published=2,live_pages=1)]
    events=[json.loads(s) for s in (out/'frames/events.jsonl').read_text().splitlines()]
    if events!=phases:raise ValueError('retirement/publication events mismatch')
    results=[]
    for name,reference in [('old-A',out),('route-after-cancel',out),('new-B',out/'new-reference')]:
        r=quad.verify(reference,out/'frames'/name);r['stage']=name;results.append(r)
    try:quad.verify(out,out/'frames/wrong-cancel-route')
    except ValueError as e:
        if 'composition mismatch' not in str(e):raise
    else:raise ValueError('canceled candidate route not rejected')
    return results

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    def run(name,args,expected=0):
        r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
        if r.returncode!=expected or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
        return log
    import sys
    quad=HERE.parent/'text_packed_quad_lab';run('prepare-real-glyphs',[sys.executable,quad/'run_lab.py','--out',out/'prepared','--font',a.font])
    prepared=out/'prepared';build=prepared/'build';reference=json.loads((prepared/'reference.json').read_text());(out/'reference.json').write_text(json.dumps(reference)+'\n')
    newref=json.loads(json.dumps(reference))
    for g in newref['glyphs']:g['pixels']=[v*.5 for v in g['pixels']]
    (out/'new-reference').mkdir();(out/'new-reference/reference.json').write_text(json.dumps(newref)+'\n')
    engine=HERE.parent/'engine_scale_lab/main.cpp';s=engine.read_text();old='enabled12.drawIndirectCount = countEnabled;'
    if s.count(old)!=1:raise ValueError('helper hook changed')
    s=s.replace(old,old+'\nif(!f12.timelineSemaphore)throw std::runtime_error("timeline unavailable");enabled12.timelineSemaphore=VK_TRUE;');(build/'combined_engine.hpp').write_text(s)
    s=(build/'quad_lab_reused.hpp').read_text()
    for old,new in [(str(engine),str(build/'combined_engine.hpp')),('dp.maxSets=1;','dp.flags=VK_DESCRIPTOR_POOL_CREATE_FREE_DESCRIPTOR_SET_BIT;dp.maxSets=3;'),('VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1};','VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,3};')]:
        if s.count(old)!=1:raise ValueError('pipeline hook changed '+old)
        s=s.replace(old,new)
    (build/'combined_pipeline.hpp').write_text(s)
    cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build)]
    if os.environ.get('VULKAN_SDK_PREFIX'):cmd+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
    run('compile',cmd+[HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'combined_lab'])
    args=[build/'combined_lab',build/'shaders',prepared/'atlas.f32',prepared/'vertices.f32']
    log=run('vulkan',args+[out/'frames'])
    if 'validation_enabled=1' not in log or 'COMBINED_RESOURCES_DESTROYED' not in log:raise ValueError('validation/cleanup evidence missing')
    results=verify(out)
    abort=run('abort-pending',args+[out/'aborted','--abort-pending'],1)
    if 'INTENTIONAL_COMBINED_PENDING_CLEANUP' not in abort or 'CLEANUP_TIMEOUT' in abort or 'COMBINED_PENDING_CLEANUP_OK' not in abort:raise ValueError('pending cleanup failed')
    before={str(p.relative_to(out/'frames')):sha(p) for p in (out/'frames').rglob('*') if p.is_file()}
    run('refuse-overwrite',args+[out/'frames'],1)
    if before!={str(p.relative_to(out/'frames')):sha(p) for p in (out/'frames').rglob('*') if p.is_file()}:raise ValueError('overwritten evidence')
    summary={'status':'PASS','validation_enabled':True,'draws':results,'actual_draw_count':4,'actual_upload_count':3,'peak_atlas_pages':2,'negative_checks':['actual completed canceled descriptor route rejected','controlled pending submissions cleanup','existing output refused unchanged'],'scope':'same device/queue actual packed vertex quads plus two-page cancellation/growth/retirement; generation2 scales trusted glyph coverage by0.5','limits':['controlled nonoverlapping integer nearest quads','ALL_COMMANDS gate means submission pending, not shader executing','single queue blocks candidate upload behind old draw','not full allocator/device-loss cleanup','not production packing, multidevice or target hardware']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    provenance={'sources':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'main.cpp',HERE/'run_lab.py',quad/'run_lab.py',quad/'quad.vert',engine]},'binary_sha256':sha(build/'combined_lab'),'generated_hashes':{p.name:sha(p) for p in [build/'combined_engine.hpp',build/'combined_pipeline.hpp']},'prepared_tool_driver_receipt':json.loads((prepared/'local-provenance.json').read_text())}
    (out/'local-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');print(json.dumps(summary));return 0
if __name__=='__main__':raise SystemExit(main())
