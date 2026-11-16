import hashlib,importlib.util,json,sys,types
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import contract_registry19 as registry
pytestmark=pytest.mark.candidate19
@pytest.mark.parametrize('kind',['duplicate','stale-digest','symlink','directory'])
def test_external_input_rejected_before_children(tmp_path,monkeypatch,kind):
 spec=importlib.util.spec_from_file_location('entry',ROOT/'checks19/check_resource_contract_chain.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
 pair=json.loads((ROOT/'coverage/v1.0.19/pair.json').read_text());skill=tmp_path/'skill';skill.mkdir();trace=tmp_path/'trace.json';trace.write_text('{"proofs":[],"proofs":[]}');vu=tmp_path/'vu';vu.write_text('{}');out=tmp_path/'out'
 if kind=='symlink':link=tmp_path/'link';link.symlink_to(trace);trace=link
 if kind=='directory':trace=tmp_path
 digest=hashlib.sha256(trace.read_bytes()).hexdigest() if trace.is_file() else 'a'*64
 if kind=='stale-digest':digest='0'*64
 monkeypatch.setattr(entry,'git',lambda root,*args: ('a'*40 if Path(root)==ROOT else pair['skill_sha']) if args==('rev-parse','HEAD') else '')
 fake=types.SimpleNamespace(parse=registry.parse,verify=lambda *a:{},INPUTS={})
 def loader(name,path):
  assert name=='chain_registry', 'must not load supervisor or start children'
  return fake
 monkeypatch.setattr(entry,'load',loader)
 argv=['entry','--docs-root',str(tmp_path),'--validusage',str(vu),'--skill-root',str(skill),'--trace',str(trace),'--evidence-root',str(tmp_path),'--output',str(out),'--expected-tests-head','a'*40,'--expected-skill-head',pair['skill_sha'],'--expected-trace-sha256',digest,'--development']
 monkeypatch.setattr(sys,'argv',argv);assert entry.main()==2
 report=json.loads((out/'report.json').read_text());assert report['status']=='BLOCKED' and report['steps']==[]
 expected={'duplicate':'duplicate','stale-digest':'external trace digest','symlink':'regular non-symlink','directory':'regular non-symlink'}[kind]
 assert expected in report['error']
