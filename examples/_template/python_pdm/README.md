# python_pdm

Note: most of the content of this directory were auto-generated.

After installing PDM, run the following commands:

    pdm init
    pdm add zaber-motion
    pdm add --dev black pylint pydocstyle mypy

Put a script, [`hello.py`](src/python_pdm/hello.py) under [`src/<package_name>`](src/python_pdm/).

Manually add the following entry to `pyproject.toml` to indicate script entry point:

    [tool.pdm.scripts]
    hello = {call = "src.python_pdm.hello:main"}

And then run:

    pdm run hello
