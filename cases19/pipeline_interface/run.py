"""Real compiler -> pipeline interface -> descriptor -> dispatch -> readback pair."""
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, uuid, importlib.util

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--tools',type=pathlib.Path,required=True);p.add_argument('--include',required=True);p.add_argument('--loader',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);src=pathlib.Path(__file__).parent
    report={'run_id':str(uuid.uuid4()),'runner_sha256':sha(__file__),'cases':{},'tools':{},'scope':'Original deliberate shader/layout fault injection; CPU ICD actual dispatch, not external production bug or mobile qualification.'}
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
    if before.count('#define LAYOUT_DESCRIPTOR_TYPE VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER')!=1 or after!=before.replace('#define LAYOUT_DESCRIPTOR_TYPE VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER','#define LAYOUT_DESCRIPTOR_TYPE VK_DESCRIPTOR_TYPE_STORAGE_BUFFER'):raise ValueError('patch outside one-line repair')
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
    if caps!=['Shader'] or extensions or 'DescriptorSet 0' not in text or 'Binding 0' not in text or 'StorageBuffer' not in text:raise ValueError('unexpected shader interface')
    report['shader']=dict(source_sha256=sha(src/'compute.comp'),spirv_sha256=sha(spv),disassembly_sha256=sha(asm),target_env='vulkan1.1',capabilities=caps,extensions=extensions,compile=clog,validate=vlog,disassemble=dlog)
    rule_path=src.resolve().parents[1]/'tools'/'pipeline_interface19.py'
    specmod=importlib.util.spec_from_file_location('pipeline_interface19',rule_path);rule=importlib.util.module_from_spec(specmod);specmod.loader.exec_module(rule)
    report['rule_sha256']=sha(rule_path)
    validation_record=dict(artifact_sha256=sha(spv),disassembly_sha256=sha(asm),exit_code=vlog['exit_code'],target_env='vulkan1.1')
    reflection=rule.reflect(artifact_sha256=sha(spv),disassembly=text,extraction_sha256=sha(asm),validation=validation_record)
    if reflection['status']!='BOUNDED_REFLECTION':raise ValueError('actual reflection unavailable')
    report['reflection']=reflection;report['validation_record']=validation_record
    identity=None
    for name,kind,mode,expected_vuid,exit_code,output in [('bad-type','baseline','normal','07990',0,0),('good','fixed','normal',None,0,42),('missing-binding','fixed','missing-binding','07988',0,0),('wrong-output','fixed','wrong-output',None,6,42)]:
        r,log=run(name,[a.output/(kind+'-probe'),mode,spv]);lines=r.stderr.decode().splitlines();ids=[json.loads(x[9:]) for x in lines if x.startswith('IDENTITY ')];mem=[json.loads(x[7:]) for x in lines if x.startswith('MEMORY ')];vuids=[x for x in lines if x.startswith('VUID ')];others=[x for x in lines if not x.startswith(('IDENTITY ','MEMORY ','VUID ','LAYOUT '))]
        expected=[] if expected_vuid is None else ['VUID phase=pipeline-create id=VUID-VkComputePipelineCreateInfo-layout-'+expected_vuid]
        result=json.loads(r.stdout)
        layouts=[json.loads(x[7:]) for x in lines if x.startswith('LAYOUT ')]
        if len(layouts)!=1:raise ValueError('missing actual layout record')
        admission=rule.compare(reflection,layouts[0],artifact_sha256=sha(spv))
        actual_ids=[x.split(' id=',1)[1] for x in vuids]
        if admission.get('vuids')!=actual_ids or admission['status']!=('REJECTED_INTERFACE' if expected else 'WITHIN_CHECKED_INTERFACE'):raise ValueError('rule/API interface mismatch')
        if r.returncode!=exit_code or result!={'mode':mode,'output':output,'errors':len(expected),'pipeline_result':-1000011001 if expected else 0,'exit_code':exit_code} or vuids!=expected or others:raise ValueError('unexpected actual pipeline result: '+name)
        if len(ids)!=1 or len(mem)!=1 or ids[0]['device_type']!=4 or ids[0]['layer_spec']!=spec or ids[0]['layer_impl']!=int(layer['implementation_version']):raise ValueError('identity mismatch')
        if mem[0]['flags']&6!=6 or not mem[0]['compatible_bits']&(1<<mem[0]['type']):raise ValueError('not compatible coherent mapped memory')
        if identity is None:identity=ids[0]
        if ids[0]!=identity:raise ValueError('runtime changed')
        report['cases'][name]=dict(result=result,layout=layouts[0],admission=admission,log=log,diagnostics=vuids,memory=mem[0],binary_sha256=report['repair'][kind+'_binary_sha256'],shader_sha256=sha(spv),status='ORACLE_NEGATIVE_EXPECTED_FAILURE' if name=='wrong-output' else 'EXPECTED_DIAGNOSTIC_ABORT' if expected else 'DISPATCH_READBACK_PASS')
    report['identity']=identity;report['status']='BOUNDED_PIPELINE_INTERFACE_REPAIR_PASS'
    report['limitations']=['Not external engineering acceptance.','wrong-output is an oracle negative, not an independent discovered GPU fault.','Coherent CPU memory only; no noncoherent or mobile claim.','Ordinary Validation only; not SyncVal or GPU-AV.']
    (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
if __name__=='__main__':main()
