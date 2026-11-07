# 来源与许可

## 出处

本目录 `references/` 下的 84 篇上游文档（`00_start/` … `90_case-studies/`、9 个 `_index.md`）来自：

- 项目：**dsh-hoi4-modding**
- 版本：**2.0.0**
- 现仓库：https://github.com/Kiant98/dsh-hoi4-modding
- 旧仓库：https://github.com/a1249070611/dsh-hoi4-modding（账号已迁走，GitHub 仍重定向到这里）
- 许可：**MIT**
- 原路径：`skills/hoi4-modding/references/`

上游源码版权：`Copyright (c) 2026 dsh-hoi4-modding contributors`

### 版本对应关系（重要）

公开仓库 https://github.com/Kiant98/dsh-hoi4-modding 自 **v3.0.1（2026-11-07）** 起已包含本目录全部内容：84 篇上游正文、全部自撰文档（共 153 篇），以及根 `manifest.json`、`knowledge/notes`。本目录用的上游正文仍来自 **2.0.0 / 84 篇**，2026-11-06 逐文件 MD5 比对结果为 0 处差异。

这意味着：**公开仓库现在可以直接当平台知识库用**（`kiant_hoi4_kb_sync` 的 branch 用 `master`）。上游发布更新时，用上游 2.0.0 源覆盖这 84 篇，重新核对篇数与 `manifest.json` 的 `file_count`，跑一遍 `selftest.py` 确认文档数字不漂移。

## 我改了什么

**正文一个字没改。** 这样上游更新时可以直接覆盖，不用做三方合并。

本目录里由我新增的只有三个文件（不计入上游 84 篇）：

| 文件 | 作用 |
|---|---|
| `README.md` | 怎么读这套文档、权威性分层、以及上游 CLI 命令到本插件 MCP 工具的映射表 |
| `ATTRIBUTION.md` | 本文件，出处、版本对应与许可 |
| `AUTHORITY.md` | 三级可信度判定标准（A 有坐标可复核 / B 本机实测无坐标 / C 作者项目经验） |

**没有搬过来的部分**：上游的 `tools/`（21 个 Python 脚本）、`scripts/`（16 个兼容入口）、`lib/index.js`、`cordis.patch.yml`、`fixtures/`、`tests/`。本插件的工具层是自研的 MCP server，与上游 CLI 是两套架构，混在一起只会让人不知道用哪个。上游工具的能力清单与缺口见 `README.md` 的映射表。

## 验证情况

搬进来之前，我抽查了会把本插件现有写法推翻的几条，在真实文件上核过：

| 上游结论 | 我验证的方式 | 结果 |
|---|---|---|
| `.mod` 用 `picture=` 不是 `thumbnail=` | 未验证——按要求不读取 `mod/` 目录 | ⚠️ 按上游文档采信 |
| `common/units/equipment/` 存在、`common/equipment/` 不存在 | 在游戏安装目录逐个 stat（只读） | ✅ 成立（前者 OK，后者 MISS） |
| 地形在 `common/terrain/00_terrain.txt`，`map/terrain.txt` 已消失 | 同上 | ✅ 成立（前者 OK，后者 MISS） |
| 学说在 `common/doctrines/` | 同上 | ✅ 成立 |
| 中文 font override 在 `interface/core_chinese.gfx` | 同上 | ✅ 文件存在（内容未逐条核对） |
| 启动参数是 `-debug_mode` 不是 `-debug` | 读游戏自带的 `launcher-settings.json` | ✅ 成立，官方调试入口的 `exeArgs` 就是 `["-gdpr-compliant","-debug_mode"]` |
| 决议文件顶层就是分类块，没有 `decisions = { }` 外层 | 未验证 | ⚠️ 按上游文档采信 |
| 角色块有多种布局 | 未验证 | ⚠️ 按上游文档采信 |
| `supported_version` 不是运行门槛 | 与 `launcher-settings.json` 的版本字段交叉看 | ⚠️ 部分采信：未做「故意写错版本再启动」的实验，措辞已从「会被判为不兼容」改为「影响启动器与工坊的兼容提示」 |
| 补给区在 1.19 基本自动生成 | 未验证 | ⚠️ 上游自己标了「观察 + 推断」，我照抄了这个标注 |
| 官方尺寸表（focus 100×88 等） | 未验证 | ⚠️ 采信，未逐个量 DDS 头 |

> 验证口径：只读**游戏安装目录**（`<GAME_DIR>`）。不读取、不索引任何第三方模组目录，
> 因此凡涉及第三方模组才能核对的说法，一律标 ⚠️ 而不是 ✅。

未验证的直接原因是本机没有对应素材，不是存疑。要复核时按上游文档给的路径 grep 即可——每篇的「证据」小节都点了文件与行号。

## MIT 许可全文

```
MIT License

Copyright (c) 2026 dsh-hoi4-modding contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 本插件自身的许可

`mcp-server/`、`agents/`、`skills/`、`knowledge/`、`examples/`、根目录文档均为 MIT，版权归 dsh-hoi4-modding contributors。两套 MIT，互不冲突。
