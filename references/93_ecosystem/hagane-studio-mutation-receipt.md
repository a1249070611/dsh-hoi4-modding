---
title: "mutation_receipt：写给 AI 的诚实约束机制"
domain: 93_ecosystem
repo: https://github.com/hagane-works/hagane-studio
verified_at: 2026-11-06
method: 通读 internal/toolapi/mutation_receipt.go（513 行）+ 配套测试
---

# mutation_receipt：防 AI 谎报的回执

位置：`internal/toolapi/mutation_receipt.go`，513 行。**这是整个仓库我认为最值得学的设计。**

它要解决的问题很具体：**AI 调用写操作后，会倾向于宣称"成功了"。** 而实际上：

- 文件可能只是写进去了（`committed`），但内容根本没被验证
- 可能部分成功（10 条里 8 条成 2 条败）
- 可能写进去了但引用指向不存在的东西（国策永远不会亮）
- 可能验证根本没跑（`not_run`）

人类做这些事会自己再去检查一遍；**AI 不会，它会直接说"已完成"**。

## 一、回执的六个字段

```go
type mutationReceipt struct {
	Tool               string `json:"tool"`
	ProjectID          int64  `json:"project_id"`
	WriteStatus        string `json:"write_status"`
	VerificationStatus string `json:"verification_status"`
	SavedValuesSource  string `json:"saved_values_source"`
	ReportingRule      string `json:"reporting_rule"`   // ★ 给 AI 看的规则
}
```

两个状态维度**刻意分开**：

| 字段 | 取值 | 含义 |
|---|---|---|
| `write_status` | `committed` | 确实写进去了 |
| | `partially_committed` | 部分成功（有失败行但也有成功行） |
| | `no_change` | 什么都没改（`ok=false` 或全部失败） |
| `verification_status` | `not_run` | **写了，但没验**（默认态） |
| | `references_passed` | 引用的东西都存在 |
| | `verified` | 工具自己报了完成且各项证明都通过 |
| | `issues_found` | 有问题 |
| | `verification_unavailable` | 想验但验不了 |
| | `diagnostics_found` | 写成功了但有诊断警告 |

**`committed` + `not_run` 是最常见的组合**，也是它专门要防的：
"我写完了"不等于"我写对了"。

## 二、`reporting_rule`：直接约束 AI 的话术

这是核心创新。它不是给人看的错误信息，而是**给模型看的指令**：

```go
reportingRule = "The write committed, but semantic verification did not run. " +
	"Report only values returned by this result; " +
	"re-read and validate before claiming completion."
```

失败时更直接：

```go
"The write committed with unresolved references. Do not claim the affected " +
"behavior is complete or working until those references are repaired and checked again."
```

批量部分失败时：

```go
"The batch contains failed rows. Report the successful and failed result rows separately; " +
"never describe the full batch as completed."
```

**用词都是可执行的动作**（report / do not claim / re-read / validate），
不是"请注意""建议检查"这种软话。

## 三、它会主动去查引用

不只是报告状态，它会**真的发一次请求验证引用完整性**：

```go
resp, err := proxyAuthedCall(ctx, proxy, "GET",
	fmt.Sprintf("/api/projects/%d/relations/entity/%s/%d", projectID, sourceKind, sourceID), nil)
```

然后逐条检查 `resolved` 字段：

```go
for _, raw := range rows {
	edge := raw.(map[string]any)
	if resolved, present := edge["resolved"].(bool); present && resolved {
		continue
	}
	unresolved = append(unresolved, DanglingReference{...})
}
```

有悬空引用就生成人话警告：

```
UNRESOLVED REFERENCE: completion_reward uses add_idea -> idea SOME_ID,
but that target does not exist. Create it or remove the reference before claiming success.
```

**注意它只对特定工具做这件事**（`mutationReferencePolicies` 白名单）：
`create_focus` / `update_focus` / `create_event` / `update_event` /
`add_event_option` / `create_decision` / `update_decision` / `create_idea` / `update_idea`。

为什么只这几个：这些的脚本字段里可能出现**带索引的引用**（`add_idea = X`、
`country_event = { id = X }`），而这些 X 是否有效可以直接查。其他工具的引用语义复杂，
查了容易误报。

## 四、怎么判断"工具说它完成了"

`inspectExplicitMutationProof` 检查两类字段：

**主语**（工具自己声明完成）：

```go
for _, key := range []string{"completed", "valid"} {
	if value, present := fields[key].(bool); present {
		if value { proof.primaryPassed = true } else { proof.failedPrimary = append(..., key+"=false") }
	}
}
```

**旁证**（十种验证标记）：

```go
"persistence_verified", "authoritative_validation", "readback_verified",
"references_verified", "sprite_references_verified", "localisation_verified",
"structurally_valid", "references_valid", "compiled_readback_valid", "export_valid"
```

判定逻辑有个很讲道理的细节：

```go
} else if len(proof.failedRelated) > 0 && proof.primaryPassed {
	verificationStatus = "issues_found"
	reportingRule = "The tool reported completion or validity, but these explicit " +
		"verification proofs failed: ... Do not claim completion until they pass."
}
```

**"工具说自己完成了，但旁证说没通过" → 判为有问题。** 这就是不轻信工具自述。

## 五、挂在中间件上，工具作者不用管

```go
func mutationReceiptMiddleware(proxy *RESTProxy) Middleware {
	return func(next MethodHandler) MethodHandler {
		return func(ctx, method, req) (Result, error) {
			result, err := next(ctx, method, req)          // 先执行原工具
			if !isMutationToolName(toolName) { return result, err }
			// 再包一层回执
			fields["mutation_receipt"] = buildMutationReceipt(...)
			call.StructuredContent = fields
			return result, err
		}
	}
}
```

**横切关注点做成中间件**——149 个工具没有一个需要自己写回执逻辑。
判断某个工具是不是"写操作"靠**名字前缀白名单**：

```go
var mutationPrefixes = []string{
	"acquire_", "add_", "apply_", "assign_", "attach_", "batch_", "cancel_",
	"clear_", "compile_", "compose_", "connect_", "create_", "delete_", "derive_",
	"detach_", "discard_", "edit_", "ensure_", "export_", "generate_", "import_",
	"instantiate_", "materialize_", "name_", "publish_", "queue_", "remove_",
	"rename_", "repair_", "replace_", "reuse_", "save_", "seed_", "select_", "set_",
	"stage_", "start_", "unlist_", "update_", "upload_",
}
```

`preview_` 开头的一律**不算写操作**（它们只是预览）：

```go
if strings.HasPrefix(name, "preview_") { return false }
```

## 六、还会往工具描述里注入契约

`addMutationContractToToolList` 在 `tools/list` 时，给每个写工具的描述**追加一段话**：

```go
base := "On success inspect mutation_receipt: write_status only confirms persistence; " +
	"summarize saved values from the tool result, then re-read and validate before claiming gameplay success."

if referenceAware {
	base += " When this call supplies script-bearing fields, " +
		"reference_check=failed or unavailable means the task is unfinished."
}
```

**这意味着 AI 在选工具时就已经看到"别乱说成功"的提醒**，而不是等调用完才看到。

## 七、测试怎么守这些语义

| 测试 | 守什么 |
|---|---|
| `TestMutationReceiptSeparatesPersistenceFromVerification` | `committed` + `not_run` 必须是两个独立值，不能合并 |
| `TestBusinessFailureDoesNotGetASuccessMutationReceipt` | `IsError` 时**不给回执**（不能让失败看起来像成功） |
| 工具描述断言 | 每个写工具的描述里必须含 `mutation_receipt` 字样 |
| 引用检查测试 | `reference_check=failed` 时 `verification_status` 必须是 `issues_found` |

## 八、本库该怎么吸收

这是**本库最缺的东西**。现状：

| 本库现状 | 问题 |
|---|---|
| `kiant-hoi4-lint.py` 只输出错误/警告 | 没有"我验证了没有"的明确声明 |
| 自检全绿就报告"完成" | 全绿只说明我的规则没意见，不说明游戏能跑 |
| 报告里写"已修复" | 没有区分"改了"和"改对了" |

### 最小可行改造

给所有写操作（未来如果有）加一个回执结构：

```python
{
  "write_status": "committed",          # 文件确实改了
  "verification_status": "not_run",     # 没跑任何校验
  "reporting_rule": "文件已写入，但未验证语法和引用。"
                    "只能报告实际写入的值，不要说'已完成'。"
}
```

跑完 lint 后更新：

```python
{
  "verification_status": "syntax_passed",   # 语法过了，但引用没查
  "reporting_rule": "语法检查通过（N 个文件 0 错误）。"
                    "引用完整性和游戏内行为仍未验证。"
}
```

### 更重要的：改措辞

本库现在报告用"已修复""完成""全绿"。按这套思路应该改成：

| 现在说 | 应该说 |
|---|---|
| 已修复 3 个问题 | 改了 3 处，lint 通过，未进游戏验证 |
| 自检全绿 | 209 条静态断言全过，只覆盖规则内可检的部分 |
| 功能可用 | 接口存在且单元测试通过，未在真实项目中验证 |

**这不是自我贬低，是让使用者能准确判断风险。**

## 九、完整判定表（想抄的话照这个写）

| write_status | verification_status | reporting_rule 应向 AI 传达 |
|---|---|---|
| committed | not_run | 只报实际写入值，别说完成 |
| committed | references_passed | 引用都解析成功，但游戏语义未验 |
| committed | verified | 工具声明完成且旁证通过，仅限该范围 |
| committed | issues_found | 有明确问题，别说完成 |
| committed | verification_unavailable | 想验没验成，必须重读并跑 validate |
| partially_committed | issues_found | 分批报成功与失败，绝不说整批完成 |
| no_change | issues_found | 操作返回 ok=false，别说改动生效 |
