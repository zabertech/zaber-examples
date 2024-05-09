# Python Checklist

This is a checklist for contributing Python example code to this repository.

- [ ] Ideally examples are compatible with Python 3.10 and above.
- [ ] Ideally the `README.md` and all other markdown documents should pass linting
with [pymarkdownlnt](https://github.com/jackdewinter/pymarkdown).
- [ ] The code example should use some form of [package manager and virtual environment](python-virtual-environment.md).
- [ ] The code must pass the following linter / type checkers:
  - [ ] Use [Black code formatter](https://black.readthedocs.io) with override of line length of 100.
    - `black -l100 <filename.py>`
  - [ ] Use [Pylint](https://pypi.org/project/pylint/) with default configuration.
    - `pylint <filename.py>`
  - [ ] Use [mypy](https://mypy-lang.org/) with strict configuration.
    - `mypy --strict <filename.py>`
  - [ ] Use [pydocstyle](https://www.pydocstyle.org/en/stable/)
  to help write more readable docstrings according to [PEP 257](https://peps.python.org/pep-0257/).
    - `pydocstyle <filename.py>`

The [CI script](../.github/workflows/check_examples.yml) will automatically call
the [`check_example` script](../tools/check_examples/) to activate [supported virtual environments](python-virtual-environment.md)
and run the linters.  The [`check_example` script](../tools/check_examples/) can be called manually before
committing changes or doing a pull request.  All of the linters must pass before contribution can be merged.
