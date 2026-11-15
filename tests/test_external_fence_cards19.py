import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.candidate19
P=Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))/'references/03_api_manual/08_synchronization/fence.md'
REQUIRED=['delivery19-external-fence-timeout','02d3010a3517620e7eedd919217e169c4a188de3','dca8e0842417ef14440135ee48a09870a05d5bff','实现决定','32 位形参不能修复','不是 64 位最大值','显式标注替身依赖','仅作为开发/开放答案任务','feature 不可用时保持未运行']
def validate(t):
 if '`UINT64_MAX` 为无限等待。[SPEC]' in t:raise ValueError('unqualified infinite claim')
 for x in REQUIRED:
  if x not in t:raise ValueError('missing scope')
 return True

def test_current():assert validate(P.read_text())
@pytest.mark.parametrize('x',REQUIRED)
def test_required_scope(x):
 t=P.read_text();assert validate(t)
 with pytest.raises(ValueError,match='missing scope'):validate(t.replace(x,''))
def test_unqualified_infinite():
 t=P.read_text();assert validate(t)
 with pytest.raises(ValueError,match='unqualified'):validate(t+'`UINT64_MAX` 为无限等待。[SPEC]')
