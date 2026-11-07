# Vulkan Expert Skill v1.0.14 开发计划
## Mobile Hybrid Lighting & Temporal Quality — 移动端混合光照与时域画质

> 编制日期：2026-11-02，Asia/Singapore。  
> 本次检索窗口：**2026-08-05—2026-11-02，共 90 个自然日（含首尾）**。不再限于最近 30 天。  
> 当前定位：开发计划与只读资料核查；未修改仓库、未调用被测模型、未编译或运行 GPU/Android 实验。  
> 核心目标：在 v1.0.13 已具备的 Shader、Pipeline、资源驻留与 GPU-driven 底座上，指导实现**可回退的光照与阴影、可选 Ray Query、稳定的时域处理以及有证据的画质/性能取舍**。

---

## 1. 版本结论

**v1.0.13 主要解决“内容如何高效进入引擎并扩大场景规模”；v1.0.14 解决“规模化场景如何获得稳定、可信、适合移动设备预算的画质”。**

本版交付四条主线，不重新建设资源管理器、GPU-driven 框架或神经 SDK 封装：

| 编号 | 能力主线 | 本版必交付 | 不作强制要求 |
|---|---|---|---|
| C1 | 光照、阴影与反射的基础路径 | 光照/深度/材质合同；稳定 shadow-map 基线；屏幕空间/探针回退；不同可见集合 | 完整虚拟阴影贴图、通用 GI 引擎 |
| C2 | 可选 Ray Query 与加速结构 | 独立能力查询；BLAS/TLAS、scratch、更新/压缩/退休；混合阴影与单次反射参考路径；alpha-mask/OMM 边界 | 所有手机启用光追、Ray Tracing Pipeline/SBT、完整 OMM baker |
| C3 | 时域稳定与去噪 | motion/depth/jitter/exposure 合同；history 失效与重投影；传统时空滤波基线；现有超分/插帧路径的输入协调 | 新神经模型训练、强制接入指定厂商 SDK |
| C4 | 画质、成本与设备分档 | 可解释降级策略；匹配负载 A/B；图像序列与性能证据；分层回归 | 无实测的提速/功耗承诺、桌面收益外推手机 |

统一链路：

```text
v1.0.13 场景/Shader/材质/驻留数据
→ 相机可见集合、阴影投射集合与反射相关集合
→ 基础光照 + Shadow Map / 屏幕空间 / 探针
→ 受支持时构建或更新 BLAS/TLAS，执行 Ray Query
→ 输出 visibility / radiance / confidence 等明确语义的数据
→ 重投影、history 校验、时空滤波
→ 可选的既有超分/插帧适配 → UI/输出合成
→ 画质、帧时间、内存峰值与持续热状态验证
```

“必交付”指 Skill 的规则、来源、工作流、条件回退、测试题与可执行的精简验证材料。硬件增强路径是否运行另有能力门控；缺少设备不能伪填通过，也不能以缺少光追设备为理由省略普通光栅回退。

---

## 2. 固定基线及与前版的界限

| 对象 | 本次读取的值 |
|---|---|
| Skill 仓库 | `oahc09/vulkan-rendering-expert-skill` |
| Skill main SHA | `8d62f861b4ead27699e2ff3d80a1a9f0e72a4968` |
| 入口声明版本 | `1.0.13`，last-updated `2026-11-01` |
| 测试仓库 | `oahc09/vulkan-rendering-expert-skill-tests` |
| 测试 main SHA | `9c4cba3a3985b709ccdbec182c79a6988bfc721e` |
| 测试 release-contract 中的 Skill 候选 | `d4965f77365b4cd78692e60d048929040ba65c8b`，expected version `1.0.13` |
| 运行时包预算 | `max_runtime_files: 200`；现有契约 `allowed_new_knowledge: []` |
| 已有 Live 题库 | 64 个场景；原 40 + ENG13 24，不代表全部执行通过 |
| 本次读取的上游规范更新 | Vulkan-Docs changelog 顶部为 2026-10-30 / Vulkan 1.4.367 |

依据：[R1–R4、S6]。main 与测试 pin 的 SHA 不同，实施前比较 tree 和变更，不自动判错，也不自动继承测试结果。执行期间 HEAD 变化时先检查差异，不覆盖用户已有改动。

### 继承，不重做

- v1.0.11：移动采集/持续性能、fault、tile、外部互操作、神经图形的条件接入。
- v1.0.12：Engine/Surface/resource generation、多实例、媒体帧、颜色/HDR/透明合成。
- v1.0.13：Shader artifact/ABI、Pipeline 缓存/热更新、上传/驻留、GPU culling、LOD、Hi-Z、粒子、多视图。
- 原有模型/宿主配置、触发条件、hard_rules 全文、routing-entry、分段读取、Evidence/Architecture Map、影响面分类、R1–R5、适用范围内 G1–G6、MIT 和安全打包全部保留。

本版不是把 v1.0.13 的相机剔除列表直接接上光追。阴影与反射需要自己的相关几何集合；history、AS 和材质都必须连接既有资源代际和退休机制。

---

## 3. 90 天资料筛选与实际增量

### 3.1 时间与证据规则

记录 `event_date`、`published_at`、`updated_at`、`checked_at`、source revision/hash；不把爬取时间当发布日期，不把文档更新当功能首次发布。官方规范用来判定合法性，作者文章/样例用来形成工程候选，Issue 只证明报告存在。

X 可以发现演示、作者观点和问题线索，但核心规则必须回链到官方正文、源码、发布记录或论文。此次未取得足以独立支撑新规则的 X 原帖；不补造链接或互动数据。

### 3.2 纳入本版的时间窗口证据

| 来源日期 | 已核实事实 | 本版落点 | 状态边界 |
|---|---|---|---|
| **08-24，页面更新** | Arm Android Ray Tracing 学习路径列出能力查询、AS 和阴影/反射等工程入口。[S1] | C2 的设备门控与混合效果路径 | 是旧主题的更新入口，不是 Ray Query 在 2026 年首次发布；设备型号示例不是通用白名单。 |
| **09-17，文章发布** | AMD 讨论四面体 cage 降低动态几何 BVH 内存和更新成本。[S2] | C2 的 AS 成本预算与动画几何取舍 | 演示为桌面 Radeon 工作负载；本版不移植 cage 算法、不借其数字承诺 Android 收益。 |
| **09-22，技术说明** | Qualcomm ANF 文档解释 SR/FG 的时域输入及调试可视化；公开集成指南进一步区分 SR 与 FG 的尺寸、jitter 和 UI 顺序。[S3、S9] | C3 的输入合同、诊断视图和 SDK 适配边界 | 厂商特定路径，不把其尺寸/格式/质量模式当所有时域算法共同要求；不重做 v1.0.11 接入。 |
| **10-17，用户 Issue** | NVRHI #165 报告 query-only 配置被额外引入 SBT usage 和 Ray Tracing Shader stage。[S4] | C2 的负向能力测试和 API 边界 | 读取时 Issue open，报告者建议补丁未测试；不是维护者确认修复，也不是本次复现。关键规则另由规范核对。 |
| **10-22，厂商工程文章** | Arm 在 Moku/Mali G2 的匹配工作负载中评估 OMM，强调 alpha-masked 几何和内容适用性。[S5] | C2 alpha-cutout/OMM；C4 匹配负载与序列验证 | 是条件实验，不能推广所有手机、所有透明材质；RTP/引擎定制结果不自动等于 query-only 样例已通过。 |
| **10-23 / 10-30，规范修订** | Vulkan-Docs 更新 AS/OMM 边界、部分 VU 和动态状态说明。[S6] | M0 的固定规范与相关符号/VUID 核对 | 文档修订不等于 SDK 或目标 Android 驱动已实现新扩展。 |

本版**新增技术主轴**来自上述资料与现有知识缺口的交集，而不是把每一篇资讯变成一个文档。

### 3.3 只作背景或观察项

- `VK_KHR_ray_query` 自身不是 90 天内新增扩展；其规范是 C2 的长期基础。[S7]
- `VK_KHR_opacity_micromap` 参考页的 Last Modified Date 为 2026-05-08，早于窗口；窗口内新价值是 10 月案例与规范修订。[S10]
- Arm ASR 页面在搜索索引与打开的缓存正文中出现不同更新时间（8 月与 6 月）；不将该条算作日期已经完全核实的 90 天新功能。ASR 作为可选既有方案，实施时固定源码再引用。
- Filament main 的 release notes 含 motion vectors/TAA 改动，但本次未确认对应 v1.80.0 release 发布状态；可作后续提交研究，不称为已发布的新稳定版本。[S11]
- 完整 ReSTIR GI、radiance cache、神经去噪训练、四面体 cage、完整 Virtual Shadow Map 系统放观察列表。本版只写触发条件和研究入口，不形成隐藏必交付任务。

---

## 4. M0 必须处理的命中纠错

先修会被新知识引用的已有规则，不开展无限制全文重写。

| 现有文件 | 已读取的问题/风险 | 处理与验收 |
|---|---|---|
| `02_core_mental_model/modern_patterns.md` §3 | 示例把 timeline semaphore 直接用于 acquire/present 主链 | WSI 保留合法 binary 边界；timeline 用于适用的队列/资源进度。按 `vkAcquireNextImageKHR`、`vkQueuePresentKHR` 核对，不用“看驱动”绕开规范。[R5、S12] |
| 同文件的版本/能力概括 | “Vulkan 1.4…无需运行时查询”容易抹平子属性、启用状态与实际使用边界 | 复用现有 capability 卡，不再复制一套版本承诺；区分规范保证、所选路径的额外能力、应用实际启用和平台限制。 |
| `05_workflows/02_render_pass_effects/add_depth_pass.md` §7 | 含普通 depth image 直接转 PRESENT 的示例；同时将写入 layout 描述过窄 | 默认路径改为深度写入→采样/可视化至颜色输出；present 对象须为当前 WSI 路径的可呈现 image。布局枚举按所用路径核对。[R6、S13] |
| 同文件的深度阶段描述 | 把 depth 状态笼统归为 fragment output | 依实际 early/late depth-stencil 访问选范围；阴影采样另用真正 shader consumer，不凭状态名称猜同步阶段。[S14] |

新反例测试需分别读取摘要和正文，避免只改详细章节、短路由仍保留旧建议。非法符号作为明确否定的反例可以保留，扫描器不能机械删掉警示文本。

---

## 5. C1：基础光照、稳定阴影与反射回退

### C1.1 输入与空间合同

在现有 render-target / depth / postprocess 文档内明确：

- 线性工作颜色空间、光照与显示变换的边界；复用 v1.0.12，不重新定义 HDR 链路。
- depth range、正/反 Z、clear value、比较方向、投影矩阵、viewport 和纹理坐标方向。
- normal 的空间、编码和几何法线/着色法线用途；roughness/metallic 的约定。
- 相机、灯光、材质、mesh、LOD 与资源的稳定 ID 和 generation。
- 透明混合、alpha-cutout、双面几何分别处理，不能靠统一“透明标志”决定阴影或 ray 命中。

这些是引擎的数据约定，不是 Vulkan 新结构体。由目标仓库现有表示承载，不强制新增 JSON 运行时依赖。

### C1.2 不同可见集合

**相机不可见，不等于不能投影或被反射看到。**

- 主视图集合：继续复用 v1.0.13 culling/LOD。
- 阴影集合：按光源、阴影覆盖与预算构建，保留屏幕外但会遮挡受光面的几何。
- 反射/AS 集合：按 ray 作用范围、距离和允许的近似选择，不能直接照搬主视图 frustum。
- 低精度代理、影子专用 LOD 和剔除范围是显式画质策略；与实际材质、动画和资源驻留关联。
- 多视图/壁纸实例之间可共享不可变资源，不能复用错误的 camera-specific 列表或 history。

### C1.3 Shadow-map 默认实现

提供稳定的方向光 shadow-map/CSM 与局部灯光 atlas 的设计、最小参考实验和选型，不要求每个目标引擎同时引入全部方案。

必含：投影范围、级联分割、texel 稳定性、depth/normal/slope bias、过滤和边缘行为、atlas 区间/guard、缓存失效与投影者 LOD。bias 不使用对所有尺度都有效的固定魔数；过滤格式/比较采样支持按设备查询。

受影响材质和动画改变时，影子缓存必须失效。用静止相机/缓慢平移/移动灯光/薄片几何/远近尺度比较自阴影、悬浮阴影、级联跳变与闪烁。先解决正确性再测成本，不以“关掉投影者”制造性能提升。

### C1.4 反射与间接贡献的有限范围

基础档保留环境/预过滤探针；有条件增加 SSR，处理屏外、遮挡、深度厚度和失配的置信度，回退到合法探针/既有路径。平面反射可作为已有实现的选项，但不要求本版另做完整系统。

本版新增 Ray Query 的效果参考以**遮挡/阴影和单次反射**为主；AO 可复用相同查询合同。它们不是完整全局光照，不用模糊后的屏幕空间效果冒充路径追踪。

**C1 交付**：数据合同、可见集合关系、稳定 shadow-map 工作流、反射回退表、基础图像样例与定位清单。

---

## 6. C2：Ray Query、BLAS/TLAS 与 alpha-mask 条件增强

### C2.1 能力不混绑

以 `VK_KHR_ray_query` 为可选路径；查询并启用所需的 AS、buffer device address、相关依赖、limits 和所选 shader 路径。[S16] 扩展依赖按固定 Registry 解析，不统一要求升级到 Vulkan 1.4。

- Ray Query 可在已有 graphics/compute shader 内执行，不等于要创建 Ray Tracing Pipeline。[S7]
- Query-only 路径不因为名字含“ray”就加入 SBT usage、`vkCmdTraceRaysKHR` 或 `RAY_TRACING_SHADER` stage。
- Ray Query 与 Bindless、Mesh Shader、Descriptor Heap、独立 compute queue 分别决策；不是互相默认前置条件。
- 缺任一必要能力时走 C1 基线，不按 GPU 名称/Android 版本猜测支持，不不断重试失败初始化。

### C2.2 AS 数据与生命周期

在现有 allocator、资源表和退休系统上建立 AS 子合同，复用 v1.0.13 的驻留、取消与 generation，不新建第二套 ResourceManager。

```text
几何上传/蒙皮完成
→ 选择有效驻留的 geometry generation
→ 查询 build/update 大小及 scratch 对齐
→ 构建/更新 BLAS
→ 显式依赖
→ 构建/更新 TLAS
→ 显式依赖
→ fragment/compute Ray Query
→ 最后使用完成后回收旧 AS / scratch / 被引用数据
```

必需处理：

1. BLAS/TLAS owner、输入 geometry/index/instance 范围、数据格式与地址有效性。
2. build/update/trace 内存、scratch、compaction 新旧并存峰值分别预算；不能只统计 AS 最终大小。[S18]
3. scratch 的 device address 对齐以及并行 build 的区域不重叠；串行复用需有依赖。
4. 一次多 build 调用内部不隐含依赖；相关 BLAS 与依赖它的 TLAS 不可假定由数组顺序保证。[S8]
5. rigid transform 更新与 geometry/topology 改变分开；是否允许 UPDATE、哪些参数必须保持一致按规范核对，条件不满足则 BUILD。[S8、S17]
6. compaction/move 后发布新 AS 地址并更新关联 TLAS/descriptor；旧地址仍被 in-flight 使用时保留旧对象。
7. build 完成后输入/scratch 可按规则复用，但 hit-shading 仍读取的顶点、材质和纹理必须单独存活；“AS 自包含”不代表整套材质数据可释放。
8. 主视图看不见、mesh 请求取消或某个 Engine 退出，不自动授权回收其他 query/TLAS 仍引用的 BLAS。

### C2.3 Producer/consumer 同步表

以下是待落地核对的 **Sync2 示例合同**，不是要求旧引擎一律迁移 Sync2。采用 legacy 路径时做等价映射并验证。[S8、S14]

| 实际 producer | 实际 consumer | 核对的 stage/access 关系 |
|---|---|---|
| transfer copy 写 geometry/instances | AS build 读取输入 buffer | COPY/TRANSFER_WRITE → ACCELERATION_STRUCTURE_BUILD/SHADER_READ |
| compute 蒙皮写 vertex buffer | AS build 读取顶点 | COMPUTE_SHADER/SHADER_WRITE → ACCELERATION_STRUCTURE_BUILD/SHADER_READ |
| BLAS build 写 AS | TLAS build 读 BLAS | AS_BUILD/AS_WRITE → AS_BUILD/AS_READ |
| TLAS/BLAS build 写 AS | compute 中 Ray Query | AS_BUILD/AS_WRITE → COMPUTE_SHADER/AS_READ |
| TLAS/BLAS build 写 AS | fragment 中 Ray Query | AS_BUILD/AS_WRITE → FRAGMENT_SHADER/AS_READ |
| compute query 写结果图 | 时域/合成实际读取 | COMPUTE_SHADER/SHADER_WRITE → 对应 shader stage/read，另核 image layout |

不得将 query shader 的 AS 读取一律记为 RT pipeline 专用 stage。跨 queue 另检查 semaphore、共享模式和必要的 ownership transfer；同 family 不代表两个不同 queue 自动有依赖。

### C2.4 阴影与反射查询语义

- 阴影遮挡测试和最近命中反射不是同一种终止条件。遮挡路径在满足其内容条件时可早停；反射不能用“遇到首个候选”替代最近有效命中。
- alpha-cutout 的 candidate 需要按材质规则判断并继续/确认；不能一律标 opaque，也不能忽略所有 cutout 几何后声称画质等价。
- 透明 alpha blending 与二值 alpha testing 分开；OMM 不是通用半透明折射或混合加速器。
- origin offset、tMin/tMax、变换、normal 与浮点误差按空间尺度处理；用薄片、接触点与不同尺度验证漏光/自相交。
- 反射 shader 用于命中材质的数据仍要满足 descriptor、索引、LOD 和驻留边界。

### C2.5 OMM：资料与测试必交付，硬件实现条件启用

新增 OMM 选型、扩展分支和正反例，不要求所有设备建立 micromap：

- 将静态 alpha-mask、频繁变动 alpha、普通 opaque 和 alpha-blended 内容区分。
- 记录 mesh/UV/alpha texture/cutoff/材质表达的烘焙兼容标识；运行时改变后重新构建、禁用或回退，不继续用过期分类。
- KHR 与 EXT 路径分别核对对象、依赖、feature、命令和 shader 控制；不能替换后缀就认为同一 ABI。[S10]
- unknown opacity 状态如何交给 query/material 路径要明确，不能把 unknown 全部当透明来减少成本。
- 本版不复制厂商 UE 分支或新增完整 baker；使用合法可分发的精简静态输入或已有工具输出，保存来源和 hash。
- 执行 OMM A/B 时内容、构建偏好和 ray 工作负载保持一致。Arm 的工程结果只作为实验设计参考，不预设相同提速。[S5]

### C2.6 动态几何研究的处理

AMD 的 tetrahedral cage 资料用于提醒：AS 更新成本和内存可能先成为瓶颈。[S2] 本版先提供 conventional BLAS rebuild/update、静态共享、动画/阴影 LOD 和预算策略。cage 生成、几何变形近似和桌面实现移植不纳入必交付；只有目标项目被证据证明受此瓶颈限制时另立实验。

**C2 交付**：能力矩阵、AS 生命周期/同步合同、query-only 正反例、混合阴影/单次反射精简实验、alpha-mask/OMM 决策与回退。实际 RT/OMM 未运行则单列未验证。

---

## 7. C3：时域输入、重投影与去噪

### C3.1 统一语义，不统一所有 SDK 的格式

为每个时域消费者定义输入合同，至少包含：

```text
viewId / frameId / sceneGeneration / geometryGeneration
inputSize / outputSize / viewport / historySize
motionDirection / motionUnits / jitterConvention
currentAndPreviousCamera / currentAndPreviousObjectState
depthConvention / normalSpace / exposureOrPreExposure
colorEncoding / alphaConvention / confidenceSemantics
historyGeneration / resetReason / completedUse
```

这些是项目合同字段，不是现成 Vulkan API。MV 是 current→previous 还是 previous→current、pixel 还是 UV、是否含 jitter，必须由生产者与消费者匹配。不能默认所有算法接受同一种约定。

相机运动、刚体运动、蒙皮/变形和程序化动画分别有 previous state；仅有上一帧相机矩阵不足以重建运动物体。frame slot、swapchain image index、逻辑渲染帧和呈现帧的编号不可混用。

### C3.2 History 校验与失效

以 View/Engine/资源 generation 隔离 history。以下事件须有显式策略：camera cut、投影/viewport 改变、输出/输入尺寸变化、暂停/跳帧、资源替换、材质与光照突变、效果切换、Device 重建。

每个事件选择“保持、重采样、局部拒绝或整体重置”，并记录依据；不能一律每帧清空，也不能永久复用旧数据。分辨率切换若适配器不支持重采样，走合法重建路径。

重投影至少检查越界、depth/normal 不一致、disocclusion、history age/confidence 和材质变化。移动灯光、阴影移动和粒子亮度变化可能没有对应 geometry motion，需降低历史信任度，不能把 MV=0 当场景静止。

### C3.3 传统时空滤波基线

提供一个非神经的可编译最小参考：history rejection/限制 + 边缘感知空间滤波；算法参数由场景固定，不追求本版构建通用商业 denoiser。

必须区分：

- 阴影 visibility、AO 标量与反射 radiance 的数值范围和可组合方式。
- diffuse/specular 分量与 roughness、hit distance 等辅助数据的适用性；不把所有结果喂同一“通用模糊”。
- exposure/pre-exposure 的变更与历史重标定，不能直接累积不同曝光尺度的值。
- spatial filter 的 normal/depth 边缘与 temporal filter 的反遮挡；不能靠加大模糊消除所有噪声而不记录细节损失。
- history ping-pong 的真实跨帧依赖、多个 frames-in-flight 和回收条件；二维纹理存在不等于其内容已就绪。

### C3.4 与已有超分/插帧路径协调

复用 v1.0.11 `mobile_neural_graphics.md`，本版只补通用时域适配、输入可视化和效应组合，不另造神经 SDK 集成框架。

ANF 的已读公开指南可作具体对照：SR 的颜色/深度带场景 jitter，MV 不含 projection jitter；FG 对尺寸/jitter 有不同合同，不能直接把不同分辨率的 SR 辅助输入传给 FG；UI 分开合成。[S9] 这些约束归属于对应 SDK revision，不推广到所有厂商路径。

调用前输出清晰的 pass 顺序：遮挡/反射信号 → 对应滤波 → 合成 → 选定 upscaler/FG → UI/显示。是否先做某个后处理由 SDK 与颜色合同决定，不硬编码一条适用于全部引擎的顺序。避免在上游和下游重复 TAA/锐化/曝光处理。

增加诊断视图：motion vector 方向/单位、jitter、线性深度、history weight/rejection、disocclusion、shadow visibility、reflection hit/confidence。诊断视图是真实资源输出，不是模型生成的“正确效果图”。

**C3 交付**：时域合同、history 状态表、传统滤波参考、SDK 适配差异表、动态序列正反例。

---

## 8. C4：画质、性能与持续功耗取舍

### C4.1 三档不是硬编码机型表

| 档位 | 典型路径 | 条件与降级 |
|---|---|---|
| Baseline | 既有光照 + shadow map + probes；可选已有屏幕空间效果 | 不需要 Ray Query；最低支持集服从项目，不擅自提升到 1.4 |
| Hybrid | 少量指定效果用 Ray Query；低/半分辨率信号与传统时域处理 | feature、驻留、AS/trace 成本、画质满足才开；保留 C1 回退 |
| Enhanced | 匹配内容的 OMM、更高 ray/过滤预算、受支持的已有 upscaler | 独立能力与成本证据；不能靠设备品牌全量开启 |

按 CPU、AS build/update、ray pass、denoise、带宽、内存峰值和热状态决定调整项。使用滞回/冷却期、优先级和 generation 交接避免频繁开关；不每次温度波动就重建整个 Device。

### C4.2 A/B 比较合同

固定：场景与随机种子、相机轨迹、光源/动画、分辨率、render scale、画质档、驱动与工具版本、预热、采样窗口和可比热状态。将冷创建、稳态和压力恢复分开报告。

测量项：

- CPU/GPU frame time 分布（至少 median 与高分位），各 pass 的时间与可获得的真实 query/counter。
- AS 构建/更新/trace、滤波成本及新旧资源并存峰值。
- 原生渲染帧、生成帧、呈现帧分开；平均 FPS 不能代替延迟。
- 图像 ROI 的空间误差与时间变化：阴影边缘、薄片、反射轮廓、disocclusion、运动物体与高亮区域。
- 热状态和频率；只有存在合适测量来源时报告能量/功耗，不能用温度或 FPS 直接换算节电比例。

FP/HDR 图像用固定域和容差比较；不要求所有 GPU 像素 hash 一致。SSIM/PSNR 等单值不能替代序列观察，也不能证明物理正确；先定义参考路径/高质量参考图的来源与限度。

### C4.3 预先定义判据

执行前在测试 manifest 中填入业务接受阈值、ROI、序列和误差解释；不得看完结果再放宽判据。硬性正确性失败（悬垂 AS、非法 usage/stage、过期 history、明显缺失投影者）不能被平均分掩盖。

不得承诺统一“60 FPS”或“提升 30%”。原 Skill 输入 token 的 30% 目标属于另一套冻结对照，不是 GPU 性能指标。

**C4 交付**：质量/成本分档表、匹配实验协议、机器可读记录模板、图像序列对照和明确的未验证状态。

---

## 9. 文件落点与整体结构控制

### 9.1 约束

保持 8 个 references 模块、既有路径与模板；**运行时知识文件净增目标 0、实际白名单包不超过当前 200 文件内部预算**。[R4]

这是主动控制结构，不是把所有内容挤入一个文件。每个新合同有一个权威段落，其余位置只放短摘要/稳定锚点；旧引用不变。复杂专题可按稳定锚点分批读取，不把所有新段落加入强制预读。

下列锚点为**计划新增**，不是声称当前仓库已存在。执行前先查重，必要时复用原有锚点。

| 主要现有文件（均相对 references/） | 计划权威段/更新 | 边界 |
|---|---|---|
| `02_core_mental_model/engine_architecture.md` | `#hybrid-lighting-decisions`：基础/混合/增强、不同可见集合、预算取舍 | 不复制 API 字段 |
| `02_core_mental_model/render_target_model.md` | `#lighting-temporal-data-contract`：深度/normal/MV/颜色语义 | v1.0.12 色彩链继续为上位合同 |
| `02_core_mental_model/modern_patterns.md` | 修正命中旧规则；增简短导航 | 不建第二套路由/同步规则 |
| `03_api_manual/06_pipeline/compute_pipeline.md` | `#ray-query-capability-contract`：query-only 能力、shader/RT pipeline 差异 | 明确 query 不限 compute；完整 AS 内存合同转下项 |
| `03_api_manual/04_buffer_image_memory/memory_allocation.md` | `#acceleration-structure-resource-contract`：AS/输入/scratch/压缩/更新/退休 | 复用 allocator 与 v1.0.13 预算 |
| `03_api_manual/08_synchronization/pipeline_barrier.md` | `#as-build-query-dependencies`：实际 producer/consumer 表 | 不复制 WSI 规则，链接其权威段 |
| `05_workflows/02_render_pass_effects/add_depth_pass.md` | `#stable-shadow-workflow`：稳定阴影、深度合同与可视化 | 先修普通 depth present 旧示例 |
| `05_workflows/03_compute_workflows/add_compute_pass.md` | `#hybrid-ray-query-workflow`：AS 准备→query→结果输出 | 图形 fragment-query 作为分支，不限定单队列/compute |
| `05_workflows/02_render_pass_effects/add_postprocess_pass.md` | `#temporal-quality-workflow`：历史校验、去噪、组合顺序 | 非完整神经/后处理引擎 |
| `05_workflows/02_render_pass_effects/mobile_neural_graphics.md` | 补 SR/FG 辅助输入协调与诊断链接 | 不再次集成 v1.0.11 SDK |
| `04_debug_playbooks/01_visual_issues/flickering.md` | history、shadow shimmer、MV/exposure 证据决策 | 无日志不直接归咎 GPU |
| `05_workflows/07_optimization/optimize_frame_time.md` | `#quality-budget-tiers`：各 pass 成本与降级 | 与现有持续热状态策略衔接 |
| `06_cases/06_performance/case_performance.md` | `#hybrid-quality-evidence`：公开案例与本地实验分开 | 不伪造真实案例或复制长篇厂商文档 |
| 索引、路由与 `07_integration_pack` | 命中段与验收/版本视图 | 不改变已有触发与宿主发现方式 |

变更预计覆盖约 14 个主体落点及必要索引，不把数量当硬性完成指标。原模板章节保持；新增锚点需通过独立段读取与链接检查。若某合同放入原文件会破坏职责，应先提出合并/拆分与包预算方案，不能静默超限或删除旧知识。

### 9.2 仓库职责

- Skill 仓库：规则、API/工作流/案例与既有本地契约/安全打包脚本。
- tests 仓库：计划原文/hash、90 天 source ledger、问题/rubric、实验 fixtures、原始回答、图像与运行记录。
- 不把历史答案、厂商 SDK 二进制、模型权重、抓帧或大图塞入 Skill。
- 维持评估读取隔离：模型不能读 rubric、预期答案和历史结果；工具日志才是读取证据。

---

## 10. 开发里程碑与依赖

仅一个主里程碑标记 in_progress。独立文档子任务可并行，但共同合同与路由由单一责任方整合，避免多 Agent 各自定义不同数据语义。

| 里程碑 | 内容 | 输入/依赖 | 交付及完成标准 |
|---|---|---|---|
| M0 基线与证据 | 固定两仓 SHA、规范/tool revision；读取差异；命中纠错；冻结旧 64 题 | 最新 main、原计划、官方资料 | baseline/source ledger；旧知识冲突已定位并定向修正；未验证列表明确 |
| M1 光照与数据合同 | C1；定义 C3 的 MV/depth/exposure/history 共同接口 | M0、v1.0.13 数据/驻留 | 光栅基线、可见集合、shadow/reflection 回退、原始诊断输出 |
| M2 可选混合查询 | C2：能力、AS、query-only、alpha/OMM 条件 | M1 合同、allocator/retirement | query-only 实验、AS 状态/同步正反例、可用回退；unsupported 项单列 |
| M3 时域稳定 | C3：history、传统滤波、已有 SR/FG 协调 | M1 的原始信号，可与 M2 部分并行 | 无模型依赖的时域参考与动态序列；多实例状态隔离 |
| M4 综合验收 | C4、题库、端到端场景、发布包 | M1–M3 | 最终 SHA 对应分层报告、图像/性能边界、包 manifest/hash；无权限或设备项不冒充通过 |

本版不附虚构人日或固定设备性能承诺。M2 某硬件增强不可运行，不阻止其余已授权静态、编译与基础路径检查；正式声明明确限定实际完成范围。

---

## 11. 精简端到端实验：Hybrid Quality Lab

复用 tests 仓库 Engine Scale Lab 的构建、资源和验证方式，新增受控场景/模式，**不另建完整商业引擎**。只有已有夹具不能表达时才加最小适配层，并说明原因。

### 11.1 一个场景覆盖四条主线

原创简化庭院：接触地面的几何、带 alpha-cutout 的叶片/栅栏、一个动画物体、一个反射平面/材质、屏外投影者、可移动灯光。可选第二 View 以不同尺寸观察同一场景。

模式：

1. Raster baseline：shadow-map + probe/允许的 SSR。
2. Hybrid：query 阴影；单次反射独立开关；不强制同时启用。
3. Temporal：同一原始信号，关闭/开启 history 与空间滤波对照。
4. Optional OMM / existing upscaler：能力支持且输入合同通过才运行。

### 11.2 固定序列

静止、慢平移、快速转向、相机切换、移动灯光、cutout 穿过阴影边缘、动画变形、切 LOD/卸载再加载、render-scale/曝光切换、暂停恢复、第二 View 销毁/重建。

保存场景 seed、全部参数、源与编译产物 hash、相机/灯光轨迹以及实际启用 features。不能把隐藏几何从基线删除而只在增强路径保留，再声称匹配比较。

### 11.3 设备与实现矩阵

| 设备/环境 | 可验证内容 | 不可自动宣称 |
|---|---|---|
| CPU 单测/模拟 | 状态机、依赖图、generation、题库/包契约 | Vulkan 执行或模型理解 |
| Shader 编译器 + SPIR-V 校验 | 选定 target 的语法/字节码/布局部分约束 | 驱动接受、图像正确 |
| 实际软件 Vulkan（能力不足需跳过对应分支） | 支持范围内的真实 dispatch/draw、基础数值/图像 | 移动 RT 性能、功耗 |
| 非 RT Android | Baseline、history、回退与持续运行 | Ray Query/OMM 已运行 |
| 支持 Ray Query 的 Android | AS 与 query、图像、成本和生命周期 | 其他型号/厂商同样支持 |
| 支持 OMM 的目标设备 | 对应 KHR/EXT 分支与匹配 A/B | 所有 RT 手机均有 OMM |
| 桌面 RT GPU | 开发调试、正确性辅助 | Android 的资源预算/延迟/热表现 |

Android 接入样例使用现有项目语言；新测试桥接优先 Java/JNI/C++，不强行引入 Kotlin。设备、厂商工具、商业 SDK 或模型调用需要本次环境与授权，不擅自购买云设备、取用凭据或注入系统级故障。

---

## 12. 新增 VIS14 行为与技术回归场景

保留现有 64 个场景的原始 prompt bytes 和历史结果；新增 **20 个 VIS14** 场景，目标合计 **84 个场景**。[R3] 对照条件放在同一场景内，不把两个输入条件算成两次已完成运行。

| ID | 对照输入/问题 | 必须体现的判断 |
|---|---|---|
| VIS14-01 | rayQuery/AS 支持但 RT Pipeline 不支持；另一个设备连 query 也无 | 不强加 SBT/RT stage；缺 query 走基础档 |
| VIS14-02 | 主相机外物体向屏内投影；第二条件物体确在光源范围外 | 区分可见集合，不直接复用主 frustum 结果 |
| VIS14-03 | 正 Z/反 Z、不同场景尺度与阴影 bias | 比较/清除/投影/bias 一致，不用固定常数解决所有情况 |
| VIS14-04 | SSR 命中有效；屏外/遮挡失配 | 使用置信度与合法回退，不补造屏外信息 |
| VIS14-05 | compute 蒙皮→BLAS→TLAS→fragment query | 逐资源正确 stage/access；BLAS/TLAS 不隐含有序 |
| VIS14-06 | 两次 build 并行共用 scratch；另一个有明确串行依赖 | 区间/对齐/复用条件不同，不能只看 buffer 句柄 |
| VIS14-07 | 刚体 transform 改变；geometry/topology 改变 | 检查 UPDATE 原始 flags/约束，不无条件 update |
| VIS14-08 | BLAS compact 后旧 TLAS 和帧仍 pending | 地址发布与退休分开；不能即时释放旧 AS |
| VIS14-09 | 主相机剔除/mesh 取消，但反射/TLAS 仍引用 | 共享驻留与 generation 正确，避免悬垂 |
| VIS14-10 | opaque、alpha-cutout、alpha-blend 三类 | candidate/nearest/early-out 不混用，不把透明通通当 opaque |
| VIS14-11 | OMM 扩展支持差异、烘焙 alpha 与运行时 alpha 改变 | KHR/EXT/unknown 分类/失效回退，不套后缀和旧数据 |
| VIS14-12 | MV 为 pixel 与 UV；含/不含 jitter | 明确转换与方向，不只检查纹理非黑 |
| VIS14-13 | 相机静止而蒙皮物体运动 | 不以 camera-only MV 通过；previous deformation 需要证据 |
| VIS14-14 | geometry 不动但灯光/阴影变化 | 历史置信度调整；MV=0 不等于辐射不变 |
| VIS14-15 | 曝光变化、HDR/pre-exposure 历史 | 对齐颜色尺度，不直接累积导致过亮/拖影 |
| VIS14-16 | resize/camera cut/多 Engine 两视图历史共享 | 明确 reset/resample/隔离，不能只按 swapchain index 取 history |
| VIS14-17 | 阴影 visibility 与反射 radiance 交给同一个滤波器 | 数据语义、边缘和参数分开，记录细节损失 |
| VIS14-18 | SR 输出喂 FG，depth/MV 尺寸不一致，UI 已混入 | 使用具体适配器合同，不直接透传低分辨率辅助输入 |
| VIS14-19 | 温度上升需要降档，随后短暂恢复 | 滞回/冷却/generation；不重建整个 Device、不伪造节电率 |
| VIS14-20 | 桌面 BVH/厂商 OMM 收益或旧教程更新时间 | 区分公开测量/技术推断/本地未测、首次发布/更新日期 |

每题先冻结 rubric，再生成新输出。自动 smoke 检查只检测可观察合同，必须另做人/独立审查的语义核对；不要仅靠出现“未验证”“barrier”等词通过，也不要强制复述固定中文句子。

### 分层结果

- Static：路径/锚点、来源/符号与包契约。
- Snapshot：历史固定输出，只验证样本及解析，不冒充当前模型。
- Host Unit：owner/generation、预算与状态机。
- Shader Unit：真实编译/验证及产物。
- Vulkan Integration：命名实现上真正运行 draw/dispatch/build/query 的结果。
- Live：当前 Skill 的真实模型读取与回答，保留原始输出和 usage。
- Android Device / Visual Quality：设备上真实输出/序列/性能/生命周期。

不存在的模型命令、设备能力或工具应写 BLOCKED/UNSUPPORTED/UNVERIFIED，并与真正代码失败分开；不能把 mock、静态解析或软件 Vulkan 解释成手机已通过。

### Token 与版本对照

原 v1.0.8 / 原始 12 题的 provider input-token 目标保持不动。VIS14 20 题单独统计，没有新增 30% 目标；v1.0.13→1.0.14 的旧 64 题不退化比较另列。不要用 84 题混合中位数替换原比较。

---

## 13. 证据与发布门槛

每次记录：Skill/tests SHA 和 tree、dirty state、规范/SDK/工具/编译器 revision、场景与输入 hash、模型 ID/参数/实际读取、输出/捕获 hash、Device/driver/features、执行命令、超时/失败、人工复核及验证覆盖。

上游 source ledger：日期字段、固定 URL/SHA、来源类型、技术变化与受影响文件、证据状态（source-read/build/device/live）、许可/再分发边界。Issue 或 AI-assisted 摘要不能单独证明规范事实；只转述必要短信息，链接原始资料，不把整篇厂商文档复制进 MIT 包。

发布检查：

1. 新触发/路由不会绕开原硬约束；普通知识问答仍不机械套完整工程报告。
2. 八模块、公共路径和旧规则不丢失； runtime 净增 0，白名单实际包 ≤200。
3. M0 命中错误修正，新 query-only/AS/时域语义没有已知关键错误。
4. 对最终候选执行既有安全/契约/静态测试；历史数字不直接沿用。
5. 旧 64 + 新 20 注册和隔离正确；Live 未运行不能写专家行为通过。
6. C1/C3 的可执行基线与 C2 的条件路径提供真实完成状态；缺 RT/OMM 硬件，不宣称对应设备验收。
7. 图像序列和性能结果采用预先确定的对照协议；单个漂亮截图不是时域通过。
8. 双次打包的内容一致性、CRC、per-file hash、无覆盖/脏树拒绝等安全行为保持。
9. 未完成 Live/宿主/Device/功耗/原 token 目标时单独列出；若只交付知识候选，明确范围，不称为全能力验收。

没有授权，不执行合并 main、上架、部署、权限变更、凭据处理、收费设备/服务或自动定时监控。此计划本身不是以上操作的授权。

---

## 14. 可直接交给 AI 的实施提示词

```text
基于两个仓库最新代码，实施 Vulkan Expert Skill v1.0.14：
Mobile Hybrid Lighting & Temporal Quality（移动端混合光照与时域画质）。

本计划核查基线：
Skill main 8d62f861b4ead27699e2ff3d80a1a9f0e72a4968，版本 1.0.13；
tests main 9c4cba3a3985b709ccdbec182c79a6988bfc721e。
最近90天窗口：2026-08-05至2026-11-02；固定原发布/更新日期与revision，
不要把爬取时间、SDK头文件存在或厂商品牌当成设备能力。

开始先读取AGENTS、git status/diff、两个HEAD、SKILL、release-contract、
已存在的路由/模板/安全打包、ENG13实验和评估读取隔离。
HEAD变化先核对增量，不回滚、不覆盖用户已有改动。

保留八模块、原模型/宿主配置、触发条件、最小启动、Evidence/Architecture Map、
影响面、R1-R5、适用G1-G6、安全打包和MIT。运行时知识净增0，白名单包≤200。
不重做v1.0.11神经SDK、v1.0.12系统呈现、v1.0.13资源/GPU-driven框架。

M0：固定Spec/Registry/tool版本并定向纠错：modern_patterns的timeline直接
acquire/present路径、过宽版本保证、add_depth_pass的普通depth直接present和
深度阶段/布局说明。新规则要能追溯，不用经验冒充SPEC。
M1：C1光照/深度/材质合同、相机/阴影/反射不同可见集合、稳定shadow-map基线、
SSR/probe回退，同时定义motion/depth/jitter/exposure/history共通接口。
M2：C2 query-only能力、BLAS/TLAS/scratch/update/compaction/retirement、逐资源
同步，混合阴影和单次反射实验；不强制RT Pipeline/SBT/Bindless/Mesh。
alpha-mask与alpha-blend分开；OMM的KHR/EXT/失效/unknown与回退分别核对。
M3：C3重投影、disocclusion、history隔离/失效、传统时空滤波与已有SR/FG适配；
不复制整套SDK、不把所有时域输入当同一种格式。
M4：C4匹配A/B、画质/帧时间/峰值/热状态分档；复用Engine Scale Lab添加精简场景。
冻结旧64题，新增VIS14-01..20，总84题；对照条件不冒充两次执行。

权威段与锚点按计划文件落点建立，其他位置简述+链接，不把新专题加入强制预读。
只在目标能力真实满足时运行RT/OMM；基础回退必须可用。
无模型/无设备则对应Gate明确BLOCKED/UNSUPPORTED/UNVERIFIED，继续其他可执行检查。
不改历史答案使测试通过，不把关键词测试、CPU模拟或软件Vulkan当移动真机证明。

原始12题token基线保持v1.0.8；VIS14单列，无新增30%承诺。
报告固定双方SHA/tree、sources、改动文件、权威锚点、包manifest/hash、
Static/Snapshot/Host/Shader/Vulkan/Live/Device独立结果、原始失败、
图像序列判据与数据、未验证项和回滚方法。

按本次明确授权执行文件修改；未授权提交/推送/PR/合并/上架/凭据操作不执行。
最终结论必须绑定最终候选输入，不能继承旧SHA或dirty工作区PASS。
```

---

## 15. 来源与复核入口

### 仓库证据（本次固定提交）

- **[R1]** Skill 入口：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/8d62f861b4ead27699e2ff3d80a1a9f0e72a4968/SKILL.md
- **[R2]** 变更日志：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/8d62f861b4ead27699e2ff3d80a1a9f0e72a4968/references/00_expert_entry/change_log.md
- **[R3]** 测试说明（64场景与分层）：
  https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/9c4cba3a3985b709ccdbec182c79a6988bfc721e/tests/README.md
- **[R4]** 发布契约：
  https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/9c4cba3a3985b709ccdbec182c79a6988bfc721e/release-contract.json
- **[R5]** 现代模式（本次命中旧规则）：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/8d62f861b4ead27699e2ff3d80a1a9f0e72a4968/references/02_core_mental_model/modern_patterns.md
- **[R6]** 深度工作流：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/8d62f861b4ead27699e2ff3d80a1a9f0e72a4968/references/05_workflows/02_render_pass_effects/add_depth_pass.md

### 90天资料与规范基础

- **[S1]** Arm Learning Path，Implement ray tracing effects with Vulkan on Android；页面更新2026-08-24：
  https://learn.arm.com/learning-paths/mobile-graphics-and-gaming/ray_tracing/
  页面部分直开返回text/markdown，本次由官方索引内容确认更新日期与范围；不依据AI-assisted FAQ独立形成硬规则。
- **[S2]** AMD GPUOpen，How tetrahedral cages significantly reduce BVH memory usage；2026-09-17：
  https://gpuopen.com/learn/how-tetrahedral-cages-significantly-reduce-bvh-memory-usage/
- **[S3]** Qualcomm，Introducing Adreno Neural Fusion SDK for Snapdragon mobile platforms；2026-09-22：
  https://www.qualcomm.com/developer/blog/2026/09/introducing-adreno-neural-fusion-sdk-for-snapdragon-mobile-platforms
- **[S4]** NVIDIA-RTX/NVRHI Issue #165；2026-10-17；本次读取为open，用户报告、未本地复现：
  https://github.com/NVIDIA-RTX/NVRHI/issues/165
  报告所指固定源码：
  https://github.com/NVIDIA-RTX/NVRHI/blob/6b96fb03e07539f08327aea76c56d55f1de9d906/src/vulkan/vulkan-upload.cpp
- **[S5]** Arm，Reducing ray-traced shadow costs for foliage with OMM: Moku results on Arm Mali G2；2026-10-22：
  https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/reducing-ray-traced-shadow-costs-for-foliage-with-omm-moku-results-on-arm-mali-g2
- **[S6]** Khronos Vulkan-Docs ChangeLog；读取时顶端为2026-10-30/1.4.367，blob SHA `3434a870d4823d7e786822b5adfc537e48ec96f2`：
  https://github.com/KhronosGroup/Vulkan-Docs/blob/main/ChangeLog.adoc
- **[S7]** Vulkan `VK_KHR_ray_query` 规范：
  https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_ray_query.html
- **[S8]** `vkCmdBuildAccelerationStructuresKHR`，含多build无隐含顺序、输入/scratch寿命及同步：
  https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdBuildAccelerationStructuresKHR.html
- **[S9]** ANF公开集成指南，读取blob SHA `4e58751c2937b824f2a87df8b3477482e653cef9`；实施前固定对应commit/tag：
  https://github.com/SnapdragonGameStudios/adreno-neural-fusion/blob/main/INTEGRATION-GUIDE.md
- **[S10]** KHR/EXT Opacity Micromap，对象与依赖分别核对：
  https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_opacity_micromap.html
  https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_opacity_micromap.html
- **[S11]** Filament release notes，读取blob SHA `82cf76a6a54bdbb42041645d2a80f19c2677715b`；main段落不等于对应release已发布：
  https://github.com/google/filament/blob/main/RELEASE_NOTES.md
- **[S12]** WSI semaphore边界：
  https://docs.vulkan.org/refpages/latest/refpages/source/vkAcquireNextImageKHR.html
  https://docs.vulkan.org/refpages/latest/refpages/source/vkQueuePresentKHR.html
- **[S13]** Present 对象与layout约束：
  https://docs.vulkan.org/refpages/latest/refpages/source/VkPresentInfoKHR.html
- **[S14]** 同步阶段与查询实际执行阶段：
  https://docs.vulkan.org/refpages/latest/refpages/source/VkPipelineStageFlagBits2.html
  https://docs.vulkan.org/spec/latest/chapters/synchronization.html
- **[S15]** Khronos Basic Ray Queries 样例；已有标准graphics pipeline中fragment query投影：
  https://docs.vulkan.org/samples/latest/samples/extensions/ray_queries/README.html

- **[S16]** 加速结构扩展、版本依赖、核心对象/命令：
  https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_acceleration_structure.html
- **[S17]** AS build/update 几何信息与合法性：
  https://docs.vulkan.org/refpages/latest/refpages/source/VkAccelerationStructureBuildGeometryInfoKHR.html
- **[S18]** AS 与 build/update scratch 大小查询：
  https://docs.vulkan.org/refpages/latest/refpages/source/vkGetAccelerationStructureBuildSizesKHR.html

`latest`/`main` 链接会变化。实施应保存固定source revision/hash及核验日期。本轮没有把第三方性能数字转化为本项目验收结果。

---

## 16. 本轮交付状态

- **完成**：读取最新两个main和关键文件；对照v1.0.13范围；扩展90天检索；筛选新资料；制定v1.0.14范围、文件落点、里程碑、20题与实验/发布边界。
- **未验证**：真实模型、实际宿主、源码/Shader编译、Vulkan/GPU/Android执行、OMM/RT支持、画质与性能/功耗、最终发布包。
- **失败/限制**：部分官方网页直开失败或缓存日期不一致，已使用官方索引/连接器补证并保留日期边界；没有可靠来源的X条目未采纳。
- **仓库写入**：无。本文为新的日期/版本文档，不覆盖此前计划文件。
