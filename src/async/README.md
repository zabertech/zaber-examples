# Asynchronous use of the Zaber Motion Library

*By Soleil Lapierre*

This example demonstrates fully asynchronous use of the library in each language.  It's intended as
a reference for advanced programmers and to help debug async-related problems.

The example generates a two-dimensional grid of points to visit, as needed, and moves two
device axes to each point in order, waiting for motion to stop at each point.

There are three forms of asynchrony involved in controlling Zaber motion devices:
# Many Zaber Motion Library commands have both synchronous and asynchronous versions. For simplicity
  most of our example code uses the synchronous versions; this example uses the asynchronous functions
  as much as possible.
# Functions that cause the devices to move can return before the move is completed, or can optionally
  block until the device stops moving. Many of the other examples use the blocking behavior; this example
  does not, and reveals places where CPU time is available while the device moves.
# Communications lag. Most of the library functions send a command to the device over a serial
  communication channel and wait for an acknowledging reply, which can take up to a few milliseconds.
  This delay is inherent in any device control function whether it's synchronous or asynchronous,
  but using the asynchonous functions as in this example allows you to make use of
  CPU time while the device command and reply messages are in flight.

Users new to the Zaber Motion Library or novice programmers should use the synchronous functions
found in other examples until there is a need for asynchronicity. Asynchronous programs can
be difficult to understand and debug.


## Hardware Requirements

This example assumes you have either a controller with two linear axes, or two linear devices
connected together. You can edit the constants in the example source code to set the connection
information, device address(es) and grid dimensions to work with your particular devices (the
default values may not address your devices or may produce out-of-range motion).

## Dependencies / Software Requirements / Prerequisites

!!!

Describe the software dependencies and programs required to demonstrate the script, including
instructions on how to install packages or programs.

If there is more than one language example provided, you may need a sub-sections for
each language.

Note that this is only required for dependencies and installation instructions
that are not included as part of the ordinary package manager.  For example, if you are using
`pipenv` to manage your virtual environment and packages in Python, then there is no need
to list all the dependencies that are already in `Pipfile`.`

_**Example:**_

> The script uses `pipenv` to manage virtual environment and dependencies:
> ```
> python3 -m pip install -U pipenv
> ```
> The dependencies are listed in Pipfile.

## Configuration / Parameters
Often scripts will need some command line parameters or arguments to specify what the script
should do.  Even simpler code examples may define a few constants that the user needs to edit
before it will run.  This is the section that explains what those configuration constants,
or command line parameters are.  This will aid the user in getting the script running.

_**Example:**_

> Edit the following constants in the script to fit your setup before running the script:
> - `SERIAL_PORT`: the serial port that your device is connected to.
> For more information on how to identify the serial port,
> see [Find the right serial port name](https://software.zaber.com/motion-library/docs/guides/find_right_port).

## Running the Script
Provide actual instructions to run the script.  If the script is meant to run on command line,
list the actual commands and arguments to type into the terminal, including any commands
required to set up environment variables or virtual environment.

_**Example:**_

> To run the script:
> ```
> cd src/microplate-scanning-basic/python
> pipenv install
> pipenv run python scanning.py
> ```

# Explaining the Central concept
This section explains the central concept or idea of the example in plain language.
There could be multiple subsections that talk about different parts of the code that supports
the central concept.

Sometimes it is useful to reference snippets of code in your explanation.
Use a [permanent link](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-a-permanent-link-to-a-code-snippet)
to some lines of code in the repository after at least one commit, and GitHub will link directly to the snippet.

## Optional Troubleshooting Tips or FAQ
Can provide additional information as needed.
