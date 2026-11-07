---
title: "hagane-studio 解析器：token 级 trivia 与结构化错误恢复"
domain: 93_ecosystem
repo: https://github.com/hagane-works/hagane-studio
verified_at: 2026-11-06
method: 通读 internal/hoi4/paradox/ 全部 9 个文件 + 测试用例
---

# paradox 解析器

位置：`internal/hoi4/paradox/`，9 个文件约 188 KB。它是整个工具的入口——
所有读游戏文件、读 mod 文件的路径都从这里开始。

**核心差异（对照本库 `mcp-server/cw.py`）**：

| 能力 | cw.py（本库） | paradox（hagane-studio） |
|---|---|---|
| 解析成 AST | ✅ | ✅ |
| 保留注释与空白 | ❌ 全丢弃 | ✅ **token 级携带** |
| 无损写回原文 | ❌ 做不到 | ✅ 字节级一致 |
| 错误恢复 | 收集 errors，尽量继续 | ✅ 结构化 `Recovery`，且重挂 trivia |
| 数值精度 | 字符串原样存 | ✅ `big.Int` + Python 浮点表示 |
| 深度保护 | 256 层 | 1000 层，且有专门测试 |
| fuzz 测试 | ❌ | ✅ 原生 fuzz + 逐字节截断 + 原版语料 |

## 一、trivia：为什么它能无损往返

这是最关键的机制。看 Token 定义（`token.go:3`）：

```go
type Token struct {
	Type   string
	Value  string
	Line   int
	Quoted bool
	Trivia Payload   // ★ 每个 token 自带装饰
}

type Payload struct {
	Leading  []Comment   // 该 token 前面的注释
	Trailing []Comment   // 挂在上一个 token 后面的行尾注释
}
```

`Comment` 不仅存文本，还存**它原本的缩进和列位置**：

```go
type Comment struct {
	Text   string
	Line   int
	Column int
	Inline bool    // 是行尾注释还是独占一行
	WS     string  // 原始空白（Inline 时只存行尾空白，否则存整段前缀）
}
```

### 归属规则

`triviaTracker.record()` 的判定只有一条：

```go
if c.Inline && previous != nil {
    previous.Trailing = append(previous.Trailing, c)   // 行尾注释 → 挂到前一个 token
} else {
    t.pending = append(t.pending, c)                   // 独占行 → 攒着，给下一个 token
}
```

**行尾注释归前面，独占行注释归后面**——这是所有「格式化工具不破坏注释」问题的标准解。

### 效果

读进来再写出去，注释、缩进、空行全部原位保留。这就是它能做"导入已有 Mod → 编辑 → 导出"
而不会把原作者几千行注释冲掉的根本原因。

> **对照本库**：`cw.py` 的 `tokenize` 遇到 `#` 直接跳过，注释彻底消失。
> 我们做"读→分析"没问题，做"读→改→写"就会毁掉原文件。
> 这是本库目前的能力缺口。

## 二、AST 结构：Entry 表达四种形态

```go
type Entry struct {
	Key       *string    // nil = 无名条目（列表项）
	Op        *string    // "=" / "==" / ">" / "<" / ">=" / "<=" / "!="
	Scalar    Scalar     // 标量值（与 Block 互斥）
	Block     *Block     // 块值
	Line      int
	Quoted    bool
	Qualifier *string    // rgb / hsv / RGB / HSV
	Trivia    Payload
}
```

四种形态：
1. `key = value`（Scalar）
2. `key = { ... }`（Block）
3. `{ ... }`（Key 为 nil 的无名块）
4. `key = rgb { 153 0 51 }`（带 Qualifier 的块）

**Qualifier 是引擎的真实语法**——`color = rgb { ... }` 里的 `rgb` 不是键也不是值，
是颜色空间限定符。它只认固定的四个：

```go
var blockQualifiers = map[string]bool{"rgb": true, "hsv": true, "RGB": true, "HSV": true}
```

不在名单里的（比如写错成 `rgba`）**不会被吞掉**，而是当成普通值处理——有专门的测试
`TestParseUnknownQualifierIsNotSwallowed` 守着。

## 三、数值：big.Int + 复刻 Python 浮点

```go
type Scalar struct {
	Kind  ScalarKind  // ScalarStr / ScalarInt / ScalarFloat
	Str   string
	Int   *big.Int    // ★ 用大整数，不是 int64
	Float float64
}
```

为什么用 `big.Int`：HOI4 里有超长 ID 和超大数值，`int64` 会静默溢出。用大整数保证
**读写往返一字不差**。

浮点更讲究——`pyfloat.go` 手写复刻 Python 的 `repr(float)`：

```go
func pyFloatRepr(f float64) string {
	sci := strconv.FormatFloat(f, 'e', -1, 64)
	// exp < -4 或 exp >= 16 → 科学记数法，否则展开
	switch {
	case exp < -4 || exp >= 16:
		out = mant + "e" + pySciExp(exp)
	case exp >= len(digits)-1:
		out = digits + strings.Repeat("0", exp-(len(digits)-1)) + ".0"
	...
}
```

**这是从 Python 版迁移过来的证据。** 整个 `internal/` 里有几十个 `pyXxx` 函数
（`pyUpper` / `pyStrip` / `pyCaseFold` / `pyFloatRepr` / `pyDictValue`…），
全是为了让 Go 实现与老版本 Python 实现产出的文本**逐字节相同**。

> **方法论启示**：重写实现语言时，"行为对齐旧版"和"功能正确"是两件不同的事。
> 前者需要复刻对方的怪癖（Python 的浮点格式化规则就是典型怪癖）。
> 他们选择复刻而不是"改成更合理的格式"，因为已有用户的项目文件不能变形。

## 四、错误恢复：Recovery 而非 panic

```go
type Recovery struct {
	Code    string          // "parser_recovery_stray_rbrace" 等
	Line    int
	Details map[string]any  // 具体上下文（哪个 key、遇到什么终止符）
}

const (
	RecoveryStrayRBrace   = "parser_recovery_stray_rbrace"
	RecoveryEmptyValue    = "parser_recovery_empty_value"
	RecoveryUnclosedBlock = "parser_recovery_unclosed_block"
)
```

三类问题：

| 类型 | 场景 | 处理 |
|---|---|---|
| `stray_rbrace` | 顶层多出一个 `}` | 跳过该 token，**不中断**解析（`parser.go:206`） |
| `empty_value` | `key =` 后面直接 `}` 或 EOF | 造一个空字符串值，记 recovery，继续 |
| `unclosed_block` | 文件结束时还有块没闭合 | 用 EOF 当隐式闭合 |

**关键细节在 `carryRecoveryTrivia`**：跳过坏 token 时，把它身上的 trivia **移到下一个
token 上**，这样注释不会因为恢复而丢失。

这点和本库实测完全一致：原版 14 个文件末尾缺 `}`（引擎容忍），
hagane-studio 也把它当 recovery 而非 error。

## 五、深度保护：1000 层，且被测试钉死

```go
const maxBlockDepth = 1000
```

超过就返回 `ParseError`（不是 stack overflow）。测试写了两个方向：

```go
// 正好 1000 层必须能解析（不能冤枉合法文件）
ast, _, err := Parse(strings.Repeat("a = {", maxBlockDepth))

// 病态嵌套必须是 ParseError，不能是 stack overflow
func TestPathologicalNestingIsAParseErrorNotAStackOverflow
```

**两个方向都测**——只测"能挡住"不测"不误伤"，就会出现"合法文件被拒"的问题。

本库 `cw.py` 用的是 256，偏保守但没测试钉着。

## 六、测试策略：三层，一层比一层狠

### 6.1 单元（`parser_test.go`，20+ 用例）

覆盖到很细：标量种类、比较运算符保留、列表 vs 键值、带限定符的颜色块、
未知限定符不被吞、无名块、空输入、行号正确、三类 recovery 各一组、
以及"嵌套未闭合块每个只报一次"、"EOF 注释不重复"这类**边界交互**。

### 6.2 抗崩溃（`malformed_test.go`）

```go
// 逐字节截断：把源码砍成 0..len 每一种长度，全都不能 panic
for i := 0; i <= len(runes); i++ {
	parseNoPanic(t, "truncated at "+itoa(i), string(runes[:i]))
}
```

还有 Go 原生 fuzz：

```go
func FuzzParseNoPanic(f *testing.F) {
	seeds := []string{"a = 1", ...}
```

### 6.3 原版全量语料（`vanilla_corpus_test.go`）

```go
root := os.Getenv("HOI4_VANILLA_DIR")
if root == "" {
	t.Skipf("SKIPPED (no vanilla install) · set HOI4_VANILLA_DIR to run the full-corpus sweep")
}
```

**没有游戏就跳过（不 fail），有游戏就把原版所有 `.txt` 扫一遍。** 这个设计很实用：
CI 上没有游戏也能过，本地开发机上能跑真语料。

> **这一层最值得本库抄。** 我们的测试全靠自己造样本，从没跑过"原版全部 4892 个 txt 能不能解析"。
> 有了这一层，"解析器改坏了"会在提交前就暴露，而不是等用户遇到奇怪文件。

## 七、本库可以直接借用的三点

### 7.1 给 `cw.py` 加 trivia（如果要支持"改完写回"）

最小可行方案：Token 加 `LeadingTrivia []string`，只在需要保真的路径上启用。
不必一上来就做到字节级，先做到"注释不丢"就有价值。

### 7.2 数值改用 Python 兼容格式化

我们目前所有数值都当字符串原样存——这其实是**优势**（天然无损）。
但如果将来要计算并写回（比如自动加 10%），就必须决定：`0.1 + 0.2` 写成 `0.3` 还是
`0.30000000000000004`？hagane-studio 的答案是**复刻 Python 规则**。

### 7.3 把「原版全量解析」加进自检

```python
# 我们的版本可以这样
if os.environ.get("HOI4_VANILLA_DIR"):
    for f in walk_all_txt(HOI4_VANILLA_DIR):
        cw.parse_file(f)   # 只要求不抛异常
else:
    print("SKIP: 未设置 HOI4_VANILLA_DIR")
```

成本很低，收益是"解析器在 4892 个真实文件上不会崩"这个硬保证。

## 八、差距清单

| 能力 | 本库现状 | 差距等级 |
|---|---|---|
| 解析成 AST | 有，295 行 | 相当 |
| 错误诊断 | 有，但继续解析的能力弱 | 中等 |
| 注释保留 | 无 | **大** |
| 无损写回 | 无 | **大** |
| 大整数 | 无（都用 str） | 小（str 也不丢精度） |
| 深度保护 | 256 层无测试 | 小 |
| fuzz | 无 | 中 |
| 原版语料扫描 | 无 | **大** |
