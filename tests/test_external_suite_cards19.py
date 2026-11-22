import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.candidate19
P=Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))/'references/04_debug_playbooks/tool_usage.md'
NEEDED=['delivery19-external-history-suite','六次运行只是上下文回归','不加入成功分母','不能计为独立模型盲测','只接受固定 child entry','HOST 替身边界','已验证完成前缀','旧轮迟到报告不能归入新 run','不能推广为 GPU 挂死','不得过滤已有驱动 warning']
def check(t):
 for x in NEEDED:
  if x not in t:raise ValueError('missing suite boundary')
 return True
def test_current():assert check(P.read_text())
@pytest.mark.parametrize('x',NEEDED)
def test_boundary(x):
 t=P.read_text();assert check(t)
 with pytest.raises(ValueError):check(t.replace(x,''))
