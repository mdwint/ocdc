from .parser import parse
from .renderer import render_new_template  # noqa
from .renderer import render_markdown


def format(text: str) -> str:
    return render_markdown(parse(text))
