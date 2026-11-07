# 更新日志

本仓库自 3.0.1 起重写：旧的 1.x 插件骨架（`lib/index.js`、`cordis.patch.yml`、`.github/workflows`、`skills/hoi4-modding` 等）已全部移除，仓库内容即本工具包本体。

## 3.0.1 — 2026-11-07

首个发布到 GitHub 的 3.0.x 版本，也是本仓库的大版本重写节点。

**新增与修复**

- 知识库解码链：`kb.py` 改为 utf-8-sig → gbk → cp1252 → latin-1 依次回退并记录 `files.enc`，GBK 文件不再被解成 U+FFFD 且增量不再永久跳过。
- 中文混排切词：修复 CJK 与拉丁字符混排时的分词边界，检索命中率回升。
- `LIKE` 转义：`kb.py` 的模糊检索对 `%`、`_` 做转义，避免用户输入被当通配符。
- `remote.py` 拉取改为 stage-then-switch：先落到临时目录并校验，成功后才切换缓存，失败不再删掉旧缓存。
- `check_defines` 不再把 Lua 表字面量误报为错误。
- 新增 music 校验器（情感电台实测抓到 3 个静默问题：030.ogg 缺失、0010 拼写错、mp3 混入）。
- 文档数字漂移修复：参考库篇数、错题本条数、模块行数、可同步文件数与磁盘保持一致。
- 23 个工坊 mod 学习轮：新增 `93_ecosystem/mod-maintenance-engineering.md` 与 EB-022~025，五处域文档扩写。
