#!/usr/bin/env python3
import argparse,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import prose_generation19 as g
from checks19.process_supervisor19 import Cancellation,run_step
p=g.p
def main():
 a=argparse.ArgumentParser();a.add_argument('--docs-git',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--cancel-file',type=Path);a=a.parse_args()
 a.output.mkdir(parents=True,exist_ok=False);a.output=a.output.resolve();report={'status':'BLOCKED','closure_status':'BLOCKED','steps':[],'config':{'spec':'core','version':'1.4','extensions':[],'target':'generated'},'limits':['No Asciidoctor/Ruby HTML/Reference/validusage execution.','Include existence is not conditional expansion; missing files are not proved active.','Two independent runs compare output bytes; not two semantic tests.']}
 owned=[Path(__file__).resolve(),ROOT/'tools/prose_generation19.py',ROOT/'tools/prose_denominator19.py',ROOT/'checks19/process_supervisor19.py'];own={str(x.relative_to(ROOT)):p.sha(x.read_bytes()) for x in owned};report['implementation_sha256']=own
 report['tests_head']=p.git(ROOT,'rev-parse','HEAD').decode().strip()
 oldenv=dict(os.environ);oldcwd=Path.cwd();cancel=Cancellation(a.cancel_file);cancel.install();deadline=time.monotonic()+180
 try:
  files=p.load(a.docs_git);source={x:p.sha(f['raw']) for x,f in files.items()};report['source_sha256']=source
  os.environ.clear();os.environ.update({'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C','PYTHONDONTWRITEBYTECODE':'1','PYTHONHASHSEED':'0','HOME':str(a.output)})
  report['tools']={x:p.sha(Path(x).read_bytes()) for x in ('/usr/bin/python3.13','/usr/bin/make','/usr/bin/git','/bin/sh')}
  # Use only copied .py package sources, never distro pyc or arbitrary site packages.
  package=Path('/usr/lib/python3/dist-packages/pyparsing');depfiles={f.relative_to(package).as_posix():p.sha(f.read_bytes()) for f in sorted(package.rglob('*.py'))}
  p.need(depfiles and '__init__.py' in depfiles,'existing pyparsing sources required')
  isolated=a.output/'dependency-sources'/'pyparsing'
  for name,h in depfiles.items():
   dest=isolated/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((package/name).read_bytes());p.need(p.sha(dest.read_bytes())==h,'dependency copy')
  os.environ['PYTHONPATH']=str(isolated.parent)
  report['pyparsing']={'original_package':str(package),'executed_source_copy':str(isolated),'files':depfiles,'site_imports':'DISABLED_WITH_MINUS_S'}
  probe_argv=['/usr/bin/python3.13','-S','-B','-c','import pyparsing,json; print(json.dumps({"version":pyparsing.__version__,"path":pyparsing.__file__}))']
  probe=run_step(probe_argv,a.output/'dependency.stdout',a.output/'dependency.stderr',timeout=10,total_deadline=deadline,cancellation=cancel);probe['argv']=probe_argv;probe['label']='dependency';report['steps'].append(probe)
  p.need(probe['returncode']==0 and not any(probe[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and probe['group_cleanup']['group_gone'],'dependency probe failed')
  observed=json.loads((a.output/'dependency.stdout').read_bytes());p.need(Path(observed['path']).resolve()==isolated/'__init__.py','actual dependency mismatch');report['pyparsing']['observation']=observed
  results=[]
  for label in ('first','second'):
   cancel.check(deadline);root=a.output/label;root.mkdir()
   for name,f in files.items():
    target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(f['raw']);target.chmod(0o755 if f['mode']=='100755' else 0o644)
   argv=['/usr/bin/python3.13','-S','-B','makeSpec','-spec','core','-version','1.4','-v','PYTHON=/usr/bin/python3.13 -S -B','-j1','SPECDATE=2026-11-06T01:31:32Z','SPECREMARK=frozen-fa30d4e-source-replay','generated']
   os.chdir(root);step=run_step(argv,a.output/(label+'.stdout'),a.output/(label+'.stderr'),timeout=75,total_deadline=deadline,cancellation=cancel);step['argv']=argv;step['label']=label;report['steps'].append(step)
   p.need(step['returncode']==0 and not any(step[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and step['group_cleanup']['group_gone'],'official generator failed')
   for name,digest in source.items():p.need(p.sha((root/name).read_bytes())==digest,'exported source changed')
   results.append(g.validate(root/'gen'))
  report['comparison']=g.compare(*results);report['generated']=results[0];report['include_observations']=g.include_observations(files,results[0])
  p.need({x:p.sha(f['raw']) for x,f in p.load(a.docs_git).items()}==source,'fixed source changed')
  for tool,h in report['tools'].items():p.need(p.sha(Path(tool).read_bytes())==h,'tool changed')
  p.need({f.relative_to(package).as_posix():p.sha(f.read_bytes()) for f in sorted(package.rglob('*.py'))}==depfiles and g.inventory(isolated)==depfiles,'pyparsing changed')
  for label in ('first','second'):
   p.need(g.validate(a.output/label/'gen')==results[0],'generated output changed')
   export=a.output/label;actual={k:v for k,v in g.inventory(export).items() if not k.startswith('gen/')}
   p.need(actual==source,'export inventory changed')
   for name,f in files.items():p.need((export/name).stat().st_mode&0o777==(0o755 if f['mode']=='100755' else 0o644),'source mode changed')
  p.need({str(x.relative_to(ROOT)):p.sha(x.read_bytes()) for x in owned}==own,'implementation changed')
  p.need(p.git(ROOT,'rev-parse','HEAD').decode().strip()==report['tests_head'],'tests head changed')
  report['logs']={f.name:p.sha(f.read_bytes()) for f in a.output.iterdir() if f.suffix in ('.stdout','.stderr')};report['status']='OFFICIAL_CORE14_GENERATED_REPRODUCED_NOT_EXPANDED'
 except Exception as e:report['error']=type(e).__name__+': '+str(e)
 finally:
  os.chdir(oldcwd);os.environ.clear();os.environ.update(oldenv);cancel.restore();(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'closure_status':'BLOCKED','steps':len(report['steps'])}));return 0 if report['status']=='OFFICIAL_CORE14_GENERATED_REPRODUCED_NOT_EXPANDED' else 2
if __name__=='__main__':raise SystemExit(main())
