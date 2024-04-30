"""Check and lint Python files."""

from typing import Generator
from pathlib import Path
from common import (
    execute,
    file_exists,
    subdirectory_exists,
    filter_not_ignored,
)
from terminal_utils import (
    iprint_pass,
    iprint_fail
)

def check_python(directory: Path, indent: int) -> int:
    """Check python code."""
    # List python files
    python_files = list_python_files(directory)
    if not python_files:
        return 0

    # Change directory to Python subdirectory if necessary
    python_directory = directory
    if subdirectory_exists(directory, "python"):
        python_directory = directory / "python"

    if file_exists(python_directory, "pdm.lock"):
        iprint_pass("pdm.lock found: use PDM", indent)
        return check_python_pdm(python_directory, indent)

    if file_exists(python_directory, "Pipfile"):
        iprint_pass("Pipfile found: use pipenv.", indent)
        return check_python_pipenv(python_directory, indent)
    
    if file_exists(python_directory, "requirements.txt"):
        iprint_pass("requirements.txt found: use venv and pip.", indent)
        return check_python_requirements(python_directory, indent)
    
    iprint_fail("Missing Pipfile or requirements.txt", indent)
    return 1


def check_python_pdm(directory: Path, indent: int) -> int:
    """Check python using PDM if example provides pdm.lock."""
    return_code = 0
    return_code |= execute(["pdm", "install", "-d"], directory, indent)

    python_files = list_python_files(directory)
    python_filenames = [str(x.relative_to(directory)) for x in python_files]
    
    return_code = run_linters(
        ["pdm", "run"],
        python_filenames,
        directory,
        indent,
    )
    return return_code


def check_python_pipenv(directory: Path, indent: int) -> int:
    """Check python using pipenv if example provides Pipfile."""
    return_code = 0
    return_code |= execute(
        ["pipenv", "--rm"],
        directory,
        indent,
    )
    return_code |= execute(
        ["pipenv", "install", "--dev"],
        directory,
        indent,
    )

    python_files = list_python_files(directory)
    python_filenames = [str(x.relative_to(directory)) for x in python_files]

    return_code = run_linters(
        ["pipenv", "run"],
        python_filenames,
        directory,
        indent,
    )
    return return_code


def check_python_requirements(directory: Path, indent: int) -> int:
    """Check python using pip and venv if example provides requirements.txt."""
    return_code = 0
    return_code |= execute(
        ["rm", "-rf", ".venv"],
        directory,
        indent,
    )
    return_code |= execute(
        ["python3", "-m", "venv", ".venv"],
        directory,
        indent,
    )
    if return_code:
        return return_code
    
    return_code |= execute(
        [".venv/bin/python3", "-m", "pip", "install", "--upgrade", "pip"],
        directory,
        indent,
    )

    return_code |= execute(
        [".venv/bin/python3", "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"],
        directory,
        indent,
    )
    return_code |= execute(
        [
            ".venv/bin/python3",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "black",
            "pylint",
            "pydocstyle",
            "mypy",
        ],
        directory,
        indent,
    )

    python_files = list_python_files(directory)
    python_filenames = [str(x.relative_to(directory)) for x in python_files]

    return_code = run_linters(
        [".venv/bin/python3", "-m"],
        python_filenames,
        directory,
        indent,
    )

    return return_code


def list_python_files(directory: Path) -> list[Path]:
    """Return a list of python files in a directory."""

    def get_python_files(currdir: Path) -> Generator[Path, None, None]:
        """Yield all .py files recursively, excluding directories that start with a period."""
        for item in currdir.iterdir():
            if item.name[0] == ".":  # ignore files starting with a "."
                continue
            if item.suffix == ".py":
                yield item
            if item.is_dir() and filter_not_ignored(item):
                yield from get_python_files(item)

    list_filepaths = list(get_python_files(directory))
    list_filepaths = list(filter(filter_not_ignored, list_filepaths))
    return sorted(list_filepaths)


def run_linters(
    command_prefix: list[str], python_filenames: list[str], directory: Path, indent: int
) -> int:
    """Run a set of linters in the appropriate virtual environment."""
    return_code = 0

    def lint_files(command: list[str]) -> int:
        """Lint files using venv."""
        return execute(
            command_prefix + command + python_filenames,
            directory,
            indent,
        )

    return_code |= lint_files(["black", "-l100", "--check"])
    return_code |= lint_files(["pylint", "--score=n"])
    return_code |= lint_files(["pydocstyle"])
    return_code |= lint_files(["mypy", "--strict"])

    return return_code