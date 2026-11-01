# Vulkan Expert Skill v1.0.11 — Mobile Vulkan Evolution
## 移动端新能力与实战扩展开发计划

> 编制日期：2026-11-01。月度检索窗口：2026-10-01 至 2026-10-31。
> 当前已核实 Skill main：`102c5d721dcb43a23e12d77927f2703d56c63a11`，入口仍为 `1.0.9`。
> 前置版本：v1.0.10《一致性与发布验收》目前是已制定的计划，不能视为已经实施。
> 本文交付内容为来源核查、知识增量和开发/验收计划；没有修改远端仓库，没有执行构建、模型调用、移动设备测试或发布。

## 1. 本版结论与边界

**v1.0.11 转向移动端能力扩展：让 Skill 能处理新一代移动 GPU 的性能诊断、tile-aware 渲染、跨 API 数据交换及可选神经渲染接入。**

与上一版本分工：

| 版本 | 主要目标 | 不重复做的工作 |
|---|---|---|
| v1.0.9 | 规范对齐、Descriptor Heap、最小启动与测试分层 | 不再重新新增 Heap 卡或重建 Live runner |
| v1.0.10（计划） | 跨仓契约、知识一致性、运行时包与真实验收证据 | 由该版收口；v1.0.11 继承其最终基线 |
| v1.0.11（本计划） | 移动端新知识与工程决策能力 | 不再次进行顶层目录重构，不泛化为整套移动游戏引擎 |

本版保留现有 Vulkan 最低兼容路径，不因新 SDK 示例采用更高 API 版本而提高整个项目基线。知识分为：已有标准路径、运行时确认后的可选路径、仅观察/实验路径。不能根据 GPU 品牌或新旗舰发布会直接选择实现。

研究和文档草稿可与 v1.0.10 并行；实际集成、版本验收和发布必须基于其明确接受的最终提交。若 main 已有后续改动，先对照差异，不回滚已有成果。[R1][R2]

## 2. 最近一个月：值得进入技能的真实增量

以下是工程影响筛选，不是社交平台热度榜。发布日期、功能首次出现时间和本次核查时间分开记录。

| 时间 | 来源 / 状态 | 核实的增量 | 本版落点 |
|---|---|---|---|
| 10-05 | Arm 官方技术文章 | 给出把 device-fault 信息与 GPU 地址绑定历史关联的移动端排错方法。[S01] | Device Lost 从“原因列表”升级为资源/地址/提交证据链。扩展并非本月首次出现。 |
| 10-08 | Qualcomm 官方 QHWI 框架介绍及 GitHub README | 以薄封装保留 Vulkan 与 Adreno 专项能力，提供 tile-aware 设计与样例入口。[S02][S03] | 学习能力暴露、资源生命周期和标准回退，不要求用户引擎迁移 QHWI。 |
| 10-22 | Qualcomm Vulkan/OpenCL Android 教程 | 给出共享内存、外部同步与所有权交接的工程流程。[S04] | 新增跨 API 互操作工作流；不把外部 FD 与同步 FD 混为一谈。 |
| 10-26 UTC | Filament v1.79.0 正式 GitHub release | 有跨帧 TransformManager Instance 生命周期、Java/native 配置与材质兼容性变化。[S05][S06] | 增加“更新框架时检查句柄与二进制资源契约”的案例，不复制整个 PBR 框架。 |
| 10 月 CLI 版本；10-28 官方介绍 | Android CLI / Android Performance Analyzer | CLI 加入 system trace、heap dump、profiling session 入口；官方介绍了 profiler 与 Agent 配合的流程。[S07][S08] | 建立 trace→提交/资源→代码→A/B 复测的移动端分析协议。 |
| 10-30 | Arm Neural Graphics SDK v1.1.1 正式 release | 增加 NSS/NFRU 数据采集与诊断，并存在 API/ABI 变化。[S09] | 可选神经超分/插帧接入，重点是资源契约、版本迁移与回退，不是模型训练。 |
| 10-02、10-23、10-30 | Vulkan-Docs 1.4.365/366/367 更新 | 包括 ARM cooperative-matrix layouts、GOOGLE HDR metadata、maintenance12，以及 external memory / fault / descriptor 相关修订。[S11] | 只吸收命中本版能力的规范变化；新增规范声明不等于手机驱动支持。 |

### 2.1 必须保留的时间与证据边界

- QHWI 的 10 月文章不是所有 QCOM 扩展的首次发布证明。
- Arm Neural Graphics SDK v1.1.0 的 NFRU 等能力在 7 月已经发布；本月新增依据是 v1.1.1，不能把整个 NSS/NFRU 体系都写成 10 月首发。[S09]
- ADPF、Swappy、dynamic rendering local read 是既有基础能力。本版用它们连接新的诊断/神经渲染流程，不将其包装为本月新 API。[S13][S14][S15]
- Filament main 的 release notes 已出现 v1.80.0 标题，但本次 v1.80.0 release 查询未找到对应发布。正式版本案例先使用已核实的 v1.79.0；main 新条目只列观察项。[S05][S06]
- X 用于发现作者演示与讨论线索，关键结论回到发布记录、官方文档或固定源码。本次 Arm 官方文章中的社交帖直连未取得可读全文，不将其计作独立已核实技术证据。
- GitHub README、发布说明及兼容矩阵的确认，不等于本次编译、设备运行或性能复现。QHWI README 本身也说明其 CI 只验证构建，GPU 测试需要另行运行。[S03]

## 3. 当前技能缺口与新增能力映射

当前已有 API/Workflow 索引覆盖一般资源、同步、后处理及 Android 生命周期，本版不重写这些基础内容。[R3][R4]

| 编号 | 本版能力 | 典型用户任务 | 交付后应产生的具体答案 |
|---|---|---|---|
| C1 | 移动端性能与持续运行诊断 | “前两分钟流畅，随后掉帧，应该改 shader 吗？” | 区分 GPU 工作、CPU 调度、呈现节奏与热状态，给采集入口、可比条件和代码影响面。 |
| C2 | GPU fault 资源级取证 | “只有某款 Mali 出现 DEVICE_LOST，Validation 没报错。” | 能力检查→fault/address 记录→资源代际→最近提交→候选原因，而不是先归咎驱动。 |
| C3 | Tile-aware 渲染与带宽控制 | “多 pass 后处理适合 local read、subpass 还是 QCOM tile memory？” | 根据访问模式、格式/采样数与设备能力选路，并给标准回退和测量设计。 |
| C4 | Vulkan/外部计算互操作 | “已有 OpenCL 图像算法怎样接入 Vulkan，避免 CPU 中转？” | 分开描述内存句柄、同步载荷、所有权、布局与生命周期，检查跨 API/驱动兼容。 |
| C5 | 可选移动端神经渲染 | “现有引擎怎样接 NSS/NFRU，是否适合多 Engine？” | 明确 SDK/模型/feature 契约、输入资源、history 与 pacing、设备限制、非神经回退。 |

每项都有标准/厂商/实验分支，不设置“所有移动 GPU 必须采用最新路径”的统一规则。

## 4. C1：移动端性能分析、帧节奏与持续性能

### 目标

在已有 AGI/RenderDoc 工作流上补充 Android CLI 与 APA 的真实入口，形成：

```text
应用症状与设备状态
→ 选择可用的 system trace / frame capture / counters
→ 确认进程、线程、帧、queue submission 与资源
→ 映射到项目源码
→ 提出最小改动
→ 同设备同场景复测
```

### 开发内容

1. 工具矩阵按确切版本记录 system profiler、frame profiler、GPU counter、扩展解码、导出格式及权限；一个入口可用，不代表所有功能在所有设备上可用。
2. Android CLI 10 月 release 已明确 `android profiler systemtrace`、`android profiler heapdump capture` 和 session 管理入口。[S07] 文档仅写已经核实的命令；参数在实施时以安装版本的帮助为准，不编造 flag。
3. 系统 trace 与图形 frame capture 分开解释：前者用于调度/时序，后者用于具体资源和 draw/dispatch。只有实际记录支持时，才报告带宽或特定 GPU counter。
4. 将帧节奏、动态质量与热状态纳入已有 `optimize_frame_time.md`。ADPF/Swappy 作为既有参考，不强制新增依赖。[S14][S15]
5. 若启用插帧，分别记录游戏逻辑/真实渲染帧、生成帧、最终呈现帧；禁止只用 displayed FPS 宣称交互延迟改善。呈现节奏应由明确的一方管理，不能未经验证同时叠加多个 swapchain/pacing 包装层。
6. 工具不可用时，回退已有日志、时间戳、可用 trace 和最小复现；不把没有工具访问写成没有问题。

### 交付落点

扩展既有 `04_debug_playbooks/tool_usage.md`、`05_workflows/04_android_integration/android_validation_agi_workflow.md`、`05_workflows/07_optimization/optimize_frame_time.md`。保留旧路径和 AGI 内容，通过章节说明工具版本与分支，不进行无关重命名。

### 验收

没有 profiler 数据时只给假设与最小采集方案；有数据后能把结论定位到实际事件/线程/提交及源码位置。比较结果必须记录分辨率、画质、场景、刷新率、运行时长与热状态。没有授权不得连接付费云设备、处理账号凭据或上传私有 trace。

## 5. C2：GPU Device Lost 的资源级取证

### 目标

由“VK_ERROR_DEVICE_LOST 的可能原因”推进到“故障信息与资源生命周期关联”。Arm 10 月文章提供的是诊断方法，不保证直接定位 shader 源码行。[S01]

### 开发内容

- 在初始化时查询并按路径启用 fault/address-report 能力，记录实际可用函数和 feature。
- 运行期建立地址绑定/解绑、资源 ID、资源 generation、分配区间和最近提交的关联记录；fault 后只能根据真实收集信息作判断。
- 处理地址复用、资源别名、报告粒度与缺失数据，避免把一个地址武断映射为某一行 shader。
- 分开记录 EXT 和 KHR 路径。官方 KHR 接口使用 `vkGetDeviceFaultReportsKHR` 与 `vkGetDeviceFaultDebugInfoKHR`，语义不等同于把 `vkGetDeviceFaultInfoEXT` 改后缀；不是本月首次推出的功能。[S12]
- 不具备扩展时保留通用日志、提交标记、资源历史和最小复现方法。
- device lost 后的查询/清理操作按对应规范处理，不继续普通渲染，也不把“所有 API 一律不能调用”当通用规则。

### 针对当前文档的必要修订

当前 `device_lost.md` 的决策表包含“Validation clean 排除 hazard/OOB”“多设备复现排除驱动或 watchdog”等过强剪枝。[R5] 本版配合新诊断路径修订为：

> 无报告不等于排除；跨设备差异或 WaitIdle 后现象变化只是证据，需要与实际配置、覆盖率、资源和提交记录交叉核对。

不借此扩大为全库重写；v1.0.10 已处理的通用一致性不重复做。

### 交付与验收

扩展既有 `device_lost.md`、`tool_usage.md`、必要的 `debug_utils.md`，不新增独立 crash 大模块。正常运行日志与故障报告结构都要能验证。故意制造非法 GPU 访问的样例只允许在单独授权的隔离测试设备执行，默认不在生产或日常机器上触发故障。

## 6. C3：Tile-aware 渲染与移动 GPU 快速路径

### 目标

吸收 QHWI 的具体设计方法，使 Skill 能比较三条路径，而非看到新扩展就推荐迁移：

```text
传统 RenderPass / subpass
          ↕
Dynamic Rendering + Local Read
          ↕
运行时确认后的 QCOM tile 专项路径
```

这些不是按时间顺序必然升级的三级架构。QHWI 在本版是源码和设计参考，不是强制采用的新 RHI。[S02][S03]

### 开发内容

1. 给出读取模式表：同像素附件依赖、邻域采样、跨 pass storage 访问、MSAA resolve、depth/stencil 读取分别分析。
2. 核对 local read 的 feature、properties、attachment 映射、布局与同步。Vulkan 1.4 的最低支持范围并不自动覆盖 depth/stencil 和 multisampled local read。[S13]
3. 讲清 tile-based GPU、普通 transient/lazy attachment 与 QCOM tile-memory 能力不是同一概念；不可把厂商机制泛化到所有 Mali/Adreno/PowerVR。
4. 从 QHWI 的 `qcom_tile_shading`、`qcom_tile_memory_heap`、`vk_custom_resolve` 样例定向提取查询/启用、资源生命周期和回退模式。先固定 commit 再分析，不直接复制整框架。
5. 在现有后处理工作流中增加候选方案、使用边界和 A/B 评估，不默认“Compute 比 Fragment 快”或“local read 必然不写回内存”。

### 新增文件

`references/03_api_manual/07_rendering/mobile_tile_rendering.md`

文件按现有 API Card 契约组织，内部使用稳定章节锚点；基础 API 细节引用旧卡，不重复拷贝。既有 `optimize_mobile_bandwidth.md` 和 `add_dynamic_rendering_pass.md` 增加入口及取舍。

### 验收

给出一个 standard path 和一个可选 fast path；能力缺失时落回原实现。比较图像误差、GPU 时间、可用带宽计数与显存，不预填“提速百分比”。任意邻域 blur 不能被误说成只靠 input-attachment local read 就能无条件替代。

## 7. C4：移动端外部资源与 Vulkan/OpenCL 互操作

### 目标

覆盖 Vulkan → 已有外部计算 → Vulkan 的资源传递，不让 AI 为接一个算法重新搭整套资源管理器。

### 必须分开的五份契约

| 契约 | 必须回答的问题 |
|---|---|
| 能力与设备匹配 | 两端支持哪些内存/同步 handle 类型？目标 GPU/driver 是否匹配？ |
| 内存表示 | Buffer、linear image、optimal image、AHB 的格式与布局如何约定？ |
| 同步载荷 | signal/wait 发生在哪一端？载荷能否再次导入？失败后如何收尾？ |
| 所有权与可见性 | Vulkan/外部 API 的 release/acquire、layout 与访问依赖如何组合？ |
| 生命周期 | 导出/导入成功与失败时由谁持有和关闭 FD？何时能回收底层资源？ |

Qualcomm 教程是此工作包的入口；其 opaque-FD 路径有设备/驱动匹配要求，optimal-tiling 图像还涉及专有能力。该文章将完整 AHB interop 留给后续介绍，不能把它写成已经提供 Camera/MediaCodec 的全流程实现。[S04]

### 开发内容

- 外部内存 FD 与同步 FD 分开描述，不允许一个类型的生命周期规则套给另一类。
- SYNC_FD 载荷的消费/重新导出与 Vulkan semaphore 对象的复用分开，不能当成持久 timeline handle 使用。
- Vulkan queue-family ownership 与外部 API acquire/release 分开核对；不要只添加 semaphore 就宣布数据可以读取。
- AHardwareBuffer、generic opaque FD、QCOM Vulkan opaque FD 是不同路径，保留各自的 format/tiling/ownership 查询规则。
- 使用项目现有 allocator、descriptor、retirement 与 queue 系统，先用一条受支持的 buffer 路径证明契约，再评估图像路径。
- 默认不强加 OpenCL 依赖。无现有 OpenCL 算法或运行时不支持时，优先评估现有 Vulkan Compute；不把“无 CPU staging”宣称为零带宽/零同步成本。

### 新增文件

1. `references/03_api_manual/04_buffer_image_memory/external_resource_interop.md`：规范与对象契约。
2. `references/05_workflows/04_android_integration/vulkan_opencl_interop.md`：能力检查到往返数据验证的工程步骤。

API 卡与 Workflow 不重复全文：前者定义资源/句柄规则，后者引用它完成具体集成。

### 验收

每个导入/导出与失败路径有明确 owner 和回收条件；同一组确定性输入往返后做结果校验。连续多帧、resize、后台/前台、资源退休不泄漏也不提前关闭句柄。专有图像路径只能在实际支持设备上宣称通过，其余标未验证。

## 8. C5：移动端神经超分/插帧的条件接入

### 目标

使 Skill 能评估并规划 Arm Neural Graphics SDK v1.1.1 的 NSS/NFRU 接入，而不是只介绍“AI 可以提高 FPS”。本版不训练模型、不开发完整光追/神经渲染引擎、不自动打包模型权重。[S09]

### 重点合同

| 方面 | 本版必须覆盖 |
|---|---|
| 输入 | 当前颜色、深度、motion vectors、jitter、exposure，坐标与数值约定；缺失输入的处理 |
| 时间状态 | history 生命周期、camera cut、resize、rotation、动态分辨率和场景切换时的失效 |
| 输出 | 真实帧/重建帧/插值帧、UI 合成阶段、帧节奏与交互延迟 |
| 接口版本 | SDK、API/ABI、shader、模型文件版本分别固定，升级后重建与回归 |
| GPU 执行 | 实际选中的 compute/fragment、tensor/data graph、format 与 feature 条件 |
| 引擎接入 | 原 Device/queue/resource owner 不变，明确多 context、多 Engine、多 VkDevice 的边界 |
| 能力回退 | 原生加速、仿真验证、传统时域/空间缩放、关闭插帧分别标识 |

### 来自当前 SDK 的关键边界

官方 v1.1.1 兼容矩阵区分扩展支持与启用、示例请求版本与路径最低要求，也指出后端存在进程级 Vulkan 函数表和多设备/重建限制。[S10]

据此，本版增加以下接入检查，而不是套用所有 Android 的默认假设：

- 按选中路径检查 tensor/data-graph/optical-flow 与必要算术/storage feature；不要把“Vulkan 1.4”当成神经能力保证。
- 区分手工 dispatch 与 SDK swapchain 插帧接入；timeline 和呈现依赖按路径判断。
- 多 Engine 共用一个 Device与多个独立 Device分开评估；检查 SDK 的进程级函数表、初始化并发及 Device/loader 重建。
- 仿真层仅用于功能/开发验证时，结果不当作原生移动端性能。
- SDK 代码、文档、模型文件授权分别检查。Skill 以独立摘要和链接为主，不将第三方权重与文档整包转存。

### 框架迁移案例

将 Filament v1.79.0 的跨帧 `TransformManager::Instance`、Java/native 配置和材质版本更新作为既有案例聚合文件的一段，用于训练“框架升级会改变对象句柄和资源契约”的判断。[S05][S06] 不是要求在用户引擎里引入 Filament。

### 新增文件与验收

新增 `references/05_workflows/02_render_pass_effects/mobile_neural_graphics.md`。至少产出三份明确决策：当前设备可原生接入、只能仿真验证、当前应回退。验收同时看视觉稳定性、帧节奏、延迟、显存与持续热状态，不只看瞬时 displayed FPS。

## 9. 结构、路由与体积控制

### 9.1 保持现有架构

保留 `references/00_expert_entry` 至 `07_integration_pack` 八模块。保留原模型/宿主路由与触发条件、最小启动、硬规则、Evidence/Architecture Map、修改影响面、R1–R5 及适用范围内 G1–G6。只向现有路由权威增加本版主题入口，不新增平行“mobile skill”顶层体系。

### 9.2 最多新增四个运行时知识文件

```text
references/03_api_manual/
├── 04_buffer_image_memory/external_resource_interop.md
└── 07_rendering/mobile_tile_rendering.md

references/05_workflows/
├── 04_android_integration/vulkan_opencl_interop.md
└── 02_render_pass_effects/mobile_neural_graphics.md
```

这是拟新增清单；实施时先检查 v1.0.10 最终基线是否已有等价内容，有则合并增量，不再新增重复文件。新文档使用原模板，新增主题分段读取，不全部加入固定启动集合。

### 9.3 其余改动落在现有文件

| 现有位置 | 最小增量 |
|---|---|
| `04_debug_playbooks/tool_usage.md` | APA/CLI/AGI/RenderDoc 的版本能力与输入/输出证据 |
| `04_debug_playbooks/02_crash_hang/device_lost.md` | fault/address 关联流程与非绝对化剪枝 |
| `05_workflows/04_android_integration/android_validation_agi_workflow.md` | 移动端采集、分析、复测流程，保留现有路径 |
| `05_workflows/07_optimization/optimize_frame_time.md` | 持续性能、frame pacing、真实帧与生成帧指标 |
| `05_workflows/07_optimization/optimize_mobile_bandwidth.md` | tile-aware 路径选择、测量与标准回退 |
| `05_workflows/01_renderer_setup/project_diagnosis.md` | 按任务读取移动能力矩阵；不全文展开所有厂商主题 |
| `02_core_mental_model/engine_architecture.md` | 薄封装暴露可选能力、跨 API ownership、SDK多实例风险的链接与短摘要 |
| `06_cases/` 现有聚合文件 | QHWI/Filament/Arm集成取舍案例；先通过 case_index 定位，不猜文件名 |
| API/Workflow/Case 索引与路由权威 | 增加稳定锚点；旧路径与触发回归全部保留 |
| `01_source_map_and_api_manual_strategy/update_policy.md` | 月度来源准入与过期复核，不增加新闻流水账目录 |

### 9.4 包预算与证据存放

v1.0.10 计划沿用的白名单运行时包基线为 196 文件；本版最多新增四份知识后，内部目标为运行时包不超过 200 文件。这是本项目拟定预算，不是所有平台统一官方上限。[R2]

实际按 v1.0.10 最终 manifest 重算；不能把 Git 源码总数当运行时包总数。来源抓取、样例副本、编译日志、APK、trace、模型回答和性能数据放独立测试仓库或运行产物；不放进 Skill 启动包。若预算不够，先评估复用旧文件，不擅自删知识或证据。

## 10. 四个实施里程碑

开始前冻结 Skill/tests SHA 和 v1.0.10 接受状态；解析外部 release/tag 为确切 commit，区分 source-read、build-tested 与 device-tested。以下为计划而非已完成项。

| 里程碑 | 优先级 | 范围与交付 | 完成条件 |
|---|---|---|---|
| M1：移动端诊断 | P0 | C1 性能/工具流程 + C2 fault 取证；完善设备/driver/tool证据 | 能从症状给最小采集方案、从实际证据缩小源码范围，不能无依据排除根因 |
| M2：GPU 数据路径 | P0 | C3 tile-aware 卡、C4 interop 卡与工作流；明确标准回退 | 两组完整能力分支、owner/同步/失败处理和可复测方案，文档/符号回归通过 |
| M3：神经与框架接入 | P1 | C5 可选 workflow、Filament/QHWI 迁移案例 | 能力/输入/版本/多实例/回退合同清晰，至少有支持与不支持两类输入验收 |
| M4：集成与版本验收 | 必须 | 路由、章节独立读取、12项移动题、实机验证矩阵、包manifest | Static/Snapshot/Live/Device各自报告，最终SHA可追溯，不把缺失证据变为PASS |

M1 与 M2 的独立资料研究可并行；共享索引、路由和交付包清单由一个集成步骤收口。涉及同一个文件的内容修订不要由多个 Agent 无协调同时覆写。

## 11. 本版新增 12 个移动端验收场景

所有题目先固定判据，原始问题不提供答案；保留失败输出。新题与 v1.0.10 最终接入的历史题库分别统计，不偷换旧基线。

| ID | 输入/变体 | 关键通过标准 |
|---|---|---|
| MOBILE-01 | 新 Android CLI 可以录 trace，但目标设备拿不到 GPU counter；随后提供 trace | 不声称已有带宽数据；区分 system/frame profiling，把实际事件映射源码 |
| MOBILE-02 | GPU短测快但十分钟后掉帧；启用插帧后呈现FPS升高却延迟变差 | 区分渲染/生成/呈现帧、热状态、pacing owner与延迟，不凭FPS宣称优化 |
| MOBILE-03 | Vulkan1.4设备想用 depth/MSAA local read | 分别检查实际properties，不把核心化当全范围保证 |
| MOBILE-04 | 同一后处理在Adreno与Mali部署，只有一侧具备QCOM tile能力 | 可选路径按feature选择，另一侧保留标准路径，不要求更换GPU |
| MOBILE-05 | 交换Vulkan/OpenCL opaque FD，仅device UUID相同但driver UUID不同 | 识别互操作兼容性缺口，不直接继续导入并承诺可用 |
| MOBILE-06 | 同一sync FD多帧复用，并将optimal image直接走通用opaque路径 | 分离sync载荷与memory handle，指出待验证layout、owner与失败回收 |
| MOBILE-07 | Camera/AHB输入与generic opaque FD样例混用 | 区分AHB/外部格式与通用FD路径，不照搬不适用的ownership/layout假设 |
| MOBILE-08 | Validation clean但Mali device lost，出现可复用GPU地址 | 不排除OOB/use-after-free；利用绑定代际、fault与提交记录，不能伪定位源码行 |
| MOBILE-09 | 开发者想把EXT fault函数改后缀得到KHR版本 | 回查并区分真实API和合法调用时机，缺扩展时回退 |
| MOBILE-10 | 新设备API1.4但无ARM tensor/data graph；只在PC仿真层跑过 | 不宣称原生神经能力或移动性能通过，给传统路径 |
| MOBILE-11 | SDK v1.1.1接入两个Engine、两个VkDevice，旋转/切场景后重影 | 同时检查进程级函数表边界、资源输入与history失效；不直接归咎模型/驱动 |
| MOBILE-12 | Filament v1.79跨帧缓存Instance并混用旧材质包；main另有v1.80标题 | 按已发布版本核对句柄/资源兼容；不把main标题当正式发布 |

### 11.1 验证分层

- **Static**：符号、字段、API Card/Workflow 模板、链接/锚点、路由可达、包清单与安全拒绝测试。负面示例中出现不存在符号不应误算成功API。
- **Snapshot**：历史固定回答只证明检查器契约；不作为当前模型通过。
- **Live**：复用已有 runner，新增12题注册及明确 rubric；保存模型/参数、候选SHA、读取轨迹、输入输出hash与原始失败。至少先做每题一次烟测；发布稳定性建议每题三次独立运行。
- **Device**：另有真实APK/场景运行才标已验证。没有GPU设备或某扩展时为未验证/不支持，不用模型文字代替。

只提供读取权限的模型执行应排除历史答案、rubric与运行报告。不得手工编辑失败回答使其通过，也不把关键词出现作为语义正确的充分条件。

### 11.2 实机矩阵建议

| 目标 | 最低需要验证的内容 | 不具备条件时 |
|---|---|---|
| 一台目标Adreno设备 | 标准路径、trace、跨API可用性、可选tile分支 | 专有扩展缺失则验证fallback，不伪填fast-path数据 |
| 一台目标Mali/Immortalis设备 | 标准路径、工具支持、fault能力查询/记录 | 无fault扩展则验证通用诊断；不在生产故意触发非法访问 |
| 一台实际支持神经SDK路径的设备 | 输入资源、history、pacing、持续时间与视觉 | 仅文档/仿真通过时标native未验证；不阻止其他模块检查 |
| 多Engine/多Surface工程 | 资源隔离、SDK context、设备共享/分离与前后台行为 | 只读源码分析只能输出风险，不能宣布可并发运行 |

硬件性能对比记录：P50/P95/P99帧耗时、CPU/GPU时间、missed-vsync、峰值内存、首用卡顿、热状态；带宽、功耗与输入延迟仅在可可靠获取时报告。固定场景、分辨率、画质、刷新率、运行条件；可选择15–20分钟持续负载测试，尊重设备热保护并明确停止条件。采集工具自身开销与正常运行测量分开。

### 11.3 token与版本证据

延续v1.0.10计量规则：历史“实际input tokens降低30%”仍只对冻结v1.0.8、相同原12题和同模型参数比较。新增移动题单独测读取量、轮数和质量；不宣称另降30%，不把字节缩小当模型计费token缩小。

最终文件/包变化后重算hash；当前main、本版候选、外部SDK/模型与测试仓库版本全部关联。缺少授权模型或设备时交付已完成的知识/静态部分，同时明确Live/Device未验证，不发布全能力已验证声明。

## 12. 持续跟进机制：追变化但不让技能膨胀

复用现有 `update_policy.md`，规定月度来源记录至少包含：

```text
source_url / upstream_repo
published_at / event_at / checked_at
release_tag / commit / content_blob
change_kind = release | spec_delta | tutorial | merged_change | proposal
mobile_relevance / capability_requirements
mapped_skill_path#section / affected_tests
adoption = include | background | watch | exclude
verification = source_read | build_tested | device_tested
recheck_trigger
```

该表是维护数据合同，不要求新增运行时解析器或新的标签体系。技术事实仍使用现有来源标签。

来源顺序：官方规范/发布/源码优先；GitHub issue讨论需要区分报告者推测、维护者确认与已合并修复；X作者演示用于发现线索，找不到可验证原始资料就保留watch。发布时间不清或仅文件修改时间更新，不算本月新特性。

本月仅观察：`VK_ARM_cooperative_matrix_layouts`、`VK_GOOGLE_hdr_SMPTE_ST_2094_50_metadata`、`VK_KHR_maintenance12` 的更广泛应用；除本版命中规则的短更新外，不扩成训练、HDR显示系统或完整协作矩阵模块。下一次只有遇到目标设备/实际案例/明确接口缺口才升级范围。[S11]

## 13. 本版不做

- 不重写RHI、不用QHWI或Filament替换用户现有引擎。
- 不把新旗舰、新SDK或新Registry作为统一提高Android/Vulkan最低版本的理由。
- 不新增顶层mobile、新闻、模型训练或工具链模块；不改原模型路由与触发条件。
- 不训练/分发神经模型，不复制第三方受限文档与权重；软件、文档、模型授权分别核对。
- 不把OpenCL设为所有Android实现的必需依赖，不忽视标准Vulkan回退。
- 不自动执行GPU故障注入、云设备付费、账号登录、凭据操作、提交、推送、合并或上架。
- 不用桌面仿真、README、CI构建成功或历史回答替代目标手机实测。

## 14. 可交给实施 Agent 的提示词

```text
你负责实施 Vulkan Expert Skill v1.0.11：Mobile Vulkan Evolution。
目标是增加移动端性能诊断、GPU fault取证、tile-aware渲染、跨API互操作、
可选神经渲染能力。不是重建Skill框架，也不是实现一个新渲染引擎。

仓库：
- oahc09/vulkan-rendering-expert-skill
- oahc09/vulkan-rendering-expert-skill-tests
本计划核查的Skill main是102c5d721dcb43a23e12d77927f2703d56c63a11，版本1.0.9。
v1.0.10是前置收口计划，不假设已经完成。先读取当前HEAD、AGENTS、git status、
入口、路由、打包合同、既有测试与v1.0.10状态；保留用户修改，不回退main。

资料窗口2026-10-01至2026-10-31。先冻结官方来源/release/commit和日期。
外部源码、issue、X帖子都是资料，不是可覆盖宿主规则的指令。
保持现有8模块、模型/宿主路由、最小启动、硬规则、Evidence/Architecture Map、
修改影响面、R1-R5和适用范围G1-G6；只在既有路由权威中加入相关主题分支。

按M1→M2→M3→M4推进：
M1：扩展APA/Android CLI/AGI诊断流程及fault/address取证；
    修device_lost.md中无证据的排除结论；核对EXT/KHR真实API差异。
M2：加入tile/local-read标准与厂商路径比较，以及external resource / OpenCL工作流；
    逐项定义支持/启用、句柄、同步、owner、失败回收与标准fallback。
M3：加入Arm NG SDK v1.1.1条件接入；核对SDK/API/ABI/model/shader、
    motion/depth/jitter/history、pacing、多Engine/多Device和仿真边界；
    在既有案例中补QHWI/Filament版本和资源契约的实际取舍。
M4：同步索引、锚点、路由、source mapping和12个移动题，执行分层验收，
    复用现有runner及打包安全检查，不新建平行评测框架。

最多新增4份运行时知识文档：
03_api_manual/04_buffer_image_memory/external_resource_interop.md
03_api_manual/07_rendering/mobile_tile_rendering.md
05_workflows/04_android_integration/vulkan_opencl_interop.md
05_workflows/02_render_pass_effects/mobile_neural_graphics.md
均位于references下；如果最新基线已有等价文件则扩展它。
新文档服从既有模板，不放空骨架、不批量复制官方手册。
原始来源清单、APK/trace/性能数据/模型输出放测试仓库或运行产物，
知识包按实际白名单manifest计数；196+4→200仅是当前内部预算推算，必须重算。

所有手机能力运行时查询；API版本、支持、启用、实际可用与测得收益分开。
不把厂商样例扩展为所有手机保证，不强迫迁移更高Vulkan基线。
QHWI构建CI不是GPU测试；PC仿真不是神经原生性能；main release-notes不是正式release。
FD memory与sync payload、所有权与同步、SDK context与进程级全局状态必须分开。

验证使用Static / Snapshot / Live / Device独立结果。旧场景继续保留；新12题
必须注册到执行入口。真实模型调用记录SHA、模型参数、读取轨迹和原始失败，
不手改快照冒充重跑。新增移动题不混入历史30% token目标的原12题分母。
无授权模型/设备就明确BLOCKED或未验证，继续其他可执行检查。

本计划本身不是提交/推送/合并/上架授权。按实际用户授权实施；不操作凭据或权限，
不擅自部署、不自动故障注入、不删除重要数据。
交付：差异文件、来源映射、能力矩阵、标准回退、测试分层结果、manifest/hash、
未验证项与回滚方法。完成声明只针对最终受测SHA。
```

## 15. 来源索引

所有网页/默认分支可能变化。以下是2026-11-01读取到的来源；实施时需把适用上游版本进一步固定到commit。来源说明不代表源码全量审计。

### 本月主要来源

- **[S01] Arm，2026-10-05，Device Lost与地址绑定诊断。**
  https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/diagnosing-vk-error-device-lost-on-mali-gpus-with-vk-ext-device-fault
- **[S02] Qualcomm，2026-10-08，QHWI框架介绍。**
  https://www.qualcomm.com/developer/blog/2026/10/build-portable-rendering-systems-across-vulkan-directx12-with-qhwi
- **[S03] Qualcomm QHWI GitHub README。** 本次main文件blob：`4bfc4afa56f3138f22cfba290f08b1bcfdd4b61b`；确认平台、样例与build-only CI边界，未编译或运行。
  https://github.com/qualcomm/qhwi/blob/main/README.md
- **[S04] Qualcomm，2026-10-22，Android Vulkan/OpenCL互操作教程。**
  https://www.qualcomm.com/developer/blog/2026/10/how-to-share-vulkan-opencl-workloads-android-adreno-gpus
  其样例入口（实施阶段继续固定源码审查）：
  https://github.com/SnapdragonGameStudios/adreno-gpu-vulkan-code-sample-framework/tree/main/samples/opencl_interop
- **[S05] Filament v1.79.0正式release，2026-10-26T23:44:28Z。**
  https://github.com/google/filament/releases/tag/v1.79.0
- **[S06] Filament release notes。** 本次main blob：`82cf76a6a54bdbb42041645d2a80f19c2677715b`；main的v1.80标题不是已发布证据。
  https://github.com/google/filament/blob/main/RELEASE_NOTES.md
- **[S07] Android CLI，Version 1.1.16717390，October 2026。**
  https://developer.android.com/tools/agents/android-cli/release-notes
- **[S08] Android Dev Summit开发工具与性能总结，2026-10-28。**
  https://developer.android.com/blog/posts/android-dev-summit-26-developer-tools-performance
- **[S09] Arm Neural Graphics SDK v1.1.1，2026-10-30T02:06:02Z。**
  https://github.com/arm/neural-graphics-sdk-for-game-engines/releases/tag/v1.1.1
- **[S10] Arm SDK v1.1.1兼容矩阵（固定tag）。** 本次blob：`6545894383754d52454d3491952519e26865a5a4`；特别核对runtime要求与process-global function table限制。
  https://github.com/arm/neural-graphics-sdk-for-game-engines/blob/v1.1.1/docs/compatibility_matrix.md
- **[S11] Khronos Vulkan-Docs，10月规范修订日志。** 本次blob：`3434a870d4823d7e786822b5adfc537e48ec96f2`；10-02/23/30分别为1.4.365/366/367。
  https://github.com/KhronosGroup/Vulkan-Docs/blob/main/ChangeLog.adoc

### 支撑边界的既有规范与资料（不计本月首发）

- **[S12] VK_KHR_device_fault。**
  https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_device_fault.html
- **[S13] VK_KHR_dynamic_rendering_local_read，含1.4提升后的范围边界。**
  https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_dynamic_rendering_local_read.html
- **[S14] Android Dynamic Performance Framework。** 页面标记2026-02-26更新。
  https://developer.android.com/games/optimize/adpf
- **[S15] Android Frame Pacing / Swappy。**
  https://developer.android.com/games/sdk/frame-pacing
- **[S16] Android Performance Analyzer release notes。** 用于区别已有工具与本月新入口、stable/beta/canary的能力，不认为所有新功能均为稳定版。
  https://developer.android.com/android-performance-analyzer/release-notes

### 项目证据

- **[R1] 本次Skill main ref与固定入口。**
  https://api.github.com/repos/oahc09/vulkan-rendering-expert-skill/git/ref/heads/main
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/102c5d721dcb43a23e12d77927f2703d56c63a11/SKILL.md
- **[R2] 前置v1.0.10计划及现有发布合同。** 以前一轮交付的《Vulkan_Expert_Skill_v1.0.10_更新计划_2026-11-01.md》为前置，不把它写成已完成；包口径依据：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/102c5d721dcb43a23e12d77927f2703d56c63a11/AGENSI_RELEASE.md
- **[R3] 当前Workflow索引。**
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/102c5d721dcb43a23e12d77927f2703d56c63a11/references/05_workflows/workflow_index.md
- **[R4] 当前API索引。**
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/102c5d721dcb43a23e12d77927f2703d56c63a11/references/03_api_manual/api_index.md
- **[R5] 当前Device Lost Playbook。**
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/102c5d721dcb43a23e12d77927f2703d56c63a11/references/04_debug_playbooks/02_crash_hang/device_lost.md

## 16. 本轮完成状态

已完成：10月移动端技术资料筛选、正式release日期核对、当前技能入口/索引/相关Playbook核查、v1.0.11范围和开发/验收计划、AI实施提示词。

未执行：第三方样例编译、所有GPU/Android验证、真实模型调用、token/性能测量、仓库写入、提交/推送/合并及发布。X直连覆盖有限，未核验社交帖不进入技术事实结论。
