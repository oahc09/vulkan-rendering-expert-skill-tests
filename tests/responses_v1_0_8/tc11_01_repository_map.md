# TC11.1 Model Response — Repository Architecture Map

结论：当前证据足以确认这是一个“传统 RenderPass + 显式 frame loop + VMA 资源管理 + per-material descriptor”的 Vulkan Renderer；RenderGraph、Dynamic Rendering、bindless、command-pool ownership、swapchain 创建路径和 Android lifecycle 均未提供源码证据，因此标记为**未验证**，不做推断。

## [CODE] Evidence Map

| 结论 | 源码证据 | 关键行为 | 置信度 |
|---|---|---|---|
| Vulkan target 至少按 1.2 初始化 | [CODE] `src/VulkanContext.cpp::VulkanContext::init` | `app.apiVersion = VK_API_VERSION_1_2`，随后 `vkCreateInstance` / `vkCreateDevice` | 高 |
| graphics / present queue 分开获取 | [CODE] `src/VulkanContext.cpp::VulkanContext::init` | 对 `graphicsFamily` 与 `presentFamily` 分别 `vkGetDeviceQueue` | 高 |
| frame loop 是 acquire → record → submit → present | [CODE] `src/Renderer.cpp::Renderer::drawFrame` | `vkAcquireNextImageKHR` → `record` → `vkQueueSubmit` → `vkQueuePresentKHR` | 高 |
| 使用传统 `VkRenderPass` | [CODE] `src/RenderPassCache.cpp::RenderPassCache::create` | 调用 `vkCreateRenderPass` | 高 |
| graphics pipeline 与 renderPass 兼容性绑定 | [CODE] `src/PipelineCache.cpp::PipelineCache::createGraphics` | `info.renderPass = key.renderPass` 后创建 graphics pipeline | 高 |
| Image 分配复用 VMA | [CODE] `src/ResourceManager.cpp::ResourceManager::createImage` | 调用 `vmaCreateImage` | 高 |
| material descriptor 走集中分配与更新 | [CODE] `src/DescriptorManager.cpp::allocateMaterialSet` | `vkAllocateDescriptorSets` + `vkUpdateDescriptorSets` | 高 |
| RenderGraph / Dynamic Rendering / bindless | 未提供对应创建、调度或 descriptor-indexing 代码 | **未验证**，不能写成“不存在” | 低 |

`[CODE]` 只证明当前仓库实现；Vulkan API 合法性仍需以 `[SPEC]` / Validation 为准。

## Architecture Map

```text
Application
  ↓
VulkanContext::init
  ├─ VkInstance
  ├─ VkDevice
  ├─ graphics VkQueue
  └─ present VkQueue
  ↓
Renderer::drawFrame
  ├─ vkWaitForFences
  ├─ vkAcquireNextImageKHR
  ├─ record(frame.cmd, imageIndex)
  ├─ vkQueueSubmit(graphicsQueue)
  └─ vkQueuePresentKHR(presentQueue)
  ↓
Rendering Model
  ├─ RenderPassCache → VkRenderPass
  └─ PipelineCache → VkGraphicsPipeline + renderPass compatibility
  ↓
Resource / Binding
  ├─ ResourceManager → VMA image allocation
  └─ DescriptorManager → material descriptor sets
```

已确认层：Device/Queue、frame loop、传统 RenderPass、graphics pipeline、Image allocator、material descriptor。

未验证层：Swapchain 创建与 recreate、CommandPool / CommandBuffer owner、pipeline layout 管理、descriptor pool 生命周期、同步 barrier 体系、compute queue、RenderGraph、Dynamic Rendering、bindless、Android Surface 生命周期。

## 当前风险点

1. [CODE] graphics 与 present queue 分离，但未看到 queue-family ownership / sharing mode；如果两者来自不同 family，需要继续检查 swapchain image sharing 配置与同步。[SPEC]
2. [CODE] frame loop 可看到 fence wait，但未看到 fence reset、submit semaphore chain 和返回值处理，暂不能判断 frames-in-flight 是否完整。
3. [CODE] pipeline key 包含 renderPass，因此任何 attachment compatibility 变化都可能传播到 pipeline cache；这是后续 resize / format 改造的影响面。

当前任务只要求诊断，不建议迁移 Dynamic Rendering、RenderGraph 或 Bindless；缺少“当前架构已经失效”的源码或性能证据。

## Verification Gate

- G1 API 合法性：**未验证**；只有源码片段，未运行 Validation / 编译。
- G2 生命周期：**未验证**；swapchain、descriptor pool、VMA allocation 销毁路径未提供。
- G3 同步：**未验证**；只确认 frame fence 与 submit/present 主链，barrier/semaphore 细节缺失。
- G4 Validation Layer：**未验证**；无运行结果。
- G5 RenderDoc / AGI：**未验证**；无 capture。
- G6 平台回归：**未验证**；平台矩阵未提供。