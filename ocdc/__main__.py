import argparse
import sys
from pathlib import Path

from . import __version__, api

DEFAULT_PATH = Path("CHANGELOG.md")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Format a changelog.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.set_defaults(func=format)
    p.add_argument(
        "-p",
        "--path",
        type=Path,
        default=DEFAULT_PATH,
        help=(
            "Path to changelog. Pass '-' to read from stdin\n"
            "and write the formatted result to stdout."
        ),
    )
    p.add_argument(
        "--check",
        action="store_true",
        help=(
            "Don't modify the file, only report the status.\n"
            "Exit code 0 means nothing would change.\n"
            "Exit code 1 means the file would be reformatted."
        ),
    )
    p.add_argument("-V", "--version", action="version", version=__version__)
    sub = p.add_subparsers(help="Subcommands")

    new = sub.add_parser("new", help="Create a new changelog")
    new.set_defaults(func=create_new)
    new.add_argument(
        "-f", "--force", action="store_true", help="Overwrite existing file"
    )

    return p


def main() -> None:
    args = build_arg_parser().parse_args()
    try:
        args.func(args)
    except Exception as e:
        sys.exit(f"ERROR: {e}")


def _full_path(path: Path) -> Path:
    if path.is_dir():
        path /= DEFAULT_PATH
    return path


def format(args: argparse.Namespace) -> None:
    is_stdin = str(args.path) == "-"
    if is_stdin:
        orig = sys.stdin.read()
    else:
        path = _full_path(args.path)
        orig = path.read_text()

    result = api.format(orig)

    if is_stdin:
        print(result, end="")
    elif result != orig:
        if args.check:
            sys.exit(f"ERROR: {path} would be reformatted")
        else:
            path.write_text(result)
            print(f"{path} was reformatted")
    else:
        print(f"{path} is well-formatted")


def create_new(args: argparse.Namespace) -> None:
    path = _full_path(args.path)

    if path.exists() and not args.force:
        sys.exit(f"ERROR: {path} exists (use --force to overwrite)")

    text = api.render_new_template()
    path.write_text(text)


if __name__ == "__main__":
    main()
