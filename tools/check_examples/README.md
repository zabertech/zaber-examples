# Check Examples

This script checks that all the example directories have the required files,
and performs linting as required for various languages.

For Python examples, the script looks for `pdm.lock`, `Pipfile` or `requirements.txt`
and uses `pdm`, `pipenv` or `venv` to create virtual environments and install dependencies as needed.

This script is also used by GitHub Actions,
and called from `.github/workflows/check_examples.yml`

## Dependency

The script uses `pdm` and the dependencies are listed in [`pyproject.toml`](pyproject.toml)

## Installing the script

To install the script:

    pip install --user --upgrade pdm
    cd tools/check_examples
    pdm install --dev
    pdm check

## Commands

Examples of how to use the script:

- `pdm check --help`: list usage options
- `pdm check all`: check all files
- `pdm check changed`: check all changed examples
- `pdm check docs`: lint all markdown files in the /docs/ subdirectory
- `pdm check list`: list example directories that would be checked
- `pdm check self`: lint the check_example script itself.
- `pdm check <example>`: check specific examples

## Note

Currently the check script uses [pymarkdownlnt](https://github.com/jackdewinter/pymarkdown/),
which has some bugs and limitations.  For example, it doesn't detect all instances of
needing space around lists (rule [MD032](https://github.com/jackdewinter/pymarkdown/blob/main/docs/rules/rule_md032.md)).  The Python markdown linter should be replaced by
something a bit more robust, perhaps from the Javascript ecosystem.
