---
title: "SOL-001 DDS 生成与检查工具"
id: SOL-001
domain: 92_solutions
status: upstream-only
source: skills/hoi4-modding/tools/dds_helper.py
verified_on: 未验证（本插件未实现）
verified_at: 2026-11-06
---

# SOL-001 DDS 生成与检查工具

## 它想解决什么

HOI4 的图标必须是 DDS 格式，但不是任意 DDS 都能读。没有工具时，只能靠 GIMP/Photoshop 插件手转，且格式参数（压缩方式、是否带 alpha、尺寸是否必须 2 的幂）容易搞错。

症状对应：`EB-005 图标被拉伸、偏左、被裁`。

## 思路

上游 `dds_helper.py` 提供三个子命令：

```bash
# 从 PNG 生成 DDS，可指定尺寸
python dds_helper.py make input.png out.dds --width 100 --height 88   # 国策图标尺寸
# 生成纯色占位图（画图标前的临时素材）
python dds_helper.py solid out.dds --width 60 --height 68 --color "#3a6ea5" --alpha 255
# 检查已有 DDS 的头信息是否符合 HOI4 可读
python dds_helper.py check out.dds
```

关键设计点：默认输出 **32-bit 未压缩 DDS**，与原版 UI 图标一致。这一点很重要——很多人默认用 DXT5 压缩，虽然也能用，但边缘会出现失真。

`make` 的 `--width`/`--height` 允许缩放，直接对齐目标槽位尺寸，避免"出图后再拉伸"这个错误做法。

## 为什么没被采用

本插件要求**零第三方依赖**（纯标准库），而生成 DDS 需要写二进制头 + 像素数据，或者依赖 Pillow。当时选择不实现，把这件事留给美术工具链。

但上游实现是纯 Python 手写 DDS 头，理论上可以搬过来不引入依赖——**这一点没验证过**。

## 如果要用，怎么验证

1. 读上游源码 `skills/hoi4-modding/tools/dds_helper.py`，确认它是否依赖 Pillow：

```bash
grep -n "^import\|^from" <上游路径>/dds_helper.py
```

2. 如果只依赖标准库 → 可以自己抄过来改成脚本用
3. 如果有 Pillow 依赖 → 要么装这个依赖，要么用标准库自己写 DDS 头

验证标准：生成的 DDS 放进 mod，游戏内图标正常显示不变形。

## 备注

上游还提供了 `_dds.py`（底层 DDS 读写）和 `item_sprite_check.py`（图标尺寸核对），可能可以一并参考。
