"""Static release-contract checks; no claims about live model behavior."""
import re
import subprocess
from pathlib import Path

from conftest import PROJECT_ROOT, SKILL_DIR
from behavior_cases import CASES as NEW_CASES
from run_live_model_behavior import BASELINE_SHA, CASES


def test_release_version_and_manifest_budget(tmp_path):
    import json
    import sys
    import importlib.util
    contract = json.loads((Path(__file__).parent.parent / 'release-contract.json').read_text())
    sha = subprocess.check_output(['git','-C',str(PROJECT_ROOT),'rev-parse','HEAD'], text=True).strip()
    assert re.fullmatch('[0-9a-f]{40}', contract['skill_sha']), 'Pin a reviewed full candidate SHA before release'
    assert sha == contract['skill_sha']
    skill = (PROJECT_ROOT / 'SKILL.md').read_text()
    assert re.search(r'^\s*version:\s*' + re.escape(contract['expected_version']) + r'\s*$', skill, re.M)
    sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
    try:
        spec = importlib.util.spec_from_file_location('candidate_packer', PROJECT_ROOT / 'scripts/agensi_audit_and_pack.py')
        packer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packer)
        report = packer.check(PROJECT_ROOT, tmp_path / 'candidate.zip')
    finally:
        sys.path.pop(0)
    assert report['status'] == 'PASS', report
    assert report['revision'] == sha
    packaged = {item['path'] for item in report['files']}
    tracked = set(subprocess.check_output(['git','-C',str(PROJECT_ROOT),'ls-files'], text=True).splitlines())
    assert report['tracked_files'] == len(tracked)
    assert report['package_files'] == len(packaged) <= contract['max_runtime_files']
    assert packaged == {p for p in tracked if p in packer.REQUIRED or p.startswith('references/')}
    assert report['zip']['crc_verified']
    baseline = set(subprocess.check_output(['git','-C',str(PROJECT_ROOT),'ls-tree','-r','--name-only',contract['knowledge_baseline_sha']], text=True).splitlines())
    expected_knowledge = {p for p in baseline if p.startswith('references/')} | set(contract['allowed_new_knowledge'])
    assert {p for p in tracked if p.startswith('references/')} == expected_knowledge


def test_eighty_four_cases_and_eighty_rubrics():
    assert len(CASES) == len(set(CASES)) == 84
    assert len(NEW_CASES) == 80
    assert set(NEW_CASES) == set(CASES[4:])
    for case in CASES:
        assert (Path(__file__).parent / 'prompts' / f'{case}.txt').is_file()
    for spec in NEW_CASES.values():
        assert len(spec['rubric']) > 100
        assert len(spec['required']) >= 2


def test_descriptor_heap_has_explicit_size_stride_and_authority():
    text = (SKILL_DIR / '03_api_manual/05_descriptor/descriptor_heap.md').read_text()
    for token in ['VK_EXT_descriptor_heap', 'heapArrayStride', '8', '16']:
        assert token in text
    assert 'https://' in text
    assert '[SPEC]' in text or '[REGISTRY]' in text
