"""Controlled CLI orchestration; no machine-local normative SDK needed."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
sp=importlib.util.spec_from_file_location('layout_entry19',ROOT/'checks19/run_layout_contracts.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
@pytest.fixture
def sources(monkeypatch):
 mapping={'status':'CONTROLLED_SOURCE_DOUBLE'}
 ids=['VUID-VkPushConstantRange-offset-00294','VUID-VkPushConstantRange-offset-00295','VUID-VkPushConstantRange-size-00296','VUID-VkPushConstantRange-size-00297','VUID-VkPushConstantRange-size-00298','VUID-VkPipelineLayoutCreateInfo-pPushConstantRanges-00292','VUID-vkCmdPushConstants-offset-01795','VUID-vkCmdPushConstants-offset-01796']
 corpus={'source':{'sha256':'a'*64,'api_version':'1.4.309'},'entries':{v:[{'vuid':v,'api_owner':v.split('-')[1],'condition_key':'core','page':'chapters/descriptorsets.html'}] for v in ids}}
 def mapped(c,i):
  if (c,i)!=(b'chapter',b'common'):raise ValueError('controlled chapter/include mismatch')
  return mapping
 def loaded(v):
  if v!=b'vu':raise ValueError('controlled VU mismatch')
  return corpus
 monkeypatch.setattr(m.prose,'map_sources',mapped);monkeypatch.setattr(m.spec,'load_pinned',loaded)
 return mapping,corpus

def test_full_controls_bounded_and_hash_bound(sources):
 r=m.run(b'chapter',b'common',b'vu');assert r['case_count']==18
 assert r['semantic_completion']=='UNKNOWN_NOT_INFERRED' and r['release_status']=='BLOCKED'
 assert r['evidence_kind']=='CALLER_DECLARED_DEFINITION_HOST_CONTROLS_NOT_GPU'
 for p,h in r['implementation_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
 assert r['prose']==sources[0] and r['vuid_source']==sources[1]['source']
 rows={c['name']:c['result'] for c in r['cases']}
 assert rows['different-stage-byte-overlap-created']['status']=='RANGES_WITHIN_SCOPE'
 assert rows['overlap-update-only-vertex']['vuids']==['VUID-vkCmdPushConstants-offset-01796']
 assert rows['bind-incompatible-prefix-disturbs-both-directions']['disturbed']==[0,2]

@pytest.mark.parametrize('part',['chapter','common','validusage'])
def test_cli_wrong_input_no_output(sources,tmp_path,monkeypatch,part):
 paths={k:tmp_path/k for k in ['chapter','common','validusage']}
 for k,v in zip(paths,[b'chapter',b'common',b'vu']):paths[k].write_bytes(v)
 paths[part].write_bytes(b'bad');out=tmp_path/'out'
 monkeypatch.setattr(sys,'argv',['layout',*[arg for k,v in paths.items() for arg in ['--'+k,str(v)]],'--out',str(out)])
 with pytest.raises(ValueError,match='mismatch'):m.main()
 assert not out.exists()

@pytest.mark.parametrize('part',['prose','vu'])
def test_actual_hash_gates_without_sdk(monkeypatch,part):
 if part=='vu':monkeypatch.setattr(m.prose,'map_sources',lambda c,i:{})
 with pytest.raises(ValueError,match='wrong frozen|digest mismatch'):m.run(b'bad',b'bad',b'bad')

def test_cli_new_output_only(sources,tmp_path,monkeypatch):
 argv=['layout']
 for key,raw in [('chapter',b'chapter'),('common',b'common'),('validusage',b'vu')]:
  p=tmp_path/key;p.write_bytes(raw);argv+=['--'+key,str(p)]
 out=tmp_path/'out';monkeypatch.setattr(sys,'argv',argv+['--out',str(out)])
 m.main();before=(out/'report.json').read_bytes();assert json.loads(before)['case_count']==18
 with pytest.raises(FileExistsError):m.main()
 assert before==(out/'report.json').read_bytes()

def test_wrong_control_result_is_rejected(sources,monkeypatch):
 m.run(b'chapter',b'common',b'vu')
 monkeypatch.setattr(m.rule,'compatible',lambda *args:{'status':'COMPATIBLE'})
 with pytest.raises(ValueError,match='set0-diff'):m.run(b'chapter',b'common',b'vu')

def test_correct_status_wrong_detail_is_rejected(sources,monkeypatch):
 m.run(b'chapter',b'common',b'vu');original=m.rule.push_update
 def corrupted(*args):
  r=original(*args)
  if r['status']=='REJECTED':r['vuids']=[]
  return r
 monkeypatch.setattr(m.rule,'push_update',corrupted)
 with pytest.raises(ValueError,match='overlap-update-only-vertex'):m.run(b'chapter',b'common',b'vu')

def test_missing_coordinate_rejected(sources):
 m.run(b'chapter',b'common',b'vu')
 sources[1]['entries'].pop('VUID-vkCmdPushConstants-offset-01796')
 with pytest.raises(KeyError):m.run(b'chapter',b'common',b'vu')
