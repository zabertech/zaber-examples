"""Check for basic requirements of example repositories."""

from pathlib import Path
from .common import file_exists, list_files_of_suffix, execute, get_git_root_directory
from .terminal_utils import iprint_fail, iprint_pass
from .markdown_links import check_links_in_markdown


def check_basic(directory: Path) -> int:
    """Check basic requirements of any example repository."""
    return_code = 0
    essential_files = ["README.md", "article.yml"]
    for file in essential_files:
        if not file_exists(directory, file):
            iprint_fail(f"{file} not found.", 1)
            return_code = 1
        else:
            iprint_pass(f"{file} found.", 1)
    return return_code


def check_markdown(directory: Path, recurse: bool = True) -> int:
    """Check markdown files."""
    return_code = 0
    markdown_files = list_files_of_suffix(directory, ".md", recurse=recurse)
    check_example_directory = get_git_root_directory() / "tools/check_examples"
    config_file = check_example_directory / "pymarkdownlnt.toml"
    for file in markdown_files:
        filename = str(file)
        return_code |= execute(
            ["pdm", "run", "pymarkdownlnt", "--config", str(config_file.name), "scan", filename],
            check_example_directory,
        )
        return_code |= check_links_in_markdown(file)
    return return_code
