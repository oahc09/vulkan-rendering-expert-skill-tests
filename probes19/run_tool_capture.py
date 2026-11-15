"""Opt-in actual local tools; no download, device claims or raw-data upload."""
import argparse,hashlib,json,os,pathlib,subprocess,sys,time,uuid
import capture_contract
p=argparse.ArgumentParser();p.add_argument('--probe',required=True);p.add_argument('--trace-processor',required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--layer-manifest',type=pathlib.Path,required=True)
a=p.parse_args();capture_contract.reserve_output(a.output)
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
import evidence19
events=[];cases={}; identities=[];run_id=str(uuid.uuid4())
layer=json.loads(a.layer_manifest.read_text())['layer']
for case in ('bad','good'):
 start=time.monotonic_ns()
 r=subprocess.run([a.probe,case],capture_output=True,timeout=30)
 end=time.monotonic_ns()
 if r.returncode:raise RuntimeError(f'{case} probe failed: {r.returncode}')
 (a.output/f'{case}.json').write_bytes(r.stdout)
 events.append(dict(name='validation_probe_'+case,ph='X',pid=os.getpid(),tid=1,ts=start/1000,dur=(end-start)/1000))
 ids=capture_contract.callbacks(case,r.stdout)
 identities.append(capture_contract.identity(r.stderr,layer))
 cases[case]=dict(exit_code=r.returncode,message_ids=ids,sha256=hashlib.sha256(r.stdout).hexdigest())
if identities[0]!=identities[1]:raise ValueError('device/layer changed between cases')
trace=a.output/'capture.json';trace.write_text(json.dumps(dict(traceEvents=events)))
tool=subprocess.check_output([a.trace_processor,'--version'],text=True).strip()
query=a.output/'query.sql';query.write_text(evidence19.SQL)
r=subprocess.run([a.trace_processor,'-q',str(query),str(trace)],capture_output=True,check=True,timeout=30)
csv=a.output/'slices.csv';csv.write_bytes(r.stdout)
capture_contract.trace(r.stdout,events)
scope=json.dumps(identities[0],sort_keys=True)
records=evidence19.perfetto_csv(r.stdout,run_id,tool,scope)
validation=evidence19.validation((a.output/'bad.json').read_bytes(),run_id,str(layer['implementation_version']),scope)
if len(validation)!=1:raise ValueError('unexpected validation count')
report=dict(source_sha256=hashlib.sha256(pathlib.Path(__file__).with_name('validation_probe.c').read_bytes()).hexdigest(),runner_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),run_id=run_id,runtime_identity=identities[0],binary_sha256=hashlib.sha256(pathlib.Path(a.probe).read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256(a.layer_manifest.read_bytes()).hexdigest(),trace_processor_sha256=hashlib.sha256(pathlib.Path(a.trace_processor).read_bytes()).hexdigest(),status='PASS_LOCAL_TOOL_PIPELINE_ONLY',layer_api=layer['api_version'],layer_implementation=layer['implementation_version'],trace_processor=tool,cases=cases,trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),trace_export_sha256=hashlib.sha256(r.stdout).hexdigest(),parsed_slices=len(records),parsed_validation=len(validation),limitations=['authored minimal buffer probe, not real project','software ICD, not hardware/device acceptance','CPU subprocess timing, not GPU execution time','no capture-event/resource generation join','only size VUID checked; clean good case is not general correctness'])
(a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
