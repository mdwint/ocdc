import datetime as dt
import sys
from textwrap import TextWrapper, indent

from packaging.version import InvalidVersion, Version as ParsedVersion

from . import ast

MAX_WIDTH = 90
INDENT = "  "

wrapper = TextWrapper(MAX_WIDTH, drop_whitespace=False)
item_wrapper = TextWrapper(MAX_WIDTH, initial_indent="- ", subsequent_indent=INDENT)


def wrap(text: str) -> str:
    return "\n".join(wrapper.fill(line) for line in text.splitlines())


def wrap_item(item: ast.ListItem) -> str:
    return indent(item_wrapper.fill(item.text), item.level * INDENT)


MAX_VERSION = ParsedVersion(str(sys.maxsize))


def parse_version(number: str) -> ParsedVersion:
    try:
        return ParsedVersion(number)
    except InvalidVersion:
        return MAX_VERSION


change_type_order = {t.value: i for i, t in enumerate(ast.ChangeType)}


def render_markdown(c: ast.Changelog) -> str:
    text = ""

    if c.title:
        text += f"# {c.title}\n\n"

    if c.intro:
        text += wrap(c.intro) + "\n"

    version_order = {v.number: parse_version(v.number) for v in c.versions}

    for v in sorted(c.versions, reverse=True, key=lambda v: version_order[v.number]):
        text += f"\n\n## {v.number}"
        if v.date:
            text += f" - {v.date}"
        text += "\n"

        for type_ in sorted(v.changes, key=lambda t: change_type_order[t]):
            text += f"\n### {type_}\n\n"
            changes = v.changes[type_]
            for item in changes.items:
                text += wrap_item(item) + "\n"
            if changes.footer:
                text += f"\n{changes.footer}\n"

    return text


def render_new_template() -> str:
    v = ast.Version(
        number="0.1.0",
        date=dt.date.today().isoformat(),
        changes={
            ast.ChangeType.Added.value: ast.Changes(
                items=[ast.ListItem(text="Initial version.")]
            )
        },
    )
    c = ast.Changelog(title="Changelog", intro=INTRO, versions=[v])
    return render_markdown(c)


INTRO = """
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
""".strip()
