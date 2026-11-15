import importlib.util,math
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
s=importlib.util.spec_from_file_location('emoji_provider',Path(__file__).parent/'fixtures/text_emoji_lab/provider.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_presentation_policy():
 assert m.policy('❤\ufe0e')=='text' and m.policy('❤\ufe0f')=='emoji'
@pytest.mark.parametrize('s',['❤','❤\ufe0d','😀'])
def test_unsupported_cluster(s):
 with pytest.raises(ValueError,match='unsupported presentation cluster'):m.policy(s)
def test_transparent_canonical():assert m.linear_pixel([0,0,0,0])==[0,0,0,0]
def test_encoded_premult_conversion():
 result=m.linear_pixel([64,32,16,128]);straight=[.125,.25,.5]
 expected=[math.exp(2.4*math.log((v+.055)/1.055))*128/255 for v in straight]+[128/255]
 assert result==pytest.approx(expected,abs=1e-15)
def test_invalid_premult():
 with pytest.raises(ValueError,match='invalid premultiplied BGRA'):m.linear_pixel([129,0,0,128])
