# Python Checklist
This is a checklist for contributing Python example code to this repository.

- [ ] Ideally examples are compatible with Python 3.10 and above.
- [ ] The code example should isolate its own dependencies using [virtual environment](virtual-environment.md).

We recommend running the following linters in the order listed below.

All of the linters may be obtained using `pip`:

    python3 -m pip install -U black pylint mypy pydocstyle

- [ ] Run [Black code formatter](https://black.readthedocs.io)
before the other linters will reduce the number of errors emitted.
Override with line length of 100.
  - `black -l100 <filename.py>`
- [ ] We recommend using [Pylint](https://pypi.org/project/pylint/)
with default configuration.
  - `pylint <filename.py>`
- [ ] We recommend static type checking with [mypy](https://mypy-lang.org/)
using strict configuration
  - `mypy --strict <filename.py>`
- [ ] Optionally, use [pydocstyle](https://www.pydocstyle.org/en/stable/)
to help write more readable docstrings according to [PEP 257](https://peps.python.org/pep-0257/).
  - `pydocstyle <filename.py>`

We recommend using [Pipenv](https://pipenv.pypa.io/en/latest/).
If you are using `pipenv`, make sure you are in `/src/<example_directory>/python/`:

    pipenv install --dev black pylint mypy pydocstyle
    pipenv shell

Windows users should replace `pipenv` in the above commands with `py -3 -m pipenv`
