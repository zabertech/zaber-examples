# Virtual Environment

## Python
For scripts and examples written in Python, we recommend using a
virtual environment to isolate and to manage packages and dependencies.
Each example is self-contained and should use its own environment.

There are several options available in Python:
- [venv](https://docs.python.org/3/library/venv.html)
- [Pipenv](https://pipenv.pypa.io/en/latest/)

### Pipenv
We recommend using [Pipenv](https://pipenv.pypa.io/en/latest/).

Tutorials on Pipenv:
- [Pipenv: A Guide to the New Python Packaging Tool](https://realpython.com/pipenv-guide/)

An example of using Pipenv has been set up in [example template](../src/_template/python/).

To install Pipenv:

Windows:

    py -3 -m pip install -U pipenv

Linux / Mac:

    python3 -m pip install -U pipenv

#### Pycharm configuration:
1. Open the `src/example/python/` as a new project.
2. Note: Opening `zaber-examples/` will not work since pipenv environments are constrained
   within individual examples.
3. [Add a new pipenv interpreter](https://www.jetbrains.com/help/pycharm/pipenv.html#pipenv-new-project)
   using this guide.
4. Run `pipenv shell` in the terminal.

#### Pipenv with Zaber Motion Library
For examples using Zaber Motion Library, please add three OS-specific lines
to the `Pipfile` under `zaber-motion = "*"`:

    [packages]
    zaber-motion = "*"
    zaber-motion-bindings-darwin = {version = "*", markers = "platform_system == 'Darwin'"}
    zaber-motion-bindings-windows = {version = "*", markers = "platform_system == 'Windows'"}
    zaber-motion-bindings-linux = {version = "*", markers = "platform_system == 'Linux'"}

This is to ensure that when `Pipfile.lock` is generated, it will include the bindings required
for all platforms.  Otherwise, the checked-in `Pipfile.lock` will only work
on the OS where the lock file was generated.

Please see example [`Pipfile`](../src/_template/python/Pipfile) for more detail.
