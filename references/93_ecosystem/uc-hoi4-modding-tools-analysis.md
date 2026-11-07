---
title: 工程解剖：HOI4 Modding Tools（UC-ModdingUtilities）
domain: 93_ecosystem
scope: tooling
verified_on: VSIX v2.36.0（市场标 2.36.1）解包实测；仓库 OlanderIAO/HOI4-Modding-Tools-Extension-for-VSC
verified_at: 2026-11-07
source: 市场 2861 装机；仓库 26★；VSIX 内 out/ 编译产物 106,389 行逐项核对
---

# 工程解剖：HOI4 Modding Tools（UC-ModdingUtilities）

> **先说清一个反差**：市场装机 2861（同类最高），GitHub 只有 26★——因为
> **仓库里没有源码**。14 个文件 = README（45KB）+ 直接 commit 的
> `hoi4moddingtools.vsix` 二进制 + 12 张截图；无 LICENSE 文件（MIT 徽章挂在
> README，MIT 文本藏在 VSIX 内）、无 CI、无 release（README 却引导去
> Releases）。用户从市场装二进制包，GitHub 只是分发占位符。
> 本篇所有 file:line 证据来自 VSIX 解包（`out/` 111 个编译后 JS）。

## 1. 实态核对：宣传 vs 事实

| 宣传 | 实测 | 判定 |
|---|---|---|
| 200+ MCP 工具 | 逐族数出 **236**（git 84 / map 78 / gui 35 / script 20 / loc 6 / focus 6 / event 4 / mod 3） | ✅ 属实 |
| 129 commands / 42 settings | package.json 一致 | ✅ |
| "1631 checks / 21 suites" | 23 个 `test_*.js` 约 1690 处 check()，自研框架，`node` 直跑；**只随 VSIX 分发，GitHub 上没有** | ⚠️ 同量级属实但不可复核 |
| GFX Auditor（尺寸/格式校验） | 430 行只做 entity↔mesh 集合差 | ❌ 名不副实 |
| Battle/Equipment Simulator | 闭式公式 + 拍脑袋权重（attackPower = SA + HA×0.5 + Air×0.3，穿甲阈值硬编码 15/60/100） | ⚠️ 计算器而非模拟器 |

**工程本质**：单人 + LLM 辅助快速堆料（VSIX 里带 `MEMORY.md`——写给 AI 的
开发日志，内含过期测试数字 244/7 与 README 的 1631/21 互相打架）。运行时
依赖只有 `@modelcontextprotocol/sdk` + `sharp`，**但 node_modules 不打进
VSIX**——MCP 开箱即不可用，需用户在扩展目录手动 `npm install`。

## 2. 架构

- 无 LSP：所谓语言服务是内置 effects/triggers/modifiers 数据库的
  hover/completion provider（`out/hoi4WikiServer.js`，85KB）；
- 前端全是 **webview 单文件巨石**：mapEditorPanel.js 528KB、
  eventEditorPanel.js 263KB（HTML/CSS/JS 字符串内嵌）；
- **MCP = stdio fork 子进程**（`out/extension.js:1034-1041`）：
  mapMcpServer.js / modelMcpServer.js 等按需启动，状态栏开关按钮，
  **"Copy Claude Code Command" 按钮直接生成 `claude mcp add hoi4-map -- node …`**。

## 3. 最扎实的三个实现

1. **Dependency Graph**（dependencyGraph.js，819 行）：glob 索引 8 类目录、
   SCRIPTED_BLOCK 关键字白名单跳过（:52-58）、ROOT/THIS/FROM 作用域 token、
   DLC 前缀过滤 vanilla 引用、`\u0000` 分隔键去重（:70）、LRU 缓存 2000 文件
   + 增量重解析。注释里记录了教训：曾 8-20GB RSS 内存泄漏（MEMORY.md）。
2. **Git workbench 的 MCP 表驱动**（gitMcpTools.js:10-14）：**一张 OPERATIONS
   表同时喂 UI 和 MCP**——运行时生成 84 个工具，约 40 行代码。
3. **结构性 3-way merge**（structuralMerge.js，226 行）：块级祖先对齐、
   冲突降级到行合并——Clausewitz 文件的语义合并，mod 协作的硬需求。

## 4. 对本插件的可吸收点（按成本排序）

| 点 | 成本 | 说明 |
|---|---|---|
| dry_run + 写前备份 + 返回 `{error}` 不抛异常的统一安全层 | 半日 | 与我们「写盘工具写哪里写在明面上」的边界声明互补 |
| **OPERATIONS 单表生成 MCP 工具** | 低 | 一张表喂 UI 与 MCP 两端；若我们将来加写操作族，照此结构 |
| 自动生成 `claude mcp add` 命令的接入 UX | 低 | 我们 platform/ 文档可加一行同样的一键接入串 |
| Dependency Graph 的 NUL 键去重 + LRU + 增量重解析 | 一日 | 我们 list_overrides/kb 的内存治理参考 |
| SCRIPTED_BLOCK / scope-token 白名单 | 半天 | 引用 vs 判定的词表，直接进 kb 知识 |
| 四文件一致性导出预览（先 diff 后落盘） | 低 | preview/scaffold 的交互升级方向 |
| 按块 3-way merge | 一日 | 仅当要做 mod 协作场景 |

**明确不值**：战斗/装备"模拟器"（原版规则还原度低）；webview 巨石架构；
GFX Auditor（我们的 sprites/dds 校验器已更强）。

## 5. 坑与坏味道（为什么「广度路线」要打折）

1. **发布链断裂**：无 LICENSE 文件、无 releases、README 内 10+ 处链接指向
   不存在的目录；
2. **依赖不打进包**：普通用户必然在 MCP 步骤失败；
3. **自相矛盾**：GUI 编辑器整文件重写**丢注释**（focus 内部块重建，
   保存后 rawBlock=null）vs script_* 工具宣称保注释；
4. quickLocalization 用 prompt()/confirm() 反模式；
5. 本地化工作台是纯文件对比（无 MT 调用），别被名字误导；BOM 处理倒是对的
   （写入补 `\ufeffl_english:`、导入剥 BOM）。

## 6. 与本插件的定位对照

| | UC（广度） | 本插件（深度） |
|---|---|---|
| 工具数 | 236（多数为编辑器操作暴露） | 20（校验/知识/生成） |
| 知识 | 内置 wiki 数据库（编译进 JS） | 运行时索引原版 + 实例符号 6 万+ |
| 校验 | 弱（启发式计算器） | 8 个校验器 + 错题本 + 315 自检 |
| 源码可审计 | ❌（只发二进制） | ✅（MIT 全源码） |
| AI 接入 | MCP 广度 + 一键接入 UX | MCP 深度 + agent 规范（agents/） |

**结论**：UC 证明了「MCP 化的编辑器操作」有真实需求（2861 装机），
也演示了无源码发布的天花板（不可复核、不可贡献、依赖链断裂）。
两条路线互补而非竞争；接入 UX（一键 mcp add）值得照抄。
