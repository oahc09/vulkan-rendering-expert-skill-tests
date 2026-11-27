import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.candidate19
P=Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))/'references/03_api_manual/05_descriptor/storage_buffer_image_descriptor.md'
REQUIRED=['delivery19-external-shared-buffer','8c3bfef40c2387944fdc81746e2e3249e4da5566','aaac58d5009e8f6b33e2723258dc1542854d09a4','合并 usage 和可写属性','不同资源对象也可能合法别名同一内存','共享存储不自动建立执行/内存依赖','实际执行结果必须与源码推断分开报告','不是未知任务盲测']
def check(t):
 for x in REQUIRED:
  if x not in t:raise ValueError('missing reviewed boundary')
 return True
def test_current():assert check(P.read_text())
@pytest.mark.parametrize('x',REQUIRED)
def test_boundary(x):
 t=P.read_text();assert check(t)
 with pytest.raises(ValueError):check(t.replace(x,''))
