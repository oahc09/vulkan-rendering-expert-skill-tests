"""Execute fixed HOST controls and check a bounded caller-declared buffer trace."""
import argparse,hashlib,importlib.util,json,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OWN=['checks19/check_resource_contract_chain.py','tools/contract_registry19.py','tools/resource_contract_chain19.py','tests/fixtures/contract-registry19.json','checks19/process_supervisor19.py','coverage/v1.0.19/pair.json','docs/v1.0.19-original-plan.md']
def require(x,m):
 if not x:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True,timeout=30).strip()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('docs-root','validusage','skill-root','trace','evidence-root','output'):p.add_argument('--'+name,type=Path,required=True)
 for name in ('expected-tests-head','expected-skill-head','expected-trace-sha256'):p.add_argument('--'+name,required=True)
 p.add_argument('--development',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);a.output=a.output.resolve();report=dict(status='BLOCKED',run_id=str(uuid.uuid4()),development=a.development,steps=[])
 try:
  identity=lambda:{k:dict(head=git(r,'rev-parse','HEAD'),dirty=git(r,'status','--porcelain')) for k,r in [('tests',ROOT),('skill',a.skill_root)]}
  before=identity();require(before['tests']['head']==a.expected_tests_head and before['skill']['head']==a.expected_skill_head,'expected revisions');require(a.development or all(not x['dirty'] for x in before.values()),'strict clean repositories');pair=json.loads((ROOT/'coverage/v1.0.19/pair.json').read_text());require(pair['skill_sha']==a.expected_skill_head and pair['release_status']=='BLOCKED','exact pair');require(sha(ROOT/'docs/v1.0.19-original-plan.md')==pair['plan_sha256'],'original plan hash');report['provenance']=before
  own={k:sha(ROOT/k) for k in OWN}
  if not a.development:
   for k in OWN:require((ROOT/k).read_bytes()==subprocess.check_output(['git','-C',str(ROOT),'show',a.expected_tests_head+':'+k]),'uncommitted executable/manifest')
  sys.path.insert(0,str(ROOT));reg=load('chain_registry',ROOT/'tools/contract_registry19.py');snapshot=reg.parse((ROOT/'tests/fixtures/contract-registry19.json').read_bytes());report['subdenominator']=reg.verify(snapshot,ROOT,a.skill_root);normpaths=sorted({x for values in reg.INPUTS.values() for x in values.values()});normhash={x:sha(a.docs_root/x) for x in normpaths};vuhash=sha(a.validusage);report['normative_source_hashes']=normhash;report['validusage_sha256']=vuhash
  require(a.trace.is_file() and not a.trace.is_symlink(),'trace must be regular non-symlink file');require(a.trace.stat().st_size<=262144,'trace input size');trace_bytes=a.trace.read_bytes();require(hashlib.sha256(trace_bytes).hexdigest()==a.expected_trace_sha256,'external trace digest');trace=reg.parse(trace_bytes)
  # A hash proves bytes relative to this input, never the truth of a declaration.
  evidence={};total=0
  for proof in trace['proofs']:
   h=proof['evidence_sha256'];require(type(h)is str and len(h)==64 and all(c in '0123456789abcdef' for c in h),'evidence digest syntax');f=a.evidence_root/(h+'.bin');require(f.is_file() and not f.is_symlink() and f.resolve().is_relative_to(a.evidence_root.resolve()),'evidence path escape');total+=f.stat().st_size;require(total<=16*1024*1024,'evidence budget');require(sha(f)==h,'evidence bytes mismatch');evidence[h]=str(f)
  report['evidence_byte_hashes']=sorted(evidence);report['evidence_authority']='CALLER_DECLARED_OR_UNRESOLVED; byte integrity is not proof of truth'
  sup=load('chain_supervisor',ROOT/'checks19/process_supervisor19.py');cancel=sup.Cancellation();cancel.install();deadline=time.monotonic()+120;reports={}
  try:
   for family,inputs in reg.INPUTS.items():
    out=a.output/family;argv=[sys.executable,str(ROOT/f'checks19/run_{family}_contracts.py'),'--validusage',str(a.validusage),'--out',str(out)]
    for key,relative in inputs.items():argv+=['--'+key,str(a.docs_root/relative)]
    stdout=a.output/(family+'.stdout');stderr=a.output/(family+'.stderr');step=sup.run_step(argv,stdout,stderr,timeout=30,total_deadline=deadline,cancellation=cancel);step.update(label=family,argv=argv,stdout_sha256=sha(stdout),stderr_sha256=sha(stderr));report['steps'].append(step);require(type(step['returncode'])is int and step['returncode']==0 and not any(step[k] for k in ('cancelled','timed_out','budget_exhausted','unexpected_descendants')) and step['group_cleanup']['group_gone']is True,'original control process failed')
    actual=reg.parse((out/'report.json').read_bytes());reg.verify_report(snapshot,family,actual,a.docs_root,a.validusage.read_bytes());reports[family]=dict(report_sha256=sha(out/'report.json'),cases=actual['case_count'])
  finally:cancel.restore()
  report['full_manifest_verification']=reg.verify_rebuilt(snapshot,ROOT,a.skill_root,a.docs_root,a.validusage.read_bytes())
  from tools import resource_contract_chain19 as chain
  report['chain']=chain.check(trace);report['original_controls']=reports;report['control_count']=sum(x['cases'] for x in reports.values());require(report['control_count']==125,'frozen control count')
  report['sources']=own;report['trace_sha256']=a.expected_trace_sha256;report['normative_versions']='368 prose; separate309 VUID coordinates. No inferred equivalence.'
  require(identity()==before and {k:sha(ROOT/k) for k in OWN}==own,'source revision changed');reg.verify(snapshot,ROOT,a.skill_root);require({x:sha(a.docs_root/x) for x in normpaths}==normhash and sha(a.validusage)==vuhash,'normative sources changed');require(sha(a.trace)==a.expected_trace_sha256 and all(sha(Path(path))==h for h,path in evidence.items()),'inputs changed');
  for step in report['steps']:require(sha(a.output/(step['label']+'.stdout'))==step['stdout_sha256'] and sha(a.output/(step['label']+'.stderr'))==step['stderr_sha256'],'control logs changed')
  for family,r in reports.items():require(sha(a.output/family/'report.json')==r['report_sha256'],'report changed')
  report['status']='DEVELOPMENT_HOST_CONTRACT_REVIEW' if a.development else 'HOST_CONTRACT_REVIEW_COMPLETE';report['release_status']='BLOCKED';report['semantic_completion']='NOT_INFERRED'
 except (Exception,KeyboardInterrupt) as e:report['error']=type(e).__name__+': '+str(e)
 finally:(a.output/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'chain_status':report.get('chain',{}).get('status')}));return 0 if report['status']in ('HOST_CONTRACT_REVIEW_COMPLETE','DEVELOPMENT_HOST_CONTRACT_REVIEW') and report['chain']['status']=='CONSISTENT_DECLARED_TRACE' else 2
if __name__=='__main__':sys.exit(main())
