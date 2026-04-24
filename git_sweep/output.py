"""Output helpers: print to stdout/stderr with optional colour."""

from __future__ import annotations

import sys
from typing import Optional

TRY_COLOR = True

try:
    import colorama  # type: ignore

    colorama.init(autoreset=True)
    _RED = colorama.Fore.RED
    _GREEN = colorama.Fore.GREEN
    _YELLOW = colorama.Fore.YELLOW
    _CYAN = colorama.Fore.CYAN
    _RESET = colorama.Style.RESET_ALL
except ImportError:  # pragma: no cover
    TRY_COLOR = False
    _RED = _GREEN = _YELLOW = _CYAN = _RESET = ""


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color or not TRY_COLOR:
        return text
    return f"{color}{text}{_RESET}"


def print_info(msg: str, use_color: bool = True) -> None:
    print(_colorize(msg, _CYAN, use_color))


def print_success(msg: str, use_color: bool = True) -> None:
    print(_colorize(msg, _GREEN, use_color))


def print_warning(msg: str, use_color: bool = True) -> None:
    print(_colorize(msg, _YELLOW, use_color), file=sys.stderr)


def print_error(msg: str, use_color: bool = True) -> None:
    print(_colorize(msg, _RED, use_color), file=sys.stderr)


def print_report(text: str, use_color: bool = True) -> None:
    """Print a full report block; section headers are highlighted."""
    for line in text.splitlines():
        if line.startswith("=" * 10):
            print(_colorize(line, _CYAN, use_color))
        elif line.startswith("  !"):
            print(_colorize(line, _RED, use_color))
        elif line.startswith("    -"):
            print(_colorize(line, _YELLOW, use_color))
        else:
            print(line)
