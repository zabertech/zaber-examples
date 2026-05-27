"""Check and lint Python files."""

import tomllib
from pathlib import Path

from .common import (
    execute,
    file_exists,
    get_git_root_directory,
    list_files_of_suffix,
    subdirectory_exists,
)
from .terminal_utils import iprint_fail, iprint_pass


def check_python(directory: Path, *, fix: bool) -> int:
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
        return check_python_pdm(python_directory, fix=fix)

    if file_exists(python_directory, "Pipfile"):
        iprint_pass("Pipfile found: use pipenv.", 1)
        return check_python_pipenv(python_directory, fix=fix)

    if file_exists(python_directory, "requirements.txt"):
        iprint_pass("requirements.txt found: use venv and pip.", 1)
        return check_python_requirements(python_directory, fix=fix)

    if file_exists(python_directory, "uv.lock"):
        iprint_pass("uv.lock found: use uv.", 1)
        return check_python_uv(python_directory, fix=fix)

    iprint_fail("Missing Pipfile or requirements.txt", 1)
    return 1


def check_python_pdm(directory: Path, *, fix: bool) -> int:
    """Check python using PDM if example provides pdm.lock."""
    return_code = 0
    return_code |= execute(["pdm", "install", "--dev"], directory)
    return_code |= run_legacy_linters(["pdm", "run"], directory, fix=fix)
    return return_code


def check_python_pipenv(directory: Path, *, fix: bool) -> int:
    """Check python using pipenv if example provides Pipfile."""
    return_code = 0
    return_code |= execute(["pipenv", "clean"], directory)
    return_code |= execute(["pipenv", "install", "--dev"], directory)
    return_code |= run_legacy_linters(["pipenv", "run"], directory, fix=fix)
    return return_code


def check_python_requirements(directory: Path, *, fix: bool) -> int:
    """Check python using pip and venv if example provides requirements.txt."""
    return_code = 0
    return_code |= execute(["rm", "-rf", ".venv"], directory)
    return_code |= execute(["python3", "-m", "venv", ".venv"], directory)
    if return_code:
        return return_code

    return_code |= execute([".venv/bin/python3", "-m", "pip", "install", "--upgrade", "pip"], directory)

    return_code |= execute(
        [".venv/bin/python3", "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"],
        directory,
    )

    return_code |= run_legacy_linters([".venv/bin/python3", "-m"], directory, fix=fix)

    return return_code


def check_python_uv(directory: Path, *, fix: bool) -> int:
    """Check python using uv if example provides uv.lock."""
    return_code = 0
    return_code |= check_uv_tooling_config(directory)
    return_code |= execute(["uv", "sync", "--frozen"], directory)
    return_code |= run_uv_linters(["uv", "run"], directory, fix=fix)
    return return_code


def check_uv_tooling_config(directory: Path) -> int:
    """Verify pyproject.toml extends the shared ruff and pyright configs."""
    pyproject_path = directory / "pyproject.toml"
    if not pyproject_path.exists():
        iprint_fail("pyproject.toml not found", 1)
        return 1

    with Path.open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    tooling_config = get_git_root_directory() / "tools" / "tooling_config"
    expected_ruff = (tooling_config / "zaber-ruff.toml").resolve()
    expected_pyright = (tooling_config / "zaber-pyright.toml").resolve()

    return_code = 0

    try:
        ruff_config = config["tool"]["ruff"]
        ruff_extend = ruff_config.get("extend", None)

        if not ruff_extend:
            iprint_fail(
                f"pyproject.toml [tool.ruff] missing 'extend'.\
                [tool.ruff] extend must point to {expected_ruff}",
                1,
            )
            return_code = 1
        elif (directory / ruff_extend).resolve() != expected_ruff:
            iprint_fail(f"[tool.ruff] extend must point to {expected_ruff}", 1)
            return_code = 1
        else:
            iprint_pass("[tool.ruff] extend correct", 1)

    except KeyError:
        iprint_fail("pyproject.toml missing [tool.ruff]", 1)
        return_code = 1

    try:
        pyright_config = config["tool"]["pyright"]
        pyright_extends = pyright_config.get("extends", None)

        if not pyright_extends:
            iprint_fail(
                f"pyproject.toml [tool.pyright] missing 'extends'.\
                Must point to {expected_pyright}",
                1,
            )
            return_code = 1
        elif (directory / pyright_extends).resolve() != expected_pyright:
            iprint_fail(f"[tool.pyright] extends must point to {expected_pyright}", 1)
            return_code = 1
        else:
            iprint_pass("[tool.pyright] extend correct", 1)

    except KeyError:
        iprint_fail("pyproject.toml missing [tool.pyright]", 1)
        return_code = 1

    return return_code


def run_legacy_linters(command_prefix: list[str], directory: Path, *, fix: bool) -> int:
    """Run a set of linters in the appropriate virtual environment."""
    return_code = 0

    python_files = list_files_of_suffix(directory, ".py")
    python_filenames = [str(x.relative_to(directory)) for x in python_files]

    def lint_files(command: list[str]) -> int:
        """Lint files using venv."""
        return execute(command_prefix + command + python_filenames, directory)

    if fix:
        return_code |= lint_files(["black", "-l130"])
    else:
        return_code |= lint_files(["black", "-l130", "--check"])
    return_code |= lint_files(["pylint", "--score=n"])
    return_code |= lint_files(["pydocstyle"])
    return_code |= lint_files(["mypy", "--strict"])

    return return_code


def run_uv_linters(command_prefix: list[str], directory: Path, *, fix: bool) -> int:
    """Run a set of linters in the appropriate virtual environment."""
    return_code = 0

    def lint_files(command: list[str]) -> int:
        """Lint files using venv."""
        return execute(command_prefix + command, directory)

    if fix:
        return_code |= lint_files(["ruff", "format"])
        return_code |= lint_files(["ruff", "check", "--fix"])
    else:
        return_code |= lint_files(["ruff", "format", "--check"])
        return_code |= lint_files(["ruff", "check"])

    return_code |= lint_files(["pyright", str(directory)])

    return return_code
