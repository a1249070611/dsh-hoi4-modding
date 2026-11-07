# 在 WorkBuddy 里装成「专家包」

WorkBuddy 的专家包 = 人设 + 技能 + 可选的工具服务。这个仓库的三部分正好一一对应。

## 一、装技能

```bash
cp -r skills/* ~/.workbuddy/skills/
```

装完新开一个会话，技能列表里会出现 15 个 `hoi4-*` 技能。想只留部分也可以，单目录复制即可。

## 二、建专家

在左侧栏进入**专家中心** → 新建专家，按下面填：

| 字段 | 填写内容 |
|---|---|
| 名称 | 钢铁雄心4 模组工程师 |
| 简介 | HOI4 mod 开发：国策树、事件、决议、本地化、GFX、兼容性与 error.log 排错 |
| 人设 / 系统提示 | 粘贴 `agents/kiant-hoi4-modder.md` 的正文（去掉最上面 `---` 包起来的 frontmatter） |
| 技能 | 勾选上一步装的 15 个 `hoi4-*` 技能 |

人设文件里已经写明了工作流、工具优先级和硬性约束，不需要再补充。

## 三、接工具服务

工具是可选的——没有 MCP 服务时，技能仍然能提供方法论，只是少了自动校验能力。

注册方式：在 `~/.workbuddy/mcp.json` 里加入

```json
{
  "mcpServers": {
    "kiant-hoi4-modkit": {
      "command": "python",
      "args": ["C:/绝对路径/dsh-hoi4-modding/mcp-server/server.py"]
    }
  }
}
```

保存后**不会自动生效**。到连接器管理页面右上角的「自定义连接器」入口，找到 `dsh-hoi4-modding` 点「信任」，才会真正启动。

这一步是刻意保留的：任何会自动拉起本地进程的配置，都该由你亲手确认一次。

## 四、验证

新开一个专家会话，说：

> 在 D:/mods/testmod 建一个德国国策，加个 autobahn 焦点，然后校验。

预期行为：

1. 调 `kiant_hoi4_scaffold` kind=mod 建骨架
2. 调 `kiant_hoi4_scaffold` kind=focus 加国策，同时写入本地化
3. 调 `kiant_hoi4_validate_mod` 报告 0 error
4. 用中文说明生成了哪些文件、下一步该做什么

如果第 3 步没被调用，说明人设没生效或工具没信任成功。
