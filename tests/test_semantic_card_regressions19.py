"""Knowledge-card regression only: no device capability or full semantic proof."""
import os
import pathlib
import re
import pytest

ROOT = pathlib.Path(os.environ.get('VULKAN_SKILL_ROOT', '/tmp/vulkan119-skill'))
CARD = 'references/03_api_manual/05_descriptor/descriptor_indexing.md'

def validate_card(text):
    # Reject the exact invented generic identifier, not real type-specific names.
    if re.search(r'\bdescriptorBindingUpdateAfterBind\b', text):
        raise ValueError('invented generic UAB feature')
    if 'maxDescriptorArrayLength' in text:
        raise ValueError('unsupported generic array-length field')
    pairs = {
        'descriptorBindingUniformBufferUpdateAfterBind': '03005',
        'descriptorBindingSampledImageUpdateAfterBind': '03006',
        'descriptorBindingStorageImageUpdateAfterBind': '03007',
        'descriptorBindingStorageBufferUpdateAfterBind': '03008',
        'descriptorBindingUniformTexelBufferUpdateAfterBind': '03009',
        'descriptorBindingStorageTexelBufferUpdateAfterBind': '03010',
        'descriptorBindingInlineUniformBlockUpdateAfterBind': '02211',
        'descriptorBindingAccelerationStructureUpdateAfterBind': '03570',
    }
    for feature, suffix in pairs.items():
        if not any(feature in line and '| '+suffix+' |' in line for line in text.splitlines()):
            raise ValueError('missing or mismatched type-specific mapping: '+feature)
    for phrase in ('物理设备支持并不等于已启用', '最高 binding 编号',
                   '不能批准仍被访问的 stale slot',
                   '只启用 sampled-image UAB 不批准 storage-buffer UAB',
                   'maxVariableDescriptorCount'):
        if phrase not in text:
            raise ValueError('missing bounded knowledge contract: '+phrase)
    return True

@pytest.fixture
def card():
    return (ROOT / CARD).read_text()

def test_actual_card_contract(card):
    assert validate_card(card)

@pytest.mark.parametrize('old', ['descriptorBindingUpdateAfterBind', 'maxDescriptorArrayLength'])
def test_invented_field_negative(card, old):
    assert validate_card(card)
    with pytest.raises(ValueError, match='generic'):
        validate_card(card+'\n'+old)

@pytest.mark.parametrize('feature,suffix', [
    ('descriptorBindingStorageBufferUpdateAfterBind','03008'),
    ('descriptorBindingSampledImageUpdateAfterBind','03006'),
    ('descriptorBindingAccelerationStructureUpdateAfterBind','03570')])
def test_cross_type_mapping_negative(card,feature,suffix):
    assert validate_card(card)
    lines=[line.replace('| '+suffix+' |','| 99999 |') if feature in line else line for line in card.splitlines()]
    with pytest.raises(ValueError,match='mapping'):
        validate_card('\n'.join(lines))

def test_support_not_enable_and_stale_not_retired(card):
    assert validate_card(card)
    for phrase in ('物理设备支持并不等于已启用','不能批准仍被访问的 stale slot'):
        with pytest.raises(ValueError,match='contract'):
            validate_card(card.replace(phrase,''))
