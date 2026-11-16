import copy,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import registry_denominator19 as r
pytestmark=pytest.mark.candidate19
XML=b'<registry><types><type category="struct" name="A" api="vulkan"><member optional="true"><type>uint32_t</type><name>x</name></member></type><type name="B" alias="A"/></types><feature name="V" api="vulkan" number="1.4"><require depends="X+Y"><type name="B"/></require><remove><type name="A"/></remove></feature><unknown secret="retained">raw<child/>tail</unknown></registry>'
@pytest.fixture
def sources(monkeypatch):
 s={'vk.xml':XML,'video.xml':b'<registry><types/></registry>'};monkeypatch.setattr(r,'HASHES',{n:r.sha(b) for n,b in s.items()});return s
def test_complete(sources):
 v=r.build(sources);assert r.verify(v,sources);d=v['documents']['vk.xml'];assert d['element_count']==14
 assert any(n['tag']=='unknown' and n['attributes']=={'secret':'retained'} for n in d['nodes'].values())
 assert any(x['kind']=='remove' for x in d['relations'])
 assert any(x.get('expression')=='X+Y' for x in d['relations'])
@pytest.mark.parametrize('mutation',['node','reference','condition','duplicate','attribute','unknown','text','context'])
def test_reconstruction_rejects(sources,mutation):
 v=r.build(sources);assert r.verify(v,sources);d=v['documents']['vk.xml']
 if mutation=='node':d['nodes'].pop('0/0/0')
 elif mutation=='reference':d['relations']=[x for x in d['relations'] if x['kind']!='alias']
 elif mutation=='condition':d['relations']=[x for x in d['relations'] if x['kind']!='condition:depends']
 elif mutation=='duplicate':d['relations'].append(copy.deepcopy(d['relations'][0]))
 elif mutation=='attribute':d['nodes']['0/0/0']['attributes'].pop('api')
 elif mutation=='unknown':d['nodes'].pop('0/2')
 elif mutation=='text':d['nodes']['0/2']['text']='changed'
 else:d['nodes']['0/0/0']['context']=[]
 with pytest.raises(ValueError):r.verify(v,sources)
def test_wrong_hash(sources):
 sources['vk.xml']+=b' '
 with pytest.raises(ValueError,match='wrong frozen'):r.build(sources)
def test_alias_does_not_enable_or_cross_api(sources):
 v=r.build(sources);a=next(x for x in v['documents']['vk.xml']['relations'] if x['kind']=='alias');s={'api':'vulkan','api_version':'1.4','registry_revision':'1.4.368','conditions':[]}
 assert r.alias_applicability(v,sources,'vk.xml',a['source'],s,s)=='STRUCTURAL_ALIAS_TARGET_ONLY_NOT_ENABLED_OR_INTERCHANGEABLE'
 for other in ({**s,'api':'vulkansc'},{**s,'conditions':['X']},{**s,'registry_revision':'1.4.309'},{}):assert r.alias_applicability(v,sources,'vk.xml',a['source'],s,other)=='APPLICABILITY_UNRESOLVED'
 assert r.alias_applicability(v,sources,'vk.xml','fake',s,s)=='APPLICABILITY_UNRESOLVED'
 v['documents']['vk.xml']['relations'][0]['target']='forged'
 with pytest.raises(ValueError):r.alias_applicability(v,sources,'vk.xml',a['source'],s,s)
def test_cycle_is_preserved_not_equated():
 d=r._document(b'<registry><types><type name="A" alias="B"/><type name="B" alias="A"/></types></registry>','test')
 assert [(x['target'],x['resolution']) for x in d['relations']]==[('B','UNIQUE_STRUCTURAL_CANDIDATE'),('A','UNIQUE_STRUCTURAL_CANDIDATE')]
def test_enum_groups_resolve():
 d=r._document(b'<registry><enums name="E"><enum name="A" value="1"/></enums><extensions><extension name="X"><require><enum name="B" extends="E" value="2"/></require></extension></extensions></registry>','test')
 assert next(x for x in d['relations'] if x['kind']=='extends')['candidates']==['0/0']
def test_real_frozen_sources():
 p=Path('/workspace/scratch/62d43a81bbde/cts-src/external/vulkan-docs/src/xml')
 if not all((p/n).is_file() for n in r.HASHES):pytest.skip('fixed XML not locally available; not executed')
 s={n:(p/n).read_bytes() for n in r.HASHES};v=r.build(s);assert r.verify(v,s)
 assert v['documents']['vk.xml']['element_count']>30000
 assert v['documents']['video.xml']['element_count']>3000

def test_source_reader_rejects_fifo_symlink(tmp_path):
 import os
 f=tmp_path/'fifo';os.mkfifo(f)
 with pytest.raises(ValueError):r.read_source(f)
 ordinary=tmp_path/'source';ordinary.write_bytes(XML);link=tmp_path/'link';link.symlink_to(ordinary)
 with pytest.raises(OSError):r.read_source(link)
 assert r.read_source(ordinary)==XML

def test_explicit_sc_alias_not_overridden(monkeypatch):
 s={'vk.xml':b'<registry><types><type name="A" api="vulkansc"/><type name="B" alias="A"/></types></registry>','video.xml':b'<registry/>'}
 monkeypatch.setattr(r,'HASHES',{n:r.sha(b) for n,b in s.items()});v=r.build(s)
 scope={'api':'vulkan','api_version':'1.4','registry_revision':'1.4.368','conditions':[]}
 assert r.alias_applicability(v,s,'vk.xml','0/0/1',scope,scope)=='APPLICABILITY_UNRESOLVED'
