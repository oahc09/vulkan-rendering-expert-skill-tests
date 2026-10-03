# TC11.3 Model Response — Android Rotation Crash

结论：最高优先级根因不是 shader，而是 **Surface 销毁后 render thread 仍继续对旧 swapchain 执行 acquire / submit / present**；同时 `setWindow()` 与 `drawFrame()` 之间没有看到线程同步或 swapchain teardown，这会把 Surface 生命周期问题放大成竞态。[CODE][ENGINE]

## [CODE] Evidence Map

| 结论 | 源码证据 | 置信度 |
|---|---|---|
| Java 层在 surfaceDestroyed 时传 null | [CODE] `app/RenderSurface.java::surfaceDestroyed` → `nativeSetSurface(null)` | 高 |
| JNI 把 null 映射为 null ANativeWindow | [CODE] `native/JniBridge.cpp::nativeSetSurface` | 高 |
| setWindow 会 release 旧 ANativeWindow | [CODE] `native/Renderer.cpp::Renderer::setWindow` | 高 |
| window=null 时没有停止 render thread | [CODE] `Renderer::drawFrame` 注释与代码：仍无条件 acquire/submit/present | 高 |
| 新 Surface 到来时直接 createSurfaceAndSwapchain | [CODE] `Renderer::setWindow` | 高 |
| 未看到旧 VkSwapchainKHR / VkSurfaceKHR / framebuffer/depth teardown | 提供的 `setWindow` / `createSurfaceAndSwapchain` 片段中没有 | 中；只能说“当前片段未展示”，完整仓库仍需确认 |
| setWindow 与 drawFrame 的线程互斥 / generation handoff | 未提供 | **未验证** |

## Android 生命周期链

```text
SurfaceView.surfaceDestroyed
→ nativeSetSurface(null)
→ Renderer::setWindow(nullptr)
→ ANativeWindow_release(old)
→ [当前缺口] render thread 应停止 acquire/present
→ wait in-flight
→ destroy swapchain-dependent resources
→ destroy old VkSwapchainKHR / VkSurfaceKHR

SurfaceView.surfaceCreated
→ nativeSetSurface(new Surface)
→ ANativeWindow_fromSurface
→ Renderer::setWindow(newWindow)
→ vkCreateAndroidSurfaceKHR
→ vkCreateSwapchainKHR
→ ImageView / Depth / Framebuffer recreate
→ render thread resume
```

## 最可能根因排序

1. **Surface 无效后仍调用 `vkAcquireNextImageKHR` / `vkQueuePresentKHR`**。[CODE]
   - 这是当前证据最直接的生命周期断裂。
2. **setWindow 与 drawFrame 缺少明确的跨线程状态同步**。[CODE][ENGINE]
   - 如果 UI/JNI 线程 release old window / recreate swapchain，同时 render thread 使用旧对象，会形成竞态。
3. **旧 swapchain-dependent resource 未见 teardown**。[CODE]
   - 当前片段只展示创建，没有展示 wait-in-flight + destroy old image views/depth/framebuffers/swapchain/surface。
4. 返回值处理缺失。
   - 片段中没看到对 `VK_ERROR_OUT_OF_DATE_KHR` / `VK_ERROR_SURFACE_LOST_KHR` 的分支；需回仓库确认。[SPEC]

## 修复分级

### Workaround

- 当 `window == nullptr` 时在 `drawFrame()` 最前面直接跳帧。
- Surface 切换时用 `vkDeviceWaitIdle` 再 teardown/recreate。

这能快速止血，但 `vkDeviceWaitIdle` 粗重，且单纯判断 window 不能彻底解决线程竞态。

### Minimal Fix

1. 引入 renderer surface state：`NoSurface / Recreating / Ready`。
2. `surfaceDestroyed`：
   - 发布 NoSurface 状态并阻止新 acquire/present。
   - 等待当前 in-flight frame fence 完成。
   - 成组销毁 framebuffer / depth / swapchain image views / swapchain / surface。
3. `surfaceCreated`：
   - 持有新 ANativeWindow。
   - 创建 `VkSurfaceKHR`、查询 extent/capabilities。
   - extent=0 时保持暂停，不创建 swapchain。
   - 重建所有 swapchain-dependent resources 后再切 Ready。
4. `vkAcquireNextImageKHR` / `vkQueuePresentKHR` 必须检查返回值，OUT_OF_DATE / SURFACE_LOST 进入同一 recreate state machine。[SPEC]

### Structural Fix

- 把 Surface 事件变成 render-thread command，而不是 JNI/UI 线程直接修改 renderer-owned Vulkan 对象。
- 用 surface generation id 保证旧 generation 的 command buffer / framebuffer 不会在新 Surface 上继续使用。
- swapchain-dependent resource 注册成一组统一重建，避免 rotation 漏项。

## Change Impact

### Must Change

- [CODE] `native/Renderer.cpp::drawFrame`：Surface 无效时停止 acquire/present；检查 acquire/present 返回值。
- [CODE] `native/Renderer.cpp::setWindow`：不要只 release/set pointer；接入状态切换和旧 swapchain teardown。
- [CODE] `native/Renderer.cpp::createSurfaceAndSwapchain`：增加旧资源生命周期边界、extent=0 handling、完整 recreate 顺序。

### Should Change

- [CODE] `native/JniBridge.cpp`：Surface 事件改为投递 render-thread command，避免跨线程直接改 renderer state。
- 增加 surface generation / lifecycle 日志，记录 Surface、swapchain、frame index。

### Can Defer

- 用 fence 精确等待替代 `vkDeviceWaitIdle` 的性能优化；先保证状态机正确。
- 把 swapchain-dependent resources 抽象成更通用 registry。

### Do Not Change

- 不修改 shader / descriptor / pipeline 逻辑，当前证据不支持这些是 rotation crash 根因。

## 回归验证

- 连续 rotation 50 次。
- surfaceDestroyed 后日志中不得再出现 acquire/present。
- pause/resume、home→back、锁屏→解锁。
- extent=0 窗口阶段不创建 swapchain。
- Validation Layer + synchronization validation。
- AGI / logcat 检查是否仍访问旧 swapchain image / framebuffer。

## Verification Gate

- G1 API 合法性：未验证；需跑 Validation。
- G2 生命周期：当前代码证据显示高风险，修复后需通过 rotation/pause/resume。
- G3 同步：未验证；需要确认 UI/JNI 与 render thread handoff 以及 in-flight fence。
- G4 Validation：未验证。
- G5 AGI/RenderDoc：未验证。
- G6 Android 平台回归：未验证；这是本问题必须通过的最终 Gate。