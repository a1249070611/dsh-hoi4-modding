---
title: "toolapi：149 个工具的组织与五个横切中间件"
domain: 93_ecosystem
repo: https://github.com/hagane-works/hagane-studio
verified_at: 2026-11-06
method: 通读 internal/toolapi/（16485 行代码 + 13818 行测试）
---

# toolapi：工具层

位置：`internal/toolapi/`，**16485 行代码配 13818 行测试**（46%）。
这是 hagane-studio 与外界（CLI、脚本、AI）交互的唯一入口。

## 一、149 个工具覆盖什么

按域分组（来自 `docs/cli.md`）：

| 域 | 工具数 | 例子 |
|---|---:|---|
| 离线知识 | 2 | `search_knowledge` `get_knowledge_article` |
| 项目 | 5 | `list_projects` `validate_project` `export_project` |
| **任意内容** | 5 | `list_entities` `get_entity` `batch_update_entities` `delete_entity` |
| 国策树 | 8 | `create_focus` `connect_focus` `set_focus_mutual_exclusion` |
| 人物 | 6 | `create_character` `assign_character_role` |
| 事件 | 7 | `create_event_namespace` `create_super_event` |
| 决议与理念 | 6 | `create_decision_category` `create_idea` |
| 国家与历史 | 5 | `create_country` `set_country_history` `create_bookmark` |
| 政治 | 7 | `create_ideology_root` `preview_delete_ideology` |
| 科技与装备 | 16 | `create_technology_surface_branch` `repair_technology_surface_timeline` |
| 军事 | 18 | `create_division_template` `add_ship` `get_oob_snapshot` |
| 组织 | 12 | `create_mio` `create_intelligence_agency` |
| 州与地图 | 8 | `seed_states_from_vanilla` `repair_world_map` |
| 从图片生成世界 | 8 | `create_world_image` `create_country_split` |
| 脚本 | 20 | `create_scripted_localisation` `create_ai_strategy_plan` |
| 界面 | 15 | `list_ui_panels` `apply_gui_overlay_edits` |

**注意"任意内容"那组只有 5 个工具**——`list_entities` / `get_entity` / `batch_update` / `delete`。
它是个**通用的兜底接口**：149 个专用工具覆盖常见操作，兜底接口处理长尾。
这是很实用的取舍。

## 二、协议：MCP 的方法名，跑在 HTTP 上

```go
case "tools/list":
case "tools/call":
```

方法名直接借用 MCP 规范，但**传输层不是 stdio，是本地 HTTP**：

```go
type Server struct {
	tools      map[string]*registeredTool
	middleware []Middleware
}
```

对外 REST 路由（`docs/cli.md`）：

| 路由 | 作用 |
|---|---|
| `GET /api/tools` | 状态 + 所有工具（名字、描述、输入 schema） |
| `GET /api/tools/{name}` | 单个工具 + 字段参考 |
| `POST /api/tools/{name}` | 调用（body 是输入对象，返回结果对象） |
| `GET /api/tools/fields` | 字段参考清单 |

### 安全设计（值得抄）

`internal/server/server.go:45` 三道闸：

```go
header.Set("Cross-Origin-Resource-Policy", "same-origin")

if r.Host != s.host {                    // ① Host 必须精确匹配 127.0.0.1:port
	// 403
}
if origin := r.Header.Get("Origin"); origin != "" && origin != "http://"+s.host {
	// 403                                // ② Origin 非空且不是自己 → 拒绝
}
```

| 闸 | 作用 |
|---|---|
| ① `Host` 精确匹配 | 防 DNS rebinding（别人把域名解析到 127.0.0.1） |
| ② `Origin` 拒绝 | 防用户浏览的任意网页调本地 API |
| ③ `Cross-Origin-Resource-Policy: same-origin` | 防跨域读取响应 |

再加 **Bearer token**（`settings.json` 旁的 `tools-token`，首次启动生成）。

测试直接钉住行为：

```go
if code := call("POST", "/api/app/show", map[string]string{"Origin": "https://example.com"}); code != http.StatusForbidden {
	// fail
}
```

> **本库要警惕同样的问题**：任何本地 HTTP 服务（包括 MCP server 如果开 HTTP 端口）
> 若允许跨域，就等于把工具的执行权交给用户浏览的任意网页。
> 这三道闸是最低标准。

## 三、五个中间件：横切的正确姿势

`chain()` 用标准洋葱模型：

```go
func (s *Server) chain() MethodHandler {
	handler := MethodHandler(s.handle)
	for i := len(s.middleware) - 1; i >= 0; i-- {
		handler = s.middleware[i](handler)
	}
	return handler
}
```

五个中间件，每个解决一类**所有写操作都有的共性需求**：

### 3.1 `mutationReceiptMiddleware` — 防谎报

见 `hagane-studio-mutation-receipt.md`。给每个写操作加 `write_status` /
`verification_status` / `reporting_rule`。

### 3.2 `editRevisionsMiddleware` — 乐观锁

```go
"Edit revisions." — docs/cli.md
```

国策树和书签的写操作要带 `edit_revisions`（读到的版本号）。
**版本过期就拒绝，而不是覆盖更新的内容。**

```json
// 传入
{"edit_revisions": {"focus_tree:3": 7}}
// 版本不对 → 409 conflict
```

返回结果里的 `edit_revisions` 是下次该用的版本号。

**这解决的是"AI 读了旧数据然后盲目覆盖"的问题。** 多轮对话里 AI 很容易基于
过时上下文改东西。

### 3.3 `idReassignmentMiddleware` — id 撞车的如实告知

它**不主动分配 id**，而是在工具执行完后**比对请求的 id 和实际存下的 id**：

```go
if notice := reassignmentNotice(requested, returned); notice != "" {
	returned["id_reassigned"] = notice
}
```

即：工具发现 id 已被占用、自己换了一个存下去，这个中间件负责**把这件事说出来**。

```json
{"id_reassigned": {"requested": "GER_plan", "assigned": "GER_plan_2"}}
```

**不失败，但绝不静默。** 比"报错让你自己改"体验好，也比"悄悄覆盖"安全。

顺带发现：这个中间件还负责把请求里的 `locale` 注入 context
（`ctx = withContentLocale(ctx, locale)`）——横切逻辑的典型用法，
避免每个工具都自己解析语言参数。

### 3.4 `authoringDefaultsMiddleware` — 补默认值

写内容之前，自动把项目设置补齐：

- 导出语言列表加上"内容实际用的语言"
- 独立项目缺战役结束日期就补一个

结果里通过 `authoring_defaults` 告知补了什么。

**这是"防呆"而不是"防错"**：AI 通常不会想到"还要设置导出语言"，
补上比报错友好。

### 3.5 `fieldReferenceHintMiddleware` — 字段提示

`hw describe <tool>` 能显示每个字段期望什么、哪些字段装的是**原始 HOI4 脚本**。

```json
{"fields": {"completion_reward": {"type": "script", "raw": true}}}
```

对 AI 尤其重要：知道"这个字段是原生脚本"和"这个字段是枚举值"，
写出来的东西完全不一样。

## 四、区别 `id` 和 `key`（核心概念）

`docs/cli.md` 明确区分：

> `id` is the row id of a thing in the project (use it to change or delete it);
> `key` is the identifier the game uses (use it to reference the thing from other content).

| 概念 | 谁用 | 例子 | 用途 |
|---|---|---|---|
| `id` | 编辑器 | 数据库行号 `12` | 改/删这件事 |
| `key` | 游戏 | `GER_the_four_year_plan` | 别处引用它 |

**这个区分极其重要**。本库目前只有 `key`（游戏内的标识），没有独立的行 id。
后果是：如果一个 mod 里有两个同名 key（引擎允许后者覆盖前者），
我们无法单独定位"第二个"。

**借鉴价值**：如果本库将来支持编辑，必须引入稳定的行 id，
不能拿 key 当主键。

## 五、测试策略：接口层测得最狠

`toolapi` 有 60 多个 `_test.go`，几乎一个工具文件配一个。看几个名字就知道关注点：

```
tools_focus_proxy_test.go          23.3 KB   国策工具
tools_gui_overlay_test.go          34.2 KB   界面覆盖
tools_daily_edit_proxy_test.go      7.6 KB   日常编辑
mutation_receipt_test.go           10.8 KB   回执语义
id_selfcheck_test.go                3.7 KB   id 撞车
rest_proxy_business_diagnostics_test.go  6.2 KB  业务诊断
```

**测试体积能反映复杂度**：`tools_gui_overlay` 62 KB 代码配 34 KB 测试，
`tools_focus_proxy` 32 KB 配 23 KB。**代码越复杂，测试投入越高**。

值得注意的是有 `states_display_name_regression_test.go`——**回归测试单独成文件**，
说明某个 bug 曾经出现过且值得永久守住。

## 六、输入校验：schema + 字段参考双层

每个工具有 `input_schema`（JSON Schema），但**不只是 schema**：

```go
type Tool struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	InputSchema any    `json:"input_schema"`
}
```

`hw describe <tool>` 同时还返回**字段参考**（field reference）：
解释每个字段的语义、取值范围、哪些是原生脚本。

**schema 管"类型对不对"，字段参考管"语义对不对"。** 两层分离，
因为 JSON Schema 表达不了"这个字符串是 HOI4 原生脚本"这种事。

## 七、错误码设计

`docs/cli.md`：

| 状态 | 含义 |
|---|---|
| 400 | 输入不符合工具的 schema |
| 404 | 项目不存在 |
| 409 | 冲突（版本过期、id 撞车） |
| 422 | 程序拒绝了这次修改 |
| 503 | 未就绪，等会儿重试（游戏索引还在建） |

**503 这条很实用**：游戏索引建立要几秒到几十秒，这段时间工具不可用。
用 503 明确告诉调用方"等"，而不是报个模糊错误。

## 八、本库该怎么吸收

### 8.1 立刻可做：给 lint 加回执

本库现在 `kiant-hoi4-lint.py` 只输出"错误/警告/干净"。改成：

```json
{
  "files_checked": 81,
  "errors": 1,
  "warnings": 0,
  "write_status": "read_only",
  "verification_status": "syntax_checked",
  "reporting_rule": "语法和运算符已静态检查；引用完整性和游戏内行为未验证。"
}
```

### 8.2 中期：id 与 key 分离

本库的 `checks.py` 采集定义时用 key 当标识。如果要支持编辑，
需要一个 `(file, line)` 或稳定 id 作为行标识——**这不是重构，是补基础**。

### 8.3 长期：中间件模式

本库的 MCP server（`mcp-server/server.py`）现在是平铺的 `if/elif` 分发。
如果要加"回执""乐观锁""默认值"这类横切逻辑，
**改成中间件链比在每个 handler 里复制粘贴干净**。

## 九、诚实评价

**好的一面**：
- 接口层测得极狠（46%）
- 横切逻辑用中间件，没污染 149 个工具
- MCP 术语 + HTTP 传输，兼顾兼容性和可控性
- 本地安全设计（拒 Origin、拒非 loopback）到位

**疑虑**：
- 149 个工具的学习成本很高，`hw tools` 输出 149 行
- 每个工具都有独立 schema，游戏更新后同步维护量大
- `mutationPrefixes` 靠名字前缀判断"是不是写操作"，
  新工具命名不规范就会漏挂回执——这是**约定优于配置的隐患**

最后一条值得本库警惕：任何"靠命名约定驱动行为"的机制，
都需要一个**测试守住约定**。它有：

```go
if !strings.Contains(tool.Description, "mutation_receipt") {
	t.Errorf("mutation tool %q has no mutation_receipt contract", tool.Name)
}
```

**测试遍历所有工具，检查每个写工具的描述里都有回执契约。**
约定 + 守卫测试 = 可靠。
