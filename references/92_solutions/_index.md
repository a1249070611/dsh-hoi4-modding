---
title: 解决方案参考索引（思路池 / 未验证线索）
domain: 92_solutions
scope: index + 使用协议
verified_on: 1.19.x
verified_at: 2026-11-06
---

# 92_solutions — 解决方案参考

> **这个目录和错题本的区别，一句话说清：**
>
> - `91_error-book/` = **已经验证过**的标准答案。「这个坑我踩过，这么修」。
> - `92_solutions/` = **还没验证**的思路池。「也许可以这么试，不知道行不行」。
>
> 错题本里每条都有实证。这里每条都可能错。**用的时候必须自己验证。**

## 为什么要这个目录

上游旧插件（`dsh-hoi4-modding`）有一套 30 个 CLI 命令的工具链，本插件把它改造成了 17 个 MCP 工具。改造过程中有约一半命令没有迁移。

这些没迁移的东西**不一定没用**——它们可能是：
- 好想法但当时没时间实现
- 实现得不够通用，换个项目就不好使
- 有更适合的场景，只是当前用不上
- 干脆就是错的

**在没验证之前，不应该丢掉，也不应该当作能用。** 所以一条一条列在这里，标明来源、思路、状态。

## 状态标记

每条必须有状态，不许空着：

| 状态 | 含义 | 怎么用 |
|---|---|---|
| `idea` | 只有思路，没实现过 | 从零做起，参考它的设计意图 |
| `upstream-only` | 上游有完整实现，本插件没迁 | 可直接去上游源码抄（给了路径） |
| `suspect` | 怀疑有问题 | 先验证它的前提是否成立 |
| `rejected` | 验证过，确认不可用 | 别再试，条目留着说明为什么不行 |
| `promoted` | 已验证可用，已固化为错题本条目或工具 | 看指向哪里 |

## 一、旧插件未迁移的工具（upstream-only）

这些在上游有完整实现，源码路径在 `skills/hoi4-modding/tools/`。

| ID | 工具 | 思路 | 状态 |
|---|---|---|---|
| [SOL-001](SOL-001-dds-helper.md) | `dds_helper.py` | DDS 生成/纯色占位/头检查，解决"没有工具就出不了 DDS" | `upstream-only` |
| [SOL-002](SOL-002-tech-icon-import.md) | `tech_icon_import.py` | 照片→科技卡图标，含去背、安全区、卡片预览自检 | `upstream-only` |
| [SOL-003](SOL-003-map-audit.md) | `map_audit.py` | province/state/strategicregion 引用一致性 | `upstream-only` |
| [SOL-004](SOL-004-font-audit.md) | `font_audit.py` | 找出 GUI 里用了没有中文分片的字体名 | `upstream-only` |
| [SOL-005](SOL-005-tank-designer-layout.md) | `tank_designer_layout.py` | 生成 16/18 槽坦克设计器 GUI | `upstream-only` |
| [SOL-006](SOL-006-install-mod.md) | `install_mod.py` | 把开发目录的 mod 安装到玩家数据目录 | `upstream-only` |
| [SOL-007](SOL-007-tech-available-patch.md) | `tech_folder_available.py` | 批量修补 `technology_tags` 里的 `has_country_flag` | `upstream-only` |
| [SOL-008](SOL-008-doctor.md) | `doctor.py` | 环境体检：游戏在哪、版本多少、路径对不对 | `upstream-only` |
| [SOL-009](SOL-009-reference-build.md) | `build_reference.py` | 从游戏 `documentation/` 生成 effect/trigger 速查表 | `upstream-only` |

## 二、写 mod 时想过但没走通的思路

这些是**做 mod 本身**的思路，不是做工具的。状态为 `rejected` 的是已经验证过
确实不行的，别再去试。

| ID | 思路 | 为什么可疑 | 状态 |
|---|---|---|---|
| [SOL-012](SOL-012-replace-path-for-patch.md) | 用 `replace_path` 实现"只改几项" | 它是整目录替换，会删掉原版其他内容 | `rejected` |

## 三、待验证的思路（idea）

想到但完全没动手的。

| ID | 思路 | 可能价值 |
|---|---|---|
| — | 见 `99_plugin-devlog/DEVN-*` | 开发插件本身的思路不在 mod 方案库里 |

> 开发这个插件时想过但没走通的思路（全量重建索引、脚本直传资料库等），
> 记在 `99_plugin-devlog/`，不在这里。原因很简单：那些思路解决的是「怎么写这个工具」，
> 不是「怎么写 mod」。混在一起会让方案库的检索结果里出现一堆与 mod 无关的条目。

## 四、使用协议

**遇到问题时：**

```
1. 先在 91_error-book/ 查（已验证的答案）
2. 没有 → 来这里，按「症状相关的域」扫一遍状态列
3. 命中 upstream-only → 去上游源码抄实现，抄完验证
4. 命中 idea/suspect → 当作假设去做实验，不要当作方案直接执行
5. 验证完 → 不管成不成，都回来更新这条的状态
```

**验证完必须回写状态。** 这是这个目录存在的意义——如果状态不更新，它就退化成一份"不知道有没有用的清单"，和没有一样。

- 验证可用 → 状态改 `promoted`，并注明"已固化为 EB-xxx / 已实现为某工具"
- 验证不可用 → 状态改 `rejected`，**写清为什么不行**，防止以后有人重试
- 暂时没结论 → 保持原状态，补一行"试到哪一步了"

## 五、条目格式

```markdown
---
title: "SOL-NNN 一句话思路"
id: SOL-NNN
domain: 92_solutions
status: idea | upstream-only | suspect | rejected | promoted
source: 上游路径 / 自己的想法 / 某次排障
verified_on: 未验证 | 1.19.x
verified_at: YYYY-MM-DD
---

# SOL-NNN 一句话思路

## 它想解决什么

具体痛点。不要写"提升效率"这种废话。

## 思路

怎么做的。有上游实现就给源码路径和关键函数。

## 为什么没被采用 / 不确定在哪

诚实写。是没时间？是设计有问题？是场景不合适？

## 如果要用，怎么验证

给可执行的验证步骤。**这条必须有**，否则这个条目没法被推进。
```

## 六、维护约定

- **状态不许留空。** 空状态等于没状态
- **`rejected` 的条目不要删。** 它的价值在于"阻止后人重试"，删了就白踩一次
- **别把已验证的东西留在这里。** 验证通过就迁去 `91_error-book/` 或做成工具，这里只留过程
- **条目可以很短。** 一句话思路也行，但「怎么验证」不能省
