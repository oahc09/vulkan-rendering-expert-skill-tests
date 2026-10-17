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

from run_live_model_behavior import BASELINE_CONTEXT_FILES, BASELINE_SHA, SKILL_REPO, digest, read_context, CASES, audit_case


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
        if len(manifest['cases']) != 12 or set(manifest['cases']) != set(CASES):
            raise ValueError('Retrieval target requires all 12 unique cases')
        cases = []
        for case in manifest['cases']:
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


def compare_runs(baseline_run, candidate_run, candidate_sha):
    """Paired real-provider input usage, including every retrieval round."""
    unavailable = {'status': 'unmeasured', 'actual_model_input_target_met': None}
    if not baseline_run or not candidate_run:
        return dict(unavailable, reason='Two complete real model runs are required')
    if not candidate_sha or not re.fullmatch('[0-9a-f]{40}', candidate_sha):
        return dict(unavailable, reason='An explicit full candidate SHA is required')
    try:
        manifests = [json.loads((root / 'manifest.json').read_text()) for root in (baseline_run, candidate_run)]
        expected = [BASELINE_SHA, candidate_sha]
        totals = []
        for root, manifest, sha in zip((baseline_run, candidate_run), manifests, expected):
            if manifest.get('layer') != 'Live':
                raise ValueError('Only real live-run manifests are eligible')
            if manifest['status'] not in ('generated', 'gate_passed', 'gate_failed'):
                raise ValueError('Run is not complete')
            if manifest['skill_sha'] != sha or manifest['skill_dirty']:
                raise ValueError('Each run must use the exact clean pinned skill revision')
            if len(manifest['cases']) != len(CASES) or set(manifest['cases']) != set(CASES):
                raise ValueError('Both runs must contain exactly the same 12 unique cases')
            counts = {}
            for case in CASES:
                record = audit_case(root / case, manifest)
                counts[case] = sum(step['usage']['input_tokens'] for step in record['rounds'])
                if counts[case] <= 0:
                    raise ValueError('Positive actual provider input usage is required')
            totals.append(counts)
        if manifests[0]['model'] != manifests[1]['model'] or manifests[0]['parameters'] != manifests[1]['parameters']:
            raise ValueError('Model and inference parameters must match exactly')
        for case in CASES:
            old = json.loads((baseline_run / case / 'record.json').read_text())
            new = json.loads((candidate_run / case / 'record.json').read_text())
            if old['user_task_sha256'] != new['user_task_sha256']:
                raise ValueError('Paired user prompt hashes must match')
        old_median, new_median = (statistics.median(counts.values()) for counts in totals)
        reduction = 1 - new_median / old_median
        return {'status': 'measured', 'metric': 'median_total_provider_input_tokens_per_case_all_rounds',
                'baseline_sha': BASELINE_SHA, 'candidate_sha': candidate_sha,
                'model': manifests[0]['model'], 'parameters': manifests[0]['parameters'],
                'baseline_median': old_median, 'candidate_median': new_median,
                'reduction': reduction, 'target_reduction': 0.30,
                'actual_model_input_target_met': reduction >= .30,
                'baseline_case_input_tokens': totals[0], 'candidate_case_input_tokens': totals[1],
                'semantic_acceptance': 'Separate rubric review required; token savings alone do not establish answer quality'}
    except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
        return dict(unavailable, reason=f'Invalid or incomplete comparison evidence: {type(exc).__name__}: {exc}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-root', type=Path, default=SKILL_REPO)
    parser.add_argument('--encoding', default='o200k_base')
    parser.add_argument('--live-run', type=Path)
    parser.add_argument('--baseline-run', type=Path)
    parser.add_argument('--candidate-run', type=Path)
    parser.add_argument('--candidate-sha')
    args = parser.parse_args()
    if args.baseline_run or args.candidate_run:
        result = compare_runs(args.baseline_run, args.candidate_run, args.candidate_sha)
    else:
        result = measure(args.skill_root, args.encoding, args.live_run)
    print(json.dumps(result, indent=2))
