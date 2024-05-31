# Python Virtual Environment

All Python scripts and examples in this repository must use some form of package manager
and virtual environment to isolate and to manage dependencies.
Each example in this repository is self-contained and should use its own environment.

There are several supported option for package manager and virtual environment:

- [PDM](https://pdm-project.org/en/latest/) (Recommended)
- [Pipenv](https://pipenv.pypa.io/en/latest/)
- `requirements.txt` and [venv](https://docs.python.org/3/library/venv.html)

The [`check_example` script](../tools/check_examples/) invoked by the CI will automatically
recognize the presence of the above-mentioned options, activate each virtual environment,
install dependencies, and run linters accordingly.

## PDM

We recommend using [PDM](https://pdm-project.org/en/stable/) as the
virtual environment and package manager of choice for example projects.
There are many different ways to install PDM according to instructions on the website.

See [microscope_tiling_basler_camera](../src/microscope_tiling_basler_camera/) as an example
of how PDM is used to manage packages and virtual environment.

PDM uses a [src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
directory structure, and PDM handles initializing and populating a bare directory with the essential files:

    pdm init

To add packages, for example, [Zaber Motion Library](https://software.zaber.com/motion-library/docs):

    pdm add zaber-motion

Be sure to install all of the linters required by the [`check_example` script](../tools/check_examples/)
as development packages in PDM:

    pdm add --dev black pylint pydocstyle mypy

To run scripts, edit `pyproject.toml` section on [PDM Scripts](https://pdm-project.org/en/stable/usage/scripts/).
The scripts can be executed by `pdm run <sript_name>`.

If you have just cloned this repository and the example you want to run uses PDM:

    pdm install --dev
    pdm run <script_name>

## Pipenv

Tutorials on Pipenv:

- [Pipenv: A Guide to the New Python Packaging Tool](https://realpython.com/pipenv-guide/)

An example of using Pipenv has been set up in [example template](../src/_template/python_pipenv/).

Our recommended way to install Pipenv:

Windows:

    py -m pip install --user --upgrade pipenv

Linux:

    python3 -m pip install --user --upgrade pipenv

Mac:

    brew install pipenv

Be sure to install all of the linters required by the [`check_example` script](../tools/check_examples/)
as development packages in Pipenv:

    pipenv install --dev black pylint pydocstyle mypy

### Pipenv with Zaber Motion Library

If you are using the latest version of Zaber Motion Library (after 5.2.0), you can ignore this section.

For examples using Zaber Motion Library prior to
[Version 5.2.0](https://software.zaber.com/motion-library/docs/support/changelog#_2024-04-11-version-520),
please add three OS-specific lines to the `Pipfile` under `zaber-motion = "*"`:

    [packages]
    zaber-motion = "*"
    zaber-motion-bindings-darwin = {version = "*", markers = "platform_system == 'Darwin'"}
    zaber-motion-bindings-windows = {version = "*", markers = "platform_system == 'Windows'"}
    zaber-motion-bindings-linux = {version = "*", markers = "platform_system == 'Linux'"}

This is because older version of Zaber Motion Library had separate bindings for the different operating systems.
Adding these lines ensure that when `Pipfile.lock` is generated, it will include the bindings required
for all platforms.  Otherwise, the checked-in `Pipfile.lock` will only work
on the OS where the lock file was generated.

Please see example [`Pipfile`](../src/_template/python_pipenv/Pipfile) for more detail.

This section will be deleted when all examples are updated to use the latest version of Zaber Motion Library.

### PyCharm configuration with Pipenv

Here are some tips on using PyCharm:

1. Open the `src/example/python/` as a new project.
2. Note: Opening `zaber-examples/` will not work since pipenv environments are constrained
   within individual examples.
3. [Add a new pipenv interpreter](https://www.jetbrains.com/help/pycharm/pipenv.html#pipenv-new-project)
   using this guide.
4. Run `pipenv shell` in the terminal.

## requirements.txt and venv

This option uses `venv` that comes packaged with Python, and `pip` with `requirements.txt` to do the minimum
package management.  This option is not recommended for new examples.

The versions of the dependencies should be fully specified in `requirements.txt`.
