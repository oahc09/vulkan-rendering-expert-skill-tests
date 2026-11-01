# Vulkan Expert Skill v1.0.13 开发计划
## Shader、Pipeline、资源加载与 GPU-driven 规模化渲染

> 编制日期：2026-11-01。
> 计划状态：待实施。本轮完成范围整合、固定基线读取和关键官方资料核对；未修改远端仓库，未执行编译、模型调用或 GPU 测试。
> 版本决定：将原建议放在 v1.0.14 的 GPU-driven 与规模化渲染正式并入 **v1.0.13**，与 Shader、Pipeline、资源加载一起交付。
> 交付定位：升级专家 Skill 的知识、判断、工作流与验证能力；配套测试仓库提供可复现的精简实验，不在本版另造完整商业渲染引擎。

---

## 1. 版本目标与边界

本版使 Skill 能回答并指导解决以下完整工程问题：

**新内容如何正确构建、按预算进入运行中的引擎，并通过 GPU 剔除、LOD 和间接绘制扩展场景规模，同时保留低能力设备的正确回退？**

```text
Shader / 材质 / 纹理 / 几何内容
→ 编译产物与接口校验
→ Pipeline 准备、资源转码与预算化上传
→ 场景数据发布与资源驻留
→ GPU Frustum Culling / LOD / 可选 Hi-Z
→ 可见实例与间接命令生成
→ 状态分组、Indirect Draw / MDI
→ 呈现与性能取证
→ 跨帧复用、取消、退休与预算回收
```

五条主线都属于 v1.0.13，不再把核心 GPU-driven 链路后置：

| 编号 | 能力主线 | 本版必交付内容 |
|---|---|---|
| C1 | Shader 工程化 | 产物契约、接口兼容、变体、热更新、精度边界 |
| C2 | Pipeline 卡顿治理 | 分层缓存、预热、异步创建、失效恢复、可选 Pipeline Binary / GPL |
| C3 | 资源流式与预算 | KTX2/Basis 条件接入、纹理与几何上传、驻留、取消、回收 |
| C4 | GPU-driven 基础链路 | CPU 对照、GPU 剔除、固定槽位与紧凑命令、Indirect Count、同步与回退 |
| C5 | 规模化渲染 | LOD、Hi-Z、实例/粒子批处理、多视图状态、Mesh Shader 条件路径、联合性能验证 |

“必交付”指规则、工作流、回退、测试输入与可执行验证材料齐全。目标设备不支持的增强功能不强制执行，但必须说明能力判定、回退及未验证状态。缺少 GPU 或授权模型时，不得把静态产物称作运行通过。

### 不扩大到以下工程

- 不要求业务引擎全量迁移至 Bindless、Descriptor Heap、Mesh Shader、独立 Compute Queue 或新的 RenderGraph。
- 不新增 Ray Tracing、完整虚拟纹理系统、通用 GPU 排序库、3DGS 专用压缩渲染器、神经模型训练。
- 不把 Device Generated Commands 作为基础路径；本版只在已有间接命令卡中解释其与普通 MDI 的边界及后续接入点。
- Shader 热更新仅指授权开发环境中的迭代，不包含线上远程资源发布服务。
- 不建设新的模型评测平台、独立 Agent 调度系统或第二套引擎资源管理器。

---

## 2. 固定基线与继承要求

| 项目 | 本次读取值 |
|---|---|
| Skill 仓库 | `oahc09/vulkan-rendering-expert-skill` |
| Skill main | `d049afefaec8539cecca5f8e37c4cd66ec9da728` |
| 当前入口版本 | `1.0.12` |
| 测试仓库 | `oahc09/vulkan-rendering-expert-skill-tests` |
| 测试 main | `9278d9be3a7a4d4e919ac36927ee165a433450a9` |
| 当前测试 release-contract 所指 Skill | `5c53ec2a600c96d57399a942236640b7061c43fe`，expected version `1.0.12` |
| 当前运行时包内部预算 | `max_runtime_files: 200`；这是项目契约，不是本次重新核实的平台统一上限 |
| 当前 Live 题库 | 40 场景；“题库存在”不表示已实际运行 |

来源：[R1–R5]。实施时重新解析 HEAD，保留最新用户改动。release-contract 指向的候选与 main SHA 不同，先核对 tree/差异及其证据范围，再更新；不同 SHA 既不能自动视为不一致，也不能自动继承 PASS。

### 必须继承的能力

保持八个 references 模块、公开路径、现有触发条件和模型/宿主配置；保留 hard_rules 全文、routing-entry、按段读取、Evidence Map / Architecture Map、影响面分类、R1–R5、适用范围内的 G1–G6、安全打包与历史证据隔离。

v1.0.11 的可选能力、fault、移动热状态、外部互操作，以及 v1.0.12 的 Engine/Surface/resource generation、媒体帧与色彩合同不能回退。不能以本版“GPU-driven”为理由将 Surface 丢失升级为整个 Device 重建，或让一台设备的性能结论覆盖其他 GPU。

---

## 3. 先处理既有内容的命中问题

本版不是从零写教程。已有 `shader_binding_workflow.md`、`reduce_pipeline_creation_stutter.md`、`add_texture_resource.md`、`indirect_commands.md` 和 `compute_to_graphics_sync.md` 是主要增量落点。[R6–R10]

| 现有位置/表述 | 风险或不足 | 本版处理 |
|---|---|---|
| indirect 卡中的 `DISPATCH_INDIRECT_BIT` | 容易误导为 Vulkan 同步阶段；间接 dispatch 的参数读取也属于 DRAW_INDIRECT | 按 Registry 与规范修订示例、表格和反例；不要生成不存在的阶段枚举。[S2–S4] |
| indirect dispatch 的 `x*y*z` 与 `maxComputeWorkGroupCount` 比较 | 混淆 workgroup 数量各维限制和局部 workgroup invocation 限制 | 分别核对 x/y/z；另查 LocalSize、每维 workgroup size、总 local invocations。[S3] |
| 固定 drawCount 被描述为“不是真正 GPU-driven” | GPU 改写固定槽位的 instanceCount 也可决定可见性 | 保留固定槽位合法基础路径；Count 是可选增强，不强制回读或迁移。[S1、S5] |
| `vkCmdDrawIndirectByteCountEXT` 归为 `VK_EXT_multi_draw` | 扩展归属和语义错误 | 归回 transform feedback；其计算的是该 draw 的 vertex count，不是普通命令数组长度。[S6] |
| Shader reflection 等同于唯一可用 Descriptor schema | 反射不包含所有引擎语义；合法布局也未必逐字等同 | 区分兼容性、引擎策略、动态 UBO、允许的 stage/count/range 规则，按规范和目标环境验证。[S9、S15] |
| specialization / GPL 直接等同于减少 Pipeline 或显著加速 | 编译产物数量、Pipeline 组合、最终性能不是一回事 | 去掉无条件收益归因；将特化值与兼容状态纳入 key，A/B 测量。[S7、S8、S18] |
| 普通纹理创建被要求先有 Surface/swapchain | 引擎初始化顺序被写成通用 API 约束 | 分开描述 Device 能力与项目依赖；允许有条件的离屏创建/上传。[S16] |
| Compute→Graphics 只给一条抽象 barrier | 未区分 command/count、SSBO、vertex/index 等消费者 | 增加按资源角色展开的同步表；覆盖 reset、多阶段 dispatch、跨帧和跨 queue。[S2、S4] |

审查仅改本版命中的错误与依赖链；不对无关章节进行无依据大改。教程和 Samples 也是参考，不高于规范；出现文档笔误时必须回查 API Reference/Registry。

---

## 4. C1：Shader 工程化

### C1.1 编译产物合同

建立一份由现有构建流程产出的 manifest，至少记录：

```text
sourceHash / includeDependencyHashes
compilerName / compilerVersion / compilerOptions
sourceLanguage / entryPoint / stage
targetVulkanEnvironment / targetSpirvEnvironment
requiredExtensions / requiredFeatures / requiredLimits
reflectionHash / interfaceContractHash / bytecodeHash
materialSchemaVersion / buildRevision
```

这是建议的工程记录结构，不是 Vulkan 官方结构体。字段由现有项目语言/格式承载，不强制增加运行时 JSON 解析依赖。

验收将下列状态分开：编译通过、SPIR-V 校验通过、接口合同通过、设备能力满足、Pipeline 创建通过、图像/数值正确。任一步成功不替代其他步骤。编译器、反射器、SDK 和命令参数在实施时固定版本，不编造 CLI。

### C1.2 资源接口与数据布局

需要校验 descriptor 类型与数量、set/binding、使用阶段、push constant 范围、block member offsets、matrix/array stride、顶点输入及 stage interface。输出兼容与不兼容的原因，而不是只比较文本。

特别要求：

- 动态 UBO 是引擎绑定策略之一，不能仅凭 shader 反射普通 uniform block 就判 `UNIFORM_BUFFER_DYNAMIC` 非法。
- 允许的 stageFlags 超集、descriptor 数量与 push constant 跨阶段重叠必须按目标规范核对，不能把“与反射不完全相同”统一判错。
- `std140`、`std430`、scalar layout、host padding 分开；对 GPU 场景结构、间接参数和实例 metadata 给出实际 offset/stride 校验。[S9]
- specialization constants 影响使用方式时，反射结果与选定特化组合一起核验，不无限穷举所有不使用的组合。

### C1.3 开发期热更新

将修改分为：实现变化且接口兼容、接口变化、目标 feature 变化。为每类输出具体影响文件、Pipeline key、Descriptor/PipelineLayout/材质数据的迁移边界。

```text
请求 reload
→ 构建/校验新的完整产物
→ 后台创建兼容 Pipeline
→ 核对 Engine/Device/material generation
→ 向新命令录制路径发布新版本
→ 旧命令与资源完成后退役
```

新旧 Pipeline 可以合法并存；不把“GPU 完全空闲”当作唯一切换方法。失败时保留旧可用路径；取消后到达的完成回调不可重新发布旧代际资源。接口不兼容时不能只换 shader module，必须协调相关布局与数据。

### C1.4 变体与移动精度

分别统计 source variants、SPIR-V 产物、Pipeline key、实际使用组合；避免把减少 shader 文件数量写成减少 Pipeline 数量。[S18]

FP16 算术、16-bit storage、stage I/O、整数能力分别检查。[S10] 默认保持剔除判定、深度比较等敏感环节的保守精度；降精度必须验证视锥边界、远近尺度、NaN/Inf、动画和跨 GPU 结果。不能仅凭静态截图或吞吐量决定精度可用。

**C1 交付**：原文件中的产物合同与热更新流程、接口正反例、可编译 Shader fixtures、反射/布局检查与取消代际测试。

---

## 5. C2：Pipeline 卡顿治理

### C2.1 分层缓存与正确的 key

区分源码编译缓存、SPIR-V、引擎 Pipeline 状态 key、`VkPipelineCache`，以及可选的 Pipeline Binary；不要视为一种可任意交换的 cache。[S7、S8]

引擎 key 覆盖真正相关的 shader/interface、特化值、渲染目标兼容性、静态状态、动态状态声明、采样数及所用 feature 路径。不按 shader 文件名或单个 hash 直接复用所有状态。

磁盘包记录兼容标识、长度、校验值、生成环境和版本。未知/损坏/不兼容输入拒绝使用，走已验证的冷创建或旧可用路径；不修改 opaque cache 字节，不自动下载第三方驱动二进制。

### C2.2 预热与后台创建调度

预热列表按首屏、近期可见场景与材质分组；GPU-driven 的 batch 状态也进入需求列表。后台任务按 CPU 时间、队列长度与内存压力限流，不一律设“线程越多越快”。

任务状态建议：`Queued → Building → Ready → Published → Retired`，另有 `Canceled / Failed / Obsolete`。需要去重、错误回传、旧 Device generation 拒绝、重试限额和兼容 fallback。

后台创建使用的 create-info、pNext、shader 数据与其他输入必须在调用期间有效；不能把临时栈对象指针传给迟到的任务。Device teardown 必须协调正在运行的创建任务。CPU 任务生命周期与 GPU 对象退休是两套完成条件。

### C2.3 Cache 并发与可选路径

- 按实际 cache flags、相关命令的 host synchronization 要求选择共享锁、每线程 cache 或 merge 策略，不使用“所有 Vulkan 对象都 internally synchronized”等笼统规则。[S7、S15]
- Pipeline Binary 明确支持/启用、key、二进制取得/消费、缺失/不兼容回退；不能假设 Vulkan 1.4 自动提供扩展，也不保证跨驱动可迁移。[S8]
- GPL、derivative、特化值分别给收益条件、额外成本与不适用场景；不要求移动端统一开启。
- 发布新 Pipeline 不自动销毁旧 Pipeline；完成 CPU 发布与最后 GPU 使用退休后，才由原 owner 回收。

**C2 交付**：分层 key/失效表、异步创建状态机、取消/损坏缓存 fixtures，以及冷/热启动和首次效果切换测量方法。不得预填速度提升比例。

---

## 6. C3：纹理、几何流式加载与内存预算

### C3.1 格式选择与内容构建

使用 KTX2/Basis 作为可选内容管线参考，明确容器、传输编码、转码结果和 GPU 最终格式是不同层。[S11] 依照 format、usage、tiling、过滤和颜色语义查询目标支持；不能按 GPU 品牌假定 ASTC/ETC2/BC 全部可用。

压缩纹理的 mip、块对齐、复制区域和不能直接 blit 的格式需要独立路径；未支持所需过滤/存储操作时，离线生成或换受支持方案，不强行使用运行时 blit。

几何数据同样进入资源合同：vertex/index 格式、分配范围、mesh/LOD ID、bounds、顶点与索引偏移、generation、resident 标记。先采用普通 buffer 分段/页管理，不要求 sparse binding 或 mesh compression 专用扩展。

### C3.2 上传、取消与背压

```text
请求内容
→ CPU 解码/转码预算
→ 保留 GPU/staging 容量
→ 分批上传
→ 上传完成与访问可见
→ 发布可采样 mip / 可绘制 mesh
→ 下游使用完成后复用 staging 和旧资源
```

任务预算至少覆盖 CPU 时间、转码临时内存、上传字节、staging in-flight、GPU allocation、新旧资源并存峰值。正在上传与已经发布的资源状态分开。

取消未提交任务可以立即回收其独占 CPU 数据；已经提交的 copy 及其引用内存必须等对应使用结束。销毁一个 Engine 不能回收其他 Engine 仍引用的共享资源；使用已有 generation/引用与退休机制，不新建第二套 manager。

### C3.3 部分 mip 与真正驻留

只允许 shader 采样已初始化且合同允许的 mip。初版推荐使用视图范围/安全 sampler LOD 与版本化 descriptor 发布，避免在 in-flight 普通 descriptor set 上非法更新。view 的 baseMip 与 shader 的 LOD 语义需要一并校验。

**限制采样 LOD 不等于释放 image allocation；分配了完整 mip 链也不等于全部内容驻留可用。** 初版以低分辨率替代资源、资源整体淘汰或重新创建较小资源回收内存；若采用 sparse residency，必须另有能力、绑定和 page 生命周期证据，不将其作为本版默认。[S12、S16]

### C3.4 预算压力与恢复

预算是观测与决策输入，不是下一次分配必成功的承诺。[S12] 定义软阈值/紧急阈值、滞回、上传暂停、冷资源淘汰、驻留粗 LOD、重试退避和恢复流程。

GPU 剔除/LOD 只能引用有效驻留数据；目标 LOD 未就绪时采用保守 resident fallback 或明确的跳过/替代策略，不输出指向未上传 buffer 的 indirect command。资源迁移后刷新地址/索引表，并等待旧引用退役。

**C3 交付**：纹理与几何的生命周期/预算表、上传队列与故障注入测试、压缩格式与 mip fixtures，以及与 C4/C5 共用的 resident contract。

---

## 7. C4：GPU-driven 基础链路（本版核心，必须完成）

### C4.1 先分清几种机制

- **CPU instancing/batching**：CPU 决定可见性与状态分组，可一次绘制多个实例。
- **GPU 固定槽位间接绘制**：CPU 录制已知容量；GPU 为每个槽位写参数/instanceCount，隐藏槽位为零。无需 CPU 读取可见数量，也不要求 Indirect Count。[S1]
- **GPU 紧凑命令 + Indirect Count**：GPU 把可见项压到有效前缀并生成 count；draw 消费这个前缀。[S5]
- **MDI**：同一已绑定状态下消费多条 indirect draw 参数，不自动为每条命令切换 Pipeline、descriptor 或 blend。
- **Mesh Shader / Device Generated Commands**：独立可选能力，不是前述基础路径的前提。[S13]

这里的 GPU 生成命令指写入间接参数 `VkBuffer`，不是让 shader 录制或修改 `VkCommandBuffer`。

任何选择都须给出当前目标设备、实际启用的能力、场景特征、CPU/GPU 瓶颈与回退。保留 CPU 对照路径，用于正确性验证与低能力设备运行。

### C4.2 场景数据合同

以下名称为引擎层建议数据，不是 Vulkan API：

| 数据 | 最小职责 | 需要保护的条件 |
|---|---|---|
| Object / Instance table | 稳定 ID、transform、bounds、material、mesh/LOD 引用 | 非均匀缩放/动画后的保守 bounds；地址/索引与 generation |
| Mesh / LOD table | vertex/index 范围、各级误差与 resident 状态 | index 类型、vertexOffset 有符号、资源已就绪 |
| Material / Batch table | Pipeline 与绑定模型的兼容批次 | 不合并不兼容状态；透明规则独立 |
| Visible list | 可见实例或对象 ID | 容量、有界写入、跨 pass 可见性 |
| Indirect command buffer | Vulkan 定义的 draw/dispatch 参数 | usage、offset、stride、范围及 enabled features |
| Count / Overflow | 合法命令数与溢出标记 | reset 与 append/finalize 依赖；无越界写 |
| Frame/View context | 相机、资源快照、可见结果、完成标记 | 多帧/多输出不串用列表和 Hi-Z 历史 |

CPU 数据准备与 GPU 读取之间采用已有更新策略。既不要求全场景每帧重传，也不将“用了 SSBO”误称为已完全 GPU-driven。

### C4.3 能力分层与回退

| 层级 | 路径 | 前置检查 | 回退 |
|---|---|---|---|
| G0 | CPU 剔除 + Direct/Instanced Draw | 基础绘制与资源合同 | 基准及调试路径 |
| G1 | Compute 剔除 + 固定槽位 indirect | 所用 queue 支持 Compute；合法 storage/indirect buffer；参数布局及同步 | G0；没有 MDI 时可逐条 drawCount=1，不能据此承诺省 CPU |
| G2 | 紧凑列表 + Count / MDI | 对应核心/扩展路径及 feature 已启用；maxDrawIndirectCount；countBuffer 合法 | G1，不把 count 回读 CPU 当唯一回退 |
| G3 | Bindless/BDA 优化数据访问 | descriptor indexing 的具体子特性、非均匀索引、地址与资源生命周期分别满足 | 分材质/批次 descriptor 与普通 SSBO |
| G4 | Mesh Shader 或 async-compute 增强 | 实际扩展、feature、limits、队列条件与 profile 证明 | G1/G2；保持相同 scene/residency 接口 |

`multiDrawIndirect`、`drawIndirectFirstInstance`、Indirect Count、shader draw parameters、BDA 和 descriptor indexing 不是同一个开关；核心化、支持与已启用分别记录。[S5、S13、S14]

`firstInstance` 必须为零的设备可选择固定批次映射、合法的实例索引表或 CPU 逐批设置基址；不能为了映射 object ID 偷写非零值。任何替代方案仍需核对所用 shader 内建变量和 buffer 范围。

### C4.4 Frustum culling 与命令生成

初版采用保守 sphere/AABB 剔除。处理坐标空间、非均匀缩放、负缩放、动画 bounds、近平面交叉、数值异常和多个 view；无法可靠判断时保留对象，而不是激进剔除。

固定槽位路径要求每帧更新所有相关槽位，不留下上一帧的可见状态。紧凑路径分清：计数复位、候选判定、有效项写入、count finalize、draw 消费。

不能只计算可见数而不压缩命令前缀：如果前几个槽位不可见，后续 drawCount 小于容量时直接执行旧数组前缀会漏画。

### C4.5 容量、溢出与非法命令防护

规范中的 `maxDrawCount` 限定执行数量，不替 compute 的越界写兜底。[S5] 必须同时实现：

1. 分配容量与字节范围检查；CPU 算术使用防溢出计算。
2. append 索引在写入前判界，并处理计数器数值溢出；记录 overflow，不写 buffer 外。
3. 最终 count、实际写入前缀与命令区间一致；不读取未初始化命令。
4. 超载时给可观察策略：扩大下一帧容量、拆批、降低粒子数量或回退 CPU；不可静默丢失关键内容。
5. `offset + (count - 1) * stride + sizeof(command)` 等边界按具体 API 的 count/stride 条件核对，不用一个保守近似冒充精确 VU。
6. Indirect Dispatch 各维 workgroup 数、局部 workgroup 大小、invocation 数分别检查；零任务和极端值有测试。[S3]

固定参数缓冲区、GPU 写入区域与 count 都按最后使用完成复用。`robustBufferAccess` 不替代命令生产端范围校验。

### C4.6 同步合同：参数读取与 Shader 数据读取分开

以下为**同一支持相应阶段的 queue、Sync2 已启用**时的设计模板，不是所有管线可直接复制的一组万能 mask。legacy 路径另给等价可用表达；跨 queue 必须补 semaphore 与必要的所有权处理。[S2、S4]

| Producer / 资源 | 源阶段 / 访问 | 实际 Consumer | 目标阶段 / 访问 |
|---|---|---|---|
| `vkCmdFillBuffer` 清零 count | `VK_PIPELINE_STAGE_2_CLEAR_BIT` / `VK_ACCESS_2_TRANSFER_WRITE_BIT` | Compute 原子读改写 | `COMPUTE_SHADER` / shader storage read + write |
| Compute 生成 command/count | `COMPUTE_SHADER` / shader storage write | Draw 或 Dispatch 参数读取 | `DRAW_INDIRECT` / `INDIRECT_COMMAND_READ` |
| Compute 写 visible IDs / transforms | `COMPUTE_SHADER` / shader storage write | Vertex Shader 的 SSBO 读取 | `VERTEX_SHADER` / shader storage read |
| Compute 写 vertex stream | `COMPUTE_SHADER` / shader storage write | 固定功能 vertex fetch | `VERTEX_ATTRIBUTE_INPUT` / vertex attribute read |
| Compute 写 index stream | `COMPUTE_SHADER` / shader storage write | Index fetch | `INDEX_INPUT` / index read |
| Cull pass 输出供 compact pass | `COMPUTE_SHADER` / shader storage write | 下一个 Compute pass | `COMPUTE_SHADER` / 按其实际读写指定 |

表中简写在最终代码中展开为固定 Registry 验证过的枚举。Fill 的精确 Sync2 CLEAR 路径也可以按需求用更保守的 ALL_TRANSFER，但不得把 COPY 当所有传输操作的同义词。[S2、S17]

必须覆盖独立 count buffer，不能只 barrier command buffer。shader `barrier()` 不是跨 workgroup、跨 dispatch 或跨 queue 的全局完成机制。

跨 queue 的条件分开：

- 同一 queue：建立资源相应访问依赖。
- 不同 VkQueue、同一 family：仍需跨 queue 执行/内存依赖，通常通过 semaphore；不是自动有序。
- 不同 family、exclusive sharing：在所选共享协议下补 release/acquire ownership transfer；concurrent sharing 不因此免除同步。
- 不因选择 async Compute 就保证硬件重叠或性能提升。

### C4.7 批次与命令状态

将对象按 Pipeline/渲染目标兼容、descriptor 模型、vertex/index 布局、primitive topology、blend/depth 等状态划分批次。普通 MDI 不是任意状态命令流；Pipeline 改变仍需在外层录制对应状态。

GPU 输出可采用预分桶、分段 command buffer 或后续 compact/bin pass。基础实现先走确定性分组与合法 descriptor；不强制 Bindless。

资源尚未就绪时选 resident fallback；Pipeline 未就绪时使用经过兼容性校验的替代路径或明确跳过策略。不能把任意“默认材质 Pipeline”绑定到不兼容布局上。

**C4 交付**：完整端到端工作流、能力/回退表、固定槽位与紧凑命令两套对照、同步模板、ABI/范围/计数的反例测试，以及精简 GPU 实验的源码与运行入口。

---

## 8. C5：规模化渲染（同版交付）

### C5.1 LOD、驻留与抖动控制

按屏幕空间误差/投影尺寸选择 LOD，不把固定世界距离当作通用规则。记录可用 LOD、误差、bounds 和 resident 状态；加入阈值滞回，防止相机微动时频繁切换。

几何 LOD、纹理 mip、材质复杂度与 GPU 预算是不同决策。丢弃细 LOD 前需确认旧命令/地址不再引用；目标细 LOD 尚未上传时，选择已有粗 LOD，不等待整条 GPU queue idle。

正确性比较先固定同一 LOD，再测 culling 等价；LOD 自身的画质另按提前锁定的误差门槛验收。不能把降画质产生的收益全部算成 GPU-driven 收益。

### C5.2 Hi-Z 遮挡剔除

本版交付 **当前帧保守 Hi-Z 路径**的算法说明、同步和可运行测试；上一帧历史作为可选实验，默认关闭。

基础顺序：可信不透明深度 → 深度层级 → bounds 的保守投影 → occlusion test → 命令生成。深度 prepass、金字塔和剔除的额外成本必须计入总 GPU 时间，tile GPU 的 load/store 成本也要计入。

需要先定义 depth convention、clear、compare、金字塔规约和 epsilon。对经典“用覆盖区域最远深度证明对象完全被遮挡”的保守算法，可用下列设计作为参考：

| 深度约定 | 层级规约 | 被遮挡的必要证明 |
|---|---|---|
| 常规 Z，近小远大 | 区域 max，包括 clear/far 样本 | 对象最靠近相机的深度仍严格在整个覆盖区域最远遮挡深度之后，含安全 epsilon |
| Reversed-Z，近大远小 | 区域 min，包括 clear/far 样本 | 对象最靠近相机的深度仍严格在整个覆盖区域最远遮挡深度之后，比较方向反转 |

上表是本计划选用的算法合同，不是 Vulkan 对 Hi-Z 的强制规定；不同深度表示必须重新推导。用数值/栅格对照测试证明规约、采样 footprint 与判定一致，不直接复制 min/max 名字。

必须处理：近平面/相机内部相交、投影包围范围、屏幕边缘、NPOT 层级边缘、空洞、alpha-tested 深度覆盖、MSAA 未覆盖样本、clear 值、透明物体和动态 occluder。

上一帧深度不能无条件证明当前帧遮挡。相机跳变、FOV/分辨率变化、实例新增/移动、occluder 移除和多 Surface 切换都需要 history invalidation；证据不足就保守可见或关闭该次遮挡。不得为追求剔除率接受未声明漏画。

### C5.3 实例、粒子与透明内容

- 大量相同或相近 mesh 采用实例化和合理状态分组；“对象数”“实例数”“draw 数”“三角形数”分别统计。
- 粒子增加 GPU 模拟、alive list、压缩和间接实例数；检查 spawn/kill、容量、counter、ping-pong buffer 和更新→绘制依赖。
- Additive 或明确顺序无关的特效可作为基础压力项；标准 alpha blending 不能按 opaque 的任意重排处理。
- 对标准透明内容，给出保序分组、排序或保留既有透明路径的选择；不把 OIT 当免费功能，也不强制开发完整 OIT 框架。
- 鱼群、植被、碎片等作为共享实例链路的应用案例；3DGS/大点云只记录“排序与 overdraw 特殊、不能直接等同于普通 mesh 剔除”的边界，不承诺本版解决其全部瓶颈。

### C5.4 多视图、多实例与生命周期

复用 v1.0.12 的 owner/generation。Geometry/Material 表可以共享，但各 view 的 frustum、LOD、visible list、indirect output、Hi-Z/history 与完成点需明确归属。

销毁一个 Surface 不得让其他输出读取被回收的共享 instance/mesh buffer。共享 Device 下的故障必须按既有分层恢复；纹理/几何异步发布、Pipeline 热更与 GPU 命令表切换使用同一可追踪代际边界。

### C5.5 Mesh Shader 与 Async Compute：在本版内做条件增强

本版必须完善已有 `mesh_shader.md` 的选型与回退，不把它简单推给下一版本。但以下路径不是所有设备的强制运行条件：

- mesh/task feature 分别查询并启用；核对 workgroup、payload、输出顶点/primitive、共享内存与资源限制；meshShader 不自动等于 taskShader。
- Meshlet 数据/边界与传统 mesh/LOD 表对接；无支持时使用 indexed indirect 路径，不能要求资产只保留 mesh-only 表示。
- shader 与流水线需合法编译；有设备才报告运行通过。桌面 GPU 测过不意味着 Adreno/Mali 支持或更快。[S13]
- Async Compute 先测负载、提交/等待链和真实 overlap；回退到单 queue 仍保持结果正确。优化需要可观察收益，不采用“Compute 占比超过某常数就必须换 queue”的无依据规则。

**C5 交付**：LOD/residency 联动、当前帧 Hi-Z、实例/粒子链路、透明回退、多视图状态与 Mesh/queue 决策材料，以及对应边界测试。硬件不支持的增强项以能力回退通过、原生运行未验证分别记录。

---

## 9. 文件落点与结构控制

### 9.1 运行时不扩目录、不新增平行流程

继续保留现有八模块，运行时知识文件净增目标 **0**，包内文件数不超过当前项目的 **200** 内部预算。不是把所有章节塞进一个新巨型文件，而是在既有责任文件内给稳定锚点与定向引用。

下列锚点为本版拟新增或修订的契约；实施前检查是否已有同名锚点，保留旧链接。路径全部相对 Skill 根目录：

| 能力 | 主要权威落点 | 拟定锚点/内容 |
|---|---|---|
| Shader 产物 | `references/03_api_manual/06_pipeline/shader_module.md` | `shader-artifact-contract` |
| 接口与热更 | `references/05_workflows/06_pipeline_descriptor/shader_binding_workflow.md` | `shader-interface-validation`、`shader-hot-reload` |
| 变体 | `references/03_api_manual/06_pipeline/specialization_constants.md` | `variant-cost-boundary` |
| 缓存/Binary | `references/03_api_manual/06_pipeline/pipeline_cache.md` | `cache-compatibility`、`pipeline-binary-path` |
| 创建调度 | `references/05_workflows/07_optimization/reduce_pipeline_creation_stutter.md` | `pipeline-build-scheduler` |
| 流式纹理 | `references/05_workflows/05_resource_management/add_texture_resource.md` | `texture-streaming-residency` |
| 几何/驻留 | `references/05_workflows/05_resource_management/manage_resource_lifetime.md` | `geometry-streaming-retirement` |
| 预算 | `references/03_api_manual/04_buffer_image_memory/vma_usage.md` | `streaming-budget-policy`，不复制整个 VMA 文档 |
| GPU scene 数据 | `references/02_core_mental_model/compute_graphics_relationship.md` | `gpu-scene-contract` |
| Indirect API | `references/03_api_manual/03_command_buffer/indirect_commands.md` | `indirect-capability-fallback`、`indirect-capacity-safety` |
| GPU-driven 总工作流 | `references/05_workflows/03_compute_workflows/add_compute_pass.md` | `gpu-driven-rendering`，作为任务路由首入口 |
| 同步 | `references/05_workflows/03_compute_workflows/compute_to_graphics_sync.md` | `gpu-produced-draw-sync` |
| LOD/Hi-Z/多视图 | `references/05_workflows/03_compute_workflows/add_compute_pass.md` | `gpu-lod-residency`、`hiz-occlusion`、`multi-view-culling` |
| Mesh Shader | `references/03_api_manual/06_pipeline/mesh_shader.md` | `mesh-path-fallback` |
| 规模与瓶颈取舍 | `references/05_workflows/07_optimization/optimize_frame_time.md` | `scaled-rendering-ab` |
| 经验与反例 | 现有 performance / sync / engine-architecture Case 聚合文件 | 测试案例写明 synthetic/公开来源/本地实测，不伪装真实故障 |

同步更新既有 API/workflow/case 索引、单一路由、模块统计、CHANGELOG、README 和版本字段。完整模板层级保留；新增扩展段不打破原有章节解析契约。

### 9.2 加载与防膨胀

- SKILL 只导航；不把五条主线全部加到固定启动读取。
- 简单 shader 问题不默认加载 GPU culling；indirect 参数问题也不强制加载纹理流式全文。
- GPU-driven 系统任务先读总工作流，再按 query 命中具体 API、数据与同步段。
- 大章节有明确输入、输出和适用边界；锚点读取时，必要前提通过短前置摘要或显式依赖引用传递。
- 各专题新增实际 token/读取字节/轮数单独记录；旧任务不能被动加载全部新增内容。
- 包预算、安全检查、无覆盖发布、MIT 与既有宿主配置保留；不为省文件删除知识、篡改统计或移除安全单测。

### 9.3 两仓交付分工

Skill 主仓只放专家知识、必要自检与既有安全打包逻辑。独立测试仓库放：实现计划原件与 hash、来源台账、fixtures、可运行实验、prompts、隐藏 rubric、编译/模型/设备原始结果。

拟新增测试材料可按既有结构归并；以下名字为建议，不作为“已存在”声明：

```text
测试仓库：
  docs/v1.0.13-plan-source.*             原始计划与 SHA-256
  tests/fixtures/engine_scale_lab/       Shader/ABI/状态机与 GPU 精简实验
  tests/test_v1_0_13_*.py                结构、合同、反例和解析器回归
  tests/prompts/eng13_*.txt              新 24 题
  reports/v1.0.13/                       来源、基线、分层执行与设备矩阵
```

不提供隐藏 rubric/历史答案给待测模型；CPU 模拟结果、编译结果、软件 Vulkan 结果与移动 GPU 结果分别标记。

---

## 10. 执行里程碑与依赖顺序

| 阶段 | 目标与工作 | 输入 | 输出 | 退出条件 |
|---|---|---|---|---|
| M0 基线与纠错 | 读取两仓最新状态，固定版本/规范，修命中错误，锁定 task/fixture/rubric | 本计划、现有五条链及测试合同 | 差异清单、来源台账、错误处置、40 题冻结清单 | 无未说明的已知错误继续作为新算法依据；权限和范围明确 |
| M1 内容工程底座 | C1 Shader、C2 Pipeline、C3 流式资源；先冻结共享数据/generation contract | M0、原 manager/构建/预算接口 | 接口/任务/驻留合同与单项 fixtures | 资源、Pipeline 与实例数据可以安全发布/取消/回收；C4 输入已定义 |
| M2 GPU-driven 基础 | C4 两种命令生成、frustum、状态桶、count/range、同步与回退 | M1 的 shader/interface/resident 数据 | G0/G1/G2 对照实现与工作流 | 核心正确性测试通过；CPU/GPU 可见性可比较；无越界与缺失依赖 |
| M3 规模化扩展 | C5 LOD、当前帧 Hi-Z、实例/粒子、多视图；补 Mesh/async 条件路径 | M2、固定场景与预算 | 规模分档实验、回退/画质/成本分析 | 无无法解释的漏画；不支持增强时基础路径正确；每项收益可单独测 |
| M4 集成与发布候选 | 结构、编译、Live、设备、包与加载量分别验收 | 最终候选 SHA、测试 SHA、全部结果 | 清晰分层报告、确定性 ZIP、回滚说明 | 已执行层无关键失败；未执行项明示；未满足 gate 不宣称完整验收 |

依赖图：

```text
M0
 ├─ C1 Shader contract ─────────┐
 ├─ C3 资源驻留 contract ───────┼─ M2 GPU-driven ─ M3 Scale ─ M4
 └─ 既有 manager / frame model ┘
       C1 ─ C2 Pipeline cache/build ────────────────┘
```

C1、C3 和测试输入准备可在不修改共享文件时并行；C2 的接口/key 冻结依赖 C1。共享路由/索引/版本字段由单一集成阶段更新，避免不同 Agent 覆盖。协调视图仅保留一个当前 `in_progress` 里程碑；不把尚未验证的阶段标为完成。

### 每组交付统一格式

```text
Task ID / 本次目标
实际源码证据 / 规范来源
候选方案及不采用方案
修改文件与锚点
数据、生命周期、同步与失败路径
自动检查 / 人工检查 / 设备检查
结果及证据范围
未验证项与回退
```

---

## 11. 统一实验：Engine Scale Lab

### 11.1 实验定位

在测试仓库内提供精简、可编译的 Vulkan 实验。优先复用已授权的现有测试框架；如果没有，提供最小 fixture，不新建通用引擎。

C++ 沿原项目风格，Android 接入优先 Java + Native，不引入 Kotlin 必需依赖。基线使用设备确实支持的核心/扩展路径；桌面或软件 Vulkan 可验证部分功能，但报告中不得换称移动 GPU 性能。

### 11.2 场景规格

使用可再分发的程序化几何、固定随机种子和确定性相机路径，避免下载大体积/不明许可模型。

| 场景 | 规格建议 | 目标 |
|---|---|---|
| A 首屏与切换 | 多材质区域、重复 mesh、可切换 shader 与纹理集合 | 预热、热更、资源到达、fallback |
| B 规模实例 | 1,000 / 10,000 / 100,000 三档实例；可见率约 10% / 50% / 100% 的固定相机路线 | CPU 与 GPU 生成成本、低可见率/高可见率拐点 |
| C LOD/Hi-Z | 每个原型至少 3 个 LOD，遮挡墙、移动物体、近平面相交、相机瞬移 | 保守剔除、LOD 驻留与 history invalidation |
| D 粒子 | 固定种子、alive/dead 变化、容量上限、加法与标准 alpha 两种模式 | 计数、排序边界、状态/带宽瓶颈 |
| E 故障恢复 | 缓存损坏、编译失败、上传取消、预算下降、输出 A 销毁而 B 继续 | 不串代、不死锁、不持续泄漏 |

实例数是输入规模，不等于 draw 数，也不是所有手机的 60 FPS 承诺。三角形数、材质桶数、输出分辨率、overdraw 和纹理大小在实验 manifest 固定。低能力设备跑不了最高档时记录资源限制/未完成档位，不能私自降低负载后宣称通过最高档。

### 11.3 对照模式

必须能够单独切换以下模式，以隔离收益来源：

1. 不做 GPU 剔除的可检查参考图像/ID 输出。
2. CPU frustum + Direct/Instanced Draw，作为公平的优化 CPU 基线。
3. GPU frustum + 固定槽位 indirect。
4. GPU frustum + compact/count（支持时）。
5. 在上一模式上单独开启 LOD、当前帧 Hi-Z、粒子间接绘制。
6. 支持且有设备时，单独比较 Mesh Shader 与 async Compute。

不能只用最差的逐对象 CPU 提交作为唯一对照，也不能一次开启压缩、LOD、Hi-Z、降低分辨率后把全部收益归给 MDI。

### 11.4 必测结果

| 分类 | 指标与证据 |
|---|---|
| 正确性 | CPU/GPU 可见 ID、合法命令范围、overflow、图像/深度对照、LOD/精度误差、首次错误日志 |
| CPU | culling、command recording、Pipeline 创建、转码、上传调度的 p50/p95/p99 与关键路径 |
| GPU | culling、compact、Hi-Z 构建、主绘制、粒子和总 GPU 时间；等待开销不能漏计 |
| 内容到达 | 冷/热启动、首个正确帧、首次使用卡顿、占位内容升级时间、取消完成时间 |
| 内存 | CPU 解码/转码、staging、可见/命令/count、Hi-Z、几何/纹理 allocation、旧版本待退休峰值 |
| 规模 | 总实例/可见实例、实际 draw/dispatch、状态桶、处理三角形、可获得的带宽/overdraw 证据 |
| 持续性能 | 相同设备/驱动、分辨率、场景、帧节奏、温度与供电条件下的时间序列 |
| 稳定性 | 重复加载卸载、旋转/暂停恢复、多输出独立退出、任务取消与 capacity overflow |

性能测试关闭会显著改变行为的调试读回与验证层；正确性测试单独启用。图像、GPU timer、trace 和本地日志要记录配置。没有硬件 counter 时报告不可用，不从 pass 数变化推导出虚构带宽数据。

### 11.5 通过标准

- 所选基准中，保守 frustum/当前帧 Hi-Z 不漏掉参考路径应显示的物体；多画的保守结果可接受但统计成本。
- 可见列表与绘制参数在容量、generation、索引/地址范围内；零可见、全可见、极端 count 均不越界。
- 热更/取消/资源降级的行为符合合同；替代内容与允许的画质误差在测量前约定。
- 固定槽位与 count 路径的正确结果一致；能力不支持时确实回退，不只在 UI 中标识。
- 高规模场景需要证明所选优化相对公平 CPU 基线的目标收益，或明确给出不值得启用的结论；不预设统一提升百分比。
- 低规模回退与高 GPU/带宽压力场景不能强制开启成本更大的路径。不同设备可做不同选择。
- 重复加载/卸载在缓存暖机后达到可解释平台，资源计数与待退休列表无持续增长。故障注入优先限制在隔离 fixture，不通过故意压垮用户系统来测试。

---

## 12. 新增 ENG13 行为题库：24 个场景

保留现有 40 场景及 prompt bytes；新建 **ENG13-01～24** 独立 cohort。若实施时基线仍为 40，完整集合变为 **64**；注册表与实际枚举结果为准，不为了凑数跳过已有题目。

每题至少有一组条件相反的变体，先冻结输入、判据和错误结论拦截，再运行模型。下面是出题/人工验收要求，不可直接注入模型提示词作为标准答案。

| ID | 测试主题 | 必需判断 / 禁止错误 |
|---|---|---|
| ENG13-01 | Shader 编译环境与旧设备 | 区分编译器、SPIR-V target、runtime feature；编译通过不等于可运行 |
| ENG13-02 | Reflection 与 host 布局 | 检查 offset/stride；不把合法动态 UBO、stage 超集等统一误报 |
| ENG13-03 | 热更新改变资源接口 | 区分接口兼容与迁移；旧 in-flight 对象继续存活；失败不发布半套资源 |
| ENG13-04 | FP16 变体与剔除边界 | 分开 arithmetic/storage/I/O；边界结果错误时不能以 FPS 提升判成功 |
| ENG13-05 | Pipeline 缓存损坏/驱动变化 | 正确验证与回退；不编辑 opaque 数据或跨设备硬用 Binary |
| ENG13-06 | 后台编译晚到与 Device 退出 | 检查输入内存、generation、取消与 teardown；不发布旧设备结果 |
| ENG13-07 | 共享 PipelineCache 并发 | 按 flags 和具体命令核对 host sync；不靠一个全局口号判断合法 |
| ENG13-08 | GPL/特化值/变体爆炸 | 分开 SPIR-V 产物与 Pipeline 组合；没有设备数据不保证加速 |
| ENG13-09 | 无 Surface 创建纹理 | 普通 image 按 Device 能力创建；与项目约束、外部 AHB 区分 |
| ENG13-10 | KTX2/Basis 与压缩 mip | 正确格式选择/usage/转码回退；不能对所有压缩格式假定可 blit |
| ENG13-11 | 部分 mip 与内存压力 | 不采样未初始化数据；限制 LOD 不等于释放 allocation |
| ENG13-12 | 上传取消与共享 geometry | 提交前后回收不同；不能淘汰其他实例仍引用的 mesh/texture |
| ENG13-13 | 间接 dispatch 阶段与 limits | DRAW_INDIRECT 消费参数；x/y/z 分维限制，拒绝虚构 stage |
| ENG13-14 | 固定槽位 instanceCount=0 | 承认合法 GPU 可见性路径；无 Count 不强制 CPU 每帧回读 |
| ENG13-15 | Indirect feature 分离 | multiDraw、firstInstance、Count、DrawID/BDA 等分别判断并回退 |
| ENG13-16 | count 超容量/ABI 边界 | 写入前界限、有效前缀、stride/offset、vertexOffset signedness；maxDrawCount 不阻止 OOB 写 |
| ENG13-17 | reset→cull→compact→draw | 独立 count 和多 dispatch 依赖齐全；shader barrier 不当全局同步 |
| ENG13-18 | command/SSBO/vertex/index 多消费者 | 按真实消费者访问指定 barrier；单独 DRAW_INDIRECT 不覆盖所有数据 |
| ENG13-19 | 材质批次与透明 | MDI 不自动切 Pipeline；缺少 Bindless 可分组；透明不能任意重排 |
| ENG13-20 | 跨 queue/family 的资源复用 | semaphore 与 ownership 条件分开；不同 queue 不自动同步 |
| ENG13-21 | LOD 未驻留/阈值抖动 | resident fallback、滞回、旧地址退休；不让命令引用未上传资源 |
| ENG13-22 | Hi-Z 正反 Z 与无效历史 | 规约/compare/clear 一致，保守覆盖；相机切换与空洞不漏画 |
| ENG13-23 | GPU 粒子与“draw 数变少” | alive/capacity/透明排序正确；看完整 CPU/GPU/画质/热状态，不用 draw 数判性能 |
| ENG13-24 | Mesh/async 与多输出能力差异 | Unsupported 回退、每 view 独立数据、真实收益；不强制升级硬件或 API 基线 |

自动 smoke checks 只验证最低可观察契约；技术正确性还需人工 rubric 和可执行证据。不得因回答出现“Mip、LOD、barrier”关键词就判完整通过。

---

## 13. 验证层、执行条件与证据

| 层 | 应执行内容 | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| Static / Contract | 引用、锚点、模板、符号、版本、包清单、安全单测、cohort 完整性 | 文件与规则契约没有明显破损 | 模型理解、算法/GPU 正确 |
| Host/Shader Unit | manifest/key、ABI、取消/代际/预算模拟、SPIR-V 编译与验证、参考剔除数学 | 指定输入下的代码/构建合同 | Android/GPU 性能、真实设备能力 |
| Snapshot | 旧历史样本契约保持 | 历史 fixture 可解析 | 当前候选实时行为 |
| Live Model | 当前 Skill 与真实模型执行旧40+新24，保存读取轨迹与原始输出 | 固定输入/模型/版本下的实际回答 | 未运行设备的渲染或性能 |
| Vulkan Integration | 精简实验的图像、可见列表、同步与生命周期回归 | 所用 Vulkan 实现上的可观察正确性 | 所有驱动通用正确或移动端性能 |
| Mobile/Scale | Adreno/Mali 等真实目标设备上的分档、图像、延迟、内存与热状态 | 指定设备/场景结果 | 其他硬件或未支持的 Mesh/async 路径 |

### 建议执行范围

- 不依赖 GPU 的单测、Shader 编译、ABI/容量边界检查应可在 CI 执行。
- 小型 Vulkan 实验必须能够运行，不以 Python 状态机替代实际 draw/dispatch；没有设备时明确 BLOCKED，源码/编译完成可以单独交付。
- 移动端目标优先至少一台 Adreno 与一台 Mali，另以显式关闭高级 feature 验证降级路径；不虚构型号、版本或支持率。
- Mesh/async/Binary 原生验证仅在支持设备运行；无硬件时合同/编译可验证，原生结果未验证，不阻塞合法基础回退的验证。
- 64 场景一次 smoke 后，发布稳定性建议至少 3 个独立 run。保留每次原始输出，不把失败答案手改成成功；重跑生成新目录。
- Live adapter、凭据、设备和付费服务必须来自明确授权；不主动获取凭据或部署云端实验。

### 每次报告绑定

```text
Skill SHA / Skill tree / Tests SHA / dirty state
source revisions / compiler & SDK versions / SPIR-V target
model / explicit parameters / request IDs / input-output hashes
actual reads / sections / provider token usage
renderer source SHA / binary or APK hash / scene seed & config
GPU / device / OS / driver / enabled features / capability snapshot
validation / capture / visual-ID diff / timings / resource counters
PASS / FAIL / BLOCKED / NOT_RUN / NOT_APPLICABLE 与原因
```

模型输出、图像和 trace 涉及项目数据时只在授权范围保存；不上传私有素材/抓帧给公共仓库。

### 计量不得换基线

原“30% provider input-token 下降”仍只使用 v1.0.8 的固定基线和原始 12 题。当前 v1.0.12→v1.0.13 的旧40回归与新增ENG13-24用量独立报告；不能拿64题混合中位数替代旧12题结果，也不再强加一次30%降幅。

新增内容不能让旧简单任务默认预读全部大章节。测量实际读取清单、字节、token和轮数；没有 provider usage 时标 UNMEASURED，不能用 Markdown 字节数称为实际模型 token。

---

## 14. 发布门槛、回滚与完成定义

### 14.1 文档与测试材料完成

- [ ] C1–C5 全部有权威段落、调用入口、输入输出、版本/能力边界和回退。
- [ ] GPU-driven 核心链路没有被移回下一版本；Mesh/async 仅原生执行条件化。
- [ ] 已确认错误按规范修正，并检查摘要、正文、伪代码和索引一致性。
- [ ] 旧40题与其读取隔离仍在；新增24题真正注册到 runner/验收，不只是提交 prompt 文件。
- [ ] 单元模拟、SPIR-V 编译、Vulkan 实验与设备验证明确分层。
- [ ] Runtime 文件净增0；预算检查实际白名单包，不把整仓文件数当包大小。

### 14.2 候选验证完成

- [ ] Static、编译/合同和安全检查针对最终候选无关键失败。
- [ ] 原有功能不退化；新 ENG13 语义题有真实 Live 结果与人工复核，或明确 BLOCKED 而非 PASS。
- [ ] CPU/固定槽位/Count 的正确性对照与基础 Vulkan 实验已执行，或明确未执行层。
- [ ] 移动性能有支持设备结果才宣称；CPU-only 或软件 Vulkan 不冒充移动收益。
- [ ] 同一干净候选双次打包一致，CRC/per-file SHA/manifest通过；旧 SHA 包与报告不复用为新候选证据。
- [ ] 原始模型失败、测试失败和未达指标完整保留；已修与未验证分开。

### 14.3 发布声明边界

可以分别交付“知识/代码材料已完成”和“完整运行验收通过”，不可混为一项。Live、真实宿主或基础 GPU gate 缺失时，标记为待验收候选，不宣称专家行为和性能已证实。已经合并 main 也不会自动补齐这些证据。

若候选未满足完整门槛，是否以限制范围发布需维护者明确决定；默认不自动合并、发版或上架。

### 14.4 回滚策略

工程路径保留开关：CPU参考、GPU固定槽位、Count、LOD、Hi-Z、粒子、Mesh、async分别可回退。缓存异常可局部失效；Shader热更失败保留旧产物；资源预算下降采用已定义降级，不关闭全部同步。

Skill 修改以可审查的增量 patch/分组提交回退，不删除历史规则或覆盖用户未提交修改。公共锚点尽量保留，迁移必须给兼容引用与测试。

---

## 15. AI 实施提示词

以下提示词用于维护者另行授权的实施环境；本计划本身不授权 push、合并、部署、上架或凭据操作。

```text
你负责升级 oahc09/vulkan-rendering-expert-skill 到 v1.0.13：
Shader、Pipeline、资源加载与 GPU-driven 规模化渲染。
测试仓库是 oahc09/vulkan-rendering-expert-skill-tests。
GPU-driven 与规模化渲染已并入本版，不再推迟到 v1.0.14。

计划固定基线：
Skill main d049afefaec8539cecca5f8e37c4cd66ec9da728，入口1.0.12。
Tests main 9278d9be3a7a4d4e919ac36927ee165a433450a9。
若 HEAD 变化，先读取差异，不覆盖、不回滚用户已有工作。
先读宿主指令、AGENTS、git status、SKILL、硬规则、单一路由、相关模板/知识、
实际release-contract、打包器、runner、计量器与已有原始证据。

实施 M0→M1→M2→M3→M4，协调视图只保留一个 in_progress 里程碑。
C1：Shader产物、接口、热更、变体与精度。
C2：分层缓存、预热/异步创建、任务取消与generation、Binary/GPL条件路径。
C3：KTX2/Basis条件转码、纹理/几何分批上传、部分mip、驻留与预算回收。
C4：CPU对照+GPU frustum、固定槽位+compact/count、state bins、容量和同步。
C5：LOD、当前帧保守Hi-Z、实例/粒子、多视图，Mesh/async作为同版可选增强。

先修命中知识错误：
间接dispatch参数读取使用DRAW_INDIRECT，不能编造DISPATCH_INDIRECT阶段；
x/y/z各维groupCount与local invocation limits分开；
固定槽位instanceCount=0是有效基础路径，Indirect Count不是GPU-driven必需条件；
DrawIndirectByteCountEXT归属transform_feedback，不能混同multi_draw；
普通纹理不要求先有Surface；specialization不自动减少Pipeline组合。
用固定Registry/Ref/Spec核对符号、VU和语义，不把Samples的描述当绝对规范。

必须给出：
资源owner/generation/resident合同；count reset→cull→compact→draw依赖；
command/count与SSBO/vertex/index消费者的不同同步；跨queue与family的条件；
capacity在写入前保护，maxDrawCount不能阻止compute越界；
状态批次、透明顺序、LOD缺页回退、Hi-Z误剔除保护；
缓存/上传/编译失败、取消和旧版本退休。
不默认要求Bindless、Descriptor Heap、Mesh Shader、BDA或独立Compute Queue。

结构与交付：
保持八模块、原触发条件、模型/宿主配置、hard_rules、Evidence/Architecture Map、
R1–R5、适用G1–G6与安全打包。
运行时知识净增0、白名单包≤200（实际release-contract若变化先报告）。
以现有add_compute_pass.md的gpu-driven-rendering锚点作为总流程入口，
API规则、同步细节与Case分别放回各自责任文件，不在SKILL里堆全部知识。
测试工程、prompts、rubric、源码实验、原始结果放独立测试仓库。

测试：
保留旧40场景及原始12题token分母，增加ENG13-01..24，预计64题。
用既有runner，先锁定判据，隐藏答案/rubric；真实调用保存SHA/hash/读取/usage。
没有授权模型/设备时标BLOCKED，不用快照或CPU模拟冒充Live/GPU。
Engine Scale Lab必须区分CPU参考、GPU固定槽位、GPU Count、LOD/Hi-Z逐项开关；
1k/10k/100k规模是负载档位，不是60FPS承诺。
测CPU/GPU完整时间、首次卡顿、画质、内存峰值与持续热状态，不只数draw calls。

最终输出：
基线和差异、C1–C5完成映射、文件/锚点、官方来源及待核项、
结构/编译/模型/Vulkan/移动设备分层结果、包manifest/hash、原始失败记录、
未验证与回滚。未授权不提交/推送/合并/发版/上传，遵从本次明确授权。
```

---

## 16. 来源、版本与核验边界

本计划不是新一份“最近一个月新闻榜”；它把已讨论的 v1.0.13 三条主线与 GPU-driven 合并为可执行范围。Pipeline Binary、MDI、KTX、Mesh Shader 等是工程参考，不在此宣称均为本月首发。

GitHub 内容通过连接器读取，仓库依据固定至下述 SHA。公共规范/工具页面于 2026-11-01 查询；`latest` 会变化，实施时应保存适配目标的 Registry/Spec/工具 tag 或 commit，并记录实际启用配置。

### 16.1 本项目源码证据

- [R1] 当前 Skill main ref（本次解析为 d049af…）：https://api.github.com/repos/oahc09/vulkan-rendering-expert-skill/git/ref/heads/main
- [R2] 入口： https://github.com/oahc09/vulkan-rendering-expert-skill/blob/d049afefaec8539cecca5f8e37c4cd66ec9da728/SKILL.md
- [R3] 测试主线固定源码： https://github.com/oahc09/vulkan-rendering-expert-skill-tests/tree/9278d9be3a7a4d4e919ac36927ee165a433450a9
- [R4] 发布合同： https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/9278d9be3a7a4d4e919ac36927ee165a433450a9/release-contract.json
- [R5] 测试 README（含40场景与历史计量口径）： https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/9278d9be3a7a4d4e919ac36927ee165a433450a9/tests/README.md
- [R6] Shader binding： https://github.com/oahc09/vulkan-rendering-expert-skill/blob/d049afefaec8539cecca5f8e37c4cd66ec9da728/references/05_workflows/06_pipeline_descriptor/shader_binding_workflow.md
- [R7] Pipeline stutter： https://github.com/oahc09/vulkan-rendering-expert-skill/blob/d049afefaec8539cecca5f8e37c4cd66ec9da728/references/05_workflows/07_optimization/reduce_pipeline_creation_stutter.md
- [R8] Texture workflow： https://github.com/oahc09/vulkan-rendering-expert-skill/blob/d049afefaec8539cecca5f8e37c4cd66ec9da728/references/05_workflows/05_resource_management/add_texture_resource.md
- [R9] Indirect Commands： https://github.com/oahc09/vulkan-rendering-expert-skill/blob/d049afefaec8539cecca5f8e37c4cd66ec9da728/references/03_api_manual/03_command_buffer/indirect_commands.md
- [R10] Compute→Graphics： https://github.com/oahc09/vulkan-rendering-expert-skill/blob/d049afefaec8539cecca5f8e37c4cd66ec9da728/references/05_workflows/03_compute_workflows/compute_to_graphics_sync.md

### 16.2 官方规范与实现参考

- [S1] Khronos GPU Rendering and Multi-Draw Indirect sample（仅参考方法，API细节以规范为准）： https://docs.vulkan.org/samples/latest/samples/performance/multi_draw_indirect/README.html
- [S2] Synchronization and Cache Control（阶段、访问与queue能力）： https://docs.vulkan.org/spec/latest/chapters/synchronization.html
- [S3] VkDispatchIndirectCommand（每维group count）： https://docs.vulkan.org/refpages/latest/refpages/source/VkDispatchIndirectCommand.html
- [S4] Khronos Synchronization Examples： https://docs.vulkan.org/guide/latest/synchronization_examples.html
- [S5] vkCmdDrawIndexedIndirectCount 与命令布局： https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdDrawIndexedIndirectCount.html ；https://docs.vulkan.org/refpages/latest/refpages/source/VkDrawIndexedIndirectCommand.html
- [S6] vkCmdDrawIndirectByteCountEXT： https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdDrawIndirectByteCountEXT.html
- [S7] Pipeline Cache Guide 与并发 flags： https://docs.vulkan.org/guide/latest/pipeline_cache.html ；https://docs.vulkan.org/refpages/latest/refpages/source/VkPipelineCacheCreateFlagBits.html
- [S8] Pipeline Binary 扩展与样例： https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_pipeline_binary.html ；https://docs.vulkan.org/samples/latest/samples/extensions/pipeline_binary/README.html
- [S9] Shader Memory Layout： https://docs.vulkan.org/guide/latest/shader_memory_layout.html
- [S10] Explicit 16-bit Arithmetic： https://docs.vulkan.org/samples/latest/samples/performance/16bit_arithmetic/README.html
- [S11] Khronos KTX-Software / libktx： https://github.khronos.org/KTX-Software/
- [S12] VMA Staying Within Budget： https://gpuopen-librariesandsdks.github.io/VulkanMemoryAllocator/html/staying_within_budget.html
- [S13] VK_EXT_mesh_shader： https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_mesh_shader.html
- [S14] Features： https://docs.vulkan.org/refpages/latest/refpages/source/VkPhysicalDeviceFeatures.html ；https://docs.vulkan.org/refpages/latest/refpages/source/VkPhysicalDeviceVulkan12Features.html
- [S15] Pipeline/布局合法性： https://docs.vulkan.org/spec/latest/chapters/pipelines.html ；https://docs.vulkan.org/refpages/latest/refpages/source/VkPipelineLayoutCreateInfo.html
- [S16] Image 创建： https://docs.vulkan.org/refpages/latest/refpages/source/vkCreateImage.html
- [S17] count reset / fill： https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdFillBuffer.html
- [S18] Specialization Constants 与 GPL： https://docs.vulkan.org/samples/latest/samples/performance/specialization_constants/README.html ；https://docs.vulkan.org/samples/latest/samples/extensions/graphics_pipeline_library/README.html

官方文档与样例支持能力边界和使用规则，不证明本项目某个实现已编译或运行。Hi-Z 的保守算法、调度/预算策略与实验档位是本计划的工程设计，必须通过对照验证，不冒称 Vulkan 强制规定。第三方源码/资产的许可证在真正引入时核查，本计划不内嵌供应商模型或受限文档。

---

## 17. 本轮交付状态

- **已完成**：将 GPU-driven 与规模化渲染并入 v1.0.13；核对两仓固定基线、Indirect/Compute 相关文档、现有40场景与发布预算；形成五主线、五里程碑、24新场景、实验规格、文件落点、验收与执行提示词。
- **未执行**：Skill/tests 代码修改、编译、pytest、Live模型、真实宿主、Vulkan/Android/GPU、性能测量及打包重跑。
- **远端写入**：无。本文件是计划，不是实现记录或测试通过证明。
