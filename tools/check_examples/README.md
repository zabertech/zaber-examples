# Check Examples

This script checks that all the example directories have the required files,
updates ZML to the latest version (if included as a dependency),
and performs linting as required for various languages.

For Python examples, the script looks for `uv.lock`,`pdm.lock`, or `Pipfile`
and uses `uv`, `pdm`, `pipenv` or `venv` to create virtual environments and install dependencies as needed.
For `uv`, the script requires that the example's `ruff` and `pyright` configuration in `pyproject.toml` is extended from
the Zaber provided configuration files in `check_examples/tooling_config`.

This script is also used by GitHub Actions,
and called from `.github/workflows/check_examples.yml`

## Dependency

The script uses [`markdownlint-cli2`](https://github.com/DavidAnson/markdownlint-cli2)
to lint markdown files, and needs [`Node.js`](https://nodejs.org/en) to install and run.

Configure `markdownlint-cli2` rules via [`.markdownlint.jsonc`](../../.markdownlint.jsonc)
in the project root directory.

The script uses [`pdm`](https://pdm-project.org/en/latest/) to manage virtual environment
and Python dependencies.  See [`pyproject.toml`](pyproject.toml) for more detail.

## Commands

Examples of how to use the script:

- `uv run check --help`: list usage options
- `uv run check all`: check all files
- `uv run check changed`: check all changed examples
- `uv run check docs`: lint all markdown files in the /docs/ subdirectory
- `uv run check list`: list example directories that would be checked
- `uv run check self`: lint the check_example script itself
- `uv run check <example>`: check a specific example

Note: the first time the script is run, `uv` automatically installs required dependancies for the project.
