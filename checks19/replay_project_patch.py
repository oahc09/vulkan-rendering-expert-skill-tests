"""Fixed AST-portability project patch replay. Known repair, not a blind/user repair."""
import argparse,hashlib,json,math,os,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OWN=['checks19/replay_project_patch.py','tools/project_patch_replay19.py','checks19/process_supervisor19.py','coverage/v1.0.19/pair.json']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,s):
 if not x:raise ValueError(s)
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ('project-root','skill-root','docs-root','validusage','output'):ap.add_argument('--'+k,type=Path,required=True)
 for k in ('base','candidate','expected-patch-sha256','expected-tests-head','expected-skill-head'):ap.add_argument('--'+k,required=True)
 ap.add_argument('--allowed-path',action='append',required=True);ap.add_argument('--development',action='store_true');ap.add_argument('--budget-seconds',type=float,default=180);ap.add_argument('--step-seconds',type=float,default=30);ap.add_argument('--cancel-file',type=Path);a=ap.parse_args()
 a.output.mkdir(parents=True,exist_ok=False);a.output=a.output.resolve();report=dict(status='BLOCKED',development=a.development,run_id=str(uuid.uuid4()),steps=[],stages=[],pending=[s+'-'+v for s in ('before','after','rollback') for v in ('312','313')],release_status='BLOCKED');cancel=None
 try:
  need(a.project_root.resolve()==ROOT,'only authorized registered Tests project');need(all(math.isfinite(x) and 0<x<=600 for x in (a.budget_seconds,a.step_seconds)),'finite budgets')
  git_env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_REPLACE_OBJECTS':'1'}
  git=lambda root,*args:subprocess.check_output(['/usr/bin/git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-C',str(root),*args],timeout=30,env=git_env)
  state=lambda:{k:dict(head=git(p,'rev-parse','HEAD').decode().strip(),dirty=git(p,'status','--porcelain').decode()) for k,p in [('tests',ROOT),('skill',a.skill_root)]}
  before=state();need(before['tests']['head']==a.expected_tests_head and before['skill']['head']==a.expected_skill_head,'expected current heads');need(a.development or all(not x['dirty'] for x in before.values()),'strict clean sources')
  sources={p:sha(ROOT/p) for p in OWN}
  if not a.development:
   for p in OWN:need((ROOT/p).read_bytes()==git(ROOT,'show',a.expected_tests_head+':'+p),'implementation commit bytes')
  sys.path.insert(0,str(ROOT));from tools import project_patch_replay19 as r
  from checks19 import process_supervisor19 as sup
  pair=json.loads((ROOT/'coverage/v1.0.19/pair.json').read_text());need(pair['skill_sha']==a.expected_skill_head and pair['release_status']=='BLOCKED','current pair')
  patch=r.patch(ROOT,a.base,a.candidate,a.expected_patch_sha256,a.allowed_path);(a.output/'review.patch').write_bytes(patch)
  need(sha(a.validusage)==r.VU_SHA,'fixed VUID corpus')
  tools={k:dict(path=str(Path(v[0]).resolve()),sha256=sha(v[0])) for k,v in r.PYTHONS.items()};need(all(tools[k]['sha256']==v[1] for k,v in r.PYTHONS.items()),'registered interpreter binaries')
  support_tools={p:sha(p) for p in ('/usr/bin/git','/usr/bin/ldd')};report['support_tools']=support_tools
  report.update(recipe='tests-ast312-313-portability-v1',provenance=before,source_sha256=sources,tool_identity=tools,patch_sha256=r.PATCH_SHA,base=r.BASE,candidate=r.CANDIDATE,allowed_paths=r.ALLOWED,scope='Known historical Tests repair. HOST only, no new user repair or blind solve.')
  exports={};originalfixture=json.loads(r.git(ROOT,'show',r.BASE+':tests/fixtures/contract-registry19.json'))
  cards=sorted({f['skill']['path'] for f in originalfixture['families'].values()});exports['skill']=r.export(a.skill_root,r.SKILL,cards,a.output/'skill')
  exports['docs']=r.export(a.docs_root,r.DOCS,r.DOC_PATHS,a.output/'docs')
  (a.output/'validusage.json').write_bytes(a.validusage.read_bytes());exports['validusage.json']=r.VU_SHA
  # Source closure is fixed code, never paths/commands supplied by a report.
  exports['patch-check']=r.export(ROOT,r.BASE,r.SOURCES,a.output/'patch-check')
  exports['candidate']=r.export(ROOT,r.CANDIDATE,r.SOURCES,a.output/'candidate')
  fixture=json.loads((a.output/'candidate/tests/fixtures/contract-registry19.json').read_text())
  need(sorted(r.diffs(originalfixture,fixture))==r.ast_paths(originalfixture),'patch fixture changes only 44 AST coordinates')
  cancel=sup.Cancellation(a.cancel_file);cancel.install();deadline=time.monotonic()+a.budget_seconds;env={**git_env,'PYTHONDONTWRITEBYTECODE':'1'}
  def checkpoint():
   (a.output/'replay-index.tmp').write_text(json.dumps(report,indent=2)+'\n');(a.output/'replay-index.tmp').replace(a.output/'replay-index.json')
  def run(label,argv,expected=0,cwd=None):
   out=a.output/(label+'.stdout');err=a.output/(label+'.stderr');old=dict(os.environ);oldcwd=Path.cwd();os.environ.clear();os.environ.update(env)
   try:
    if cwd:os.chdir(cwd)
    step=sup.run_step(list(map(str,argv)),out,err,timeout=a.step_seconds,total_deadline=deadline,cancellation=cancel)
   finally:os.chdir(oldcwd);os.environ.clear();os.environ.update(old)
   step.update(label=label,argv=list(map(str,argv)),stdout_sha256=sha(out),stderr_sha256=sha(err));report['steps'].append(step);checkpoint()
   need(type(step['returncode'])is int and step['returncode']==expected and not any(step[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and step['group_cleanup']['group_gone']is True,'controlled step failed '+label)
   need(err.read_bytes()==b'','unexpected stderr '+label);return out
  libraries={}
  for version,v in tools.items():
   out=run('runtime-'+version+'-ldd',['/usr/bin/ldd',v['path']]);libs={}
   for line in out.read_text().splitlines():
    if '=>'in line:
     name,rest=line.split('=>',1);p=Path(rest.strip().split()[0])
     if p.is_absolute() and p.is_file():libs[name.strip()]=dict(path=str(p.resolve()),sha256=sha(p))
   libraries[version]=libs
  report['runtime_libraries']=libraries
  run('apply-exact-patch',['/usr/bin/git','apply','--whitespace=nowarn',a.output/'review.patch'],cwd=a.output/'patch-check')
  patched={p:sha(a.output/'patch-check'/p) for p in r.SOURCES};need(patched==exports['candidate'],'applied base must equal candidate bytes');exports['patch-check']=patched
  report['patch_application']='EXACT_CANDIDATE_BYTES';results={}
  for stage,head in [('before',r.BASE),('after',r.CANDIDATE),('rollback',r.BASE)]:
   directory='patch-check' if stage=='after' else stage
   if stage!='after':exports[directory]=r.export(ROOT,head,r.SOURCES,a.output/directory)
   values={};snap=json.loads((a.output/directory/'tests/fixtures/contract-registry19.json').read_text())
   for version,(python,_) in r.PYTHONS.items():
    for folder,files in exports.items():
     if type(files)is dict:need(r.inventory(a.output/folder)==files,'exact export inventory before worker')
    label=stage+'-'+version;expected_mismatch=stage!='after' and version=='313'
    out=run(label,[python,'-I','-S','-B',ROOT/'tools/project_patch_replay19.py','--fixed-worker',a.output/directory,a.output/'skill',a.output/'docs',a.output/'validusage.json'],42 if expected_mismatch else 0)
    for folder,files in exports.items():
     if type(files)is dict:need(r.inventory(a.output/folder)==files,'exact export inventory after worker')
    need(out.stat().st_size<4_000_000,'worker output budget');v=json.loads(out.read_bytes());result=r.verify_worker(v,snap,expected_mismatch,'3.12.14' if version=='312' else '3.13.5');values[version]=v
    report['stages'].append(dict(stage=stage,source_directory=directory,python=version,result=result,manifest_sha256=r.sha(r.canonical(v['manifest'])),log_sha256=sha(out)));report['pending'].remove(label);checkpoint()
   expected=[] if stage=='after' else r.ast_paths(snap);need(sorted(r.diffs(values['312']['manifest'],values['313']['manifest']))==expected,'cross-version exact manifest relation');results[stage]=values
  for version in r.PYTHONS:need(r.canonical(results['before'][version])==r.canonical(results['rollback'][version]),'fresh baseline repeat')
  need(state()==before and {p:sha(ROOT/p) for p in OWN}==sources,'source state drift')
  need(sha(a.output/'review.patch')==r.PATCH_SHA,'delivered patch drift')
  need(r.patch(ROOT,a.base,a.candidate,a.expected_patch_sha256,a.allowed_path)==patch,'patch drift')
  for directory,files in exports.items():
   if type(files)is dict:need(r.inventory(a.output/directory)==files,'exact exported input drift')
   else:need(sha(a.output/directory)==files,'corpus drift')
  for k,v in tools.items():need(sha(v['path'])==v['sha256'],'interpreter changed')
  need(all(sha(p)==h for p,h in support_tools.items()),'support tools changed')
  need(all(sha(v['path'])==v['sha256'] for libs in libraries.values() for v in libs.values()),'runtime libraries changed')
  for stage in results.values():
   for v in stage.values():need(all(sha(item['path'])==item['sha256'] for item in v['runtime']['stdlib'].values()),'stdlib changed')
  for s in report['steps']:
   for stream in ('stdout','stderr'):need(sha(a.output/(s['label']+'.'+stream))==s[stream+'_sha256'],'log drift')
  (a.output/'REPLAY.md').write_text('# Known AST portability repair replay\n\nThis is a known historical repair, not a new user repair or blind solve.\nAfter executes the patch-applied isolated base tree, byte-equal to the candidate.\nRollback freshly reconstructs the original base; the authorized working tree is never reset.\n\n'+ '\n'.join('- '+s['stage']+' / Python '+s['python']+': '+s['result'] for s in report['stages'])+'\n\nSix stage/interpreter executions repeat the same 125 controls; they are not 750 independent tests.\nOnly this fixed source/tool cohort is established. No general portability, GPU or full release claim.\n')
  report['readable_sha256']=sha(a.output/'REPLAY.md');report['exports']=exports;report['status']='DEVELOPMENT_KNOWN_PATCH_REPLAYED' if a.development else 'KNOWN_PATCH_REPLAYED';report['limitations']=['Only registered historical repair and interpreter cohort','Fresh baseline reconstruction is not rollback of the user working tree','No GPU, production project, blind solve or general Python portability acceptance'];checkpoint()
 except (Exception,KeyboardInterrupt) as e:report['status']='BLOCKED';report['error']=type(e).__name__+': '+str(e)
 finally:
  if cancel:cancel.restore()
  (a.output/'replay-index.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'verified_stage_runs':len(report['stages']),'error':report.get('error')}));return 0 if report['status']!='BLOCKED' else 2
if __name__=='__main__':sys.exit(main())
