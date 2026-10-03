# TC11.4 Model Response — Add Compute Blur Pass

结论：现有引擎已经暴露了 Resource、Descriptor、Compute Pipeline、per-frame compute CommandBuffer、barrier helper 和 compute submit 路径，因此新增 blur pass 应作为这些子系统上的一个新 pass，**不新增第二套资源/descriptor/pipeline/queue manager**。[CODE][ENGINE]

## [CODE] Evidence Map

| 当前能力 | 源码证据 | 结论 |
|---|---|---|
| 统一资源创建与 retire | [CODE] `src/ResourceManager.cpp` | blur output image 应由 ResourceManager 创建/回收 |
| 统一 descriptor allocate/update | [CODE] `src/DescriptorAllocator.cpp` | storage image + sampled input 都走现有 DescriptorAllocator |
| 已有 compute pipeline manager | [CODE] `src/PipelineManager.cpp::getCompute` | blur pipeline 走现有 cache/manager |
| FrameContext 已有 `computeCmd` | [CODE] `src/FrameContext.h` | 不新建独立 command-pool 系统 |
| 已有 imageBarrier / dispatch helper | [CODE] `src/CommandContext.cpp` | 同步与 dispatch 复用现有 CommandContext |
| 已有 compute / graphics submit API | [CODE] `src/Queue.cpp` | 可以接现有 queue submission；是否不同 queue family **未验证** |

## Architecture Map

```text
BlurPass
  ↓
ResourceManager
  ├─ sampled input image（existing）
  └─ storage/output image
  ↓
DescriptorAllocator
  └─ sampled input + storage output
  ↓
PipelineManager::getCompute
  └─ compute pipeline
  ↓
FrameContext.computeCmd
  ↓
CommandContext
  ├─ imageBarrier
  └─ dispatch
  ↓
Queue::submitCompute
  ↓ semaphore / queue dependency
Queue::submitGraphics
  ↓
fragment sampled read
```

## 应复用的现有子系统

- [CODE] `ResourceManager`：Image 生命周期与 retire。
- [CODE] `DescriptorAllocator`：blur descriptor set。
- [CODE] `PipelineManager::getCompute`：compute pipeline cache。
- [CODE] `FrameContext.computeCmd`：per-frame command recording。
- [CODE] `CommandContext`：barrier 与 dispatch。
- [CODE] `Queue`：compute/graphics submit。

## Files To Modify

1. **新增** `src/passes/ComputeBlurPass.*`
   - pass 参数、descriptor layout、dispatch size。
2. [CODE] `src/ResourceManager.cpp`
   - 仅当现有 `ImageDesc` 不能表达 `VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_SAMPLED_BIT` 时扩展描述；否则 Do Not Change。
3. [CODE] `src/DescriptorAllocator.cpp`
   - 原则上复用；如果已有 layout/write 抽象能表达 storage image，则 Do Not Change。
4. [CODE] `src/PipelineManager.cpp`
   - 原则上只调用 `getCompute`；不新增另一个 pipeline cache。
5. [CODE] `src/CommandContext.cpp`
   - 复用 `imageBarrier` / `dispatch`；只有 barrier desc 缺 stage/access/layout 表达能力时才扩展。
6. [CODE] `src/Queue.cpp`
   - 复用 submitCompute / submitGraphics；先确认两者是否同 queue family，再决定是否需要 ownership transfer。

## Dependency Order

```text
Task 1: 确认 Queue::submitCompute / submitGraphics 的实际 queue family
→ Task 2: 定义 blur input/output ImageDesc + lifetime
→ Task 3: 定义 DescriptorLayout + ComputePipelineDesc
→ Task 4: 实现 ComputeBlurPass command recording
→ Task 5: 接 compute → graphics synchronization
→ Task 6: 接 frame graph / pass 调度入口
→ Task 7: Validation + capture + resize / frames-in-flight 回归
```

## 同步与 Layout

假设 compute 写 output image，后续 fragment shader 采样：

### 同一 Queue / 同一 Queue Family

建议使用 Sync2 表达（若引擎当前仍是 legacy barrier，则映射到现有 `ImageBarrierDesc`，不要为一个 pass 强行重写全引擎）：

```text
Producer stage  = VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT
Producer access = VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT
oldLayout       = VK_IMAGE_LAYOUT_GENERAL
newLayout       = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL
Consumer stage  = VK_PIPELINE_STAGE_2_FRAGMENT_SHADER_BIT
Consumer access = VK_ACCESS_2_SHADER_SAMPLED_READ_BIT
```

对象链：

```text
vkCmdDispatch
→ compute shader storage write
→ image barrier
→ fragment shader sampled read
```

[SPEC]

### 不同 Queue

先确认 `submitCompute` 与 `submitGraphics` 是否真的来自不同 `VkQueue` / queue family；当前片段不足，标记**未验证**。

若跨 queue：
- compute submit signal semaphore / timeline value。
- graphics submit wait 该 semaphore/value。
- 若不同 queue family 且 image 为 exclusive sharing，需要 release/acquire ownership transfer。
- 不能只靠 pipeline barrier 跨 queue 建立完整依赖。[SPEC]

## Change Impact

### Must Change

- 新增 ComputeBlurPass。
- output image usage 必须覆盖 storage write + sampled read。
- descriptor 必须绑定 sampled input 与 storage output。
- compute pipeline / dispatch。
- compute write → fragment read 的同步与 layout。
- resize 时如 output 与 render extent 绑定，必须跟随重建。

### Should Change

- 给 pass 增加 GPU marker / profiler label，便于 AGI / RenderDoc 定位。
- 将 blur output 生命周期接入已有 retire / transient 机制，而不是永久常驻。

### Can Defer

- 独立 async compute 性能优化。先正确接入；只有 profile 证明存在 overlap 收益再评估。
- RenderGraph 化。如果当前引擎没有 RenderGraph，不因一个 blur pass 强行引入。

### Do Not Change

- 不新建 ResourceManager / DescriptorAllocator / PipelineManager。
- 不新建第二套 command-pool / fence 系统。
- 不默认开启独立 compute queue；先读取 Queue 实现和 profile。

## Risks

- storage image format 不支持目标 storage usage。
- descriptor imageLayout 与实际 layout 不一致。
- per-frame output 被下一帧 CPU/GPU 提前复用。
- compute/graphics 如果跨 queue，漏 semaphore 或 ownership transfer。
- resize 后 descriptor 仍引用旧 output image view。
- async compute 反而增加等待链。

## Rollback

把 ComputeBlurPass 作为可关闭的 pass；旧 graphics/postprocess 路径保留到 G1-G6 通过。资源和 pipeline 都走现有 manager，关闭 pass 后不会遗留第二套生命周期系统。

## Definition of Done

- Validation + sync validation 无新增错误。
- RenderDoc / AGI 能看到 dispatch、storage write 和后续 sampled read。
- blur 输出正确，连续多帧无闪烁。
- resize 后 output/descriptor 正确重建。
- frames-in-flight 下没有 overwrite / use-after-free。
- 若启用独立 compute queue，A/B profile 证明 frame time 不退化。

## Verification Gate

- G1 API 合法性：未验证；需检查 format feature / descriptor / pipeline creation。
- G2 生命周期：未验证；需确认 output 是否 per-frame / transient / swapchain-dependent。
- G3 同步：设计已给出，但 queue family 尚未验证。
- G4 Validation：未验证。
- G5 RenderDoc / AGI：未验证。
- G6 平台回归：未验证；至少覆盖 resize、frames-in-flight 和目标 Android GPU。