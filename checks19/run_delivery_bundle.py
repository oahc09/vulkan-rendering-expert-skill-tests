"""Fixed five-chain actual local delivery run. Never final external/hardware acceptance."""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import uuid

ROOT=pathlib.Path(__file__).resolve().parents[1]
CHAINS={
 'transfer':('cases19/transfer/run.py','PASS_SCOPED_REAL_API_REGRESSION',{'before','after','mutant'}),
 'descriptor_lifetime':('cases19/descriptor_lifetime/run.py','PASS_SCOPED_DESCRIPTOR_LIFETIME_API_REGRESSION',{'good','bad','wrong-output','pending-reset','stale-submit'}),
 'pipeline_interface':('cases19/pipeline_interface/run.py','BOUNDED_PIPELINE_INTERFACE_REPAIR_PASS',{'bad-type','good','missing-binding','wrong-output'}),
 'image_compute':('cases19/image_compute/run.py','INTEGRATED_IMAGE_UPLOAD_COMPUTE_READBACK_REPAIR_PASS',{'missing-upload-dependency','good','bad-layout','missing-readback-dependency','wrong-output'}),
 'tool_capture':('probes19/run_tool_capture.py','PASS_LOCAL_TOOL_PIPELINE_ONLY',{'bad','good'})}
SCOPES=['cases19/transfer','cases19/descriptor_lifetime','cases19/pipeline_interface','cases19/image_compute','probes19','tools/pipeline_interface19.py','tools/evidence19.py','coverage/v1.0.19/pair.json','docs/v1.0.19-original-plan.md']

def digest(data):return hashlib.sha256(data).hexdigest()
def sha(path):return digest(pathlib.Path(path).read_bytes())
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],timeout=30)

def verify_pair(root,skill,tests_head,skill_head):
    if len(tests_head)!=40 or len(skill_head)!=40:raise ValueError('full expected commit IDs required')
    if git(root,'rev-parse','HEAD').decode().strip()!=tests_head or git(skill,'rev-parse','HEAD').decode().strip()!=skill_head:raise ValueError('HEAD does not match explicit pair')
    if git(skill,'status','--porcelain','--untracked-files=no'):raise ValueError('Skill tracked working tree dirty')
    pair=json.loads((root/'coverage/v1.0.19/pair.json').read_text())
    if pair['skill_sha']!=skill_head or pair['plan_sha256']!=sha(root/'docs/v1.0.19-original-plan.md') or pair['release_status']!='BLOCKED':raise ValueError('pair/plan/candidate status mismatch')
    if 'version: 1.0.19' not in (skill/'SKILL.md').read_text():raise ValueError('unexpected skill version')
    files=git(root,'ls-files','-z','--',*SCOPES).decode().split('\0');manifest={}
    for relative in filter(None,files):
        path=root/relative
        if path.is_symlink() or not path.is_file():raise ValueError('missing/symlink source')
        data=path.read_bytes()
        if data!=git(root,'show',tests_head+':'+relative):raise ValueError('source differs from declared HEAD: '+relative)
        manifest[relative]=digest(data)
    untracked=git(root,'ls-files','--others','--exclude-standard','-z','--',*SCOPES).decode().split('\0')
    if any(p and '__pycache__/' not in p for p in untracked):raise ValueError('untracked chain input')
    if any(v[0] not in manifest for v in CHAINS.values()):raise ValueError('runner missing from source inventory')
    return manifest

def verify_report(name,report):
    if report.get('status')!=CHAINS[name][1] or set(report.get('cases',{}))!=CHAINS[name][2] or not isinstance(report.get('run_id'),str):raise ValueError('invalid chain summary')
    uuid.UUID(report['run_id'])
    c=report['cases']
    if not report.get('limitations'):raise ValueError('missing bounded limitations')
    identity=report.get('identity',report.get('runtime_identity'))
    if not isinstance(identity,dict) or identity.get('device_type')!=4:raise ValueError('not CPU scope')
    if name=='transfer':
        if c['after']['exit']!=0 or c['after']['matching_words']!=64 or c['after']['errors'] or c['after']['message_ids']:raise ValueError('transfer repair failed')
        for key,code in [('before',0),('mutant',6)]:
            if c[key]['exit']!=code or c[key]['message_ids']!=['SYNC-HAZARD-READ-AFTER-WRITE'] or c[key]['errors']!=len(c[key]['message_ids']):raise ValueError('transfer negative failed')
    elif name=='descriptor_lifetime':
        for key,case in c.items():
            r=case['result']
            if r['first']!=42 or r['second']!=99 or r['fence_not_ready'] is not True or r['exit_code']!=(6 if key=='wrong-output' else 0):raise ValueError('lifetime readback failure')
            expected={'bad':'VUID phase=pending-update id=VUID-vkUpdateDescriptorSets-None-03047','pending-reset':'VUID phase=pending-reset id=VUID-vkResetCommandBuffer-commandBuffer-00045','stale-submit':'VUID phase=stale-submit id=VUID-vkQueueSubmit-pCommandBuffers-00070'}
            wanted=[expected[key]] if key in expected else []
            if case['diagnostics']!=wanted or r['errors']!=len(wanted) or r['expected_vuid_count']!=len(wanted) or r['rejected_call_result']!=(-1000011001 if key in ('pending-reset','stale-submit') else 0):raise ValueError('missing/wrong lifetime negative')
    elif name=='pipeline_interface':
        for key,case in c.items():
            r=case['result'];positive=key in ('good','wrong-output')
            if r['output']!=(42 if positive else 0) or r['errors']!=(0 if positive else 1) or r['exit_code']!=(6 if key=='wrong-output' else 0):raise ValueError('pipeline repair/oracle failed')
            wanted=[] if positive else ['VUID phase=pipeline-create id=VUID-VkComputePipelineCreateInfo-layout-'+('07990' if key=='bad-type' else '07988')]
            if case['diagnostics']!=wanted or r['pipeline_result']!=(0 if positive else -1000011001):raise ValueError('wrong pipeline diagnostic')
            if case['admission']['status']!=('WITHIN_CHECKED_INTERFACE' if positive else 'REJECTED_INTERFACE'):raise ValueError('pipeline admission mismatch')
    elif name=='image_compute':
        for key,case in c.items():
            r=case['result'];positive=key in ('good','wrong-output')
            if r['pixels']!=([(i*11+5)*3+7 for i in range(16)] if positive else [0]*16) or r['submitted']!=positive or r['exit_code']!=(6 if key=='wrong-output' else 0):raise ValueError('image pixel/negative failure')
            expected={'missing-upload-dependency':['DIAGNOSTIC phase=compute-dispatch id=SYNC-HAZARD-READ-AFTER-WRITE'],'missing-readback-dependency':['DIAGNOSTIC phase=readback id=SYNC-HAZARD-READ-AFTER-WRITE'],'bad-layout':['DIAGNOSTIC phase=compute-dispatch id=VUID-VkDescriptorImageInfo-imageLayout-00344','DIAGNOSTIC phase=compute-dispatch id=VUID-vkCmdDispatch-None-08114']}
            if case['diagnostics']!=expected.get(key,[]) or r['errors']!=len(case['diagnostics']):raise ValueError('image wrong diagnostic')
        off=report['heuristic_off_observation']
        if off['status']!='HAZARD_NOT_DETECTED_NOT_PASS' or off['result']['exit_code']!=5 or off['result']['errors']!=0 or off['result']['submitted'] is not False:raise ValueError('heuristic limitation lost')
    else:
        if report['parsed_slices']!=2 or report['parsed_validation']!=1 or c['bad']['message_ids']!=['VUID-VkBufferCreateInfo-size-00912'] or c['good']['message_ids']:raise ValueError('actual tool parsing incomplete')
    return identity

def inventory(directory):
    result={}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():raise ValueError('output symlink forbidden')
        if path.is_file():result[str(path.relative_to(directory))]={'sha256':sha(path),'bytes':path.stat().st_size}
    if 'summary.json' not in result:raise ValueError('missing actual summary')
    return result

def bind_report(name,report,source_manifest,output):
    def eq(value,path):
        if value!=source_manifest[path]:raise ValueError('source binding failed: '+path)
    runner=CHAINS[name][0];folder=str(pathlib.PurePosixPath(runner).parent)
    if name=='transfer':
        eq(report['cases']['before']['source_sha256'],folder+'/baseline.c');eq(report['patch_sha256'],folder+'/fix.patch')
        for case in ('before','after','mutant'):
            if report['cases'][case]['binary_sha256']!=sha(output/'work'/case):raise ValueError('transfer binary binding')
    elif name=='descriptor_lifetime':
        for path,value in report['sources'].items():eq(value,folder+'/'+path)
        if report['binary_sha256']!=sha(output/'probe') or report['shader_sha256']!=sha(output/'compute.spv'):raise ValueError('lifetime artifact binding')
    elif name in ('pipeline_interface','image_compute'):
        eq(report['runner_sha256'],runner);eq(report['repair']['baseline_sha256'],folder+'/baseline.c');eq(report['repair']['patch_sha256'],folder+'/fix.patch');eq(report['shader']['source_sha256'],folder+'/compute.comp')
        if report['shader']['spirv_sha256']!=sha(output/'compute.spv') or report['shader']['disassembly_sha256']!=sha(output/'compute.spvasm'):raise ValueError('shader artifact binding')
        for kind in ('baseline','fixed'):
            if report['repair'][kind+'_binary_sha256']!=sha(output/(kind+'-probe')):raise ValueError('pipeline/image binary binding')
    else:
        eq(report['runner_sha256'],runner);eq(report['source_sha256'],'probes19/validation_probe.c')
        if report['trace_sha256']!=sha(output/'capture.json') or report['trace_export_sha256']!=sha(output/'slices.csv'):raise ValueError('trace source/export binding')

    def logs(record,label):
        for stream in ('stdout','stderr'):
            if record[stream+'_sha256']!=sha(output/(label+'.'+stream)):raise ValueError('log binding mismatch: '+label+'.'+stream)
    if name=='transfer':
        for key,case in report['cases'].items():
            if case['callback_sha256']!=sha(output/(key+'.json')):raise ValueError('transfer callback binding')
    elif name=='descriptor_lifetime':
        for key,case in report['cases'].items():logs(case,key)
    elif name in ('pipeline_interface','image_compute'):
        for key,case in report['cases'].items():logs(case['log'],key)
        for field,label in [('compile','shader.compile'),('validate','shader.validate'),('disassemble','shader.dis')]:logs(report['shader'][field],label)
        for field,label in [('log','patch'),('baseline_build','baseline.build'),('fixed_build','fixed.build')]:logs(report['repair'][field],label)
        for key,tool in report['tools'].items():logs(tool['log'],key+'.version')
        if name=='image_compute':logs(report['heuristic_off_observation']['log'],'heuristic-off')
    else:
        for key,case in report['cases'].items():
            if case['sha256']!=sha(output/(key+'.json')):raise ValueError('capture callback binding')

def verify_snapshot(directory,expected):
    if inventory(directory)!=expected:raise ValueError('chain artifacts changed after validation')

def verify_hash_refs(value,known):
    if isinstance(value,dict):
        for k,v in value.items():
            if k.endswith('sha256') and isinstance(v,str) and v not in known:raise ValueError('reported hash has no actual current input/output: '+k)
            verify_hash_refs(v,known)
    elif isinstance(value,list):
        for v in value:verify_hash_refs(v,known)

def main():
    p=argparse.ArgumentParser()
    for key in ('tools','include','loader','trace-processor','skill-root','output'):p.add_argument('--'+key,type=pathlib.Path,required=True)
    p.add_argument('--development',action='store_true',help='explicit local working-tree entrypoint; never final commit evidence')
    p.add_argument('--expected-tests-head',required=True);p.add_argument('--expected-skill-head',required=True)
    a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
    index={'development':a.development,'schema_version':1,'run_id':str(uuid.uuid4()),'status':'BLOCKED','tests_head':a.expected_tests_head,'skill_head':a.expected_skill_head,'entrypoint_sha256':sha(__file__),'chains':{},'scope':'Fixed five independent local tool chains; no cross-chain resource/timeline join; not final acceptance.'}
    code=1
    try:
        sources=verify_pair(ROOT,a.skill_root,a.expected_tests_head,a.expected_skill_head);index['source_manifest']=sources
        layer_dir=pathlib.Path(os.environ['VK_LAYER_PATH']);layer=layer_dir/'VkLayer_khronos_validation.json'
        required=[a.loader,a.trace_processor,layer,pathlib.Path(os.environ['VK_DRIVER_FILES']),a.include/'vulkan/vulkan.h',*(a.tools/name for name in ('glslangValidator','spirv-val','spirv-dis'))]
        if any(not f.is_file() for f in required):raise ValueError('required tool/header/manifest missing')
        if any(not os.access(f,os.X_OK) for f in [a.trace_processor,*(a.tools/name for name in ('glslangValidator','spirv-val','spirv-dis'))]):raise ValueError('tool not executable')
        if a.trace_processor.read_bytes()[:4]!=b'\x7fELF':raise ValueError('trace processor must be local ELF binary, not download wrapper')
        tool_hashes={str(i):sha(f) for i,f in enumerate(required)};index['input_tool_hashes']=dict(zip(['loader','trace_processor','layer_manifest','icd_manifest','vulkan_header','glslang','spirv_val','spirv_dis'],tool_hashes.values()))
        index['entrypoint_in_declared_head']=git(ROOT,'ls-tree',a.expected_tests_head,'--','checks19/run_delivery_bundle.py').strip()!=b''
        if not a.development:
            if not index['entrypoint_in_declared_head'] or pathlib.Path(__file__).read_bytes()!=git(ROOT,'show',a.expected_tests_head+':checks19/run_delivery_bundle.py'):raise ValueError('final entrypoint not committed at expected HEAD')
        index['steps']=[]
        def execute(label,command,timeout=240):
            args=list(map(str,command));step={'label':label,'argv':args,'timeout_seconds':timeout,'start_monotonic_ns':time.monotonic_ns()};index['steps'].append(step)
            try:
                r=subprocess.run(args,capture_output=True,timeout=timeout);stdout=r.stdout;stderr=r.stderr;step['returncode']=r.returncode;step['timed_out']=False
            except subprocess.TimeoutExpired as e:
                stdout=e.stdout or b'';stderr=e.stderr or b'';step['returncode']=None;step['timed_out']=True
            except OSError as e:
                stdout=b'';stderr=str(e).encode();step['returncode']=None;step['timed_out']=False;step['launch_error']=type(e).__name__
            step['end_monotonic_ns']=time.monotonic_ns()
            for stream,data in [('stdout',stdout),('stderr',stderr)]:
                (a.output/(label+'.'+stream)).write_bytes(data);step[stream+'_sha256']=digest(data)
            if step['timed_out'] or step['returncode']!=0:raise RuntimeError(label+' failed: '+str(step['returncode']))
        execute('trace-processor-version',[a.trace_processor,'--version'],timeout=30)
        index['trace_processor_version']=(a.output/'trace-processor-version.stdout').read_text().strip()
        if not index['trace_processor_version'].startswith('Perfetto '):raise ValueError('unexpected trace processor version')
        probe=a.output/'validation-probe'
        execute('validation-probe-build',['gcc','-Wall','-Wextra','-Werror','-I'+str(a.include),ROOT/'probes19/validation_probe.c',a.loader,'-o',probe])
        index['validation_probe_sha256']=sha(probe)
        run_ids=set()
        for name,(runner,_,_) in CHAINS.items():
            out=a.output/name;command=[sys.executable,'-O',ROOT/runner]
            if name=='tool_capture':command+=['--probe',probe,'--trace-processor',a.trace_processor,'--layer-manifest',layer]
            else:
                command+=['--include',a.include,'--loader',a.loader]
                if name=='descriptor_lifetime':command+=['--glslang',a.tools/'glslangValidator','--spirv-val',a.tools/'spirv-val','--layer-manifest',layer]
                elif name!='transfer':command+=['--tools',a.tools]
            command+=['--output',out];execute(name,command)
            report=json.loads((out/'summary.json').read_text());identity=verify_report(name,report);bind_report(name,report,sources,out)
            if name=='tool_capture' and report['binary_sha256']!=sha(probe):raise ValueError('capture binary mismatch')
            if report['run_id'] in run_ids:raise ValueError('reused child run ID')
            run_ids.add(report['run_id'])
            files=inventory(out)
            known=set(sources.values())|set(tool_hashes.values())|{sha(probe)}|{item['sha256'] for item in files.values()}
            verify_hash_refs(report,known)
            index['chains'][name]={'status':report['status'],'run_id':report['run_id'],'report':name+'/summary.json','report_sha256':sha(out/'summary.json'),'artifacts':inventory(out),'limitations':report['limitations'],'runtime_identity':identity,'runner_sha256':sources[runner]}
        for name,record in index['chains'].items():
            verify_snapshot(a.output/name,record['artifacts'])
        if verify_pair(ROOT,a.skill_root,a.expected_tests_head,a.expected_skill_head)!=sources:raise ValueError('sources changed during delivery')
        if {str(i):sha(f) for i,f in enumerate(required)}!=tool_hashes:raise ValueError('tools changed during delivery')
        if sha(__file__)!=index['entrypoint_sha256']:raise ValueError('entrypoint changed during delivery')
        for step in index['steps']:
            for stream in ('stdout','stderr'):
                if sha(a.output/(step['label']+'.'+stream))!=step[stream+'_sha256']:raise ValueError('root execution log changed')
        if set(index['chains'])!=set(CHAINS):raise ValueError('incomplete delivery')
        index['status']='PASS_FIVE_BOUNDED_LOCAL_CHAINS';code=0
        index['limitations']=['Independent processes and resource lifetimes: no cross-chain causal/resource-ID/time correlation.','CPU ICD/coherent memory only; noncoherent remains unrun.','Perfetto slices measure CPU subprocess duration, not GPU timing.','Image SyncVal shader-access heuristic limitation preserved in child report.','Not external project, mobile/hardware, Live model, SC or overall v1.0.19 acceptance.','Uncommitted entrypoint, if flagged, is identified by hash, not misattributed to declared HEAD.']
    except (Exception,) as e:
        index['failure']={'type':type(e).__name__,'message':str(e)}
    (a.output/'delivery-index.json').write_text(json.dumps(index,indent=2)+'\n')
    print(index['status']);return code
if __name__=='__main__':sys.exit(main())
