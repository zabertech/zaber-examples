"""Provide screen printing and string manipulation utilities."""

from enum import Enum


class AnsiEscape(Enum):
    """ANSI Escape codes for color and styling of text."""

    # https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    # https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_(Select_Graphic_Rendition)_parameters
    BOLD = 1
    UNDERLINE = 4


def color_text(string: str, color: AnsiEscape) -> str:
    """
    Color text using terminal escape code.

    Args:
        string: String to color
        color: color escape code

    Returns:
        ANSI terminal compatible escape string
    """
    return f"\033[{color.value};{AnsiEscape.BOLD.value}m{string}\033[0m"


PASS = color_text("[PASS]", AnsiEscape.GREEN)
FAIL = color_text("[FAIL]", AnsiEscape.RED)
WARN = color_text("[WARN]", AnsiEscape.YELLOW)
INFO = color_text("[INFO]", AnsiEscape.CYAN)
INDENT = " " * 4


def iprint(message: str, indent: int) -> None:
    """Print with indent level."""
    lines = message.splitlines(True)
    indented_lines = [INDENT * indent + line for line in lines if line.strip()]
    block = "".join(indented_lines)
    if block.strip():
        print(block)


def iprint_pass(message: str, indent: int = 0) -> None:
    """Print with PASS icon."""
    print(INDENT * indent + PASS + " " + message)


def iprint_fail(message: str, indent: int = 0) -> None:
    """Print with FAIL icon."""
    print(INDENT * indent + FAIL + " " + message)


def iprint_warn(message: str, indent: int = 0) -> None:
    """Print with WARN icon."""
    print(INDENT * indent + WARN + " " + message)


def iprint_info(message: str, indent: int = 0) -> None:
    """Print with INFO icon."""
    print(INDENT * indent + INFO + " " + message)


def match_string(fragment: str | None, options: list[str]) -> tuple[str | None, str]:
    """Match a fragment of a string to options.

    Args:
        fragment: a string to match to available options
        options: list of available options to choose from

    Returns:
        A tuple (match, message) where:
            single_match: either the match, or if no match return None
            message: the message regarding the match
    """
    if not fragment:
        message = "please specify"
        return None, message
    matching: list[str] = []
    for item in options:
        if fragment in item:
            matching.append(item)
    match matching:
        case []:
            message = f"no match for '{fragment}'"
            return None, message
        case [single_match]:
            if fragment == single_match:
                message = f"found exact match for '{single_match}'"
            else:
                message = f"found unique match for '{single_match}'"
            return single_match, message
        case _:
            for item in matching:
                if fragment == item:
                    message = f"multiple matches, using exact match for '{item}'"
                    return item, message
            message = f"multiple match for '{fragment}', be more specific"
            return None, message
