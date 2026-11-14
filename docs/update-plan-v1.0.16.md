# Vulkan Expert Skill v1.0.16 开发计划
## Mobile GPU Simulation & Dynamic Geometry — 移动端 GPU 仿真与动态几何

> 编制日期：2026-11-07。  
> 资料窗口：**2026-08-10—2026-11-07，含首尾 90 个自然日**。  
> 状态：开发计划；本轮只读核查、资料研究和文档生成，未修改远端仓库、调用被测模型、编译或运行 GPU/Android 实验。  
> 定位：让 Skill 能把绳索、布料、轻量形变、水面涟漪与交互粒子作为**可稳定更新、可验证、可回退的 Vulkan 数据生产者**接入现有引擎，而不是再建立一个通用物理引擎。  
> 前置边界：本轮读取的主仓入口为 **v1.0.14**；v1.0.15 仍以已交付计划作为依赖范围，不当作已合入或已通过验收。

---

## 1. 版本结论与不变约束

v1.0.13 解决 Shader、资源与 GPU-driven；v1.0.14 扩展混合光照与时域画质；v1.0.15 计划补透明、体积与 Gaussian 合成。v1.0.16 的新增问题是：**这些画面背后的状态如何随输入和时间演化，又怎样在移动 GPU 上安全地交给渲染器。**

四条主线：

| 编号 | 主线 | 必交付内容 | 本版不承担 |
|---|---|---|---|
| C1 | 仿真时钟与状态合同 | 固定步长、输入重采样、暂停/恢复、预算、状态代际与多视图共享 | 联网锁步、全平台逐位确定性 |
| C2 | 轻量 XPBD 与动态几何 | 绳索/规则布料、基础约束、解析碰撞、无浮点原子基线、数值对照 | 通用刚体、撕裂、复杂自碰撞、完整毛发系统 |
| C3 | 水面与交互粒子场 | 有界高度场涟漪、外部扰动、边界、粒子单向事件、有限邻域合同 | 完整三维流体、SPH/PBF/MPM 生产求解器、双向多物理耦合 |
| C4 | Compute—渲染协同 | kernel 读写所有权、逐阶段同步、快照、法线/包围盒/运动向量、能力回退与持续成本 | 默认异步队列、默认 FP16、默认浮点原子、另一套 RenderGraph |

“必交付”指知识、来源、工作流、适用边界、回退、验收题和精简实验材料全部具备。文档完成、模型行为、Shader 编译、Vulkan 执行和 Android 性能是不同验收层。

保持已有八模块、模型/宿主配置、触发条件、最小启动、19 条硬规则的原语义、唯一任务路由、按段读取、Evidence Map、Architecture Map、影响面分类、R1–R5、适用范围内 G1–G6、MIT 与安全打包。新增内容不加入固定启动预读。

## 2. 固定基线与前置版本处理

| 对象 | 本轮读取值 |
|---|---|
| Skill 仓库 | `oahc09/vulkan-rendering-expert-skill` |
| Skill main SHA | `4a7ff82372648c4a9df91e76848cbc9c95de51a3` |
| SKILL metadata | `version: 1.0.14`；`last-updated: 2026-11-07` |
| 测试仓库 | `oahc09/vulkan-rendering-expert-skill-tests` |
| tests main SHA | `f8cadd3614f998b042b77293618323120bcb6d28` |
| release-contract 被测 pin | `eff33ec1d8ec726c3978e47f570dd056bfd6d5d3`；expected version `1.0.14` |
| runtime 契约 | `max_runtime_files: 200`；`allowed_new_knowledge: []` |
| 实际登记行为集合 | README 记录为 84：旧 64 + VIS14 20；不是 84 项本轮已运行 |
| 前置 v1.0.15 计划 | `Vulkan_Expert_Skill_v1.0.15_透明体积与3DGS渲染开发计划_2026-11-07.md` |
| 上述计划 SHA-256 | `6eb304df06c22f012c3d5e0ee05b654f58add75d50c843782c70613f098d2e45` |

依据：[R1–R5、P15]。main 与 release pin 不同先比对 tree、变更及证据，不自动判断错误，也不继承测试 PASS。本轮读取的 changelog 起始仍是 v1.0.13，实施时应核对版本记录是否在其他位置及其准确性；这不等于认定 v1.0.14 内容不存在。

实施前必须重新检查 AGENTS、git status、两仓 HEAD、已有分支和实际发布合同。HEAD 已前进时只做增量，不覆盖用户成果。

### 2.1 与前版的边界

| 已有/前置能力 | v1.0.16 如何复用 | 本版新增 |
|---|---|---|
| v1.0.13 粒子存活、compact、indirect、LOD、资源预算 | 继续使用现有 manager、计数与 command ABI | 状态积分、约束迭代、时间合同和状态快照 |
| v1.0.14 光照、运动向量、AS 与时域历史 | 接收新几何和对应的历史数据 | 仿真姿态、法线、bounds、渲染前姿态与可选 AS 更新的一致发布 |
| v1.0.15 水/玻璃、天气、体积和透明合成计划 | 接收 height/normal/particle 输入，不重做合成 | 水面状态和扰动传播；渲染外观与物理模型明确分离 |
| v1.0.12 多 Engine/Surface 与 generation | 保留 owner/ack 和局部销毁机制 | 一份仿真多输出时不能按输出数重复推进 |

若 v1.0.15 未合入，C1/C2 与不透明 wireframe/高度可视化可独立推进；透明外观对接保持前置未验证。不得把未落地的接口写成当前代码事实，也不直接把 v1.0.14 主干改号跳过前版。

---

## 3. 90 天资料筛选与证据强度

### 3.1 近期实现与复盘

| 日期/性质 | 核实内容 | 本版吸收 | 明确限制 |
|---|---|---|---|
| **2026-08-23、08-27，README 更新** | `steampower33/XPBD-Cloth` 文档说明 graph-colored stretch、atomic Jacobi 路径、分步计算和邻域缓存；作者明确经验调参与非逐位确定性。[S1] | 写冲突分析、算法路径区分、约束最小测试、邻域失效表 | 这两次是文档更新，不宣称算法在 8 月首次出现；Windows/RTX 配置不是 Android 测试 |
| **2026-10-20，报告提交；正文标记 10-21 测量** | `igor-polev/textile-wave` 补充稳定性/性能记录，并指出 CPU 完成等待的延迟可能误导自适应 substep 控制；文档还记录过多子步时的精度问题。[S2] | GPU 成本与 CPU 等待分开计量；预算调整必须受数值稳定范围限制 | 两个日期按来源原样保留，不混称发布日期；测量为作者/项目报告，未独立复现；WebGPU 不是 Vulkan 运行证据 |
| **2026-11-06，代码/演示更新** | `20niship/nebula` 合并新的 Blender 输出演示；固定版本包含 XPBD、PBF、MPM 等 Vulkan compute 路径和 CPU Vulkan CI 说明。[S3] | 可借鉴无窗口数值回读、求解器与渲染解耦、独立验收分层 | Blender 导出演示不等于实时移动；不同算法的对比不证明 Vulkan API 比 CUDA 快；不复制其大规模数值承诺 |

没有找到需要提升本技能最低 Vulkan 版本的新强制特性；本轮近期材料的价值在**并行求解和工程测量经验**，不是为使用新扩展而使用新扩展。X 可继续发现线索，本轮没有将不可核验的社交帖、播放量或点赞数纳入计划依据。

### 3.2 长期基础，不冒充近期新闻

- XPBD 原始论文为 2016 年，Small Steps 为 2019 年；本轮核查了原文方程、求解流程和精度限制。[S4、S5]
- Ten Minute Physics 的高度场与软体教学仅作模型/CPU 对照来源，不把浏览器演示当作原生手机 Vulkan 基准。[S6]
- Khronos 的 Workgroup/Subgroup、同步、原子 feature 和时间查询规则作为 API 权威；实现代码不能覆盖规范。[S7–S11]
- Android reduced-precision 与 Arm profiling 文档用于能力和测量边界，不因为页面近期抓取就称为近期新特性。[S12、S13]

来源台账必须包含 `event_date / published_date / checked_at / fixed_revision / claim / source_level / target_anchor / local_build / device_status`。许可不清楚时只写自主分析，不复制源码；依赖、模型和数据的许可证分别检查。

---

## 4. C1：仿真时钟、输入与状态快照

### 4.1 首先定义时间，不把 render dt 直接当求解步长

建立独立合同：

| 字段 | 含义 |
|---|---|
| `simulationTick` / `simulationTime` | 已实际完成的离散仿真进度 |
| `fixedStep` | 每次完整更新的时间长度，独立于屏幕刷新率 |
| `substeps` / `solverIterations` | 时间细分与每步约束求解次数，不互换术语 |
| `accumulator` / `droppedTime` | 待推进时间及主动丢弃的时间，不能默默吞掉 |
| `inputTimestamp` / `eventId` | 输入发生时刻和去重身份 |
| `worldGeneration` / `topologyGeneration` | 场景重建与拓扑更新代际 |
| `snapshotId` / `completion` | 可供渲染读取的完整状态及其完成条件 |

默认使用固定外层 tick 与有限子步；渲染可插值，不能为了补偿掉帧无上限追加任务。暂停恢复时显式选择“暂停世界时间”“有限追赶”或“重置”，默认不将后台的几十秒直接积分。高刷新率只改变采样/呈现，不默认改变仿真速度。

预算不足可以暂缓非必要工作、降低模拟规模或使用已验证质量档；不能仅为满足帧预算把子步砍到已知不稳定范围。改变 tick/substep 后必须重新核对 compliance、damping、驱动点速度和输入脉冲，不保证材料行为完全不变。[S4、S5]

### 4.2 输入与多个输出

- 触摸/拖拽/风场输入按 simulation time 重采样；一次 impulse 有唯一 eventId，不能每个渲染帧或每个子步重复施加同一脉冲。
- 持续 force 与瞬时 impulse 分开表示；单位、坐标空间和积分方法写清。
- 驱动固定点不只是 `inverseMass=0`：还要提供当前/上一仿真时刻的目标位置及明确速度规则。
- 共享仿真只由一个调度 owner 推进；壁纸、预览或第二相机是多个 consumer，不分别推进相同世界。
- Surface 暂停与仿真暂停不是同一事件。可见性策略决定是否继续更新，所有 consumer 的退休仍需完成证据。

### 4.3 数值故障处理

所有状态处理 `NaN/Inf`、零长度约束、无效质量、非正 dt、异常输入幅值及容量越界。可选择拒绝输入、冻结到最后有效 snapshot 或受控重置；必须计数并输出诊断，不用无限速度裁剪掩盖算法错误。

数值确定性分三级报告：固定输入下的算法可复现、同实现容差内可重复、跨设备结果容差可接受。不得把 seed 固定或消除数据竞争等同于跨 GPU 浮点逐位一致。

**C1 验收：**30/60/120 Hz 呈现使用相同 tick 输入时仿真进度一致；长暂停不会产生无限追赶；多 view 不倍增时间；输入恰好按定义消费。

---

## 5. C2：轻量 XPBD、绳索与规则布料

### 5.1 本版必须实现的最小范围

1. 两粒子距离约束与固定端点 CPU 数值对照。
2. 可交互绳索/短链，球/平面/胶囊解析碰撞。
3. 规则网格布料：距离伸长、剪切及明确标为近似的距离弯曲约束；不假冒完整连续体材料。
4. 同一组件支持拉拽、挂点变化、暂停/恢复和拓扑重建。
5. 输出更新后的顶点、法线与保守 bounds，接现有 graphics 路径。

小型体积约束/四面体软体作为 **P1 条件扩展**：需要单独的非退化体积、翻转与参数测试；没有合格输入网格时不强做。短链可用于摆动物件或少量发束，但完整毛发渲染、碰撞簇、塑性、撕裂、通用自碰撞不在本版完成承诺内。

### 5.2 XPBD 数值合同

对一个标量约束 C(x)，以本次子步长度 h、inverse mass w、compliance α 记：

```text
α̃ = α / h²
Δλ = ( -C(x) - α̃ * λ ) / ( Σ_i w_i * |∇_i C|² + α̃ )
Δx_i = w_i * ∇_i C * Δλ
λ ← λ + Δλ
```

这是 XPBD 原文的标量展开，不是所有接触、摩擦或材料模型的通用即插即用公式。[S4]

要求：

- 基线每个积分子步初始化 λ；同子步内多次 iteration 累积，不能每个 iteration 都清零。warm start 是独立策略，另定重标定与失效条件。
- `α/h²` 使用实际子步 h，不使用整帧 dt。硬约束 α=0 与无可移动粒子的退化情况分别处理。
- 速度按最终修正位置与该子步旧位置重建，再执行明确的阻尼/碰撞规则。
- Substeps、iterations、浮点精度和 dispatch 开销一起报告；更多子步不是无条件更准，论文已说明过小步长的浮点限制。[S5]
- 接触不等式、单边推离和释放条件不能照搬双边距离约束；本版基础碰撞允许显式标记为解析投影近似。

### 5.3 两条无浮点原子的并行基线

| 路径 | 实现合同 | 风险与验证 |
|---|---|---|
| Graph-colored in-place | CPU 验证同颜色约束不共享被写粒子；颜色之间分 dispatch 并建立正确依赖 | 不能只按“不同 constraint ID”判断无冲突；拓扑变化必须重新着色 |
| Jacobi + gather | 从只读预测位置计算每约束贡献，写独占临时槽；由每粒子唯一 owner gather 后统一 apply | 两端贡献、归一化、relaxation 和 λ 更新与 CPU 同算法对照，不能只复制 GS 公式后假定收敛等价 |

`VK_EXT_shader_atomic_float` 是可选增强；精确检查 buffer/shared/image 与位宽对应的 feature 并启用。没有该能力时必须能走上述基线，不能将整数原子可用误推为浮点加可用。[S9]

固定点、退化边、重复约束、重拓扑、极硬/极软参数是必测输入。半精度只对经过误差评估的字段考虑；默认位置积分、残差和约束求解保持 FP32，不强制手机 FP64。

### 5.4 碰撞范围和邻域边界

P0 只承诺解析碰撞器和低成本短链/网格，不承诺不穿透的通用连续碰撞。快速移动物体要检测位移与尺寸的关系，增加经验证子步、使用 swept 解析检测或限制交互；方法和能力边界显式标注。

若扩展自碰撞或粒子近邻，使用已存在的 sort/scan 基础并验证 cell、hash collision、负坐标、候选过滤、列表容量、静态邻接排除及高速运动后的失效条件。候选溢出不能静默截断后宣称碰撞正确；参考项目按间隔复用邻域只是近似，不是保守碰撞保证。[S1]

**C2 验收：**CPU/GPU 同算法位置与残差在预注册容差内；同色写集合无交集；无浮点原子设备可用；异常参数可拒绝或安全降级。

---

## 6. C3：水面涟漪与交互粒子场

### 6.1 明确模型，不把所有“水”叫流体仿真

基础交付采用 **二维高度场波动模型**，面向水庭、点击涟漪和浅表扰动。高度场每个平面位置只有一个高度，不支持翻卷、破碎、多值表面、完整体积流动；它不自动等于非线性浅水方程或 Navier–Stokes。[S6]

状态至少含 height、velocity 或相邻两个时刻的 height、边界 mask、扰动事件、模型版本和 generation。波速、世界尺度、网格间距、阻尼与时间步长写入配置，不通过屏幕像素大小隐式控制物理速度。

### 6.2 可验证的更新路径

```text
输入事件按 tick 消费
→ bounded source/impulse 注入
→ 读取前一稳定场 + 更新下一场
→ 边界处理
→ normal/gradient 输出
→ 发布对应 tick 的 height + normal snapshot
→ v1.0.15 水/玻璃渲染或独立高度可视化
```

全局 stencil 更新采用不同输入/输出存储，不以 shader 内 workgroup barrier 实现全网格同步；storage image 格式不可用时保留 SSBO 路径。[S7、S8]

对于均匀网格、常波速 c、显式中心差分的线性二维波动基线，可以从离散稳定性分析得到检查量：

```text
r = c * h * sqrt(1/dx² + 1/dy²)
```

该理想模型要求 r 不超过 1，工程测试还需安全裕量。它是所选离散模型的约束，不是所有水面算法统一的 CFL 定理；阻尼实现、边界、非线性或耦合变化后重新推导/测试。不要靠高度 clamp 掩盖不稳定。

### 6.3 边界与输入

- 无外力、全零初态必须保持平静；边界选固定、反射或耗散并独立测试。
- 单次扰动在固定 tick 施加，改变渲染 FPS 不改变注入次数。
- 改变网格分辨率后保持世界尺寸与波速语义；重采样、清空或保留状态的策略须显式。
- 扰动重叠由单元 gather 或独占事件归约处理；不默认多个线程可以普通加法写同一 texel。
- height 与 normal 来自同一状态；旧 normal 配新 height 是可检测的不一致，不通过增加滤波隐藏。

### 6.4 粒子与水面的受控联系

复用 v1.0.13 的粒子池、存活列表和 indirect；只增加连续 force、瞬时 impulse、解析碰撞、有限寿命、事件 ID 和按 tick 的扰动转换。

“雨滴撞击水面产生波纹”默认是**单向视觉耦合**：碰撞生成一次有界事件，水面消费它。没有质量/动量交换方程和对照实验时，不宣称双向守恒耦合。

PBF、SPH、MPM 的区别、适用条件和迁移成本可记录到现有架构决策段，生产级实现后置。特别是流沙/颗粒摩擦和液体不可压缩性不是加几条距离约束即可准确解决，不从演示外观倒推物理正确。

**C3 验收：**静水、单脉冲、双脉冲、边界、非法步长、尺寸变化和密集事件均有数值判据；新增模型可以独立于透明渲染验收。

---

## 7. C4：Kernel、同步与渲染协同

### 7.1 四种同步范围不能混用

1. 单 invocation 对自己独占输出的写入。
2. Workgroup 内 shared-memory 通信与 barrier。
3. Dispatch 之间的资源访问依赖。
4. Queue 之间的执行/内存依赖与需要时的所有权交接。

`barrier()` 的 workgroup 协同不能等待整个 dispatch 的所有 workgroup。需要全局阶段顺序时，基线拆成 dispatch 并用 Vulkan 同步表达；禁止忙等全局计数器充当普通 GPU 的通用全局 barrier。[S7、S8]

尾线程不能在其 workgroup 的后续统一 barrier 之前随意 early-return；使用 active mask、为 shared 槽初始化中性值，并保证要求的参与和控制流条件。workgroup 大小、维度、shared memory、subgroup operation 支持分别检查，不能假定 subgroup=32/64。[S7、S10]

### 7.2 资源所有权表

| 资源 | 写入者 | 读取者 | 最早允许重用的条件 |
|---|---|---|---|
| 仿真 state A/B | 当前 tick 的积分/约束阶段 | 下一阶段或下一 tick | 全部依赖满足；仅双缓冲名字不构成安全证明 |
| λ/constraint scratch | 对应 solver stage | 同子步后续 iterations | 当前求解批次结束且无后续读取 |
| per-constraint contribution | 每 constraint 唯一 writer | 每 particle gather | gather 完成后才清空重用 |
| height/velocity | 对应 stencil 输出 pass | 后续更新及输出构造 | 当前引用者全部结束 |
| render snapshot | 发布 pass | 一个或多个 view、shadow、可选 AS build | 所有实际 consumer 完成，而非只等主相机 |
| previous-render snapshot | 帧历史管理器 | motion-vector pass | 该输出的历史消费结束 |
| feedback/readback | GPU 统计 pass | CPU 非关键路径观察 | 真实 completion 与 non-coherent invalidate 条件满足 |

仿真 state 和 render snapshot 可以使用不同存储策略。两个 ping-pong state 并不自动覆盖三帧在途和多个视图；缓冲数量由完整使用图决定。避免每帧读回全部顶点，调试或定期统计可单独执行。

### 7.3 同步表：按真实 consumer 选择

下表是同 queue 下典型 Sync2 路径；实施时核对实际 usage、范围、feature 与精确规范。[S8]

| Producer → Consumer | 典型源 | 典型目标 | 必须附带的检查 |
|---|---|---|---|
| transfer 初始化 → solver | `COPY` / `TRANSFER_WRITE` | `COMPUTE_SHADER` / `SHADER_STORAGE_READ` 或实际读写 | counter/state 初始化完整 |
| solver iteration → 下一 iteration | `COMPUTE_SHADER` / `SHADER_STORAGE_WRITE` | `COMPUTE_SHADER` / `SHADER_STORAGE_READ/WRITE` | buffer range；RAW/WAW/WAR 分析 |
| solver → 顶点属性读取 | `COMPUTE_SHADER` / `SHADER_STORAGE_WRITE` | `VERTEX_ATTRIBUTE_INPUT` / `VERTEX_ATTRIBUTE_READ` | 输出 buffer 含 vertex usage |
| solver → vertex shader SSBO | 同上 | `VERTEX_SHADER` / `SHADER_STORAGE_READ` | 与固定功能 vertex fetch 区分 |
| height/normal → fragment sampling | 同上 | `FRAGMENT_SHADER` / `SHADER_SAMPLED_READ` | sampled usage、格式与合法 layout；不强制无意义 transition |
| solver → indirect 参数读取 | 同上 | `DRAW_INDIRECT` / `INDIRECT_COMMAND_READ` | 命令/count 分别同步；延用 v1.0.13 的 ABI |
| deformed geometry → AS build（可选） | 同上 | `ACCELERATION_STRUCTURE_BUILD_KHR` / `SHADER_READ` | 顶点/index/instance 等输入 buffer 的读取；另查实际 AS 能力、输入 usage 与后续 build→query 依赖 |
| snapshot 读完 → 后续覆盖 | consumer 的实际 stage/access | solver 写入阶段 | 处理读后写，不仅写后读 |

表内 stage/access 为省略固定前缀的类别名；实际文档示例使用 Registry 核实的完整 `VK_PIPELINE_STAGE_2_*` / `VK_ACCESS_2_*` 标识，不把类别字符串直接当合法枚举。

AS build 必须区分读取的对象：输入顶点、索引、transform、AABB 和 instance 数据使用 build stage + `VK_ACCESS_2_SHADER_READ_BIT`；源/目标加速结构对象以及 scratch 的访问则按其相应 AS read/write 规则处理。不能因为 consumer 名称是 AS build，就把所有输入访问都写为 `ACCELERATION_STRUCTURE_READ_KHR`。[S14]

跨 queue 增加真实 semaphore/timeline 依赖；不同 queue family 且 exclusive sharing 时处理 ownership。相同 family 不自动需要 ownership transfer，也不自动省掉跨 queue 信号依赖。默认先做单 queue 正确基线；是否 async 取决于全帧 overlap、延迟、功耗和内存成本。

### 7.4 发布动态几何，不只更新 position

同一 snapshot 包括 tick/generation、position、normal、bounds、可用 topology/LOD、资源 generation。主视图、阴影、反射等可以消费同一姿态，但各自保留可见列表和完成归属。

- normal 重建避免相邻三角形同时无保护写同一顶点；使用贡献→gather 或经过门控的原子路径。
- bounds 必须覆盖变形后的 geometry；重新计算或有可证明的保守膨胀。静态 rest bounds 不能直接继续用于 GPU culling。
- motion vectors 使用该渲染输出上一展示姿态与当前展示姿态；不是无条件用上一 solver 子步。reset、teleport、拓扑/LOD 对应关系失效时使历史无效。
- 可选 Ray Query 需由相同 geometry generation 更新 AS，不能旧 BLAS 配新 position；是否 UPDATE 合法由前版 AS 合同确定，不无条件 refit。
- 多 Surface 共用仿真时，销毁一个输出只退休其 consumer；共享 state 生命周期仍由其他 consumer 决定。

### 7.5 移动端预算

分别计量 simulation、normal/bounds、上传/回读、同步等待和绘制。记录 substeps × iterations × colors/dispatches，不能用粒子数量单独解释成本。

GPU timestamp 能力按 queue 检查；结果异步获取，明确 timestampPeriod/有效位等规则。CPU 等待完成的 wall time 不冒充纯 GPU kernel 时间，持续热状态与帧预算和数值质量一起记录。[S2、S11、S13]

质量档可减少网格/链数量、简化碰撞器、关闭独立增强；不能为了加速任意改变 dt 而不复验。统计读取频率可以降低，但正确性依赖不能省略。软件 Vulkan 可用于部分正确性验证，不代表 Adreno/Mali 性能。

---

## 8. 能力与回退矩阵

| 能力/条件 | 基础选择 | 条件增强 | 不满足时 |
|---|---|---|---|
| Compute + storage buffer | P0 必需，按项目现有 Vulkan 最低基线接入 | 无 | 明确禁用该 GPU 仿真或使用项目已有静态/CPU 小规模路径；不切换渲染后端 |
| Synchronization2 | 项目已有时复用 | 更清晰的 stage/access 表达 | 映射现有 legacy 同步；不为此自动提高产品最低版本 |
| Float atomic add | 不依赖 | 仅具体 feature 支持且有数值/成本收益 | graph coloring / gather |
| Subgroup ballot/reduce | 不依赖固定大小 | 查询 stage、operation、size-control 后优化 | workgroup/多 dispatch 基线 |
| FP16 | 基础 solver FP32 | 经误差验收的存储或局部计算 | FP32；不以 FP16 支持推导全部 storage/IO 可用 |
| Storage image format | 明确查询 | heightfield 用受支持 image | SSBO + 输出转换或另一受支持格式 |
| 独立 compute queue | 默认不需要 | 可证明收益的 async | 单 queue；维持输入延迟和快照正确 |
| Ray Query/AS | 本版不是前提 | 对接 v1.0.14 的变形几何路径 | 传统渲染/阴影方案 |
| 自碰撞/软体 | 独立质量档 | 有界候选与专门数值验证 | 解析外部碰撞、低复杂度网格，不静默伪装已支持 |

支持、启用、编译目标、运行返回值与性能结果分别记录。API 版本、设备品牌、桌面运行成功都不能代替这些检查。

---

## 9. 文件落点与结构预算

### 9.1 核心知识落点

以下为**拟增加锚点**，不是已存在接口；实施前检查是否重名，并保留旧链接。

| 既有文件（相对 references） | 拟新增权威锚点 | 负责内容 |
|---|---|---|
| `02_core_mental_model/compute_graphics_relationship.md` | `simulation-state-contract` | 时钟、状态、generation、共享世界与 snapshot |
| `05_workflows/03_compute_workflows/add_compute_pass.md` | `simulation-scheduling` | 多 tick/substep 调度、输入消费、预算与暂停恢复 |
| `05_workflows/03_compute_workflows/compute_write_storage_buffer.md` | `xpbd-deformation-contract` | 绳索/布料、λ、两类并行基线、解析碰撞 |
| `05_workflows/03_compute_workflows/compute_write_storage_image.md` | `heightfield-simulation-contract` | 水面模型、边界、stencil、稳定性与输出 |
| `05_workflows/03_compute_workflows/compute_to_graphics_sync.md` | `simulation-render-handoff` | 阶段同步、快照、多 consumer、历史姿态与可选 AS |
| `03_api_manual/06_pipeline/compute_pipeline.md` | `simulation-kernel-portability` | workgroup/subgroup、原子、维度、tail 与能力门控 |
| `05_workflows/05_resource_management/manage_frame_resources.md` | `simulation-snapshot-retirement` | state 与帧资源不同生命周期、取消和回收 |
| `05_workflows/07_optimization/optimize_frame_time.md` | `simulation-cost-quality-budget` | 计时、质量档、持续负载、移动分档 |

API 正确性尽量引用现有 buffer/image/synchronization/query_pool 卡，不再在每个 workflow 复制整页定义。调试与案例按需在现有 `compute_no_output`、`device_lost`、`case_compute.md` 与 `case_performance.md` 类聚合文件的实际路径追加短入口；以索引真实路径为准，不能猜文件名后制造断链。

### 9.2 总体结构约束

- 八模块不变；本版 **运行时知识文件净增目标 0**，实际白名单包 **≤200 文件**，不把整仓 git 文件数当运行时包数。
- 不新建顶层 physics/simulation 技能，不加入新的启动文件，不变更模型路由和触发条件。
- 每个权威锚点需独立说明输入、适用条件、关键限制、关联规则和输出；测试单段读取不会拿到缺少前提的公式。
- 其他章节只维护短摘要和链接；允许有依赖的按需二轮读取，不通过巨大聚合文件强迫全文预读。
- 路由只在现有命中类别中增加细分导航；常规 API 问题不自动加载仿真规则。
- 原始第三方研究、源码快照、实验工程、原始模型答案与 rubric 在 tests 仓；runtime 不装大型项目、动画/GIF、benchmark CSV 或模型文件。
- 改 README/索引/版本时不丢失 v1.0.14/15 的新增记录；处理重复规则前记录旧位置到新位置的映射。

**结构验收：**文件/锚点完整，旧题及原始输入不变，原启动集合不变，安全打包仍失败关闭；token 节省只有实测才可宣称。

---

## 10. 实施里程碑

| 阶段 | 任务 | 交付/退出标准 |
|---|---|---|
| M0 | 冻结两仓、前置状态、来源、数值合同与测试判据；检查已有粒子/同步/资源路径 | 有差异清单；不重复 GPU-driven，不假定 v1.0.15 完成；所有新增知识有落点 |
| M1 | C1 + kernel/同步基础；建立 CPU 参考与最小 compute 消费链 | 固定 tick、输入去重、暂停、多 view、tail、读写集合与 snapshot retirement 测试可执行 |
| M2 | C2 绳索/布料与 C3 高度场/粒子事件 | 两条无 float-atomic solver 路线均提供最小 GPU 实验与同算法 CPU 参考；实际编译/执行状态分别报告；水面数值独立验证，碰撞与回退完整 |
| M3 | C4 输出法线/bounds/history、可选 AS 与移动预算；接现有渲染实验 | 同姿态跨 pass、无提前回收；成本与误差可分别采集；不让视觉滤波替代数值验收 |
| M4 | 注册 SIM16、运行可用验证层、配对 Live、移动设备对照与确定性打包 | 最终 SHA、输入输出、工具版本、包 hash 可追溯；各层通过/失败/未运行分开 |

M1 的数据合同冻结后，M2 的 buffer solver 与高度场可在文件/接口不冲突前提下并行；共享索引、版本、release pin 与报告串行汇总。不能通过多 Agent 同时改相同权威文件制造覆盖。

---

## 11. 实验与业务验收

### 11.1 复用实验设施，不新建生产引擎

在测试仓既有 Engine Scale Lab 基础设施中增加 Simulation 小场景/子目标；命名可为 `simulation_lab`，复用 device、allocator、shader build、离屏输出与日志。源码以 C++/GLSL 为默认；Android 桥接确有需要时用 Java，不引入 Kotlin 强制依赖。

三个场景可单独运行，也能合成一张“互动材料桌面”：

| 场景 | 内容 | 数值与工程重点 |
|---|---|---|
| Rope & Cloth | 固定绳索、可拖拽布片、球/胶囊碰撞器 | 两粒子 oracle、残差、固定点、颜色冲突、退化约束与 snapshot |
| Ripple Garden | 网格水面、点击脉冲、少量落雨事件 | 波速/步长、边界、事件一次消费、height/normal 对应与尺寸变化 |
| Shared Dynamics | 两个 view 共享同一仿真；其中一个暂停/销毁 | 每世界只推进一次、上一渲染姿态、资源退休和输出独立性 |

建议实验档位：绳索 32/128/512 节点，布片 16×16/32×32/64×64 顶点，水面 64×64/128×128/256×256。它们是输入规模，不是全机型性能承诺。保持相同算法、步长、约束配置、碰撞器与视觉负载比较。

### 11.2 可在无手机环境先做的数值判据

- **硬距离约束**：x0=(0,0,0) 固定，x1=(1.2,0,0)、w1=1、rest=1、α=0、无外力。一次正确投影得到 x1=(1,0,0)。
- **柔顺距离约束**：同输入，h=0.1、α=0.01、λ=0，则 α̃=1、Δλ=-0.1，得到 x1=(1.1,0,0)。这是公式推导，不是已测 GPU 值。
- **迭代 λ**：对同一步重复求解时保留 λ；构造能识别“每轮清 λ 导致错误刚度”的对照。
- **零场**：全零水面、无事件与匹配边界应保持零；单脉冲按预定义时间到达并传播。
- **调度**：相同 simulated ticks 与输入序列、不同 render callback 节奏应消费相同 eventId；长暂停触发指定恢复策略。
- **碰撞/容量**：解析碰撞检查距离/穿透容差；容量满时触发声明的拒绝/降级，保留 overflow，不凭图像存在判成功。

最小两粒子 CPU FP64 参考可采用绝对误差 1e-12，对应基础 FP32 GPU 检查建议 1e-5（模型单位）；这些仅用于该小测试。复杂布料、水面和长期轨迹在 M0 预注册相对尺度、残差、漂移与可接受穿透阈值，不能直接套一个全局 epsilon，也不能看到结果后改阈值。

### 11.3 禁止危险“验证捷径”

负向测试优先验证配置拒绝、调度检查器、SPIR-V 校验与有界输入。不得为了证明检测有效，在用户真实设备上故意运行已知死锁的 shader、无界 busy-wait 或非法内存访问。模拟失败明确标为 host fixture，不叫真实 GPU fault。

---

## 12. SIM16 行为测试：16 个成对条件场景

每题有主输入与对照条件，算 16 个场景而非 32 次已运行。题目不提供预期答案；rubric、历史原文、实验参考结果不交给待测模型。

| ID | 主输入 / 对照输入 | 必须体现的判断 |
|---|---|---|
| SIM16-01 | 60Hz正常 / 120Hz呈现 | 仿真时钟与渲染时钟分开，不加倍推进 |
| SIM16-02 | 短抖动 / 后台停留后恢复 | 有限 backlog 和显式 droppedTime；不单步积分巨大 dt |
| SIM16-03 | 一次点击 / 同事件被两 view 看到 | impulse 恰好一次；持续 force 与 impulse 区分 |
| SIM16-04 | 固定 substeps / 预算自动改变 substeps | compliance、输入、damping 复核；CPU 等待不是 kernel 时间 |
| SIM16-05 | 每步 λ 清零 / 每 iteration 清零 | 原始 XPBD 状态寿命，不能把两者视为等价 |
| SIM16-06 | 同色约束不共享点 / 修改拓扑后共享点 | 检测 write set 冲突，重着色或 gather |
| SIM16-07 | float atomic 支持 / 仅整数 atomic 支持 | feature 粒度与无原子基线；不虚构支持 |
| SIM16-08 | 静态解析碰撞 / 快速碰撞器或旧邻域 | 不承诺无隧穿；失效/连续检测/有界子步策略 |
| SIM16-09 | 尾线程无 barrier / 尾线程后有 workgroup barrier | bounds 与 barrier 参与都正确，不简单 early-return |
| SIM16-10 | 单 workgroup / 多 workgroup 全局更新 | 不把 workgroup barrier 当全局同步；拆 dispatch |
| SIM16-11 | 合法高度场步长 / 提高波速或缩小 dx 后越界 | 针对具体离散模型检查稳定性，拒绝用 clamp 隐藏 |
| SIM16-12 | height和normal同tick / 法线落后一tick | 统一 snapshot；光学效果不证明水面数值正确 |
| SIM16-13 | 一个consumer / 两view加shadow异步消费 | 全消费者完成后回收；2个ping-pong不自动足够 |
| SIM16-14 | 常规变形 / teleport或拓扑变化 | bounds、motion vectors、history和可选AS的代际一致 |
| SIM16-15 | 同queue / 独立queue或不同family | barrier、semaphore、ownership分别判断；async非必快 |
| SIM16-16 | 桌面演示高FPS / 手机限热与不支持选项 | 不外推性能；按数值质量、全帧成本和能力回退 |

### 集合与计量

- 当前实际登记 84；v1.0.15 计划增加 TRAN15 20，但本轮不宣称已登记。
- 若 v1.0.15 全部落地，再加 SIM16 16，则计划集合为 **120**。若尚未落地只能报告实际 registry 的数量与缺失，不能为凑数生成空题。
- 原始 12 题的输入 token 目标与固定 v1.0.8 基线保持不变；SIM16 单独计量，没有新的 30% 目标。
- 既有原题 bytes/hash 冻结，补充新 cohort 不修改旧题来获得 PASS。案例数不是质量指标，新增题必须命中不同的失败模式。
- Live 结果至少保存原始模型输出、实际模型/参数、工具读取轨迹、两仓 SHA、输入输出 hash 与 provider usage；语义人工复核单列，关键词只做 smoke。

---

## 13. 分层验收与设备矩阵

| 层 | 可证明什么 | 不可外推 |
|---|---|---|
| Static / Host contract | 路径、模板、锚点、输入合同、隔离与打包 | 求解正确、真实宿主读取 |
| Numerical Host Unit | 同算法 oracle、约束/时间/边界的数值合同 | GPU race、安全与吞吐 |
| Shader Unit | 实际编译、SPIR-V 验证、布局与 feature 目标 | 运行正确或跨设备性能 |
| Vulkan Integration | 指定实现上的真实 dispatch/draw、回读和图像 | 软件 Vulkan 不能替代移动硬件 |
| Live / Host acceptance | 当前模型/宿主对本候选的分析与读取行为 | 不代表 GPU 代码已执行 |
| Android / Sustained Quality | 实际设备上的视觉序列、帧耗时、热状态、内存 | 单机不证明所有同品牌 GPU；无测量不报功耗 |

建议至少两类实际移动目标：Adreno 与 Mali；其他实现可补覆盖。设备矩阵记录型号、OS/API、GPU、driver、实际 features、workgroup/subgroup、格式、APK/Shader hash、场景配置、温度/热状态与测试时长。没有原子能力或可用 timestamp 的设备用于回退测试，不为了测量改成另一图形 API。

性能实验顺序：同算法 CPU/小规模 oracle → 软件或桌面 Vulkan 正确性 → 目标手机基线 → 单项优化 A/B → 持续负载。substeps、iterations、网格、碰撞与输出质量不一致时，不把结果叫同等负载加速。

候选发布门槛：受影响静态/安全检查无失败；关键数值和语义缺陷已处理；实际执行层有日志；未执行的 Live、宿主、Android、可选软体/原子/async 路径保持 BLOCKED/UNVERIFIED/UNSUPPORTED。无设备也能交付资料和实验工程，但只能声明对应覆盖，不称“移动仿真完整验收”。

---

## 14. 交付物与权限

主仓交付：定向知识增量、稳定锚点、索引/路由更新、版本与 changelog、兼容回退、原始硬约束不退化。新增本版知识不要求新模型、新运行时依赖或付费服务。

测试仓交付：精确计划副本/hash、source ledger、SIM16 prompt/rubric/cohort、数值 fixtures、实验源码与配置、原始失败/成功证据、设备矩阵、最终 release-contract 与包 manifest/hash。

发布包保持原白名单、脏树拒绝、路径/symlink 检查、CRC、per-file SHA 和不覆盖发布规则；最终 clean candidate 双次构建比较字节。若上游发生新合并，重新冻结并重跑受影响验证，不复用旧 SHA 的结果。

本计划不授权提交、推送、合并 main、部署、上架、凭据处理、付费云设备或破坏性 GPU 测试。实际实施按用户当轮授权执行；不删除既有知识、测试或用户文件来通过预算。

## 15. AI 实施提示词

```text
基于最新两个仓库，实施 Vulkan Expert Skill v1.0.16：GPU 仿真与动态几何。
这是既有 Vulkan Skill 的内容增量和可验证实验，不是重建通用物理引擎。

本计划读取的基线：
Skill 4a7ff82372648c4a9df91e76848cbc9c95de51a3，入口1.0.14；
tests f8cadd3614f998b042b77293618323120bcb6d28，实际登记84题。
v1.0.15为前置计划，先核查是否合入。HEAD变化时读取差异，不回退用户成果。

先读AGENTS、git status、SKILL、hard_rules全文、routing-entry、release-contract，
以及既有compute、资源、GPU-driven、motion history和前置透明合成合同。
保留八模块、原模型/宿主配置与触发条件、最小启动、R1-R5、G1-G6、MIT与安全打包。

M0：固定双方SHA、前置依赖、90天来源与数值/图像/性能判据。
M1：C1时钟/输入/暂停/代际；建立CPU oracle和单queue的kernel读写所有权。
M2：C2轻量XPBD绳索/规则布料，解析碰撞，graph coloring或Jacobi+gather基线；
    C3高度场波纹和一次性粒子事件。不得强制浮点atomic/FP16/独立compute queue。
M3：C4发布同tick position/normal/bounds/snapshot，正确上一渲染姿态和全consumer退休；
    可选AS/async按能力和收益启用，不重复前版框架。
M4：复用现有runner/lab，新增SIM16-01..16，保留旧题与原12题token基线。
    v15的20题实际存在后才可统计84+20+16=120；不虚报测试数量或覆盖。

关键约束：
- XPBD α/h²用实际子步h；λ在子步初始化、同子步iteration累积；不承诺无条件稳定。
- workgroup barrier不是dispatch全局barrier；尾线程与barrier参与规则均要满足。
- 两条无浮点原子路径必须存在可行回退；相同seed不等于跨GPU逐位确定性。
- 固定仿真tick独立呈现FPS；暂停不产生无限追赶；共享世界不按view重复更新。
- 高度场是受限波动模型，不冒充完整流体；稳定性取决于实际离散方案。
- snapshot不能在其他view/shadow/AS仍读时覆盖；上一子步不等于上一展示姿态。
- CPU等待延迟不冒充GPU耗时；性能比较固定算法、质量、热状态和输入。
- 图像正确不证明数值正确，Validation clean不证明无race；各层验收独立。

默认runtime文件净增0、实际白名单≤200，已有文件按权威锚点扩展，其他位置短引用。
原始来源、模型答案、rubric、实验与日志放tests仓，待测模型禁止读取答案和判据。
保存失败原文；修改后重新生成结果，不改旧答案冒充模型进步。
未经单独授权不提交推送/合并main/部署/上架/处理凭据/购买设备服务。

最终输出：两仓SHA、范围差异、文件/锚点映射、数值与来源证据、分层测试结果、
Live/宿主/设备状态、运行时manifest/hash、计量、未验证项与回滚方法。
```

---

## 16. 来源索引

### 仓库与前置计划

- **[R1] Skill main ref，本次读取。** https://api.github.com/repos/oahc09/vulkan-rendering-expert-skill/git/ref/heads/main
- **[R2] 固定 Skill 入口。** https://github.com/oahc09/vulkan-rendering-expert-skill/blob/4a7ff82372648c4a9df91e76848cbc9c95de51a3/SKILL.md
- **[R3] 已有 Compute/GPU-driven 工作流。** https://github.com/oahc09/vulkan-rendering-expert-skill/blob/4a7ff82372648c4a9df91e76848cbc9c95de51a3/references/05_workflows/03_compute_workflows/add_compute_pass.md
- **[R4] 固定 tests release-contract。** https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/f8cadd3614f998b042b77293618323120bcb6d28/release-contract.json
- **[R5] 固定 tests README，VIS14/84题与分层验证。** https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/f8cadd3614f998b042b77293618323120bcb6d28/tests/README.md
- **[P15] 当前会话 v1.0.15 计划附件。** 文件名与 SHA-256 见 §2；本轮直接读取挂载文件，作为前置范围，不作为已实现证据。

### 近期实现资料

- **[S1] XPBD-Cloth，固定至 2026-08-27 README 更新。** https://github.com/steampower33/XPBD-Cloth/blob/c7019d35414e75c77ede2c3500a762837bcab6a6/README.md  
  日期证据：https://github.com/steampower33/XPBD-Cloth/commit/c7019d35414e75c77ede2c3500a762837bcab6a6  
  本轮仅 source-read：作者明确 desktop 配置、atomic 顺序与经验调参边界；没有把其数值当手机证据。
- **[S2] Textile-Wave，固定至 2026-10-20 性能/稳定性报告提交。** https://github.com/igor-polev/textile-wave/blob/c9afe32aed360acb6e1c45092ff8b0ab3c096701/README.md  
  日期证据：https://github.com/igor-polev/textile-wave/commit/c9afe32aed360acb6e1c45092ff8b0ab3c096701  
  正文测量日期为10-21；保留UTC提交/正文日期差异。文档披露AI辅助测量与人工审核，本轮未独立复现。
- **[S3] Nebula，固定至 2026-11-06 演示更新合并。** https://github.com/20niship/nebula/blob/13a3f5cbd4d16713f6435b4305b029e7fdef194d/README.md  
  日期证据：https://github.com/20niship/nebula/commit/13a3f5cbd4d16713f6435b4305b029e7fdef194d  
  本轮核查README和提交元数据；未编译、未审计完整solver，不把文中不同求解器的对比当API性能定论。

### 理论与 API 权威

- **[S4] XPBD: Position-Based Simulation of Compliant Constrained Dynamics，2016。** https://matthias-research.github.io/pages/publications/XPBD.pdf  
  本轮查看原文 Algorithm 1、式(17)/(18)，并检查PDF页图；不是90天内新论文。
- **[S5] Small Steps in Physics Simulation，2019。** https://matthias-research.github.io/pages/publications/smallsteps.pdf  
  本轮查看 Algorithm 1、式(4)–(7)和§7精度限制，并检查PDF页图。
- **[S6] 作者 Ten Minute Physics：height-field water、XPBD、soft body 与互动教学入口。** https://matthias-research.github.io/pages/tenMinutePhysics/index.html  
  历史基础；JS/其他后端教学不直接充当Vulkan实现。
- **[S7] Khronos Vulkan Specification — Shaders / Compute execution / Workgroup。** https://docs.vulkan.org/spec/latest/chapters/shaders.html
- **[S8] Khronos Vulkan Specification — Synchronization and Cache Control。** https://docs.vulkan.org/spec/latest/chapters/synchronization.html
- **[S9] VK_EXT_shader_atomic_float 及按存储域/操作区分的 feature。** https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_shader_atomic_float.html  
  feature 原文：https://docs.vulkan.org/refpages/latest/refpages/source/VkPhysicalDeviceShaderAtomicFloatFeaturesEXT.html
- **[S10] Vulkan Guide — Subgroups。** https://docs.vulkan.org/guide/latest/subgroups.html
- **[S11] VkPhysicalDeviceLimits / timestampPeriod 与 timestampComputeAndGraphics。** https://docs.vulkan.org/refpages/latest/refpages/source/VkPhysicalDeviceLimits.html
- **[S12] Android — Optimize with reduced precision。** https://developer.android.com/games/optimize/vulkan-reduced-precision
- **[S13] Arm Frame Advisor 2026.5 — Analyze shader programs。** https://support.arm.com/documentation/102693/2026-5/Analyze-your-frames/Analyze-shader-programs
- **[S14] vkCmdBuildAccelerationStructuresKHR：输入几何、scratch 与 AS 对象的不同访问类型。** https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdBuildAccelerationStructuresKHR.html

规范/官方文档以本次可读取页面为依据；`latest` 是可变链接，实施时在source ledger冻结Registry/Spec/工具版本与内容指纹，不宣称上述链接永久不变。没有日期或只是抓取日期的页面不计入近期新闻数量。

## 17. 本轮交付状态

- 完成：读取两仓main与固定文件、读取v1.0.15计划、90天来源核查、原始论文/规范核对、范围与里程碑设计、计划书生成及结构检查。
- 未验证：目标仓库全量内容一致性、第三方完整源码正确性、任何Shader/实验编译、Vulkan或手机执行、Live模型、宿主、性能/功耗/延迟改善、最终v1.0.16发布包。
- 仓库写入：无；未提交、推送、合并或发布。
- 来源限制：三个近期社区项目仅作为实现/复盘材料；不因README更新、演示或作者报告即认定成熟移动方案。原始算法和API规则另以论文/官方规范为依据。
