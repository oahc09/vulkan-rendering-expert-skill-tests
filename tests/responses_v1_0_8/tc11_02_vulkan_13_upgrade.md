# TC11.2 Model Response — Vulkan 1.1 → 1.3 Impact

结论：如果目标只是把项目**基线提升到 Vulkan 1.3**，真正必须改的是版本声明、设备能力门槛和 Android capability gate；现有 `vkQueueSubmit`、`VkRenderPass` 和基于 renderPass 的 graphics pipeline 在 Vulkan 1.3 中仍可继续使用，因此 **Synchronization2 与 Dynamic Rendering 不是版本升级的 Must Change**。[SPEC]

## [CODE] Evidence Map

| 当前事实 | 源码证据 | 影响 |
|---|---|---|
| 应用声明 Vulkan 1.1 | [CODE] `src/VulkanContext.cpp`：`appInfo.apiVersion = VK_API_VERSION_1_1` | 基线升级入口 |
| Device creation 未展示 1.3 feature chain | [CODE] `src/VulkanContext.cpp`：仅看到 `VkDeviceCreateInfo` + `vkCreateDevice` | 是否启用具体 1.3 feature **未验证** |
| submit 使用 legacy path | [CODE] `src/Queue.cpp::Queue::submit`：`VkSubmitInfo` + `vkQueueSubmit` | 1.3 下仍合法，不要求迁移 |
| rendering 使用传统 RenderPass | [CODE] `src/RenderPass.cpp::create`：`vkCreateRenderPass` | 1.3 下仍合法 |
| pipeline 依赖 renderPass | [CODE] `src/Pipeline.cpp::create`：`ci.renderPass = desc.renderPass` | 若未来迁 Dynamic Rendering，会传播到 pipeline key / creation |
| Android gate 只要求 1.1 | [CODE] `src/AndroidVulkan.cpp::supportsRequiredVersion` | 提升基线时必须同步 |

## Change Impact

### Must Change

1. [CODE] `src/VulkanContext.cpp`
   - 将目标版本从 `VK_API_VERSION_1_1` 调整到 `VK_API_VERSION_1_3`。
   - 在创建 Instance / 选择 PhysicalDevice 前确认 loader 与 device 的可用 Vulkan 版本；不能只改宏后假设设备支持。[SPEC]
2. [CODE] `src/AndroidVulkan.cpp::supportsRequiredVersion`
   - 最低版本 gate 从 1.1 改为 1.3，或按产品策略保留 fallback。
   - 设备不足 1.3 时必须明确拒绝 / fallback，而不是进入 renderer 后失败。
3. [CODE] `src/VulkanContext.cpp`
   - 审计实际准备使用的 1.3 feature/extension；“版本 1.3”不等于所有可选 feature 自动启用。若要使用具体 feature，再把对应 feature struct 接入 feature query / device creation chain。[SPEC]

### Should Change

1. 增加启动日志：instance version、physical-device apiVersion、已启用 feature / extension，方便回归定位。
2. 把版本/feature capability 结果集中成一份 DeviceCaps，避免 Android gate 与 Device 初始化各写一套条件。

### Can Defer

1. [CODE] `src/Queue.cpp::Queue::submit`：`vkQueueSubmit` → `vkQueueSubmit2` / Synchronization2。
   - **可延后**。只有计划统一 Sync2 表达、减少 legacy barrier/submit 双路径时再迁。
2. [CODE] `src/RenderPass.cpp` + `src/Pipeline.cpp`：Traditional RenderPass → Dynamic Rendering。
   - **可延后**。迁移会改变 render target / pipeline compatibility 路径，属于架构改造，不是 1.3 基线升级的前置条件。

### Do Not Change

1. 当前版本升级阶段不要为了“现代化”重写 `Queue::submit`。
2. 不要在没有收益证据时删除 `RenderPass` 路径。
3. 不要同时引入 RenderGraph / Bindless；它们与版本基线提升没有直接依赖。

## Dependency Order

```text
Task 1: 查询 loader / physical-device Vulkan 版本
→ Task 2: 更新 Android capability gate
→ Task 3: 更新 appInfo.apiVersion 到 1.3
→ Task 4: 仅对实际需要的 1.3 feature 做 query + enable
→ Task 5: 编译 + Validation + Android 设备矩阵回归
→ Optional: 独立评估 Sync2 / Dynamic Rendering 迁移
```

## Files To Modify

- `src/VulkanContext.cpp` — version negotiation、feature/capability 记录。
- `src/AndroidVulkan.cpp` — 1.3 support gate / fallback。
- `src/Queue.cpp` —本轮 **Do Not Change**，除非另开 Sync2 migration。
- `src/RenderPass.cpp` / `src/Pipeline.cpp` —本轮 **Do Not Change**，保持传统路径。

## Risks

- 把 app version 提到 1.3，但设备选择仍允许 1.1/1.2 设备。
- 把“core in 1.3”误解为“feature 自动启用”。
- 同一版本升级 PR 同时迁 Sync2 + Dynamic Rendering，导致回归面从 capability gate 扩大到 submit、barrier、pipeline、render-target 全链路。

## Rollback

保留一个 Vulkan baseline 配置项或单独 commit；若目标设备矩阵出现兼容问题，可回退到 1.1 baseline，而不需要回滚 RenderPass / Queue，因为本轮未强制改它们。

## Definition of Done

- 所有目标设备报告 Vulkan 1.3 或按产品策略正确 fallback。
- Instance / PhysicalDevice / Device capability 日志一致。
- Validation Layer 无新增错误。
- 现有 RenderPass / submit 路径功能回归通过。
- Android 启动、pause/resume、rotation 基本回归通过。

## Verification Gate

- G1 API 合法性：未验证；需对目标 SDK/设备跑 Validation，并回查 1.3 capability/feature 规则。
- G2 生命周期：本轮对象生命周期不应改变；需回归确认。
- G3 同步：Do Not Change；仍需确保无现有 sync regression。
- G4 Validation：未验证。
- G5 RenderDoc / AGI：可选，用于确认 frame path 未变。
- G6 平台回归：未验证；至少需要 Android 1.3 支持设备矩阵。