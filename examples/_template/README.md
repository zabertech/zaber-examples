# Title of the Article

_*By Author Name*_

This is a template for example code and documentation in this repository.
Replace this paragraph with a succinct description of the purpose of this example.

Note that this template has two Python examples using different package managers:

- [`python_pdm`](./python_pdm/)
- [`python_pipenv`](./python_pipenv/)

If you are using Python, we recommend using [PDM](https://pdm-project.org/en/stable/).

## Hardware Requirements

Describe the hardware required to demonstrate the script, including instructions on how to
setup the hardware.

## Dependencies / Software Requirements / Prerequisites

Describe the software dependencies and programs required to demonstrate the script, including
instructions on how to install packages or programs.

If there is more than one language example provided, you may need a sub-sections for
each language.

Note that this is only required for dependencies and installation instructions
that are not included as part of the ordinary package manager.  For example, if you are using
`PDM` to manage your virtual environment and packages in Python, then there is no need
to list all the dependencies that are already in `pyproject.toml`.

_**Example:**_

> The script uses `PDM` to manage virtual environment and dependencies:
>
> ```bash
> pdm install --dev
> ```
>
> The dependencies are listed in `pyproject.toml`.

## Configuration / Parameters

Often scripts will need some command line parameters or arguments to specify what the script
should do.  Even simpler code examples may define a few constants that the user needs to edit
before it will run.  This is the section that explains what those configuration constants,
or command line parameters are.  This will aid the user in getting the script running.

_**Example:**_

> Edit the following constants in the script to fit your setup before running the script:
>
> - `SERIAL_PORT`: the serial port that your device is connected to.
> For more information on how to identify the serial port,
> see [Find the right serial port name](https://software.zaber.com/motion-library/docs/guides/communication/find_right_port).

## Running the Script

Provide actual instructions to run the script.  If the script is meant to run on command line,
list the actual commands and arguments to type into the terminal, including any commands
required to set up environment variables or virtual environment.

_**Example:**_

> To run the script:
>
> ```bash
> cd src/<example_directory>
> pdm install --dev
> pdm run <name_of_script_in_pyproject_toml>
> ```

## Explaining the Central concept

This section explains the central concept or idea of the example in plain language.
There could be multiple subsections that talk about different parts of the code that supports
the central concept.

Sometimes it is useful to reference snippets of code in your explanation.
Use a [permanent link](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-a-permanent-link-to-a-code-snippet)
to some lines of code in the repository after at least one commit, and GitHub will link directly to the snippet.

## Optional Troubleshooting Tips or FAQ

Can provide additional information as needed.
