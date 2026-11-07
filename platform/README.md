# 平台接入

本工具包刻意**不预置可自动加载的 MCP 配置**。原因很直接：`.cursor/mcp.json`、`.claude-plugin/plugin.json` 这类文件一旦存在，客户端会立刻启动 `server.py` 进程——你还没读过它的代码，它就已经在跑了。

所以接入方式是：**你自己复制下面这段配置，粘到你信任的位置。** 九行，比读一份陌生插件的权限清单快得多。

```json
{
  "mcpServers": {
    "kiant-hoi4-modkit": {
      "command": "python3",
      "args": ["/绝对路径/kiant-hoi4-modkit/mcp-server/server.py"]
    }
  }
}
```

Windows 上 `command` 用 `python`，路径用正斜杠或双反斜杠：

```json
{
  "mcpServers": {
    "kiant-hoi4-modkit": {
      "command": "python",
      "args": ["C:/Users/you/kiant-hoi4-modkit/mcp-server/server.py"]
    }
  }
}
```

装好后客户端会问你是否信任这个服务，选信任才会真正启动。

---

## Claude Code

**Agent 与技能**（不需要 MCP 也能用）：

```bash
# 技能：复制到用户级目录，所有项目可用
cp -r skills/* ~/.claude/skills/

# Agent：复制到项目级 agents 目录
mkdir -p .claude/agents && cp agents/kiant-hoi4-modder.md .claude/agents/
```

**MCP 工具**：

```bash
claude mcp add kiant-hoi4-modkit -- python3 /绝对路径/kiant-hoi4-modkit/mcp-server/server.py
```

或手动编辑 `~/.claude.json`，把上面的 `mcpServers` 片段合并进去。

**验证**：新开会话，问「用 kiant_hoi4_validate_mod 检查 /path/to/mod」。工具列表里应能看到 20 个 `kiant_hoi4_*` 工具。

**先建知识库**，否则跨文件引用检查会降级：

```json
{"action": "discover"}
```

确认源列表后再 `{"action": "build"}`。没有索引工具照样能用，但「查原版怎么写的」这个能力就没有了。

---

## Cursor

**MCP**：`Cursor Settings → MCP → Add new MCP Server`，Type 选 `command`，Command 填：

```
python3 /绝对路径/kiant-hoi4-modkit/mcp-server/server.py
```

或编辑 `~/.cursor/mcp.json`（全局）／项目根 `.cursor/mcp.json`（仅本项目），合并上面的片段。

**规则**：把 `agents/kiant-hoi4-modder.md` 的内容追加到 `.cursor/rules/hoi4.mdc`，Cursor 会把它当项目规则用。技能内容可以按需贴进规则文件，Cursor 没有技能目录的概念。

---

## Codex / OpenAI 系

没有 MCP 时的降级方案：直接把 `server.py` 当命令行工具调用。

```
python server.py --list
python server.py --call kiant_hoi4_validate_mod '{"mod_path": "/path/to/mod"}'
```

把 `agents/kiant-hoi4-modder.md` 作为 `AGENTS.md` 的一部分放进项目根目录，它会被自动读取。

---

## WorkBuddy

技能目录是 `~/.workbuddy/skills/`，每个技能一个文件夹，内含 `SKILL.md`：

```bash
cp -r skills/* ~/.workbuddy/skills/
```

Agent 走专家包路径，见 `platform/workbuddy/README.md`。

MCP 服务在 `~/.workbuddy/mcp.json` 里注册（同上面的片段），保存后需要在连接器管理页对新服务点「信任」才会生效。

---

## 任何其它支持 MCP 的客户端

只要客户端支持 stdio 传输的 MCP 服务器，配置都是同一个形状：命令 `python`，参数指向 `server.py` 的绝对路径，不需要环境变量，不需要安装依赖。

## 装不上时的排查

| 现象 | 原因 |
|---|---|
| 客户端报 `command not found` | 用了 `python3` 但系统只有 `python`（Windows 常见），互换试 |
| 连接建立后立刻断开 | 路径含空格且没加引号；或 `server.py` 里 `sys.path` 找不到同目录模块（确认四个 .py 文件都在 `mcp-server/` 下） |
| 工具列表为空 | 客户端版本太老，不支持 `tools/list`；升级客户端 |
| 中文乱码 | 系统默认编码不是 UTF-8，设置环境变量 `PYTHONUTF8=1` |
