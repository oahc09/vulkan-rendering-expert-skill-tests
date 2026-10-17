# Vulkan Expert Skill v1.0.9 执行报告

日期：2026-10-17 UTC。候选 Skill commit：`7c167d1b27e112c48219c0ebcd57e4d209a926db`。
Skill PR：https://github.com/oahc09/vulkan-rendering-expert-skill/pull/4

## 已完成
- 规范纠错与 Descriptor Heap 卡；能力矩阵、AHB/YCbCr、工具版本/覆盖边界、公开误判案例和后端迁移门槛。
- 保留8模块、19硬规则、原触发词和宿主配置；200个包文件，只新增1张知识卡。
- 69个API Markdown文件的符号/限定成员/VUID扫描及明确未知项处置，另外逐项纠正12个已有VUID的语义错配。范围和官方冻结来源见 [registry audit](registry-audit/README.md)。扫描不是全语义或GPU正确性证明。
- 测试分为Static、Snapshot、Live。原4场景快照保留；新增8场景的提示词、判定规则；支持章节/锚点读取、原始失败保存、SHA/hash/调用参数和provider usage记录及版本对照。

## 实际验证
- 冻结旧两仓库基线：76通过、2跳过。旧跳过分别是索引解析未覆盖反引号路径和已合并的release checklist旧路径，现已改成有效断言。
- 当前本地：Static 94通过；Snapshot 4通过；Live 12跳过。总计98通过、12跳过、0失败。运行日志附本目录。
- 扫描器独立根路径/错误父目录/空目录3项验证通过，防止0文件假通过。
- 首轮强制加载字节代理：42050→11222。仅启动路径，不含随后任务资料与宿主开销；不作为实际模型token节约证据。

## 尚未通过的发布验收
真实Codex CLI smoke在调用模型前初始化失败：`failed to initialize in-process app-server client: Read-only file system (os error 30)`。原始stderr已保存。
因此没有伪造Live回答，也没有把历史快照算成当前模型验证；同模型12场景新旧版本对照、真实输入token中位数降低≥30%尚未验证。GPU/硬件测试未运行。
两个PR应保留Draft，直至补齐所需Live验收或用户明确调整验收标准；不自动合并。

## 复跑与CI
见 [测试说明](../../tests/README.md)。CI的PR/feature运行冻结到上述Skill SHA；main及手动默认Skill main，保留skill_ref输入。合并顺序Skill先、测试仓库后。CI仅能证明Static/Snapshot及Live可用性状态，不能将未配置Live显示为通过。
所有证据文件的SHA256见 manifest.json；没有将完整官方XML/header/validusage数据塞进Skill包。
