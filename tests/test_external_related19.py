import pytest
from tools import external_related19 as r
@pytest.mark.parametrize('case',r.CASES)
def test_baseline(case):r.verify_result(case,0,r.CASES[case][1],r.WARN if case.startswith('draw_') else '')
@pytest.mark.parametrize('case',r.CASES)
def test_summary_alone_not_pass(case):
 with pytest.raises(ValueError):r.verify_result(case,0,'Summary: 1 pass, 0 fail\n','')
@pytest.mark.parametrize('case',r.CASES)
def test_extra_error(case):
 with pytest.raises(ValueError):r.verify_result(case,0,r.CASES[case][1],'[ERROR]')
def test_not_additional_bug():assert len(r.CASES)==3 and len(r.ORDER)==6
