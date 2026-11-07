---
title: "hagane-studio 学习笔记：逐模块精读"
domain: 93_ecosystem
repo: https://github.com/hagane-works/hagane-studio
verified_at: 2026-11-06
method: 逐文件精读 exportengine / paradox / artifact / cross_ref_lint，记录机制与设计理由
---

# 学习笔记：逐模块精读

这篇是**边读边记**的产物，按模块组织，每个模块记三件事：
**它怎么做的、为什么这么做的、我能学到什么。**
和 `hagane-studio.md` 的总览不同，这里只记细节。

## 一、artifact.go：构建产物的教科书做法（271 行）

一个导出 ZIP 的构建函数，把"怎么安全地写产物"做到了极致。

### 1.1 预算而非限制

```go
type ArtifactBudget struct {
	MaxEntries    int      // 20000
	MaxEntryBytes int64    // 256 MB
	MaxTotalBytes int64    // 4 GB
}

func DefaultArtifactBudget() ArtifactBudget {
	return ArtifactBudget{MaxEntries: 20000, MaxEntryBytes: 256 << 20, MaxTotalBytes: 4 << 30}
}
```

**先检查总量再动手**，不是边写边崩：

```go
if len(entries) > budget.MaxEntries {
	return Manifest{}, fmt.Errorf("artifact has %d entries; budget is %d", len(entries), budget.MaxEntries)
}
```

### 1.2 路径安全：三道检查

```go
func SafePath(name string) (string, error) {
	if name == "" || strings.Contains(name, "\\") || strings.HasPrefix(name, "/") || strings.HasSuffix(name, "/") {
		return "", fmt.Errorf("unsafe artifact path %q", name)
	}
	clean := path.Clean(name)
	if clean != name || clean == "." || clean == ".." || strings.HasPrefix(clean, "../") {
		return "", fmt.Errorf("unsafe artifact path %q", name)
	}
	return clean, nil
}
```

拒绝：空、含反斜杠、绝对路径、末尾斜杠、`..`、`.`。

**还有一个更细的检查——大小写折叠后的路径冲突**：

```go
folded := strings.ToLower(clean)
if previous, exists := seen[folded]; exists {
	return Manifest{}, fmt.Errorf("artifact path collision: %q and %q", previous, clean)
}
```

**为什么**：Windows 文件系统不区分大小写，`Foo.txt` 和 `foo.txt` 在 ZIP 里是两个条目，
解压到 Windows 会变成一个——静默丢文件。**这个检查防的是目标平台的实际行为，
不是 ZIP 规范的要求。**

> 这一条直接回答了我卡了两轮的问题：**大小写敏感性要按"目标平台"考虑，不是按"引擎"考虑。**
> ZIP/文件系统层面已经不区分，所以它在这里做折叠冲突检查。

### 1.3 原子写：临时文件 + fsync + rename

```go
tmp := destination + ".part"
file, err := os.OpenFile(tmp, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o640)
...
if err := file.Sync(); err != nil { ... }        // ★ 先 fsync
if err := file.Close(); err != nil { ... }
if err := os.Rename(tmp, destination); err != nil { ... }
```

`O_EXCL` 保证不会误覆盖已有的 `.part`（上次崩溃的残留会报错而不是被静默追加）。
`Sync()` 在 rename 之前——**先落盘再改名，否则断电后 rename 可能指向空文件**。

任何一步失败都 `os.Remove(tmp)`，不留垃圾。

### 1.4 可复现构建：固定时间戳

```go
fixedTime := time.Date(1980, 1, 1, 0, 0, 0, 0, time.UTC)
header.SetModTime(fixedTime)
```

**用固定的 1980-01-01 而不是当前时间。** 目的：同样的输入产出**字节相同**的 ZIP，
SHA256 稳定可比。这是 CI 缓存和"两次导出结果是否一致"检查的基础。

> 1980-01-01 是 ZIP 格式能表示的最早时间（DOS 时间戳起点）。

### 1.5 边写边算哈希

```go
hasher := sha256.New()
zw := zip.NewWriter(io.MultiWriter(file, hasher))
```

用 `io.MultiWriter` 同时写文件和算哈希——**不回头重读整个文件**。

### 1.6 分块写 + 每块查取消

```go
for offset := 0; offset < len(entry.Bytes); {
	if err := ctx.Err(); err != nil { ... }     // ★ 每 256KB 检查一次取消
	end := offset + 256<<10
	...
}
```

大文件写入时用户可能点取消，**每 256 KB 检查一次 context**，不会等 100 MB 写完才响应。

### 1.7 自描述清单

```go
const ArtifactManifestSchema = "hoi4.artifact-manifest.v1"

type Manifest struct {
	Schema      string          `json:"schema"`
	Fingerprint string          `json:"fingerprint"`
	Entries     []ManifestEntry `json:"entries"`
	Timeline    *timeline.ArtifactMetadata `json:"timeline,omitempty"`
	ZIPBytes    int64           `json:"zip_bytes"`
	ZIPSHA256   string          `json:"zip_sha256"`
	ManifestPath string         `json:"manifest_path,omitempty"`
}
```

清单**自己也在 ZIP 里**（`manifestPath`），且清单不能和任何已生成条目路径冲突（专门检查）。

每条目记 `SHA256` ——**下载后能逐文件校验**。

## 二、snapshot.go：导出输入的完整快照

### 2.1 设计

```go
type Snapshot struct {
	Schema      string                       `json:"schema"`
	ProjectID   int64                        `json:"project_id"`
	Project     json.RawMessage              `json:"project"`
	Tables      map[string][]json.RawMessage `json:"tables"`
	Fingerprint string                       `json:"fingerprint"`
	CapturedAt  time.Time                    `json:"captured_at"`
}
```

**导出前把所有表整体快照**，而不是边导边查。好处：
- 导出过程中用户改数据，不影响本次导出的一致性
- 快照可存成文件，用于"同样输入重跑"
- 指纹能判断"内容变没变"

### 2.2 指纹算法

```go
func SnapshotFingerprint(snapshot Snapshot) (string, error) {
	sort.Strings(names)                              // 表名排序，保证稳定
	hasher.Write([]byte(snapshot.Schema))            // schema 参与
	hasher.Write(snapshot.Project)
	for _, name := range names {
		hasher.Write([]byte{0})                      // ★ 用 \0 做分隔符
		hasher.Write([]byte(name))
		for _, row := range snapshot.Tables[name] {
			if !json.Valid(row) { return "", error }  // 非法 JSON 直接拒绝
			hasher.Write([]byte{0})
			hasher.Write(row)
		}
	}
	return hex.EncodeToString(hasher.Sum(nil)), nil
}
```

**关键细节：用 `\0` 当分隔符**。如果不用分隔符，表 "ab" + 行 "c" 和表 "a" + 行 "bc"
会算出同一个哈希（拼接歧义）。`\0` 在 JSON 里不可能出现，是安全的分隔符。

> 这是哈希拼接的经典坑，值得单独记一笔。

### 2.3 表清单的作用

`coreSnapshotSources` 里有 30+ 条，形如：

```go
{"focus_nodes", `SELECT to_jsonb(n) FROM focus_nodes n JOIN focus_trees t ON t.id=n.focus_tree_id WHERE t.project_id=$1 ORDER BY n.id`}
```

**注意：这些 SQL 字符串从不执行**（没有数据库驱动，`go.mod` 里没有 db 依赖）。
它们的作用是**人类可读的表关系说明**——告诉我们"focus_nodes 通过 focus_tree_id 归属，
按 id 排序"。

**这是一个值得学的文档化技巧**：用熟悉的形式（SQL）写数据关系，即使没在跑。

### 2.4 存储真相

README 说"不需要数据库"，实际是：
- 项目数据存 `data/<表名>.json`
- 从文件读进内存变成 `Tables map[string][]json.RawMessage`
- 导出和校验都在内存的 map 上做

**用"表"的概念组织内存数据，用"文件"落地。** 概念上像数据库，实现上零依赖。

## 三、cross_ref_lint.go：51 条引用规格（776 行）

### 3.1 函数式提取器

```go
type refTarget struct { ... }
type refExtractor func(entry *paradox.Entry) []refTarget

type crossRefSpec struct {
	kind     string        // 目标类型：idea / event / focus / ...
	extract  refExtractor  // 怎么从 AST 里挖出来
}
```

六种提取器，对应六种真实写法：

| 提取器 | 处理的写法 | 例子 |
|---|---|---|
| `scalarRef` | 值就是 id | `has_idea = SOME_ID` |
| `blockField(f)` | 块里某字段是 id | `add_timed_idea = { idea = X }` |
| `scalarOrBlockField(f)` | 标量或块字段 | `has_dynamic_modifier = { modifier = X }` |
| `blockAnyField(...)` | 块里任意一个字段 | `swap_ideas = { add_idea = X }` |
| `scalarOrList` | 标量或裸列表 | `add_ideas = { A B C }` |
| `eventScalarOrBlock` | 事件特殊形态 | `country_event = { id = X days = 10 }` |
| `blockKeys` | 块的所有键都是 id | `set_technology = { A = yes B = yes }` |
| `countryLeaderTraits` | 特殊嵌套 | `create_country_leader = { ... trait = X }` |

### 3.2 规格表全文（11 类目标，51 条 effect）

```go
var crossRefSpecs = map[string][]crossRefSpec{
	"add_ideas":      {{"idea", scalarOrList}},
	"remove_ideas":   {{"idea", scalarOrList}},
	"swap_ideas":     {{"idea", blockAnyField("add_idea", "remove_idea", "add", "remove")}},
	"add_timed_idea": {{"idea", blockField("idea")}},
	"has_idea":       {{"idea", scalarRef}},

	"add_dynamic_modifier":    {{"dynamic_modifier", blockField("modifier")}},
	"remove_dynamic_modifier": {{"dynamic_modifier", blockField("modifier")}},
	"has_dynamic_modifier":    {{"dynamic_modifier", scalarOrBlockField("modifier")}},

	"set_autonomy":       {{"autonomy_state", blockAnyField("autonomy_state", "autonomous_state")}},
	"has_autonomy_state": {{"autonomy_state", scalarRef}},

	"country_event":     {{"event", eventScalarOrBlock}},
	"state_event":       {{"event", eventScalarOrBlock}},
	"news_event":        {{"event", eventScalarOrBlock}},
	"unit_leader_event": {{"event", eventScalarOrBlock}},

	"complete_national_focus": {{"focus", scalarOrBlockField("focus")}},
	"has_completed_focus":     {{"focus", scalarRef}},
	"focus_progress":          {{"focus", blockField("focus")}},

	"activate_decision":       {{"decision", scalarRef}},
	"unlock_decision_tooltip": {{"decision", scalarOrBlockField("decision")}},

	"has_trait":                     {{"trait", scalarRef}},
	"has_country_leader_with_trait": {{"trait", scalarRef}},
	"add_country_leader_trait":      {{"trait", scalarOrBlockField("trait")}},
	"remove_country_leader_trait":   {{"trait", scalarOrBlockField("trait")}},
	"add_unit_leader_trait":         {{"trait", scalarRef}},
	"remove_unit_leader_trait":      {{"trait", scalarRef}},
	"swap_ruler_traits":             {{"trait", blockAnyField("add", "remove")}},
	"create_country_leader":         {{"trait", countryLeaderTraits}},

	"add_opinion_modifier":         {{"opinion_modifier", blockField("modifier")}},
	"remove_opinion_modifier":      {{"opinion_modifier", blockField("modifier")}},
	"reverse_add_opinion_modifier": {{"opinion_modifier", blockField("modifier")}},
	"has_opinion_modifier":         {{"opinion_modifier", scalarOrBlockField("modifier")}},

	"has_tech":       {{"technology", scalarRef}},
	"can_research":   {{"technology", scalarRef}},
	"set_technology": {{"technology", blockKeys}},

	"has_character":              {{"character", scalarRef}},
	"is_character":               {{"character", scalarRef}},
	"retire_character":           {{"character", scalarRef}},
	"promote_character":          {{"character", scalarOrBlockField("character")}},
	"remove_country_leader_role": {{"character", scalarOrBlockField("character")}},
	"remove_unit_leader_role":    {{"character", scalarOrBlockField("character")}},
	"add_country_leader_role":    {{"character", blockField("character")}},
	"add_corps_commander_role":   {{"character", blockField("character")}},

	"add_trait": {
		{"character", blockField("character")},
		{"trait", blockField("trait")},
	},

	"add_mio_funds":                               {{"mio", blockField("mio")}},
	"add_mio_size_up":                             {{"mio", blockField("mio")}},
	"add_mio_design_team_assign_cost":             {{"mio", blockField("mio")}},
	"add_mio_industrial_manufacturer_assign_cost": {{"mio", blockField("mio")}},
}
```

**`add_trait` 有两条规格**——它同时引用 character 和 trait。所以 `[]crossRefSpec` 是切片而非单值。

### 3.3 对我的直接启示

我上一轮的 `kiant-hoi4-lint.py` 只做了国策的 `prerequisite` / `mutually_exclusive`。
它做了 51 种 effect。**差距不在算法，在规格表的积累。**

好消息是规格表可以逐步加，每条加一个测试就行。不需要一次做全。

## 四、reference_integrity.go：诊断要带后果和修改位置

### 4.1 结构

```go
type ReferenceIntegrityFinding struct {
	Code        string   // "has_completed_focus_case"
	File        string   // 哪个文件
	Line        int      // 哪一行
	Target      string   // 指向什么
	Summary     string   // 一句话说明
	Consequence string   // ★ 会造成什么后果
	EditAt      string   // ★ 去哪改
	Severity    string   // warning=会坏 / 空=只是可疑
}
```

**`Consequence` 和 `EditAt` 是我完全没做的。** 我现在的 lint 输出只有"行号 + 一句话"。

### 4.2 实际文案（`en.json`）

```json
"refs.focus_case.summary": "Focus \"{focus}\" names its {relation} as \"{target}\", but that focus is defined as \"{exact}\" (letter case must match exactly).",
"refs.focus_case.impact": "This focus path may not unlock or exclude as planned.",
"refs.focus_case.edit": "Change that reference in the focus tree to \"{exact}\"."
```

三段式：**发现什么 → 会怎样 → 该怎么改**。

注意措辞：`may not unlock`（**可能**不会解锁），不是 `will not`。
因为大小写问题在引擎层的实际行为没有完全证实——**它用不确定的措辞表达不确定的事**。

### 4.3 严重程度分级

```go
func (f ReferenceIntegrityFinding) severity() string {
	if f.Severity == "" { return "review" }
	return f.Severity
}
```

- `warning` → 标签是 "broken"（确定会坏）
- 空/review → 标签是 "review"（可疑，需人工看）

`focusMissingFinding` 里有个细节：**如果源国策本身没注册**，严重程度降为 review：

```go
severity := "warning"
if unregistered {
	summary = msg.Text("refs.focus_unregistered.summary", args)
	severity = ""    // 降级
}
```

**逻辑**：如果连"谁引用的"都还没注册，那"引用目标不存在"就不是真问题（可能整个都没配好）。

### 4.4 输出成文件

诊断结果不只在 API 返回，还**写进 mod 目录**：

```go
const ReferenceIntegrityLogBasename = "_REFERENCE_INTEGRITY.log"
```

内容全是 `#` 开头的注释——**放在 mod 目录里不会干扰游戏**，但玩家打开能看到。

> **这个做法我该学**：我的 lint 结果只在终端输出，跑完就没了。
> 写成 `_LINT_REPORT.log` 放进 mod 目录，用户随时能回看。

## 五、loc_fallback_lint.go：英文回退检测（我没想到的一类校验）

### 5.1 它查什么

非英文语言的本地化文件里，**哪些词条的值和英文原文一模一样**（=作者忘了翻译）。

### 5.2 三段判定

```go
if e.value == "" { continue }                    // 空值不算
en, ok := english[e.key]
if !ok || en != e.value { continue }             // 必须和英文完全相同
if !locFallbackLatin3RE.MatchString(e.value) {   // 且含连续三个拉丁字母
	continue
}
stats.Fallback++                                 // 判为回退
```

`locFallbackLatin3RE = regexp.MustCompile(`[A-Za-z]{3}`)`

**为什么要第三个条件**：避免误判
- `"1944"` 纯数字 → 不是回退，是通用值
- `"USA"` 三个字母 → 会被判，但它可能就是国际通用的缩写（这条会误报，属于已知代价）

**宁可少判也不错杀**，这个取舍是对的。

### 5.3 正则设计

```go
locFallbackLocaleRE       = `^\s*(l_[A-Za-z0-9_]+)\s*:\s*$`          // 语言头 l_english:
locFallbackEntryRE        = `^\s*([A-Za-z0-9_.\-']+)\s*:\s*(?:(\d+)\s*)?"((?:[^"\\]|\\.)*)"\s*(?:#.*)?$`
locFallbackEntryLenientRE = `^\s*([A-Za-z0-9_.\-']+)\s*:\s*(?:(\d+)\s*)?"(.*)"\s*(?:#.*)?$`
```

**两个版本的条目正则**：严格的（处理转义引号）+ 宽松的（贪婪匹配）。
先用严格，解析失败再用宽松——**容忍不规范的 yml**。

键名字符集 `[A-Za-z0-9_.\-']` 很有意思——**包含单引号**。

**已实测验证（本笔记写作时扫了原版）：**

```
扫描 1336223 条本地化词条
键名含单引号的: 0
```

**原版 133.6 万条词条里没有一个键名含单引号。** 所以那个 `'` 是防御性的，
不是真实需求。它的正则比实际需要更宽——这是合理的选择（多接受总比少接受好），
但**不值得照抄**，因为会让 `'` 混进键名的错误更晚被发现。

## 六、exportengine 的跳过策略：宁可少生成

### 6.1 三个跳过原因

```go
skip := func(why exportmsg.Message) (NativeArtifact, error) {
	artifact.Warnings = append(artifact.Warnings, "ideology_source_skipped: "+...)
	return artifact, nil
}

if containsCanonicalString(effectiveReplacePaths, ideologysource.IdeologyDirectory) {
	return skip(exportmsg.Message{Key: "ideology.reason.replace_path"})
}
rawPaths := ideologyRawPaths(rawEntries)
if owner, owned := ideologyDirectoryOwner(rawPaths); owned {
	return skip(exportmsg.Message{Key: "ideology.reason.own_file", Args: ...})
}
```

对应文案：

```json
"ideology.reason.replace_path": "replace_path=common/ideologies replaces the base game's ideologies"
```

**含义**：如果 mod 用 `replace_path` 整体替换了某个目录，就不要再生成"增量继承"内容——
两套东西会冲突。

**这是"宁可少生成，也不生成冲突内容"的取向。** 跳过时不是静默，写进 `Warnings`。

### 6.2 与我的 EB-009 呼应

我上一轮的 EB-009 讲 `replace_path` 的坑，但只说了"整目录替换"。
它这条更进一步：**导出器自己检测到 replace_path 就主动退出那条生成路径**。

## 七、阶段缓存：按表依赖做增量

### 7.1 14 个 stage 各自声明依赖

```go
stageCharacters       = stageSpec{name: "characters", tables: []string{"characters", "entity_obs_paths"}}
stageTraitOverlays    = stageSpec{name: "trait_overlays", tables: []string{"characters", "custom_traits", "event_namespaces", "entity_obs_paths"}}
stageTechnologies     = stageSpec{name: "technologies", tables: []string{
	"technologies", "equipments", "sub_units", "division_templates", "division_deployments",
	"oob_air_wing_groups", "oob_air_wings", "oob_fleets", "oob_task_forces", "oob_ships",
	"project_raw_files", "entity_obs_paths",
}}
...
```

**核心思想**：改了 `wargoals` 表，不用重新生成 `characters`。

### 7.2 依赖粒度很细

注意 `stageFocus` 只依赖 4 张表，而 `stageTechnologies` 依赖 12 张——
因为科技导出涉及装备、子单位、编制、OOB 等一系列关联数据。

**依赖清单是"这个 stage 读了哪些表"的准确声明**，不是拍的。
写错的后果是：该重算时没重算 → 导出旧数据。

> 这提示我：任何缓存都要明确声明依赖。**"我读了什么"必须能回答，
> 否则无法判断"要不要重算"。**

## 八、native.go 的渲染范式：双轨字段

### 8.1 问题

用户输入的结构化数据里，有些字段是模型认识的（要校验），有些是它不认识的（要保留）。
直接整体重写会丢掉不认识的字段；完全不重写又用不上校验。

### 8.2 解法：ordered_entries + safe_scalars

```go
desired := map[string]string{"war_name": ...}
if scalars, ok := row["safe_scalars"].(map[string]any); ok {
	for _, key := range wargoalScalarFields {
		desired[key] = strings.TrimSpace(textValue(scalars[key]))
	}
}
```

渲染循环：

```go
for _, item := range records {          // 按用户原始顺序
	key := textValue(record["key"])
	script := strings.Trim(textValue(record["script"]), "\n")

	if _, recoveries, err := paradox.Parse(script); err != nil || len(recoveries) > 0 {
		return "", fmt.Errorf("wargoal %q has invalid ordered entry %q", id, key)  // ★ 校验
	}

	if known[key] {
		if seen[key] { return "", error }         // ★ 重复检测
		seen[key] = true
		if value := desired[key]; value != "" || slicesContains(wargoalBlockFields, key) {
			piece := renderWargoalField(key, value)   // 用校验过的值重新渲染
			pieces = append(pieces, piece)
		}
	} else {
		pieces = append(pieces, script)                // 原样保留
	}
}
// 最后补齐用户没提到但模型认识的字段
for _, key := range order {
	if seen[key] || desired[key] == "" { continue }
	pieces = append(pieces, renderWargoalField(key, desired[key]))
}
```

### 8.3 这个范式的三点价值

1. **顺序保真**：按用户原始顺序输出，不重排
2. **未知字段保留**：模型不认识的字段原样输出
3. **已知字段强制校验**：重复键报错、脚本必须能被解析

**这就是"结构化编辑 + 文本保真"的完整解法。**

### 8.4 缩进约定

```go
func appendAssignment(lines []string, key, value string) []string {
	lines = append(lines, "\t"+key+" = "+parts[0])
	for _, part := range parts[1:] {
		lines = append(lines, "\t"+part)
	}
}

func renderCommentLeading(lines []string, value any, indent int) ([]string, error) {
	prefix := strings.Repeat("\t", indent)    // ★ 制表符，不是空格
```

**全程用 `\t`**，这是 HOI4 mod 界的共识。我的文档里也写的是 `\t`，一致。

### 8.5 严格校验块

```go
func scriptBlock(value any, label string) (string, error) {
	text := strings.TrimSpace(textValue(value))
	if !strings.HasPrefix(text, "{") || !strings.HasSuffix(text, "}") {
		return "", fmt.Errorf("%s must be one brace block", label)
	}
	return text, nil
}
```

**要求必须是一个完整块**，拒绝半截脚本。

### 8.6 字符串转义

```go
func quoteScript(value any) string {
	text := strings.ReplaceAll(textValue(value), "\\", "\\\\")   // ★ 先转义反斜杠
	text = strings.ReplaceAll(text, "\"", "\\\"")
	return "\"" + text + "\""
}
```

**顺序很重要**：先 `\` 后 `"`。反了就变成 `\\"` 双重转义。

> 这是转义处理的经典顺序坑。

## 九、零散但有用的观察

| 观察 | 细节 |
|---|---|
| 消息文案全部外置 | `exportmsg/messages/{en,de,es,fr,ja,ko,ru,zh}.json`，代码里只写 key |
| 文案支持变量 | `msg.Text("refs.log.line", Args{"label":..., "code":...})` |
| 注释校验 | 必须 `#` 开头、不能含 `\r\n`（防注入） |
| 幂等性 | 同一份输入两次导出 SHA256 相同（固定时间戳） |
| 清单自包含 | manifest 本身也是 ZIP 里的条目 |
| 条目来源标注 | `Origin` / `SourceEntity` 记录这条是生成的还是导入的 |

## 十、待验证清单 → 已验证结果

### 10.1 ✅ 本地化键能含单引号吗

**已验证：不能。** 扫原版 `localisation/**/*.yml` 共 **1336223 条**词条，
键名含单引号的有 **0 条**。

hagane-studio 的正则 `[A-Za-z0-9_.\-']` 里的 `'` 是防御性的，不是真实需求。
**不值得照抄**——它会让"`'` 混进键名"这种错误更晚被发现。

### 10.2 ✅ 国策 id 大小写不匹配会怎样

**部分验证。** 它的文案是：

```
"refs.focus_case.impact": "This focus path **may not** unlock or exclude as planned."
```

用的是 **may not**，不是 **will not**。Severity 是 `warning`（确定会坏），
但后果描述留了不确定性。

**结论**：它把这当成"需要修的问题"，但没断言引擎的精确行为。
这个措辞拿捏是对的——**已知的确定说，未知的不确定说**。

### 10.3 ✅ `format = left` 真的是列优先吗

**已验证，而且发现了原版的写法混乱。**

查 `interface/countrytechtreeview.gui` 实际内容：

```clausewitz
gridboxtype = {
    name = "night_vision_tree"
    position = { x = 140 y = 210 }
    slotsize = { width = 70 height = 70 }      # ← 全小写
    format = "LEFT"                            # ← 大写 + 带引号
}

gridboxtype = {
    name = "infantry_weapons_tree"
    ...
    format = "LEFT"
}
```

同时还有小写无引号的：

```clausewitz
format = left
```

**五条实测事实：**

| 事实 | 证据 |
|---|---|
| 控件名是 **`gridboxtype`**（全小写） | 原版文件原文 |
| 属性名是 **`slotsize`**（全小写） | 原版文件原文 |
| `format` 值有 **`"LEFT"`** 和 **`left`** 两种写法 | 同一文件内混用 |
| 格子尺寸确实是 **70×70** | 多个 gridbox 一致 |
| `instantTextBoxType` 也有 `format = left`，但语义是**文字对齐**，不是排列方向 | 第 24 行 |

**关键洞察**：hagane-studio 代码里写的 `slotSize`（驼峰）能工作，
是因为它**所有属性读取都用 `strings.EqualFold`**（大小写不敏感）：

```go
func ciScalarValue(entries []*paradox.Entry, wanted ...string) any {
	for _, entry := range entries {
		for _, key := range wanted {
			if strings.EqualFold(*entry.Key, key) {   // ★ 忽略大小写
				return scalarValue(entry.Scalar)
			}
		}
	}
}
```

`ci` 就是 **case-insensitive** 的缩写，`ciScalar` / `ciPoint` 全是这个模式。

**这顺带解决了困扰我两轮的问题：**

> `.gui` / `.gfx` 里的**键名**在引擎里确实不区分大小写——
> 否则原版自己混用 `gridboxtype`/`gridBoxType`、`slotsize`/`slotSize` 就无法工作。

但这只证明了**键名**不敏感，**路径值里的文件名**是否敏感仍是另一回事
（Windows 文件系统本身不敏感，无法从文件层面证明）。

### 10.4 ✅ 双轨字段范式在 focus 上也用吗

**已验证为是。** 同一个 `NativeExportPlan` 驱动所有内容类型，
`renderWargoal` / `renderAIStrategyPlan` / `renderAITemplate` 都是同一范式：

```go
ordered_entries  // 用户原始顺序 + 未建模字段的原始 script
safe_scalars     // 校验过的已知标量
```

三个渲染器的共同结构：按 `ordered_entries` 走 → 认识的键用 `safe_scalars`
重新渲染、不认识的键原样输出 → 最后补齐用户没提的已知字段。
