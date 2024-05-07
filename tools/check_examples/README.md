# Check Examples

This script checks that all the example directories have the required files,
and performs linting as required for various languages.

For Python examples, the script looks for `Pipfile` or `requirements.txt`
and uses `pipenv` or `venv` to create virtual environments and install dependencies as needed.

This script is also used by GitHub Actions,
and called from `.github/workflows/check_examples.yml`

## Dependency

The script uses `pipenv` and the dependencies are listed in `Pipfile`

## Installing the script

To install the script:

    pip install --user --upgrade pipenv
    cd tools/check_examples
    pipenv install -d
    alias check='pipenv run python check.py'

## Commands

Examples of how to use the script:

- `check --help`: list usage options
- `check all`: check all files
- `check changed`: check all changed examples
- `check docs`: lint all markdown files in the /docs/ subdirectory
- `check list`: list example directories that would be checked
- `check self`: lint the check_example script itself.
- `check <example>`: check specific examples

## Note

Currently the check script uses [pymarkdownlnt](https://github.com/jackdewinter/pymarkdown/),
which has some bugs and limitations.  For example, it doesn't detect all instances of
needing space around lists (rule [MD032](https://github.com/jackdewinter/pymarkdown/blob/main/docs/rules/rule_md032.md)).  The Python markdown linter should be replaced by
something a bit more robust, perhaps from the Javascript ecosystem.
