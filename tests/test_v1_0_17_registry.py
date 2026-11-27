"""Reconstructed plan §9.2 task registry, not API registry or Live certification."""
import hashlib,json,importlib.util,sys
from pathlib import Path
import pytest
BASE=Path(__file__).parent

def load(name):return json.loads((BASE/name).read_text())

def test_closed_loop_plan_task_mapping():
    cases=load('core17_cases.json');rubrics=load('core17_rubrics.json')
    assert len(cases)==24 and set(cases)==set(rubrics)
    assert {x['id'] for x in cases.values()}=={f'CORE17-{i:02d}' for i in range(1,25)}
    for key,c in cases.items():
        assert c['provenance'].startswith('reconstructed-')
        assert (BASE/'prompts'/f'{key}.txt').read_text()==c['prompt']
        assert set(c['variants'])=={'primary','contrast'} and all(c['variants'].values())
        r=rubrics[key];assert r['evaluator_only'] is True
        assert all(r[x] for x in ['normal','capability_missing','failure_recovery'])
        assert 'normal' not in c and 'required' not in c and 'rubric' not in c
    assert sum(bool(c['legacy_links']) for c in cases.values())==6
    assert all(c['legacy_equivalence']=='partial-not-equivalent' for c in cases.values() if c['legacy_links'])

def test_legacy_120_byte_frozen():
    manifest=load('core17-baseline-hashes.json');assert len(manifest['cases'])==120
    for key,sha in manifest['cases'].items():assert hashlib.sha256((BASE/'prompts'/f'{key}.txt').read_bytes()).hexdigest()==sha
    assert manifest['new_count']==24 and manifest['equivalent_reuse_count']==0
    assert all(key in manifest['cases'] for c in load('core17_cases.json').values() for key in c['legacy_links'])

def test_adapter_rejects_old_acceptance_gate_and_uses_only_cases(monkeypatch):
    sys.path.insert(0,str(BASE))
    try:
        import run_core17_live as adapter
        with pytest.raises(ValueError,match='independent semantic'):adapter.main(['--check'])
        captured={}
        monkeypatch.setattr(adapter.runner,'main',lambda args:captured.update(args=args,cases=list(adapter.runner.CASES)) or 0)
        old=adapter.runner.CASES;out=adapter.runner.DEFAULT_OUT
        try:
            assert adapter.main(['--help'])==0
            assert captured['cases']==list(load('core17_cases.json'))
        finally:adapter.runner.CASES=old;adapter.runner.DEFAULT_OUT=out
        assert 'core17_rubrics' not in (BASE/'run_core17_live.py').read_text()
    finally:sys.path.pop(0)
