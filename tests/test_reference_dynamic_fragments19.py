"""Source-backed diagnosis only; no fragment repair or semantic certification."""
import copy
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.candidate19
FIXTURE = ROOT / 'coverage/v1.0.19/reference-dynamic-fragments.json'
TARGETS = {'dynamic-state-current-value': 2708, 'dynamic-state-lifetime': 1873}

def sha(raw): return hashlib.sha256(raw).hexdigest()

def validate(data):
    assert data['authority'] == 'INDEPENDENT_READ_ONLY_ROOT_CAUSE_AUDIT_NO_PATCH_OR_NEW_RENDER'
    assert data['source_commit'] == 'fa30d4e312e843193601be7cb926c7e25d9ec885'
    assert data['counts'] == TARGETS
    assert data['affected_page_count'] == len(data['pages']) == 26
    assert len({r['page'] for r in data['pages']}) == 26
    assert data['full_spec_unique_anchor_counts'] == {k: 1 for k in TARGETS}
    assert data['proposed_probe_only']['not_authorized_or_executed'] is True
    totals = {k: 0 for k in TARGETS}
    for row in data['pages']:
        assert row['page'].startswith('man/html/') and row['page'].endswith('.html')
        assert row['generated_refpage'] == 'gen/refpage/' + Path(row['page']).stem + '.adoc'
        assert set(row['missing_counts']) == set(TARGETS)
        for k, v in row['missing_counts'].items():
            assert type(v) is int and v > 0
            totals[k] += v
        assert any(x['text'] == 'include::{chapters}/commonvalidity/draw_common.adoc[]' for x in row['late_include_locations'])
    assert totals == TARGETS
    for source in data['fixed_sources'].values():
        for span in source['spans']:
            assert sha(span['text'].encode()) == span['sha256']
            assert len(span['text'].splitlines()) == span['lines'][1] - span['lines'][0] + 1
    assert 'No fragment repaired by this audit' in data['limits']

def load(): return json.loads(FIXTURE.read_bytes())

def test_fixed_diagnosis():
    validate(load())
    assert sha(FIXTURE.read_bytes()) == '025c8cb2e4a43728f406bb1bcc5fcbc53c6a249fd84bda8e0947c3bf14765d16'

@pytest.mark.parametrize('kind', ['drop', 'duplicate', 'count', 'anchor', 'claimed_fix', 'source_hash', 'include'])
def test_mutation(kind):
    d = load(); validate(d); d = copy.deepcopy(d)
    if kind == 'drop': d['pages'].pop()
    elif kind == 'duplicate': d['pages'][-1] = copy.deepcopy(d['pages'][0])
    elif kind == 'count': d['pages'][0]['missing_counts']['dynamic-state-current-value'] += 1
    elif kind == 'anchor': d['full_spec_unique_anchor_counts']['dynamic-state-lifetime'] = 0
    elif kind == 'claimed_fix': d['proposed_probe_only']['not_authorized_or_executed'] = False
    elif kind == 'source_hash': next(iter(d['fixed_sources'].values()))['spans'][0]['sha256'] = '0' * 64
    else: d['pages'][0]['late_include_locations'] = []
    with pytest.raises(AssertionError): validate(d)

class Anchors(HTMLParser):
    def __init__(self): super().__init__(); self.ids = []; self.hrefs = []
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == 'id' or (tag == 'a' and k == 'name'): self.ids.append(v)
            if tag == 'a' and k == 'href': self.hrefs.append(v)

def test_actual_source_and_output_optin():
    value = os.environ.get('VULKAN_REFERENCE_FRAGMENT19_SOURCE')
    if not value: pytest.skip('fixed P5 source/generated/HTML cohort not provided')
    root = Path(value); d = load(); validate(d)
    def read(name, digest):
        p = root / name
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve())
        raw = p.read_bytes(); assert sha(raw) == digest; return raw
    full = read('gen/out/html/vkspec.html', d['full_spec_html_sha256'])
    doc = Anchors(); doc.feed(full.decode())
    assert all(doc.ids.count(k) == 1 for k in TARGETS)
    for row in d['pages']:
        raw = read('gen/out/' + row['page'], row['html_sha256'])
        page = Anchors(); page.feed(raw.decode())
        assert all(k not in page.ids for k in TARGETS)
        assert {k: page.hrefs.count('#' + k) for k in TARGETS} == row['missing_counts']
        src = read(row['generated_refpage'], row['generated_refpage_sha256']).decode()
        assert 'dynamic-state-' not in src
        for inc in row['late_include_locations']: assert src.splitlines()[inc['line']-1] == inc['text']
    for path, source in d['fixed_sources'].items():
        raw = read(path, source['sha256'])
        for span in source['spans']:
            start, end = span['lines']
            assert b''.join(raw.splitlines(keepends=True)[start-1:end]).decode() == span['text']
