# Vulkan Expert Skill v1.0.15 开发计划
## Mobile Transparency, Volumetrics & Gaussian Rendering — 移动端透明、体积与 3DGS 渲染

> 编制日期：2026-11-07。  
> 资料窗口：**2026-08-10—2026-11-07，含首尾 90 个自然日**；截至本次检索可取得的资料。  
> 状态：规划与只读核查。未修改仓库、未提交 PR、未调用被测模型、未编译或运行 Vulkan/Android 实验。  
> 前置边界：本次主仓仍声明 **1.0.13**。v1.0.14 是已制定的前置计划，不能把该计划自动当作已合入、已测试的代码。  
> 核心目标：让 Skill 能设计、诊断和验证玻璃、水体、雨雪、局部雾及 Gaussian 场景，明确**合成语义、精度、顺序、屏幕覆盖成本与可回退路径**。

---

## 1. 版本定位与范围

v1.0.13 解决 Shader、资源加载、GPU-driven 与规模化提交；v1.0.14 计划解决混合光照和时域稳定。v1.0.15 补上另一类瓶颈：**透明内容在正确绘制大量图元之后，仍可能因混合误差、顺序错误、覆盖过大和多层重复着色而失去画质或性能。**

本版不重新建设资源管理器、排序框架、光照系统、神经 SDK 或整套物理仿真。使用四条主线：

| 编号 | 主线 | 必交付内容 | 非强制路径 |
|---|---|---|---|
| C1 | 透明合成与精度 | alpha/颜色/深度合同，排序基线、WBOIT 条件实现、溢出规则、精度定位 | 无限层精确 OIT、强制 fragment interlock |
| C2 | 折射与局部体积 | 单层屏幕空间水/玻璃参考路径、局部雾、雨雪软交界、输入和合成顺序 | 全流体模拟、完整多重散射、任意嵌套介质精确求解 |
| C3 | Vulkan 3DGS | 数据合同、保守投影/剔除、排序/合成、多集合与 mesh 交互、背景 LOD 评估 | 训练平台、动态 4DGS 全量重建、强制 RT/Mesh Shader |
| C4 | 屏幕覆盖预算与退化诊断 | 阶段计时、覆盖/层数分布、误差预算、设备分档、同负载 A/B | 未测得的功耗收益、仅凭点数宣称性能提升 |

“必交付”包括知识、来源、工作流、回退、验收题以及可执行的精简实验材料；不能只添加一段概念说明。是否完成真实模型调用、GPU 运行、手机性能测试须独立报告。

本版主要服务三类业务：

1. 透明卡片、液态玻璃、水庭与天气效果。
2. 多层粒子、局部烟雾、密集半透明场景。
3. 3DGS 内容浏览与移动端混合场景，尤其是大 footprint、远背景重复覆盖和多集合合成问题。

这些是本版设计目标，不是本轮已经实现的效果或性能结论。

---

## 2. 本次核查基线与前置关系

| 对象 | 本次读取值 |
|---|---|
| Skill 仓库 | `oahc09/vulkan-rendering-expert-skill` |
| Skill main | `8d62f861b4ead27699e2ff3d80a1a9f0e72a4968` |
| SKILL 声明版本 | `1.0.13`，last-updated `2026-11-01` |
| 测试仓库 | `oahc09/vulkan-rendering-expert-skill-tests` |
| 测试 main | `9c4cba3a3985b709ccdbec182c79a6988bfc721e` |
| 当前 release-contract 的被测 Skill pin | `d4965f77365b4cd78692e60d048929040ba65c8b`，expected version `1.0.13` |
| 当前 runtime 文件预算 | `max_runtime_files: 200`，`allowed_new_knowledge: []` |
| 当前已登记行为集合 | 前版记录为 64 项；实施时读取最新 registry 与冻结清单复核 |
| v1.0.14 前置计划 | `Vulkan_Expert_Skill_v1.0.14_移动端混合光照与时域画质开发计划_2026-11-02.md` |
| v1.0.14 计划 SHA-256 | `7b2d62b82485712269e394a81cf24b81695841bf68fb3d3d226bbe5de6e261cc` |

依据：[R1–R5、P14]。main 与测试 pin 不同不能直接判定错误；先比较 Git tree、运行报告和变更范围，不能自动继承 PASS。

### 实施前置

- 实施时重新读取两仓 HEAD、AGENTS、工作区差异、release-contract、当前题库和 v1.0.14 状态。
- v1.0.14 已合入时，以其最终 clean commit 为本版增量基线；未合入时可先做独立资料、合同与 host 测试，但必须显式记录依赖，不把 v1.0.13 冒充 v1.0.14。
- 不回退、覆盖用户已完成的修订；不为凑版本直接改 metadata 后宣布升级完成。
- v1.0.14 负责通用光照、深度/运动/曝光和 history；本版只定义透明、体积和 Gaussian 特有输入如何接入。
- v1.0.13 负责通用资源驻留、GPU 排序/剔除基础和任务代际；本版增加 Gaussian 与覆盖预算特有约束，不另起第二套管理系统。

### 不变项

保留八模块、原模型/宿主配置与触发条件、最小启动、hard_rules 全文、routing-entry、按段读取、Evidence Map、Architecture Map、影响面分类、R1–R5、适用范围内 G1–G6、MIT 和失败关闭的安全打包。诊断与实施权限仍分开。

---

## 3. 90 天资料与本版增量

### 3.1 已核查的近期来源

| 日期与性质 | 已核实内容 | 转化为本版任务 | 不得外推 |
|---|---|---|---|
| **2026-09-03，发布公告** | NVIDIA `vk_gaussian_splatting` 2026.2.9 修复 raster/hybrid 多 splat 集合中的材质 ID 选择问题，并有随机透明/光追路径调整。[S1、S2] | 多集合 global ID、可见 surface ID、材质与颜色结果必须使用一致的选择规则；加专门反例 | Windows/Linux Vulkan 参考工具不是 Android 已验收方案；interlock 修法不是所有手机的强制路线 |
| **2026-09-16，维护者发布讨论** | Open3D v0.20 公告介绍 Gaussian 与常规 mesh 的组合、深度输出及离屏渲染。[S3] | 把混合遮挡、模型输入语义和离屏诊断纳入 3DGS 验收 | 本文采用讨论日期，不把 09-24 博文日期替代 release 的精确发布时间；不推断 Android 支持 |
| **2026-09-30，作者代码公告；10-04，论文记录** | Mobile-4DGS 公开移动 WebGL 渲染路径，论文研究静/动态划分、排序复用与紧凑表示。[S4、S5] | 研究“什么状态变化后排序可复用”，为相机、实例、时间和资源 generation 建立失效表 | 公开 WebGL 不等于公开 Android Vulkan 后端；模型专用压缩不能无条件套到任意 PLY；不外推其 FPS |
| **2026-11-06，作者工程文章** | Kitware VTK WebGPU deep framebuffer 保留每像素片段再排序，明确当前 retained-layer 和共享池容量有上限。[S6] | 比较排序、加权近似和有界片段存储；溢出必须可观测，不能把“顺序无关”当作“精确” | WebGPU API 不搬作 Vulkan API；16 层是该实现的选择，不是 Vulkan 上限；不直接宣称移动收益 |

本版的近期增量是**合成正确性、信息保留与移动排序成本**，不是宣称透明算法或 Gaussian Splatting 在这 90 天内首次出现。

### 3.2 长期基础与观察项

- Vulkan Framebuffer、格式能力、feedback-loop、interlock 规范提供 API 合法性依据，不作为近期新特性。[S7–S9]
- NVIDIA 的 OIT 对比样例用于理解算法/容量差异，GPU Gems 的体积渲染章节用于吸收—合成基础；均标记为历史背景。[S10、S11]
- NVIDIA rasterization deep dive 可参考投影、排序和数据流；性能数字、近裁面策略和剔除近似必须独立评估。[S12]
- X 仅作发现作者或演示线索的渠道；本轮未采用不可核验帖子作为硬规则，不补造发布日期、点赞数或源码可用性。
- 本轮 Open3D 官方 09-24 博文正文两次读取超时，使用可读取的官方维护者 09-16 发布讨论；未从超时正文推导额外细节。
- Mobile-4DGS README 含链接/旧引用混杂，实施时按固定 revision 核对真实 renderer 路径。README 关于 ideas 的表述不代替各代码、模型和数据集 LICENSE。

### 3.3 来源登记格式

在测试仓库保存：`source_id / canonical_url / event_date / published_at / updated_at / checked_at / commit-or-tag-or-blob / claim / destination_anchor / evidence_level / unverified_scope`。

对于动态网页，保留合理范围的摘要、内容 hash 和日期；不镜像大段版权资料。规范和第三方工具在实施时固定 revision。Issue 或论文中的结论只按其证据强度归因。

---

## 4. C1：透明合成、排序与混合精度

### C1.1 统一合成合同

扩展现有 `render_target_model.md#color-output-contract`，避免重新维护第二套颜色规则。至少记录：

- shader 输出是 straight 还是 premultiplied；RGB 与 alpha 的含义。
- 输入、工作、输出的颜色空间；乘 alpha 与解码/编码的顺序。
- 每个 attachment 的 format、blend factors、blendOp、alpha factors 和写掩码。
- opaque depth、透明 depth test/write、MSAA/sample coverage、可见性与透明度的区别。
- 最终 Android `compositeAlpha` 另由原输出合同管理，不能把 offscreen alpha 自动当宿主透明度。

线性、premultiplied source-over 的数值参考：

```text
Cout = Csrc + (1 - Asrc) * Cdst
Aout = Asrc + (1 - Asrc) * Adst
```

其中 Csrc 已乘 Asrc；这不是任何 blend 配置都可使用的无条件公式。front-to-back 透射率累积需要另一组状态：

```text
C = 0, T = 1
for each sample in front-to-back order:
    C += T * alpha * linearColor
    T *= 1 - alpha
finalColor = C + T * background
finalAlpha = 1 - T
```

实际 render target 是存 opacity 还是 transmittance 必须写清；不能把两种 alpha 语义混用。

### C1.2 精度定位顺序

建立小型 CPU FP64 数值 oracle，另有明确格式/舍入假设的存储模拟；它用于比较算法语义，不假装逐位模拟所有 GPU blend 实现。

按以下顺序隔离误差：

1. 原输入量化、SH/纹理解码、alpha 阈值。
2. straight/premultiplied、颜色编码、blend factors。
3. 排序、遮挡和片段遗漏。
4. 中间 attachment 精度、逐层存储量化、范围溢出。
5. tone mapping、输出编码与 Android 合成。

比较 RGBA8 与受支持的 FP16 等中间目标；FP16 不是零误差证明，也不是免费带宽优化。格式必须分别满足实际 attachment/blend/sample/storage 用途；不能由“可以创建 image”推断所有访问都支持。[S7]

### C1.3 三档透明算法

| 路径 | 本版要求 | 边界 |
|---|---|---|
| 排序 alpha blend | 默认参考基线；显式排序键、稳定 ID、深度约定 | 物体/primitive 中心排序不能精确处理所有交叉片段 |
| Weighted Blended OIT | 条件可执行小样例；accumulation/revealage、清除值、resolve、精度和格式检查完整 | 是近似；高 opacity、层数和深度交错需误差验收，不替代折射求解 |
| 有界片段列表/少层 depth peeling | 作为小分辨率精度对照和高预算条件路径 | 容量、带宽、原子和排序成本显式；不做无限层保证 |

没有 `independentBlend` 或所需 MRT blend 格式时，选择可行的多 pass 或排序回退，不强制扩展。[S7] interlock 可以保护每像素数据访问，但不自动给出几何深度排序；不要求所有移动设备支持。[S8]

OIT pool、每像素保留层数及 resolve 上限必须有溢出计数、诊断视图与确定性处理。可以选择拒绝该质量档、已声明 tail approximation 或预算回退；不能静默漏片段后给 PASS。[S6、S10]

### C1.4 最小对照

- 两张 alpha=0.5 的红/蓝矩形，黑背景、关闭光照与 tone mapping：在线性空间，红前蓝后为 `(0.5,0,0.25)`，反序为 `(0.25,0,0.5)`，合成 alpha 都为 0.75。改变深度应改变结果；这是公式推导的测试值，不是本次 GPU 输出。
- 多层低 alpha 在白/黑背景下累积，分离输入量化与附件存储误差。
- 相交薄片、接近不透明层和强亮度范围，比较排序、WBOIT 与有限精度参考。
- 故意超过小样例容量，验证明确失败/退化和计数，而不是只检查图像存在。

**交付：**合成合同、精度排查树、三档取舍、oracle 与负向测试。

---

## 5. C2：水体、玻璃、天气与局部体积

### C2.1 可控的屏幕空间折射

必交付一条单层/主导折射表面的参考路径，复用 v1.0.14 光照与反射回退：

```text
Opaque scene color + depth 完成
→ 保存稳定的被采样场景颜色/深度
→ 水/玻璃的 normal、厚度/吸收参数
→ 有边界的屏幕空间折射 + 反射贡献
→ 输出到另一目标或合法的独立 pass
→ 后续透明/UI 合成
```

记录屏外、遮挡错误、薄物体、缺失背面厚度和多层折射的处理。不得把背景 UV 偏移声称为精确光学；不能把 opaque-only scene color 当成已包含所有透明物体。

厚度由适用的几何或同一坐标系的线性深度估计；原始非线性 depth 差不是通用物理厚度。Fresnel、吸收、反射、颜色转换的责任各有位置，避免透明 alpha 与吸收反复衰减。

默认使用分离的 scene-color 输入与输出，或显式 ping-pong。仅把 image 改成 GENERAL 不解决同时采样/写入的 feedback hazard。采用 feedback-loop 扩展时必须另证 feature、usage、pipeline 状态、layout、访问和同步合同，不能视为通用替代方案。[S9]

### C2.2 局部体积基线

必交付有界局部均匀/程序化密度雾体，不要求云海、完整流体或多重散射系统：

- 有限体积范围、opaque depth 截止、步长、最小透射率和最大采样数。
- 定义消光系数与世界单位；步长变化时按透射/吸收模型重新积分，不能让 alpha 与采样次数机械成正比。
- 基础关系 `T = exp(-sigma_t * distance)`；光源/发光与散射近似另有语义说明。
- 输出散射/颜色贡献与 transmittance，说明如何与背景、透明表面在深度上组合。
- 同一 volume contribution 不能对前景和背景重复应用；多个互穿介质无法由任意固定 pass 顺序保证正确，超出基线时必须选择分段积分或明确近似。

早停是带误差预算的算法行为，不能把高亮背景中的可见透射尾部无条件截断。[S11]

低分辨率体积与深度引导上采样作为性能档；检查轮廓漏光和细小前景。v1.0.14 history 仅复用合同，不重写其系统。

### C2.3 雨雪与软交界

粒子模拟/批处理继续复用 v1.0.13，本版只补渲染：与不透明深度的软交界、裁剪/混合分类、透明层顺序、粒子 alpha/覆盖、远近尺度和亚像素闪烁。

每种天气效果明确 history、motion vectors 和可选 reactive 信息是否有可靠来源；没有真实运动语义时，不向重投影链提供编造的零向量。模糊后的稳定不能掩盖拖影。

### C2.4 本版效果边界

必做精简水/玻璃表面与局部雾对照；雨雪复用现有粒子渲染。大规模流体、完整水焦散求解、任意多层介质路径追踪、天气物理和光学级玻璃建模不属于本版隐藏任务。

**交付：**折射/局部体积/天气合同，读写分离工作流，混合场景的近似边界与检查清单。

---

## 6. C3：原生 Vulkan 3DGS 与移动端成本控制

### C3.1 数据合同与最低参考资产

输入字段至少覆盖：position、scale/covariance、rotation、opacity、SH/颜色、坐标约定、单位、稳定 ID 和资源 generation。

对每个导入 profile 明确：scale 是线性还是 log、opacity 是概率还是 logit、quaternion 顺序、SH 排列和系数解释。PLY 是容器，不保证所有生成器使用同一语义；字段名相同也不允许无验证套转换。

最小必交付为原创合成 Gaussian 生成器和一个写清字段合同的 PLY profile。SPZ/glTF/4D 压缩格式是条件适配，不把训练代码/模型文件塞入 Skill 包。

训练所得 radiance、带光照颜色和可重照明材质分开。普通 3DGS 没有可靠法线/BRDF 时，不因接入 v1.0.14 就重复加光或承诺物理正确重照明。

### C3.2 基础 GPU 链路

```text
加载/验证输入 → 规范化字段 → 复用上传与驻留
→ 计算视空间深度、投影椭圆和合法范围
→ 可见列表/深度键 → 排序
→ instance/indirect 绘制 + 明确的 alpha 合成
→ 与 mesh 深度及颜色合成
→ 诊断输出/回收
```

基础路线采用已有 vertex/instance + raster blend；GPU radix 排序复用 v1.0.13。小规模 CPU 排序是 correctness/回退对照，不承诺它在大模型或每台手机更快。Compute 预投影属于候选，不能把“全部改 Compute”写成默认优化。

Mesh Shader、Ray Tracing、fragment interlock、独立 compute queue 都不是基础功能的必需能力。具体 profile 继续遵守项目最低 Vulkan 与 feature 门槛。

### C3.3 投影、剔除与 footprint

- covariance 必须有限并满足所选表示的有效性；零/负/NaN 数据在输入处明确处理。
- near-plane、极小 z、视口边缘和超大椭圆必须有健壮路径，不通过任意缩小所有点遮掩问题。
- Gaussian 截断边界与 alpha cutoff 是画质约定；剔除需要考虑 footprint，而不是只检查中心是否在视锥内。
- AA 引起的 covariance 扩展与 opacity 补偿要作为配对策略验证，不把独立改一个参数视为等价。
- 显式输出投影大小分桶、clipped quad 面积、估计椭圆面积与 tile 覆盖；这些是不同量，不能互换。[S12]

### C3.4 排序复用与多集合

相机、实例 transform、时间、Gaussian 参数、LOD、可见集合、索引生成方式任一相关输入变化，都必须判断缓存是否失效。

Mobile-4DGS 的排序证书依赖其特定静/动态表示与有效条件；本版不照搬“固定 N 帧才排一次”。仅在可证明前提成立时复用，否则重排；可选的误差容忍模式必须单列。[S4、S5]

对多个 splat set 维护稳定 `(setID, localID, generation)` 映射。颜色累积、picked ID、depth proxy、材质 ID 与调试输出的选择规则一致；整数 ID attachment 不会因为另一个颜色 attachment 开了 blend 就自动得到正确 ID。以 NVIDIA 2026.2.9 修复为反例参考，不要求复制其全部实现。[S1、S2]

与 mesh 共存时先明确 depth 的语义。Gaussian 的中心/某阈值深度不是普通硬表面深度；不能直接沿用 opaque Hi-Z 剔除证明，不可用一个任意 splat 深度遮掉仍有透射的内容。

### C3.5 背景专用简化与质量预算

在内容证据支持时，优先评估远背景高重叠层的合并、LOD 或预合成；保留前景、轮廓、运动和有视差结构。距离远不是唯一判断依据。

必须同时比较：原点数、实际覆盖、排序成本、颜色/透射误差、相机移动序列和显存峰值。减少点数而扩大剩余点 footprint 可能没有收益；本版不把简单参数平均作为普适正确合并。

本次不继承历史特定场景的百分比作为新结果；既有用户案例可作为授权输入，重新固定资源 hash、相机与环境后再测。

**交付：**Gaussian 数据/合成/缓存合同，原生 Vulkan 最小参考链路，多集合反例，背景简化的证据门槛。

---

## 7. C4：屏幕覆盖预算、质量分档与性能证据

### C4.1 先量真正的工作

| 指标 | 目的 | 证据边界 |
|---|---|---|
| 可见 primitive / Gaussian 数 | 规模及剔除效果 | 不等于着色成本 |
| clipped quad/ellipse footprint 总量 | 定位大点与覆盖集中区域 | 计算估计不是硬件 fragment invocation |
| 唯一覆盖像素、层数分布 | 找到屏幕热点、尾部重叠 | 采集方式和原子开销需记录 |
| 投影/排序/光栅/resolve 各阶段 GPU 时间 | 判断优化主攻方向 | queue 与 timestamp 能力检查，避免相加重叠区间伪造帧时间 |
| 上传、临时列表、OIT pool 与中间图峰值 | 容量和预算 | include 新旧代际并存，不只记录最终资产大小 |
| 线性颜色/alpha 误差与运动稳定性 | 控制近似和精度损失 | 单帧 PSNR 不足以保证无闪烁/排序 pop |
| 持续帧耗时和热状态 | 手机可持续性 | 无功耗工具不宣称节电；插帧计数独立 |

默认先做低侵入计时与计算估计，必要时启用重诊断。带原子计数的调试路径会改变性能，不拿它的帧时间代表生产路径。硬件 counter 不可用时明确 UNMEASURED。

### C4.2 分档与回退

| 档位 | 候选路径 | 启用条件 |
|---|---|---|
| 基础 | 排序 blend、单层屏幕空间折射、有限步长局部雾、标准 instanced splats | 项目原最低能力，数据/顺序/资源合同成立 |
| 平衡 | 受支持的较高精度附件、WBOIT、低分辨率局部体积、保守背景 LOD | 格式/内存/误差预算和 A/B 证据通过 |
| 增强 | 有界 per-pixel 存储、条件排序复用、特定 tile/interlock/RT 对照 | 独立 feature/driver 路径；额外内存和稳定性可接受 |

基础档不是固定 RGBA8，也不保证所有材质无误差。允许根据内容选择更高精度；所有设备分档都以能力和测量为依据，不按 GPU 品牌硬编码。

### C4.3 必须拦截的错误建议

- “少一半点就会快一半。”
- “排序无关意味着图像等于精确 alpha blend。”
- “RGBA8 和 FP16 应逐位相同，否则驱动错误。”
- “只要 interlock 就自然是前到后排序。”
- “帧之间相机没动就能复用动态场景的排序。”
- “当前透明度接近 1 就可在所有高亮背景中无误差早停。”
- “Compute/mesh/RT 比固定管线现代，所以自动更快。”
- “WebGL/桌面 Vulkan 演示已经证明 Android 原生路径通过。”

---

## 8. Vulkan 访问与同步检查表

本表是实现时的审查方向，不代替固定规范对具体 API/queue/format 的核对。

| Producer → Consumer | 资源 | 需要明确的依赖 |
|---|---|---|
| opaque color attachment write → 折射 fragment sample | 稳定 scene-color snapshot | 实际 COLOR_ATTACHMENT_OUTPUT 写 → FRAGMENT_SHADER 采样读；合法布局；独立输出避免未声明 feedback |
| opaque depth write → 雾/粒子/GS 遮挡读 | depth 或线性深度副本 | 实际 EARLY/LATE depth-stencil 写 → 所选 shader 读取；aspect、resolve 与深度表示一致 |
| compute 生成 key/list → 后续排序 compute | SSBO | compute write → compute read/write；不同 dispatch 的边界和 per-pass scratch 不复用过早 |
| compute 生成绘制参数 → indirect read | indirect/count buffer | COMPUTE_SHADER/SHADER_WRITE → DRAW_INDIRECT/INDIRECT_COMMAND_READ；按实际范围处理 |
| compute 输出属性 → vertex/fragment 使用 | 属性/index SSBO 或 vertex buffer | consumer 取决于 shader SSBO read 或固定 vertex fetch，不能只写 indirect barrier |
| WBOIT accumulation/revealage → resolve | 多 attachment | attachment 写 → fragment/compute 实际读；format、清除值、独立 blend 或多 pass 路径一致 |
| 片段列表存储写/原子 → resolve | storage/head/counter | shader write → resolve read；每帧 reset、容量、溢出和回收独立可证 |
| history → 当前透明/体积输出 | history images/metadata | 复用 v1.0.14 generation/有效性合同，多视图禁止交叉使用 |

跨 VkQueue 需要实际的 semaphore 依赖；是否 ownership transfer 由 queue family、sharing mode 和路径决定，不是看到两条 queue 就一律转移。资源退休须覆盖所有消费者；布局转换不能替代正确合成公式。

---

## 9. 文件落点与结构优化

### 9.1 保持 8 模块，运行时文件净增 0

优先在已有文件新增短的权威章节和稳定锚点。下列锚点是本版建议，不是宣称当前已存在。

| 现有文件（相对 references/） | 建议权威章节 / 内容 |
|---|---|
| `02_core_mental_model/render_target_model.md` | `#transparent-composition-contract`：复用颜色合同，增加 opacity/transmittance 与表示边界 |
| `02_core_mental_model/engine_architecture.md` | `#transparent-gaussian-budget-decision`：方案选择与失效条件，只引用详细卡片 |
| `03_api_manual/06_pipeline/graphics_pipeline.md` | `#blend-format-capability`：blend/format/MSAA/independentBlend 能力与限制 |
| `03_api_manual/07_rendering/render_target_layout.md` | `#refraction-read-write-boundary`：独立读写、feedback-loop 与同步 |
| `03_api_manual/04_buffer_image_memory/image.md` | `#transparent-target-precision`：格式用途、精度和资源代价 |
| `05_workflows/02_render_pass_effects/add_postprocess_pass.md` | `#transparency-resolve` 与 `#local-volume-composite`：OIT resolve、局部体积与合成责任 |
| `05_workflows/02_render_pass_effects/add_texture_sampling_pass.md` | `#screen-space-refraction`：水/玻璃场景采样链 |
| `05_workflows/03_compute_workflows/add_compute_pass.md` | `#gaussian-preproject-sort`：Gaussian 数据验证、投影/排序、代际与回退 |
| `05_workflows/03_compute_workflows/compute_to_graphics_sync.md` | `#gaussian-consumer-dependencies`：间接参数与属性消费者分别同步 |
| `05_workflows/07_optimization/optimize_mobile_bandwidth.md` | `#coverage-budget`：coverage/layers/precision 的成本控制与 A/B |
| `04_debug_playbooks/06_performance_symptoms/bandwidth_fullscreen_cost.md` | 高覆盖、排序与混合精度的分流定位 |
| `06_cases/06_performance/case_performance.md` | 覆盖不降/精度差异等合成实验案例，显式标记 synthetic |
| `06_cases/02_descriptor_pipeline/case_descriptor_pipeline.md` | 多 splat-set 材质 ID 选择的公开案例与本地复现状态 |
| `07_integration_pack/task_routing_rules.md` | 命中透明/折射/体积/Gaussian 后定向读取锚点，不改变旧触发逻辑 |
| 各索引、模块摘要、changelog | 按实际结构同步，不复制全部规则 |

M0 必须核对这些路径在最终前置基线仍存在；同义改名按实际仓库定位，不为套计划恢复旧目录。

### 9.2 不以聚合文件代替可检索性

- 所有新增章节具有“适用/不适用、输入、输出、能力、同步/生命周期、回退、验证”最小闭包。
- 段落独立读取后不能丢失算法近似性质或前置能力；跨节必须有明确引用。
- 原规则不因“轻量化”删除；原模型路由和条件不变，新关键词只增量路由。
- 新闻原文、图表、模型回答、实验资源、日志和测试脚本留测试仓库或其受控产物，不进运行时包。
- 文件数、总包字节、实际读取段落/token 分开记录。文件净增 0 不代表上下文零增长。
- 单任务读取预算相对最终 v1.0.14 基线记录；不设第二次无依据的 30% 降幅目标。

### 9.3 发布预算

保留项目 `max_runtime_files: 200` 内部预算，以实际白名单 ZIP 为准，不以整个 Git 仓库跟踪数代替。先保留必要知识，再通过消除重复摘要和合理锚点组织控制大小；不能删核心约束或历史证据来凑数。平台限制若变化，单独核实，不能默改内部契约。

---

## 10. 可执行任务与里程碑

| ID | 里程碑 | 主要工作 | 交付与退出条件 |
|---|---|---|---|
| M0 | 基线、来源、合同 | 核对 v14 状态与差异；固定 sources；确认路径/版本/工具/测试；登记旧内容与增量 | 基线可复现；本版范围不重复；20 题与数值 oracle 判据先冻结 |
| M1 | C1 合成正确性 | 写合成/精度/排序合同；实现 CPU oracle、小型 Vulkan 排序 blend 与 WBOIT 条件样例 | 正反深度、低 alpha、多层、格式不支持与溢出测试具有明确判定 |
| M2 | C2 效果连接 | 单层折射、局部雾、软粒子、scene-color 读写边界和 history 接入 | 可比较离屏序列；屏外/多层/不支持情形有明确回退；无伪物理声明 |
| M3 | C3 3DGS | 合成生成器/PLY profile、投影排序、instancing、多集合、覆盖与背景简化 | 原生最小路径与 CPU 对照对应；输入非法/相机突变/近裁面/代际测试通过可执行层 |
| M4 | C4 集成与发布 | 联合场景、覆盖预算、设备 A/B、Live/宿主及所有分层回归、确定性包 | 最终 SHA 证据一致；未运行层明确；现有安全/索引/能力不退化 |

依赖关系：M0 → M1；M1 后 C2 和 C3 可在不冲突文件/接口上并行；M4 等待全部合同接入。不要让两个 Agent 同时改同一聚合文件，统一由一位集成者合并增量。

建议职责分为“合成/精度”“效果/体积”“Gaussian/成本”“测试/集成”四条工作线；不是要求宿主必须支持多 Agent。单 Agent 按相同依赖执行即可。

所有技术主线都需完成知识与验收材料；可选硬件路径无设备时不伪填 PASS，也不以此阻止标准路径的文档和可执行检查。

---

## 11. 统一实验：Transparent Scene Lab

复用测试仓库 Engine Scale Lab 的资源、计时和输出设施，增加透明场景模式，而非创建第二个通用引擎。

### 11.1 三个精简场景

| 场景 | 内容 | 主要验证 |
|---|---|---|
| Glass & Weather | 两层/交叉薄片、单层水/玻璃、opaque 深度物体、低密度雨雪、局部雾 | alpha/折射/体积次序、精度、屏外、软交界、history |
| Gaussian Coverage | 原创合成 splat，点数与 footprint 可独立调节，远背景高重叠区 | 数量与覆盖解耦、sort/raster 成本、RGBA8/FP16 误差、背景 LOD |
| Mixed Sets | 至少两个材质/变换不同的 splat set + opaque mesh + 第二视图 | global ID、遮挡、排序缓存、资源 generation、单输出销毁 |

每场景固定 seed、相机路径、灯光/曝光、分辨率、算法选项、资源 hash。默认原创合成数据；外部资产仅在明确许可和授权后使用，不下载私有内容或捆绑训练模型。

### 11.2 压力配置

- Gaussian 数量建议 10,000 / 100,000 / 1,000,000；层数建议 2 / 8 / 32 / 128。
- 点数、尺寸分布、重叠深度和屏幕区域至少有可独立控制的两个轴。
- 高档是实验负载，不是所有手机必须达到的 FPS 承诺；超过内存/时间/设备安全预算应中止并保留结果。
- 大分辨率小列表和小分辨率深列表分开，防止将 OIT 故意爆量变成危险压力测试。
- 采样不足、容量不足、格式不支持和内存分配失败都要能返回明确状态，不发生越界或无限等待。

### 11.3 CPU 与 Shader 级对照

必含：source-over 双层数值、透射率累积、片段排序和并列键、Gaussian 正定/有限值检查、边界 footprint、错误 profile 拒绝、缓存失效矩阵、索引容量上限。

Shader 编译/验证、host 单测和 real Vulkan 运行分开。CPU 模拟 pass 顺序不算 GPU 画面测试；软件 Vulkan 不证明 Adreno/Mali 性能。

### 11.4 误差与性能验收

M0 先固定每个 fixture 的颜色/alpha 容差、允许近似、排序 pop/边缘测试方法。阈值按数据与格式决定，不能看见失败输出后提高阈值让它过关。

保存线性离屏颜色、alpha/transmittance、depth proxy、set ID、错误热图及至少一段移动相机序列。反射/折射近似采用显式参考配置，不以艺术观感替代数值和序列证据。

性能记录 cold/warm、CPU 与 GPU 阶段耗时、p50/p95/p99、内存峰值、实际分辨率与热状态。比较时保持可见内容与质量档一致；删对象、降低输入层数或改曝光的实验单列，不能混为等质量加速。

---

## 12. TRAN15 行为验收：新增 20 个场景

每题提供 A/B 条件，以相反条件是否改变结论验证推理，不用固定中文句子或简单关键词代替正确性。rubric、oracle、历史答案不得进入待测模型上下文。

| ID | 成对条件 | 必须体现的判断 |
|---|---|---|
| TRAN15-01 | straight 与 premultiplied 输入 | RGB/alpha 因子与转换顺序分别正确，不双乘 alpha |
| TRAN15-02 | 红前蓝后与蓝前红后 | 区分深度顺序，使用固定线性 oracle，而不是同一混色结果 |
| TRAN15-03 | 少层与大量低 alpha 层，RGBA8/FP16 | 隔离精度、输入量化和排序，不直接归咎驱动 |
| TRAN15-04 | independentBlend/格式可用与不可用 | 能力分支或多 pass/排序回退，不编造必需支持 |
| TRAN15-05 | OIT 容量内与超限 | 溢出可观测、确定性处理；WBOIT/有界列表均不宣称无条件精确 |
| TRAN15-06 | 折射读独立 snapshot 与读写同一 subresource | 默认分离；GENERAL 或加任意 barrier 不自动合法 |
| TRAN15-07 | 原始 depth 与正确线性/世界深度 | 厚度坐标统一，正/反 Z 与屏外回退明确 |
| TRAN15-08 | 相同步长与步长减半的同一雾体 | 吸收随距离积分，不因采样次数加倍改变目标介质 |
| TRAN15-09 | 雾位于透明表面前与后/穿越表面 | 不用万能固定合成顺序；分段或明确近似 |
| TRAN15-10 | 静态粒子、运动粒子与相机突变 | history/motion/软交界路径有条件，不伪造 motion vectors |
| TRAN15-11 | 两种 PLY scale/opacity/SH 编码 | 选择明确 profile，非法/未知字段不静默猜测 |
| TRAN15-12 | 中心屏外但椭圆覆盖屏内，及近裁面 | footprint-aware 保守处理，避免 NaN/巨大无界分配 |
| TRAN15-13 | 单集合与两个不同材质/transform 集合 | ID/深度代理/材质一致，不能仅凭颜色 blend 判 ID 正确 |
| TRAN15-14 | 相机静止但动态 Gaussian 移动，及完全静态 | 缓存依据完整状态，不能固定帧间隔无条件复用 |
| TRAN15-15 | 减少点数且覆盖下降，与点数下降但 footprint 上升 | 以实际工作/画质判断，不用点数直接预测提速 |
| TRAN15-16 | 远背景低视差与前景/轮廓/动态区域 | 背景合并有边界、多视点误差验证，不普遍平均参数 |
| TRAN15-17 | Compute 只写 indirect，另写 vertex SSBO | 区分 DRAW_INDIRECT 与真正 shader/vertex 消费者同步 |
| TRAN15-18 | interlock 可用与不可用 | 保护数据不等于深度排序；基础功能不强制 interlock |
| TRAN15-19 | 主视图变更与第二视图/实例独立变化 | 独立 sort/history/generation，不把一个 Surface 失效升级为全部重建 |
| TRAN15-20 | 相同质量/持续热状态与删内容/冷机快测 | 只给可比 A/B 结论，渲染/呈现/生成帧和功耗证据分开 |

### 题库数量不能提前宣告

本次实际核查仍是 v1.0.13 的 64 项。v1.0.14 计划增加 VIS14 20 项，本版再增加 TRAN15 20 项；**在前置题库实际登记完成后，规划总数才是 104**。若实施时 v14 尚未落地，报告 actual registry 与 missing cohort，不伪称已有 84 或 104 个已执行测试。

旧 prompts、rubric 和历史结果保留；更新候选版本的规则不意味着重写旧失败输出。新 cohort 独立计分。原 v1.0.8 的原始 12 题 input-token 对比基线不变，不以 104 题中位数替换。

---

## 13. 证据分层与设备矩阵

| 层 | 本版证明什么 | 不证明什么 |
|---|---|---|
| Static | 结构、索引、符号、锚点、来源、包清单、安全契约 | 算法语义全部正确或模型已理解 |
| host_unit | 合成/排序/容量/失效的 CPU 合同 | GPU 并发、移动驱动或真实画面 |
| shader_unit | 实际编译器/validator 对特定 shader 产物的结果 | pipeline 创建及最终效果 |
| vulkan_integration | 指定实现的真实 draw/dispatch 与离屏对照 | 所有手机兼容或持续性能 |
| Live | 授权模型读取候选 Skill 后的原始答案与轨迹 | 设备运行结果；关键词烟测也不是语义全部通过 |
| Host | 实际宿主发现、最小启动、路由与段落读取 | 其他宿主自动受测 |
| mobile_visual | 指定 Adreno/Mali 等设备上的图像、顺序、回收与运行结果 | 未测设备或所有质量档 |
| mobile_performance | 同设备、同场景、同质量、匹配热状态的阶段/帧时间与内存 | 未有测量工具的带宽、功耗或普遍加速比例 |
| Package | 干净候选白名单、CRC/hash、重复打包一致 | 已上架审核或运行正确 |

设备建议至少覆盖一台 Adreno 和一台 Mali 的标准 raster 路径；确切设备、OS、driver、API/features 与工具版本在执行时记录。可选 interlock/MRT/高精度等路径各自说明能力。没有某能力的设备是回退验证机会，不应强行启用。

不得自动购买云设备、扫描凭据、改变系统驱动、执行破坏性故障注入或上传私有 capture。无授权 wrapper/宿主/设备时对应层为 BLOCKED/UNVERIFIED，能够执行的检查照常进行。

---

## 14. 发布与 Definition of Done

### 必需交付

1. 四条主线都有权威章节、来源、调用链、失败/回退和可验证任务，不是只有导航或名称。
2. 先冻结 fixture/rubric，再生成输出；失败输出原样保存，新 run 使用新目录。
3. 相同规则在摘要、独立锚点、示例和相关 API 卡中一致，旧最小启动与触发条件保留。
4. 参考实验具备源代码、构建说明、固定工具版本和实际执行记录；未执行部分明确，不用空桩冒充完整链路。
5. 不同测试层独立统计。各硬件增强路径和性能主张只有实际证据才标 PASS。
6. 原始精度基线、未知格式、越界容量、多集合和错误同步都能触发预定断言/拒绝，不只测试正常图像。
7. 运行时知识净增目标 0，实际包 ≤200，保留全部安全检查；同源两次打包 hash 相同。
8. 最终报告关联 Skill SHA、tests SHA、tree、实验源码/资源/编译产物 hash、工具/设备/模型元数据、原始输出和包 manifest。

### 允许发布声明的范围

- 只通过文档/静态测试：可以称“知识与结构候选”，不能称“手机性能版通过”。
- 软件 Vulkan 正确：可以报告其实际实现上的正确性，不外推移动 GPU。
- Live 未运行：不能拿历史 snapshot 或人工补全答案标“专家行为已通过”。
- v1.0.14 输入或宿主契约变化后，受影响的证据需要重新生成，不沿用旧指纹。
- main 合并、release、Agensi/其他市场上传、部署和权限操作均需本次实施的明确授权；本计划不自动授权。

### 回滚

保持标准排序/旧效果/原资源路径的可切换边界；新 shader、pipeline、OIT pool 与 GS 数据使用既有 generation/retirement。回滚关闭新增 pass/特性，恢复原流程；已提交 GPU 任务仍须安全完成，不能立即释放所有新对象。

---

## 15. 可直接交给 Agent 的实施提示词

```text
你负责 Vulkan Rendering Expert Skill v1.0.15：
Mobile Transparency, Volumetrics & Gaussian Rendering。

本任务是增强技能内容、工作流、回退与可验证实验，不是另建完整渲染引擎。
主仓 oahc09/vulkan-rendering-expert-skill；独立测试仓
 oahc09/vulkan-rendering-expert-skill-tests。

计划读取基线：
Skill main 8d62f861b4ead27699e2ff3d80a1a9f0e72a4968，声明1.0.13；
tests main 9c4cba3a3985b709ccdbec182c79a6988bfc721e。
v1.0.14为前置计划，不是这份计划读取时已确认的main版本。
先重新核对AGENTS、HEAD、工作区差异、v14实现、release-contract和题库。
若HEAD不同先读差异，保留用户成果，不回退或覆盖；明确最终前置SHA。

顺序 M0→M1→M2/M3→M4：
M0 固定来源/工具/基线、权威章节、fixture与20个TRAN15成对判据。
M1 C1：alpha/颜色/深度/精度合同，排序blend、条件WBOIT，容量溢出，
        CPU FP64语义oracle与Vulkan离屏对照。CPUoracle不是硬件逐位模拟。
M2 C2：单层屏幕空间水/玻璃、有限局部雾、雨雪软交界；明确读写分离、
        深度/厚度、体积透射、混合顺序和history边界。不扩成流体模拟。
M3 C3：原创合成GS与明确PLY profile、投影/footprint、排序、多集合ID、
        mesh交互和背景LOD；复用v13GPU-driven和v14颜色/history。
        WebGL/桌面样例不算Android验证；不默认全Compute、RT或Mesh Shader。
M4 C4：复用Engine Scale Lab加入Transparent Scene Lab；测coverage、层数、
        阶段时间、内存、误差与动态序列；做分层回归和确定性包验收。

必须保留八模块、原模型/宿主配置、触发条件、hard_rules、routing-entry、
按段读取、Evidence/Architecture Map、影响面、R1–R5与适用范围G1–G6。
运行时知识净增0，actual whitelist package≤200。新增内容用稳定锚点；
原始文章、模型输出、测试脚本和资产留测试仓，不进入Skill包。

禁止把WBOIT说成普遍精确，禁止静默OIT溢出，禁止把GENERAL当feedback修复；
interlock不等于深度排序，FP16不等于无误差，减少点数不等于减少覆盖。
不同queue靠真实依赖衔接；indirect参数和shader属性的consumer分别同步。

保留已有64题；确认VIS14实际登记后再加TRAN15-01..20。
完整前置成立才预计104题，不把计划题数当已执行数量。
旧题hash和原12题token对照基线不变，新cohort单独计量。
模型输入禁止访问rubric、oracle答案和历史报告；失败输出不可手工改成通过。

分别运行可用的Static/host_unit/shader_unit/Vulkan/Live/Host/mobile层。
缺授权wrapper或设备时对应BLOCKED/UNVERIFIED，不造GPU计数、FPS或节电比例。
不下载私有资源、修改驱动/权限/凭据，不擅自花费云设备或模型费用。

交付固定基线、按文件增量、来源和合同映射、实验复现说明、20题注册、
各层原始结果、未知项、实际读取量和包manifest/hash、回滚路径。
提交、推送、PR、合main、上架仅按本次明确授权执行；计划本身不构成授权。
```

---

## 16. 核查来源

### 仓库与前置文档

- [R1] Skill 固定入口，读取日期 2026-11-07：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/8d62f861b4ead27699e2ff3d80a1a9f0e72a4968/SKILL.md
- [R2] Skill 固定文件树，路径核对：
  https://github.com/oahc09/vulkan-rendering-expert-skill/tree/8d62f861b4ead27699e2ff3d80a1a9f0e72a4968/references
- [R3] 测试发布契约：
  https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/9c4cba3a3985b709ccdbec182c79a6988bfc721e/release-contract.json
- [R4] 已有颜色合同：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/8d62f861b4ead27699e2ff3d80a1a9f0e72a4968/references/02_core_mental_model/render_target_model.md#color-output-contract
- [R5] 既有测试说明与64题历史口径：
  https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/9c4cba3a3985b709ccdbec182c79a6988bfc721e/tests/README.md
- [P14] 会话提供的 v1.0.14 计划（2026-11-02）。源文件 SHA-256 见 §2；仅作范围/依赖输入，不当作已经执行的代码证据。

### 近期一手资料

- [S1] NVIDIA 样例作者 2026-09-03 发布公告：
  https://github.com/nvpro-samples/vk_gaussian_splatting/discussions/38
- [S2] NVIDIA Vulkan Gaussian Splatting Release Notes，2026.2.9：
  https://nvpro-samples.github.io/vk_gaussian_splatting/release-notes/
  固定 tag README：
  https://github.com/nvpro-samples/vk_gaussian_splatting/blob/2026.2.9/README.md
  本次读取 README blob：`c6422ee1fb50ff527f8d2f6b2dd16ca8c2327192`。
- [S3] Open3D 官方维护者 v0.20 发布讨论，2026-09-16：
  https://github.com/isl-org/Open3D/discussions/7564
- [S4] Mobile-4DGS 作者 README，代码公告 2026-09-30：
  https://github.com/xiaobiaodu/Mobile-4DGS/blob/main/README.md
  本次读取 blob：`f48fbd3888b0ea118c9a4b37aa170fe988b5298b`；实施时固定 renderer commit。
- [S5] Mobile-4DGS 论文记录，2026-10-04；本次读取在线正文，未解析 PDF：
  https://arxiv.org/abs/2610.05289
- [S6] Kitware 作者文章，Better Transparency with VTK and WebGPU，2026-11-06：
  https://www.kitware.com/better-transparency-with-vtk-and-webgpu/

### 规范与长期背景（不是90天首发）

- [S7] Khronos Vulkan Specification，Framebuffer / Blending：
  https://docs.vulkan.org/spec/latest/chapters/framebuffer.html
- [S8] Khronos `VK_EXT_fragment_shader_interlock`：
  https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_fragment_shader_interlock.html
- [S9] Khronos `VK_EXT_attachment_feedback_loop_layout`：
  https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_attachment_feedback_loop_layout.html
- [S10] NVIDIA Vulkan OIT 样例：
  https://github.com/nvpro-samples/vk_order_independent_transparency
- [S11] NVIDIA GPU Gems，Chapter 39: Volume Rendering Techniques：
  https://developer.nvidia.com/gpugems/gpugems/part-vi-beyond-triangles/chapter-39-volume-rendering-techniques
- [S12] NVIDIA Vulkan Gaussian Splatting，Rasterization deep dive：
  https://nvpro-samples.github.io/vk_gaussian_splatting/deep-dives/rasterization_of_3d_gaussian_splatting/

`main`、`latest` 和网页会变化。除已经固定的 SHA/tag/blob 外，实施时保存核对版本；本计划不声称永久最新，更不把文档证据升级为 GPU 实测。

---

## 17. 本轮交付状态

**已完成：**读取当前两仓 main ref、Skill 入口/颜色合同/发布预算和前置 v1.0.14 计划；检索并核对90天一手增量；生成本计划及文档完整性检查。

**未执行：**v1.0.15 仓库改动、实际 Shader 编译、Vulkan/Android/GPU 实验、Live 模型调用、真实宿主加载、性能/功耗测量、打包上架。

**前置未确认：**本次读取时 main 仍是 v1.0.13；v1.0.14 实施与最终验收状态需在执行前核对。正文中的实验规模、题库数量、误差与性能目标均为计划，不是完成结果。
