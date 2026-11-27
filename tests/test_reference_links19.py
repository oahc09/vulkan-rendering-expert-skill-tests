import sys,os,json,subprocess,shutil
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import reference_links19 as h
pytestmark=pytest.mark.candidate19

def fixture(tmp_path):
 root=tmp_path/'out';(root/'man/html').mkdir(parents=True);(root/'html').mkdir();(root/'html/vkspec.html').write_text('<html><a id="only-in-spec"></a></html>');(root/'style.css').write_text('body{}');(root/'man/html/A.html').write_text('<html><a id="own"></a><a href="B.html#present">B</a><a href="#own">own</a><a href="Alias.html#present">alias</a><link href="../../style.css"><a href="https://example.invalid/never-fetch">external</a></html>');(root/'man/html/B.html').write_text('<a id="present"></a>');(root/'man/html/Alias.html').symlink_to('B.html');aliases={'man/html/Alias.html':'B.html'}
 result=h.audit(root,['man/html/A.html'],aliases);assert result['counts']=={'LOCAL_RESOLVED':4,'EXTERNAL_NOT_FETCHED':1};return root,aliases

@pytest.mark.parametrize('kind',['page','fragment','alias'])
def test_host_mutations(tmp_path,kind):
 root,aliases=fixture(tmp_path)
 if kind=='page':(root/'man/html/B.html').unlink();expected='MISSING_LOCAL_TARGET'
 elif kind=='fragment':(root/'man/html/B.html').write_text('<a id="wrong"></a>');expected='MISSING_FRAGMENT'
 else:(root/'man/html/Alias.html').unlink();(root/'man/html/Alias.html').symlink_to('../../../../outside');expected='UNREGISTERED_OR_WRONG_ALIAS'
 assert h.audit(root,['man/html/A.html'],aliases)['counts'][expected]>0

@pytest.mark.parametrize('url,status',[('../../../escape','OUTSIDE_FIXED_OUTPUT_ROOT'),('%2e%2e/%2e%2e/%2e%2e/escape','OUTSIDE_FIXED_OUTPUT_ROOT'),('file:///etc/passwd','UNSUPPORTED_SCHEME_NOT_EXECUTED'),('javascript:alert(1)','UNSUPPORTED_SCHEME_NOT_EXECUTED'),('/etc/passwd','ROOT_ABSOLUTE_WITHOUT_ORIGIN'),('bad%xx','MALFORMED_OR_AMBIGUOUS_URL'),('a\\b','MALFORMED_OR_AMBIGUOUS_URL'),('//example.invalid/a','EXTERNAL_NOT_FETCHED')])
def test_url_boundary(url,status):assert h.address('man/html/A.html',url)['status']==status

def test_base_and_percent_fragment(tmp_path):
 root,aliases=fixture(tmp_path);(root/'man/html/B.html').write_text('<a id="a b"></a>');f=root/'man/html/A.html';f.write_text('<a href="B.html#a%20b">x</a>');assert h.audit(root,['man/html/A.html'],aliases)['counts']=={'LOCAL_RESOLVED':1}
 f.write_text('<base href="https://example.invalid/"><a href="B.html#a%20b">x</a>');assert h.audit(root,['man/html/A.html'],aliases)['counts']=={'BASE_CONTEXT_NOT_EVALUATED':1}

def test_fullspec_candidate_not_resolution(tmp_path):
 root,aliases=fixture(tmp_path);(root/'man/html/A.html').write_text('<a href="#only-in-spec">x</a>');r=h.audit(root,['man/html/A.html'],aliases);assert r['status']=='PARTIAL_WITH_FINDINGS' and r['rows'][0]['same_fragment_in_full_spec'] is True

def test_entry_wrong_anchor(tmp_path):
 root=tmp_path/'build';root.mkdir();(root/'report.json').write_text('{}');out=tmp_path/'out';args=[sys.executable,str(ROOT/'checks19/audit_reference_links19.py'),'--build-root',str(root),'--expected-report-sha','0'*64,'--source-root',str(tmp_path/'not-read'),'--output',str(out)];r=subprocess.run(args,capture_output=True,timeout=10);assert r.returncode==2;assert 'expected original build report digest' in json.loads((out/'report.json').read_bytes())['error']

def test_actual_page_delete_optin(tmp_path):
 base=os.environ.get('VULKAN_REFERENCE_LINKS19_SOURCE')
 if not base:pytest.skip('actual rendered source not supplied')
 source=Path(base)/'gen/out';root=tmp_path/'out';(root/'man/html').mkdir(parents=True);(root/'html').mkdir();shutil.copyfile(source/'html/vkspec.html',root/'html/vkspec.html')
 for name in ('VkMemoryDedicatedRequirements','VkStructureType'):shutil.copyfile(source/'man/html'/(name+'.html'),root/'man/html'/(name+'.html'))
 page='man/html/VkMemoryDedicatedRequirements.html';result=h.audit(root,[page],{});rows=[r for r in result['rows'] if r['href']=='VkStructureType.html'];assert rows and all(r['status']=='LOCAL_RESOLVED' for r in rows)
 (root/'man/html/VkStructureType.html').unlink();result=h.audit(root,[page],{});assert all(r['status']=='MISSING_LOCAL_TARGET' for r in result['rows'] if r['href']=='VkStructureType.html')
