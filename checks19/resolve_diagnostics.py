"""Read-only strict bundle -> pinned normative lookup -> explicitly curated Skill routes."""
import argparse,hashlib,importlib.util,json,pathlib,re,sys,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import diagnostic_spec19 as spec

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def safe_path(base,relative):
    p=pathlib.PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts:raise ValueError('unsafe evidence path')
    full=base.joinpath(*p.parts)
    if not full.resolve().is_relative_to(base.resolve()) or full.is_symlink():raise ValueError('outside/symlink evidence')
    return full

def read_json(path):return spec.parse_json(path.read_bytes())

def verify_bundle(bundle,tests,skill):
    index_path=bundle/'delivery-index.json';index_hash=sha(index_path);index=read_json(index_path)
    if index.get('development') is not False or index.get('status')!='PASS_FIVE_BOUNDED_LOCAL_CHAINS' or index.get('entrypoint_in_declared_head') is not True:raise ValueError('not a strict completed bundle')
    if not re.fullmatch('[0-9a-f]{40}',index.get('tests_head','')) or not re.fullmatch('[0-9a-f]{40}',index.get('skill_head','')):raise ValueError('invalid commit IDs')
    gatepath=tests/'checks19/run_delivery_bundle.py'
    if sha(gatepath)!=index['entrypoint_sha256']:raise ValueError('bundle gate source mismatch')
    committed_gate=subprocess.check_output(['git','-C',str(tests),'show',index['tests_head']+':checks19/run_delivery_bundle.py'],timeout=30)
    if committed_gate!=gatepath.read_bytes():raise ValueError('gate not at paired commit')
    for repo,head in ((tests,index['tests_head']),(skill,index['skill_head'])):
        if subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],timeout=30).decode().strip()!=head:raise ValueError('repository HEAD mismatch before gate import')
    gate_spec=importlib.util.spec_from_file_location('checked_delivery_gate',gatepath);gate=importlib.util.module_from_spec(gate_spec);gate_spec.loader.exec_module(gate)
    manifest=gate.verify_pair(tests,skill,index['tests_head'],index['skill_head'])
    if manifest!=index['source_manifest'] or set(index['chains'])!=set(gate.CHAINS):raise ValueError('source inventory/chain set mismatch')
    reports={}
    for name,entry in index['chains'].items():
        if entry['report']!=name+'/summary.json':raise ValueError('unexpected report path')
        report_path=safe_path(bundle,entry['report']);directory=safe_path(bundle,name)
        if sha(report_path)!=entry['report_sha256']:raise ValueError('report digest changed')
        if gate.inventory(directory)!=entry['artifacts']:raise ValueError('raw chain artifacts changed')
        report=read_json(report_path);gate.verify_report(name,report);gate.bind_report(name,report,manifest,directory)
        if report['run_id']!=entry['run_id'] or report['status']!=entry['status']:raise ValueError('child identity changed')
        if entry['runner_sha256']!=manifest[gate.CHAINS[name][0]]:raise ValueError('child runner changed')
        if report.get('identity',report.get('runtime_identity'))!=entry['runtime_identity']:raise ValueError('runtime identity changed')
        reports[name]=report
    required_steps={'trace-processor-version','validation-probe-build',*gate.CHAINS}
    if len(index['steps'])!=len(required_steps) or {s['label'] for s in index['steps']}!=required_steps:raise ValueError('missing/duplicate execution steps')
    for step in index['steps']:
        if step['returncode']!=0 or step['timed_out'] is not False or step['end_monotonic_ns']<step['start_monotonic_ns']:raise ValueError('unsuccessful recorded step')
        for stream in ('stdout','stderr'):
            if sha(safe_path(bundle,step['label']+'.'+stream))!=step[stream+'_sha256']:raise ValueError('root execution log changed')
    if sha(bundle/'validation-probe')!=index['validation_probe_sha256'] or reports['tool_capture']['binary_sha256']!=index['validation_probe_sha256']:raise ValueError('capture binary changed')
    if sha(index_path)!=index_hash:raise ValueError('bundle index changed during verification')
    return index,reports,index_hash

def observations(bundle,reports):
    out=[]
    for chain,report in reports.items():
        for case,record in report['cases'].items():
            if chain in ('transfer','tool_capture'):
                relative=f'{chain}/{case}.json';raw=safe_path(bundle,relative).read_bytes();callbacks=spec.parse_json(raw)
                ids=[r['pMessageIdName'] for r in callbacks]
                if ids!=record['message_ids']:raise ValueError('raw callback differs from summary')
                # callback JSON is a one-line array; JSON pointer disambiguates each item.
                for i,identifier in enumerate(ids):out.append(dict(chain=chain,case=case,phase=None,logfile=relative,line=1,json_pointer=f'/{i}/pMessageIdName',log_sha256=hashlib.sha256(raw).hexdigest(),diagnostic=identifier))
            else:
                relative=f'{chain}/{case}.stderr';raw=safe_path(bundle,relative).read_bytes();found=[]
                for number,line in enumerate(raw.decode().splitlines(),1):
                    if line.startswith(('VUID ','DIAGNOSTIC ')):
                        match=re.fullmatch(r'(?:VUID|DIAGNOSTIC) phase=(\S+) id=(\S+)',line)
                        if not match:raise ValueError('malformed raw diagnostic')
                        found.append(line);out.append(dict(chain=chain,case=case,phase=match[1],logfile=relative,line=number,log_sha256=hashlib.sha256(raw).hexdigest(),diagnostic=match[2]))
                if found!=record['diagnostics']:raise ValueError('raw diagnostics differ from summary')
    return out

def verify_resolver_sources(tests,head,development=False):
    if tests.resolve()!=ROOT.resolve():raise ValueError('resolver must run from explicitly selected tests checkout')
    records={}
    for relative,path in [('checks19/resolve_diagnostics.py',pathlib.Path(__file__)),('tools/diagnostic_spec19.py',pathlib.Path(spec.__file__))]:
        if path.resolve()!=(tests/relative).resolve():raise ValueError('lookup module outside selected checkout')
        if not development:
            committed=subprocess.check_output(['git','-C',str(tests),'show',head+':'+relative],timeout=30)
            if path.read_bytes()!=committed:raise ValueError('resolver/lookup source not at bundle commit')
        records[relative]=sha(path)
    return records

def main():
    p=argparse.ArgumentParser()
    for arg in ('bundle','tests-root','skill-root','validusage','output'):p.add_argument('--'+arg,type=pathlib.Path,required=True)
    p.add_argument('--development',action='store_true',help='uncommitted lookup development only; never final paired acceptance')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    result={'development':a.development,'status':'BLOCKED','resolver_sha256':sha(__file__),'lookup_tool_sha256':sha(spec.__file__),'scope':'Observed diagnostics -> exact normative entries and curated reading routes only. Not full-domain L1/L2 or external-project acceptance.'};code=1
    try:
        index,reports,index_hash=verify_bundle(a.bundle,a.tests_root,a.skill_root)
        resolver_sources=verify_resolver_sources(a.tests_root,index['tests_head'],a.development);result['resolver_source_manifest']=resolver_sources
        corpus=spec.load_pinned(a.validusage.read_bytes());result.update(bundle_index_sha256=index_hash,bundle_run_id=index['run_id'],tests_head=index['tests_head'],skill_head=index['skill_head'],source_snapshot=corpus['source'],corpus_statistics=corpus['statistics'],source_version_info=corpus['version'])
        obs=observations(a.bundle,reports);resolved=[]
        for event in obs:
            record=index['chains'][event['chain']];lookup=spec.lookup(corpus,event['diagnostic'],record['runtime_identity']['layer_spec'])
            routes=lookup.get('routes',[lookup['route']] if lookup.get('route') else [])
            route_records=[]
            for route in routes:
                relative='references/03_api_manual/'+route;path=safe_path(a.skill_root,relative)
                committed=subprocess.check_output(['git','-C',str(a.skill_root),'show',index['skill_head']+':'+relative],timeout=30)
                if path.read_bytes()!=committed:raise ValueError('knowledge route differs from paired Skill commit')
                route_records.append(dict(path=relative,sha256=sha(path),skill_commit=index['skill_head'],kind='curated reading route, not source-derived normative finding'))
            resolved.append(dict(observation=event,lookup=lookup,knowledge_routes=route_records,chain_report_sha256=record['report_sha256']))
        result['observations']=resolved;result['counts']={k:sum(r['lookup']['status']==k for r in resolved) for k in ('MATCHED_SPEC_ENTRY','TOOL_DIAGNOSTIC','UNKNOWN')}
        result['unique_observed_identifiers']=sorted({r['observation']['diagnostic'] for r in resolved})
        # Full recheck after consumption prevents a moving bundle/source from being blessed.
        _,_,final_hash=verify_bundle(a.bundle,a.tests_root,a.skill_root)
        if final_hash!=index_hash or sha(a.validusage)!=corpus['source']['sha256']:raise ValueError('evidence changed during resolution')
        if verify_resolver_sources(a.tests_root,index['tests_head'],a.development)!=resolver_sources:raise ValueError('lookup sources changed during resolution')
        result['limitations']=['validusage API1.4.309 is not vk.xml API1.4.368; inventories are separate.','Full corpus indexing is coverage of records, not semantic mastery or full L1/L2 acceptance.','Source HTML and conditional prose are retained as inert data; condition applicability is not automatically proven.','SyncVal hazard names are tool diagnostics without invented normative entries.','Different chains are separate experiments, not joined resource/time lifetimes.','Normative lookup success does not prove repair correctness; original bounded chain evidence remains authoritative.']
        result['status']='OBSERVED_DIAGNOSTICS_VERSION_PAIRED' if resolved and not result['counts']['UNKNOWN'] else 'UNKNOWN_DIAGNOSTIC_COVERAGE';code=0 if result['status']=='OBSERVED_DIAGNOSTICS_VERSION_PAIRED' else 2
        if a.development:result['status']='DEVELOPMENT_'+result['status']
    except Exception as e:result['failure']={'type':type(e).__name__,'message':str(e)}
    (a.output/'diagnostic-spec-report.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status']);return code
if __name__=='__main__':sys.exit(main())
