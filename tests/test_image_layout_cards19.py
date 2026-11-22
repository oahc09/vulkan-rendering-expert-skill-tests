"""Candidate knowledge contracts; no automatic prose/GPU validation."""
import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.candidate19
ROOT=Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))/'references/03_api_manual'
FILES=['08_synchronization/image_memory_barrier.md','04_buffer_image_memory/image_layout.md','07_rendering/render_target_layout.md']
OLD=['srcAccess 为空导致旧 layout 数据未 flush。','UNDEFINED作为旧layout丢弃旧内容', '`oldLayout`/`newLayout` 语义与 1.0 版本一致','4. `srcAccessMask` 为空就执行 layout transition','Layout transition 本身即是一种 memory dependency','transition 隐含 memory dependency','transition 隐含一次 memory dependency','- [ ] `oldLayout` 是否与实际 layout 一致？']
def validate(cards):
 text='\n'.join(cards)
 for old in OLD:
  if old in text:raise ValueError('old unconditional contract')
 for phrase in ['旧VkImageMemoryBarrier在synchronization2 feature启用时','即使两值均UNDEFINED','实际布局不变','不同 family 不可套','未覆盖 subresource 不随之更新','UNDEFINED 允许 discard','availability 后','visibility 前','VUID-VkImageMemoryBarrier2-oldLayout-01197','VUID-VkImageMemoryBarrier-oldLayout-01197','两版本来源分别绑定']:
  if phrase not in cards[0]:raise ValueError('missing reviewed scope')
 for card in cards[1:]:
  if '不是充分同步证明' not in card or '布局忽略分支中的 UNDEFINED 不表示 discard' not in card:raise ValueError('missing companion qualification')
 return True
@pytest.fixture
def cards():return [(ROOT/f).read_text() for f in FILES]
def test_current(cards):assert validate(cards)
@pytest.mark.parametrize('old',OLD)
def test_reject_old_errors(cards,old):
 assert validate(cards)
 with pytest.raises(ValueError,match='old unconditional'):validate([cards[0]+'\n'+old,*cards[1:]])
@pytest.mark.parametrize('phrase',['旧VkImageMemoryBarrier在synchronization2 feature启用时','即使两值均UNDEFINED','不同 family 不可套','未覆盖 subresource 不随之更新','两版本来源分别绑定'])
def test_missing_scope(cards,phrase):
 assert validate(cards)
 with pytest.raises(ValueError,match='missing reviewed'):validate([cards[0].replace(phrase,''),*cards[1:]])
