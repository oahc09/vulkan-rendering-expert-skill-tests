#!/usr/bin/env python3
"""Measure tokenized loading, never substitute bytes/characters for tokens.

Startup compares historical fixed-eight-file load to current SKILL.md entry.
A live read-record measures unique delivered sections, not billed conversation
input tokens. These are separate metrics; startup reduction is not live savings.
"""
import argparse
import json
import subprocess
import statistics
import re
from pathlib import Path

from run_live_model_behavior import BASELINE_CONTEXT_FILES, BASELINE_SHA, SKILL_REPO, digest, read_context, CASES, ORIGINAL_CASES, LEGACY_CASES, MOBILE_CASES, SYSTEM_CASES, ENG13_CASES, VIS14_CASES, TRAN15_CASES, SIM16_CASES, V115_CASES, V114_CASES, V113_CASES, V111_CASES, V112_CASES, REGRESSION_BASELINE_SHA, audit_case


def measure(root, encoding_name, run=None):
    try:
        import tiktoken
    except ImportError:
        return {'status': 'unmeasured', 'reason': 'Install tiktoken to measure tokens; no percentage claimed',
                'target_reduction': 0.30, 'target_met': None}
    encoding = tiktoken.get_encoding(encoding_name)
    baseline = ''.join(subprocess.check_output(['git', '-C', str(root), 'show', f'{BASELINE_SHA}:{path}']).decode('utf-8')
                       for path in BASELINE_CONTEXT_FILES)
    current = (root / 'SKILL.md').read_text(encoding='utf-8')
    old_tokens = len(encoding.encode(baseline))
    new_tokens = len(encoding.encode(current))
    result = {'status': 'measured', 'metric': 'startup_context_tokens_excluding_prompt_wrappers',
              'encoding': encoding_name, 'baseline_sha': BASELINE_SHA,
              'current_sha': subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'], text=True).strip(),
              'baseline_context_sha256': digest(baseline), 'current_context_sha256': digest(current),
              'baseline_tokens': old_tokens, 'current_tokens': new_tokens,
              'startup_reduction': 1 - new_tokens / old_tokens, 'target_reduction': 0.30,
              'startup_target_met': new_tokens <= old_tokens * 0.70,
              'retrieval_context_target_met': None, 'actual_model_input_target_met': None, 'live_status': 'unmeasured'}
    if run:
        manifest = json.loads((run / 'manifest.json').read_text())
        if manifest['status'] not in ('generated', 'gate_passed', 'gate_failed'):
            raise ValueError('Cannot measure an incomplete or skipped live run')
        if len(manifest['cases']) != len(set(manifest['cases'])) or set(manifest['cases']) not in (set(ORIGINAL_CASES), set(LEGACY_CASES), set(V111_CASES), set(V112_CASES), set(V113_CASES), set(V114_CASES), set(V115_CASES), set(CASES)):
            raise ValueError('Retrieval target requires all 12 unique cases')
        cases = []
        for case in ORIGINAL_CASES:
            record = audit_case(run / case, manifest)
            assert record['status'] == 'generated'
            sections = []
            for read in record['reads']:
                text, current_read = read_context(root, read['path'], read['section'])
                if current_read['file_sha256'] != read['file_sha256'] or digest(text) != read['content_sha256']:
                    raise ValueError('Source changed since live read; cannot reconstruct token counts')
                sections.append(text)
            tokens = len(encoding.encode(''.join(sections)))
            cases.append({'case': case, 'loaded_context_tokens': tokens, 'reduction_vs_old_fixed_load': 1-tokens/old_tokens})
        result.update(live_status='measured', live_cases=cases,
                      retrieval_context_target_met=all(c['reduction_vs_old_fixed_load'] >= .30 for c in cases))
    return result


def compare_runs(baseline_run, candidate_run, candidate_sha, *, comparison="v108-target"):
    """Paired provider usage for the explicitly selected frozen historical cohort."""
    baseline_sha = BASELINE_SHA if comparison == "v108-target" else ('8d62f861b4ead27699e2ff3d80a1a9f0e72a4968' if comparison == "v113-regression" else ('d049afefaec8539cecca5f8e37c4cd66ec9da728' if comparison == "v112-regression" else REGRESSION_BASELINE_SHA))
    if comparison not in ("v108-target", "v109-regression", "v112-regression", "v113-regression"):
        raise ValueError("Unknown comparison cohort")
    cohort = V113_CASES if comparison == "v113-regression" else V112_CASES if comparison == "v112-regression" else ORIGINAL_CASES
    unavailable = {'status': 'unmeasured', 'actual_model_input_target_met': None}
    if not baseline_run or not candidate_run:
        return dict(unavailable, reason='Two complete real model runs are required')
    if not candidate_sha or not re.fullmatch('[0-9a-f]{40}', candidate_sha):
        return dict(unavailable, reason='An explicit full candidate SHA is required')
    try:
        manifests = [json.loads((root / 'manifest.json').read_text()) for root in (baseline_run, candidate_run)]
        expected = [baseline_sha, candidate_sha]
        totals = []
        for root, manifest, sha in zip((baseline_run, candidate_run), manifests, expected):
            if manifest.get('layer') != 'Live':
                raise ValueError('Only real live-run manifests are eligible')
            if manifest['status'] not in ('generated', 'gate_passed', 'gate_failed'):
                raise ValueError('Run is not complete')
            if manifest['skill_sha'] != sha or manifest['skill_dirty']:
                raise ValueError('Each run must use the exact clean pinned skill revision')
            if len(manifest['cases']) != len(set(manifest['cases'])) or set(manifest['cases']) not in (set(ORIGINAL_CASES), set(LEGACY_CASES), set(V111_CASES), set(V112_CASES), set(V113_CASES), set(V114_CASES), set(V115_CASES), set(CASES)):
                raise ValueError('Run must contain a complete supported unique case cohort')
            if not set(cohort) <= set(manifest['cases']):
                raise ValueError('Comparison cohort missing from run')
            if comparison in ('v112-regression', 'v113-regression') and (manifest.get('tests_dirty') is not False or not re.fullmatch('[0-9a-f]{40}', manifest.get('tests_sha',''))):
                raise ValueError('v1.0.12 regression requires clean tests provenance')
            counts = {}
            for case in cohort:
                record = audit_case(root / case, manifest)
                counts[case] = sum(step['usage']['input_tokens'] for step in record['rounds'])
                if counts[case] <= 0:
                    raise ValueError('Positive actual provider input usage is required')
            totals.append(counts)
        if manifests[0]['model'] != manifests[1]['model'] or manifests[0]['parameters'] != manifests[1]['parameters']:
            raise ValueError('Model and inference parameters must match exactly')
        frozen = json.loads((Path(__file__).parent/('v113-cohort.json' if comparison == 'v113-regression' else 'v112-cohort.json' if comparison == 'v112-regression' else 'original-cohort.json')).read_text())['cases']
        for case in cohort:
            old = json.loads((baseline_run / case / 'record.json').read_text())
            new = json.loads((candidate_run / case / 'record.json').read_text())
            if old['user_task_sha256'] != new['user_task_sha256'] or old['user_task_sha256'] != frozen[case]:
                raise ValueError('Paired user prompt hashes must match')
        old_median, new_median = (statistics.median(counts.values()) for counts in totals)
        reduction = 1 - new_median / old_median
        return {'status': 'measured', 'metric': 'median_total_provider_input_tokens_per_case_all_rounds',
                'baseline_sha': baseline_sha, 'candidate_sha': candidate_sha, 'comparison': comparison,
                'baseline_tests_sha': manifests[0].get('tests_sha'), 'candidate_tests_sha': manifests[1].get('tests_sha'),
                'cohort': cohort, 'targeted_cases': 'Separate semantic cohort; excluded from token target',
                'eng13_cases': 'Independent 24-case usage; excluded from previous cohort denominators',
                'mobile_cases': 'Separate mobile cohort; excluded from original 12 denominator',
                'model': manifests[0]['model'], 'parameters': manifests[0]['parameters'],
                'baseline_median': old_median, 'candidate_median': new_median,
                'reduction': reduction, 'target_reduction': .30 if comparison == 'v108-target' else None,
                'actual_model_input_target_met': reduction >= .30 if comparison == 'v108-target' else None,
                'input_not_regressed': new_median <= old_median,
                'baseline_case_input_tokens': totals[0], 'candidate_case_input_tokens': totals[1],
                'semantic_acceptance': 'Separate rubric review required; token savings alone do not establish answer quality'}
    except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
        return dict(unavailable, reason=f'Invalid or incomplete comparison evidence: {type(exc).__name__}: {exc}')


def measure_mobile_run(run, candidate_sha):
    """Audited mobile usage only; no baseline or inherited 30% target."""
    unavailable = dict(status='unmeasured', cohort='mobile-12', target_reduction=None,
                       actual_model_input_target_met=None)
    if not run or not candidate_sha or not re.fullmatch('[0-9a-f]{40}', candidate_sha):
        return dict(unavailable, reason='Mobile run and explicit full candidate SHA required')
    try:
        manifest = json.loads((run/'manifest.json').read_text())
        if (manifest.get('layer') != 'Live' or manifest.get('status') not in ('generated', 'gate_passed', 'gate_failed')
                or manifest.get('skill_sha') != candidate_sha or manifest.get('skill_dirty') is not False
                or manifest.get('tests_dirty') is not False or not re.fullmatch('[0-9a-f]{40}', manifest.get('tests_sha',''))):
            raise ValueError('Complete clean SHA-bound Live evidence required')
        cases = manifest['cases']
        if len(cases) != len(set(cases)) or set(cases) not in (set(MOBILE_CASES), set(V111_CASES), set(V112_CASES), set(V113_CASES), set(V114_CASES), set(V115_CASES), set(CASES)):
            raise ValueError('All twelve mobile cases required, alone or within a complete supported release cohort/40')
        rows = []
        for case in MOBILE_CASES:
            record = audit_case(run/case, manifest)
            tokens = sum(step['usage']['input_tokens'] for step in record['rounds'])
            if tokens <= 0:
                raise ValueError('Positive provider input usage required')
            rows.append(dict(case=case, input_tokens=tokens, rounds=len(record['rounds']),
                             delivered_context_bytes=sum(read['bytes'] for read in record['reads'])))
        return dict(unavailable, status='measured', skill_sha=candidate_sha, tests_sha=manifest['tests_sha'],
                    model=manifest['model'], parameters=manifest['parameters'], cases=rows,
                    semantic_acceptance='Separate human review required; no device or performance acceptance')
    except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
        return dict(unavailable, reason=f'Invalid mobile evidence: {type(exc).__name__}: {exc}')


def measure_system_run(run, candidate_sha):
    """Audited system usage only; no baseline or inherited 30% target."""
    unavailable = dict(status='unmeasured', cohort='system-12', target_reduction=None,
                       actual_model_input_target_met=None)
    if not run or not candidate_sha or not re.fullmatch('[0-9a-f]{40}', candidate_sha):
        return dict(unavailable, reason='System run and explicit full candidate SHA required')
    try:
        manifest = json.loads((run/'manifest.json').read_text())
        if (manifest.get('layer') != 'Live' or manifest.get('status') not in ('generated', 'gate_passed', 'gate_failed')
                or manifest.get('skill_sha') != candidate_sha or manifest.get('skill_dirty') is not False
                or manifest.get('tests_dirty') is not False or not re.fullmatch('[0-9a-f]{40}', manifest.get('tests_sha',''))):
            raise ValueError('Complete clean SHA-bound Live evidence required')
        cases = manifest['cases']
        if len(cases) != len(set(cases)) or set(cases) not in (set(SYSTEM_CASES), set(V112_CASES), set(V113_CASES), set(V114_CASES), set(V115_CASES), set(CASES)):
            raise ValueError('All twelve system cases required, alone or within a complete supported release cohort')
        rows = []
        for case in SYSTEM_CASES:
            record = audit_case(run/case, manifest)
            tokens = sum(step['usage']['input_tokens'] for step in record['rounds'])
            if tokens <= 0:
                raise ValueError('Positive provider input usage required')
            rows.append(dict(case=case, input_tokens=tokens, rounds=len(record['rounds']),
                             delivered_context_bytes=sum(read['bytes'] for read in record['reads'])))
        return dict(unavailable, status='measured', skill_sha=candidate_sha, tests_sha=manifest['tests_sha'],
                    model=manifest['model'], parameters=manifest['parameters'], cases=rows,
                    semantic_acceptance='Separate human review required; no device or performance acceptance')
    except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
        return dict(unavailable, reason=f'Invalid system evidence: {type(exc).__name__}: {exc}')


def measure_eng13_run(run, candidate_sha):
    """Audited ENG13 usage only; no baseline or inherited 30% target."""
    unavailable = dict(status='unmeasured', cohort='eng13-24', target_reduction=None,
                       actual_model_input_target_met=None)
    if not run or not candidate_sha or not re.fullmatch('[0-9a-f]{40}', candidate_sha):
        return dict(unavailable, reason='ENG13 run and explicit full candidate SHA required')
    try:
        manifest = json.loads((run/'manifest.json').read_text())
        if (manifest.get('layer') != 'Live' or manifest.get('status') not in ('generated', 'gate_passed', 'gate_failed')
                or manifest.get('skill_sha') != candidate_sha or manifest.get('skill_dirty') is not False
                or manifest.get('tests_dirty') is not False or not re.fullmatch('[0-9a-f]{40}', manifest.get('tests_sha',''))):
            raise ValueError('Complete clean SHA-bound Live evidence required')
        cases = manifest['cases']
        if len(cases) != len(set(cases)) or set(cases) not in (set(ENG13_CASES), set(V113_CASES), set(V114_CASES), set(V115_CASES), set(CASES)):
            raise ValueError('All 24 ENG13 cases required, alone or within a full64/full84 run')
        rows = []
        for case in ENG13_CASES:
            record = audit_case(run/case, manifest)
            tokens = sum(step['usage']['input_tokens'] for step in record['rounds'])
            if tokens <= 0:
                raise ValueError('Positive provider input usage required')
            rows.append(dict(case=case, input_tokens=tokens, rounds=len(record['rounds']),
                             delivered_context_bytes=sum(read['bytes'] for read in record['reads'])))
        return dict(unavailable, status='measured', skill_sha=candidate_sha, tests_sha=manifest['tests_sha'],
                    model=manifest['model'], parameters=manifest['parameters'], cases=rows,
                    semantic_acceptance='Separate human review required; no device or performance acceptance')
    except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
        return dict(unavailable, reason=f'Invalid ENG13 evidence: {type(exc).__name__}: {exc}')


def measure_vis14_run(run, candidate_sha):
    """Audited VIS14 usage only; no baseline or inherited 30% target."""
    unavailable = dict(status='unmeasured', cohort='vis14-20', target_reduction=None,
                       actual_model_input_target_met=None)
    if not run or not candidate_sha or not re.fullmatch('[0-9a-f]{40}', candidate_sha):
        return dict(unavailable, reason='VIS14 run and explicit full candidate SHA required')
    try:
        manifest = json.loads((run/'manifest.json').read_text())
        if (manifest.get('layer') != 'Live' or manifest.get('status') not in ('generated', 'gate_passed', 'gate_failed')
                or manifest.get('skill_sha') != candidate_sha or manifest.get('skill_dirty') is not False
                or manifest.get('tests_dirty') is not False or not re.fullmatch('[0-9a-f]{40}', manifest.get('tests_sha',''))):
            raise ValueError('Complete clean SHA-bound Live evidence required')
        cases = manifest['cases']
        if len(cases) != len(set(cases)) or set(cases) not in (set(VIS14_CASES), set(V114_CASES), set(V115_CASES), set(CASES)):
            raise ValueError('All 20 VIS14 cases required, alone or within a full84 run')
        rows = []
        for case in VIS14_CASES:
            record = audit_case(run/case, manifest)
            tokens = sum(step['usage']['input_tokens'] for step in record['rounds'])
            if tokens <= 0:
                raise ValueError('Positive provider input usage required')
            rows.append(dict(case=case, input_tokens=tokens, rounds=len(record['rounds']),
                             delivered_context_bytes=sum(read['bytes'] for read in record['reads'])))
        return dict(unavailable, status='measured', skill_sha=candidate_sha, tests_sha=manifest['tests_sha'],
                    model=manifest['model'], parameters=manifest['parameters'], cases=rows,
                    semantic_acceptance='Separate human review required; no device or performance acceptance')
    except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
        return dict(unavailable, reason=f'Invalid VIS14 evidence: {type(exc).__name__}: {exc}')


def measure_tran15_run(run, candidate_sha):
    """Audited TRAN15 usage only; no baseline or inherited 30% target."""
    unavailable = dict(status='unmeasured', cohort='tran15-20', target_reduction=None,
                       actual_model_input_target_met=None)
    if not run or not candidate_sha or not re.fullmatch('[0-9a-f]{40}', candidate_sha):
        return dict(unavailable, reason='TRAN15 run and explicit full candidate SHA required')
    try:
        manifest = json.loads((run/'manifest.json').read_text())
        if (manifest.get('layer') != 'Live' or manifest.get('status') not in ('generated', 'gate_passed', 'gate_failed')
                or manifest.get('skill_sha') != candidate_sha or manifest.get('skill_dirty') is not False
                or manifest.get('tests_dirty') is not False or not re.fullmatch('[0-9a-f]{40}', manifest.get('tests_sha',''))):
            raise ValueError('Complete clean SHA-bound Live evidence required')
        cases = manifest['cases']
        if len(cases) != len(set(cases)) or set(cases) not in (set(TRAN15_CASES), set(CASES)):
            raise ValueError('All 20 TRAN15 cases required, alone or within a full104 run')
        rows = []
        for case in TRAN15_CASES:
            record = audit_case(run/case, manifest)
            tokens = sum(step['usage']['input_tokens'] for step in record['rounds'])
            if tokens <= 0:
                raise ValueError('Positive provider input usage required')
            rows.append(dict(case=case, input_tokens=tokens, rounds=len(record['rounds']),
                             delivered_context_bytes=sum(read['bytes'] for read in record['reads'])))
        return dict(unavailable, status='measured', skill_sha=candidate_sha, tests_sha=manifest['tests_sha'],
                    model=manifest['model'], parameters=manifest['parameters'], cases=rows,
                    semantic_acceptance='Separate human review required; no device or performance acceptance')
    except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
        return dict(unavailable, reason=f'Invalid TRAN15 evidence: {type(exc).__name__}: {exc}')


def measure_sim16_run(run, candidate_sha):
    """Audited SIM16 usage only; no baseline or inherited 30% target."""
    unavailable = dict(status='unmeasured', cohort='sim16-16', target_reduction=None,
                       actual_model_input_target_met=None)
    if not run or not candidate_sha or not re.fullmatch('[0-9a-f]{40}', candidate_sha):
        return dict(unavailable, reason='SIM16 run and explicit full candidate SHA required')
    try:
        manifest = json.loads((run/'manifest.json').read_text())
        if (manifest.get('layer') != 'Live' or manifest.get('status') not in ('generated', 'gate_passed', 'gate_failed')
                or manifest.get('skill_sha') != candidate_sha or manifest.get('skill_dirty') is not False
                or manifest.get('tests_dirty') is not False or not re.fullmatch('[0-9a-f]{40}', manifest.get('tests_sha',''))):
            raise ValueError('Complete clean SHA-bound Live evidence required')
        cases = manifest['cases']
        if len(cases) != len(set(cases)) or set(cases) not in (set(SIM16_CASES), set(CASES)):
            raise ValueError('All 16 SIM16 cases required, alone or within a full120 run')
        rows = []
        for case in SIM16_CASES:
            record = audit_case(run/case, manifest)
            tokens = sum(step['usage']['input_tokens'] for step in record['rounds'])
            if tokens <= 0:
                raise ValueError('Positive provider input usage required')
            rows.append(dict(case=case, input_tokens=tokens, rounds=len(record['rounds']),
                             delivered_context_bytes=sum(read['bytes'] for read in record['reads'])))
        return dict(unavailable, status='measured', skill_sha=candidate_sha, tests_sha=manifest['tests_sha'],
                    model=manifest['model'], parameters=manifest['parameters'], cases=rows,
                    semantic_acceptance='Separate human review required; no device or performance acceptance')
    except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
        return dict(unavailable, reason=f'Invalid SIM16 evidence: {type(exc).__name__}: {exc}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-root', type=Path, default=SKILL_REPO)
    parser.add_argument('--encoding', default='o200k_base')
    parser.add_argument('--live-run', type=Path)
    parser.add_argument('--baseline-run', type=Path)
    parser.add_argument('--candidate-run', type=Path)
    parser.add_argument('--candidate-sha')
    parser.add_argument('--mobile-run', type=Path)
    parser.add_argument('--system-run', type=Path)
    parser.add_argument('--eng13-run', type=Path)
    parser.add_argument('--vis14-run', type=Path)
    parser.add_argument('--sim16-run', type=Path)
    parser.add_argument('--tran15-run', type=Path)
    parser.add_argument('--comparison', choices=['v108-target','v109-regression','v112-regression','v113-regression'], default='v108-target')
    args = parser.parse_args()
    if args.sim16_run:
        result = measure_sim16_run(args.sim16_run, args.candidate_sha)
    elif args.tran15_run:
        result = measure_tran15_run(args.tran15_run, args.candidate_sha)
    elif args.vis14_run:
        result = measure_vis14_run(args.vis14_run, args.candidate_sha)
    elif args.eng13_run:
        result = measure_eng13_run(args.eng13_run, args.candidate_sha)
    elif args.system_run:
        result = measure_system_run(args.system_run, args.candidate_sha)
    elif args.mobile_run:
        result = measure_mobile_run(args.mobile_run, args.candidate_sha)
    elif args.baseline_run or args.candidate_run:
        result = compare_runs(args.baseline_run, args.candidate_run, args.candidate_sha, comparison=args.comparison)
    else:
        result = measure(args.skill_root, args.encoding, args.live_run)
    print(json.dumps(result, indent=2))
