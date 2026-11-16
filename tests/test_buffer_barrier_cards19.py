"""Bounded reviewed knowledge regressions, not automatic normative reasoning."""
import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.candidate19
ROOT=Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))
PREFIX='references/03_api_manual/08_synchronization/'
OLD_ERRORS=[
 'Host-visible buffer 的 CPU 写入需使用 `HOST_WRITE` → `SHADER_READ` 等路径。',
 '对 host-visible buffer 的 CPU 写入未使用 `VK_ACCESS_HOST_WRITE_BIT`。',
 '跨 queue 需使用 queue family ownership transfer',
 '同 family 时误填具体 index 导致不必要的 ownership transfer',
 '`offset` / `size` 未对齐，触发 validation error',
 '`size` 设为 `VK_WHOLE_SIZE` 时未注意 offset 对齐',
]
def validate(buffer,pipeline):
 text=buffer+'\n'+pipeline
 for old in OLD_ERRORS:
  if old in text:raise ValueError('known old semantic error')
 for required in ['happens-before queue submit','Non-coherent 写仍需先 flush','不能覆盖尚未退休','同 family 不需要 family ownership transfer','CONCURRENT 不需此 transfer','maintenance9','不存在一般 barrier range 对齐要求','synchronization-submission-host-writes','buffer-memory-barrier-ownership-transfer','fa30d4e312e843193601be7cb926c7e25d9ec885','7748c88e48007820179681ef4f82c1d2244afc5482b5bc0c13d370ef64821909','f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7','offset-01187','size-01188','size-01189','两个版本为分别绑定']:
  if required not in buffer:raise ValueError('missing reviewed condition/source')
 if 'VK_WHOLE_SIZE 不引入通用 offset 对齐要求' not in pipeline:raise ValueError('missing pipeline range qualification')
 return True
@pytest.fixture
def cards():return tuple((ROOT/PREFIX/n).read_text() for n in ['buffer_memory_barrier.md','pipeline_barrier.md'])
def test_current_reviewed_contract(cards):assert validate(*cards)
@pytest.mark.parametrize('old',OLD_ERRORS)
def test_actual_old_errors_rejected(cards,old):
 assert validate(*cards)
 with pytest.raises(ValueError,match='known old'):validate(cards[0]+'\n'+old,cards[1])
@pytest.mark.parametrize('condition',['Non-coherent 写仍需先 flush','不能覆盖尚未退休','同 family 不需要 family ownership transfer','size-01188','两个版本为分别绑定'])
def test_missing_scope_or_source_rejected(cards,condition):
 assert validate(*cards)
 with pytest.raises(ValueError,match='missing reviewed'):validate(cards[0].replace(condition,''),cards[1])
def test_missing_pipeline_qualification(cards):
 assert validate(*cards)
 with pytest.raises(ValueError,match='pipeline range'):validate(cards[0],cards[1].replace('VK_WHOLE_SIZE 不引入通用 offset 对齐要求',''))
