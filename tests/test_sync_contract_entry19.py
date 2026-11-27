"""CLI orchestration tests with controlled source doubles, never SDK-dependent."""
import importlib.util
import json
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('sync_entry19',ROOT/'checks19/run_sync_contracts.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
@pytest.fixture
def sources(monkeypatch):
 mapping={'status':'CONTROLLED_SOURCE_DOUBLE','source':{'sha256':'1'*64},'slices':[]}
 ids=['VUID-VkBufferMemoryBarrier-offset-01187','VUID-VkBufferMemoryBarrier-size-01188','VUID-VkBufferMemoryBarrier-size-01189']
 corpus={'source':{'sha256':'2'*64,'api_version':'1.4.309'},'entries':{v:[{'vuid':v,'api_owner':'VkBufferMemoryBarrier','condition_key':'core','page':'chapters/synchronization.html'}] for v in ids}}
 def extract(raw):
  if raw!=b'controlled-prose':raise ValueError('controlled prose bytes mismatch')
  return mapping
 def load(raw):
  if raw!=b'controlled-vu':raise ValueError('controlled VU bytes mismatch')
  return corpus
 monkeypatch.setattr(m.prose,'extract',extract);monkeypatch.setattr(m.spec,'load_pinned',load)
 return mapping,corpus

def test_controls_keep_declared_fact_boundary(sources):
 r=m.run(b'controlled-prose',b'controlled-vu')
 assert r['case_count']==20 and len(r['cases'])==20
 assert r['evidence_kind']=='DECLARED_FACTS_HOST_CONTROLS_NOT_GPU'
 assert r['semantic_completion']=='UNKNOWN_NOT_INFERRED' and r['release_status']=='BLOCKED'
 assert r['prose']==sources[0] and r['range_normative_source']==sources[1]['source']
 rows={x['name']:x['result'] for x in r['cases']}
 assert rows['unaligned-valid']['status']=='RANGE_WITHIN_SCOPE'
 assert rows['raw-only-order-and-fence']['status']=='INSUFFICIENT_DEPENDENCY'
 assert rows['war-execution-only']['status']=='CALLER_FACTS_SUFFICIENT'
 assert rows['host-missing-required_flush_completed']['status']=='UNKNOWN'

@pytest.mark.parametrize('which',['prose','vu'])
def test_real_hash_gates_reject_before_output(tmp_path,monkeypatch,which):
 # Actual production extract/load gates; no installed fixed official files needed.
 if which=='vu':monkeypatch.setattr(m.prose,'extract',lambda raw:{})
 with pytest.raises(ValueError,match='wrong frozen|digest mismatch'):m.run(b'bad',b'bad')

@pytest.mark.parametrize('which',['prose','vu'])
def test_cli_bad_source_no_report(sources,tmp_path,monkeypatch,which):
 p=tmp_path/'prose';v=tmp_path/'vu';o=tmp_path/'out';p.write_bytes(b'controlled-prose');v.write_bytes(b'controlled-vu')
 (p if which=='prose' else v).write_bytes(b'bad')
 monkeypatch.setattr(sys,'argv',['run','--prose',str(p),'--validusage',str(v),'--out',str(o)])
 with pytest.raises(ValueError,match='bytes mismatch'):m.main()
 assert not o.exists()

def test_cli_success_does_not_overwrite(sources,tmp_path,monkeypatch):
 p=tmp_path/'prose';v=tmp_path/'vu';o=tmp_path/'out';p.write_bytes(b'controlled-prose');v.write_bytes(b'controlled-vu')
 monkeypatch.setattr(sys,'argv',['run','--prose',str(p),'--validusage',str(v),'--out',str(o)])
 m.main();before=(o/'report.json').read_bytes();assert json.loads(before)['release_status']=='BLOCKED'
 with pytest.raises(FileExistsError):m.main()
 assert (o/'report.json').read_bytes()==before

def test_changed_rule_result_cannot_silently_pass(sources,monkeypatch):
 m.run(b'controlled-prose',b'controlled-vu') # positive before mutation
 monkeypatch.setattr(m.rule,'evaluate',lambda facts:{'status':'CALLER_FACTS_SUFFICIENT'})
 with pytest.raises(ValueError,match='contract control failed: raw-only-order-and-fence'):m.run(b'controlled-prose',b'controlled-vu')

def test_missing_normative_coordinate_rejected(sources):
 m.run(b'controlled-prose',b'controlled-vu')
 sources[1]['entries'].pop('VUID-VkBufferMemoryBarrier-size-01188')
 with pytest.raises(KeyError):m.run(b'controlled-prose',b'controlled-vu')
