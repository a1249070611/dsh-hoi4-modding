# broken_mod —— 故意写坏的对照样本

这个模组**不应该被修好**。它是一份可执行的反向文档：每个文件注入一类经典的 HOI4 缺陷，
`mcp-server/selftest.py` 逐个断言它们被对应的检查逮住、且等级正确。

想知道某个校验器到底在查什么，读这里比读代码快。

## 缺陷清单

| # | 文件 | 注入的问题 | 应当被谁发现 | 期望等级 |
|---|---|---|---|---|
| 1 | `descriptor.mod` / `broken_mod.mod` | `supported_version="1.19.x"` | `descriptor` | error |
| 2 | `localisation/english/broken_l_english.yml` | 没有 UTF-8 BOM（整个文件被游戏忽略） | `localisation` | error |
| 3 | `common/ideologies/broken_ideologies.txt` | 少一个右花括号 | `syntax` | error |
| 4 | `common/national_focus/broken_focus_dup.txt` | `BAD_focus_a` 与 `broken_focus.txt` 里的 id 撞车 | `duplicates` | error |
| 5 | `common/national_focus/broken_focus.txt` | `BAD_focus_b` 没有本地化键 | `localisation` | error |
| 6 | `events/broken_events.txt` | 没有 `add_namespace`，事件不注册 | `localisation` | error |
| 7 | `events/broken_events.txt` | 事件标题/正文键缺失 | `localisation` | error |
| 8 | `events/broken_events.txt` | 选项没有 `name`，也找不到 `BAD.1.a` | `localisation` | warn |
| 9 | `interface/broken_sprites.gfx` | `texturefile` 指向不存在的 `.dds` | `assets` | info* |
| 10 | `events/broken_events.txt` | `picture` 引用了未注册的 sprite | `sprites` | info* |
| 11 | `common/technologies/broken_techs.txt` | `leads_to_tech` 指向不存在的科技 | `technology` | info* |
| 12 | `common/technologies/broken_techs.txt` | 科技缺本地化名与 `_desc` | `technology` | warn |
| 13 | `broken_mod.mod` | 预览图字段写成 `thumbnail=`，应为 `picture=` | `descriptor` | warn |
| 14 | `broken_mod/descriptor.mod` | 描述文件带 UTF-8 BOM（与 `.yml` 要求相反） | `descriptor` | warn |
| 15 | `broken_mod.mod` | `replace_path` 只写在外层，内层没写 → 静默不生效 | `descriptor` | warn |

\* 标 info 的三条是「证据不足时的正确行为」：没索引原版，工具分不清是拼错还是原版本来就有。
索引原版后它们会升级为 error —— `selftest.py` 里专门有一项断言这个升级。

第 13~15 条是 2.2.0 加的：都是「文件看起来完全正确、游戏也不报错，但就是不生效」的类型。
它们不致命，所以给 warn 而不是 error —— 单条 `thumbnail=` 在真实 mod 里也有 1/29 的出现率，
说明它至少不崩游戏，只是预览图不显示。

## 怎么用

```bash
cd mcp-server
python selftest.py                                        # 全自动
python server.py --call kiant_hoi4_validate_mod '{"mod_path":"../examples/broken_mod","deep":true}'
```

把 `broken_mod` 和 `broken_mod.mod` 一起拷进
`文档/Paradox Interactive/Hearts of Iron IV/mod/`，还能在游戏里亲眼看到这些缺陷的表现：
国策格子空白、事件不弹、图标粉黑方块。
