"""Check and lint Python files."""

import subprocess
from pathlib import Path
from common import execute, iprint_pass, iprint_fail, file_exists, subdirectory_exists, ignore


def list_python_files(directory: Path) -> list[Path]:
    """Return a list of python files in a directory."""
    result = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=True,
    )
    python_filenames = result.stdout.strip().split()
    list_filepaths = [directory.joinpath(x) for x in python_filenames]
    list_filepaths = list(filter(ignore, list_filepaths))
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


def check_python_pip(directory: Path, indent: int) -> int:
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


def check_python_pipenv(directory: Path, indent: int) -> int:
    """Check python if example provides Pipfile."""
    return_code = 0
    return_code |= execute(
        ["pipenv", "clean"],
        directory,
        indent,
    )
    return_code |= execute(
        ["pipenv", "install", "-d"],
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

    if file_exists(python_directory, "Pipfile"):
        iprint_pass("Pipfile found: use pipenv.", indent)
        return check_python_pipenv(python_directory, indent)
    if file_exists(python_directory, "requirements.txt"):
        iprint_pass("requirements.txt found: use venv and pip.", indent)
        return check_python_pip(python_directory, indent)
    iprint_fail("Missing Pipfile or requirements.txt", indent)
    return 1
