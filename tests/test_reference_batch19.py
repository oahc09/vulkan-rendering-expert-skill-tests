import sys,os,json,subprocess
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import reference_batch19 as h
pytestmark=pytest.mark.candidate19

def baseline(tmp_path):
 d=tmp_path/'html';d.mkdir();raw='<html><head><title>VkThing(3)</title></head><body><h2 id="_name">Name</h2><div class="sectionbody"><p>VkThing - A registered thing</p></div>'+('valid text '*150)+'</body></html>'
 (d/'VkThing.html').write_text(raw);(d/'VkThingKHR.html').symlink_to('VkThing.html');m={'entities':{'VkThing':'a'*64},'aliases':{'VkThingKHR':'VkThing'},'content_contracts':{'VkThing':{'name_html':'VkThing - A registered thing','required_sections':['Name']}}}
 assert h.inspect_output(d,m)['alias_count']==1;return d,m

@pytest.mark.parametrize('kind',['missing','regular_alias','wrong_target','absolute_alias','extra','wrong_title','truncated','entity_link','body'])
def test_output_mutation(tmp_path,kind):
 d,m=baseline(tmp_path);f=d/'VkThing.html';alias=d/'VkThingKHR.html'
 if kind=='body':f.write_text('<html><head><title>VkThing(3)</title></head><body>'+('padding '*200)+'</body></html>')
 elif kind=='missing':f.unlink()
 elif kind=='regular_alias':alias.unlink();alias.write_text(f.read_text())
 elif kind=='wrong_target':alias.unlink();alias.symlink_to('elsewhere.html')
 elif kind=='absolute_alias':alias.unlink();alias.symlink_to(f)
 elif kind=='extra':(d/'extra.html').write_text('PASS')
 elif kind=='wrong_title':f.write_text(f.read_text().replace('VkThing(3)','Other(3)'))
 elif kind=='truncated':f.write_text(f.read_text().replace('</html>',''))
 elif kind=='entity_link':raw=f.read_bytes();f.unlink();outside=tmp_path/'outside';outside.write_bytes(raw);f.symlink_to(outside)
 with pytest.raises(ValueError):h.inspect_output(d,m)

def test_wrong_source(tmp_path):
 with pytest.raises(ValueError):h.source(tmp_path)

def test_precancel_and_output_reuse(tmp_path):
 cancel=tmp_path/'cancel';cancel.touch();out=tmp_path/'out';args=[sys.executable,str(ROOT/'checks19/render_reference_batch19.py'),'--source-root',str(tmp_path/'absent'),'--runtime-root',str(tmp_path/'absent2'),'--output',str(out),'--cancel-file',str(cancel)]
 r=subprocess.run(args,capture_output=True,timeout=10);assert r.returncode==2;raw=(out/'report.json').read_bytes();report=json.loads(raw);assert report['status']=='BLOCKED' and report['steps']==[]
 assert subprocess.run(args,capture_output=True,timeout=10).returncode!=0;assert (out/'report.json').read_bytes()==raw

def test_actual_expected_optin():
 root=os.environ.get('VULKAN_REFERENCE_BATCH19_SOURCE')
 if not root:pytest.skip('fixed source cohort not supplied')
 matrix=h.expected(Path(root));assert (len(matrix['entities']),len(matrix['aliases']),len(matrix['excluded_metadata']))==(3553,477,10)

def test_actual_complete_optin():
 root=os.environ.get('VULKAN_REFERENCE_BATCH19_RUN')
 if not root:pytest.skip('actual complete reference batch not supplied')
 root=Path(root);matrix=h.expected(root/'source');result=h.inspect_output(root/'source/gen/out/man/html',matrix);assert (result['entity_count'],result['alias_count'])==(3553,477)

def test_actual_body_removed_optin(tmp_path):
 import re
 name=os.environ.get('VULKAN_REFERENCE_BATCH19_RUN')
 if not name:pytest.skip('actual complete reference batch not supplied')
 root=Path(name);matrix=h.expected(root/'source');entity='VkMemoryDedicatedRequirements';small={'entities':{entity:matrix['entities'][entity]},'aliases':{},'content_contracts':{entity:matrix['content_contracts'][entity]}}
 raw=(root/'source/gen/out/man/html'/(entity+'.html')).read_bytes();target=tmp_path/(entity+'.html');target.write_bytes(raw);assert h.inspect_output(tmp_path,small)['entity_count']==1
 changed=re.sub(rb'(<body[^>]*>).*?(</body>)',lambda m:m.group(1)+b'HOST CONTROL BODY REMOVED '+b' '*len(raw)+m.group(2),raw,flags=re.S);assert changed!=raw;target.write_bytes(changed)
 with pytest.raises(ValueError,match='Name body'):h.inspect_output(tmp_path,small)


def test_actual_c_spec_removed_optin(tmp_path):
 import re
 name=os.environ.get('VULKAN_REFERENCE_BATCH19_RUN')
 if not name:pytest.skip('actual complete reference batch not supplied')
 root=Path(name);matrix=h.expected(root/'source');entity='VkMemoryDedicatedRequirements';small={'entities':{entity:matrix['entities'][entity]},'aliases':{},'content_contracts':{entity:matrix['content_contracts'][entity]}}
 raw=(root/'source/gen/out/man/html'/(entity+'.html')).read_bytes();target=tmp_path/(entity+'.html');target.write_bytes(raw);assert h.inspect_output(tmp_path,small)['c_specification_entity_identifiers_checked']==1
 changed=re.sub(rb'(<h2 id="_c_specification">.*?</h2>).*?(?=<h2)',lambda m:m.group(1)+b'<div class="sectionbody"> </div>',raw,flags=re.S);assert changed!=raw;target.write_bytes(changed)
 with pytest.raises(ValueError,match='C Specification'):h.inspect_output(tmp_path,small)

def test_offline_entry_rejects_wrong_anchor_before_source(tmp_path):
 build=tmp_path/'build';build.mkdir();(build/'report.json').write_text('{}');out=tmp_path/'out';args=[sys.executable,str(ROOT/'checks19/verify_reference_batch19.py'),'--build-output',str(build),'--expected-report-sha','0'*64,'--source-root',str(tmp_path/'not-read'),'--output',str(out)]
 r=subprocess.run(args,capture_output=True,timeout=10);assert r.returncode==2;report=json.loads((out/'report.json').read_bytes());assert report['status']=='BLOCKED' and 'trusted expected' in report['error']
