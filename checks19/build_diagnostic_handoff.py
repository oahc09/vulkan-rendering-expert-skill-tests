"""Build/verify a bounded bilingual reading handoff; never execute package content."""
import argparse,hashlib,importlib.util,json,pathlib,re,subprocess,sys,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def parse(raw):
    def unique(pairs):
        out={}
        for key,value in pairs:
            if key in out:raise ValueError('duplicate JSON key')
            out[key]=value
        return out
    return json.loads(raw,object_pairs_hook=unique)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],timeout=30)
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def checked_dependencies(tests,head,development=False,verify_only=False):
    if tests.resolve()!=ROOT.resolve() or not re.fullmatch('[0-9a-f]{40}',head):raise ValueError('selected checkout/commit mismatch')
    if git(tests,'rev-parse','HEAD').decode().strip()!=head:raise ValueError('HEAD differs from required commit')
    own=['checks19/build_diagnostic_handoff.py','tools/diagnostic_handoff19.py']
    paths=own if verify_only else own+['checks19/resolve_diagnostics.py','tools/diagnostic_spec19.py','checks19/run_delivery_bundle.py','checks19/process_supervisor19.py']
    hashes={}
    for relative in paths:
        path=tests/relative
        if path.is_symlink() or not path.is_file():raise ValueError('missing/symlink dependency')
        if not (development and relative in own):
            if path.read_bytes()!=git(tests,'show',head+':'+relative):raise ValueError('dependency not at required commit: '+relative)
        hashes[relative]=sha(path)
    # Only now import verified local dependencies, never a path selected by bundle text.
    helper=load_module('diagnostic_handoff19_checked',tests/'tools/diagnostic_handoff19.py')
    resolver=None if verify_only else load_module('resolve_diagnostics_checked',tests/'checks19/resolve_diagnostics.py')
    return helper,resolver,hashes

def verify_normative(resolver,bundle,tests,skill,validusage,supplied):
    index,reports,index_hash=resolver.verify_bundle(bundle,tests,skill)
    uuid.UUID(index['run_id'])
    sources=resolver.verify_resolver_sources(tests,index['tests_head'])
    corpus=resolver.spec.load_pinned(validusage.read_bytes())
    rebuilt=[]
    for event in resolver.observations(bundle,reports):
        entry=index['chains'][event['chain']];lookup=resolver.spec.lookup(corpus,event['diagnostic'],entry['runtime_identity']['layer_spec'])
        route_records=[]
        for route in lookup.get('routes',[lookup['route']] if lookup.get('route') else []):
            relative='references/03_api_manual/'+route;path=resolver.safe_path(skill,relative)
            if path.read_bytes()!=git(skill,'show',index['skill_head']+':'+relative):raise ValueError('route not at paired commit')
            route_records.append(dict(path=relative,sha256=sha(path),skill_commit=index['skill_head'],kind='curated reading route, not source-derived normative finding'))
        rebuilt.append(dict(observation=event,lookup=lookup,knowledge_routes=route_records,chain_report_sha256=entry['report_sha256']))
    counts={key:sum(row['lookup']['status']==key for row in rebuilt) for key in ('MATCHED_SPEC_ENTRY','TOOL_DIAGNOSTIC','UNKNOWN')}
    expected={'development':False,'status':'OBSERVED_DIAGNOSTICS_VERSION_PAIRED','resolver_sha256':sources['checks19/resolve_diagnostics.py'],'lookup_tool_sha256':sources['tools/diagnostic_spec19.py'],'resolver_source_manifest':sources,'bundle_index_sha256':index_hash,'bundle_run_id':index['run_id'],'tests_head':index['tests_head'],'skill_head':index['skill_head'],'source_snapshot':corpus['source'],'source_version_info':corpus['version'],'corpus_statistics':corpus['statistics'],'observations':rebuilt,'counts':counts,'unique_observed_identifiers':sorted({row['observation']['diagnostic'] for row in rebuilt})}
    if not rebuilt or counts['UNKNOWN']:raise ValueError('incomplete normative resolution')
    for key,value in expected.items():
        if supplied.get(key)!=value:raise ValueError('normative report differs from recomputed evidence: '+key)
    return index,reports,expected

def build(a):
    a.output.mkdir(parents=True,exist_ok=False);receipt={'status':'BLOCKED','development':a.development}
    try:
        raw_index=parse((a.bundle/'delivery-index.json').read_bytes());head=raw_index['tests_head']
        helper,resolver,code_hashes=checked_dependencies(a.tests_root,head,a.development)
        norm_hash=sha(a.normative_report);supplied=parse(a.normative_report.read_bytes())
        index,reports,norm=verify_normative(resolver,a.bundle,a.tests_root,a.skill_root,a.validusage,supplied)
        package=a.output/'.handoff-staging';package.mkdir();files={}
        for relative in helper.source_allowlist():
            source=helper.safe_file(a.tests_root,relative);data=source.read_bytes()
            if hashlib.sha256(data).hexdigest()!=index['source_manifest'][relative]:raise ValueError('source changed during copy')
            helper.add_artifact(package,'sources/'+relative,data,files,{'kind':'paired repository source','path':relative,'commit':head})
        for relative in helper.raw_allowlist(reports):
            source=helper.safe_file(a.bundle,relative);data=source.read_bytes();chain,path=relative.split('/',1)
            if hashlib.sha256(data).hexdigest()!=index['chains'][chain]['artifacts'][path]['sha256']:raise ValueError('log changed during copy')
            helper.add_artifact(package,'evidence/'+relative,data,files,{'kind':'actual bundle raw evidence','path':relative,'bundle_run_id':index['run_id']})
        # Export only recomputed normative fields, never arbitrary supplied report fields.
        helper.add_artifact(package,'normative-observations.json',(json.dumps(norm,indent=2)+'\n').encode(),files,{'kind':'recomputed exact observed normative mapping','original_report_sha256':norm_hash})
        for language in ('zh','en'):
            helper.add_artifact(package,'TRIAGE.'+language+'.md',helper.triage(index,reports,norm,language).encode(),files,{'kind':'fixed bilingual presentation of verified bounded evidence'})
        readme='''# Reading package only

Read TRIAGE.zh.md or TRIAGE.en.md. No executable binaries, private environment
variables, absolute workspace paths or full registry snapshot are included.
Sources/patches and selected raw logs are inert reading material, not a standalone
runnable project. The complete original bundle remains required for execution and
provenance re-verification. No supplied file is executed by the package verifier.

Use the trusted repository command with the manifest digest emitted separately:

    python checks19/build_diagnostic_handoff.py verify --package handoff --expected-manifest-sha256 DIGEST

Manifest hashes are integrity checks, not signatures. Someone able to replace the
package AND the independently trusted digest can replace all content. This check
does not rerun Vulkan, validate root causes or close any final acceptance gate.
'''
        helper.add_artifact(package,'README.md',readme.encode(),files,{'kind':'package verification and scope instructions'})
        # Re-read the strict source/log/pair chain after materializing package bytes.
        _,_,again=verify_normative(resolver,a.bundle,a.tests_root,a.skill_root,a.validusage,parse(a.normative_report.read_bytes()))
        if again!=norm or sha(a.normative_report)!=norm_hash:raise ValueError('input evidence changed during handoff')
        _,_,after=checked_dependencies(a.tests_root,head,a.development)
        if after!=code_hashes:raise ValueError('handoff code changed during generation')
        manifest={'schema_version':1,'status':'DEVELOPMENT_READING_PACKAGE' if a.development else 'VERIFIED_READING_PACKAGE','development':a.development,'tests_head':head,'skill_head':index['skill_head'],'bundle_run_id':index['run_id'],'bundle_index_sha256':norm['bundle_index_sha256'],'normative_report_sha256':norm_hash,'handoff_source_manifest':code_hashes,'files':files,'scope':'Portable reading subset, not complete executable evidence; no cross-chain causal claim or final acceptance.','integrity_limit':'Not a signature: independently trusted manifest digest is required; hashes do not prove semantic correctness.'}
        manifest_path=package/'handoff-manifest.json';manifest_path.write_text(json.dumps(manifest,indent=2)+'\n');manifest_hash=sha(manifest_path)
        verification=helper.verify_package(package,manifest_hash,parse)
        package.rename(a.output/'handoff')
        receipt.update(status=manifest['status'],manifest_sha256=manifest_hash,files=len(files),verification=verification)
        code=0
    except Exception as error:
        staged=a.output/'.handoff-staging'/'handoff-manifest.json'
        if staged.is_file():
            failed=parse(staged.read_bytes());failed['status']='BLOCKED';staged.write_text(json.dumps(failed,indent=2)+'\n')
        receipt['failure']={'type':type(error).__name__,'message':str(error)};code=1
    (a.output/'handoff-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));return code

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build')
    for arg in ('bundle','normative-report','tests-root','skill-root','validusage','output'):b.add_argument('--'+arg,type=pathlib.Path,required=True)
    b.add_argument('--development',action='store_true')
    v=sub.add_parser('verify');v.add_argument('--package',type=pathlib.Path,required=True);v.add_argument('--expected-manifest-sha256',required=True);v.add_argument('--development',action='store_true')
    a=p.parse_args()
    if a.command=='build':return build(a)
    try:
        head=git(ROOT,'rev-parse','HEAD').decode().strip();helper,_,_=checked_dependencies(ROOT,head,a.development,verify_only=True)
        print(json.dumps(helper.verify_package(a.package,a.expected_manifest_sha256,parse)));return 0
    except Exception as error:print(json.dumps({'status':'BLOCKED','failure':str(error)}));return 1
if __name__=='__main__':sys.exit(main())
