# 把知识库发布到开源平台

插件不打包知识库。知识以你维护的那份为准，不定期发布，插件按需拉取。

这份文档写两件事：你这边要怎么做，以及插件怎么判断该不该更新。

## 仓库该长什么样

不用新建仓库，用插件仓库本身就行。插件只取 `paths` 里列出的目录：

```
你的仓库/
├── manifest.json          ← 必需，版本号与文件数
├── knowledge/notes/       ← 你的笔记（.md）
├── references/            ← 参考库 163 篇（63 上游 + 6 案例 + 5 根文件 + 89 自建）
├── mcp-server/            ← 插件本体，远端同步不取
├── agents/                ← 同上
└── ...
```

远端同步只复制 `knowledge/notes/` 和 `references/` 下的 `.md`、`.txt`、`.json`、`.csv`。
代码、游戏索引、`sources.json` 一律不搬，那些东西每台机器都不一样。

按当前仓库实测，这两个目录下可取的文件共 166 个（163 篇参考库 + 3 个笔记文件）。

## manifest.json

放仓库根目录，几百字节。插件每次只拉它来判断要不要重新下载整个包：

```json
{
  "version": "2026.11.06",
  "file_count": 148,
  "built_at": "2026-11-06"
}
```

`version` 用什么格式都行，插件只做字符串相等比较。建议用日期，人能看懂：

- `2026.11.06`：当天第一次
- `2026.11.06-2`：当天第二次

每次改完知识就把 version 改掉，否则使用者那边会一直显示「已是最新」。

忘了改也不会出错，只是他们得手动 `force: true`。`pull` 返回里带了 `sha256`，
两边一对就能看出内容其实变了。

## 发布流程

```bash
# 1. 改知识
vim knowledge/notes/version-1.19-xxx.md

# 2. 改版本号
vim manifest.json          # version → 2026.11.06-2

# 3. 推
git add -A && git commit -m "kb: 补充 1.19 学说结构" && git push
```

没有第 4 步。插件不需要你构建任何东西，它自己拉 tarball、解压、建索引。

## 使用者那边

他们只需要在 `knowledge/remote.json` 里填一次仓库名：

```json
{
  "repo": "你的用户名/仓库名",
  "branch": "main",
  "paths": ["knowledge/notes", "references"],
  "manifest": "manifest.json"
}
```

然后三步：

```
kiant_hoi4_kb_sync action=status    → 本地 2026.11.06，远端 2026.11.06-2，过期 true
kiant_hoi4_kb_sync action=pull      → 下载 1 MB，解压，缓存
kiant_hoi4_kb_build action=build    → 多出一个 remote 源
```

之后 `kiant_hoi4_kb_search` 就能命中你的知识，结果里 `source` 是 `remote`，
和本地的 `refs` 区分得开。

## 为什么用 tarball 而不是逐个文件下载

| 方式 | 148 个文件 | 后果 |
|---|---|---|
| 逐个 HTTP GET | 148 次请求 | 慢、容易触发限流、中途失败没法定点续 |
| git clone | 1 次 | 要求用户装 git，且要处理整个历史 |
| tarball | 1 次请求 1 MB | 只依赖标准库 |

GitHub 的 `codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/{branch}` 是公开、
稳定、无需 token 的。

## 如果你的知识库不在 GitHub

`remote.json` 里有 `mirror` 字段，填一个 tar.gz 直链即可，优先级高于 `repo`：

```json
{ "mirror": "https://你的域名/kb-2026.11.06.tar.gz", "manifest": "https://你的域名/manifest.json" }
```

tarball 里要有一层顶层目录（GitHub 会自动加 `用户名-仓库名-sha/`）。插件解压时会剥掉它。

## 离线与内网

- 网络断了：`pull` 返回 `ok: false` 但不动缓存，检索继续用旧数据，并明确告诉你当前版本号
- 内网分发：把 tar.gz 放到共享盘，`mirror` 填 `file:///` 或直接给本地路径

## 一份自查清单

发布前对一遍：

- [ ] `manifest.json` 的 `version` 改过了
- [ ] `file_count` 和实际文件数一致（不一致只是提示不准，不影响功能）
- [ ] 新增的 `.md` 放在 `paths` 列出的目录里，别放仓库根
- [ ] 笔记里有可复核的坐标（`common/xxx.txt:123` 或官方文档行号），否则它只是 B 级线索
- [ ] 没把 `~/.kiant-hoi4-modkit/kb.sqlite` 或 `sources.json` 提交上去