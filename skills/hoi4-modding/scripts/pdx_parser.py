"""HOI4 (Clausewitz/PDX) script parser — 容错解析器。

用途：
  * 静态校验 Mod 脚本（括号、引号、编码、重复定义）
  * 从脚本里提取 ID / GFX 引用 / 本地化 key
  * 不追求 100% 还原游戏语义，追求「任何输入都不崩，尽量给出可用结构 + 精确报错位置」。

PDX 脚本语法：空格分隔的 `key = value` 对；`{ }` 为块；`#` 到行尾为注释（字符串内除外）；
字符串用双引号，内部可含转义；支持 `!= < > <= >= == ?=` 等运算符；
裸值（无 key）出现在列表中（例如 `tags = { "A" "B" }`）。

API：
    tree, errors = parse_text(text)          # errors: list[ParseError]
    tree, errors = parse_file(path)          # 自动处理 UTF-8 BOM
    for entry in tree.entries: ...           # Entry | Value
    tree.get("focus_tree")                   # -> list[Entry]
    tree.all("id")                           # -> 递归收集所有 id 值（带行号）
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator


class ParseError(Exception):
    def __init__(self, message: str, line: int, col: int = 1, path: str | None = None):
        self.message = message
        self.line = line
        self.col = col
        self.path = path
        super().__init__(f"{path or '<text>'}:{line}:{col}: {message}")

    def __str__(self) -> str:  # pragma: no cover - convenience
        return f"{self.path or '<text>'}:{self.line}:{self.col}: {self.message}"


@dataclass
class Token:
    kind: str          # 'id' | 'str' | 'num' | '{' | '}' | 'op'
    value: str
    line: int
    col: int


@dataclass
class Value:
    """裸值（列表元素）或 = 右侧的标量。"""
    value: str
    kind: str = "id"
    line: int = 0

    def __str__(self) -> str:
        return self.value


@dataclass
class Entry:
    key: str
    op: str
    value: "Value | Block"
    line: int

    # 便捷访问
    @property
    def scalar(self) -> str | None:
        return self.value.value if isinstance(self.value, Value) else None

    @property
    def block(self) -> "Block | None":
        return self.value if isinstance(self.value, Block) else None


@dataclass
class Block:
    entries: list = field(default_factory=list)
    line: int = 0

    # ---------- 查询辅助 ----------
    def pairs(self) -> Iterator[Entry]:
        for e in self.entries:
            if isinstance(e, Entry):
                yield e

    def get(self, key: str) -> Entry | None:
        for e in self.pairs():
            if e.key == key:
                return e
        return None

    def get_all(self, key: str) -> list[Entry]:
        return [e for e in self.pairs() if e.key == key]

    def first_scalar(self, key: str, default: str | None = None) -> str | None:
        e = self.get(key)
        return e.scalar if e and e.scalar is not None else default

    def first_block(self, key: str) -> "Block | None":
        e = self.get(key)
        return e.block if e else None

    def all_scalars(self, key: str) -> list[str]:
        out = []
        for e in self.get_all(key):
            if e.scalar is not None:
                out.append(e.scalar)
        return out

    def walk(self) -> Iterator[Entry]:
        """深度优先遍历所有 Entry（不含自身）。"""
        for e in self.pairs():
            yield e
            if isinstance(e.value, Block):
                yield from e.value.walk()

    def find_blocks(self, key: str) -> Iterator["Block"]:
        for e in self.walk():
            if e.key == key and isinstance(e.value, Block):
                yield e.value

    def find_entries(self, key: str) -> Iterator[Entry]:
        for e in self.walk():
            if e.key == key:
                yield e


_OPS = ("!=", "<=", ">=", "==", "?=", "<", ">", "=")
_ID_RE = re.compile(r"[^\s{}<>=!?#\"']+")


def tokenize(text: str) -> tuple[list[Token], list[ParseError]]:
    tokens: list[Token] = []
    errors: list[ParseError] = []
    i, n = 0, len(text)
    line, col = 1, 1

    def advance(k: int) -> None:
        nonlocal i, line, col
        for _ in range(k):
            if i < n and text[i] == "\n":
                line += 1
                col = 1
            else:
                col += 1
            i += 1

    while i < n:
        ch = text[i]
        if ch in " \t\r\n":
            advance(1)
            continue
        if ch == "#":  # 注释到行尾
            while i < n and text[i] != "\n":
                advance(1)
            continue
        if ch == '"':
            start_line, start_col = line, col
            advance(1)
            buf = []
            closed = False
            while i < n:
                c = text[i]
                if c == "\\" and i + 1 < n:
                    buf.append(text[i : i + 2])
                    advance(2)
                    continue
                if c == '"':
                    advance(1)
                    closed = True
                    break
                buf.append(c)
                advance(1)
            if not closed:
                errors.append(ParseError("字符串未闭合（缺少结尾双引号）", start_line, start_col))
            tokens.append(Token("str", "".join(buf), start_line, start_col))
            continue
        if ch in "{}":
            tokens.append(Token(ch, ch, line, col))
            advance(1)
            continue
        # 运算符
        matched = None
        for op in _OPS:
            if text.startswith(op, i):
                matched = op
                break
        if matched:
            tokens.append(Token("op", matched, line, col))
            advance(len(matched))
            continue
        # 裸 token（数字/标识符/@变量/路径等）
        start_line, start_col, start_i = line, col, i
        while i < n and text[i] not in ' \t\r\n{}#<>=':
            advance(1)
        raw = text[start_i:i]
        if not raw:  # 理论上不会发生，防死循环
            advance(1)
            continue
        kind = "num" if re.fullmatch(r"-?\d+(\.\d+)?", raw) else "id"
        tokens.append(Token(kind, raw, start_line, start_col))
    return tokens, errors


class _Parser:
    def __init__(self, tokens: list[Token], path: str):
        self.tokens = tokens
        self.path = path
        self.pos = 0
        self.errors: list[ParseError] = []

    def peek(self) -> Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> Token | None:
        tok = self.peek()
        if tok is not None:
            self.pos += 1
        return tok

    def err(self, msg: str, tok: Token | None) -> None:
        if tok is None:
            last = self.tokens[-1] if self.tokens else Token("id", "", 1, 1)
            self.errors.append(ParseError(msg, last.line, last.col, self.path))
        else:
            self.errors.append(ParseError(msg, tok.line, tok.col, self.path))

    def parse_root(self) -> Block:
        block = self.parse_block_body(top=True)
        return block

    def parse_block_body(self, top: bool = False) -> Block:
        block = Block(line=self.peek().line if self.peek() else 1)
        while True:
            tok = self.peek()
            if tok is None:
                if not top:
                    self.err("文件结束但缺少 1 个 '}'（块未闭合）", None)
                return block
            if tok.kind == "}":
                if top:
                    self.err("多余的 '}'", tok)
                    self.next()
                    continue
                self.next()
                return block
            if tok.kind == "{":
                # 匿名块：合法但少见（例如 script_constants 的 schema 里 `data = { { ... } }`）
                self.next()
                inner = self.parse_block_body()
                block.entries.append(Value(str(inner), "block", tok.line))
                continue
            # 读取 key（或列表裸值）
            key_tok = self.next()
            nxt = self.peek()
            if nxt is not None and nxt.kind == "op":
                op = self.next().value
                val_tok = self.peek()
                if val_tok is None:
                    self.err(f"'{key_tok.value} {op}' 后缺少值", key_tok)
                    continue
                if val_tok.kind == "{":
                    self.next()
                    inner = self.parse_block_body()
                    block.entries.append(Entry(key_tok.value, op, inner, key_tok.line))
                elif val_tok.kind in ("id", "num", "str"):
                    self.next()
                    kind = val_tok.kind
                    val = Value(val_tok.value, kind, val_tok.line)
                    block.entries.append(Entry(key_tok.value, op, val, key_tok.line))
                elif val_tok.kind == "}":
                    self.err(f"'{key_tok.value} {op}' 后缺少值", key_tok)
                else:
                    self.err(f"'{key_tok.value} {op}' 后出现意外符号 {val_tok.value!r}", val_tok)
                    self.next()
            else:
                # 列表裸值
                if key_tok.kind == "op":
                    self.err(f"意外的运算符 {key_tok.value!r}", key_tok)
                else:
                    block.entries.append(Entry(key_tok.value, "", Value(key_tok.value, key_tok.kind, key_tok.line), key_tok.line))


def parse_text(text: str, path: str | None = None) -> tuple[Block, list[ParseError]]:
    tokens, token_errors = tokenize(text)
    parser = _Parser(tokens, path or "<text>")
    tree = parser.parse_root()
    return tree, token_errors + parser.errors


def parse_file(path: str) -> tuple[Block, list[ParseError]]:
    """读文件并解析。编码：优先 UTF-8(-SIG)；失败则用 latin-1 并记录错误。"""
    with open(path, "rb") as fh:
        raw = fh.read()
    text, enc_error = decode_bytes(raw, path)
    tree, errors = parse_text(text, path)
    if enc_error:
        errors.insert(0, enc_error)
    return tree, errors


def decode_bytes(raw: bytes, path: str | None = None) -> tuple[str, ParseError | None]:
    for enc in ("utf-8-sig",):
        try:
            return raw.decode(enc), None
        except UnicodeDecodeError as exc:
            # 尝试定位行号
            line = raw[: exc.start].count(b"\n") + 1
            return raw.decode("utf-8", errors="replace"), ParseError(
                f"文件不是合法 UTF-8（第 {line} 行附近），HOI4 读中文可能乱码/报错", line, 1, path
            )
    return raw.decode("latin-1"), None  # pragma: no cover


# ---------------------------------------------------------------------------
# 高层提取工具（供 lint / 文档生成复用）
# ---------------------------------------------------------------------------

def collect_pairs(tree: Block, key: str) -> list[Entry]:
    return [e for e in tree.walk() if e.key == key]


def all_ids(tree: Block) -> list[tuple[str, int]]:
    """收集脚本里所有 `id = xxx`（用于重复定义检测）。"""
    out = []
    for e in tree.walk():
        if e.key == "id" and e.scalar is not None:
            out.append((e.scalar, e.line))
    return out


def iter_blocks(tree: Block, key: str) -> Iterator[Block]:
    for e in tree.walk():
        if e.key == key and isinstance(e.value, Block):
            yield e.value


def block_scalar(block: Block, key: str) -> str | None:
    e = block.get(key)
    return e.scalar if e else None


if __name__ == "__main__":  # 手动快速检查：python pdx_parser.py <file>
    import sys

    for p in sys.argv[1:]:
        tree, errs = parse_file(p)
        print(f"== {p}: {len(tree.entries)} top-level entries, {len(errs)} errors")
        for e in errs[:20]:
            print("  ", e)
