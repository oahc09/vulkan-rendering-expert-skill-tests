#!/usr/bin/env python3
"""Separate immutable legacy16 and reconstructed CORE17 gates; never blend pins."""
import argparse,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LEGACY_PIN_ONLY=['test_v1_0_8_project_diagnosis.py::test_current_version_and_preserved_project_diagnosis_routing', 'test_v1_0_9_regression.py::test_release_version_and_manifest_budget']
CORE_FILES=['test_core17_inventory.py','test_v1_0_17_registry.py','test_core17_pair.py','test_core17_ci.py']

def select(cohort,root=ROOT):
    if cohort not in ('legacy16','core17'):raise ValueError('unknown cohort')
    name='release-contract.json' if cohort=='legacy16' else 'core17-candidate-contract.json'
    c=json.loads((root/name).read_text());sha=c['skill_sha']
    if not re.fullmatch('[0-9a-f]{40}',sha):raise ValueError('immutable reviewed SHA required')
    expected='1.0.16' if cohort=='legacy16' else '1.0.17-reconstructed-tests'
    if c.get('expected_version',c.get('candidate_version'))!=expected:raise ValueError('wrong cohort contract')
    if cohort=='core17' and c['release_status']!='BLOCKED':raise ValueError('reconstruction not certified')
    return sha

def test_args(cohort):
    if cohort=='legacy16':
        return ['-m','static',str(ROOT/'tests'),*[f'--ignore={ROOT}/tests/{f}' for f in CORE_FILES]]
    if cohort=='core17':return ['-m','static',str(ROOT/'tests'),*[f'--deselect={node}' for node in LEGACY_PIN_ONLY]]
    raise ValueError('unknown cohort')

def check_pair(cohort,skill):
    expected=select(cohort)
    actual=subprocess.check_output(['git','-C',str(skill),'rev-parse','HEAD'],text=True).strip()
    if actual!=expected:raise ValueError('wrong exact Skill pair')
    if subprocess.check_output(['git','-C',str(skill),'status','--porcelain','--untracked-files=all'],text=True).strip():raise ValueError('dirty Skill checkout')
    flags=subprocess.check_output(['git','-C',str(skill),'ls-files','-v'],text=True).splitlines()
    if any(x and (x[0].islower() or x[0]=='S') for x in flags):raise ValueError('hidden index flags')
    return actual

def main(argv=None):
    import os
    p=argparse.ArgumentParser();p.add_argument('--cohort',choices=['legacy16','core17'],required=True);p.add_argument('--resolve',action='store_true');p.add_argument('--skill',type=Path)
    a=p.parse_args(argv)
    if a.resolve:print(select(a.cohort));return 0
    if not a.skill:p.error('--skill required unless --resolve')
    check_pair(a.cohort,a.skill)
    env=dict(os.environ,VULKAN_SKILL_ROOT=str(a.skill.resolve()))
    return subprocess.run([sys.executable,'-m','pytest','-q','-c',str(ROOT/'tests/pytest.ini'),*test_args(a.cohort)],env=env,timeout=300).returncode
if __name__=='__main__':raise SystemExit(main())
