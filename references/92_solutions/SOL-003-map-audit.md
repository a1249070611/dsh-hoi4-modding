---
title: "SOL-003 地图一致性审计"
id: SOL-003
domain: 92_solutions
status: upstream-only
source: skills/hoi4-modding/tools/map_audit.py
verified_on: 未验证（本插件未实现）
verified_at: 2026-11-06
---

# SOL-003 地图一致性审计

## 它想解决什么

改地图或加省份时，涉及四份数据必须互相引用一致，任一处不一致都会导致：

- 游戏启动失败（常见于 province 定义缺失）
- 省份存在但不可见
- 战略区域引用不存在的省份
- 建筑写在错误的省份块里

这类错误往往**没有清晰的错误提示**，只表现为"进不去游戏"或"地图上缺一块"。

## 思路

上游 `map_audit.py` 检查四个层面：

| 检查对象 | 查什么 |
|---|---|
| `map/definition.csv` | province id / RGB 颜色 / 类型（陆/海）是否合法、有无重复 id |
| `map/default.map` | `max_provinces` 与实际最大 id 是否匹配；`definitions`、`sea_starts`、`continents` 引用 |
| `map/strategicregions/` | region id 与其中 province 引用是否都存在 |
| `common/buildings.txt` | province 块对应的 province 是否真实存在 |

核心思路是**建立引用图再查孤立节点**：先收集所有 province id，再收集所有引用点，求差集。

## 为什么没被采用

优先级问题。地图修改在 mod 开发中占比不高（多数 mod 用原版地图），而实现它需要理解 `definition.csv` 的位图坐标系、`default.map` 的二进制格式等，工作量不小。

但**"这个能力缺失"是个真实缺口**——一旦有人要改地图，本插件目前帮不上忙。

## 如果要用，怎么验证

1. 读上游 `map_audit.py`，看它处理了哪些边界情况（尤其是 id 空缺号段、海洋省份）
2. 在一个原版地图副本上先跑，确认不报假阳性
3. 故意制造 3 个错误（删一个 province 定义 / 把 strategicregion 指向不存在的 id / max_provinces 改小）验证能全抓出来

验证标准：人为注入的 3 个错误全部命中，且原版数据上 0 报错。

## 备注

**地图类错误的排查成本极高**（改动一次要重启游戏，且报错信息模糊），所以这类审计工具的价值密度远高于它的代码量。

如果有余力补实现，这可能是最值得补的一个（与 SOL-004 字体审计并列）。
