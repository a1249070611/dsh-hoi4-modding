---
title: "EB-006 顶栏或窗口挂不上自定义 GUI"
id: EB-006
domain: 91_error-book
symptom_class: 界面显示
severity: 一般
verified_on: 1.19.x
verified_at: 2026-11-06
first_seen: scripted GUI 顶栏接入
related: [05_presentation/scripted-gui.md, 05_presentation/advanced-interface.md]
---

# EB-006 顶栏或窗口挂不上自定义 GUI

## 症状

自己写的 `.gui` 窗口，想做顶栏按钮或挂进某个容器，结果：完全不显示、显示在屏幕左上角、位置错乱、点了没反应。

## 错误做法（我试过的）

1. 以为是 `position` 坐标不对，反复调 → 挪到正确坐标也挂不上
2. 以为是 sprite 缺失 → 补了 icon 还是不显示
3. 直接复制原版某个窗口的整段，改名字 → 有的能成有的不能，不知道为什么

## 根因

`containerWindowType` 有几个字段是**约定而非自由参数**：

| 字段 | 约束 |
|---|---|
| `name` | 必须与挂载点期望的名字匹配。顶栏挂载有特定名字约定 |
| `positionType` | 决定它相对什么定位。写成 `center`/`top_left` 等，语义固定 |
| `orientation` | 影响子元素排布方向 |

如果 `name` 不符合挂载点约定，引擎**不会报错，只是不挂**。

## 标准化方案

1. **不要从零写。** 找原版里功能相同的窗口，整个复制过来，再改内容。这是唯一可靠的方法。

```bash
# 找原版同类窗口
grep -rn "containerWindowType" <GAME_DIR>/interface/*.gui | head -20
```

2. 对照原版的三件套字段（`name` / `positionType` / `orientation`），保持一致，只改显示内容。

3. 顶栏挂载读 `05_presentation/scripted-gui.md` 的挂载约定章节。

3. **大小框三件套尺寸别自定义**：背景 / 大框 / 小框是配套的固定尺寸，改一个就要重排全部。

## 预防

- 新 GUI 一律从原版复制改造，不手写骨架
- 改名前 grep 一遍目标名字是否已被使用

## 验证

进游戏看目标位置是否出现、点击是否有响应。

## 备注

**这条的本质是「约定优于配置」**：字段名看着像自由参数，实际有效值被挂载点写死了。原版文件是唯一权威——文档里未必写，但原版一定用了对的写法。
