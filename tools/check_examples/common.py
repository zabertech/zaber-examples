"""Common helper functions."""

import sys
import subprocess
from pathlib import Path

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "
INDENT = 4
IGNORE_FILE = "ignore.txt"

ignore_list: list[Path] = []


def iprint(message: str, indent: int) -> None:
    """Print with indent level."""
    lines = message.splitlines(True)
    indented_lines = [" " * INDENT * indent + line for line in lines if line.strip()]
    block = "".join(indented_lines)
    if block.strip():
        print(block)


def iprint_pass(message: str, indent: int = 0) -> None:
    """Print with PASS icon."""
    print(" " * INDENT * indent + PASS + " " + message)


def iprint_fail(message: str, indent: int = 0) -> None:
    """Print with PASS icon."""
    print(" " * INDENT * indent + FAIL + " " + message)


def iprint_warn(message: str, indent: int = 0) -> None:
    """Print with PASS icon."""
    print(" " * INDENT * indent + WARN + " " + message)


def execute(command: list[str], cwd: Path, indent: int) -> int:
    """Execute subprocess.run and print appropriate message."""
    result = subprocess.run(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode:
        iprint_fail(" ".join(command), indent)
        iprint(result.stdout, indent)
    else:
        iprint_pass(" ".join(command), indent)
    return result.returncode


def file_exists(directory: Path, filename: str) -> bool:
    """Check if a file exists in a directory."""
    filepath = directory / filename
    if filepath.exists() and filepath.is_file():
        return True
    return False


def subdirectory_exists(directory: Path, subdirectory: str) -> bool:
    """Check if a subdirectory exists in a directory."""
    filepath = directory / subdirectory
    if filepath.exists() and filepath.is_dir():
        return True
    return False


def get_git_root_directory() -> Path:
    """Return the git root directory regardless of where the script is executed from."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    directory = Path(result.stdout.strip())
    if not directory.exists() or not directory.is_dir():
        iprint_fail("Unable to find git root directory.", 0)
        sys.exit(1)
    return directory


def load_ignore() -> None:
    """Load list of directories and files to ignore."""
    if not ignore_list:
        git_root = get_git_root_directory()
        with open(IGNORE_FILE, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line[0] == "#":
                    continue
                ignore_filepath = git_root / line
                if ignore_filepath.exists():
                    ignore_list.append(ignore_filepath)
                    if ignore_filepath.is_dir():
                        iprint_warn(f"Ignoring directory: '{ignore_filepath}'")
                    if ignore_filepath.is_file():
                        iprint_warn(f"Ignoring file: '{ignore_filepath}'")
                else:
                    iprint_fail(
                        f"Ignoring '{line.rstrip()}' in {IGNORE_FILE} not found, unable to ignore."
                    )


def filter_ignore(filepath: Path) -> bool:
    """Check if a file or directory is in ignore.txt."""
    if filepath in ignore_list:
        return False
    return True
