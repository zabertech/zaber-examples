# Asynchronous use of the Zaber Motion Library

*By Soleil Lapierre*

This example demonstrates fully asynchronous use of the library in each language.  It's intended as
a reference for advanced programmers and to help debug async-related problems.  It is not only about
best practices; some of the comments in the example code discuss usage patterns to avoid.

The example generates a two-dimensional grid of points to visit, as needed, and moves two
device axes to each point in order, waiting for motion to stop at each point.

There are three forms of asynchrony involved in controlling Zaber motion devices:
# Many Zaber Motion Library commands have both synchronous and asynchronous versions. For simplicity
  most of our example code uses the synchronous versions, but this example uses the asynchronous functions
  as much as possible.
# Functions that cause the devices to move can return before the move is completed, or can optionally
  block until the device stops moving. Many of the other examples use the blocking behavior, which is
  the default; this example does not, and reveals places where CPU time is available while the device moves.
# Communications lag. Most of the library functions send a command to the device over a serial
  communication channel and wait for an acknowledging reply, which can take up to a few milliseconds.
  This delay is inherent in any device control function whether it's synchronous or asynchronous,
  but using the asynchonous functions as in this example allows you to make use of
  CPU time while the device command and reply messages are in flight.

Users new to the Zaber Motion Library or novice programmers should use the synchronous functions
found in other examples until there is a need for asynchronicity. Asynchronous programs can
be difficult to understand and debug.

There is no C++ version of this example because the Zaber Motion Library does not support asynchronous
function calls in that language. The best you can do there is to tell move commands not to wait for idle,
and do some other processing while the device is moving.


## Hardware Requirements

This example assumes you have either a controller with two linear axes, or two linear devices
connected together. You can edit the constants in the example source code to set the connection
information, device address(es) and grid dimensions to work with your particular devices (the
default values may not address your devices or may produce out-of-range motion).

## Dependencies / Software Requirements / Prerequisites

Running the example requires the following software setup:
* C#: DotNet 8.0 or later, or Visual Studio 2022 v17.8.2 or later.
* Java: Maven 3.6.3 or compatible, and a Java 8 or later runtime (tested with OpenJDK 1.8.0_302).
* JavaScript: Node 16 or later with a compatible version of npm.
* Python: Python 3.10.

## Running the Script

Before running the example, edit the constants in the code that define what communication port to use
and the device addresses and axis numbers for two linear axes for the program to control.
The device addresses can be the same if you have a multi-axis controller.

* C#:
  > ```
  > cd csharp
  > dotnet restore
  > dotnet run
  > ```
  Alternatively, open the `async.csproj` file with Visual Studio 2022 and use the debugger to run the program.
* Java:
  > ```
  > cd java
  > mvn clean compile assembly:single
  > java -jar target\async-1.0-SNAPSHOT-jar-with-dependencies.jar
  > ```
* JavaScript:
  > ```
  > cd javscript
  > npm i
  > node index.js
  > ```
* Python (Windows):
  > ```
  > cd python
  > py -3 -m pipenv install
  > py -3 -m pipenv run python async.py
  > ```
* Python (non-Windows):
  > ```
  > cd python
  > pipenv install
  > pipenv run python async.py
  > ```
