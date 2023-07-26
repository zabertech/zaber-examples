"""
Check example directories.

This script may also be called by .github/workflows/check_examples.yml

Usage:
    check all
    check changed
    check list
    check search <examples>...
    check -h | --help

Options:
    -h --help           Show help screen.

For more information see README.md
"""

from typing import Any
import sys
import subprocess
from pathlib import Path
from docopt import docopt
from common import (
    iprint,
    iprint_pass,
    iprint_fail,
    iprint_info,
    filter_ignore,
    load_ignore,
    get_git_root_directory,
)
from check_python import check_python
from check_basic import check_basic

Args = dict[str, Any]


def main() -> None:
    """Check example directories."""
    print("*** Check example directories ***")

    arguments = sys.argv[1:]
    args = docopt(__doc__, argv=arguments)

    if args["all"]:
        exit_code = cmd_check_all(args)
    elif args["changed"]:
        exit_code = cmd_check_changed(args)
    elif args["list"]:
        exit_code = cmd_check_list(args)
    elif args["<examples>"]:
        exit_code = cmd_check_examples(args)
    else:
        exit_code = 1  # should never get here.

    print()
    print("=== Summary ===")
    if exit_code:
        iprint_fail("One or more check(s) failed.")
    else:
        iprint_pass("Success")

    sys.exit(exit_code)


def cmd_check_all(_: Args) -> int:
    """Check all examples."""
    print("=== Check all examples ===")
    return_code = 0
    load_ignore()
    example_directories = list_example_directories()
    for example in example_directories:
        iprint_pass(f"Found '{example}'", 0)
    print(f"Found {len(example_directories)} example subdirectories in 'src':")
    for example in example_directories:
        return_code |= check_example(example, indent=1)
    return return_code


def cmd_check_changed(_: Args) -> int:
    """Check changed examples."""
    print("=== Check all changed examples ===")
    return_code = 0
    load_ignore()
    list_examples = list_example_directories()
    list_changed = list_changed_files()
    for item in list_changed:
        iprint_info(f"Found changed file '{item}'")
    changed_examples: list[Path] = []
    for example in list_examples:
        for changed_file in list_changed:
            if changed_file.is_relative_to(example) and example not in changed_examples:
                changed_examples.append(example)
    for example in changed_examples:
        iprint_pass(f"Found changed example '{example}'", 0)
    print(f"Found {len(changed_examples)} changed example subdirectories in 'src':")
    for example in changed_examples:
        return_code |= check_example(example, indent=1)
    return return_code


def cmd_check_list(_: Args) -> int:
    """List examples."""
    print("=== List examples ===")
    load_ignore()
    list_examples = list_example_directories()
    print(f"Found {len(list_examples)} example subdirectories in 'src':")
    for example in list_examples:
        iprint(str(example.relative_to(example.parent)), 1)
    return 0


def cmd_check_examples(args: Args) -> int:
    """Check specific example(s)."""
    print("=== Check specific example(s) ===")
    return_code = 0
    search_examples = args["<examples>"]
    load_ignore()
    list_examples = list_example_directories()
    example_names = [str(x.relative_to(x.parent)) for x in list_examples]
    match_examples = []
    for example in search_examples:
        if example in example_names:
            iprint_pass(f"Found exact match '{example}'", 0)
            match_examples.append(example)
        elif any(example in x for x in example_names):
            for name in example_names:
                if example in name:
                    iprint_pass(f"Found partial match '{name}'", 0)
                    match_examples.append(name)
        else:
            iprint_fail(f"Unable to find example '{example}'", 0)
            return_code = 1

    git_root = get_git_root_directory()
    example_directories = [git_root / "src" / x for x in match_examples]
    print(f"Found {len(example_directories)} example(s) to check.")
    for example in example_directories:
        return_code |= check_example(example, indent=1)

    return return_code


def list_example_directories() -> list[Path]:
    """Return a list of example directories."""
    git_root_directory = get_git_root_directory()
    list_filepaths = list(git_root_directory.joinpath("src").iterdir())
    list_directories = [x for x in list_filepaths if x.is_dir()]
    if not list_directories:
        iprint_fail("Unable to list example directories.", 0)
        sys.exit(1)
    list_directories = list(filter(filter_ignore, list_directories))
    return sorted(list_directories)


def list_changed_files() -> list[Path]:
    """Return a list of changed files."""
    # add all changed files
    result = subprocess.run(["git", "status", "-s"], capture_output=True, text=True, check=False)
    filenames_changed = result.stdout.strip().split("\n")
    filenames_changed = [x[3:] for x in filenames_changed]
    filepaths_changed = [(Path.cwd() / filename).resolve() for filename in filenames_changed]
    return filepaths_changed


def check_example(directory: Path, indent: int) -> int:
    """Perform check on each example."""
    print()
    print(f"--- Checking: {directory.relative_to(directory.parent)} ---")

    return_code = 0
    return_code |= check_basic(directory, indent)
    return_code |= check_python(directory, indent)
    # Can add other languages here such as check_csharp(), check_html(), etc.
    return return_code


if __name__ == "__main__":
    main()
