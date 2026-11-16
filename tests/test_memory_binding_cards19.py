import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.candidate19
R=Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))/'references/03_api_manual/04_buffer_image_memory'
OLD=['必须满足 resource 的 memory requirements size，且按 alignment 对齐。','销毁 memory 前未销毁绑定的 image / buffer。','- 所有绑定 resource 销毁后。','fence signal 前不能 free。']
REQ=['独立309同编号要求等于 requirements.size', '不据此要求 allocationSize','requirements.size <= allocationSize − memoryOffset','free 原 memory 也不恢复可绑定资格','仅 prefersDedicatedAllocation','memoryOffset=0','bufferImageGranularity 页隔离','nonCoherentAtomSize','之后不得继续使用那些资源','不是唯一合法顺序','两版本不能混用编号']
def validate(t):
 for x in OLD:
  if x in t:raise ValueError('old unconditional claim')
 for x in REQ:
  if x not in t:raise ValueError('missing reviewed scope')
 return True
@pytest.fixture
def text():return (R/'memory_allocation.md').read_text()
def test_current(text):assert validate(text)
@pytest.mark.parametrize('old',OLD)
def test_old_error(text,old):
 assert validate(text)
 with pytest.raises(ValueError,match='old unconditional'):validate(text+'\n'+old)
@pytest.mark.parametrize('x',REQ)
def test_scope_required(text,x):
 assert validate(text)
 with pytest.raises(ValueError,match='missing reviewed'):validate(text.replace(x,''))
