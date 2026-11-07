# MCP 服务

零依赖的 stdio MCP 服务器。纯 Python 标准库，不需要 `pip install`。

## 运行

```bash
python server.py          # MCP stdio 模式，等待客户端发 JSON-RPC
python server.py --list   # 列出全部 20 个工具
python server.py --call kiant_hoi4_validate_mod '{"mod_path": "<你的 mod 目录>"}'
```

## 模块

| 文件 | 职责 |
|---|---|
| `server.py` | JSON-RPC 循环、工具注册与 schema、错误处理 |
| `cw.py` | Clausewitz 词法/语法分析，输出带行号的 AST |
| `checks.py` | 结构校验：描述文件、本地化、重复 id、缺失键、日志分析、覆盖比对 |
| `validators.py` | 按内容类型可插拔的校验器（科技/资产/图标/界面/钩子/历史/defines/音乐/国策树/本地化命令） |
| `kb.py` | 知识库：索引构建、全文检索、范例查找、符号溯源、笔记 |
| `playbook.py` | 错题本与方案库：按症状定向检索、条目完整性检查 |
| `preview.py` | 离线 HTML 预览渲染 |
| `planner.py` | 分阶段计划与 ROADMAP 同步 |
| `scaffolder.py` | 代码生成与本地化修复 |
| `selftest.py` | 330 项自检，改完就跑 |
| `bench.py` | 在真实模组上量耗时与假阳性 |

依赖方向是单向的：`server → checks/validators/kb/playbook/preview/planner/scaffolder → cw`。下层不知道上层存在。`playbook.py` 只读 `references/` 下的 md，连 `cw` 都不依赖。

## 自检

```bash
python selftest.py                  # 330 项断言，约 10 秒
python bench.py <模组路径>          # 真实模组压力测试，看索引/校验耗时与 error 数量
python bench.py                     # 不带参数则列出检测到的模组
```

`selftest.py` 里断言了 `../examples/broken_mod/` 上 12 处注入缺陷全部命中且等级正确。改动 `checks.py` / `validators.py` 之后务必跑一遍。校验逻辑的回归用眼睛看不出来。

## 协议

实现 MCP `2024-11-05`，newline-delimited JSON-RPC over stdio。支持 `initialize`、`tools/list`、`tools/call`、`ping`，以及批量请求（JSON 数组）。

`tools/call` 里任何异常都会被捕获并转成 `isError: true` 的响应，进程不退出。客户端不会因为一次工具失败就断线。

协议层测试：

```bash
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
 | python server.py
```

## 加一个工具

1. 在对应模块里写实现函数
2. 在 `server.py` 加一个 `tool_xxx` 包装
3. 在 `TOOLS` 字典注册，写 `description` 和 `inputSchema`

`description` 决定模型什么时候会调它。写清「什么场景用」比写清「参数是什么」重要得多。

## 性能实测

| 操作 | 规模 | 耗时 |
|---|---|---|
| 索引小型模组 | 287 文件 / 899 符号 | 0.7s |
| 索引原版 vanilla | 6167 文件 / 26 万词条 / 库 131MB | 16s |
| 深度校验小型模组 | 271 文件 / 7 校验器 | 0.5s |
| 深度校验示例模组 | 9 文件 / 9 校验器 | < 0.1s |
| 生成预览 HTML | 6 国策 | 2ms |
| 中文全文检索 | 12.5 万词条 | < 50ms |

索引构建期用 `synchronous=OFF` 换速度，崩溃最多重跑一次（增量会跳过已完成的文件）。`.yml` 不进 trigram 索引，12.5 万条逐条建索引会让总耗时翻三倍；本地化检索改走 `loc` 表的 `LIKE`，够用且快。

## 已知限制

- `kiant_hoi4_parse_script` 对超大文件（>5 万行）明显变慢（纯 Python 递归下降）
- 事件/决议的语义校验只到结构层，不验证 effect 名是否真实存在。那需要原版完整语义表
- 本地化的 `[?var]` / `[Root.GetName]` 动态语法只做透传，不解析
- 索引的符号抽取依赖目录约定，自造目录名的定义可能抽不到，用 `kiant_hoi4_kb_search` 兜底
