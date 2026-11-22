"""Reviewed bounded knowledge regression; not a prose or GPU validator."""
import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.candidate19
ROOT=Path(os.environ.get('VULKAN_SKILL_ROOT','/tmp/vulkan119-skill'))/'references/03_api_manual/08_synchronization'
OLD=['对端 GPU/CPU 通过 vkWaitSemaphores(value = next)', '打印每次 `vkQueueSubmit2` 与 `vkSignalSemaphore` 的 value，断言严格单调递增。','counter 单调性即可发现绝大多数同步错位问题','→ 下游 submit 等待更高 value','检查 timeline semaphore 的 value 是否严格递增。']
REQUIRED=['wait 值无需递增','及每个 outstanding wait/signal','数值合法不等于执行顺序合法','保证其晚于这次 host signal','不是原子 query-and-signal','不是所有引用退休','禁止 unsigned 下溢','完成点须覆盖该资源的全部消费者','03258','03259','03260','两版本分别绑定']
def validate(t,s):
 for old in OLD:
  if old in t+s:raise ValueError('old incorrect shortcut')
 for phrase in REQUIRED:
  if phrase not in t:raise ValueError('missing reviewed condition')
 return True
@pytest.fixture
def cards():return ((ROOT/'timeline_semaphore.md').read_text(),(ROOT/'semaphore.md').read_text())
def test_current(cards):assert validate(*cards)
@pytest.mark.parametrize('old',OLD)
def test_reject_old(cards,old):
 assert validate(*cards)
 with pytest.raises(ValueError,match='old incorrect'):validate(cards[0]+'\n'+old,cards[1])
@pytest.mark.parametrize('phrase',REQUIRED)
def test_missing_scope(cards,phrase):
 assert validate(*cards)
 with pytest.raises(ValueError,match='missing reviewed'):validate(cards[0].replace(phrase,''),cards[1])
