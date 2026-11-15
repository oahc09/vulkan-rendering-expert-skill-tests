"""Small synthetic XML negative cases, not proof of semantic Registry coverage."""
import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('inventory',Path(__file__).parents[1]/'tools/core17_registry_inventory.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def xml(ext,features=''):return f'<registry>{features}<extensions>{ext}</extensions></registry>'.encode()
@pytest.mark.parametrize('attrs,status',[
 ('supported="vulkan"','vulkan_stable'),('supported="vulkan,vulkansc"','vulkan_stable'),
 ('supported="vulkan" provisional="true"','vulkan_provisional'),('supported="disabled"','disabled'),
 ('supported="vulkansc"','other_api_or_unspecified'),('','other_api_or_unspecified')])
def test_no_scope_silent_exclusions(attrs,status):
    r=m.inventory(xml(f'<extension name="VK_VENDOR_rare" {attrs}/>'))
    assert r['extensions'][0]['classification']==status
    assert sum(r['summary']['classification_counts'].values())==1
    assert r['summary']['release_status']=='BLOCKED'

def test_conditions_preserved_and_sc_require_excluded():
    r=m.inventory(xml('''<extension name="VK_EXT_a" supported="vulkan" deprecatedby="VK_EXT_b"><require depends="VK_VERSION_1_2+(VK_EXT_b,VK_EXT_c)"><command name="vkA"/><type name="VkT"/><enum name="VK_E" alias="VK_E2"/></require><require api="vulkansc"><command name="vkSC"/></require></extension>'''))
    e=r['extensions'][0]
    assert len(e['requirements'])==3 and e['requirements'][0]['condition']=='VK_VERSION_1_2+(VK_EXT_b,VK_EXT_c)'
    assert e['deprecatedby']=='VK_EXT_b' and e['semantic_L1_L2']=='UNREVIEWED'

def test_subdivisions_and_other_api_kept_separate():
    r=m.inventory(xml('', '<feature name="VK_BASE_VERSION_1_4" api="vulkan,vulkanbase" number="1.4"/><feature name="VKSC_VERSION_1_0" api="vulkansc" number="1.0"/>'))
    assert r['summary']['feature_records']==2 and r['summary']['included_feature_records']==1

def test_duplicate_identity_rejected():
    with pytest.raises(ValueError):m.inventory(xml('<extension name="x"/><extension name="x"/>'))

def test_symbol_identity_counts_are_deduplicated_not_reference_counts():
    r=m.inventory(xml('<extension name="a" supported="vulkan"><require><command name="vkA"/><command name="vkA"/></require></extension>'))
    assert r['summary']['unique_direct_requirement_symbols']=={'command':1}

def test_symbol_protect_and_remove_are_not_silently_lost():
    r=m.inventory(xml('''<extension name="VK_EXT_a" supported="vulkan"><require protect="BLOCK_GUARD"><enum name="VK_E" protect="VK_ENABLE_BETA_EXTENSIONS" api="vulkan"/></require><remove><type name="VkRemoved"/></remove></extension>'''))
    e=r['extensions'][0]; ref=e['requirements'][0]
    assert ref['block_attributes']['protect']=='BLOCK_GUARD'
    assert ref['symbol_attributes']['protect']=='VK_ENABLE_BETA_EXTENSIONS'
    assert ref['symbol_attributes']['api']=='vulkan'
    assert 'VkRemoved' in e['remove_blocks'][0]
