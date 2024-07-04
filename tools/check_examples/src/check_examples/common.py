"""Common helper functions."""

from typing import Generator
import sys
import os
import subprocess
from pathlib import Path
from .terminal_utils import iprint, iprint_pass, iprint_fail, iprint_warn

IGNORE_FILE = "ignore.txt"

ignore_list: list[Path] = []


def execute(command: list[str], cwd: Path) -> int:
    """Execute subprocess.run and print appropriate message."""
    env = dict(os.environ)
    del env["VIRTUAL_ENV"]
    result = subprocess.run(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        env=env,
    )
    if result.returncode:
        iprint_fail(" ".join(command), 1)
        iprint(result.stdout, 1)
    else:
        iprint_pass(" ".join(command), 1)
        iprint(result.stdout, 1)
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


def list_files_of_suffix(directory: Path, file_suffix: str, recurse: bool = True) -> list[Path]:
    """Return a list of python files in a directory."""

    def get_python_files(currdir: Path) -> Generator[Path, None, None]:
        """Yield all .py files recursively, excluding directories that start with a period."""
        for item in currdir.iterdir():
            if item.name[0] == ".":  # ignore files starting with a "."
                continue
            if item.suffix == file_suffix:
                yield item
            if item.is_dir() and filter_not_ignored(item) and recurse:
                yield from get_python_files(item)

    list_filepaths = list(get_python_files(directory))
    list_filepaths = list(filter(filter_not_ignored, list_filepaths))
    return sorted(list_filepaths)


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
                    if ignore_filepath not in ignore_list:
                        ignore_list.append(ignore_filepath)
                        if ignore_filepath.is_dir():
                            iprint_warn(f"Ignoring directory: '{ignore_filepath}'", 1)
                        if ignore_filepath.is_file():
                            iprint_warn(f"Ignoring file: '{ignore_filepath}'", 1)
                else:
                    iprint_fail(
                        f"Ignoring '{line.rstrip()}' in {IGNORE_FILE} not found, unable to ignore."
                    )
        print()


def filter_not_ignored(filepath: Path) -> bool:
    """Check if a file or directory is in ignore.txt or should be ignored otherwise."""
    if filepath in ignore_list:
        return False
    if "node_module" in str(filepath):
        return False
    return True
