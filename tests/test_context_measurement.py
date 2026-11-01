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
    manifest = dict(layer='Live', status='generated', skill_sha=sha, skill_dirty=False, tests_sha='b'*40, tests_dirty=False, cases=CASES,
                    model='UNIT-MOCK-NOT-LIVE', parameters={'temperature': 0})
    (root / 'manifest.json').write_text(json.dumps(manifest))
    for case in CASES:
        (root / case).mkdir()
        prompt_hashes = json.loads((Path(__file__).parent/'v112-cohort.json').read_text())['cases']
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


def test_system_usage_is_audited_separate_and_rejects_incomplete_or_dirty(tmp_path, monkeypatch):
    from run_live_model_behavior import SYSTEM_CASES
    monkeypatch.setattr(metrics,'audit_case',lambda folder,manifest: json.loads((folder/'record.json').read_text()))
    root=synthetic_run(tmp_path/'system','a'*40,777)
    path=root/'manifest.json'; manifest=json.loads(path.read_text())
    manifest.update(tests_sha='b'*40,tests_dirty=False,cases=list(SYSTEM_CASES))
    for case in SYSTEM_CASES:
        p=root/case/'record.json'; record=json.loads(p.read_text()); record['reads']=[dict(bytes=123)]
        p.write_text(json.dumps(record))
    path.write_text(json.dumps(manifest))
    result=metrics.measure_system_run(root,'a'*40)
    assert result['status']=='measured' and len(result['cases'])==12
    assert result['cohort']=='system-12' and result['target_reduction'] is None
    assert result['actual_model_input_target_met'] is None
    assert all(row['input_tokens']==777 and row['delivered_context_bytes']==123 for row in result['cases'])
    for changes in [dict(cases=list(SYSTEM_CASES)[:-1]),dict(cases=list(SYSTEM_CASES)*2),
                    dict(tests_dirty=True),dict(skill_dirty=True),dict(layer='Snapshot'),
                    dict(status='skipped'),dict(tests_sha=''),dict(skill_sha='c'*40)]:
        path.write_text(json.dumps(dict(manifest,**changes)))
        assert metrics.measure_system_run(root,'a'*40)['status']=='unmeasured'
    assert metrics.measure_system_run(None,None)['status']=='unmeasured'


def test_historical_28_run_remains_valid_for_original_target(tmp_path, monkeypatch):
    from run_live_model_behavior import V111_CASES
    monkeypatch.setattr(metrics, 'audit_case', lambda folder, manifest: json.loads((folder/'record.json').read_text()))
    old=synthetic_run(tmp_path/'old28',BASELINE_SHA,100)
    new=synthetic_run(tmp_path/'new40','a'*40,70)
    p=old/'manifest.json'; manifest=json.loads(p.read_text());manifest['cases']=V111_CASES;p.write_text(json.dumps(manifest))
    result=metrics.compare_runs(old,new,'a'*40)
    assert result['actual_model_input_target_met'] is True
    assert len(result['candidate_case_input_tokens'])==12


def test_eng13_usage_is_separate_from_frozen_twelve_target(tmp_path,monkeypatch):
    from run_live_model_behavior import ENG13_CASES
    monkeypatch.setattr(metrics,'audit_case',lambda folder,manifest:json.loads((folder/'record.json').read_text()))
    root=synthetic_run(tmp_path/'eng13','a'*40,333)
    path=root/'manifest.json'; manifest=json.loads(path.read_text())
    manifest.update(tests_sha='b'*40,tests_dirty=False,cases=list(ENG13_CASES))
    for case in ENG13_CASES:
        p=root/case/'record.json';record=json.loads(p.read_text());record['reads']=[dict(bytes=55)]
        p.write_text(json.dumps(record))
    path.write_text(json.dumps(manifest))
    result=metrics.measure_eng13_run(root,'a'*40)
    assert result['status']=='measured' and len(result['cases'])==24
    assert result['cohort']=='eng13-24'
    assert result['target_reduction'] is None and result['actual_model_input_target_met'] is None
    assert all(row['input_tokens']==333 and row['delivered_context_bytes']==55 for row in result['cases'])
    for changes in [dict(cases=list(ENG13_CASES)[:-1]),dict(cases=list(ENG13_CASES)*2),
                    dict(skill_dirty=True),dict(tests_dirty=True),dict(status='skipped'),
                    dict(tests_sha=''),dict(skill_sha='c'*40)]:
        path.write_text(json.dumps(dict(manifest,**changes)))
        assert metrics.measure_eng13_run(root,'a'*40)['status']=='unmeasured'


def test_v112_regression_uses_frozen_forty_without_new_thirty_percent_target(tmp_path,monkeypatch):
    from run_live_model_behavior import V112_CASES
    monkeypatch.setattr(metrics,'audit_case',lambda folder,manifest:json.loads((folder/'record.json').read_text()))
    old=synthetic_run(tmp_path/'old40','d049afefaec8539cecca5f8e37c4cd66ec9da728',100)
    new=synthetic_run(tmp_path/'new64','a'*40,90)
    p=old/'manifest.json';manifest=json.loads(p.read_text());manifest['cases']=V112_CASES;p.write_text(json.dumps(manifest))
    result=metrics.compare_runs(old,new,'a'*40,comparison='v112-regression')
    assert result['status']=='measured' and result['cohort']==V112_CASES
    assert len(result['candidate_case_input_tokens'])==40
    assert result['actual_model_input_target_met'] is None and result['target_reduction'] is None
    assert result['input_not_regressed'] is True
    assert metrics.compare_runs(old,new,'a'*40)['status']=='unmeasured'
    # A matching pair of changed system prompts cannot replace the historical cohort.
    for root in (old,new):
        p=root/V112_CASES[-1]/'record.json';record=json.loads(p.read_text())
        record['user_task_sha256']='both-edited';p.write_text(json.dumps(record))
    assert metrics.compare_runs(old,new,'a'*40,comparison='v112-regression')['status']=='unmeasured'
