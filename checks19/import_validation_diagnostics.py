"""Import local callback JSON without running the user's program or opening URLs."""
import argparse,hashlib,os,stat,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OWN=['checks19/import_validation_diagnostics.py','tools/import_validation19.py','tools/diagnostic_spec19.py','coverage/v1.0.19/pair.json']
def need(x,msg):
 if not x:raise ValueError(msg)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read_regular(path,limit):
 # O_NONBLOCK prevents a substituted FIFO from blocking between inspection/open.
 fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
 try:
  s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_size<=limit,'regular-file budget')
  parts=[];size=0
  while True:
   b=os.read(fd,min(65536,limit+1-size))
   if not b:break
   parts.append(b);size+=len(b);need(size<=limit,'file bytes budget')
  return b''.join(parts)
 finally:os.close(fd)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],timeout=30).decode().strip()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('callbacks','metadata','validusage','skill-root','output'):p.add_argument('--'+k,type=Path,required=True)
 for k in ('expected-callback-sha256','expected-metadata-sha256','expected-tests-head','expected-skill-head'):p.add_argument('--'+k,required=True)
 p.add_argument('--development',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);report=dict(status='BLOCKED',development=a.development);phase='SOURCE_PREFLIGHT';code=2
 try:
  before={k:dict(head=git(r,'rev-parse','HEAD'),dirty=git(r,'status','--porcelain')) for k,r in [('tests',ROOT),('skill',a.skill_root)]}
  need(before['tests']['head']==a.expected_tests_head and before['skill']['head']==a.expected_skill_head,'expected heads')
  need(a.development or all(not r['dirty'] for r in before.values()),'strict clean sources')
  sources={f:digest(read_regular(ROOT/f,2_000_000)) for f in OWN}
  if not a.development:
   for f in OWN:need(read_regular(ROOT/f,2_000_000)==subprocess.check_output(['git','-C',str(ROOT),'show',a.expected_tests_head+':'+f],timeout=30),'committed source bytes')
  sys.path.insert(0,str(ROOT));from tools import import_validation19 as adapter,diagnostic_spec19 as spec
  pair=adapter.parse(read_regular(ROOT/'coverage/v1.0.19/pair.json',100000));need(pair['skill_sha']==a.expected_skill_head and pair['release_status']=='BLOCKED','paired skill')
  phase='INPUT_INTEGRITY';raw=read_regular(a.callbacks,adapter.MAX_BYTES);meta=read_regular(a.metadata,65536)
  need(digest(raw)==a.expected_callback_sha256 and digest(meta)==a.expected_metadata_sha256,'external input digest')
  phase='CALLBACK_METADATA_SCHEMA';adapter.callbacks(raw);adapter.metadata(meta)
  phase='FIXED_SPEC_SOURCE';vu=read_regular(a.validusage,32_000_000);corpus=spec.load_pinned(vu)
  report=adapter.analyze(raw,meta,corpus);report.update(development=a.development,implementation_sha256=sources,tests_head=a.expected_tests_head,skill_head=a.expected_skill_head,source_state={k:dict(head=v['head'],dirty=bool(v['dirty'])) for k,v in before.items()},release_status='BLOCKED')
  phase='CURATED_ROUTE_SOURCE';routes={}
  for o in report['observations']:
   relative=o['triage'].get('knowledge_path')
   if relative:
    path=a.skill_root/relative;data=read_regular(path,2_000_000)
    need(data==subprocess.check_output(['git','-C',str(a.skill_root),'show',a.expected_skill_head+':'+relative],timeout=30),'route committed bytes')
    routes[relative]=dict(sha256=digest(data),skill_head=a.expected_skill_head,meaning='curated reading route, not a normative or causal finding')
  report['knowledge_sources']=routes
  phase='FINAL_RECHECK'
  need(digest(read_regular(a.callbacks,adapter.MAX_BYTES))==digest(raw) and digest(read_regular(a.metadata,65536))==digest(meta),'input changed')
  need(digest(read_regular(a.validusage,32_000_000))==corpus['source']['sha256'],'spec changed')
  need({f:digest(read_regular(ROOT/f,2_000_000)) for f in OWN}==sources,'implementation changed')
  need({k:dict(head=git(r,'rev-parse','HEAD'),dirty=git(r,'status','--porcelain')) for k,r in [('tests',ROOT),('skill',a.skill_root)]}==before,'source state changed')
  need(all(digest(read_regular(a.skill_root/f,2_000_000))==v['sha256'] for f,v in routes.items()),'route changed')
  report['status']='DEVELOPMENT_IMPORTED_READ_ONLY_TRIAGE' if a.development else 'IMPORTED_READ_ONLY_TRIAGE'
  report['interpretation']='Import completed; lookup is conditional on declared tool metadata. No confirmed root cause, runtime validation or repair.'
  rendered=adapter.render(report);(a.output/'TRIAGE.md').write_text(rendered);report['triage_sha256']=digest(rendered.encode());code=0
 except (Exception,KeyboardInterrupt):
  # No exception text, user paths, raw callback or metadata values are disclosed.
  report=dict(status='BLOCKED',development=a.development,error_phase=phase,error='Input or source verification failed; no diagnosis established.')
 finally:(a.output/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'status':report['status'],'counts':report.get('counts',{}),'error_phase':report.get('error_phase')}));return code
if __name__=='__main__':sys.exit(main())
