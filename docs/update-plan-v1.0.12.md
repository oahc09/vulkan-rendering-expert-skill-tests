# Vulkan Expert Skill v1.0.12 — Android System Rendering
## Android 系统级渲染与内容链路开发计划

> 编制日期：2026-11-01。延续移动端方向，增量资料窗口仍为 2026-10-01 至 2026-10-31，不把连续规划版本当作又过去了一个月。
> 本文是开发与验收计划，不是已实现报告。仅核查源码、前版计划和公开资料；没有修改仓库、提交、运行模型或移动设备测试。
> 版本定位：v1.0.11 解决“移动 GPU 有哪些新能力、如何条件接入”；v1.0.12 解决“这些能力如何接入 Android 的多实例、媒体输入和系统呈现链路”。

## 1. 结论与开发范围

**本版只扩展三项能力：多实例/多 Surface、相机与视频输入、HDR/广色域/透明合成。**

目标不是交付一个新的 Android 渲染引擎，而是增强已有 Skill 的知识、任务路由、实现工作流、案例和测试，让它能可靠回答：

- 同进程壁纸、预览、应用内多视图如何共享 GPU 资源又独立销毁？
- 相机/解码帧怎样接入 Vulkan，谁负责等待、持有、归还和错误回收？
- 输入颜色、shader 工作空间、swapchain 颜色空间与 Android 合成怎样匹配？

选择这三项，是为了把 v1.0.11 的外部资源、性能诊断和可选 GPU 能力接到真实业务，而不是继续新增彼此独立的扩展百科。

| 版本 | 分工 | v1.0.12 的处理 |
|---|---|---|
| v1.0.10 | 一致性、运行时包与验收证据 | 继承其检查器和发布边界；不重建。
| v1.0.11 | profiling、fault、tile-aware、OpenCL interop、可选神经渲染 | 复用已经实现的候选内容；不重复写通用外部 FD、tile 或神经 SDK 卡。
| v1.0.12 | Android 多消费者、多输出、颜色与生命周期的端到端约束 | 按本计划补齐三个主题及对应测试。

默认研究/样例使用 Java + JNI + C++17，沿用目标工程工具链，不引入 Kotlin 必需依赖。Android 14 / API 34+ 作为建议主验收区间，并不把新平台 API 或可选 Vulkan 扩展变成整个 Skill 的最低门槛。

## 2. 本次核查的真实基线

| 对象 | 已读取状态 | 证据 |
|---|---|---|
| Skill main（收尾复核） | `1f85b8b752e7008c73bc3af9a3c1f56969680bef`，入口声明 `1.0.11` | [R1] |
| v1.0.11 Skill PR | PR #7 已合并；原 head `f32a77b6cb8406a2883112dfc44ac46c3df26c70`，merge SHA 为上述 main；分支 `feat/v1.0.11-mobile-evolution` | [R2] |
| 配对测试 | 测试 PR #4 已合并；候选 head `77af638585044f1b6f1811a129e4eae59c7f2dbd`，合并提交 `3a8ea8b0f2f848d7b5380bc334633786c01e9248` | [R3] |
| v1.0.11 测试记录 | PR 记录 128 Static + 4 Snapshot；28 Live skipped；不是本次重跑 | [R2][R3] |
| v1.0.11 运行时包 | PR 报告 200 文件、896,329 bytes；源码跟踪文件 212；两种清单不能混算 | [R2] |

这里的“已读取状态”是规划快照。本轮开始读取时 main 尚为1.0.10、PR #7 为 Draft；收尾复核已确认其合并，以上表格与实施提示词已同步更新。PR 描述中残留的“Draft only”不是最新状态，合并状态以API元数据为准；但描述中的未运行测试边界不能因合并自动变成PASS。实施前仍须重新解析 main 与实际测试 SHA。

**前置条件：**v1.0.12 从上述已合入的 v1.0.11 main 开始做增量；若执行时 HEAD 又前进，先比较差异，不回滚已有成果。合并事实不等于上架发布或 Live/Device 验收通过；继续保留这些未完成项的证据边界，不把它们作为本版已取得的能力证明。

## 3. 本月新增依据与既有平台基础

### 3.1 可以吸收的本月增量

| 日期与状态 | 可核实变化 | 本版提炼，不等于强制引入框架 |
|---|---|---|
| 2026-10-07，AndroidX Graphics Core `1.1.0-beta01` | 官方 release notes 记录 SurfaceControl 释放线程竞态、buffer transform、Surface 重建卡顿等修复。[S1] | 用来设计生命周期与变换回归；其 GL/Canvas 实现不是 Vulkan 的直接补丁，不替换本技能后端。 |
| 2026-10-21，Media3 `1.12.0-alpha01` | 新增 Display P3 颜色标识及 MediaFormat/ColorInfo 映射。[S2] | 增强媒体输入的颜色元数据契约；Alpha 不当作稳定依赖，元数据映射不等于 Vulkan 导入或 HDR 呈现已经实现。 |
| 2026-10-08 扩展修订日期；本月 Vulkan 资料增量 | 官方参考页定义 `VK_GOOGLE_hdr_smpte_st_209450_metadata`，包含设备 feature、逐 Surface 能力与 HDR 动态元数据链。[S3][S4] | 给 HDR 输出增加可选分支；不默认手机支持，不把元数据接口当作完整 tone mapping 或色彩准确性证明。 |

这里采用官方参考页中的扩展标识符；旧新闻/摘要可能出现不同大小写或下划线拼法，生成代码前必须与固定 `vk.xml`/headers 核对，不能根据新闻标题拼 API。

Media3 页面当前的稳定版本与 Alpha 更新分开看。不要把页面顶部“最近更新日”当成稳定版发布时间；本版只将上述 Alpha 中明确列出的 P3 增量纳入观察与知识更新。[S2]

### 3.2 不是本月新发明，但本版必须补齐的基础

- WallpaperService 官方接口明确允许真实壁纸与预览等多个 Engine 同时存在，不能按“进程里只有一个 Renderer”设计。[S5]
- SurfaceHolder.Callback 对 Surface 的有效访问时段及销毁回调返回前的渲染线程停止访问有明确要求。[S6]
- AImage/AImageReader/AHardwareBuffer 是媒体帧及内存寿命的不同层次；它们已有的接口与同步语义是本版媒体链路的基础。[S7][S8]
- `VkCompositeAlphaFlagBitsKHR`、AHB 外部格式和 sampler YCbCr conversion 已有正式规则；不能把它们包装成本月新增 API。[S9][S10][S11]
- AppWidget/RemoteViews、应用内 Surface、WallpaperService、OEM/系统权限宿主不是同一种容器。[S12]

X 可以提供作者演示或问题线索，但本计划没有以未经核验的 X 帖子支撑结论。实施时发现新线索，需回到官方文档、固定提交或原始 issue，再决定是否纳入。

## 4. 已有内容与本版增量的边界

v1.0.11 的 `external_resource_interop.md` 已解释通用 handle、外部所有权和双向同步，并明确不能把 opaque-FD 示例当作 Camera/MediaCodec 流程。[R4] 本版扩展的是 Android 媒体生产者及 buffer queue 的端到端约束，不重写该通用卡。

候选中的 `handle_android_lifecycle.md` 仍主要按单 Activity/Surface 描述；部分正文残留 `vkDeviceWaitIdle` 超时处理、统一 idle 清理和混合 frame/present semaphore 生命周期表述。[R5] 因而 C1 开始前必须检查这些规则，避免将单 Surface 的保守处理扩大成多实例的全局阻塞。

需要定向核对而非无关全库重写：

1. `vkDeviceWaitIdle` 无 timeout 参数，不能设计不存在的该 API 超时分支。[S13]
2. submit 完成与 presentation 资源退役不能混为一谈；本版沿用并复核已有 WSI 分支，不发明“wait idle 就证明一切安全”。[S14]
3. 已获取 image、acquire 信号、frame fence、present wait semaphore 各自的异常收尾要与前版权威段一致。
4. 表达 swapchain image 时使用实际 `VkImage` 等规范类型；出现说明性假名或伪代码必须标明，不能冒充 SDK 类型。
5. 工程策略与规范分开：例如“默认统一提交线程”是候选架构，不是 Vulkan 规范要求所有引擎只能有一个线程。

## 5. C1：多 Engine、多 Surface 与系统宿主集成

### 5.1 目标

让 Skill 能分析、设计和诊断：一个进程中多个渲染实例、多个输出目标共存，单个实例关闭/旋转不破坏其他实例，同时不把设备级故障误当成 Surface 级故障。

### 5.2 必须建立的所有权地图

以下是设计参考，不是固定要求所有项目采用相同类名：

```text
Process / App
  └─ DeviceContext（是否共享需先确认）
      ├─ 资源缓存、allocator、pipeline 管理、提交协调
      ├─ RenderInstance A
      │    ├─ 场景/时域历史/帧上下文
      │    └─ Output A: surface + swapchain + generation
      └─ RenderInstance B
           ├─ 场景/时域历史/帧上下文
           └─ Output B: surface + swapchain + generation
```

分别记录 process、VkDevice、engine、surface、frame、swapchain-image、source-frame 的资源 owner。不能用一个 `currentSurface`、全局 frame index 或全局 renderFinished 数组代表全部输出。

### 5.3 开发内容

- 建立共享一个 VkDevice 与多个独立 VkDevice 的选择表，包含内存、调度、库的进程级状态和设备故障传播边界；不默认每个 Engine 建一个 device。
- 共用 device 的 Vulkan 对象按所属 device 使用；跨 device 不直接复用普通 handle。跨设备共享只有在明确的外部资源协议与能力下才评估，不作为默认方案。
- 每个 Surface 分别查询呈现支持、extent、format/colorSpace、transform、image count 等，不因第一个 Surface 可用就假定其他相同。
- host lifecycle 与 native render-thread 事件建立确认机制；销毁回调返回前完成“停止访问该 Surface”的要求，GPU/present 资源退休再按合法完成证据处理。不能只 post 一个 destroy 事件就立即返回继续访问旧 Surface。[S6]
- 引入 per-output generation 或同等防陈旧方案，拦截旧 resize、旧完成回调和旧 descriptor/view。不是强制新建另一套引擎资源管理器。
- shared queue 的 host 并发操作按规范外部同步。一个输出不可见时停止其无必要工作，但共享资源和其他输出不被顺带销毁。
- 独立处理 view 可见性、宿主暂停、Surface 有无和物理 device 状态；不能将四者压成一个全局 pause 布尔值。
- 对 shared-device `DEVICE_LOST` 给共享 device 范围的恢复策略；不承诺只重建一个 swapchain 就能让同 device 的另一实例继续正常。
- 区分壁纸 Engine 生命周期与 Activity 生命周期。锁屏/桌面、多显示器和 OEM 行为依据实际平台证据，不规定必有几个 Engine、固定回调顺序或固定共享方式。[S5]

### 5.4 公开 API / 权限边界

本版主路径只操作应用拥有或系统正常授予的 Surface。普通 AppWidget/RemoteViews 不承诺任意承载 SurfaceView 或自定义 native 渲染视图；应用内卡片可以使用自己控制的宿主，OEM 专有宿主另列权限与验证条件。[S12]

不使用 root、隐藏系统 API、绕过受保护内容或改系统权限作为默认解法。相机仅在授权且系统允许的前台测试路径启用；不把后台动态壁纸持续相机采集当作普遍可用方案。

### 5.5 交付与验收

交付一份 ownership 表、一份事件/状态表、共享/独立 device 决策表，以及对已有生命周期 workflow 的增量修订。验收应回答：

- A 输出销毁，B 输出为何仍能工作；哪些资源不能销毁？
- 一个旧 generation 回调晚到时如何处理？
- 同 device 故障与单 Surface 丢失如何区分？
- 同步停用回调和后台资源退休如何避免死锁？

## 6. C2：相机/视频帧 → Vulkan 的完整输入链

### 6.1 目标与分层

补齐 Android 媒体生产者，而不是再做一套 OpenCL interop：

```text
Camera 或 MediaCodec（分别核验支持的输出配置）
→ AImageReader / 对应 GPU 可用输出
→ AImage + AHardwareBuffer + acquire fence + 帧元数据
→ Vulkan 导入 / 访问约束
→ YCbCr 或 RGB 采样 / 处理
→ 所有 Vulkan 消费者结束
→ release 同步 / 归还 image
```

Media3 可以是媒体控制、元数据和设备差异的参考，并不假定其 effect 系统已经提供通用 Vulkan 接口。相机与视频解码是两条 producer adapter，不得用同一套未核验格式/usage 参数强行创建。

### 6.2 五类合同

| 合同 | 必须记录 | 禁止简化成 |
|---|---|---|
| 输入能力 | API/NDK/decoder、格式、usage、尺寸、是否受保护 | “能输出 Surface 就能导入 Vulkan” |
| 帧元数据 | timestamp、crop、方向/镜像、颜色标识、source generation | “只有宽高和 texture ID” |
| 内存寿命 | AImage、AHB 引用、VkImage/Memory/View、descriptor | “调用 acquire 就可以无限期读取同一帧” |
| 同步/回交 | acquire FD、GPU 完成、release FD、失败时 FD owner | “VkImage 创建成功等于生产者写入结束” |
| 队列压力 | 已获取 image 数、消费速度、丢帧/排队策略 | “每帧多申请一个 buffer 避免等待” |

### 6.3 开发内容

1. 按 AHB 属性查询和 v1.0.11 互操作卡建立导入、dedicated memory、格式/外部格式与 feature 分支；普通 format 与 externalFormat 分开处理。[S10]
2. 区分“保留底层内存引用”与“生产者允许复用某一帧”。`AImage_getHardwareBuffer` 不自动给调用者额外引用；跨越 AImage 生命周期需要依据接口持有 AHB。这个引用仍不替代归还帧时的 GPU 完成/同步合同。[S7][S8]
3. 使用异步 acquire/release 路径时，对 acquire fence、GPU wait、release fence 和 FD 接管逐项记录。不能提前把仍被 shader 使用的 buffer 归还；不能把普通 Vulkan fence handle 当 Android sync FD。
4. 在设备不支持所需外部 semaphore 路径时，给可证明正确的等待/回交备选，并标性能代价；不凭空拼跨 API 对象。
5. 两个输出共享同一输入时，归还条件覆盖所有消费者。不能 A 渲染结束就归还，而 B 仍在使用。建议用有界 frame lease/消费者计数加实际 GPU 完成证据；这些是工程结构建议，不是标准 API。
6. 明确 `acquireLatest` 与有序消费策略、最大在持 image 数和丢帧规则。source reader 重建时清理旧 generation 的导入缓存，不按裸指针永久缓存。
7. 在 YCbCr 路径核对 model、range、chroma offset、filter、外部格式及 descriptor 约束；颜色转换后还需独立处理工作空间和输出颜色合同。[S11]
8. 处理 decoder 格式改变、camera 切换、crop/旋转变化、暂停恢复、输入中断和 EOS。单帧屏幕显示正确不是持续多帧验收。
9. 不能使用 CPU 读回受保护内容作为调试回退。采集日志默认不含用户私有图像，测试以自制色条、非私密短片和可控输入为主。

### 6.4 交付与验收

在既有 `external_resource_interop.md` 增加 AHB 专用规则锚点；在既有 texture-sampling workflow 内补 producer→sampling→release 流程。不要把完整媒体教程塞入通用外部句柄表。

验收至少涵盖持续帧的 generation/timestamp、队列占用、内存/FD 是否收敛，以及消费者完成后再归还。无设备时用隔离 fixture 验证状态与计划质量，不宣称 AHB 真机导入已通过。

## 7. C3：HDR、广色域和透明合成的输出链

### 7.1 目标

使 Skill 能区分“纹理数值正确”“中间结果正确”和“屏幕合成正确”，避免把偏色、灰边或亮度异常都归因于 shader 算法。

输出合同为：

```text
输入编码/原色/范围
→ 解码、YCbCr/RGB 与工作空间转换
→ 工作精度、blend/alpha 约定
→ tone mapping / 输出编码的责任方
→ VkFormat + VkColorSpaceKHR + surface capability
→ Android compositor / display
```

### 7.2 开发内容

- 建立色彩合同表：primaries、transfer、range、bit depth、alpha mode、参考白/亮度假设分列。未拿到输入元数据时明确假设并设计验证，不仅凭文件扩展名推断。
- 明确 Display P3 属于色域，HDR 属于动态范围及编码/显示链；FP16/10-bit 格式也不能单独证明屏幕 HDR 输出。[S2][S3]
- format/colorSpace 成对从实际 Surface 可用结果中选择；设备支持某格式不代表每个输出都可用对应 HDR 呈现。
- 不承诺用 `VkImageLayout` transition 改变颜色编码。资源访问 layout、颜色空间与 alpha 模式是不同状态。
- 给 tone-mapping owner 表：应用自行处理和系统/媒体显示路径处理分开，防止两次映射。模式由目标链路证据确定，不固定“永远在这个 pass 处理”。
- `VK_GOOGLE_hdr_smpte_st_209450_metadata` 为可选路径：查询扩展/依赖、启用设备 feature，并查询当前 Surface 的支持；不支持时保持标准 HDR 或 SDR 回退，不提高整个引擎最低版本。[S3][S4]
- 扩展附加 metadata 不是像素转换器。`VkHdrSmpteSt209450GOOGLE` 的内容验证边界按官方规则说明，不将 Validation clean 写成动态 metadata 色彩正确性认证。[S4]
- 透明层分别核对 shader 输出是否 premultiplied、pipeline blend factors、`supportedCompositeAlpha` 与实际宿主的合成方式；禁止重复 premultiply 和 OPAQUE 模式下期待透明。[S9]
- WSI swapchain 与直接向应用拥有的 SurfaceControl 提交 buffer 是两条呈现路径；每条路径独立选择 dataspace/同步/回收合同，不混用颜色 API 或随意操作 WSI 内部 buffer queue。[S15]
- 结合旋转、crop 和 display 变化给重新查询与失效条件；不是只更新 viewport。

### 7.3 验证边界

为 SDR/P3/alpha 使用已知数值的灰阶、色块和边缘图样，做离屏数值检查与实际 UI 合成检查。保存源图案定义与比较阈值，不能由结果反向选择阈值。

HDR 显示验证与截图/回读分开：回读能检查渲染中间值，不自动证明实际面板亮度与系统 tone mapping。缺少 HDR 设备或校准条件时，报告功能/相对视觉检查范围，不声称绝对色准或亮度验收。

## 8. 结构与文件落点：运行时知识净增 0

### 8.1 不变项

- 继续使用八个 references 模块，不新增 mobile/system-rendering 顶层模块。
- 保留模型/宿主配置和原触发条件，只在唯一任务路由权威中增加新意图到现有章节的映射。
- hard_rules 全文、routing-entry、Evidence Map、Architecture Map、修改影响面、R1–R5 与适用的 G1–G6 均保留。
- 不调整 API/Workflow 模板既有必需标题；在对应章节内部增加明确的 HTML anchor / 子节。
- 不把本月新闻、完整测试答案、第三方模型权重或应用源码装入 Skill 发布包。

### 8.2 工作文件与唯一权威段

路径均相对 Skill 根目录。下面的锚点是拟新增/对齐的目标，不表示当前已经存在。

| 文件 | 本版职责 | 拟使用锚点 |
|---|---|---|
| `references/02_core_mental_model/android_surface_swapchain_lifecycle.md` | C1 多实例 owner 与事件模型 | `#multi-instance-ownership` |
| `references/05_workflows/04_android_integration/handle_android_lifecycle.md` | C1 状态、销毁确认、generation、局部/共享恢复 | `#multi-surface-lifecycle` |
| `references/05_workflows/04_android_integration/integrate_surfaceview_anativewindow.md` | 实际宿主与 Surface 的桥接入口 | `#android-host-contract` |
| `references/03_api_manual/10_android_platform/android_surface.md` | 平台有效访问、实例与 Surface 能力边界 | `#surface-host-boundaries` |
| `references/03_api_manual/04_buffer_image_memory/external_resource_interop.md` | C2 AHB 导入、寿命、同步与回交 | `#android-media-frame-contract` |
| `references/03_api_manual/05_descriptor/sampled_image_descriptor.md` | YCbCr/external-format 采样与 descriptor 前提 | `#android-media-ycbcr` |
| `references/05_workflows/02_render_pass_effects/add_texture_sampling_pass.md` | C2 producer 到消费/归还的步骤 | `#android-media-sampling` |
| `references/02_core_mental_model/render_target_model.md` | C3 输入/工作/输出颜色合同 | `#color-output-contract` |
| `references/03_api_manual/02_surface_swapchain/swapchain.md` | 逐输出 format/colorSpace、HDR 与 alpha 能力 | `#android-color-presentation` |
| `references/05_workflows/02_render_pass_effects/add_postprocess_pass.md` | tone mapping、blend 与最终输出的责任划分 | `#color-output-workflow` |
| `references/06_cases/04_swapchain_android/case_swapchain_android.md` | 多实例互相影响/旧代际回调的复盘或设计案例 | 保留原目录结构，增加具名案例 anchor |
| `references/06_cases/03_sync_layout/case_sync_layout.md` | AHB 早归还、多个消费者完成不同步的案例 | 同上 |
| `references/06_cases/01_black_screen/case_black_screen.md` | 已确认的颜色/alpha 输入错误与诊断分支 | 同上，不把所有色彩错误都称黑屏 |
| `references/07_integration_pack/task_routing_rules.md` | 新意图到上述权威段落 | 在现有 Android/API/Debug/Workflow 分类内增量映射 |

索引、模块摘要、来源策略、changelog 和版本元数据按实际改动同步。表中是目标落点，不要求为增加修改文件数量而触碰已正确部分。

### 8.3 预算与加载要求

以 v1.0.11 最终实际 manifest 为准；本次候选报告已达 200 个运行时文件，本版目标是**仍不超过 200 且新增运行时知识文件为 0**。这是内部包预算，不是整个源码仓库上限，也不代表所有平台采用同一限制。[R2]

通过按节扩展实现增量，不能把每个旧文件全文加进启动路径。复杂文件使用导航+显式锚点；共享规则只保留一个权威段，其他位置短摘要或引用。章节独立读取不得遗漏必要前提。

对新主题实际读取量设立记录，不虚构节省百分比。未命中这三类任务时，新章节不得成为必读；旧 12 题 input-token 目标保持原 v1.0.8 固定分母，新主题不混入原指标。

## 9. 统一工程验收场景：Media Surface Lab

这是建议放在独立测试仓库/已授权样例工作区的参考 fixture 与场景，不是要求在 Skill 包内开发一个完整产品或复制用户私有引擎。

### 场景构成

- 一个前台 Java Activity，两个应用自有 SurfaceView 或经核实的等价宿主，各自作为 Vulkan 输出。
- 可选的 WallpaperService 多 Engine/预览测试入口，按真实平台创建顺序验证，不假设必有固定数量实例。
- 默认输入为自制色条或非私密本地短片；前台授权后可切换 Camera producer。壁纸路径不依赖后台相机。
- 共享或独立 DeviceContext 按目标项目选择，默认先验证受支持的 shared-device 候选；每个输出有独立 generation 和帧/呈现资源。
- A 输出显示 SDR；B 输出测试透明合成或在明确能力下显示 P3/HDR。设备不支持时 B 正确走 SDR 路径，而不是测试直接失败。

### 操作与观测

1. 两输出同时运行，记录 sourceFrameId、engineId、surfaceGeneration、frameIndex、imageIndex、submission/completion。
2. 只销毁/重建一个输出，确认另一个继续工作；不能靠进程重启伪装局部恢复。
3. 快速旋转/resize/暂停恢复，检查旧 generation 事件、acquire 异常与 per-image present 同步。
4. 输入切换、解码格式变化或一侧降帧率，确认队列有界、过期帧策略可解释、共享输入不被提前归还。
5. SDR/P3/HDR/透明输出按能力切换；比较确定性色块、灰阶和边缘，不用主观“看着更亮”代替结果。
6. 测试结束资源回收到稳定基线，无持续新增的 FD、AHB/Vulkan allocation 或未完成队列。

建议 smoke 配置：100 次局部 Surface 重建、1,000 帧双消费者输入、15 分钟持续运行。它们只是初始复现覆盖，不是稳定性保证；实施前根据目标设备预算固定次数/时长，并保存真实结果。

## 10. v1.0.12 的里程碑

| 里程碑 | 优先级 | 主要工作 | 验收出口 |
|---|---|---|---|
| M0：冻结基线与内容对照 | P0 | 解析已接受 v1.0.11 SHA；读取工作区差异、现有 source ledger/测试；排除重复；修正命中主题的残留契约冲突 | 基线、来源、差异和待决点可追溯，不覆盖现有改动 |
| M1：多实例/多 Surface | P0 | C1 ownership/state/事件确认/generation/失败传播；权威规则按节落入原文件 | 对两实例、独立重建、设备故障、宿主边界给可实施且一致的方案 |
| M2：媒体输入与色彩输出 | P0/P1 | C2 AHB producer/lease/fence/回交；C3 色彩合同、SDR/P3/HDR、透明与回退 | 生命周期与颜色链完整，标准路径可解释；可选特性有明确 gate |
| M3：端到端与发布候选 | 必须 | 路由/模板/符号/章节读取、12 新题、原题回归、参考场景和目标宿主/设备验证、确定性打包 | 每层证据绑定最终候选，未执行不标通过，包与知识预算内 |

推荐顺序：M0 → M1 → M2 → M3。M2 的规范资料研究可与 M1 并行，写入同一权威文件时串行合并；不能在同一分支并发覆盖共有规则。

## 11. 新增 12 个行为回归场景

下列为“预期评审要点”，不能放进待测模型输入作为答案。输入 fixture、rubric、模型输出和原始日志放测试仓库。

| ID | 输入问题/干扰条件 | 合格判断重点 |
|---|---|---|
| SYS-01 | 两 Engine 共享 device；关闭预览后真实壁纸也黑屏 | 建立 owner 图；区分共享/实例/输出资源；不能给一律销毁 device 的局部修复 |
| SYS-02 | 旧 Surface destroy/resize 回调晚于新 Surface 创建 | per-output generation、停止访问确认、陈旧事件处理；不能只用全局 bool |
| SYS-03 | 两输出共享 queue，不同帧节奏；一侧 Surface lost / device lost | 区分 Surface 局部故障与 shared-device 故障；正确处理队列 host 同步和每输出 frame/image index |
| SYS-04 | 要求普通桌面 AppWidget 直接承载任意 Vulkan SurfaceView | 识别 RemoteViews/Wallpaper/应用内/OEM 宿主差别，不假定拥有系统权限；提出满足目标的合法宿主路线 |
| SYS-05 | AHB 引用已 acquire，所以提前 delete AImage，再让两个输出继续采样 | 区分内存寿命和生产者帧复用；归还覆盖全部消费者，不把引用计数当完成同步 |
| SYS-06 | acquire/release sync FD 导入失败，或拿 VkFence handle 直接回交 | 明确句柄种类、owner 和一次性消费；错误收尾不 double-close、不读未就绪输入 |
| SYS-07 | 双输出一快一慢，reader 达 maxImages，切视频分辨率 | 有界持有与丢帧策略、source generation 与缓存失效，不用无限缓存掩盖 backpressure |
| SYS-08 | Camera externalFormat、YCbCr 参数缺失，想直接当 RGBA 纹理 | 查询实际属性和采样约束；不编格式，不丢 crop/方向/timestamp/颜色前提 |
| SYS-09 | Media3 P3/FP16 已可用，是否可宣布 HDR 全链路完成 | 区分 gamut/transfer/range/bit depth/output capability；正确处理 Alpha 的版本状态 |
| SYS-10 | 第一 Surface 支持 HDR，另一 Surface 不支持，旋转后能力改变 | 逐 Surface format/colorSpace 查询，显式标准回退；不从 device 品牌推断 |
| SYS-11 | metadata 扩展名可枚举，但未启用 feature 或当前 Surface 不支持 | 拦截错误调用；查询/启用/Surface support 分层，不能把 metadata 等同实际 tone mapping 已验证 |
| SYS-12 | 半透明边缘发黑，输入已 premultiplied 却再次乘 alpha | 沿输入、shader、blend、compositeAlpha、宿主检查；不能只调曝光或把全部输出改 OPAQUE 掩盖问题 |

测试集合：v1.0.11 当前有 28 项 Live 场景；本版增加 12 项，预计为 **40 项**。实施时核实已接受基线，不以数量代替覆盖质量。旧 prompt 字节、cohort ID 与原 token 比较题集保持冻结；新 12 项单独汇总。[R3]

每题需要正反变体，如有/无 HDR 支持、单/双消费者、同/不同 device、相同/变化 generation，防止只凭关键词过关。解析器扩展需自身单测；人工语义复核仍是必要环节。

## 12. 测试层次、设备与证据

| 层次 | 本版执行内容 | 可以声称 | 不可以声称 |
|---|---|---|---|
| Source | 官方 API、固定源码、发布状态、capability 合同 | 来源已核对，设计边界有依据 | 真机可用或提速 |
| Static | 现有检查器、template/anchor/link、符号、状态 fixture、包清单、安全单测 | 文档和工具契约通过 | 模型会正确遵守 |
| Snapshot | 仅保留原历史 fixtures 与解析器契约 | 历史样本断言通过 | 当前模型 Live 通过 |
| Live | 最终 SHA，真实授权模型，原输入/输出、读取轨迹、usage、人工 rubric | 该模型与配置下的行为结果 | 所有模型与设备通用可靠 |
| Device | Java/Native/Vulkan 参考链在实际设备执行 | 指定设备/驱动/场景结果 | 未测 HDR/厂商/权限路径也通过 |
| Package | 原白名单、安全检查、两次独立构建与 CRC/hash | 候选包确定性与内容完整 | 平台已上架或审核通过 |

建议目标矩阵：至少一台 Adreno 与一台 Mali 测通用路径；HDR 屏和普通 SDR 屏做正反路径，不要求每台设备拥有新 GOOGLE 扩展。PowerVR/其他设备保留未验证格，不做全平台口头保证。

独立报告 camera 与本地视频、普通 Activity 与 WallpaperService、单输出与多输出。工具抓不到某路径时记录覆盖缺口。没有真实 HDR 测量条件时不提出绝对亮度/色准通过结论。

本版不重写已有 Live runner、计量脚本或打包工具。只增量接入 cohort 和语义题，保留原 fail-closed、无凭据 PR job、dirty-tree 拒绝、路径/symlink/ZIP 校验与输出不覆盖。

无可用授权模型或设备时 Live/Device 标记 BLOCKED 或 NOT RUN，继续交付可完成的知识与静态候选；不可改写失败回答或用手工答案填充通过。发布者可以明确接受“文档候选”，但不能声明未完成的端到端运行门槛通过。

## 13. 完成定义与范围控制

### 本版完成定义

- 三项能力均有标准路径、可选路径、前提、失败处理和可验证回退。
- 旧 v1.0.11 内容保持可达；本版不删除任何已有路由/模型/宿主约束。
- 多实例不会被简化成多个全局单例；媒体帧归还覆盖所有消费者；色彩/alpha 与资源 layout 不混淆。
- 章节独立读取前提完整；重要摘要与实现步骤无相反规则。
- 新 12 题与旧集合均进入实际测试选择器，而不是仅存 prompt 文件。
- 运行时文件净增 0；不靠隐藏或删除必要资料绕过包限制；实际输入量按模型日志记录。
- 最终证据绑定 source SHA、tests SHA、包 manifest/hash、模型/设备配置，状态分层。

### 明确不做

- 不强制接入 Media3、AndroidX Graphics、OpenCL 或神经 SDK。
- 不用 GL/Canvas/Skia 替换用户的 Vulkan 渲染任务；可借鉴公开平台生命周期经验。
- 不增加 Ray Tracing、Work Graphs、通用音视频编辑器、模型训练或整套新 RHI。
- 不把 Camera/MediaCodec 兼容性、锁屏壁纸、所有桌面宿主、HDR 扩展支持视为默认成立。
- 不构建跨进程共享渲染服务，不接管其他应用 Surface，不绕过 DRM/受保护内容/权限。
- 不自动合并、发布、上架、删除原始证据、操作凭据或改变仓库权限。

## 14. 可直接交给 Agent 的实施提示词

```text
你负责在现有 vulkan-rendering-expert-skill 基础上实施 v1.0.12：
Android System Rendering（Android 系统级渲染与内容链路）。
同时维护独立测试仓库 vulkan-rendering-expert-skill-tests。

本轮只实施三个能力：
C1 多 Engine / 多 Surface / Wallpaper 与应用宿主边界；
C2 Camera / MediaCodec → AImage/AHB → Vulkan → release 的帧合同；
C3 SDR / P3 / HDR / 透明合成的完整颜色与呈现合同。
不是开发新图形引擎，也不是把 v1.0.11 的 tile/OpenCL/neural 重做一遍。

先读取当前工作区 AGENTS、git status/diff、两仓 HEAD、SKILL.md、上游 PR、
source ledger、templates、唯一任务路由、最小启动、测试选择器和实际发布包 manifest。
本计划收尾复核的 main 是1f85b8b752e7008c73bc3af9a3c1f56969680bef（1.0.11）；
Skill PR7已合并，原候选f32a77b6cb8406a2883112dfc44ac46c3df26c70仅用于追溯资料。
实际实施从已接受的 v1.0.11 main 增量开始；若HEAD前进先比较，不回滚用户成果。
PR合并不等于已完成Live/设备验收，不继承未执行Gate的PASS。

顺序 M0→M1→M2→M3：
M0 冻结基线/来源/题库，核对本计划与上游差异。
M1 实例/输出owner、线程事件确认、generation、局部失效与device失效；
   Surface销毁回调返回前的停止访问和present退役分别处理。
   修正命中主题的既有冲突，禁止编造vkDeviceWaitIdle超时API。
M2 Android producer adapter复用外部资源卡；区分AHB引用、帧lease、
   acquire/release FD、所有消费者完成与队列背压；
   再补输入颜色→工作空间→输出format/colorSpace→alpha/compositor。
   GOOGLE HDR新扩展查支持/启用/逐Surface能力，不强制采用。
M3 保留原28题并增加本计划12题，正反条件变体、章节读取和原能力回归。
   现有runner/安全打包不重写。Live/Device无真实执行则标BLOCKED/NOT RUN。

保持八模块、最小启动、原触发条件和模型/宿主配置。
运行时知识文件净增0，原路径保留，内容落入本计划第8节的现有文件/显式锚点；
通用规范只有一个权威段，Workflow引用它，不在每处复制全文。
实际运行时包保持不超过已接受的v1.0.11内部预算（本次报告200），
不得把git源码总文件数当所有渠道包上限，不擅自删知识换预算。

Java + JNI + C++17样例优先；Android14/API34+为建议验收区间，
新API必须检查可用级别/能力，不无条件升级产品最低版本。
测试输入默认自制色条/非私密短片；相机在授权前台场景，
不默认后台壁纸可持续采集、不假定普通AppWidget可放任意SurfaceView。

保留原12题相对v1.0.8的token比较口径；新12题单列，
不要换基线重算“省30%”。不要让被测模型读rubric/历史答案，
不要手工改失败答案冒充重跑。保存实际模型、输入输出hash、读取日志、
provider usage、目标设备/驱动和各Gate真实状态。

交付：修改列表、源与capability矩阵、owner/state/color三份合同、
40题选择器/结果（以实际冻结集合为准）、包manifest/hash、
已完成/未验证/失败和回滚点。
本提示词不额外授权commit/push/merge/上架/凭据/权限操作；
远端写操作以当次用户明确授权为准。
```

## 15. 来源索引与证据分级

公开资料核查日均为 2026-11-01；latest/main 页面会变化。实施时保存确切页面/源码版本和日期。下列 GitHub 项目证据绑定本次读取 SHA；文档总结不代表本地复现。

### 项目与计划

- [R1] Skill main 入口（收尾复核固定提交，声明1.0.11）：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/1f85b8b752e7008c73bc3af9a3c1f56969680bef/SKILL.md
- [R2] v1.0.11 Skill PR #7（已合并；历史验收边界单独保留）：
  https://github.com/oahc09/vulkan-rendering-expert-skill/pull/7
- [R3] v1.0.11 测试 PR #4（本次已合并；历史题组与测试边界）：
  https://github.com/oahc09/vulkan-rendering-expert-skill-tests/pull/4
- [R4] v1.0.11 外部资源 API 卡：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/f32a77b6cb8406a2883112dfc44ac46c3df26c70/references/03_api_manual/04_buffer_image_memory/external_resource_interop.md
- [R5] 已读取的 Android lifecycle workflow：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/f32a77b6cb8406a2883112dfc44ac46c3df26c70/references/05_workflows/04_android_integration/handle_android_lifecycle.md
- [R6] 已读取的 render-target layout API 卡（用于核对主题职责，不当作颜色空间文档）：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/f32a77b6cb8406a2883112dfc44ac46c3df26c70/references/03_api_manual/07_rendering/render_target_layout.md
- [R7] 已有案例聚合文件索引：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/f32a77b6cb8406a2883112dfc44ac46c3df26c70/references/06_cases/case_index.md
- [R8] 本会话已提供的 v1.0.11《移动端能力扩展计划_2026-11-01.md》和 v1.0.10《更新计划_2026-11-01.md》，作为范围约束；不是已实施状态证明。

### 官方新增资料与平台规范

- [S1] AndroidX Graphics 发布说明，2026-10-07 的 `graphics-core:1.1.0-beta01`：
  https://developer.android.com/jetpack/androidx/releases/graphics
- [S2] Media3 发布说明，2026-10-21 的 `1.12.0-alpha01`（Display P3）：
  https://developer.android.com/jetpack/androidx/releases/media3
- [S3] `VK_GOOGLE_hdr_smpte_st_209450_metadata`：
  https://docs.vulkan.org/refpages/latest/refpages/source/VK_GOOGLE_hdr_smpte_st_209450_metadata.html
- [S4] `VkHdrSmpteSt209450GOOGLE`（启用、Surface capability及数据边界）：
  https://docs.vulkan.org/refpages/latest/refpages/source/VkHdrSmpteSt209450GOOGLE.html
- [S5] WallpaperService 与 Engine 多实例基础：
  https://developer.android.com/reference/android/service/wallpaper/WallpaperService
  https://developer.android.com/reference/android/service/wallpaper/WallpaperService.Engine
- [S6] SurfaceHolder.Callback 的有效访问与销毁回调合同：
  https://developer.android.com/reference/android/view/SurfaceHolder.Callback
- [S7] Android NDK Media：AImageReader、AImage、acquire/release API：
  https://developer.android.com/ndk/reference/group/media
- [S8] AOSP NdkImage.h 固定源码：AHB引用和异步归还说明：
  https://android.googlesource.com/platform/frameworks/av/+/754a4310b132681592fa9ed8d449b9953795056b/media/ndk/include/media/NdkImage.h
- [S9] `VkCompositeAlphaFlagBitsKHR`：
  https://docs.vulkan.org/refpages/latest/refpages/source/VkCompositeAlphaFlagBitsKHR.html
- [S10] `VK_ANDROID_external_memory_android_hardware_buffer`：
  https://docs.vulkan.org/refpages/latest/refpages/source/VK_ANDROID_external_memory_android_hardware_buffer.html
- [S11] `VkSamplerYcbcrConversionCreateInfo`：
  https://docs.vulkan.org/refpages/latest/refpages/source/VkSamplerYcbcrConversionCreateInfo.html
- [S12] Android AppWidget / RemoteViews 宿主限制：
  https://developer.android.com/develop/ui/views/appwidgets
  https://developer.android.com/reference/android/widget/RemoteViews
- [S13] `vkDeviceWaitIdle` 官方签名：
  https://docs.vulkan.org/refpages/latest/refpages/source/vkDeviceWaitIdle.html
- [S14] Swapchain Semaphore Reuse / present 退役边界：
  https://docs.vulkan.org/guide/latest/swapchain_semaphore_reuse.html
- [S15] Android NDK Native Activity / SurfaceControl 公开接口：
  https://developer.android.com/ndk/reference/group/native-activity

## 16. 本轮交付状态

- 已完成：读取前版计划、核对main和v1.0.11候选/测试状态、筛选本月相关新增资料、制定三项能力/文件落点/验收题与执行提示词。
- 未验证：本版知识尚未写入仓库；没有本版Static/Live/宿主/设备/性能/色彩或打包执行结果。
- 远端操作：无commit、push、merge、发布、权限或凭据变更；原计划文件保留。
