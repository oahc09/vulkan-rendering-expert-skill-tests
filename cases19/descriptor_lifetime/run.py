"""Build and verify an original CPU-ICD pending-descriptor experiment.
No external-project, hardware, performance or full descriptor-family acceptance.
"""
import argparse, hashlib, json, pathlib, subprocess, uuid

DIAGNOSTICS={
 'bad':'VUID phase=pending-update id=VUID-vkUpdateDescriptorSets-None-03047',
 'pending-reset':'VUID phase=pending-reset id=VUID-vkResetCommandBuffer-commandBuffer-00045',
 'stale-submit':'VUID phase=stale-submit id=VUID-vkQueueSubmit-pCommandBuffers-00070'}
MODES=('good','bad','wrong-output','pending-reset','stale-submit')
def verify_case(mode,returncode,data,diagnostics):
 if mode not in MODES:raise ValueError('unsupported mode')
 wanted=[DIAGNOSTICS[mode]] if mode in DIAGNOSTICS else []
 expected_exit=6 if mode=='wrong-output' else 0
 rejected=-1000011001 if mode in ('pending-reset','stale-submit') else 0
 if returncode!=expected_exit or data['exit_code']!=expected_exit or data['mode']!=mode:
  raise ValueError('unexpected outcome')
 if diagnostics!=wanted or data['errors']!=len(wanted) or data['expected_vuid_count']!=len(wanted):
  raise ValueError('diagnostics outside expected phase or count')
 if data['rejected_call_result']!=rejected:
  raise ValueError('invalid API call was not aborted')
 if data['fence_not_ready'] is not True or data['first']!=42 or data['second']!=99:
  raise ValueError('pending fence/readback failure')

def main():
 p=argparse.ArgumentParser()
 for name in ('include','loader','glslang','spirv-val','layer-manifest','output'):
  p.add_argument('--'+name,required=True,type=pathlib.Path)
 a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=False)
 here=pathlib.Path(__file__).resolve().parent
 def call(args):
  return subprocess.run([str(v) for v in args],capture_output=True,timeout=30,check=True)
 def sha(path):
  return hashlib.sha256(path.read_bytes()).hexdigest()
 shader=a.output/'compute.spv';binary=a.output/'probe'
 build=[
  ['gcc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(a.include),here/'probe.c',a.loader,'-o',binary],
  [a.glslang,'-V','--target-env','vulkan1.2',here/'compute.comp','-o',shader],
  [a.spirv_val,'--target-env','vulkan1.2',shader]]
 for command in build:call(command)
 layer=json.loads(a.layer_manifest.read_text())['layer']
 v=[int(x) for x in layer['api_version'].split('.')]
 spec=(v[0]<<22)|(v[1]<<12)|v[2]
 report=dict(run_id=str(uuid.uuid4()),provenance='original deliberate fault injection; not production discovery',
  sources={name:sha(here/name) for name in ('probe.c','compute.comp','run.py')},
  shader_sha256=sha(shader),binary_sha256=sha(binary),loader_sha256=sha(a.loader),
  layer_manifest_sha256=sha(a.layer_manifest),
  glslang_sha256=sha(a.glslang),spirv_val_sha256=sha(a.spirv_val),
  tools={'gcc':call(['gcc','--version']).stdout.decode().splitlines()[0],
         'glslang':call([a.glslang,'--version']).stdout.decode().strip(),
         'spirv-val':call([a.spirv_val,'--version']).stdout.decode().strip()},
  build_commands=[[str(x) for x in command] for command in build],
  cases={})
 identities=[]
 for mode in ('good','bad','wrong-output','pending-reset','stale-submit'):
  r=subprocess.run([str(binary),mode,str(shader)],capture_output=True,timeout=30)
  (a.output/(mode+'.stdout')).write_bytes(r.stdout)
  (a.output/(mode+'.stderr')).write_bytes(r.stderr)
  data=json.loads(r.stdout)
  lines=r.stderr.decode().splitlines()
  ids=[json.loads(x[9:]) for x in lines if x.startswith('IDENTITY ')]
  if len(ids)!=1:raise ValueError('missing runtime identity')
  identity=ids[0];identities.append(identity)
  if identity['device_type']!=4 or identity['timeline_supported'] is not True or identity['layer_spec']!=spec or identity['layer_impl']!=int(layer['implementation_version']):
   raise ValueError('runtime/manifest/scope disagreement')
  diagnostics=[x for x in lines if x.startswith('VUID ')]
  verify_case(mode,r.returncode,data,diagnostics)
  report['cases'][mode]=dict(result=data,diagnostics=diagnostics,stdout_sha256=hashlib.sha256(r.stdout).hexdigest(),stderr_sha256=hashlib.sha256(r.stderr).hexdigest())
 if any(x!=identities[0] for x in identities):raise ValueError('runtime changed')
 report.update(runtime_identity=identities[0],status='PASS_SCOPED_DESCRIPTOR_LIFETIME_API_REGRESSION',
  limitations=['CPU ICD and one queue only','actual timeline wait, not render-frame latency evidence',
  'ordinary descriptor flags only; update-after-bind/indexing excluded',
  'invalid pending update/reset and stale submit aborted by Validation; driver undefined behavior not exercised',
  'uniform/storage shader with 42 then 99 only; no general shader correctness',
  'wrong-output is an authored oracle negative, not an independently discovered defect',
  'not external-project/Live-model/hardware/SC acceptance'])
 # Raw paths/build provenance remain local. Publish only reviewed scope/result fields.
 (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report['status'])

if __name__=='__main__':main()
