# Packaging ZML with MATLAB Compiler

*By Colby Sparks*

This example demonstrates how to build and run a standalone MATLAB application which uses the Zaber Motion Library toolbox.
The code for the application is in `src/main.m`.

## MATLAB Compiler

MATLAB Compiler is a tool which allows users to package MATLAB code into standalone applications.
During the build process, it will perform a dependency analysis of a project to determine exactly which files
need to be included in the final packaged application, but binary dependencies such as mex files and shared libraries
will not be included automatically.

The Zaber Motion Library toolbox includes some binary dependencies, namely a shared library (dll/so/dylib) and
its corresponding thunk file, and the paths to these binary files must be specified manually as 'additional dependencies'.

## Prerequisites

The user must have the MATLAB Compiler and Zaber Motion Library toolboxes (version >=8.4.0) installed.
In order to run the matlab batch commands below, MATLAB must be added to the system [PATH](https://stackoverflow.com/questions/4822400/register-an-exe-so-you-can-run-it-from-any-command-line-in-windows).
This project has been tested with MATLAB R2025b.

## Building the Application

There are a couple different ways of configuring MATLAB Compiler to build a standalone application.
In this example, we use the [compiler.build.standaloneApplication](https://www.mathworks.com/help/compiler/compiler.build.standaloneapplication.html) function with [StandaloneApplicationOptions](https://www.mathworks.com/help/compiler/compiler.build.standaloneapplicationoptions.html) object,
but it is possible to configure and build an application using the [Standalone Application Compiler](https://www.mathworks.com/help/compiler/create-application-using-standalone-application-compiler-app.html) in the MATLAB IDE.

The `build_standalone_app.m` script contains all the logic for setting up and building an app with the Zaber Motion Library toolbox.
The most important thing to note is the following line where we assign the return value from `zaber.motion.Helper.getCompilerDependencies`
to the `AdditionalFiles` field of the build options object (note that if you are using the Standalone Application Compiler in the MATLAB IDE,
these files need to be added manually under "Files Required for Standalone to Run"):

```matlab
buildOpts.AdditionalFiles = zaber.motion.Helper.getCompilerDependencies();
```

You can run the script either in your MATLAB IDE, or from the command line with:

```bash
cd examples/util_matlab_compiler
matlab -batch "build_standalone_app"
```

## Running the Application (Windows)

To run the application on Windows, you can either locate and run the exe directly from File Explorer, or in powershell:

```shell
cd examples/util_matlab_compiler
.\ZaberTestApp\output\build\ZaberTestApp.exe
```

## Running the Application (Linux/macOS)

On Linux/macOS, MATLAB Compiler generates a shell script `run_ZaberTestApp.sh` which requires the path to your MATLAB Runtime (or MATLAB installation) as the first argument:

```bash
cd examples/util_matlab_compiler
./ZaberTestApp/output/build/run_ZaberTestApp.sh <deployedMcrRoot>
```

Where <deployedMcrRoot> is the path to your MATLAB install.
