"""Fail closed real memory discovery and bounded API experiment; no simulated capabilities."""
import argparse, hashlib, json, os, pathlib, subprocess, uuid

def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--include',required=True)
    p.add_argument('--loader',required=True)
    p.add_argument('--output',type=pathlib.Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=False)
    source=pathlib.Path(__file__).with_name('probe.c'); exe=a.output/'probe'
    cmd=['gcc','-Wall','-Wextra','-Werror','-I'+a.include,str(source),a.loader,'-o',str(exe)]
    build=subprocess.run(cmd,capture_output=True,timeout=60)
    (a.output/'build.stdout').write_bytes(build.stdout);(a.output/'build.stderr').write_bytes(build.stderr)
    if build.returncode: raise RuntimeError('build failed')
    report={'run_id':str(uuid.uuid4()),'source_sha256':sha(source),'runner_sha256':sha(__file__),'binary_sha256':sha(exe),'loader_sha256':sha(a.loader),'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],'cases':{},'scope':'Original deliberate API-boundary experiment. CPU ICD only. Not external-production, hardware or mobile acceptance.'}
    icd=pathlib.Path(os.environ['VK_DRIVER_FILES']); report['icd_manifest_sha256']=sha(icd)
    manifest=pathlib.Path(os.environ['VK_LAYER_PATH'])/'VkLayer_khronos_validation.json'
    report['layer_manifest_sha256']=sha(manifest)
    lm=json.loads(manifest.read_text())['layer']; parts=list(map(int,lm['api_version'].split('.'))); expected_spec=(parts[0]<<22)|(parts[1]<<12)|parts[2]
    baseline=None
    for mode in ('visibility','good','offset','size'):
        r=subprocess.run([str(exe),mode],capture_output=True,timeout=30)
        (a.output/(mode+'.stdout')).write_bytes(r.stdout);(a.output/(mode+'.stderr')).write_bytes(r.stderr)
        if r.returncode: raise RuntimeError(f'{mode}: probe exit {r.returncode}')
        records=[json.loads(line) for line in r.stdout.decode().splitlines()]
        devices=[x for x in records if x['kind']=='device']; layers=[x for x in records if x['kind']=='layer']; results=[x for x in records if x['kind']=='result']
        if len(layers)!=1 or layers[0]['specVersion']!=expected_spec or layers[0]['implementationVersion']!=int(lm['implementation_version']): raise ValueError('layer mismatch')
        if len(results)!=1 or not devices or any(d['deviceType']!=4 for d in devices): raise ValueError('unexpected scope or incomplete evidence')
        if baseline is None: baseline=devices
        if devices!=baseline: raise ValueError('runtime changed')
        selection=[x for x in records if x['kind']=='selection']
        if results[0]['status']!='UNAVAILABLE_NOT_RUN':
            if len(selection)!=1: raise ValueError('ambiguous selection')
            selected=selection[0]; device=next(d for d in devices if d['index']==selected['deviceIndex']); mt=next(t for t in device['memoryTypes'] if t['index']==selected['memoryTypeIndex'])
            if mt['flags']!=selected['flags'] or not mt['flags']&2 or not device['memoryTypeBits']&(1<<mt['index']): raise ValueError('invalid memory selection')
            if results[0].get('memoryTypeIndex')!=selected['memoryTypeIndex']: raise ValueError('result selection mismatch')
            if mode=='visibility' and mt['flags']&4: raise ValueError('coherent substitution')
        elif selection: raise ValueError('unavailable but selected')
        result=results[0]; diagnostics=r.stderr.decode().splitlines()
        expected=['VUID VUID-VkMappedMemoryRange-size-00685'] if mode in ('offset','size') else []
        if diagnostics!=expected: raise ValueError(f'{mode}: unexpected diagnostics {diagnostics}')
        eligible=[(d,t) for d in devices for t in d['memoryTypes'] if d['memoryTypeBits']&(1<<t['index']) and t['flags']&2 and not t['flags']&4]
        if mode=='visibility':
            if not eligible and result['status']!='UNAVAILABLE_NOT_RUN': raise ValueError('invented noncoherent availability')
            if eligible and (result['status']!='NON_COHERENT_READBACK_PASS' or result.get('value')!=0x12345678): raise ValueError('noncoherent readback failed')
        elif result['status']!='API_ONLY' or result['errors']!=len(expected) or result['flushResult']!=(-1000011001 if expected else 0): raise ValueError('API oracle mismatch')
        report['cases'][mode]={'result':result,'selection':selection,'diagnostics':diagnostics,'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()}
    report['devices']=baseline; report['layer']=layers[0]
    report['status']='API_BOUNDARY_PASS_NON_COHERENT_UNAVAILABLE' if report['cases']['visibility']['result']['status']=='UNAVAILABLE_NOT_RUN' else 'BOUNDED_NON_COHERENT_AND_API_PASS'
    report['limitations']=['Coherent API-boundary checks never establish noncoherent visibility.','When unavailable, transfer/flush/fence/invalidate path is compiled only, not runtime validated.','Validation callback aborts invalid calls before driver execution.']
    (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
if __name__=='__main__': main()
