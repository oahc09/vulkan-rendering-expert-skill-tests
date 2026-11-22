"""Bounded same-card/cross-step knowledge regressions; not GPU or prose reasoning."""
import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.candidate19
ROOT=Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))
CARD='references/03_api_manual/06_pipeline/pipeline_layout.md'
OLD=[
 '重新创建了“等价”但 handle 不同的 layout，仍被判定不兼容导致 bind 失败。',
 'push constant range 是否覆盖所有 stage 且不重叠？',
 '两个 range 在同一 stage 上 offset/size 重叠。',
 'Push constant range 在同一 stage 重叠。',
]
def validate(text):
 for old in OLD:
  if old in text:raise ValueError('old incorrect contract')
 for token in ['兼容性不要求相同 handle','sets 0..N','INDEPENDENT_SETS_BIT_EXT','不要求先绑定 pipeline','任意两 range 不得重复同一 stage','VERTEX[0,4) 与 VERTEX[16,20)','VERTEX[0,16) 与 FRAGMENT[0,16)','01795 要求更新的每个 byte/stage','01796 要求每个更新 byte','创建合法不推出更新合法','descriptors-compatibility','descriptors-push-constants','3de692bf6e4f8579de50175be94c564a4580e1b8f0a59ed1e1267e1c3ca88950','f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7','两份版本来源分别绑定']:
  if token not in text:raise ValueError('missing reviewed condition/source')
 return True
@pytest.fixture
def card():return (ROOT/CARD).read_text()
def test_current_card(card):assert validate(card)
@pytest.mark.parametrize('old',OLD)
def test_old_real_errors_rejected(card,old):
 assert validate(card)
 with pytest.raises(ValueError,match='old incorrect'):validate(card+'\n'+old)
@pytest.mark.parametrize('token',['sets 0..N','INDEPENDENT_SETS_BIT_EXT','01796 要求每个更新 byte','创建合法不推出更新合法','两份版本来源分别绑定'])
def test_missing_condition_rejected(card,token):
 assert validate(card)
 with pytest.raises(ValueError,match='missing reviewed'):validate(card.replace(token,''))
