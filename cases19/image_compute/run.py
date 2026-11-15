"""Real upload/image/descriptor/compute/synchronization/readback repair chain."""
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, uuid, importlib.util

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--tools',type=pathlib.Path,required=True);p.add_argument('--include',required=True);p.add_argument('--loader',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);os.environ['VK_LAYER_SYNCVAL_SHADER_ACCESSES_HEURISTIC']='true';src=pathlib.Path(__file__).parent
    report={'run_id':str(uuid.uuid4()),'runner_sha256':sha(__file__),'cases':{},'tools':{},'scope':'Original integrated image synchronization fault injection; CPU coherent ICD only, not an external engineering case.'}
    def run(label,cmd,cwd=None):
        r=subprocess.run(list(map(str,cmd)),cwd=cwd,capture_output=True,timeout=60)
        (a.output/(label+'.stdout')).write_bytes(r.stdout);(a.output/(label+'.stderr')).write_bytes(r.stderr)
        return r,dict(exit_code=r.returncode,stdout_sha256=hashlib.sha256(r.stdout).hexdigest(),stderr_sha256=hashlib.sha256(r.stderr).hexdigest())
    for name in ('glslangValidator','spirv-val','spirv-dis'):
        tool=a.tools/name;r,log=run(name+'.version',[tool,'--version'])
        if r.returncode or not r.stdout:raise ValueError('version query failed')
        report['tools'][name]=dict(binary_sha256=sha(tool),version=r.stdout.decode().strip(),log=log)
    report['compiler']=subprocess.check_output(['gcc','--version'],text=True).splitlines()[0]
    report['loader_sha256']=sha(a.loader);report['icd_manifest_sha256']=sha(os.environ['VK_DRIVER_FILES'])
    manifest=pathlib.Path(os.environ['VK_LAYER_PATH'])/'VkLayer_khronos_validation.json';report['layer_manifest_sha256']=sha(manifest)
    layer=json.loads(manifest.read_text())['layer'];v=list(map(int,layer['api_version'].split('.')));spec=(v[0]<<22)|(v[1]<<12)|v[2]
    fixed=a.output/'fixed';fixed.mkdir();shutil.copyfile(src/'baseline.c',fixed/'baseline.c')
    r,log=run('patch',['patch','--batch','--fuzz=0','-p0','-i',(src/'fix.patch').resolve()],cwd=fixed)
    if r.returncode:raise ValueError('patch failed')
    before=(src/'baseline.c').read_text();after=(fixed/'baseline.c').read_text()
    if before.count('#define UPLOAD_DEPENDENCY 0')!=1 or after!=before.replace('#define UPLOAD_DEPENDENCY 0','#define UPLOAD_DEPENDENCY 1'):raise ValueError('patch outside one-line repair')
    report['repair']=dict(baseline_sha256=sha(src/'baseline.c'),fixed_sha256=sha(fixed/'baseline.c'),patch_sha256=sha(src/'fix.patch'),log=log)
    for kind,source in [('baseline',src/'baseline.c'),('fixed',fixed/'baseline.c')]:
        r,log=run(kind+'.build',['gcc','-Wall','-Wextra','-Werror','-I'+a.include,source,a.loader,'-o',a.output/(kind+'-probe')])
        if r.returncode:raise ValueError('C build failed')
        report['repair'][kind+'_binary_sha256']=sha(a.output/(kind+'-probe'));report['repair'][kind+'_build']=log
    spv=a.output/'compute.spv';asm=a.output/'compute.spvasm'
    r,clog=run('shader.compile',[a.tools/'glslangValidator','-V','--target-env','vulkan1.1','-S','comp',src/'compute.comp','-o',spv])
    if r.returncode:raise ValueError('shader compilation failed')
    r,vlog=run('shader.validate',[a.tools/'spirv-val','--target-env','vulkan1.1',spv])
    if r.returncode or r.stdout or r.stderr:raise ValueError('shader validation failed')
    r,dlog=run('shader.dis',[a.tools/'spirv-dis',spv,'-o',asm])
    if r.returncode:raise ValueError('disassembly failed')
    text=asm.read_text();caps=re.findall(r'^\s*OpCapability\s+(\w+)\s*$',text,re.M);extensions=re.findall(r'^\s*OpExtension\s+"([^"]+)"\s*$',text,re.M)
    if caps!=['Shader'] or extensions or 'DescriptorSet 0' not in text or 'Binding 0' not in text or 'Binding 1' not in text or 'OpImageRead' not in text or 'OpImageWrite' not in text or 'R32ui' not in text:raise ValueError('unexpected shader interface')
    report['shader']=dict(source_sha256=sha(src/'compute.comp'),spirv_sha256=sha(spv),disassembly_sha256=sha(asm),target_env='vulkan1.1',capabilities=caps,extensions=extensions,compile=clog,validate=vlog,disassemble=dlog)
    report['validation_settings']={'synchronization_validation':True,'syncval_shader_accesses_heuristic':True,'source':'official layer manifest setting; enabled explicitly via VK_LAYER_SYNCVAL_SHADER_ACCESSES_HEURISTIC=true','limitation':'Static shader-access heuristic may miss accesses or report false positives; not GPU-AV.'}
    expected_pixels=[(i*11+5)*3+7 for i in range(16)]
    report['oracle']={'extent':[4,4,1],'format':'R32_UINT','input_pixels':[i*11+5 for i in range(16)],'transform':'input * 3 + 7','expected_pixels':expected_pixels,'comparison':'every uint pixel exactly; no aggregate tolerance'}
    identity=None
    for name,kind,mode,phase,ids,exit_code in [
        ('missing-upload-dependency','baseline','normal','compute-dispatch',['SYNC-HAZARD-READ-AFTER-WRITE'],0),
        ('good','fixed','normal',None,[],0),
        ('bad-layout','fixed','bad-layout','compute-dispatch',['VUID-VkDescriptorImageInfo-imageLayout-00344','VUID-vkCmdDispatch-None-08114'],0),
        ('missing-readback-dependency','fixed','bad-readback','readback',['SYNC-HAZARD-READ-AFTER-WRITE'],0),
        ('wrong-output','fixed','wrong-output',None,[],6)]:
        r,log=run(name,[a.output/(kind+'-probe'),mode,spv]);lines=r.stderr.decode().splitlines()
        prefixes=('IDENTITY','CAPABILITY','IMAGE_QUERY','MEMORY','IMAGE_MEMORY','DESCRIPTOR','BARRIER','COPY_UPLOAD','COPY_READBACK','COMPLETION','INPUT')
        records={prefix:[json.loads(x[len(prefix)+1:]) for x in lines if x.startswith(prefix+' ')] for prefix in prefixes}
        diagnostics=[x for x in lines if x.startswith('DIAGNOSTIC ')]
        others=[x for x in lines if not x.startswith(tuple(p+' ' for p in prefixes)+('DIAGNOSTIC ',))]
        result=json.loads(r.stdout)
        expected_diags=['DIAGNOSTIC phase='+str(phase)+' id='+v for v in ids]
        if r.returncode!=exit_code or result['exit_code']!=exit_code or result['mode']!=mode or diagnostics!=expected_diags or result['errors']!=len(ids) or others:raise ValueError('unexpected API/SyncVal result: '+name)
        if result['submitted']!= (not ids) or result['upload_dependency']!=(kind=='fixed') or result['pixels']!=(expected_pixels if not ids else [0]*16):raise ValueError('unexpected execution/pixel result')
        if len(records['IDENTITY'])!=1 or len(records['CAPABILITY'])!=1 or len(records['IMAGE_QUERY'])!=1:raise ValueError('missing runtime query')
        actual=records['IDENTITY'][0];cap=records['CAPABILITY'][0];query=records['IMAGE_QUERY'][0]
        if actual['device_type']!=4 or actual['layer_spec']!=spec or actual['layer_impl']!=int(layer['implementation_version']) or actual['sync_validation'] is not True:raise ValueError('identity mismatch')
        if identity is None:identity=actual
        if actual!=identity:raise ValueError('runtime changed')
        if query['format']!=98 or query['imageType']!=1 or query['tiling']!=0 or query['usage']!=11 or query['flags']!=0 or query['result']!=0 or not query['samples']&1:raise ValueError('unexpected queried image format combination')
        if cap['format']!=98 or cap['optimal_features']&49154!=49154 or cap['storage_images_limit']<2 or min(cap['max_width'],cap['max_height'])<4 or cap['optional_features_enabled'] is not False:raise ValueError('format capability unavailable')
        for prefix,key in [('MEMORY','buffer'),('IMAGE_MEMORY','image')]:
            if len(records[prefix])!=2 or [m[key] for m in records[prefix]]!=[0,1]:raise ValueError('missing allocation records')
            for m in records[prefix]:
                if not m['bits']&(1<<m['type']) or m['size']<64 or m['alignment']<1 or (prefix=='MEMORY' and m['flags']&6!=6):raise ValueError('memory compatibility failed')
        if records['INPUT']!=[[i*11+5 for i in range(16)]]:raise ValueError('actual upload input differs from oracle')
        if records['DESCRIPTOR']!=[dict(set=0,binding=i,type=3,count=1,stage=32,imageLayout=1,image=i) for i in range(2)]:raise ValueError('unexpected actual descriptor configuration')
        def barrier(image,phase,old,new,sa,da,ss,ds):
            return dict(image=image,phase=phase,oldLayout=old,newLayout=new,srcAccess=sa,dstAccess=da,srcStage=ss,dstStage=ds,aspect=1,baseMip=0,levels=1,baseLayer=0,layers=1)
        expected_barriers=[barrier(0,'initial-layouts',0,1,0,4096,1,4096),barrier(1,'initial-layouts',0,1,0,64,1,2048)]
        if kind=='fixed':expected_barriers.append(barrier(0,'upload',1,6 if mode=='bad-layout' else 1,4096,32,4096,2048))
        if not ids:expected_barriers.append(barrier(1,'readback',1,6,64,2048,2048,4096))
        if records['BARRIER']!=expected_barriers:raise ValueError('unexpected actual dependency/layout manifest')
        if records['COPY_UPLOAD']!=[dict(image=0,layout=1,width=4,height=4,depth=1,aspect=1,mip=0,baseLayer=0,layerCount=1)]:raise ValueError('upload subresource mismatch')
        expected_copy=[dict(image=1,layout=1 if mode=='bad-readback' else 6,width=4,height=4,depth=1)] if not ids or mode=='bad-readback' else []
        if records['COPY_READBACK']!=expected_copy:raise ValueError('readback manifest mismatch')
        completion=[] if ids else [dict(fence_wait='SUCCESS',host_barrier_src_access=4096,host_barrier_dst_access=8192)]
        if records['COMPLETION']!=completion:raise ValueError('completion evidence mismatch')
        report['cases'][name]=dict(result=result,log=log,diagnostics=diagnostics,actual_manifest=records,binary_sha256=report['repair'][kind+'_binary_sha256'],shader_sha256=sha(spv),status='EXPECTED_ORACLE_FAILURE' if name=='wrong-output' else 'EXPECTED_DIAGNOSTIC_ABORT' if ids else 'ALL_PIXELS_EXACT_PASS')
    # Record the pinned layer's detection limitation using the same baseline binary.
    os.environ['VK_LAYER_SYNCVAL_SHADER_ACCESSES_HEURISTIC']='false'
    r,off_log=run('heuristic-off',[a.output/'baseline-probe','normal',spv])
    off_result=json.loads(r.stdout)
    if r.returncode!=5 or off_result['errors']!=0 or off_result['submitted'] or 'DIAGNOSTIC ' in r.stderr.decode():raise ValueError('heuristic-off observation changed; review required')
    os.environ['VK_LAYER_SYNCVAL_SHADER_ACCESSES_HEURISTIC']='true'
    report['heuristic_off_observation']={'status':'HAZARD_NOT_DETECTED_NOT_PASS','result':off_result,'log':off_log,'binary_sha256':report['repair']['baseline_binary_sha256'],'shader_sha256':sha(spv),'note':'Same actual missing-dependency program, heuristic explicitly disabled. No submission; exit5 prevents false pass.'}
    report['identity']=identity;report['status']='INTEGRATED_IMAGE_UPLOAD_COMPUTE_READBACK_REPAIR_PASS'
    report['limitations']=['Original controlled experiment, not external engineering acceptance.','CPU coherent staging/readback only; noncoherent visibility remains unrun.','One queue, R32_UINT 4x4 single mip/layer/sample only; no sparse/alias/cross-queue/multiplanar coverage.','Storage image load/store, not filtered texture sampling.','Shader-access SyncVal heuristic explicitly enabled; default-disabled discovery did not detect baseline and was not called a pass.','wrong-output is an oracle negative, not a discovered GPU fault.']
    (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
if __name__=='__main__':main()
