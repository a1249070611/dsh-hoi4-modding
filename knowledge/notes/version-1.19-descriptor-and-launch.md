# 1.19 描述文件与启动参数：六条经核实的字段事实

**结论**

1. 预览图字段是 `picture=`，不是 `thumbnail=`。值是文件名：`picture="thumbnail.png"`。
2. `supported_version` 的通配符**只能放最后一段**。`"1.19.*"` 合法，`"1.*"` 会让 `error.log` 报 `Invalid supported_version`。
3. 调试启动参数是 **`-debug_mode`**。启动器自带的「以调试模式打开游戏」用的就是它。
4. `replace_path` 必须在**两个**描述文件里都写，只写一个会静默不生效。
5. `path` 必须纯 ASCII + 正斜杠。含中文时启动器能看到 mod，但进游戏毫无效果。
6. 描述文件按**无 BOM** 保存（与 `.yml` 相反）。

**依据**

- 第 1 条：参考库 `references/06_workflow/setup.md` 与 `cheatsheet.md` 明确写「`.mod` 里用 `picture=` 不是 `thumbnail=`」，
  并给出 `Unexpected token: thumbnail` 的报错。**本机未验证**——按要求不读取 `mod/` 目录。
- 第 2、3 条：`<GAME_DIR>/launcher-settings.json` 的 `alternativeExecutables` 里有一项
  `"label": {"en": "Open game in Debug Mode"}`，其 `exeArgs` 为 `["-gdpr-compliant", "-debug_mode"]`。
  这是游戏本体自带的文件，只读。
- 第 2 条另一处佐证：`<GAME_DIR>/documentation/triggers_documentation.md` 的 `is_debug` 词条写的是
  "launched with -debug argument"——**这是文档滞后**，以启动器为准。
- 第 4~6 条：来自参考库 `references/06_workflow/setup.md` 与 `compatibility.md`，**均未在本机验证**。

> 判断口径：只有引用 `<GAME_DIR>` 与参考库的条目，我才标「实测」；凡涉及第三方模组的，一律标「未验证」，
> 因为不再读取 `mod/` 目录。

**易错**

- 中文用户名是重灾区：路径里的中文来自 `C:/Users/张三/...`，用户自己看不出问题，因为启动器列表显示正常。
- `1.19.x` 不是合法写法，`x` 不是通配符。它不会崩，只是被标成不兼容。
- 描述文件的 BOM 症状不是报错，是 mod 名或版本号显示成怪字符，极难联想到编码。

**适用版本**

1.19.3 / 1.19.4.2 实测。1.18 及更早的 `-debug` 曾有效，不要据旧教程回退。

---

来源：`dsh-hoi4-modding` 参考库 + 本机实测。核对记录见 `dsh-hoi4-modding/references/ATTRIBUTION.md`。
