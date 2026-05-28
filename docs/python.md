# Python Checklist

This is a checklist for contributing Python example code to this repository.

- [ ] The code example should compatible with Python 3.10 and above.
- [ ] The `README.md` and all other markdown documents should pass linting
with [pymarkdownlnt](https://github.com/jackdewinter/pymarkdown).
- [ ] The code example should use [uv](https://docs.astral.sh/uv/).
- [ ] The code must pass the following linter / type checkers:
  - [ ] Use [Ruff](https://docs.astral.sh/ruff/tutorial/) with the Zaber recommended configuration.
    - The `.pyproject.toml` file for the directory must extend the [Zaber Ruff config](../tools/tooling_config/zaber-ruff.toml). An example can found in the [templates folder](../examples/_template/python_uv/pyproject.toml).
    - `uv run ruff format <filename.py> # format the code`
    - `uv run ruff check <filename.py> # lint the code`
  - [ ] Use [Pyright](https://microsoft.github.io/pyright/#/) with the recommended Zaber Configuration for type-checking
    - The `.pyproject.toml` file for the directory must extend the [Zaber Pyright config](../tools/tooling_config/zaber-pyright.toml). An example can found in the [templates folder](../examples/_template/python_uv/pyproject.toml).
    - `uv run pyright <filename.py>`

The [CI script](../.github/workflows/check_examples.yml) will automatically call the [`check_example` script](../tools/check_examples/) to run the linters. The [`check_example` script](../tools/check_examples/) can be called manually using `uv run check` before
committing changes or doing a pull request.  All of the checks must pass before contribution can be merged.

## Note For Older Examples

This repo previously used a different set up of package managers and linting/formatting tools. As a result, the older examples in this repo may not conform the checklist above. Read the [old checklist](./archive/python-old.md) for more details.
