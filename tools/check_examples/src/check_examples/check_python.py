"""Check and lint Python files."""

from pathlib import Path
from .common import execute, file_exists, subdirectory_exists, list_files_of_suffix
from .terminal_utils import iprint_pass, iprint_fail


def check_python(directory: Path, fix: bool) -> int:
    """Check python code."""
    # List python files
    python_files = list_files_of_suffix(directory, ".py")
    if not python_files:
        return 0

    # Change directory to Python subdirectory if necessary
    python_directory = directory
    if subdirectory_exists(directory, "python"):
        python_directory = directory / "python"

    if file_exists(python_directory, "pdm.lock"):
        iprint_pass("pdm.lock found: use PDM", 1)
        return check_python_pdm(python_directory, fix)

    if file_exists(python_directory, "Pipfile"):
        iprint_pass("Pipfile found: use pipenv.", 1)
        return check_python_pipenv(python_directory, fix)

    if file_exists(python_directory, "requirements.txt"):
        iprint_pass("requirements.txt found: use venv and pip.", 1)
        return check_python_requirements(python_directory, fix)

    iprint_fail("Missing Pipfile or requirements.txt", 1)
    return 1


def check_python_pdm(directory: Path, fix: bool) -> int:
    """Check python using PDM if example provides pdm.lock."""
    return_code = 0
    # return_code |= execute(["pdm", "update", "-u", "--save-exact", "zaber-motion"], directory)
    return_code |= execute(["pdm", "install", "--dev"], directory)

    python_files = list_files_of_suffix(directory, ".py")
    python_filenames = [str(x.relative_to(directory)) for x in python_files]

    return_code |= run_linters(
        ["pdm", "run"],
        python_filenames,
        directory,
        fix,
    )
    return return_code


def check_python_pipenv(directory: Path, fix: bool) -> int:
    """Check python using pipenv if example provides Pipfile."""
    return_code = 0
    return_code |= execute(["pipenv", "clean"], directory)
    return_code |= execute(["pipenv", "install", "--dev"], directory)

    python_files = list_files_of_suffix(directory, ".py")
    python_filenames = [str(x.relative_to(directory)) for x in python_files]

    return_code |= run_linters(["pipenv", "run"], python_filenames, directory, fix)
    return return_code


def check_python_requirements(directory: Path, fix: bool) -> int:
    """Check python using pip and venv if example provides requirements.txt."""
    return_code = 0
    return_code |= execute(["rm", "-rf", ".venv"], directory)
    return_code |= execute(["python3", "-m", "venv", ".venv"], directory)
    if return_code:
        return return_code

    return_code |= execute(
        [".venv/bin/python3", "-m", "pip", "install", "--upgrade", "pip"], directory
    )

    return_code |= execute(
        [".venv/bin/python3", "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"],
        directory,
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
    )

    python_files = list_files_of_suffix(directory, ".py")
    python_filenames = [str(x.relative_to(directory)) for x in python_files]

    return_code |= run_linters([".venv/bin/python3", "-m"], python_filenames, directory, fix)

    return return_code


def run_linters(
    command_prefix: list[str], python_filenames: list[str], directory: Path, fix: bool
) -> int:
    """Run a set of linters in the appropriate virtual environment."""
    return_code = 0

    def lint_files(command: list[str]) -> int:
        """Lint files using venv."""
        return execute(command_prefix + command + python_filenames, directory)

    if fix:
        return_code |= lint_files(["black", "-l100"])
    else:
        return_code |= lint_files(["black", "-l100", "--check"])
    return_code |= execute(["pdm", "run", "pylint", "--version"], directory)
    return_code |= lint_files(["pylint", "--score=n"])
    return_code |= lint_files(["pydocstyle"])
    return_code |= lint_files(["mypy", "--strict"])

    return return_code
