---
title: 社区 mod 的维护工程学（自测 / 静态检查 / CI / 协作公约）
domain: 93_ecosystem
scope: tooling
verified_on: 1.19.4.2
verified_at: 2026-11-07
source: BlackICE 12.1.0/12.5.1 双版对比 + The Road to 56 + Kaiserreich + Millennium Dawn 工坊实测
---

# 社区 mod 的维护工程学

> 大型 mod 的真正难点不在写内容，在**改三年**。本文记录工坊头部项目
> 2026-11 实测的维护基建：引擎自带的测试框架、Python 静态检查、CI、
> 协作公约。每条都给实测出处；「没做好的部分」同样记录——空壳脚手架
> 和腐烂的测试是更常见的常态。

## 1. 官方 Scripted Event Test Bundles：引擎自带的回归测试（KR、BICE、MD 都在用）

`tests/` 目录（mod 根，不在 common/）是**引擎原生支持**的测试框架，
语法文档随游戏分发：`tests/_documentation.info`。

```pdx
# tests/england.txt （BICE 12.5.1 在营测试，节选）
last_date = 1942.6.1        # 测试窗口；跑过这个日期后出总报告

tests = {
    ENG_capitulated_45 = {
        success = { NOT = { country_exists = ENG } }   # 持续求值的 AND trigger
        acceptable_fail_rate = 0.2                     # 容忍随机性，可多机过夜批量跑
    }
}
```

- 失败自动存 `TEST_FAIL_<test>_<date>.hoi4` 存档，日志写
  `logs/tests/tests_<timestamp>.log`——挂机跑一局 `-debug_mode -hands_off`，
  开局即可断言「法国该在 1940 前投降」「西班牙内战该以内战结束」。
- KR 的用法更激进：`tests/germany_defeats_france` 直接断言随机战役结局。
- **配套 define**：`HANDS_OFF_START_TAG`（BICE=URG、RT56=YEM、TNO=ZZZ）
  指定一个偏远国家当观战国，跑 `-hands_off` 观察 AI 对局。
- ⚠️ 腐烂实况：BICE 的 18 个 `scenario_tests/` 文件全是 2 字节空壳（从未填过），
  `tests/` 里大半国家文件整份被注释；MD 同样空壳。**脚手架不填内容 = 自欺**
  （与本插件铁律二同源：断言没被夹具触发就是恒真）。`last_date` 靠人手
  "increase as needed"，忘了改测试就静默失效。

## 2. BICE 12.5.1 的 Python 静态检查 + CI（mod 界最完整的一套）

`tools/check.py`（Typer CLI）+ `tools/checks/` 16 个规则模块，GitLab CI 双
stage（check / publish）：

| 规则 | 查什么 | 与本插件的对应 |
|---|---|---|
| history.missing_oob / missing_capital / unknown_technology | 国家历史缺 OOB/首都/引用未定义科技 | `kiant_hoi4_validate_mod` 同类 |
| encoding.*BOM | loc 文件 BOM | scan_localisation |
| line_endings.crlf_in_index | 仓库行尾一致性 | —（纯维护向） |
| file_paths.*大小写冲突 | Windows 大小写不敏感、Linux 崩 | — |
| sprite_names.*（含 vanilla_wins_with_better_art） | sprite 引用；**逐像素对比原版贴图**判断「抄原版但质量更差」 | 我们的 sprites 检查查存在性，不查质量 |
| vanilla_copy.duplicate_of_vanilla | PIL 解码逐像素找「原版拷贝没改」的贴图 | list_overrides 的图像版 |
| dlc.trigger_on_merged_dlc | 在 merged DLC 场景会炸的 trigger | — |
| shine | 统一高光动画参数 | — |

值得抄的工程决策（`tools/CLAUDE.md:1-20`）：

- **只走 git index，不走文件系统**——打包内容由 `repo.GAME_ROOTS` 决定，
  tests/、tools/ 天然不进发布包。
- **KNOWN_ISSUES 白名单「只出不进」**：已知误报先白名单挂起，新规则默认上 CI。
- **pre-commit 跑可自动修复的子集**，且注释写明「修复不得 git add，pre-commit 会 stash」。
- BICE 借用了 Millennium Dawn 的校验器（文件头注明 CC-BY-SA）——**社区校验器
  在互相借用**，佐证本插件自建校验器是正确投入。

## 3. RT56 的 mod 内 Python 工具链（随 mod 分发、非 CI）

| 脚本 | 干什么 | 值得学的 |
|---|---|---|
| `Savegame Fixer.py` | 救 `replace_path="history/states"` 造成的旧存档缺州 CTD：读 mod 自身 states 求最大州 ID，与存档比对，交互式生成缺失州的最小定义插回 | replace_path 的兼容债要用工具还 |
| `errorlog_cleaner.py` | 删 error.log 里的已知垃圾行（`*_plane_icons Invalid Scope`） | 日志降噪一次性脚本，17 行 |
| `focusgfxshine.py` | 给 goals 图标批量补 `_shine` 悬停扫光 spriteType（正则抽 name/texturefile，缺的按模板生成） | 「图标管线」自动化范本 |
| `localisationadder.py` | 扫 event/focus/ideas/decisions 把缺失 loc 键以 `key:0 ""` + `#TODO` 追加 | 本插件 `scan_localisation` 的手动版前身 |
| `Map Analyser.py` | 全部州文件统计成 Excel（建筑/资源/VP/owner/重复核心检测），缺失州回落原版 | 数据审计优于肉眼 |
| `generate_vp_arrays.py` | 向州文件批量插入 `add_to_array = { state_victory_points = N }` | 为 scripted GUI 供数据的代码生成 |

## 4. 协作公约（大模组多人开发的「土制度」）

- **ID 注册表**：RT56 的 `Unique Commanders IDS.txt`（212 行）——全队共用
  人物 ID 从 5600 起号避开原版，按国家登记已占用段位，YUG 预留 7000-8000
  并署名待更新。没有这个文件，多人并行必撞车。
- **注释标签词典**：BICE 的 `_TODO_TAGS.txt` 定义 `#TODO_MIO`、
  `#TODO_SCIENTIST` 等全团队标签，`grep` 即得工单。
- **ID 段位表写进文件头**：KR 的 `RUS events (Russia).txt:20-41`
  （`# russia_events.151-200 = Chernov assassination`）。
  ⚠️ KR 实测这张表已经自相矛盾（151-200 与 120-279 重叠、400-319 倒序）
  ——文档先烂，编号靠抢注。段位表要么工具校验，要么必然腐烂。
- **机器可读注记**：RT56 在 157 个 focus 文件头写 `#!gfx:interface\r56_goals.gfx`，
  把「focus 文件 ↔ 图标 gfx」显式绑定，供脚本校验缺图。
- **AI 协作规则**：BICE 的 `.claude/rules/*.md`（给 AI 编码代理的仓库规则：
  「规则=产出 Finding 的纯函数、每个 Case 是活的回归测试」「documentation.md
  是原版拷贝，先 diff 再覆盖」）；East Showdown 仓库带 `AGENTS.md` +
  `console_commands.md`（见本目录 East Showdown 调研）。
- **KR 的哑 idea 子模组探测**：`common/ideas/00 Submod trigger ideas.txt`
  用 `allowed = { always = no }` 的占位 idea（`kr_music_submod` 等），
  子 mod 覆盖同名 idea 后解锁——注意与 [EB-024](../91_error-book/EB-024-idea-toggle-decision-dead.md)
  的区别：占位 idea 不被自己 add_ideas，`always = no` 是合法的。

## 5. 大文件的教训（各家共性）

| mod | 实测 | 后果 |
|---|---|---|
| RT56 germany.txt | 72,062 行 | 合并冲突高危，README 专门写 PR 流程 |
| MD formable_nation_decisions.txt | 15,614 行 | 同上 |
| TNO TNO_Guangdong.txt | 56,666 行 | 单文件多 namespace，接手者靠文件头导航 |
| KR RUS events | 48,416 行 | 用文件头作者名单管理归属，而非拆文件 |
| BICE（反例→正例） | 12.1 的巨型 OOB → 12.5 拆成 7,325 个「一师一文件」 | 可按师 grep/复用/被测试断言；代价是文件数 ×9 |

结论方向一致：**拆分粒度 = 可独立 grep / 可独立归属 / 可独立断言的最小单元**。
BICE 的「一师一文件」+ `_AI`/`_player` 双份是当前最激进的实践。

## 6. replace_path 的组合拳与代价（descriptor 实测）

- BICE descriptor 声明 **66 条 replace_path**（countries/technologies/units/
  history 三件套 + ai_areas + graphic_db…），整目录顶替防原版残留——全量转换
  mod 的标准姿势；12.5 增删反映 1.19 变化（删 `common/ai_peace`、
  `map/supplyareas`，增 `common/operations`、special_projects 细分）。
- KR 约 40 条；MD/TNO 同量级。**小 mod 滥用 replace_path 是自断兼容**。
- 有专门检查器：BICE `tools/checks/modfile.py` 校验每条 replace_path
  在包里存在且非空。
- 代价实证：RT56 replace `history/states` 后，原版每补一个州都必须跟进，
  存档州数不匹配直接 CTD——所以才有 Savegame Fixer.py。

## 7. 12.1.0 → 12.5.1 的演进清单（对照两版实测，「维护性升级」长什么样）

1. **行尾统一**：全库 CRLF→LF，`CONTRIBUTING.md` 要求
   `git config merge.renormalize true`，`.git-blame-ignore-revs` 忽略一次性
   1414 文件的行尾提交。
2. **OOB 拆分**：829 → 7,325 文件（一师一文件）。
3. **测试与工具上 CI**：check.py + pytest + prek + GitLab package registry 发布。
4. **AI 协作规则成文**：`.claude/rules/` 五个文件。
5. **defines 跟版本 rebase**：4846 行整份原版拷贝只内联改 ~30 行，每次游戏
   升级手工 rebase——⚠️ 反模式仍在（整份拷贝 vs 只写覆盖行），BICE 用
   「documentation 是拷贝，先 diff 再覆盖」的规矩止血。
6. ⚠️ 打包卫生事故：12.5.1 把 `tools/.venv`（1335 文件）+ `__pycache__` 发进了
   工坊包——「3.3 万 vs 2.6 万文件」的增量主要是虚拟环境。发布包要显式排除
   开发目录（本插件的 FORBIDDEN 清单即为此设）。

## 8. TFR / East Showdown 补测（2026-11-07 第二轮）

### 8.1 defines 治理（TFR 的分文件法）

TFR 把 defines 拆成 4 个按用途命名的 .lua（而非单文件巨石）：
`TFR_defines_changes.lua`（每条行尾注释保留原版值，如 `-- 80`，可回滚对照）、
`TFR_00_magic.lua`（`COUNTRY_FLAG_TEX_MAX_SIZE=2048`，现代多色旗必需）、
`TFR_00_optimization.lua`（解锁游戏速度上限、`MAX_DAYS_BEHIND=3` 压联机 desync，
头部注释写明「防日/周/月度卡顿」）、`TFR_career_profile.lua`
（`MOD_STATISTICS_GROUP` 把生涯档案统计隔离进 mod 独立数据集，1.15+ 官方
define，极少有人用）。**defines 目录允许多文件并存**——这是比单文件 rebase
更可持续的组织法（对照 §7 第 5 条 BICE 的整份拷贝反模式）。

### 8.2 `d_` 控制台命令文档化（ES）

`d_` 前缀的 scripted effect 自动成为同名控制台命令，`args^0` 接收参数
（`d_add_ammunition = { add_to_variable = { FROM.ammunition_value_k = args^0 } }`，
ES_custom_console_commands.txt:6-8）。ES 把两条作弊命令写进
`console_commands.md` 交给测试员——「测试开关固化成文档」值得抄；
官方 debug 效果全部 `d_` 前缀即同一机制。

### 8.3 AI 协作的两种姿势

- **极简派**（East Showdown）：`AGENTS.md` 全文 31 行，就是 28 个
  ParadoxWiki 权威页面链接 + 一份 `changes.diff`（git diff 快照）当交接上下文。
  结论：**给 AI 喂权威链接比喂自研规则更省**——与本插件「知识只从正规渠道来」
  同一哲学。
- **成文派**（BICE）：`.claude/rules/` 五个文件，把「规则=纯函数、Case=回归测试」
  写成规矩（见 §2）。

### 8.4 死文件三例（发布前自查的反面教材）

| 实例 | 为什么是死的 |
|---|---|
| TFR 根目录 `flags/`（空目录） | 引擎只读 `gfx/flags`，根目录 flags 无功能 |
| TFR `TFR_organizations_xxx.txt` 放在 MIO **根目录** | 游戏只读 `organizations/` 子目录；其中 JAP_howa 与正确位置文件重复，永不加载 |
| ES `events/SuperEvents_0.6.txt` | replace events 后目录里**所有** txt 都加载，0.6 旧版与新版超级事件并存双触发（同见 EB-025 关联） |

### 8.5 冷门 1.16 系统的实装对照（两个 mod 都已跟进）

| 系统 | TFR | ES |
|---|---|---|
| raids（空袭/渗透/伞降） | nuclear_raids、paratrooper_raids_custom | bridge_strikes（29773 行逐桥生成）、能源设施打击 |
| special_projects | 含 prototype_rewards/ 与六类项目 | 仅 projects |
| script_constants + schema | country_groups/state_groups | — |
| synchronized_dynamic_tokens | 有 | — |
| generation（idea 程序化生成） | 三军顾问 ideas 程序化 | — |
| operation_tokens / phases | phases | 两者均有，ES 另有自定义 token |
| MIO 继承 | `include = generic_infantry_equipment_organization` 复用通用组织再改 icon | — |

ES 的「史实时间线编排」也值得记录：`es_on_actions.txt:1689-1700` 用
`country_event = { id = ... days = 973 }` 精确到天排剧本人格化事件，
注释标真实日期（#МИНДИЧГЕЙТ 等）——动态剧本的编年体写法。
