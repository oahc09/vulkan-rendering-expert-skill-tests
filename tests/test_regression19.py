"""Explicit historical exclusions, not weakened historical assertions."""
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('regression19',ROOT/'checks19/run_regression.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
pytestmark=pytest.mark.host_unit

def test_only_nine_named_historical_nodes():
 a=m.exclusions();assert len(a)==9 and len(set(a))==9
 assert all(x.startswith('--deselect=test_') and '::test_' in x for x in a)
 assert not any('descriptor' in x or 'delivery19' in x for x in a)

def test_current_ci_runs_full_gate_not_only_host():
 s=(ROOT/'.github/workflows/all19-candidate.yml').read_text()
 assert 'checks19/run_regression.py --skill skill' in s
 assert '-m host_unit' not in s

def test_local_lab_sweep_keeps_retry_and_source_lineage():
 import json
 d=json.loads((ROOT/'coverage/v1.0.19/full-lab-regression.json').read_text())
 assert d['primary_counts']=={'PASS':54,'SKIP':1}
 assert len(d['nodes'])==len({n['node'] for n in d['nodes']})==55
 assert sum(n['outcome']=='PASS' for n in d['nodes'])==54
 assert d['effective_unique_node_outcomes_after_retry']=={'PASS':55,'FAIL':0,'SKIP':0}
 assert d['tests_run_sha']!=d['comparison']['sha']
 assert d['comparison']['changed_paths']==[]
 assert d['comparison']['harness_changes_not_in_equivalence']
 assert d['nested_summary_status_counts']['SAMPLING_PASS_QUALITY_NOT_QUALIFIED']>0
