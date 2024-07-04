# Check Examples

This script checks that all the example directories have the required files,
updates ZML to the latest version (if included as a dependency),
and performs linting as required for various languages.

For Python examples, the script looks for `pdm.lock`, or `Pipfile`
and uses `pdm`, `pipenv` or `venv` to create virtual environments and install dependencies as needed.

This script is also used by GitHub Actions,
and called from `.github/workflows/check_examples.yml`

## Dependency

The script uses [`markdownlint-cli2`](https://github.com/DavidAnson/markdownlint-cli2)
to lint markdown files, and needs [`Node.js`](https://nodejs.org/en) to install and run.

Configure `markdownlint-cli2` rules via [`.markdownlint.jsonc`](../../.markdownlint.jsonc)
in the project root directory.

The script uses [`pdm`](https://pdm-project.org/en/latest/) to manage virtual environment
and Python dependencies.  See [`pyproject.toml`](pyproject.toml) for more detail.

## Installing the script

To install the script:

    pip install --user --upgrade pdm
    cd tools/check_examples
    npm install
    pdm install --dev
    pdm check

## Commands

Examples of how to use the script:

- `pdm check --help`: list usage options
- `pdm check all`: check all files
- `pdm check changed`: check all changed examples
- `pdm check docs`: lint all markdown files in the /docs/ subdirectory
- `pdm check list`: list example directories that would be checked
- `pdm check self`: lint the check_example script itself
- `pdm check <example>`: check a specific example
