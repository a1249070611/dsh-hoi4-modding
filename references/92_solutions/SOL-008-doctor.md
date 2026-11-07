---
title: "SOL-008 环境体检（doctor）"
id: SOL-008
domain: 92_solutions
status: upstream-only
source: skills/hoi4-modding/tools/doctor.py
verified_on: 未验证（本插件未实现）
verified_at: 2026-11-06
---

# SOL-008 环境体检（doctor）

## 它想解决什么

开工前的三件事，每次都要手工确认，很烦且容易忘：

1. 游戏装在哪（`<GAME_DIR>`）
2. 当前版本多少（`launcher-settings.json` 的 `rawVersion`）
3. 玩家数据目录在哪（`<USER_DIR>`）

忘了确认版本的后果很实际：按 1.19 的写法写，实际跑在旧版本上，报一堆看不懂的错。

## 思路

上游 `doctor.py` 做环境探测，自动查找游戏目录：

```
优先级：HOI4_GAME 环境变量 → launcher-settings.json → Steam libraryfolders.vdf → 常见路径
```

输出：游戏路径、版本号、玩家目录、当前 mod 目录。

**探测链的设计值得注意**：从最明确（环境变量）到最宽松（常见路径猜测），每一层失败才降级到下一层。

## 为什么没被采用

本插件的 MCP 工具大多接受显式路径参数，用户从上下文里给。所以没做统一的环境探测。

**但这带来了一个实际问题**：每个工具都要单独传 `game_root` / `mod_root`，容易传错或不一致。

## 如果要用，怎么验证

1. 读上游 `doctor.py` 的探测顺序与各层实现
2. 在三种环境各跑一次：
   - 正常安装（Steam 默认路径）
   - 自定义路径（改过 libraryfolders）
   - 没装游戏（应该优雅报错，不崩）
3. 确认版本号读取正确（与 `launcher-settings.json` 的 `rawVersion` 一致）

验证标准：三种环境下都能给出正确结论或清晰错误。

## 备注

**这个能力的价值在于「消除隐式假设」。**

本插件多处代码假设 `game_root` 由调用方正确传入。如果传错，症状是"索引建了很多但搜不到东西"或"validate 报 0 个文件"——错得很隐晦。

一个 `doctor` 工具能把这些隐式假设显式化：先确认环境，再干活。**这也是上游 `SKILL.md` 第 0 节「开工前三件事」的工程化落地。**
