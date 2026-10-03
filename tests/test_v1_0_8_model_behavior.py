"""v1.0.8 Project Diagnosis model behavior snapshot tests."""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
RESP = BASE / "responses_v1_0_8"

def read(name):
    path = RESP / name
    assert path.is_file(), f"missing response: {path}"
    return path.read_text(encoding="utf-8")

def common(text):
    assert len(text) >= 1200
    assert text.count("[CODE]") >= 3
    assert "Evidence Map" in text
    assert "Architecture Map" in text
    assert "Verification Gate" in text
    assert "未验证" in text

def section(text, heading):
    lines = text.splitlines()
    start = None
    level = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        hashes = len(stripped) - len(stripped.lstrip("#"))
        title = stripped[hashes:].strip()
        if 2 <= hashes <= 4 and title == heading:
            start = i + 1
            level = hashes
            break
    if start is None:
        return ""
    end = len(lines)
    for i in range(start, len(lines)):
        stripped = lines[i].lstrip()
        if not stripped.startswith("#"):
            continue
        hashes = len(stripped) - len(stripped.lstrip("#"))
        if 2 <= hashes <= level:
            end = i
            break
    return "\n".join(lines[start:end])

def test_repository_map_behavior():
    text = read("tc11_01_repository_map.md")
    common(text)
    for token in ["src/VulkanContext.cpp", "src/Renderer.cpp", "src/RenderPassCache.cpp",
                  "src/PipelineCache.cpp", "src/ResourceManager.cpp", "src/DescriptorManager.cpp",
                  "vkAcquireNextImageKHR", "vkQueueSubmit", "vkQueuePresentKHR", "vkCreateRenderPass"]:
        assert token in text
    assert "RenderGraph / Dynamic Rendering / bindless" in text
    assert "当前任务只要求诊断" in text

def test_vulkan_13_upgrade_behavior():
    text = read("tc11_02_vulkan_13_upgrade.md")
    common(text)
    for token in ["Must Change", "Should Change", "Can Defer", "Do Not Change",
                  "src/VulkanContext.cpp", "src/AndroidVulkan.cpp", "src/Queue.cpp",
                  "src/RenderPass.cpp", "src/Pipeline.cpp"]:
        assert token in text
    assert "Synchronization2 与 Dynamic Rendering 不是版本升级的 Must Change" in text
    assert "vkQueueSubmit2" in section(text, "Can Defer")
    assert "Dynamic Rendering" in section(text, "Can Defer")
    assert "Queue::submit" in section(text, "Do Not Change")
    assert "RenderPass" in section(text, "Do Not Change")
    for token in ["Dependency Order", "Rollback", "Definition of Done"]:
        assert token in text

def test_android_rotation_behavior():
    text = read("tc11_03_android_rotation_crash.md")
    common(text)
    for token in ["app/RenderSurface.java", "native/JniBridge.cpp", "native/Renderer.cpp",
                  "surfaceDestroyed", "ANativeWindow", "VkSurfaceKHR", "VkSwapchainKHR",
                  "vkAcquireNextImageKHR", "vkQueuePresentKHR"]:
        assert token in text
    for token in ["Surface 无效后仍调用", "render thread", "Workaround", "Minimal Fix",
                  "Structural Fix", "Must Change", "Should Change", "Can Defer", "Do Not Change"]:
        assert token in text
    assert "不修改 shader" in text

def test_compute_pass_behavior():
    text = read("tc11_04_add_compute_pass.md")
    common(text)
    for token in ["ResourceManager", "DescriptorAllocator", "PipelineManager",
                  "FrameContext.computeCmd", "CommandContext", "Queue::submitCompute",
                  "Queue::submitGraphics", "VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT",
                  "VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT", "VK_IMAGE_LAYOUT_GENERAL",
                  "VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL",
                  "VK_PIPELINE_STAGE_2_FRAGMENT_SHADER_BIT",
                  "VK_ACCESS_2_SHADER_SAMPLED_READ_BIT"]:
        assert token in text
    assert "不新建 ResourceManager" in text
    assert "不新建第二套 command-pool / fence 系统" in text
    for token in ["Files To Modify", "Dependency Order", "Risks", "Rollback", "Definition of Done"]:
        assert token in text
