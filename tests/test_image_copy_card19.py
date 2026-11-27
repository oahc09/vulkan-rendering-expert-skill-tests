"""Bounded image-copy knowledge regressions; not complete command validation."""
import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.candidate19
ROOT=Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))
CARD='references/03_api_manual/04_buffer_image_memory/copy_blit_resolve.md'
OLD=['相同格式，或同 size + 同 block extent 的兼容格式','压缩格式的 image copy / blit region 是否按 block size 对齐？','5. 压缩格式 region 未按 texel block 对齐。']
def validate(t):
 for old in OLD:
  if old in t:raise ValueError('old incorrect contract')
 for text in ['texel block 字节数','双方均为 compressed','compressed ↔ uncompressed','source texel 单位','边缘例外不豁免 offset','不是解压、过滤或数值格式转换','Alpha 格式类别、multi-planar','queue transfer granularity','formats-size-compatibility','copies-images-addressing','b821b4b219c3e7e691332b651c40cd169b74017d7212aad9d1ddbeef8acbec05','9360d12ae4c69c9eb7cf374dc3c99c061b6386f1551b9b4648d14728101cb7f1','srcImage-01548','srcImage-09247','两版本来源分别绑定']:
  if text not in t:raise ValueError('missing reviewed condition/source')
 return True
@pytest.fixture
def card():return (ROOT/CARD).read_text()
def test_current_card(card):assert validate(card)
@pytest.mark.parametrize('old',OLD)
def test_reject_actual_old_errors(card,old):
 assert validate(card)
 with pytest.raises(ValueError,match='old incorrect'):validate(card+'\n'+old)
@pytest.mark.parametrize('text',['边缘例外不豁免 offset','source texel 单位','双方均为 compressed','srcImage-09247','两版本来源分别绑定'])
def test_reject_missing_conditions(card,text):
 assert validate(card)
 with pytest.raises(ValueError,match='missing reviewed'):validate(card.replace(text,''))
