"""Independent negative controls for the opt-in real-tool gate (CPU only)."""
import importlib.util,json,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('capture_contract',ROOT/'probes19/capture_contract.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
pytestmark=pytest.mark.host_unit
@pytest.mark.parametrize('case,data',[('bad',[]),('bad',[{'pMessageIdName':'wrong'}]),('good',[{'pMessageIdName':c.VUID}]),('typo',[])])
def test_callback_negative(case,data):
 with pytest.raises(ValueError):c.callbacks(case,json.dumps(data))
@pytest.mark.parametrize('raw',[
 'id,ts,dur,track_id,name\n1,10000,2000,1,wrong\n',
 'id,ts,dur,track_id,name\n',
 'id,ts,dur,track_id,name\n1,40000,2000,1,a\n',
])
def test_trace_negative(raw):
 with pytest.raises(ValueError):c.trace(raw.encode(),[dict(name='a',ts=10,dur=2)])
def test_runtime_identity_mismatch():
 with pytest.raises(ValueError):c.identity(b'IDENTITY {"device_type":2,"layer_spec":4194304,"layer_impl":1}',dict(api_version='1.0.0',implementation_version='1'))
def test_optimized_python_still_rejects():
 code="import sys;sys.path.insert(0,sys.argv[1]);import capture_contract;c=capture_contract.callbacks('bad',b'[]')"
 r=subprocess.run([sys.executable,'-O','-c',code,str(ROOT/'probes19')],capture_output=True)
 assert r.returncode!=0 and b'probe callback mismatch' in r.stderr
def test_duplicate_trace_ids():
 raw=b'id,ts,dur,track_id,name\n1,10000,2000,1,a\n1,20000,2000,1,b\n'
 with pytest.raises(ValueError):c.trace(raw,[dict(name='a',ts=10,dur=2),dict(name='b',ts=20,dur=2)])
