from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, List, Optional, Set, Tuple

from . import ast
from .renderer import INDENT


def parse(text: str) -> ast.Changelog:
    tokens = Tokenizer(text)()
    return Parser(text, tokens)()


class ParseError(Exception):
    def __init__(self, msg: str, source: str, row: int, col_start: int, col_end: int):
        lines = source.splitlines()
        prev, line = lines[row - 1 : row + 1] if row > 0 else ("", lines[row])

        arrows = " " * col_start + "^" * (col_end - col_start)
        details = (f"  {prev}\n" if prev else "") + f"  {line}\n  {arrows}"

        msg = f"{msg} (line {row + 1}, column {col_start + 1}):\n\n{details}"
        super().__init__(msg)


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
    pos: int
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

    def add_token(self, typ: TokenType, text: str = "", parsed: Any = None):
        col = self.col - len(self.matched)
        token = Token(typ, self.start, self.row, col, text or self.matched, parsed)
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
        t.add_token(TokenType.NEWLINE, char)
        t.row += 1
        t.col = 0
    elif char.isspace():
        pass
    else:
        if t.col == 1 and char == "[" and t.peek(-3) == "\n":
            t.add_token(TokenType.FOOTER_BEGIN)
        while t.peek() != "\n" and t.has_more:
            t.advance()
        text = t.matched
        if text:
            t.add_token(TokenType.TEXT, text)


class Parser:
    def __init__(self, source: str, tokens: List[Token]):
        self.source = source
        self.tokens = tokens
        self.current = 0

    @property
    def has_more(self) -> bool:
        return self.peek().typ != TokenType.EOF

    def advance(self, n: int = 1):
        if self.has_more:
            self.current += n
        return self.peek()

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

    def expect(self, *types: TokenType) -> bool:
        n = len(types)
        if self.current + n < len(self.tokens):
            if all(self.peek(-i).typ is typ for i, typ in enumerate(types)):
                self.advance(n)
                return True
        return False

    def error(
        self, msg: str, token: Optional[Token] = None, back: int = 0, forward: int = 0
    ) -> ParseError:
        token = token or self.peek()
        col_start = col_end = token.col
        if back:
            col_start -= back
        if forward:
            col_end += forward
        return ParseError(msg, self.source, token.row, col_start, col_end)

    def __call__(self) -> ast.Changelog:
        return changelog(self)


def changelog(p: Parser) -> ast.Changelog:
    c = ast.Changelog()

    if p.expect(TokenType.HASH, TokenType.TEXT):
        c.title = p.peek(1).text

    c.intro = text(p)
    if p.peek().typ is TokenType.FOOTER_BEGIN:
        c.intro += "\n"
        while p.match({TokenType.FOOTER_BEGIN}):
            c.intro += "\n" + text(p)

    while p.expect(TokenType.HASH, TokenType.HASH, TokenType.TEXT):
        c.versions.append(version(p))

    if p.has_more:
        raise p.error("Unprocessable text", forward=len(p.peek().text))

    return c


def text(p: Parser) -> str:
    text = ""
    while p.match({TokenType.TEXT, TokenType.NEWLINE}):
        text += p.peek(1).text
    return text.strip()


def version(p: Parser) -> ast.Version:
    title = p.peek(1).text
    try:
        number, date = title.split(" - ", 1)
    except ValueError:
        number, date = title, ""

    number = number.strip("[]")
    v = ast.Version(number=number, date=date)
    skip_newlines(p)

    while p.expect(TokenType.HASH, TokenType.HASH, TokenType.HASH, TokenType.TEXT):
        type_, changes_ = changes(p)
        v.changes[type_.value] = changes_

    return v


def changes(p: Parser) -> Tuple[ast.ChangeType, ast.Changes]:
    token = p.peek(1)
    title = token.text
    try:
        type_ = getattr(ast.ChangeType, title)
    except AttributeError:
        err = p.error("Unexpected title for changes", token, forward=len(title))
        raise err from None

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
