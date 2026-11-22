import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.candidate19
R=Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))/'references/03_api_manual/05_descriptor'
OLD=['`descriptorCount` 与数组大小不一致。','array 大小不一致。','最后一个 binding 可加 VARIABLE_DESCRIPTOR_COUNT','Variable count binding 没有放在 layout 最后一个 binding 上。']
REQ=['不要求等于整个数组长度','先执行全部 writes，再执行全部 copies','各数组内部按数组顺序执行','同 set 的源和目的范围不得重叠','引用必然相同','不让旧资源退休','stage 单列10776','不是声明数组的最后一项']
def validate(t):
 for x in OLD:
  if x in t:raise ValueError('old false shortcut')
 for x in REQ:
  if x not in t:raise ValueError('missing reviewed condition')
 return True
@pytest.fixture
def text():return '\n'.join((R/n).read_text() for n in ['descriptor_update.md','descriptor_indexing.md'])
def test_current(text):assert validate(text)
@pytest.mark.parametrize('old',OLD)
def test_old_rejected(text,old):
 assert validate(text)
 with pytest.raises(ValueError,match='old false'):validate(text+'\n'+old)
@pytest.mark.parametrize('x',REQ)
def test_condition_required(text,x):
 assert validate(text)
 with pytest.raises(ValueError,match='missing'):validate(text.replace(x,''))
