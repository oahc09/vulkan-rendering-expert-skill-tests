"""Independent-section static smoke checks; not GPU or semantic model evidence."""
import hashlib
import json
from pathlib import Path
from conftest import PROJECT_ROOT
from run_live_model_behavior import select_section


def section(path, title):
    return select_section((PROJECT_ROOT/'references'/path).read_text(), title)[0]


def test_frame_summary_and_steps_delay_reset_until_recorded():
    path = '05_workflows/01_renderer_setup/setup_frame_loop.md'
    summary = section(path, '1. 任务目标')
    assert summary.index('Record CommandBuffer') < summary.index('Reset Fence') < summary.index('Queue Submit')
    steps = section(path, '8. 实现步骤（帧循环权威契约）')
    assert steps.index('record command buffer') < steps.index('紧邻 submit reset frame fence')
    failure = section(path, '提前退出与失败分支')
    for token in ['OUT_OF_DATE', 'TIMEOUT', 'NOT_READY', 'SUBOPTIMAL', '录制失败', 'submit 失败', '不 reset frame fence', '不 present']:
        assert token in failure


def test_present_independent_debug_section_preserves_retirement_boundary():
    text = section('03_api_manual/03_command_buffer/frames_in_flight.md', '8. Debug 检查路径')
    assert 'currentFrame' in text and 'imageIndex' in text
    assert 'submit fence / WaitIdle 不能单独' in text


def test_feature_section_is_self_contained():
    text = section('02_core_mental_model/vulkan_1_4_overview.md', '3. 强制功能')
    for token in ['VK_API_VERSION_1_4', 'VK_VERSION_1_4', 'VkPhysicalDeviceVulkan12Features',
                  'VkPhysicalDeviceVulkan13Features', 'scalarBlockLayout', 'timelineSemaphore', '启用']:
        assert token in text
    assert '查询支持不等于' in text


def test_verification_scope_section_does_not_force_runtime_for_api_answers():
    text = section('00_expert_entry/verification_gate.md', '1. 定位')
    assert '纯概念 / API 问答' in text
    assert '不要求运行' in text
    assert '方案尚未运行' in text
    assert 'G1-G6' in text


def test_archived_evaluation_is_exact_and_not_current_evidence():
    root = Path(__file__).parent.parent/'reports/history/v1.0.9'
    manifest = json.loads((root/'manifest.json').read_text())
    assert hashlib.sha256((root/'behavior_evaluation.md').read_bytes()).hexdigest() == manifest['sha256']
    assert manifest['source_sha'] == '102c5d721dcb43a23e12d77927f2703d56c63a11'
    assert 'not candidate' in manifest['status']


def test_original_twelve_prompts_are_frozen():
    from run_live_model_behavior import ORIGINAL_CASES
    root = Path(__file__).parent
    manifest = json.loads((root/'original-cohort.json').read_text())
    assert manifest['source_tests_sha'] == 'f48871940b6af3c20a6fa9d108645631735512ac'
    assert set(manifest['cases']) == set(ORIGINAL_CASES)
    for case, expected in manifest['cases'].items():
        assert hashlib.sha256((root/'prompts'/f'{case}.txt').read_bytes()).hexdigest() == expected
