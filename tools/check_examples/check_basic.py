"""Check for basic requirements of example repositories."""

from pathlib import Path
from common import file_exists
from terminal_utils import iprint_fail, iprint_pass


def check_basic(directory: Path, indent: int) -> int:
    """Check basic requirements of any example repository."""
    return_code = 0

    essential_files = ["README.md", "article.yml"]

    for file in essential_files:
        if not file_exists(directory, file):
            iprint_fail(f"{file} not found.", indent)
            return_code = 1
        else:
            iprint_pass(f"{file} found.", indent)

    return return_code
