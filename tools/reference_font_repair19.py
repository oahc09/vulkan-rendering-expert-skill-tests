"""Fixed nine-preload repair verification, not a normative or visual correction."""
from html.parser import HTMLParser
from . import prose_denominator19 as p
OLD=b'href="../katex/fonts/'
NEW=b'href="../../katex/fonts/'
REPORT_SHA='5a70d2710c68fe30337944d240a308df66bdc38aa65e19524cc7d3a4f8adc613'
class Fonts(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,t,attrs):
  d=dict(attrs)
  if t=='link' and d.get('rel')=='preload' and d.get('as')=='font' and 'KaTeX_' in d.get('href',''):self.urls.append(d.get('href'))
def patch(raw):
 marker=b'      # Load KaTeX stylesheet, but we no longer run a script to convert math\n'
 p.need(raw.count(marker)==1 and raw.count(OLD)==9,'fixed patch preimage')
 return raw.replace(marker,b"      katexScript.gsub!('../katex/fonts/', katexpath + '/fonts/')\n\n"+marker)
def page(before,after,directory):
 p.need(before.count(OLD)==9 and after==before.replace(OLD,NEW),'only nine registered href replacements allowed')
 doc=Fonts();doc.feed(after.decode('utf-8'));p.need(len(doc.urls)==9 and len(set(doc.urls))==9,'nine unique font preloads')
 files={}
 for url in doc.urls:
  p.need(type(url)is str and url.startswith('../../katex/fonts/KaTeX_') and url.endswith('.woff2') and all(c not in url for c in '?#%\\'),'fixed local font URL')
  name=url.removeprefix('../../katex/fonts/');p.need('/'not in name,'simple font name')
  f=directory.parents[1]/'katex/fonts'/name
  p.need(f.is_file() and not f.is_symlink(),'font asset must be regular')
  p.need(f.resolve().is_relative_to(directory.parents[1].resolve()),'asset stays in output root')
  raw=f.read_bytes();p.need(raw[:4]==b'wOF2','WOFF2 asset signature');files[name]=p.sha(raw)
 return files


def commands(build,runtime):
 from pathlib import Path
 src=Path(build)/'source';rt=Path(runtime);ruby=rt/'usr/bin/ruby3.3';node=Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin/node');adoc=rt/'usr/share/rubygems-integration/all/gems/asciidoctor-2.0.23/bin/asciidoctor'
 nodecode="const r=require('module').createRequire(process.argv[1]);const ids=['escape-string-regexp','he',process.argv[2]];let resolved=ids.map(x=>r.resolve(x));ids.forEach(x=>r(x));console.log(JSON.stringify({resolved,loaded:Object.keys(require.cache)}))"
 return [
 ['ruby-ldd',['/usr/bin/ldd',str(ruby)]],
 ['node-ldd',['/usr/bin/ldd',str(node)]],
 ['node-modules',[str(node),'-e',nodecode,str(src/'scripts/translate_math.js'),str(src/'katex/katex.min.js')]],
 ['python-import',['/usr/bin/python3.13','-S','-B','-c',"import pyparsing,json;print(json.dumps({'path':pyparsing.__file__}))"]],
 ['all-reference-html',['/usr/bin/python3.13','-S','-B','makeSpec','-spec','all','-version','1.4','PYTHON=/usr/bin/python3.13 -S -B','ASCIIDOC='+str(ruby)+' --disable-gems '+str(adoc),'NODEJS='+str(node),'SPECDATE=2026-11-06T01:31:32Z','SPECREMARK=frozen-fa30d4e-source-replay','-j4','manhtmlpages']]]
def verify_commands(steps,build,runtime):
 p.need([[s.get('label'),s.get('argv')]for s in steps]==commands(build,runtime),'fixed original five argv/configuration')
