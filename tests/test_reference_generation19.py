import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import reference_generation19 as h
pytestmark=pytest.mark.candidate19

def fixture():
 vid='VUID-vkBindBufferMemory-memory-01035'
 obj={'version info':dict(h.VERSION),'validation':{'vkBindBufferMemory':{'core':[{'vuid':vid,'text':'Memory must satisfy requirements','page':'chapters/resources.html'}]}}}
 return obj, "xrefMap = {"+repr(vid)+": ['resources','']}\n", "pageMap = {'resources':'chapters/resources.adoc'}\n",'<html><a id="'+vid+'"></a></html>'

def check(values):
 a,b,c,d=values;return h.inspect_vu(json.dumps(a).encode(),b.encode(),c.encode(),d.encode())

def test_positive():assert check(fixture())['vuid_count']==1

@pytest.mark.parametrize('kind',['empty','missing','version','null','owner','bucket','text','page','extra','duplicate','map','anchor'])
def test_mutation(kind):
 values=list(fixture());assert check(values)['vuid_count']==1
 obj=values[0];v=obj['validation']['vkBindBufferMemory']['core'][0]
 if kind=='empty':obj.clear()
 elif kind=='missing':obj.pop('validation')
 elif kind=='version':obj['version info']['schema version']=True
 elif kind=='null':obj['validation']=None
 elif kind=='owner':obj['validation']={'../private':{}}
 elif kind=='bucket':obj['validation']['vkBindBufferMemory']['extension']=[]
 elif kind=='text':v['text']=' '
 elif kind=='page':v['page']='../../private.html'
 elif kind=='extra':v['status']='PASS'
 elif kind=='duplicate':obj['validation']['vkBindBufferMemory']['core'].append(copy.deepcopy(v))
 elif kind=='map':values[2]="pageMap={'unrelated':'chapters/resources.adoc'}"
 elif kind=='anchor':values[3]='<html>fake success</html>'
 with pytest.raises(ValueError):check(values)

def test_map_no_execution_or_duplicate():
 for raw in (b"xrefMap={'a':1,'a':2}",b"import os\nxrefMap={'a':1}",b"xrefMap=__import__('os')"):
  with pytest.raises(ValueError):h.literal_map(raw,'xrefMap')

def test_real_optin():
 import os
 path=os.environ.get('VULKAN_REFERENCE19_ROOT')
 if not path:pytest.skip('actual fixed all generated output not provided')
 r=Path(path);result=h.inspect_vu((r/'gen/out/validation/validusage.json').read_bytes(),(r/'gen/xrefMap.py').read_bytes(),(r/'gen/pageMap.py').read_bytes(),(r/'gen/out/html/vkspec.html').read_bytes())
 assert (result['owners'],result['vuid_count'])==(2251,27464)

@pytest.fixture(scope='module')
def actual_matrix():
 import os
 path=os.environ.get('VULKAN_REFERENCE19_ROOT')
 if not path:pytest.skip('actual fixed all generated output not provided')
 r=Path(path);result=h.inspect_vu((r/'gen/out/validation/validusage.json').read_bytes(),(r/'gen/xrefMap.py').read_bytes(),(r/'gen/pageMap.py').read_bytes(),(r/'gen/out/html/vkspec.html').read_bytes());h.fixed_cohort(result);return result

@pytest.mark.parametrize('kind',['owner','text','drop','page','order','status'])
def test_coordinated_matrix_mutation(actual_matrix,kind):
 r=copy.deepcopy(actual_matrix)
 if kind=='owner':r['rows'][0]['owner']='VkOtherOwner'
 elif kind=='text':r['rows'][0]['text_sha256']='0'*64
 elif kind=='drop':r['rows'].pop();r['vuid_count']-=1
 elif kind=='page':r['rows'][0]['page']='chapters/private.html'
 elif kind=='order':r['rows'][0],r['rows'][1]=r['rows'][1],r['rows'][0]
 elif kind=='status':r={'status':'PASS','rows_sha256':h.ROWS_SHA,'owners':2251,'vuid_count':27464}
 if 'rows'in r:r['rows_sha256']=h.p.sha(h.p.canon(r['rows']))
 with pytest.raises(ValueError):h.fixed_cohort(r)

@pytest.mark.parametrize('kind',['selected','condition','path','missing','extra'])
def test_actual_trace_mutants(kind):
 import os
 name=os.environ.get('VULKAN_REFERENCE19_RUN');runtime=os.environ.get('VULKAN_REFERENCE19_RUNTIME')
 if not name or not runtime:pytest.skip('actual trace cohort not provided')
 root=Path(name);raw=(root/'observed-vu-trace.jsonl').read_bytes();h.inspect_trace(raw,root/'observed',Path(runtime));rows=[json.loads(l) for l in raw.splitlines()]
 if kind=='selected':rows[0]['selected_sha256']='0'*64
 elif kind=='condition':next(r for r in rows if r['kind']=='condition')['target']='PRIVATE_FAKE_EXTENSION'
 elif kind=='path':rows[0]['file']='/private/forged.adoc'
 elif kind=='missing':rows.pop()
 elif kind=='extra':rows[0]['status']='PASS'
 altered=b'\n'.join(json.dumps(r).encode() for r in rows)
 with pytest.raises(ValueError):h.inspect_trace(altered,root/'observed',Path(runtime))

def test_html_extra_vuid():
 v=list(fixture());assert check(v)['vuid_count']==1;v[3]+='<a id="VUID-vkExtra-field-12345"></a>'
 with pytest.raises(ValueError):check(v)

def test_entry_precancel_and_fresh_rejection(tmp_path):
 import subprocess
 cancel=tmp_path/'cancel';cancel.touch();out=tmp_path/'out';args=[sys.executable,str(ROOT/'checks19/generate_reference19.py'),'--docs-git',str(tmp_path/'not-read'),'--runtime-root',str(tmp_path/'also-not-read'),'--output',str(out),'--cancel-file',str(cancel)]
 result=subprocess.run(args,capture_output=True,timeout=10);assert result.returncode==2
 report=json.loads((out/'report.json').read_bytes());assert report['status']=='BLOCKED' and report['steps']==[] and report['error'].startswith('Cancelled:')
 original=(out/'report.json').read_bytes();again=subprocess.run(args,capture_output=True,timeout=10);assert again.returncode!=0 and (out/'report.json').read_bytes()==original
