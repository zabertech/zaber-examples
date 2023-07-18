# Check Examples
This script checks all the example directories for having all the required files,
and performs linting as required on various languages.

This script is also used by GitHub Actions,
and called from `.github/workflows/check_examples.yml`

## Dependency
The script uses `pipenv` and the dependencies are listed in `Pipfile`

The only 3rd party module the script depends on is `docopt`.

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
- `check all --ignore`: check all examples except files and directories listed in `ignore.txt`
- `check search <examples>...`: check specific examples
