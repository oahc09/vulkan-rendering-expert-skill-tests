"""SDK-independent CLI source doubles; no GPU or complete-copy assertion."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
s=importlib.util.spec_from_file_location('image_copy_entry19',ROOT/'checks19/run_image_copy_contracts.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
RAW={k:k.encode() for k in ('formats','copies','common')}
@pytest.fixture
def sources(monkeypatch):
 ids=['VUID-vkCmdCopyImage-srcImage-01548','VUID-vkCmdCopyImage-srcImage-09247']+[f'VUID-vkCmdCopyImage-pRegions-{i:05}' for i in range(7278,7284)]+[f'VUID-vkCmdCopyImage-{side}Image-{i:05}' for side,ns in [('src',range(1728,1731)),('dst',range(1732,1735))] for i in ns]
 corpus={'source':{'sha256':'1'*64,'api_version':'1.4.309'},'entries':{v:[dict(vuid=v,api_owner='vkCmdCopyImage',condition_key='core',page='chapters/copies.html')] for v in ids}}
 mapping={'status':'CONTROLLED_SOURCE_DOUBLE'}
 def source_map(inputs):
  if inputs!=RAW:raise ValueError('controlled prose mismatch')
  return mapping
 def load(raw):
  if raw!=b'vu':raise ValueError('controlled VU mismatch')
  return corpus
 monkeypatch.setattr(m.prose,'map_sources',source_map);monkeypatch.setattr(m.spec,'load_pinned',load)
 return mapping,corpus

def test_complete_control_report_scope_and_sources(sources):
 r=m.run(RAW,b'vu');assert r['case_count']==19 and len(r['vuid_coordinates'])==14
 assert r['whole_copy_admission']=='NOT_INFERRED' and r['release_status']=='BLOCKED'
 assert r['prose']==sources[0] and r['vuid_source']==sources[1]['source']
 for p,h in r['implementation_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
 rows={x['name']:x['result'] for x in r['cases']}
 assert rows['bc1-to-rg32']['status']=='FORMAT_CONDITIONS_WITHIN_SCOPE'
 assert rows['astc-small-mip-block-representation']['unique_destination_extent_inferred'] is False
 assert rows['dst-aligned-offset-partial-edge-extent']['complete_copy_admission'] is False

@pytest.mark.parametrize('part',['formats','copies','common','validusage'])
def test_wrong_cli_source_no_output(sources,tmp_path,monkeypatch,part):
 argv=['copy']
 for k,b in {**RAW,'validusage':b'vu'}.items():
  p=tmp_path/k;p.write_bytes(b'bad' if k==part else b);argv+=['--'+k,str(p)]
 out=tmp_path/'out';monkeypatch.setattr(sys,'argv',argv+['--out',str(out)])
 with pytest.raises(ValueError,match='mismatch'):m.main()
 assert not out.exists()

@pytest.mark.parametrize('part',['prose','vu'])
def test_real_hash_gates_without_sdk(monkeypatch,part):
 if part=='vu':monkeypatch.setattr(m.prose,'map_sources',lambda raw:{})
 with pytest.raises(ValueError,match='wrong frozen|digest mismatch'):m.run(RAW,b'bad')

def test_cli_refuses_overwrite(sources,tmp_path,monkeypatch):
 argv=['copy']
 for k,b in {**RAW,'validusage':b'vu'}.items():
  p=tmp_path/k;p.write_bytes(b);argv+=['--'+k,str(p)]
 out=tmp_path/'out';monkeypatch.setattr(sys,'argv',argv+['--out',str(out)])
 m.main();before=(out/'report.json').read_bytes();assert json.loads(before)['case_count']==19
 with pytest.raises(FileExistsError):m.main()
 assert before==(out/'report.json').read_bytes()

def test_correct_status_wrong_details_rejected(sources,monkeypatch):
 m.run(RAW,b'vu');original=m.rule.format_admit
 def changed(*args):
  r=original(*args)
  if r['status']=='REJECTED':r['vuids']=[]
  return r
 monkeypatch.setattr(m.rule,'format_admit',changed)
 with pytest.raises(ValueError,match='different-block-bytes'):m.run(RAW,b'vu')

def test_missing_vuid_source_rejected(sources):
 m.run(RAW,b'vu');sources[1]['entries'].pop('VUID-vkCmdCopyImage-srcImage-09247')
 with pytest.raises(KeyError):m.run(RAW,b'vu')
