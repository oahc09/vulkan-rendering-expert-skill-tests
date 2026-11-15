"""Offline exact-pair/ancestry check. No network and no release certification."""
import argparse
import json
import re
import subprocess
from pathlib import Path


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()


def inspect_pair(skill, tests, *, tests_main):
    contract = json.loads((Path(tests) / 'text18-candidate-contract.json').read_text())
    for sha in (contract['skill_sha'], contract['tests_base_sha'], tests_main):
        if not re.fullmatch('[0-9a-f]{40}', sha):
            raise ValueError('full immutable commit SHA required')
    head = git(tests, 'rev-parse', 'HEAD')
    skill_head = git(skill, 'rev-parse', 'HEAD')
    errors = []
    if skill_head != contract['skill_sha']:
        errors.append('SKILL_SHA_MISMATCH')
    for root in (skill, tests):
        if git(root, 'rev-parse', '--is-shallow-repository') != 'false':
            raise ValueError('shallow history cannot prove ancestry')
        if git(root, 'status', '--porcelain', '--untracked-files=all', '--ignore-submodules=none'):
            if 'DIRTY_CHECKOUT' not in errors: errors.append('DIRTY_CHECKOUT')
        # Git flags can deliberately hide tracked changes from status/diff.
        flags = git(root, 'ls-files', '-v').splitlines()
        if any(line and (line[0].islower() or line[0] == 'S') for line in flags):
            if 'HIDDEN_INDEX_FLAGS' not in errors: errors.append('HIDDEN_INDEX_FLAGS')
        if any(line.startswith('160000 ') for line in git(root, 'ls-files', '--stage').splitlines()):
            if 'SUBMODULE_NOT_VERIFIED' not in errors: errors.append('SUBMODULE_NOT_VERIFIED')
    def ancestor(a, b):
        # Verify existence first: missing/shallow history is not evidence of exclusion.
        git(tests, 'cat-file', '-e', a + '^{commit}')
        git(tests, 'cat-file', '-e', b + '^{commit}')
        p = subprocess.run(['git', '-C', str(tests), 'merge-base', '--is-ancestor', a, b], capture_output=True)
        if p.returncode not in (0, 1):
            raise ValueError('ancestry unavailable')
        return p.returncode == 0
    base = contract['tests_base_sha']
    if not ancestor(base, head):
        errors.append('BASE_NOT_ANCESTOR')
    stacked = not ancestor(base, tests_main)
    return {'schema': 1, 'skill_sha': skill_head, 'tests_sha': head,
            'tests_main_sha': tests_main, 'tests_base_sha': base,
            'pair_status': 'FAIL' if errors else 'PASS', 'errors': errors,
            'stacked_base_not_in_main': stacked,
            'release_status': 'BLOCKED',
            'unclosed': contract['unclosed']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--skill', required=True, type=Path)
    p.add_argument('--tests', required=True, type=Path)
    p.add_argument('--tests-main-sha', required=True, help='explicit locally verified main snapshot; no live freshness claim')
    args = p.parse_args()
    result = inspect_pair(args.skill, args.tests, tests_main=args.tests_main_sha)
    print(json.dumps(result, indent=2))
    return 0 if result['pair_status'] == 'PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())
