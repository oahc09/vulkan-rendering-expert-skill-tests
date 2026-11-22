"""Controlled entry tests: no machine-local SDK requirement or semantic certification."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('semantic_card_entry19',ROOT/'checks19/audit_semantic_cards.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OLDLINE='资源销毁前是否已更新 descriptor 指向新资源或等待 GPU idle？'

@pytest.fixture
def setup(tmp_path,monkeypatch):
 # Tiny normative coordinate fixture, not the full frozen inventory.
 corpus=m.s.spec.index_document({'version info':{'schema version':2,'api version':'1.4.309'},'validation':{'vkDestroyBuffer':{'core':[{'vuid':'VUID-vkDestroyBuffer-buffer-00922','text':'All submitted commands that refer to buffer must have completed execution','page':'memory.html'}]}}})
 corpus['source']={'sha256':m.s.spec.PINNED_SHA256,'api_version':'1.4.309'}
 inv=m.s._assemble(corpus,{'source_sha256':m.s.registry.SOURCE_SHA256,'source_commit':m.s.registry.SOURCE_COMMIT,'features':[{'name':'VK_VERSION_1_0','included_standard_vulkan':True,'api':'vulkan'}],'extensions':[]})
 skill=tmp_path/'skill'; folder=skill/m.PREFIX;folder.mkdir(parents=True)
 # Exact scoped passages, rather than pretending these are all original cards.
 (folder/'descriptor_update.md').write_text('''### delivery19-descriptor-retirement-contract
This card and `uniform_buffer_descriptor.md#delivery19-ordinary-ubo-lifetime`
share one ordinary-binding contract: descriptor replacement does not retire old
resource consumers. Pending update is prohibited by the exact Vulkan1.4.309
`VUID-vkUpdateDescriptorSets-None-03047`; buffer destruction independently requires
all submitted commands referring to the buffer to complete
(`VUID-vkDestroyBuffer-buffer-00922`). Advanced flags never waive resource lifetime.
Updating affected recording/executable ordinary bindings requires reset/re-record
before reuse; existing actual 03047/00070 lifecycle controls cover this bounded
path. These controls do not exercise illegal destruction of a pending resource.
''')
 (folder/'uniform_buffer_descriptor.md').write_text('''### delivery19-ordinary-ubo-lifetime: retirement is not reusable recording
An ordinary binding used by a pending command buffer cannot be updated
(VUID03047). The same descriptor value is not an exemption. A fence that actually
covers that submission can establish retirement; a stale generation or unrelated
queue's fence cannot. Track every referencing command buffer and serialize host
updates. Unknown reference inventory is not safe-to-update evidence.
After retirement, updating a set referenced by a recording/executable command
buffer can invalidate that command buffer. Reset/re-record the affected commands
before submission; merely observing a signaled fence does not restore their
recorded validity. Retain referenced resource lifetime and memory dependencies
separately. Advanced binding flags require their own enabled-feature and usage
contracts; this ordinary-binding planner deliberately refuses that scope.
''')
 (folder/'descriptor_indexing.md').write_text('descriptorBindingSampledImageUpdateAfterBind\nmaxVariableDescriptorCount\n')
 old=('historical checklist\n'+OLDLINE+'\n').encode()
 calls=[]
 def git(argv):
  calls.append(argv)
  assert argv==['git','-C',str(skill),'show',m.OLD+':'+m.PREFIX+'descriptor_update.md']
  return old
 monkeypatch.setattr(m.subprocess,'check_output',git)
 monkeypatch.setattr(m,'REPAIRED_CARD_SHA256',{m.PREFIX+p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()})
 return inv,skill,old,calls

def test_build_binds_actual_quote_and_current_bytes(setup):
 inv,skill,old,calls=setup;r=m.build(inv,skill)
 assert calls and r['historical_line']==OLDLINE
 assert r['historical_card_sha256']==hashlib.sha256(old).hexdigest()
 assert r['before_findings'][0]['kind']=='SAME_SCOPE_OPPOSED_ASSERTIONS'
 assert r['after_findings']==[]
 for path,digest in r['current_card_sha256'].items():assert digest==hashlib.sha256((skill/path).read_bytes()).hexdigest()
 assert 'Manually authored' in r['claim_interpretation']
 assert r['semantic_L1_L2_completion']=='UNKNOWN_NOT_INFERRED' and r['release_status']=='BLOCKED'
 assert r['denominators']['stable_registry_review_scopes']==1 # not claiming 497 full semantic scope

@pytest.mark.parametrize('name,text',[('descriptor_update.md',OLDLINE),('descriptor_indexing.md','descriptorBindingUpdateAfterBind'),('descriptor_indexing.md','maxDescriptorArrayLength')])
def test_known_regression_rejected(setup,name,text):
 inv,skill,_,_=setup;m.build(inv,skill)
 (skill/m.PREFIX/name).write_text(text)
 with pytest.raises(ValueError,match='exact reviewed repair cohort'):m.build(inv,skill)

def test_historical_quote_must_match(setup,monkeypatch):
 inv,skill,_,_=setup;m.build(inv,skill)
 monkeypatch.setattr(m.subprocess,'check_output',lambda argv:b'unrelated historical content')
 with pytest.raises(ValueError,match='historical defect'):m.build(inv,skill)

def test_cli_wrong_source_hash_has_no_output(tmp_path,monkeypatch):
 vu=tmp_path/'vu.json';vu.write_text('{}');reg=tmp_path/'vk.xml';reg.write_text('<registry/>');out=tmp_path/'out'
 monkeypatch.setattr(sys,'argv',['audit','--validusage',str(vu),'--registry',str(reg),'--skill',str(tmp_path),'--out',str(out)])
 with pytest.raises(ValueError,match='digest mismatch'):m.main()
 assert not out.exists()

def test_cli_controlled_fixture_output(setup,tmp_path,monkeypatch):
 inv,skill,_,_=setup;vu=tmp_path/'vu';reg=tmp_path/'reg';vu.write_bytes(b'controlled-vu');reg.write_bytes(b'controlled-reg');out=tmp_path/'out'
 def controlled_load(v,r):
  assert (v,r)==(b'controlled-vu',b'controlled-reg');return inv
 monkeypatch.setattr(m.s,'load',controlled_load)
 monkeypatch.setattr(sys,'argv',['audit','--validusage',str(vu),'--registry',str(reg),'--skill',str(skill),'--out',str(out)])
 m.main();r=json.loads((out/'card-audit.json').read_text());assert r['after_findings']==[] and r['release_status']=='BLOCKED'
 assert json.loads((out/'unreviewed-audit.json').read_text())['counts']['unclaimed_normative_units']==1
 with pytest.raises(FileExistsError):m.main()

@pytest.mark.parametrize('name,text',[('descriptor_update.md',''),('descriptor_update.md','arbitrary replacement'),('uniform_buffer_descriptor.md','authority altered'),('descriptor_indexing.md','')])
def test_positive_card_binding_not_absence_of_bad_text(setup,name,text):
 inv,skill,_,_=setup;m.build(inv,skill)
 (skill/m.PREFIX/name).write_text(text)
 with pytest.raises(ValueError,match='exact reviewed repair cohort'):m.build(inv,skill)
