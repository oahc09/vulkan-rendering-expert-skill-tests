"""Live-only gates. Missing run is a skip; incomplete/tampered runs fail."""
import json
import os
import re
from pathlib import Path

import pytest
from behavior_cases import CASES as NEW_CASES
from run_live_model_behavior import CASES, digest, audit_case
import test_v1_0_8_model_behavior as historical

pytestmark = pytest.mark.live


@pytest.fixture
def live_run():
    location = os.environ.get('VULKAN_LIVE_RUN_DIR')
    if not location:
        pytest.skip('No live run configured; historical snapshots are not live evidence')
    root = Path(location)
    manifest = json.loads((root / 'manifest.json').read_text())
    assert manifest['layer'] == 'Live'
    assert manifest['status'] in ('generated', 'gate_passed', 'gate_failed'), manifest
    assert re.fullmatch('[0-9a-f]{40}', manifest['skill_sha'])
    assert manifest['model']
    assert isinstance(manifest['parameters'], dict)
    assert set(manifest['cases']) == set(CASES), 'Full live gate requires all 12 cases'
    return root, manifest


@pytest.mark.parametrize('case', CASES)
def test_live_case(live_run, case, monkeypatch):
    root, manifest = live_run
    folder = root / case
    record = audit_case(folder, manifest)
    reads = {(r['path'], r['section']) for r in record['reads']}
    assert ('references/00_expert_entry/hard_rules.md', None) in reads
    route = 'references/07_integration_pack/task_routing_rules.md'
    assert any(path == route and section in (None, '#routing-entry', '0. 唯一路由入口') for path, section in reads)
    assert record['status'] == 'generated', record
    answer = (folder / 'answer.md').read_bytes()
    assert digest(answer) == record['answer_sha256']
    assert record['reads'][0]['path'] == 'SKILL.md'
    for read in record['reads']:
        assert re.fullmatch('[0-9a-f]{64}', read['content_sha256'])
        assert re.fullmatch('[0-9a-f]{64}', read['file_sha256'])
        assert read['start_line'] <= read['end_line']
    assert record['rounds']
    for step in record['rounds']:
        assert digest((folder / step['input_file']).read_bytes()) == step['input_sha256']
        raw = (folder / step['output_file']).read_bytes()
        assert digest(raw) == step['output_sha256']
        envelope = json.loads(raw)
        assert envelope['model'] == step['model'] == manifest['model']
        assert envelope['parameters'] == step['parameters'] == manifest['parameters']
        assert step['returncode'] == 0
        assert step['usage'] == envelope['usage']
        for key in ('input_tokens', 'output_tokens'):
            assert type(step['usage'][key]) is int and step['usage'][key] >= 0
    final = json.loads((folder / record['rounds'][-1]['output_file']).read_bytes())
    assert final['response']['answer'].encode('utf-8') == answer
    text = answer.decode('utf-8')
    if re.search(r'(?m)^\s*(?:结论[：:]\s*)?(?:已完成|已解决|根因已修复|性能已优化)', text):
        assert ('references/00_expert_entry/verification_gate.md', None) in reads
    if case in NEW_CASES:
        for pattern in NEW_CASES[case]['required']:
            assert re.search(pattern, text, re.I), f'{case}: missing smoke criterion {pattern}'
    else:
        # Preserve all four original diagnosis assertions, without relabeling snapshots.
        monkeypatch.setattr(historical, 'read', lambda _: text)
        checks = dict(zip(CASES[:4], [historical.test_repository_map_behavior,
                      historical.test_vulkan_13_upgrade_behavior,
                      historical.test_android_rotation_behavior,
                      historical.test_compute_pass_behavior]))
        checks[case]()
