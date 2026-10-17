"""Synthetic accounting unit fixtures, never live inference results."""
import json
from pathlib import Path

import pytest
import measure_context as metrics
from run_live_model_behavior import CASES, BASELINE_SHA


def test_no_paired_evidence_is_unmeasured():
    result = metrics.compare_runs(None, None, None)
    assert result['status'] == 'unmeasured'
    assert result['actual_model_input_target_met'] is None


def synthetic_run(root, sha, count):
    root.mkdir()
    manifest = dict(layer='Live', status='generated', skill_sha=sha, skill_dirty=False, cases=CASES,
                    model='UNIT-MOCK-NOT-LIVE', parameters={'temperature': 0})
    (root / 'manifest.json').write_text(json.dumps(manifest))
    for case in CASES:
        (root / case).mkdir()
        record = dict(user_task_sha256='same-unit-prompt', rounds=[dict(usage=dict(input_tokens=count))])
        (root / case / 'record.json').write_text(json.dumps(record))
    return root


def test_paired_provider_accounting_and_rejections(tmp_path, monkeypatch):
    # Only the auditor is stubbed: no such fixtures are accepted by real audit_case.
    monkeypatch.setattr(metrics, 'audit_case', lambda folder, manifest: json.loads((folder/'record.json').read_text()))
    candidate_sha = 'a' * 40
    old = synthetic_run(tmp_path/'old', BASELINE_SHA, 100)
    new = synthetic_run(tmp_path/'new', candidate_sha, 60)
    result = metrics.compare_runs(old, new, candidate_sha)
    assert result['status'] == 'measured'
    assert result['reduction'] == .4
    assert result['actual_model_input_target_met'] is True
    path = new/'manifest.json'
    manifest = json.loads(path.read_text())
    for changed in [dict(cases=[]), dict(cases=CASES[:-1]), dict(cases=CASES+[CASES[0]]),
                    dict(model='different'), dict(parameters={'temperature': 1}),
                    dict(skill_dirty=True), dict(skill_sha='b'*40), dict(status='skipped')]:
        path.write_text(json.dumps(dict(manifest, **changed)))
        result = metrics.compare_runs(old, new, candidate_sha)
        assert result['status'] == 'unmeasured'
        assert result['actual_model_input_target_met'] is None
    path.write_text(json.dumps(manifest))
    (new/CASES[0]/'record.json').write_text(json.dumps(dict(user_task_sha256='different', rounds=[dict(usage=dict(input_tokens=60))])))
    assert metrics.compare_runs(old, new, candidate_sha)['status'] == 'unmeasured'
