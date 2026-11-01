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
        prompt_hashes = json.loads((Path(__file__).parent/'original-cohort.json').read_text())['cases']
        record = dict(user_task_sha256=prompt_hashes.get(case, 'new-targeted-unit-prompt'), rounds=[dict(usage=dict(input_tokens=count))])
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


def test_original_cohort_unchanged_by_four_new_cases(tmp_path, monkeypatch):
    from run_live_model_behavior import ORIGINAL_CASES, REGRESSION_BASELINE_SHA
    monkeypatch.setattr(metrics, 'audit_case', lambda folder, manifest: json.loads((folder/'record.json').read_text()))
    old = synthetic_run(tmp_path/'old', BASELINE_SHA, 100)
    new = synthetic_run(tmp_path/'new', 'a'*40, 60)
    for case in set(CASES)-set(ORIGINAL_CASES):
        (new/case/'record.json').write_text(json.dumps(dict(user_task_sha256='new-cohort', rounds=[dict(usage=dict(input_tokens=99999))])))
    result = metrics.compare_runs(old, new, 'a'*40)
    assert result['candidate_median'] == 60
    assert len(result['candidate_case_input_tokens']) == 12
    manifest = json.loads((old/'manifest.json').read_text())
    manifest.update(skill_sha=REGRESSION_BASELINE_SHA)
    (old/'manifest.json').write_text(json.dumps(manifest))
    assert metrics.compare_runs(old,new,'a'*40)['status'] == 'unmeasured'
    result = metrics.compare_runs(old,new,'a'*40,comparison='v109-regression')
    assert result['status'] == 'measured'
    assert result['actual_model_input_target_met'] is None
    assert result['target_reduction'] is None
    assert result['input_not_regressed'] is True


def test_twelve_baseline_and_sixteen_candidate_remain_comparable(tmp_path, monkeypatch):
    from run_live_model_behavior import ORIGINAL_CASES
    monkeypatch.setattr(metrics, 'audit_case', lambda folder, manifest: json.loads((folder/'record.json').read_text()))
    old = synthetic_run(tmp_path/'old', BASELINE_SHA, 100)
    new = synthetic_run(tmp_path/'new', 'a'*40, 70)
    path = old/'manifest.json'
    manifest = json.loads(path.read_text())
    manifest['cases'] = ORIGINAL_CASES
    path.write_text(json.dumps(manifest))
    assert metrics.compare_runs(old,new,'a'*40)['actual_model_input_target_met'] is True
    # Even a matching pair is invalid if both prompts departed from the frozen cohort.
    for root in (old,new):
        path = root/ORIGINAL_CASES[0]/'record.json'
        record = json.loads(path.read_text())
        record['user_task_sha256'] = 'same-but-not-original'
        path.write_text(json.dumps(record))
    assert metrics.compare_runs(old,new,'a'*40)['status'] == 'unmeasured'


def test_legacy_sixteen_and_new_twenty_eight_keep_original_twelve_target(tmp_path, monkeypatch):
    from run_live_model_behavior import LEGACY_CASES, ORIGINAL_CASES
    monkeypatch.setattr(metrics, 'audit_case', lambda folder, manifest: json.loads((folder/'record.json').read_text()))
    old = synthetic_run(tmp_path/'old', BASELINE_SHA, 100)
    new = synthetic_run(tmp_path/'new', 'a'*40, 70)
    path=old/'manifest.json'; manifest=json.loads(path.read_text())
    manifest['cases']=LEGACY_CASES; path.write_text(json.dumps(manifest))
    result=metrics.compare_runs(old,new,'a'*40)
    assert result['actual_model_input_target_met'] is True
    assert result['cohort'] == ORIGINAL_CASES
    assert len(result['candidate_case_input_tokens']) == 12


def test_mobile_metrics_separate_usage_from_device_or_token_target(tmp_path, monkeypatch):
    from run_live_model_behavior import MOBILE_CASES
    monkeypatch.setattr(metrics,'audit_case',lambda folder,manifest: json.loads((folder/'record.json').read_text()))
    root=synthetic_run(tmp_path/'mobile','a'*40,123)
    path=root/'manifest.json'; manifest=json.loads(path.read_text())
    manifest.update(tests_sha='b'*40,tests_dirty=False,cases=list(MOBILE_CASES))
    path.write_text(json.dumps(manifest))
    for case in MOBILE_CASES:
        p=root/case/'record.json'; record=json.loads(p.read_text());record['reads']=[dict(bytes=99)]
        p.write_text(json.dumps(record))
    result=metrics.measure_mobile_run(root,'a'*40)
    assert result['status']=='measured' and len(result['cases'])==12
    assert result['target_reduction'] is None and result['actual_model_input_target_met'] is None
    assert all(row['input_tokens']==123 and row['delivered_context_bytes']==99 for row in result['cases'])
    manifest['cases']=list(MOBILE_CASES)[:-1];path.write_text(json.dumps(manifest))
    assert metrics.measure_mobile_run(root,'a'*40)['status']=='unmeasured'
    assert metrics.measure_mobile_run(None,None)['status']=='unmeasured'
