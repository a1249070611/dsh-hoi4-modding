# 交接文件（HANDOVER）

> 写给接手本项目的人（或未来的自己）。读完这一篇 + `STRUCTURE.md` + `ARCHITECTURE.md`，你就能安全地开始改代码。
> 交接日期：2026-11-07 ｜ 当前版本：3.0.1 ｜ 自检 311/311 全绿 ｜ 变异 17/17

---

## 一、项目一句话

**kiant-hoi4-modkit**：HOI4 mod 开发的 MCP 工具。20 个工具（校验/知识库/脚手架/预览/排障），纯 Python 标准库零依赖，12 个 mcp-server 模块 9446 行 + 153 篇参考库（全库 185 篇 Markdown）。校验器全部对照原版 1.19.4.2 全量实证。

## 二、代码地图（改哪去哪）

| 模块 | 行数 | 职责 | 改动风险 |
|---|---|---|---|
| `cw.py` | 341 | Clausewitz 解析器。**所有模块的地基**。宽容设计：坏输入不抛异常、累积诊断 | 高——改动影响一切，跑全量自检 |
| `checks.py` | 1582 | 结构校验主体。`resolve_mod_root` 的相对 path 双基准逻辑要特别小心 | 高 |
| `kb.py` | 1445 | SQLite+FTS5 知识库。增量构建的 stale 清理、中文 2 字滑窗都是修复过的雷区 | 高 |
| `validators.py` | 864 | 8 个按类型校验器。**遍历列表块一律用 `cw.entries()`**，不要用 `stmts()`（裸 token 会整块静默跳过） | 中 |
| `server.py` | 1097 | MCP 协议 + 20 个工具注册。工具 schema 与文档数字受自检盯防 | 中 |
| `selftest.py` | 1992 | 311 项断言。**文档数字一致性也在里面**（篇数/行数/条数漂移会被抓） | 低 |
| `scaffolder/preview/planner/remote/playbook` | ~2000 | 生成/预览/计划/远端同步/错题本检索 | 低-中 |
| `tools/` 4 个脚本 | — | dds 体积校验（块数必须 `(w+3)//4` 向上取整）/ lint / survey / mutate | 低 |

**三条铁律**（都是从真实事故里来的，详见 `references/99_plugin-devlog/`）：

1. **裸 token 列表必须用 `cw.entries()`**。`events = { usa.6 }` 解析成 `Scalar`，`stmts()` 恒返回空——三个检查曾因此静默失效而自检全绿。
2. **每条新断言要有能触发它的夹具**。断言没被任何夹具路径覆盖 = 恒真，给人「测过了」的错觉。broken_mod 夹具现在 12 文件 18 缺陷 14 断言，加检查就加夹具。
3. **变异没被捕获时，先确认变异真的改变了行为**。Windows 上 `os.path.join(root, "C:\\x")` 丢弃前缀直接返回绝对路径——有些「改坏」实际是等价改写。手工应用变异、打印输出对比。

## 三、日常工作流（改完代码后按顺序跑）

```bash
# 1. 自检（约 10 秒，必须全绿）
python mcp-server/selftest.py

# 2. 变异测试（约 3 分钟，证明断言不是恒真）
python tools/kiant-hoi4-mutate.py

# 3. 打包（220+ 文件；FORBIDDEN 清单自动从当前环境生成，出现本机信息会整体失败）
python ../_pack.py 3.0.1

# 4. 资料库同步（WorkBuddy 资料库，只同步 .md）
python ../_resync.py <改过的路径...>      # 旧节点自动归档后重传
python ../_verify_library.py              # 双向核对：必须「完全一致且无重复」
```

**打包与同步的坑**（都有脚本内注释，这里只列标题）：

- `_sync_state.json` 的 `dirs` 键**不带末尾斜杠**；写错会让归档步骤静默跳过
- 平台没有 delete-node：重传 = rename 打标 → move 进归档 → upload。`_resync` 的 `stale_siblings` 必须 `keep=""`（重传时没有任何节点是对的）
- `_resync` 开头拒绝非 `.md`（曾发生「旧节点已归档、新文件 403」= 平台丢文件）；上传失败会把旧节点移回主目录
- 版本号规则：**默认只升末位**；中/大版本必须用户明说

## 四、知识体系的可信度分层（写文档前先想清楚在哪一层）

| 层 | 放哪 | 什么算数 |
|---|---|---|
| 本机实证 | `91_error-book`（`EB-`）、域文档正文 | 对照原版 1.19.4.2 文件跑过、有行号 |
| 权威转述 | 各域文档的「N.5 官方 wiki 校对补充」节 | hoi4.paradoxwikis.com，标注抓取日期 |
| 未验证思路 | `92_solutions`（`SOL-`，带 status） | 只要是想法就行，但必须标状态 |
| 维护者向 | `99_plugin-devlog`（`DEVB-`/`DEVN-`） | 插件自身的 bug 与思路，modder 不读 |

**编号互不共用**：搜 `EB-` 永不命中 devlog。数字必须实测，不能估算——`selftest.py` 会抓文档数字与磁盘的漂移（篇数、条数、模块行数、夹具文件数全在盯）。

## 五、当前状态与遗留清单

**已完成**：3.0.1 已交付（3.0.0 之上的 bug 修复 + 23 个工坊 mod 学习轮：music 校验器、EB-022~025、`93_ecosystem/mod-maintenance-engineering.md` 与五处域文档扩写；详见交付说明）；3.0.0 已交付（`交付-kiant-hoi4-modkit-3.0.0/`，含交付说明）；官方 wiki 10 页已学习并分发进 7 篇域文档。

**待办（按优先级）**：

1. **GitHub 仓库（已完成，2026-11-07）**：https://github.com/Kiant98/dsh-hoi4-modding 已建立并推送 v3.0.1（大版本重写：旧 1.x 内容全部删除，README/文档同步更新，clone 地址已填入 README；`.gitignore` 与根 manifest.json 已就位）
2. **未修 bug 六条**（见交付说明 §六，最值得先修的两个）：
   - `kb.py` `errors="replace"` 把 GBK 文件变 U+FFFD 且增量永不重试 → 建议回退解码链（utf-8-sig → cp1252 → gbk）并统计替换字符数
   - `remote.py` pull 先删旧缓存后校验 → 改 stage-then-switch
3. **可选增强**：wiki 知识落成校验规则（`set_popularities` 合计 100、`set_capital` 块语法、news_event 缺 `major`）；校验器去重 os.walk（现在全树扫 8 次）

## 六、30 秒上手检查

```bash
python mcp-server/selftest.py                       # 应 311/311
python mcp-server/server.py --call kiant_hoi4_kb_stats '{}'   # 应 69102 symbols（需已建索引）
python ../_verify_library.py                        # 应「完全一致且无重复」
```

三条都过 = 环境正常，可以开始干活。改任何东西之前，先读一遍你要动的模块在 `99_plugin-devlog/` 里的相关条目——那里记的每一个坑都真实踩过一次。
