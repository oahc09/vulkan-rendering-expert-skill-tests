# Vulkan Expert Skill v1.0.10 — 一致性与发布验收

> 刷新日期：2026-11-01。
> 结论：旧 v1.0.9 计划的大部分实现已经进入 main。下一轮不再重做 Descriptor Heap、最小启动或 Live runner；以 v1.0.10 收口跨仓契约、知识一致性、运行时边界和真实验收证据。
> 本文是只读核查后的实施计划，不是本轮执行结果；未修改远端仓库、未运行 pytest / GPU / 实时模型、未发布。

## 1. 本次固定基线

| 对象 | 本次核实值 |
|---|---|
| Skill 仓库 | `oahc09/vulkan-rendering-expert-skill` |
| Skill main SHA | `102c5d721dcb43a23e12d77927f2703d56c63a11` |
| Skill Git tree | `5c1b21ffa2d7db0fad14abb8e5073f5651aba8e7` |
| 入口声明版本 | `1.0.9`，`last-updated: 2026-10-17` |
| 最新 main 合并 | 2026-10-30，PR #5：Agensi 发布打包加固与最小启动契约对齐 |
| 测试仓库 | `oahc09/vulkan-rendering-expert-skill-tests` |
| 测试 main SHA | `f48871940b6af3c20a6fa9d108645631735512ac` |
| 旧计划的 Skill 基线 | `1bad967c8e6880c3eecdaa6a946901cbc5c1f060`，当时为 v1.0.8 |

以上来自 GitHub 连接器对 main ref、固定 SHA 文件和合并记录的读取。[R1–R4]

本次主要刷新代码差异与执行计划，没有重新制作一份“最近一个月热点排行榜”。原计划的 2026-09-17 至 2026-10-17 调研窗口保留为历史资料；不把其中的规范/SDK版本继续称为永久最新。实际实施时冻结对应 Registry / Spec / SDK 修订，再判断是否需要额外更新。

## 2. 旧计划哪些已经完成

“完成”在下表中指实现或文档已存在，不代表所有语义、真实宿主与 GPU 行为已经通过验收。

| 旧计划项目 | 最新代码情况 | 新计划处理 |
|---|---|---|
| Descriptor Buffer 符号/字段纠错 | 卡片已重写：明确 opaque descriptor、host 生成、真实对齐字段；不存在的枚举保留为反例并明确否定。[R5] | 从新增任务中删除，保留定向语义回归；扫描器必须区分错误用法与反例文本。 |
| 新增 Descriptor Heap | changelog、API 卡交叉引用及专项回归均已包含此主题。[R4、R5、R8] | 不重复新增卡片；只对有证据的剩余问题修订。 |
| 最小启动与单一路由 | SKILL 已改为 hard_rules 全文 + routing-entry + 命中段落；输出模板、验证范围按任务展开。[R1] | 不再次重构入口；验证宿主是否真的执行该契约。 |
| Static / Snapshot / Live 分层 | 测试仓库已分层；历史快照明确不是实时证据；runner 已支持读取请求、调用元数据、usage、hash 和失败留存。[R6] | 不重写 runner；补当前候选执行证据和实际宿主接入。 |
| token 统计 | 已有 `measure_context.py`，区分启动代理指标、读取上下文指标和同模型实际 input-token 配对指标。[R6] | 使用现有计量口径，不另造重复统计。 |
| Vulkan feature 与 WSI 修订 | 10-24/25 修订已覆盖版本宏、feature struct、fence reset、present semaphore 和退役边界。[R4、R10] | 扫描摘要/正文/示例之间的残余矛盾，并纳入定向评估。 |
| 安全与可复现打包 | PR #5 已提供白名单打包、dirty-tree 拒绝、链接/锚点检查、ZIP CRC 与逐文件 SHA 校验；合并记录报告 24 项单测通过、196 文件包。[R3、R11] | 复用现有脚本；不重建打包系统，不把历史记录当本轮重跑结果。 |

因此本版目标不是“进一步扩大 Vulkan 知识面”，而是：**同一条规则在不同入口保持一致，同一份发布产物有同一组可追溯验收证据。**

## 3. 当前剩余缺口与优先级

### P0-A：测试契约落后于主仓打包方式

`tests/test_v1_0_9_regression.py::test_release_version_and_manifest_budget` 当前：

- 写死入口版本为 `1.0.9`。
- 把 `git ls-files` 与非忽略未跟踪文件的并集称为 packaged，再断言 ≤200。
- 从 v1.0.8 基线比较新增 references，要求新增项只能是 `descriptor_heap.md`。[R8]

但主仓现在使用白名单运行时 ZIP，且已有 `references/07_integration_pack/behavior_evaluation.md` 等后续变更。[R3、R9、R11]

这首先是**契约差异**，不能通过删除知识、忽略所有失败或随意放宽断言解决。需要分别校验源码清单和实际交付清单，并保留内容完整性、脏树拒绝与安全检查。

此外，`.github/workflows/test-skill-branch.yml` 的非 main / PR 默认仍固定为 `7c167d1b27e112c48219c0ebcd57e4d209a926db`。它不能作为更新后的 main 或未来 v1.0.10 已受测的证据。[R7]

### P0-B：同一 Workflow 的摘要与详细步骤仍不一致

`references/05_workflows/01_renderer_setup/setup_frame_loop.md`：

- §1 摘要：`Wait → Acquire → Reset Fence → Reset / Record CommandBuffer → Submit`。
- §8 详细步骤：先录制成功，再确定会提交，紧邻 submit reset fence。[R10]

不能仅凭这个顺序就断言所有提前 reset 的实现都违反 Vulkan 规范；具有完整失败恢复的实现需单独判断。但当前文档对同一默认工作流给出不同建议，按段检索会得到不同答案。应统一默认安全路径，并明确 acquire、录制与 submit 的各类失败分支。

官方教程说明了 reset 后因 acquire 失败提前返回导致 fence 无人 signal 的问题；官方 Guide 则明确 submit fence 不能单独证明 present wait semaphore 已完成使用。[S1、S2]

### P1-A：运行时知识与历史评估原文混在一起

`references/07_integration_pack/behavior_evaluation.md` 保留历史原始回答，且其顶部明确说明旧工作区指纹、dirty state 和合并后没有重跑。白名单打包包含 `references/**`，因此这份历史评估也进入运行时包。[R9、R11]

建议将原始评估、加载记录及指纹完整归档到独立测试仓库，再把原路径保留为短的证据边界/历史索引。不要丢失证据、不要改写原始失败或成功回答；迁移先完成副本与 hash 验证，再替换运行时正文。

目标是减少无关上下文并降低评估答案被加载的风险，不是继续压缩核心 API 知识。

### P1-B：历史 PASS 尚未覆盖最终候选

测试仓库当前 `reports/v1.0.9/manifest.json` 对应 Skill SHA `7c167d1...`：94 Static、4 Snapshot、12 Live skipped，Live 状态为模型调用前基础设施阻塞，真实 input-token 降幅为 null，硬件测试未运行。[R12]

主仓的 4/4 定向评估记录也明确限定旧工作区指纹，不能迁移为合并后 main 的行为 PASS。[R9]

PR #5 的打包/契约测试有对应 tree 证据，但明确不涵盖实际宿主发现、Live 行为、GPU 和平台审核。[R3]

下一步应补**当前候选的证据**，不是把上述数字相加成为一个更大的“通过数”。

## 4. v1.0.10 只做四个里程碑

### M0：跨仓契约对齐

**目的**：确保测试真正检查当前候选及实际交付包。

主要落点：

- 测试仓库 `.github/workflows/test-skill-branch.yml`。
- `tests/test_v1_0_9_regression.py` 和仍依赖旧整仓预算的相关测试。
- 主仓 `scripts/agensi_audit_and_pack.py`、`scripts/host_contract.py` 的既有契约及报告接口。
- `AGENSI_RELEASE.md` 的版本/渠道说明。

工作内容：

1. 冻结 Skill SHA 与 tests SHA；先运行现有检查，保留原始失败结果，区分真缺陷与契约过时。
2. 发布测试使用明确 expected version 与 reviewed Skill SHA；不要简单改为“版本大于 1.0.9 就算通过”。历史版本测试仍可保留独立基线。
3. 将三个指标分开：源码跟踪文件数、运行时包文件数、Agent 实际读取量。
4. 包预算依据实际白名单 manifest；测试确认运行时所需知识完整、仓库专用脚本/配置未误入。整仓清洁检查不能删除。
5. 不再使用旧 PR 固定 SHA 冒充当前候选；发布验收显式指定完整 Skill SHA，并记录实际 checkout SHA。找不到候选时失败，不回退旧版本。
6. 将主仓 Node 检查、host contract、24 项现有 Python 单测与独立仓库 Static/Snapshot 纳入同一组候选记录。具体测试数量按实际输出，不冻结为 24 或 94。

**验收**：报告同时给出 Skill SHA、tests SHA、source tree、package manifest 与包 hash；全部应运行的静态检查无失败，skip 必须说明原因；既有安全拒绝行为不退化。

### M1：知识一致性修订，不扩知识面

**目的**：防止最小段落读取拿到与正文冲突的规则。

优先四条链：

| 知识链 | 优先核对文件/区域 | 验证要点 |
|---|---|---|
| Frame loop 与异常路径 | `setup_frame_loop.md`、`frame_lifecycle.md`、`fence.md`、`queue_submit.md` | acquire 前后、录制失败、submit 失败的 fence/image/semaphore 状态一致。 |
| Present 复用与退役 | `frames_in_flight.md`、`semaphore.md`、Swapchain API/workflow、Android 生命周期 | frameIndex 与 imageIndex 分离；submit 完成不等于 presentation 退役；扩展与无扩展路径分开。 |
| Vulkan version / feature | `vulkan_1_4_overview.md`、`physical_device.md`、`logical_device.md`、相关 feature 卡 | 数值版本宏、头文件宏、feature 支持起点、结构体归属、查询与启用不混淆。 |
| 验证强度 | `hard_rules.md`、`accuracy_check.md`、`verification_gate.md`、`response_formats.md` | 纯知识、设计审查与实际完成声明分别处理，保留必要验证而非机械展开所有关卡。 |

实施要求：

- 先修已确认的 §1/§8 冲突，再检索相同规则的其他引用；不进行无关全文重写。
- 每条易错规则指定一个权威段落，其余位置给一致的短摘要或稳定锚点引用。
- 建立“章节独立读取”检查：摘要、主步骤、失败路径、引用分别读取时不产生相反建议。
- 符号扫描保留，但不把“出现不存在枚举的反例”误判为 API 使用错误；也不靠白名单跳过实际错误。
- 不把 WSI 复杂边界简化为“所有场景只需 WaitIdle”，也不把工程保守建议写成无条件规范要求。

**验收**：上述四条链的摘要/正文/示例一致；已有规范来源可定位；关键错误结论的自动回归与人工复核通过。此阶段不声称已经在 GPU 上验证。

### M2：收口运行时结构与交付边界

**目的**：保留 v1.0.9 的精简成果，不再增加平行框架。

不变项：

- 保持 `references/00` 至 `07` 八模块，不重新编号。
- 保持触发条件、已有模型/宿主配置和兼容回退；没有证据不调整现有模型路由。
- hard_rules 全文、routing-entry、按需资料；Evidence Map / Architecture Map、影响面、R1–R5、适用范围内 G1–G6 不丢失。
- 不新增 API 大专题；运行时知识文件净增目标为 0。

具体改动：

1. 历史评估原文归档测试仓库，原 references 路径保留短索引/边界声明，避免断开旧引用。
2. 测试输入不暴露历史答案、人工 rubric 和预期修复；runner/harness 用可验证的读取边界排除这些材料，而不只要求模型自行承诺不读。
3. 主仓维护“知识 + 本地契约与安全打包脚本”；测试仓库维护“行为题库 + Live 调用 + 计量 + 原始证据”。不搬走 PR #5 已有的安全单测来制造新的发布依赖。
4. `agents/claude-code.yaml` 继续标为示意配置，直到真实宿主加载记录证明该文件确被使用。静态 YAML 通过不升级为宿主通过。[R11]
5. 保留白名单、dirty-tree 拒绝、symlink/path 检查、无覆盖发布、CRC 和 per-file SHA；修订后双次打包复验确定性。

**预算口径**：

- 当前 PR #5 报告的 Agensi 网站包为 196 文件（195 个附加文本文件）。本版建议保持不超过这一内部基线，除非有明确新增价值与审核；不要为省数字删除必要知识。[R3]
- Agensi 官方当前区分网站上传 1,000 文件/50 MB、Agent 上传 100 文件/5 MB、交付最多 200 个附加文本文件/600 万字符。本版沿用网站包路线，不把 196 文件包用于 100 文件渠道。[S3]
- ClawHub 若继续维护，作为独立 profile 核实并检查，不把其历史预算套在全部 Git 源码或其他平台上。
- 文件数不是 token 指标；实际读取字节、token、轮数与模型费用分别记录。

**验收**：八模块与公共引用稳定；原始证据完整保存；运行时包不含历史回答正文和无关开发工具；包清单与渠道限制一致；安全测试仍通过。

### M3：真实宿主、Live 与发布证据闭环

**目的**：证明当前候选在真实加载条件下工作，而不只是文档静态通过。

复用既有 runner、rubric、16 项语义场景来源，不另建一套评测系统：

- 原有 4 项 Project Diagnosis。
- v1.0.9 已有 8 项对抗题。
- 10-25 已记录的 4 项定向题：版本/feature struct、acquire/fence 异常、present semaphore 复用/退役、纯 API 与未运行方案的证据边界。

先将四项定向题规范化进入测试仓库，并保留旧历史记录；运行时不提供答案或判据。题库扩展时同步修改当前固定 12 项的校验与计量逻辑，不只添加 prompt 而让它永远不执行。

运行顺序：

1. 对当前候选执行 Static、Snapshot 和打包/宿主契约检查；不同层单独计数。
2. 16 场景各一次做烟测；发布级稳定性建议同模型同参数每场景至少三次，原始输出不可修改。
3. 至少一个实际目标宿主完成发现、加载、路由与按段读取验证；其他宿主没有证据时保持未验证。仓库里的配置文件不自动等于宿主支持。
4. Agensi 清单的 Android 黑屏、同步/VUID、性能、架构四类人工题继续做端到端检查，可复用相近输入，但保留独立人工判定与读取记录。
5. 每个结论绑定 Skill SHA/tests SHA、实际模型/参数、输入输出 hash、读取轨迹与 provider usage。模型名称取不到就如实记录，不能伪填。
6. 对语义正确性人工复核；关键词 smoke check 不单独代表专家能力通过。
7. 最终 commit 变更后，失效的测试、读取指纹和打包 hash 必须重算，不把旧 dirty tree 或旧 SHA 的 PASS 继承过来。

**token 目标不要偷换基线**：

- 原“降低至少 30%”承诺的基线仍是 v1.0.8 SHA `1bad967...`；按原相同 12 场景、相同模型与参数测 provider input tokens。
- 本版新增 4 场景单独计分，不拿不同题目集合比较中位数。
- 当前 v1.0.9 SHA `102c5d7...` 可用于 v1.0.10 的行为/输入量不退化比较，但不能重新要求再降 30%，也不能替换旧承诺基线。
- 启动字节数、tokenizer 估算、读取上下文代理指标与实际模型输入成本分开展示。
- 没有授权模型/可观测宿主/可用设备时，对应 gate 为 BLOCKED 或未验证，其他可执行检查照常进行；不得用历史快照补位。

**发布门槛**：静态与安全检查通过、关键语义无错误、最终 SHA 的 Live/宿主证据齐全、实际交付包可复现。若 token 目标未测或未达，只能单独声明未验证/未达，不宣称轻量化目标达成；需明确决定是否仅发布 correctness-only 候选。GPU 结果只有实际执行后才可宣称，本次技能文档发布不等于交付 Vulkan 运行时。

## 5. 建议的实施边界

| 范围 | 本版决策 |
|---|---|
| 新增顶层知识模块 | 不做 |
| 再写 Descriptor Heap / Live runner | 不做，已有实现 |
| 重写所有 API 卡 | 不做，仅处理有证据的冲突和新增回归 |
| 扩展 Ray Tracing、Work Graphs、协作矩阵 | 后置 |
| 最小启动再次改架构 | 不做，以当前契约验证和修正为主 |
| 提交/推送/合并/上架 | 由本次实施授权决定；本计划不自动授权发布或凭据操作 |
| 最新新闻吸收 | 只有能映射到现有知识缺口和可验证问题时入库，不为新闻增加目录 |

## 6. AI 实施提示词

```text
基于两个仓库最新 main，实施 Vulkan Expert Skill v1.0.10：一致性与发布验收。
本计划固定的 Skill SHA 是 102c5d721dcb43a23e12d77927f2703d56c63a11，
测试 SHA 是 f48871940b6af3c20a6fa9d108645631735512ac。
若实际 HEAD 变化，先读差异，不回退、不覆盖用户已有成果。

先读取 AGENTS、git status、SKILL.md、AGENSI_RELEASE.md、现有打包/契约检查、
测试仓库 README/CI/发布回归/Live runner/measure_context 和相关原始证据。
不重做 v1.0.9 已完成的 Heap、最小启动、Static/Snapshot/Live 分层。

按 M0→M1→M2→M3 执行：
M0：对齐两仓候选SHA、expected version、源码清单和白名单发布包清单。
     不删除脏树拒绝、安全校验或内容完整性断言；旧SHA不能冒充新候选受测。
M1：先修 setup_frame_loop.md §1 与 §8 的 reset fence 时序不一致；
     沿 frame/WSI/version-feature/verification 四条链检查摘要、正文与示例。
     只有证据支持才改技术规则，保留官方来源、失败分支和适用边界。
M2：保留8模块、触发条件、模型配置、稳定引用与安全打包。
     历史评估原文先完整归档到测试仓库并验hash，原路径保留短索引；
     不让待测模型读取历史答案/rubric。运行时知识文件净增目标0。
M3：复用runner，原12题+4项定向题；真实调用留原始输入输出、读取轨迹、
     模型/参数、双方SHA、hash、usage和人工复核。至少验证一个实际宿主。
     没有真实调用则Live=BLOCKED，不编辑快照冒充通过。

计量：原30%输入token目标仍对比v1.0.8固定SHA与相同12题；
当前v1.0.9→候选的回归比较单列，不偷换基线或用字节数替代token。
包预算检查实际白名单及渠道profile，不再把git ls-files数量当所有平台包大小。
保持MIT、免费分发、原模型路由和触发条件；不增加API大专题。

按授权修改并做必要测试；未经单独授权不得合并main、上架、部署、改权限或处理凭据。
交付：固定基线、差异清单、知识纠错证据、分层测试结果、Live/宿主状态、
包manifest/hash、token计量、未验证项和回滚方法。
发布声明必须针对最终候选SHA，不继承旧dirty工作区/旧SHA结果。
```

## 7. 核查来源

下列 GitHub 链接均固定至本次读取的提交；本轮是源码读取和计划刷新，不是重新执行其测试。

- [R1] 当前 Skill 入口：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/102c5d721dcb43a23e12d77927f2703d56c63a11/SKILL.md
- [R2] 最新合并提交：
  https://github.com/oahc09/vulkan-rendering-expert-skill/commit/102c5d721dcb43a23e12d77927f2703d56c63a11
- [R3] 已合并 PR #5 的变更/验收记录：
  https://github.com/oahc09/vulkan-rendering-expert-skill/pull/5
- [R4] 当前 changelog：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/102c5d721dcb43a23e12d77927f2703d56c63a11/references/00_expert_entry/change_log.md
- [R5] Descriptor Buffer 卡片：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/102c5d721dcb43a23e12d77927f2703d56c63a11/references/03_api_manual/05_descriptor/descriptor_buffer.md
- [R6] 最新测试与Live/计量契约：
  https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/f48871940b6af3c20a6fa9d108645631735512ac/tests/README.md
- [R7] 当前跨仓 CI：
  https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/f48871940b6af3c20a6fa9d108645631735512ac/.github/workflows/test-skill-branch.yml
- [R8] 当前发布契约测试：
  https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/f48871940b6af3c20a6fa9d108645631735512ac/tests/test_v1_0_9_regression.py
- [R9] 历史定向评估及其失效边界：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/102c5d721dcb43a23e12d77927f2703d56c63a11/references/07_integration_pack/behavior_evaluation.md
- [R10] 当前 Frame Loop Workflow：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/102c5d721dcb43a23e12d77927f2703d56c63a11/references/05_workflows/01_renderer_setup/setup_frame_loop.md
- [R11] 当前 Agensi 发布与宿主验收边界：
  https://github.com/oahc09/vulkan-rendering-expert-skill/blob/102c5d721dcb43a23e12d77927f2703d56c63a11/AGENSI_RELEASE.md
- [R12] 已有 v1.0.9 报告 manifest（针对旧候选，不是最新 main）：
  https://github.com/oahc09/vulkan-rendering-expert-skill-tests/blob/f48871940b6af3c20a6fa9d108645631735512ac/reports/v1.0.9/manifest.json
- [S1] Khronos 官方教程，Swap chain recreation / Fixing a deadlock：
  https://docs.vulkan.org/tutorial/latest/03_Drawing_a_triangle/04_Swap_chain_recreation.html
- [S2] Khronos 官方 Guide，Swapchain Semaphore Reuse：
  https://docs.vulkan.org/guide/latest/swapchain_semaphore_reuse.html
- [S3] Agensi 官方包装与渠道限制，2026-11-01 再核验：
  https://www.agensi.io/docs/packaging

## 8. 本轮交付状态

- 已完成：读取最新两个 main、对照旧计划、识别已完成工作与剩余缺口、刷新里程碑和执行提示词。
- 未验证：当前候选的全量 pytest、打包重跑、Live 模型、真实宿主、token改善、GPU/Android运行、平台上架。
- 环境限制：本轮容器 Git 网络解析不可用，未建立本地 checkout；核查依据是 GitHub 连接器返回的固定 SHA 源码与记录，不宣称已经本地执行测试。
- 仓库写入：无。旧计划文件保留，本文以新日期/新版本独立交付。
