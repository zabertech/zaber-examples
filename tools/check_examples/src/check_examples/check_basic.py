"""Check for basic requirements of example repositories."""

from datetime import datetime
from pathlib import Path
from subprocess import run

import yaml

from .common import file_exists, list_files_of_suffix, execute, get_git_root_directory
from .terminal_utils import iprint_fail, iprint_pass, iprint_warn
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


def check_lastmod_date(directory: Path) -> int:
    """Check that the updated_date field exists and appears to make sense."""
    with open(directory.joinpath("article.yml"), "r") as stream:
        meta = yaml.safe_load(stream)
    updated_date = meta["updated_date"]
    if updated_date is None:
        iprint_fail("article.yml does not contain the updated_date field.", 1)
        return 1

    extensions = [".py", ".cs", ".md", ".ui", ".bat", ".sh", ".cpp", ".h", ".swift"]
    for ext in extensions:
        for file in list_files_of_suffix(directory, ext):
            iprint_pass(f"Checking {file}...", 1)
            output = run(["git", "--no-pager", "log", "-1", "--format=\"%as\"", "--", str(file)],
                check=True,
                capture_output=True)
            try:
                file_date = datetime.strptime(output.stdout.decode("utf-8").strip().strip("\""), "%Y-%m-%d").date()
                if file_date > updated_date:
                    iprint_warn(f"{file} has a revision date newer than updated_date in article.yaml", 1)
            except ValueError:
                iprint_warn(f"Could not get revision date of {file} - maybe it's not in git yet?", 1)
                iprint_warn("Consider updating the updated_date field in article.yaml", 1)

    return 0
