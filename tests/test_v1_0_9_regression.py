"""Static release-contract checks; no claims about live model behavior."""
import re
import subprocess
from pathlib import Path

from conftest import PROJECT_ROOT, SKILL_DIR
from behavior_cases import CASES as NEW_CASES
from run_live_model_behavior import BASELINE_SHA, CASES


def test_release_version_and_manifest_budget():
    skill = (PROJECT_ROOT / 'SKILL.md').read_text()
    assert re.search(r'^\s*version:\s*1\.0\.9\s*$', skill, re.M)
    tracked = set(subprocess.check_output(['git','-C',str(PROJECT_ROOT),'ls-files'], text=True).splitlines())
    # Include untracked prospective release files, excluding git internals.
    extra = subprocess.check_output(['git','-C',str(PROJECT_ROOT),'ls-files','--others','--exclude-standard'], text=True).splitlines()
    packaged = tracked | set(extra)
    assert len(packaged) <= 200, f'{len(packaged)}/200 packaged files'
    baseline = set(subprocess.check_output(['git','-C',str(PROJECT_ROOT),'ls-tree','-r','--name-only',BASELINE_SHA], text=True).splitlines())
    new_knowledge = {p for p in packaged-baseline if p.startswith('references/') and p.endswith('.md')}
    assert new_knowledge == {'references/03_api_manual/05_descriptor/descriptor_heap.md'}


def test_twelve_cases_and_eight_distinct_new_rubrics():
    assert len(CASES) == len(set(CASES)) == 12
    assert len(NEW_CASES) == 8
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
