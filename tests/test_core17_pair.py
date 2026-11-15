"""Exact fixed Skill pairing; does not certify gates K/B/P."""
import json,subprocess
from pathlib import Path
from conftest import PROJECT_ROOT
ROOT=Path(__file__).parents[1]
def test_exact_skill_and_base_contract():
    c=json.loads((ROOT/'core17-candidate-contract.json').read_text())
    assert subprocess.check_output(['git','-C',str(PROJECT_ROOT),'rev-parse','HEAD'],text=True).strip()==c['skill_sha']
    assert c['release_status']=='BLOCKED' and c['new_prompts']==24 and c['equivalent_reuse']==0
    subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',c['tests_base_sha'],'HEAD'],check=True)
def test_independent_old_release_contract_not_relabelled():
    c=json.loads((ROOT/'release-contract.json').read_text())
    assert c['expected_version']=='1.0.16'
    assert c['skill_sha']=='416f4a6c0c887dee72bcc6dca13ce9c857d7957f'
def test_private_rubric_refused_as_runtime_context():
    import pytest
    from run_live_model_behavior import read_context
    with pytest.raises((ValueError,OSError)):
        read_context(ROOT,'tests/core17_rubrics.json',None)
