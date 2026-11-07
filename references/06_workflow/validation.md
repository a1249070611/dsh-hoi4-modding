---
title: 校验（分层方法论 / auto-check 门禁）
domain: 06_workflow
scope: workflow
verified_on: 1.19.x
verified_at: 2026-11-06
---

# 校验：从 lint 到门禁

> 目标：把「靠肉眼和进游戏试」变成「分层检查 + 一条命令跑完」。每一层都能单独跑，门禁层把它们串成一次执行、分项给结论。

## 0. 为什么必须分层

HOI4 的失败方式大多是**静默**的：没有 gridbox 的科技不画、loc key 缺了直接显示 key 原文、sprite 没注册只是空白、`available` 写错整页变灰但日志干净。所以校验要按「能不能在文件层判定」分层——能静态判定的尽量前移，运行时只留观察。

| 层 | 判定对象 | 代价 | 可靠性 |
|---|---|---|---|
| L1 语法 | 文件形状 | 毫秒 | 高（确定性规则） |
| L2 引用 | 名字/路径是否两边都有 | 秒 | 高 |
| L3 语义 | 内容系统的结构关系 | 秒~分钟 | 中（需要规则编码） |
| L4 运行 | 引擎实际行为 | 分钟（要启动游戏） | 最高，但只能抽样 |
| L5 门禁 | 以上四层的执行与报告 | — | 取决于前四层 |

## 1. 五层模型

| 层 | 查什么 | 手段 | 典型能发现 | 发现不了 |
|---|---|---|---|---|
| L1 语法 | 花括号平衡、`key = value` 形状、编码矩阵、`.mod` 字段 | `scripts/hoi4_lint.py`、`pdx_parser.py` | 括号不配对、`thumbnail=`、`1.*` 版本号、`.yml` 缺 BOM | 任何逻辑错误 |
| L2 引用 | 本地化 key、GFX sprite、图标文件、ID 命名空间 | grep + `item_sprite_check.py`、`tech_tree_audit.py` | loc key 未定义、sprite 未注册、贴图路径不存在 | 引用对了但语义错 |
| L3 语义 | 科技挂载链、国策连线、装备 archetype、scope 链 | `tech_tree_audit.py`、`tech_folder_available.py`、`tank_designer_probe.py`、自写拓扑检查 | 科技无 folder/gridbox、prerequisite 悬空或成环、`module_slots` 未定义 | 数值平衡、AI 行为 |
| L4 运行 | error.log、崩溃 `LastRead`、控制台 | `errorlog_triage.py`、`-debug_mode`、`-crash_data_log` | 加载期数据结构错、GUI 缺 sprite、事件 target 无效 | 需要特定玩家操作才走到的路径 |
| L5 门禁 | 把 L1–L4 串成一次执行 | 自建 `auto_check`（见 §6） | 回归、发布前遗漏 | — |

## 2. L1 语法层

五条都能脚本化：

1. `{}` 平衡——先剥离字符串与注释再计数（`#` 行注释、`"..."` 字符串里的括号不算）。
2. 顶层键白名单——`focus_tree` / `country_event` / `ideas` / `technologies` / `equipments` …；出现未知顶层键，通常是把内容放错目录或键拼错。
3. 编码矩阵——`.yml` 必须 UTF-8 **带 BOM**；`.txt` / `.gui` / `.gfx` / `.mod` / `descriptor.mod` 必须 UTF-8 **无 BOM**。GBK/ANSI 文件要报「编码错」，不要报成「语法错」（否则你会去改括号）。
4. `.mod` 字段——`picture=`（不是 `thumbnail=`）、`supported_version` 通配符只能在最后一段、`path` 用 `/` 且纯 ASCII。
5. DDS 头——尺寸与压缩格式（`scripts/dds_helper.py check`）。

```bash
python scripts/hoi4_lint.py <mod 目录>
python scripts/hoi4_lint.py <mod 目录> --json     # 机器可读，给门禁用
```

## 3. L2 引用层（四张存在性表）

### 3.1 本地化 key

- 定义集合：`localisation/**/*.yml` 里的 `key:` 行（注意每个语言目录都要有，且 BOM 正确）。
- 引用集合：脚本与 GUI 里当作 loc 用的标识——`title =`、`desc =`、`name =`、`tooltip =`、focus/idea/decision 的名字、事件 option 名。
- 只把「**引用但未定义**」报 FAIL；「定义未引用」降为 warning（原版有大量共用 key）。

### 3.2 GFX sprite

- 定义：`interface/**/*.gfx` 里的 `spriteType = { name = "GFX_x" texturefile = "gfx/..." }`。
- 引用：`.gui` 的 `spriteType = "GFX_x"`、脚本里的 `icon = GFX_x` / `picture = GFX_x`。
- 两边都要有；`texturefile` 指向的文件还必须真实存在（见 3.3）。

### 3.3 图标 / 贴图文件

- `texturefile` → 文件存在性 + 扩展名（`.dds` / `.tga`）+ 头信息尺寸。
- 尺寸要符合控件比例。**具体目标尺寸是项目选择，不是通用规则**（例如科技卡图标尺寸的推导见 `../90_case-studies/icon-pipeline-tech-card.md`）。
- 批量检查：`scripts/item_sprite_check.py`（sprite 引用 / 文件 / 头信息三合一）。

### 3.4 ID 与命名空间

- `add_namespace` 是否存在、事件 `id` 是否落在 namespace 内、`id` 是否跨文件重复（重复 = 后加载者覆盖前者，且通常不报错）。
- 科技 `folder` 名是否在 `common/technology_tags/` 注册（挂载链见 §4.1）。

## 4. L3 语义层（按内容系统分）

### 4.1 科技挂载链（「页面在、内容不显示」的第一嫌疑）

按顺序每环都要成立：

```
tech 定义
 → folder { name, position }
 → common/technology_tags/ 注册
 → countrytechtreeview.gui：<folder> 容器 + tab
 → gridboxtype <root>_tree        （缺失＝「科技不画」，日志仅一行 Found no grid box for tech）
 → item 模板（大框 techtree_<folder>_item / 小框三件套 _small_item）
 → 背景 sprite GFX_technology_<folder>_<state>_item_bg（+ _small_ 变体）
```

检查项：folder 名一致性、同页 `position` 是否落在统一网格、`available` 用的是 `original_tag` 还是 `has_country_flag`（后者会导致方框在、连线全无、日志干净）。完整配方与实测结论见 `../90_case-studies/tech-tree-gridbox.md`（案例）；通用字段语义看 02_content 的科技页文档。

### 4.2 国策连线

- 每个 `prerequisite` / `mutually_exclusive` 指向的 focus id 必须存在；
- 依赖图无环（对 `prerequisite` 做拓扑排序）；
- 两个 focus 是否占了同一个 `x,y`（同坐标会叠在一点）；
- `icon` 对应的 `GFX_focus_*` 与 `*_shine` 是否都存在。

### 4.3 装备与模块

- `archetype` / `is_archetype` 引用存在，且「克隆」类写法在被复制对象之后求值；
- `module_slots` 里每个 slot 名在 `common/units/equipment/` 的 slot 定义里存在；
- `allowed_module_categories` / `gui_category` 指向的 category 已定义（category 常隐式创建，拼错也静默）；
- `module_count_limit` 的互斥组是否自相矛盾。

### 4.4 scope 链与事件目标

- `country_event = { id target }`、`every_country` 内直接写 state 效果之类，都是「scope 不匹配」的高发点；
- 同一行脚本在加载期（`[no_game_date]`）和运行期（带游戏日期）的语义不同；
- 静态只能扫「可疑 scope 变换」，精确判定交给 L4。

## 5. L4 运行层：error.log 三件套

固定三件，缺一不可：

1. **基线计数**：未改动/空 mod 时的日志行数（原版噪声本底）。
2. **加载期行**：`[no_game_date]`——描述文件、数据结构、GFX 定义。
3. **游戏内行**：带游戏日期的、且命中你的 ID 前缀或文件路径。

```bash
python scripts/errorlog_triage.py "<用户目录>/logs/error.log"   # 分类 + 计数
```

判读三条规则（虚拟根路径 / 两种时间戳 / `invalid event target`）见 [debugging.md](debugging.md) §4.3。

门禁里把 L4 做成：**同一操作录两次（改动前/后），只比「新增类别」与「新增行」**，绝不要求总数下降。

## 6. L5 门禁层：auto-check 脚本的设计契约

目标：开发者与 CI 一条命令拿到「分项 PASS/FAIL + 退出码」，不读日志也能判断能不能发。

### 6.1 输出 schema

```json
{
  "schema": "hoi4check/1",
  "mod": "<name>",
  "checks": [
    {"id": "syntax.braces", "layer": "L1", "status": "PASS", "severity": "error",
     "message": "", "evidence": ["common/technologies/a.txt:12"]}
  ],
  "summary": {"pass": 18, "fail": 0, "skip": 2, "error": 0}
}
```

- `id` 稳定（`层.对象.规则`），CI 才能按 id 忽略或加白；
- `status ∈ {PASS, FAIL, SKIP, ERROR}`：`SKIP` = 环境不具备（如没有游戏目录、没装 Pillow），`ERROR` = 检查器自身崩了——**两者都不算通过**；
- `severity ∈ {error, warning, info}`：只有 `error` 影响退出码；
- `evidence` 必填：`文件:行号` 或可复现命令.

### 6.2 行为契约

1. **默认只读**；写操作（`--apply` / `--fix`）必须显式开启并先备份。
2. **幂等**：同一输入跑两次，结论一致、无副作用。
3. **可降级**：缺游戏目录/缺依赖时对应检查变 `SKIP` 并给原因，不要静默 PASS，也不要整条命令崩。
4. **可分段**：`--only L1,L2`、`--fast`（语法+引用，目标 <2s）、`--full`（+语义）、`--runtime <log>`。
5. **基线 diff**：`--baseline <json>` 只报「新增 FAIL」，适合放进提交钩子。

### 6.3 退出码

| 码 | 含义 |
|---|---|
| 0 | 全部 PASS 或 SKIP（warning 不阻塞） |
| 1 | 至少一个 `severity=error` 的 FAIL |
| 2 | 用法错误 / 环境缺失（参数错、找不到 mod、Python 版本低） |
| 3 | 检查器内部错误 / 写操作被拒（权限、备份失败） |

### 6.4 反模式

- 只有退出码没有分项 → 出问题只能重跑加 print。
- 把原版噪声当 FAIL → 门禁永远红，最后没人看。
- 检查器自己抛异常被当成「没发现问题」→ 必须显式 `ERROR`。
- 依赖本机绝对路径/固定用户名 → 换机器即废；路径一律来自参数或统一的目录探测。
- 与文档字面量强耦合（断言某篇 md 必须出现某句话）→ 文档一改测试就红；应断言行为与结构。

### 6.5 最小骨架

```python
#!/usr/bin/env python3
# 只读、分项、--json、退出码按 6.3
import argparse, json, sys
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Result:
    id: str
    layer: str
    status: str                  # PASS / FAIL / SKIP / ERROR
    severity: str = "error"      # error / warning / info
    message: str = ""
    evidence: Optional[list[str]] = None

def run_all(mod: str, only: Optional[str]) -> list[Result]:
    ...                          # 每一项检查都返回一个 Result

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mod")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only", default=None)
    ap.add_argument("--baseline", default=None)
    a = ap.parse_args(argv)
    results = run_all(a.mod, a.only)
    if a.json:
        print(json.dumps({"schema": "hoi4check/1", "mod": a.mod,
                          "checks": [asdict(r) for r in results]},
                         ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"[{r.status}] {r.id:28} {r.message}")
    if any(r.status == "ERROR" for r in results):
        return 3
    return 1 if any(r.status == "FAIL" and r.severity == "error" for r in results) else 0

if __name__ == "__main__":
    sys.exit(main())
```

## 7. 与其它文档的关系

- 为什么静默失败这么多、日志怎么读 → [debugging.md](debugging.md)
- 发布前必须过的 8 项 → [publishing.md](publishing.md)（≈ 门禁的 L1 + L2 子集）
- 大版本升级后要重验的 5 件事 → [migration.md](migration.md) §7

## 8. 自检清单

- [ ] L1 能不能在 2 秒内跑完（提交前每次都跑）？
- [ ] loc key / sprite / 图标文件三类引用都有「定义 ↔ 引用」双向检查？
- [ ] 科技挂载链的五个环节，缺哪一环会被检查报出来？
- [ ] 门禁有稳定的分项 `id` 吗？CI 能定位到具体规则吗？
- [ ] `SKIP` 和 `ERROR` 有没有被当成 `PASS`？
- [ ] 是否默认只读、写操作要求显式开关 + 备份？
- [ ] 是否用「基线 + 新增」对比，而不是要求 error.log 清零？
