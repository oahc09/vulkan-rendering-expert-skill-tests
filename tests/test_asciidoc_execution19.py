import copy,json,os,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import asciidoc_execution19 as h
pytestmark=pytest.mark.candidate19
def test_normalization_preserves_unknown_paths():
 v=[{'path':'/source/a','private':'/different/a','condition':'VK_SC','result':False}]
 r=h.normalized_trace(v,Path('/source'),Path('/runtime'),Path('/tools'))
 assert r==[{'path':'$SOURCE/a','private':'/different/a','condition':'VK_SC','result':False}]
def test_duplicate_keys():
 with pytest.raises(ValueError):json.loads('{"kind":1,"kind":2}',object_pairs_hook=h.unique)
def test_wrong_runtime_rejected(tmp_path):
 (tmp_path/'fake').write_text('PASS')
 with pytest.raises(ValueError):h.runtime(tmp_path)
def test_wrong_generated_rejected(tmp_path):
 (tmp_path/'summary.json').write_text('{"status":"PASS"}')
 with pytest.raises(ValueError):h.generated(tmp_path)
@pytest.fixture(scope='module')
def actual():
 location=os.environ.get('VULKAN_HTML19_RUN')
 if not location:pytest.skip('actual HTML trace opt-in unavailable; not executed')
 b=Path(location);rt=Path(os.environ['VULKAN_HTML19_RUNTIME']);trace=(b/'trace.jsonl').read_bytes();a=(b/'baseline/gen/out/html/vkspec.html').read_bytes();c=(b/'observed/gen/out/html/vkspec.html').read_bytes()
 assert h.analyze(trace,b/'observed',a,c,rt)['status']=='FIXED_CORE_HTML_OBSERVED_MATCH'
 return b,rt,trace,a,c
@pytest.mark.parametrize('kind',['selected_resigned','conditional','resolve','unknownfield','missing','loaded','html','fake_status'])
def test_actual_coordinated_mutants(actual,kind):
 b,rt,trace,a,c=actual;rows=[json.loads(l) for l in trace.splitlines()]
 if kind=='selected_resigned':
  r=next(x for x in rows if x['kind']=='push_include');r['selected_pieces']=['fabricated normative data'];r['selected_sha256']=h.p.sha(json.dumps(r['selected_pieces'],ensure_ascii=False,separators=(',',':')).encode())
 elif kind=='conditional':
  r=next(x for x in rows if x['kind']=='conditional');r['target']='PRIVATE_FAKE';r['skipping_after']=False
 elif kind=='resolve':next(x for x in rows if x['kind']=='resolve')['resolved'][0]='/private/fake.adoc'
 elif kind=='unknownfield':rows[0]['invented_pass']=True
 elif kind=='missing':rows.pop(10)
 elif kind=='loaded':rows[-1]['loaded_features'][0]['sha256']='0'*64
 elif kind=='html':a=c=b'fake success'
 else:rows=[{'status':'PASS'}]
 changed=b'\n'.join(json.dumps(r,ensure_ascii=False,separators=(',',':')).encode() for r in rows)
 with pytest.raises(ValueError):h.analyze(changed,b/'observed',a,c,rt)

@pytest.mark.parametrize('value',['/tmp/x;echo-secret','/tmp/$(touch-x)','/tmp/space name','/tmp/a\nb'])
def test_no_make_path_injection(value):
 with pytest.raises(ValueError):h.execution_path(value)
