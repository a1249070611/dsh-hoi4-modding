"""Clausewitz script parser for Paradox / Hearts of Iron IV files.

Zero dependencies, tolerant by design: malformed input never raises, it
accumulates diagnostics instead. Handles .txt, .gui, .gfx, .asset, .mod files
(anything using the `key = value` / `key = { ... }` grammar).

Why hand-written instead of a library: mod folders are full of half-valid files
that the game still loads. A strict parser would refuse to open them, which is
exactly when you need diagnostics most.
"""

from __future__ import annotations

import re
from typing import Any, Iterator

TOKEN_RE = re.compile(
    r"""
      (?P<ws>[ \t\r\n]+)
    | (?P<comment>\#[^\n]*)
    | (?P<op>\?=|==|!=|>=|<=|[=<>])
    | (?P<lbrace>\{)
    | (?P<rbrace>\})
    | (?P<semi>;)
    | (?P<string>"(?:[^"\\]|\\.)*")
    | (?P<word>[^\s{}=<>#"]+)
    | (?P<bad>.)
    """,
    re.VERBOSE,
)

MAX_DEPTH = 256


class Node:
    __slots__ = ()


class Scalar(Node):
    __slots__ = ("value", "quoted", "line")

    def __init__(self, value: str, quoted: bool = False, line: int = 0) -> None:
        self.value = value
        self.quoted = quoted
        self.line = line

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Scalar({self.value!r})"


class Block(Node):
    __slots__ = ("items", "line")

    def __init__(self, line: int = 0) -> None:
        self.items: list[Node] = []
        self.line = line

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Block({len(self.items)} items)"


class Stmt(Node):
    __slots__ = ("key", "op", "value", "line")

    def __init__(self, key: str, op: str, value: Node, line: int = 0) -> None:
        self.key = key
        self.op = op
        self.value = value
        self.line = line

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Stmt({self.key!r} {self.op} ...)"


class Token:
    __slots__ = ("kind", "value", "line")

    def __init__(self, kind: str, value: str, line: int) -> None:
        self.kind = kind
        self.value = value
        self.line = line

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Token({self.kind},{self.value!r})"


def tokenize(text: str, errors: list[dict] | None = None) -> list[Token]:
    tokens: list[Token] = []
    line = 1
    pos = 0
    length = len(text)
    flagged_line = 0
    while pos < length:
        m = TOKEN_RE.match(text, pos)
        if not m:  # pragma: no cover - regex covers every char
            break
        kind = m.lastgroup or ""
        raw = m.group()
        if kind == "ws":
            line += raw.count("\n")
        elif kind == "comment":
            pass
        elif kind == "semi":
            # 行尾分号：游戏文件里真实存在（textureFile = "x.dds";），引擎忽略
            # 之。此前 `;` 落进 word 类会变成裸 scalar 污染列表块。参照
            # pdx.tools 的 Clausewitz 语法陷阱清单（rakaly/jomini 作者）。
            pass
        elif kind == "bad":
            if raw.strip():
                if errors is not None:
                    errors.append(
                        {"line": line, "level": "warn", "message": f"unexpected character {raw!r}"}
                    )
        else:
            value = raw
            if kind == "string":
                value = raw[1:-1]
            elif (
                kind == "word"
                and len(raw) > 1
                and raw.startswith("'")
                and not flagged_line == line
            ):
                # 有人把 'foo' 当字符串定界符。裸 token 里含单引号本身合法
                # （人名 Alhx'es、L'if' 就这样），所以只在「以单引号开头」时提示；
                # 像 L'if' 这种结尾带撇号的人名不会被误伤。
                flagged_line = line
                if errors is not None:
                    errors.append(
                        {
                            "line": line,
                            "level": "warn",
                            "message": "single quote is not a string delimiter in Clausewitz script",
                        }
                    )
            tokens.append(Token(kind, value, line))
        pos = m.end()
    return tokens


def parse(text: str) -> tuple[Block, list[dict]]:
    """Parse a whole file. Returns (root_block, diagnostics)."""
    errors: list[dict] = []
    tokens = tokenize(text, errors)
    root, idx = _parse_block(tokens, 0, errors, depth=0, opener_line=0)
    if idx < len(tokens):
        errors.append(
            {
                "line": tokens[idx].line,
                "level": "error",
                "message": f"unexpected '{tokens[idx].value}' after top-level block closed",
            }
        )
    return root, errors


def _parse_block(
    tokens: list[Token], idx: int, errors: list[dict], depth: int, opener_line: int
) -> tuple[Block, int]:
    block = Block(opener_line)
    if depth > MAX_DEPTH:
        errors.append(
            {"line": opener_line, "level": "error", "message": f"nesting deeper than {MAX_DEPTH}, giving up"}
        )
        return block, len(tokens)

    n = len(tokens)
    while idx < n:
        tok = tokens[idx]

        if tok.kind == "rbrace":
            return block, idx + 1

        if tok.kind == "lbrace":
            # Anonymous block with no key, e.g. list shorthand.
            inner, idx = _parse_block(tokens, idx + 1, errors, depth + 1, tok.line)
            block.items.append(inner)
            continue

        if tok.kind == "op":
            errors.append(
                {"line": tok.line, "level": "error", "message": f"operator '{tok.value}' without a left-hand key"}
            )
            idx += 1
            continue

        # A key, or a bare scalar inside a list block.
        key = tok.value
        nxt = tokens[idx + 1] if idx + 1 < n else None

        # 无等号块 `key{...}`：语法合法（引擎视为 key = {...}），EU4/CK3 文件
        # 常见而 HOI4 原版全量扫描（common/events/history/interface）零命中——
        # 但跨游戏来的 mod 作者会带进来。此前把 key 解析成裸 Scalar、块变成
        # 兄弟节点，get_one(key) 拿不到，静默丢失关联。现在归一成 Stmt。
        if nxt is not None and nxt.kind == "lbrace":
            inner, idx = _parse_block(tokens, idx + 2, errors, depth + 1, nxt.line)
            block.items.append(Stmt(key, "=", inner, tok.line))
            continue

        if nxt is not None and nxt.kind == "op":
            op = nxt.value
            after = tokens[idx + 2] if idx + 2 < n else None
            if after is None:
                errors.append(
                    {"line": tok.line, "level": "error", "message": f"'{key}' ends with '{op}' but no value"}
                )
                block.items.append(Stmt(key, op, Scalar("", False, tok.line), tok.line))
                return block, n
            if after.kind == "lbrace":
                inner, idx = _parse_block(tokens, idx + 3, errors, depth + 1, after.line)
                block.items.append(Stmt(key, op, inner, tok.line))
                continue
            if after.kind == "rbrace":
                errors.append(
                    {"line": tok.line, "level": "error", "message": f"'{key}' has an operator but empty value"}
                )
                block.items.append(Stmt(key, op, Scalar("", False, tok.line), tok.line))
                return block, idx + 2
            block.items.append(
                Stmt(key, op, Scalar(after.value, after.kind == "string", after.line), tok.line)
            )
            idx += 3
            continue

        block.items.append(Scalar(key, tok.kind == "string", tok.line))
        idx += 1

    if depth > 0:
        errors.append(
            {"line": opener_line, "level": "error", "message": "unclosed block: reached end of file"}
        )
    return block, idx


# --------------------------------------------------------------------------- #
# Navigation helpers
# --------------------------------------------------------------------------- #

def stmts(block: Block | Node) -> Iterator[Stmt]:
    if isinstance(block, Block):
        for item in block.items:
            if isinstance(item, Stmt):
                yield item


def entries(block: Block | Node) -> Iterator[tuple[str, Node]]:
    """遍历一个列表块的每一项，裸 token 和 key=value 都能拿到。

    HOI4 的列表块有两种写法，语义相同：

        events = { usa.6 usa.7 }          # 裸 token → 解析成 Scalar
        random_events = { 100 = usa.6 }   # key=value → 解析成 Stmt

    只用 stmts() 的话裸 token 整块被跳过——这是 on_actions / add_ideas /
    dependencies 三处检查静默失效的总根源。这里统一两种形态：
    Scalar 产出 (值, 自身)，Stmt 产出 (键, 自身)。

    对 random_events 这类「权重 = id」写法，键是权重数字，调用方按需区分
    （数字键视为权重、取第二个分量当 id）。
    """
    if not isinstance(block, Block):
        return
    for item in block.items:
        if isinstance(item, Scalar):
            yield item.value, item
        elif isinstance(item, Stmt):
            yield item.key, item.value


def get_all(block: Block | Node, key: str) -> list[Stmt]:
    return [s for s in stmts(block) if s.key == key]


def get_one(block: Block | Node, key: str) -> Stmt | None:
    for s in stmts(block):
        if s.key == key:
            return s
    return None


def get_one_ci(block: Block | Node, key: str) -> Stmt | None:
    """大小写不敏感的查找。

    原版里真实存在键名大小写不一致的写法，游戏照常认：
        events/USA.txt:1487      Hidden = yes      （首字母大写）
        events/*.txt              Picture = ...     （8 处）
    引擎对键名不敏感，精确匹配会把这类写法当成「没写这个字段」，
    进而误报「事件缺标题 / 选项缺名称 / 图标没引用」。
    只用于**读取字段值**；不用于 sprite 名（那是标识符，需保持原样）。
    """
    if not isinstance(block, (Block, Node)):
        return None
    low = key.lower()
    for s in stmts(block):
        if s.key.lower() == low:
            return s
    return None


def get_all_ci(block: Block | Node, key: str) -> list[Stmt]:
    """get_all 的大小写不敏感版本。理由见 get_one_ci。"""
    if not isinstance(block, (Block, Node)):
        return []
    low = key.lower()
    return [s for s in stmts(block) if s.key.lower() == low]


def as_text(node: Node | None) -> str:
    if isinstance(node, Scalar):
        return node.value
    return ""


def walk(block: Block | Node, trail: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], Stmt]]:
    """Depth-first walk yielding (path, statement)."""
    for s in stmts(block):
        yield trail + (s.key,), s
        if isinstance(s.value, Block):
            yield from walk(s.value, trail + (s.key,))


def to_python(block: Node) -> Any:
    """Convert to plain JSON-friendly data.

    Duplicate keys collapse into a list; bare scalars in a list block collect
    under "#values".
    """
    if isinstance(block, Scalar):
        return block.value
    if not isinstance(block, Block):
        return None

    out: dict[str, Any] = {}
    values: list[Any] = []
    for item in block.items:
        if isinstance(item, Stmt):
            converted = to_python(item.value)
            if item.key in out:
                if not isinstance(out[item.key], list):
                    out[item.key] = [out[item.key]]
                out[item.key].append(converted)
            else:
                out[item.key] = converted
        elif isinstance(item, Scalar):
            values.append(item.value)
        elif isinstance(item, Block):
            values.append(to_python(item))
    if values:
        out["#values"] = values
    return out


def parse_file(path: str) -> tuple[Block, list[dict]]:
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        text = fh.read()
    return parse(text)
