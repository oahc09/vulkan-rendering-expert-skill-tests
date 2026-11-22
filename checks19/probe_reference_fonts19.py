#!/usr/bin/env python3
"""Fixed isolated upstream preload patch experiment, not a normative source update."""
import argparse,json,os,shutil,sys,time
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import reference_batch19 as h
from tools import asciidoc_execution19 as a
from checks19.process_supervisor19 import Cancellation,run_step
p=h.p
class Fonts(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,t,attrs):
  d=dict(attrs)
  if t=='link' and d.get('rel')=='preload' and d.get('as')=='font' and 'KaTeX_' in d.get('href',''):self.urls.append(d['href'])
def inspect(file,expect):
 parser=Fonts();parser.feed(file.read_text());p.need(len(parser.urls)==9 and len(set(parser.urls))==9,'nine unique KaTeX preloads')
 for href in parser.urls:
  p.need(href.startswith(expect+'/fonts/') and href.endswith('.woff2') and '?' not in href and '#' not in href,'exact fixed font href')
 return {'html_sha256':p.sha(file.read_bytes()),'hrefs':parser.urls,'existing':[str((file.parent/u).resolve()) for u in parser.urls if (file.parent/u).is_file()]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=Path,required=True);ap.add_argument('--runtime-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 for n in ('source_root','runtime_root','output'):setattr(args,n,a.execution_path(getattr(args,n)))
 out=args.output;out.mkdir(parents=True,exist_ok=False);report={'status':'BLOCKED','authority':'ISOLATED_PATCH_EXPERIMENT_NOT_UPSTREAM_SNAPSHOT_CHANGE','steps':[]};envold=dict(os.environ);cwd=Path.cwd();cancel=Cancellation(None);cancel.install();deadline=time.monotonic()+600
 try:
  inv=h.source(args.source_root);runtime=a.runtime(args.runtime_root);own=p.sha(Path(__file__).read_bytes());report['implementation_sha256']=own;report['tests_head']=p.git(ROOT,'rev-parse','HEAD').decode().strip();src=out/'source';shutil.copytree(args.source_root,src,symlinks=True)
  rt=args.runtime_root;gem=rt/'usr/share/rubygems-integration/all/gems';ruby=rt/'usr/bin/ruby3.3';node=Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin/node');adoc=gem/'asciidoctor-2.0.23/bin/asciidoctor';libs=out/'ruby-libs';libs.mkdir();(libs/'libruby-3.3.so.3.3').symlink_to(rt/'usr/lib/x86_64-linux-gnu/libruby-3.3.so.3.3')
  os.environ.clear();os.environ.update({'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':str(out),'LD_LIBRARY_PATH':str(libs),'RUBYLIB':':'.join(map(str,[rt/'usr/lib/ruby/3.3.0',rt/'usr/lib/x86_64-linux-gnu/ruby/3.3.0',gem/'asciidoctor-2.0.23/lib',gem/'rouge-4.5.1/lib'])),'NODE_PATH':str(rt/'usr/share/nodejs'),'PYTHONPATH':'/usr/lib/python3/dist-packages','PYTHONDONTWRITEBYTECODE':'1'})
  file=src/'config/katex_replace/extension.rb';original=file.read_bytes();marker=b"      # Load KaTeX stylesheet, but we no longer run a script to convert math\n";p.need(original.count(marker)==1 and original.count(b'href="../katex/fonts/')==9,'fixed upstream patch preimage')
  modified=original.replace(marker,b"      katexScript.gsub!('../katex/fonts/', katexpath + '/fonts/')\n\n"+marker)
  (out/'patch-preimage.rb').write_bytes(original);(out/'patch-postimage.rb').write_bytes(modified)
  report['tool_hashes']={str(f):p.sha(f.read_bytes()) for f in (ruby,node,Path('/usr/bin/python3.13'),Path('/usr/bin/make'),Path('/bin/sh'))}
  report['python_dependency']=a.tree(Path('/usr/lib/python3/dist-packages/pyparsing'))
  report['patch']={'file':'config/katex_replace/extension.rb','before_sha256':p.sha(original),'after_sha256':p.sha(modified),'added_line':"katexScript.gsub!('../katex/fonts/', katexpath + '/fonts/')"}
  ref=src/'gen/out/man/html/VkMemoryDedicatedRequirements.html';spec=src/'gen/out/html/vkspec.html';original_ref=ref.read_bytes();original_spec=spec.read_bytes();(out/'baseline-reference.html').write_bytes(original_ref);(out/'baseline-specification.html').write_bytes(original_spec);report['baseline']={'reference':inspect(ref,'../katex'),'specification':inspect(spec,'../katex')};p.need(not report['baseline']['reference']['existing'] and len(report['baseline']['specification']['existing'])==9,'baseline path depth mismatch not reproduced')
  file.write_bytes(modified);os.chdir(src)
  def run(label,target):
   argv=['/usr/bin/python3.13','-S','-B','makeSpec','-spec','all','-version','1.4','PYTHON=/usr/bin/python3.13 -S -B','ASCIIDOC='+str(ruby)+' --disable-gems '+str(adoc),'NODEJS='+str(node),'SPECDATE=2026-11-06T01:31:32Z','SPECREMARK=frozen-fa30d4e-source-replay','-j1',str(target)]
   r=run_step(argv,out/(label+'.stdout'),out/(label+'.stderr'),timeout=300,total_deadline=deadline,cancellation=cancel);r.update(label=label,argv=argv);report['steps'].append(r);p.need(r['returncode']==0 and not any(r[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and r['group_cleanup']['group_gone'],'official patch probe command failed');p.need((out/(label+'.stderr')).read_bytes()==b'','unreviewed render diagnostics')
  ref.unlink();run('patched-reference',ref);report['patched_reference']=inspect(ref,'../../katex');(out/'patched-reference.html').write_bytes(ref.read_bytes());p.need(len(report['patched_reference']['existing'])==9,'patched fonts absent');p.need(ref.read_bytes()==original_ref.replace(b'href="../katex/fonts/',b'href="../../katex/fonts/'),'patch changed more than nine reference preloads')
  spec.unlink();run('patched-specification','html');report['patched_specification']=inspect(spec,'../katex');(out/'patched-specification.html').write_bytes(spec.read_bytes());p.need(spec.read_bytes()==original_spec and len(report['patched_specification']['existing'])==9,'existing specification route regressed')
  file.write_bytes(original);ref.unlink();run('reverted-reference',ref);p.need(ref.read_bytes()==original_ref,'reversion did not reproduce original bytes');report['reverted_reference']=inspect(ref,'../katex');(out/'reverted-reference.html').write_bytes(ref.read_bytes());p.need(not report['reverted_reference']['existing'],'reversion failed to reproduce missing fonts')
  p.need(a.tree(src)==inv,'isolated experiment did not restore exact original tree');p.need(h.source(args.source_root)==inv and a.runtime(rt)==runtime,'readonly input changed');p.need(all(p.sha(Path(f).read_bytes())==v for f,v in report['tool_hashes'].items()),'tool changed');p.need(a.tree(Path('/usr/lib/python3/dist-packages/pyparsing'))==report['python_dependency'],'Python dependency changed');p.need(p.sha(Path(__file__).read_bytes())==own,'implementation changed');report['artifacts']={f.name:p.sha(f.read_bytes()) for f in out.iterdir() if f.is_file()};report['status']='SCOPED_PRELOAD_FIX_AND_REVERSION_VERIFIED';report['limits']=['one reference page and existing all-spec depth only, not all3553 rerendered','static path/file existence, not browser network/font appearance','original all-reference broken-link audit remains unchanged','no normative prose or fragments repaired']
 except Exception as e:report['error']=type(e).__name__+': '+str(e)
 finally:
  os.chdir(cwd);os.environ.clear();os.environ.update(envold);cancel.restore();(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report['status']);return 0 if report['status']=='SCOPED_PRELOAD_FIX_AND_REVERSION_VERIFIED' else 2
if __name__=='__main__':raise SystemExit(main())
