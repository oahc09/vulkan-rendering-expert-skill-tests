"""Three original neighboring Amber regressions, NOT additional historical bugs."""
import uuid
import json,pathlib,subprocess,time
from tools import external_amber95119 as a
CASES={
 'compute_accumulated_ubo_definition.amber':('0de59a7238c5882c7886f6fa3c4969331e9416fb8e1a6e0550d9cfa2f0bc0e61','69: ComputeCommand\n71: ProbeSSBOCommand\n72: ProbeSSBOCommand\n\nSummary: 1 pass, 0 fail\n'),
 'compute_dynamic_buffers.amber':('3b0df06994e72995d70635945a645f6d8ea4f7381f6bdfa34052908cc9115176','59: ComputeCommand\n61: ProbeSSBOCommand\n62: ProbeSSBOCommand\n63: ProbeSSBOCommand\n\nSummary: 1 pass, 0 fail\n'),
 'draw_storagetexelbuffer.amber':('1fc21c505479f60875dd4a2a87143802e52d351934902cc0c5589b6f1eb8086f','51: ComputeCommand\n1: CompareBufferCommand\n\nSummary: 1 pass, 0 fail\n')}
WARN='[WARNING] validation layer (../src/vulkan/runtime/vk_nir.c:58):\nSPIR-V offset 512: SPIR-V WARNING:\n    Image Type operand of OpTypeSampledImage should not have a Dim of Buffer.\n    512 bytes into the SPIR-V binary\n'
OWN=['tools/external_related19.py','checks19/run_external_related.py']
ORDER=[(case,v) for case in CASES for v in ('before','after')]
def verify_result(case,code,stdout,stderr):
 a.require(case in CASES,'unknown regression');a.require(type(code)is int and code==0,'regression process failed')
 a.require(stdout==CASES[case][1],'original oracle transcript mismatch')
 a.require(stderr==(WARN if case=='draw_storagetexelbuffer.amber' else ''),'unexpected regression diagnostics')
def argv(root,case,v):
 return [str(root/f'amber951-{v}-build/amber/amber'),'-D','0','-v','1.2','--log-execute-calls',str(root/f'amber951-{v}-src/tests/cases'/case)]
def verify_inputs(root):
 m=a.verify_artifacts(root)
 for case in CASES:
  for v in ('before','after'):a.require(a.fh(root/f'amber951-{v}-src/tests/cases'/case)==CASES[case][0],'regression source changed')
 return m
def run(root,out,run_id=None):
 run_id=str(uuid.uuid4()) if run_id is None else run_id
 if not isinstance(run_id,str) or str(uuid.UUID(run_id))!=run_id:raise ValueError('canonical run UUID required')
 root=pathlib.Path(root).resolve();out=pathlib.Path(out);a.require(not out.exists() and not out.is_symlink(),'fresh output required');m=verify_inputs(root)
 own={x:a.fh(a.ROOT/x) for x in OWN};env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C',**m['environment']};out.mkdir(parents=True)
 report={'schema':1,'run_id':run_id,'output_root':str(out.resolve()),'status':'BLOCKED','release_status':'BLOCKED','scope':'Three unchanged original neighboring Amber regressions, no new bugs or repairs. Software Vulkan, not hardware/full CTS.','environment':env,'provenance':a.provenance_state(),'steps':[],'implementation_sha256':own,'manifest_sha256':a.MANIFEST,'source_commits':{'before':a.BEFORE,'after':a.AFTER}}
 try:
  for i,(case,v) in enumerate(ORDER):
   cmd=argv(root,case,v);step={'case':case,'variant':v,'argv':cmd,'source_sha256':CASES[case][0],'binary_sha256':a.fh(cmd[0]),'started':time.monotonic()};stdout=stderr=None
   try:
    p=subprocess.run(cmd,env=env,capture_output=True,timeout=30);stdout,stderr=p.stdout,p.stderr;step.update(returncode=p.returncode,timed_out=False)
   except subprocess.TimeoutExpired as e:
    stdout,stderr=e.stdout or b'',e.stderr or b'';step.update(returncode=None,timed_out=True);raise
   finally:
    step['ended']=time.monotonic()
    if stdout is not None:
     (out/f'{i}.stdout').write_bytes(stdout);(out/f'{i}.stderr').write_bytes(stderr);step.update(stdout_sha256=a.sha(stdout),stderr_sha256=a.sha(stderr))
    report['steps'].append(step)
   verify_result(case,p.returncode,stdout.decode(),stderr.decode())
  verify_inputs(root);a.require(own=={x:a.fh(a.ROOT/x) for x in OWN},'implementation changed');report['status']='RELATED_ORIGINAL_REGRESSIONS_PASSED'
 finally:
  report['artifacts']={p.name:a.fh(p) for p in out.iterdir() if p.is_file() and p.name!='report.json'};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 return report
