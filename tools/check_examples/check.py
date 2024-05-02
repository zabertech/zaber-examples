"""
Check example directories.

This script may also be called by .github/workflows/check_examples.yml

Usage:
    check all [-fm]
    check changed [-fm]
    check docs
    check list
    check self [-f]
    check <example> [-fm]
    check -h | --help

Options:
    -h --help           Show help screen.
    -f --fix            Fix fixable issues (i.e. black)
    -m --markdown       Check markdown files in examples

For more information see README.md
"""

from typing import Any
import sys
import subprocess
from pathlib import Path
from docopt import docopt
from common import filter_not_ignored, load_ignore, get_git_root_directory
from terminal_utils import iprint, iprint_pass, iprint_fail, iprint_info, match_string
from check_python import check_python
from check_basic import check_basic, check_markdown

Args = dict[str, Any]


def main() -> None:
    """Check example directories."""
    print("*** Check example directories ***")

    arguments = sys.argv[1:]
    args = docopt(__doc__, argv=arguments)

    exit_code = 0
    if args["all"]:
        exit_code |= cmd_check_self(args)
        exit_code |= cmd_check_docs(args)
        exit_code |= cmd_check_all(args)
    elif args["changed"]:
        exit_code |= cmd_check_changed(args)
    elif args["docs"]:
        exit_code |= cmd_check_docs(args)
    elif args["list"]:
        exit_code |= cmd_check_list(args)
    elif args["self"]:
        exit_code |= cmd_check_self(args)
    elif args["<example>"]:
        exit_code |= cmd_check_examples(args)
    else:
        exit_code = 1  # should never get here.

    print()
    print("=== Summary ===")
    if exit_code:
        iprint_fail("One or more check(s) failed.")
    else:
        iprint_pass("Success")

    sys.exit(exit_code)


def cmd_check_all(args: Args) -> int:
    """Check all examples."""
    print("=== Check all examples ===")
    return_code = 0
    fix = args["--fix"]
    markdown = args["--markdown"]
    load_ignore()
    example_directories = list_example_directories()
    for example in example_directories:
        iprint_info(f"Found '{example}'", 1)
    iprint(f"Found {len(example_directories)} example subdirectories in 'src':", 1)
    for example in example_directories:
        return_code |= check_example(example, fix, markdown)
    return return_code


def cmd_check_changed(args: Args) -> int:
    """Check changed files."""
    # Note: this is a placeholder function.  Doesn't work yet.
    print("=== Check all changed files ===")
    return_code = 0
    fix = args["--fix"]
    markdown = args["--markdown"]
    load_ignore()
    list_examples = list_example_directories()
    list_changed = list_changed_files()
    for item in list_changed:
        iprint(f"Found changed file '{item}'", 1)

    # Determine which directories to run checks on
    changed_examples: list[Path] = []
    changed_self: bool = False
    changed_docs: bool = False
    self_directory = get_git_root_directory() / "tools" / "check_examples"
    docs_dierctory = get_git_root_directory() / "docs"
    for changed_file in list_changed:
        if changed_file.is_relative_to(self_directory):
            changed_self = True
        if changed_file.is_relative_to(docs_dierctory):
            changed_docs = True
        for example in list_examples:
            if changed_file.is_relative_to(example) and example not in changed_examples:
                changed_examples.append(example)

    # Indicate which directories to run checks on
    if changed_self:
        iprint_info("Found changed files in check_examples script.", 1)
    if changed_docs:
        iprint_info("Found changed files in docs/ subdirectory.", 1)
    iprint_info(f"Found {len(changed_examples)} changed example subdirectories in 'src':", 1)
    for example in changed_examples:
        iprint(f"Found changed example '{example}'", 2)
    print()

    # Run checks
    if changed_self:
        cmd_check_self(args)
    if changed_docs:
        cmd_check_docs(args)
    print("=== Check changed examples ===")
    for example in changed_examples:
        return_code |= check_example(example, fix, markdown)
    return return_code


def cmd_check_docs(_: Args) -> int:
    """Check markdowns in documentation folder."""
    print("=== Check docs subdirecotry ===")
    return_code = 0
    docs_directory = get_git_root_directory()
    return_code |= check_markdown(docs_directory, recurse=False)
    docs_directory = get_git_root_directory() / "docs"
    return_code |= check_markdown(docs_directory)
    print()
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


def cmd_check_self(args: Args) -> int:
    """Check this code itself."""
    print("=== Self check ===")
    return_code = 0
    fix = args["--fix"]
    self_directory = get_git_root_directory() / "tools" / "check_examples"
    print()
    print(f"--- Self-check: {self_directory} ---")
    return_code |= check_markdown(self_directory)
    return_code |= check_python(self_directory, fix)
    print()
    return return_code


def cmd_check_examples(args: Args) -> int:
    """Check specific example(s)."""
    print("=== Check specific example(s) ===")
    return_code = 0
    fix = args["--fix"]
    markdown = args["--markdown"]
    search_term = args["<example>"]
    load_ignore()
    list_examples = list_example_directories()
    example_names = [str(x.relative_to(x.parent)) for x in list_examples]
    match_example, message = match_string(search_term, example_names)
    print(message)
    if not match_example:
        for name in example_names:
            iprint(name, 1)
        return 1
    git_root = get_git_root_directory()
    example_to_check = git_root / "src" / match_example
    return_code |= check_example(example_to_check, fix, markdown)
    return return_code


def list_example_directories() -> list[Path]:
    """Return a list of example directories."""
    git_root_directory = get_git_root_directory()
    list_filepaths = list(git_root_directory.joinpath("src").iterdir())
    list_directories = [x for x in list_filepaths if x.is_dir()]
    if not list_directories:
        iprint_fail("Unable to list example directories.", 0)
        sys.exit(1)
    list_directories = list(filter(filter_not_ignored, list_directories))
    return sorted(list_directories)


def list_changed_files() -> list[Path]:
    """Return a list of changed or untracked files."""
    result = subprocess.run(["git", "status", "-su"], capture_output=True, text=True, check=False)
    filenames_changed = result.stdout.rstrip().split("\n")
    filenames_changed = [x[3:] for x in filenames_changed]
    filepaths_changed = [(Path.cwd() / filename).resolve() for filename in filenames_changed]
    return filepaths_changed


def check_example(directory: Path, fix: bool, markdown: bool) -> int:
    """Perform check on each example."""
    print()
    print(f"--- Checking: {directory.relative_to(directory.parent)} ---")

    return_code = 0
    return_code |= check_basic(directory)
    if markdown:
        return_code |= check_markdown(directory)
    return_code |= check_python(directory, fix)
    # Can add other languages here such as check_csharp(), check_html(), etc.
    return return_code


if __name__ == "__main__":
    main()
