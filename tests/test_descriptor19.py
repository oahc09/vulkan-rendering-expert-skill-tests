"""Ordinary UBO boundary tests; CPU rules, not GPU shader behavior."""
from pathlib import Path
import sys,json,hashlib
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));import descriptor19 as d
pytestmark=pytest.mark.host_unit
def check(**kw):
 args=dict(buffer_size=256,offset=0,range_bytes=16,max_range=256,alignment=16,bound=True,uniform_usage=True,update_safe=True);args.update(kw);return d.check(**args)
def test_positive():assert check()['status']=='WITHIN_CHECKED_SCOPE'
@pytest.mark.parametrize('kw,suffix',[(dict(offset=256),'00340'),(dict(range_bytes=0),'00341'),(dict(range_bytes=257),'00342'),(dict(offset=1),'00327'),(dict(max_range=8),'00332'),(dict(bound=False),'00329'),(dict(uniform_usage=False),'00330')])
def test_rejections(kw,suffix):assert any(v.endswith(suffix) for v in check(**kw)['vuids'])
def test_whole_effective_not_unbounded():
 assert check(range_bytes=d.WHOLE)['effective_range']==256
 assert check(range_bytes=d.WHOLE,max_range=128)['status']=='REJECTED'
 assert check(offset=128,range_bytes=d.WHOLE,max_range=128)['status']=='WITHIN_CHECKED_SCOPE'
@pytest.mark.parametrize('kw',[dict(max_range=None),dict(alignment=None),dict(bound=None),dict(uniform_usage=None),dict(update_safe=None)])
def test_unknowns(kw):assert check(**kw)['status']=='UNKNOWN'
@pytest.mark.parametrize('kw',[dict(offset=-1),dict(range_bytes=True),dict(buffer_size=2**64),dict(alignment=0),dict(bound=1),dict(max_range=2**32)])
def test_invalid_input(kw):
 with pytest.raises(ValueError):check(**kw)
def test_real_record_source_and_pair():
 record=json.loads((ROOT/'coverage/v1.0.19/descriptor-pair.json').read_text())
 assert record['source_sha256']==hashlib.sha256((ROOT/'cases19/descriptor/probe.c').read_bytes()).hexdigest()
 assert len(record['cases'])==5
 for case in record['cases'].values():assert sorted(case['rule']['vuids'])==case['observed_vuids']

def test_known_unsafe_is_rejected():
 assert check(update_safe=False)['status']=='REJECTED'
