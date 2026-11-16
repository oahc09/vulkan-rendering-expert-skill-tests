"""Host negative controls for actual-tool runner, not new GPU executions."""
import importlib.util
from pathlib import Path
import pytest
p=Path(__file__).resolve().parents[1]/'cases19/descriptor_lifetime/run.py'
spec=importlib.util.spec_from_file_location('lifetime_actual_runner',p)
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
pytestmark=pytest.mark.host_unit

def output(mode):
 return dict(mode=mode,exit_code=0,fence_not_ready=True,first=42,second=99,errors=1,expected_vuid_count=1,rejected_call_result=-1000011001)

@pytest.mark.parametrize('mode',['pending-reset','stale-submit'])
def test_valid_recovered_negative(mode):
 runner.verify_case(mode,0,output(mode),[runner.DIAGNOSTICS[mode]])

@pytest.mark.parametrize('field,value',[('rejected_call_result',0),('fence_not_ready',False),('first',0),('second',42),('errors',0),('expected_vuid_count',0),('exit_code',6)])
def test_reject_incomplete_experiment(field,value):
 d=output('stale-submit');d[field]=value
 with pytest.raises(ValueError):runner.verify_case('stale-submit',0,d,[runner.DIAGNOSTICS['stale-submit']])

def test_vuid_correct_but_wrong_phase():
 d=output('pending-reset')
 with pytest.raises(ValueError):runner.verify_case('pending-reset',0,d,[runner.DIAGNOSTICS['pending-reset'].replace('phase=pending-reset','phase=cleanup')])

def test_extra_error_and_unexpected_process_failure():
 d=output('pending-reset');diag=[runner.DIAGNOSTICS['pending-reset']]
 with pytest.raises(ValueError):runner.verify_case('pending-reset',0,d,diag+diag)
 with pytest.raises(ValueError):runner.verify_case('pending-reset',-9,d,diag)

def test_wrong_output_control_cannot_be_pass():
 d=output('wrong-output');d.update(errors=0,expected_vuid_count=0,rejected_call_result=0)
 with pytest.raises(ValueError):runner.verify_case('wrong-output',0,d,[])
