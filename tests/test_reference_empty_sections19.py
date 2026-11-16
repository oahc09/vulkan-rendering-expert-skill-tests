"""Independent fixed-cohort source classification, never a semantic allowance."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
pytestmark = pytest.mark.candidate19
FIXTURE = ROOT / 'coverage/v1.0.19/reference-empty-sections.json'
COMMIT = 'fa30d4e312e843193601be7cb926c7e25d9ec885'
COUNTS = {
    'DESCRIPTION_ONLY_COMMENT_ONLY_GENERATED_VALIDITY_INCLUDE': 47,
    'MEMBER_PROSE_PRESENT_IN_OTHER_GENERATED_SECTION': 4,
    'UPSTREAM_EXPLICIT_PLACEHOLDER_NO_MEMBER_PROSE': 12,
    'DESCRIPTION_BODY_SC_ONLY_FILTERED_IN_VULKAN_CONFIG': 3,
}
SC = {'VkDeviceMemory', 'VkShaderModule', 'VkStructureType'}
MOVED = {'VkAllocationCallbacks': 'Description',
         'VkPhysicalDeviceVertexAttributeDivisorPropertiesEXT': 'Description',
         'VkSurfaceCapabilitiesKHR': 'Description',
         'VkDeviceFaultDebugInfoKHR': 'C Specification'}
PLACEHOLDERS = {'VkAmigoProfilingSubmitInfoSEC', 'VkCuFunctionCreateInfoNVX',
 'VkCuLaunchInfoNVX', 'VkCuModuleCreateInfoNVX', 'VkCuModuleTexturingModeCreateInfoNVX',
 'VkDescriptorSetBindingReferenceVALVE', 'VkDescriptorSetLayoutHostMappingInfoVALVE',
 'VkPhysicalDeviceAmigoProfilingFeaturesSEC', 'VkPhysicalDeviceDescriptorSetHostMappingFeaturesVALVE',
 'VkPhysicalDevicePipelineCacheIncrementalModeFeaturesSEC', 'VkPhysicalDeviceThrottleHintFeaturesSEC',
 'VkThrottleHintSubmitInfoSEC'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def span_valid(span):
    assert set(span) == {'lines', 'sha256', 'text'}
    start, end = span['lines']
    assert type(start) is int and type(end) is int and 1 <= start <= end
    assert len(span['text'].splitlines()) == end - start + 1
    assert digest(span['text'].encode()) == span['sha256']


def validate(data):
    assert data['source_commit'] == COMMIT
    assert data['authority'] == 'INDEPENDENT_READ_ONLY_SOURCE_CLASSIFICATION_NOT_RENDER_RERUN'
    assert data['counts'] == COUNTS and len(data['rows']) == 66
    assert len({(x['entity'], x['empty_section']) for x in data['rows']}) == 66
    counts = {k: 0 for k in COUNTS}
    for row in data['rows']:
        n = row['entity']; kind = row['classification']
        assert kind in counts
        counts[kind] += 1
        assert row['semantic_acceptance'] is False
        assert row['generated_file'] == 'gen/refpage/' + n + '.adoc'
        span_valid(row['generated_section'])
        body = row['generated_section']['text']
        assert body.startswith('== ' + row['empty_section'] + '\n')
        assert len(row['original_normative_contexts']) == 1
        origin = row['original_normative_contexts'][0]
        assert origin['file_sha256'] == data['verified_original_files'][origin['path']]
        span_valid(origin['context'])
        assert "refpage='" + n + "'" in origin['context']['text']
        if kind == 'DESCRIPTION_ONLY_COMMENT_ONLY_GENERATED_VALIDITY_INCLUDE':
            assert row['empty_section'] == 'Description' and n not in SC
            inc = row['include']
            assert inc['path'] == 'gen/validity/structs/' + n + '.adoc'
            assert digest(inc['text'].encode()) == inc['sha256']
            assert all(not line.strip() or line.lstrip().startswith('//') for line in inc['text'].splitlines())
            assert body.split('\n', 1)[1].strip() == 'include::{generated}/validity/structs/' + n + '.adoc[]'
        elif kind == 'DESCRIPTION_BODY_SC_ONLY_FILTERED_IN_VULKAN_CONFIG':
            assert n in SC and row['empty_section'] == 'Description'
            content = body.split('\n', 1)[1].strip()
            assert content.startswith('ifdef::VKSC_VERSION_1_0[]')
            assert content.endswith('endif::VKSC_VERSION_1_0[]')
        elif kind == 'UPSTREAM_EXPLICIT_PLACEHOLDER_NO_MEMBER_PROSE':
            assert n in PLACEHOLDERS and row['empty_section'] == 'Members'
            assert 'There is currently no specification language written for this type.' in origin['context']['text']
        else:
            assert n in MOVED and row['empty_section'] == 'Members'
            assert row['member_prose_destination'] == MOVED[n]
            span_valid(row['destination_span'])
            assert row['destination_span']['text'].startswith('== ' + MOVED[n] + '\n')
            assert '  * pname:' in row['destination_span']['text']
    assert counts == COUNTS
    for evidence in data['extraction_code_context'].values():
        span_valid(evidence['context'])
    assert 'No empty section is globally exempted by this report' in data['limits']


def load():
    return json.loads(FIXTURE.read_bytes())


def test_fixed_classification():
    validate(load())
    assert digest(FIXTURE.read_bytes()) == '6990ca13d37cc646c8973b6d6e1fa351322b6f274ebf536d14100fbb40b4c500'


@pytest.mark.parametrize('kind', ['missing', 'duplicate', 'classification', 'span_hash',
                                 'semantic_pass', 'placeholder_erased', 'include_prose',
                                 'wrong_sc', 'wrong_destination'])
def test_mutation(kind):
    data = load(); validate(data)
    changed = copy.deepcopy(data)
    first = changed['rows'][0]
    if kind == 'missing': changed['rows'].pop()
    elif kind == 'duplicate': changed['rows'][-1] = copy.deepcopy(first)
    elif kind == 'classification': first['classification'] = 'UPSTREAM_EXPLICIT_PLACEHOLDER_NO_MEMBER_PROSE'
    elif kind == 'span_hash': first['generated_section']['sha256'] = '0' * 64
    elif kind == 'semantic_pass': first['semantic_acceptance'] = True
    elif kind == 'placeholder_erased':
        row = next(x for x in changed['rows'] if x['entity'] in PLACEHOLDERS)
        span = row['original_normative_contexts'][0]['context']
        span['text'] = span['text'].replace('There is currently no specification language written for this type.', 'All specification language has been reviewed.')
        span['sha256'] = digest(span['text'].encode())
    elif kind == 'include_prose':
        first['include']['text'] += 'A previously omitted normative requirement.\n'
        first['include']['sha256'] = digest(first['include']['text'].encode())
    elif kind == 'wrong_sc':
        row = next(x for x in changed['rows'] if x['entity'] in SC)
        span = row['generated_section']; span['text'] = span['text'].replace('VKSC_VERSION_1_0', 'VK_VERSION_1_0')
        span['sha256'] = digest(span['text'].encode())
    else:
        next(x for x in changed['rows'] if x['entity'] in MOVED)['member_prose_destination'] = 'Members'
    with pytest.raises(AssertionError): validate(changed)


def test_actual_sources_optin():
    value = os.environ.get('VULKAN_REFERENCE_EMPTY19_SOURCE')
    if not value: pytest.skip('fixed P5 source/generated cohort not provided')
    root = Path(value).resolve(); data = load(); validate(data)
    def read(path, expected):
        file = root / path
        assert not file.is_symlink() and file.resolve().is_relative_to(root)
        raw = file.read_bytes(); assert digest(raw) == expected
        return raw
    def check_span(raw, span):
        first, last = span['lines']
        assert b''.join(raw.splitlines(keepends=True)[first-1:last]).decode() == span['text']
    for row in data['rows']:
        raw = read(row['generated_file'], row['generated_sha256'])
        check_span(raw, row['generated_section'])
        if 'destination_span' in row: check_span(raw, row['destination_span'])
        if 'include' in row:
            inc = row['include']; assert read(inc['path'], inc['sha256']).decode() == inc['text']
        for origin in row['original_normative_contexts']:
            check_span(read(origin['path'], origin['file_sha256']), origin['context'])
    for path, evidence in data['extraction_code_context'].items():
        check_span(read(path, evidence['sha256']), evidence['context'])
