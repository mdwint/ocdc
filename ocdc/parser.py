from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

from . import ast
from .renderer import INDENT


def parse(text: str) -> ast.Changelog:
    tokens = Tokenizer(text)()
    return Parser(text, tokens)()


class TokenType(Enum):
    HASH = auto()
    DASH = auto()
    TEXT = auto()
    NEWLINE = auto()
    FOOTER_BEGIN = auto()
    EOF = auto()


@dataclass
class Token:
    typ: TokenType
    row: int
    col: int
    text: str
    parsed: Any = None


class Tokenizer:
    def __init__(self, source: str):
        self.source = source
        self.start = self.current = self.row = self.col = 0
        self.tokens: List[Token] = []

    @property
    def has_more(self) -> bool:
        return self.current < len(self.source)

    @property
    def matched(self) -> str:
        return self.source[self.start : self.current]

    def advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        self.col += 1
        return char

    def peek(self, offset: int = 0) -> str:
        try:
            return self.source[self.current + offset]
        except IndexError:
            return "\0"

    def add_token(self, typ: TokenType, text: str = "", parsed: Any = None) -> None:
        col = self.col - len(self.matched)
        token = Token(typ, self.row, col, text or self.matched, parsed)
        self.tokens.append(token)

    def __call__(self) -> List[Token]:
        while self.has_more:
            self.start = self.current
            scan_token(self)
        self.start = self.current
        self.add_token(TokenType.EOF)
        return self.tokens


def scan_token(t: Tokenizer) -> None:
    char = t.advance()
    if char == "#":
        t.add_token(TokenType.HASH)
    elif char == "-":
        t.add_token(TokenType.DASH)
    elif char == "\n":
        t.add_token(TokenType.NEWLINE)
        t.row += 1
        t.col = 0
    elif char.isspace():
        pass
    else:
        if t.col == 1 and char == "[" and t.peek(-3) == "\n":
            t.add_token(TokenType.FOOTER_BEGIN)
        while t.peek() != "\n" and t.has_more:
            t.advance()
        text = t.matched.strip()
        if text:
            t.add_token(TokenType.TEXT, text)


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, source: str, tokens: List[Token]):
        self.source = source
        self.tokens = tokens
        self.current = 0

    @property
    def has_more(self) -> bool:
        return self.peek().typ != TokenType.EOF

    class Rollback(Exception):
        pass

    @contextmanager
    def checkpoint(self) -> Iterator[None]:
        saved = self.current
        try:
            yield
        except self.Rollback:
            self.current = saved

    def advance(self, n: int = 1) -> None:
        if self.has_more:
            self.current += n

    def check(self, typ: TokenType) -> bool:
        return self.has_more and self.peek().typ is typ

    def peek(self, back: int = 0) -> Token:
        return self.tokens[self.current - back]

    def match(self, types: Set[TokenType]) -> bool:
        for typ in types:
            if self.check(typ):
                self.advance()
                return True
        return False

    def match_many(self, typ: TokenType) -> int:
        n = 0
        while self.match({typ}):
            n += 1
        return n

    def expect(self, *types: TokenType) -> bool:
        n = len(types)
        if self.current + n < len(self.tokens):
            if all(self.peek(-i).typ is typ for i, typ in enumerate(types)):
                self.advance(n)
                return True
        return False

    def error(
        self,
        msg: str,
        token: Optional[Token] = None,
        back: int = 0,
        forward: int = 0,
        hint: str = "",
    ) -> ParseError:
        token = token or self.peek()
        msg += " " + annotate(self.source, token, back, forward)
        if hint:
            msg += f"\n\nHint: {hint}"
        return ParseError(msg)

    def __call__(self) -> ast.Changelog:
        return changelog(self)


def changelog(p: Parser) -> ast.Changelog:
    c = ast.Changelog()

    skip_newlines(p)
    if p.expect(TokenType.HASH, TokenType.TEXT):
        c.title = p.peek(1).text

    c.intro = text(p)
    if p.peek().typ is TokenType.FOOTER_BEGIN:
        c.intro += "\n"
        while p.match({TokenType.FOOTER_BEGIN}):
            c.intro += "\n" + text(p)

    seen_version_titles: Dict[str, Token] = {}
    while p.expect(TokenType.HASH, TokenType.HASH, TokenType.TEXT):
        v, title_token = version(p)

        duplicate_title_token = seen_version_titles.get(v.number)
        if duplicate_title_token:
            forward = len(v.number)
            at = annotate(p.source, title_token, forward=forward)
            msg, hint = "Duplicate version", f"Version was first used {at}"
            raise p.error(msg, duplicate_title_token, forward=forward, hint=hint)

        seen_version_titles[v.number] = title_token
        c.versions.append(v)

    if p.has_more:
        raise p.error("Unprocessable text")

    return c


def text(p: Parser) -> str:
    text = ""
    while p.match({TokenType.TEXT, TokenType.NEWLINE}):
        text += p.peek(1).text
    return text.strip()


def version(p: Parser) -> Tuple[ast.Version, Token]:
    title_token = p.peek(1)
    title = title_token.text
    try:
        number, date = title.split(" - ", 1)
    except ValueError:
        number, date = title, ""

    number = number.strip().strip("[]")
    v = ast.Version(number=number, date=date.strip())
    skip_newlines(p)

    while p.expect(TokenType.HASH, TokenType.HASH, TokenType.HASH, TokenType.TEXT):
        type_, changes_ = changes(p)
        key = type_.value
        if key in v.changes:
            v.changes[key].merge(changes_)
        else:
            v.changes[key] = changes_

    detect_wrong_title_level(p, 3, "before changes")

    return v, title_token


def detect_wrong_title_level(p: Parser, expected: int, reason: str) -> None:
    with p.checkpoint():
        level = p.match_many(TokenType.HASH)
        if level != expected:
            token = p.peek(1)
            p.match({TokenType.TEXT})
            skip_newlines(p)
            if p.match({TokenType.DASH}):
                msg = f"Expected a title of H{expected} {reason}"
                if level:
                    msg += f", but found H{level}"
                    raise p.error(msg, token, back=level)
                else:
                    raise p.error(msg, token=p.peek(1))
        raise p.Rollback


def changes(p: Parser) -> Tuple[ast.ChangeType, ast.Changes]:
    token = p.peek(1)
    title = token.text
    try:
        type_ = getattr(ast.ChangeType, title)
    except AttributeError:
        msg = "Unexpected title for changes"
        hint = "Choose from " + ", ".join(f'"{t.value}"' for t in ast.ChangeType) + "."
        raise p.error(msg, token, hint=hint) from None

    skip_newlines(p)

    items = []
    while p.match({TokenType.DASH}):
        level = p.peek(1).col // len(INDENT)
        item = ast.ListItem(text=text(p), level=level)
        items.append(item)

    footer = ""
    while p.match({TokenType.FOOTER_BEGIN}):
        footer += text(p) + "\n"
    footer = footer.strip()

    return type_, ast.Changes(items=items, footer=footer)


def skip_newlines(p: Parser) -> None:
    while p.match({TokenType.NEWLINE}):
        pass


def annotate(source: str, token: Token, back: int = 0, forward: int = 0) -> str:
    lines = source.splitlines()
    row = min(token.row, len(lines) - 1)
    prev, line = lines[row - 1 : row + 1] if row > 0 else ("", lines[row])

    if not (back or forward):
        forward = len(token.text)

    col_start = token.col - back
    col_end = token.col + forward
    col = max(0, col_start)

    arrows = " " * col_start + "^" * (col_end - col_start)
    details = (f"  {prev}\n" if prev else "") + f"  {line}\n  {arrows}"
    return f"at line {row + 1}, column {col + 1}:\n\n{details}"
