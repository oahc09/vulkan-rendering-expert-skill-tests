"""HOST verifier unit controls, not additional GPU/device observations."""
import pytest
from tools import external_fence19 as f

def test_before():f.verify_output('before','old',0,f.expected(False),'')
def test_after():f.verify_output('after','fixed',0,f.expected(True),'')
def test_historical_reject():f.verify_output('before','fixed',6,'empty wait=0 calls=0\ndefault timeout=4294967295 result=0 calls=1\n','ORACLE_MISMATCH\n')
def test_invalid_mode():f.verify_output('after','invalid',2,'','INVALID_MODE\n')
@pytest.mark.parametrize('code,out,err',[(True,None,''),(1,None,''),(0,'',''),(0,None,'warning'),(0,'garbage','')])
def test_output_mutations(code,out,err):
 with pytest.raises(ValueError):f.verify_output('after','fixed',code,f.expected(True) if out is None else out,err)
@pytest.mark.parametrize('value',['4294967295','0','18446744073709551614'])
def test_default_truncation(value):
 with pytest.raises(ValueError):f.verify_output('after','fixed',0,f.expected(True).replace('default timeout=18446744073709551615','default timeout='+value),'')
def test_old_rejects_fixed_behavior():
 with pytest.raises(ValueError):f.verify_output('before','old',0,f.expected(True),'')
def test_expected_negative_cannot_pass():
 with pytest.raises(ValueError):f.verify_output('before','fixed',0,f.expected(True),'')
def test_abort_is_not_expected_negative():
 with pytest.raises(ValueError):f.verify_output('before','fixed',-6,'','')
@pytest.mark.parametrize('label,name',[('other','fence_pool.cpp'),('before','../secret'),('after','fence_pool.cc')])
def test_source_selector_reject(label,name):
 with pytest.raises(ValueError,match='unknown source'):f.source_bytes('/unread',label,name)
def test_source_wrong_bytes(monkeypatch):
 monkeypatch.setattr(f.subprocess,'check_output',lambda *a,**k:b'changed')
 with pytest.raises(ValueError,match='hash mismatch'):f.source_bytes('/unread','before','fence_pool.cpp')
def test_existing_output_reject(tmp_path):
 with pytest.raises(ValueError,match='fresh'):f.run(tmp_path,tmp_path,tmp_path)
def test_missing_headers_reject(tmp_path):
 with pytest.raises(ValueError,match='headers missing'):f.run(tmp_path,tmp_path,tmp_path/'new')
def test_wrong_parent(monkeypatch):
 monkeypatch.setattr(f.subprocess,'check_output',lambda *a,**k:'0'*40)
 with pytest.raises(ValueError,match='parent mismatch'):f.verify_parent('/unread')
def test_missing_parent(monkeypatch):
 def fail(*a,**k):raise f.subprocess.CalledProcessError(1,['git'])
 monkeypatch.setattr(f.subprocess,'check_output',fail)
 with pytest.raises(f.subprocess.CalledProcessError):f.verify_parent('/unread')
def test_extra_output_reject():
 with pytest.raises(ValueError):f.verify_output('after','fixed',0,f.expected(True)+'extra\n','')
