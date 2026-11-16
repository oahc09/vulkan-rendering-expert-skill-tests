import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import reference_dynamic_route19 as r
pytestmark=pytest.mark.candidate19

def test_registered_shape():
 c=r.config();assert len(c['pages'])==26;assert sum(c['counts'].values())==4581
@pytest.mark.parametrize('kind',['body','unknown','local','count'])
def test_byte_gate(kind):
 c={'counts':{'dynamic-state-lifetime':1},'pages':{'A':{'counts':{'dynamic-state-lifetime':1}}}}
 b=b'<a href="#dynamic-state-lifetime">same</a>';a=b.replace(b'href="#',b'href="../../html/vkspec.html#');assert r.check_page('A',b,a,c)['dynamic-state-lifetime']==1
 if kind=='body':a+=b'changed'
 elif kind=='unknown':a=a.replace(b'lifetime',b'other')
 elif kind=='local':b+=b'<a id="dynamic-state-lifetime"></a>';a+=b'<a id="dynamic-state-lifetime"></a>'
 else:c['pages']['A']['counts']['dynamic-state-lifetime']=2
 with pytest.raises(ValueError):r.check_page('A',b,a,c)
def test_unaffected_unchanged():
 c=r.config();b=b'<a href="#other">unchanged</a>';r.check_page('Other',b,b,c)
 with pytest.raises(ValueError):r.check_page('Other',b,b+b'changed',c)

@pytest.mark.parametrize('kind',['source','generated-page','missing-fullspec','missing-anchor','duplicate-anchor'])
def test_actual_preflight_mutations(tmp_path,kind):
 import os,shutil,copy
 value=os.environ.get('VULKAN_DYNAMIC_ROUTE19_SOURCE')
 if not value:pytest.skip('fixed actual source opt-in required')
 root=Path(value);c=r.config();r.preflight(root,c)
 names=set(c['sources'])|{'gen/refpage/'+n+'.adoc'for n in c['pages']}|{'gen/out/html/vkspec.html'}
 for name in names:
  f=tmp_path/name;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,f)
 r.preflight(tmp_path,c)
 if kind=='source':
  f=tmp_path/'chapters/commonvalidity/draw_common.adoc';f.write_bytes(f.read_bytes()+b'changed')
 elif kind=='generated-page':
  f=tmp_path/'gen/refpage/vkCmdDraw.adoc';f.write_bytes(f.read_bytes()+b'changed')
 elif kind=='missing-fullspec':
  (tmp_path/'gen/out/html/vkspec.html').unlink()
 else:
  f=tmp_path/'gen/out/html/vkspec.html';raw=f.read_bytes();needle=b'id="dynamic-state-lifetime"'
  raw=raw.replace(needle,b'id="different-anchor"',1)if kind=='missing-anchor'else raw+b'<a id="dynamic-state-lifetime"></a>'
  f.write_bytes(raw);c=copy.deepcopy(c);c['full_spec_html_sha256']=r.p.sha(raw) # coordinated HOST mutation must still fail unique-target gate
 with pytest.raises((ValueError,FileNotFoundError)):r.preflight(tmp_path,c)
