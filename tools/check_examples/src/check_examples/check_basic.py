"""Check for basic requirements of example repositories."""

from datetime import date
from pathlib import Path

import yaml

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
    tool_path = get_git_root_directory() / "tools/check_examples"
    config_path = Path("../../.markdownlint.jsonc")
    for file in markdown_files:
        filename = str(file)
        return_code |= execute(
            ["npx", "markdownlint-cli2", filename, "--config", str(config_path)], tool_path
        )
        return_code |= check_links_in_markdown(file)
    return return_code


def validate_article_metadata(directory: Path) -> int:
    """Check that the required yaml fields exist."""
    with open(directory.joinpath("article.yml"), "r", encoding="utf-8") as stream:
        meta = yaml.safe_load(stream)

    required_fields = {
        "date": date,
        "updated_date": date,
        "category": str,
        "picture": str,
    }

    for field, field_type in required_fields.items():
        if field not in meta:
            iprint_fail(f"article.yml does not contain the {field} field.", 1)
            return 1
        if not isinstance(meta[field], field_type):
            iprint_fail(f"article.yml {field} field is not of type {field_type.__name__}.", 1)
            return 1

    return 0
