# Packaging Zaber Motion Library with MATLAB Compiler

*By Colby Sparks*

This example demonstrates how to build and run a standalone MATLAB application which uses the Zaber Motion Library toolbox.
The source code for the application is in `src/main.m`.

## MATLAB Compiler

MATLAB Compiler is a tool which allows users to package MATLAB code into standalone applications.
During the build process, it will perform a dependency analysis of a project to determine exactly which files
need to be included in the final packaged application, but binary dependencies such as `*.mex` files and shared libraries (`*.dll`/`*.so`/`*.dylib`)
will not be included automatically.

The Zaber Motion Library toolbox includes some binary dependencies, namely a shared library and
its corresponding thunk file, so the paths to these binary files must be specified manually.

## Prerequisites

The user must have the [MATLAB Compiler](https://www.mathworks.com/products/compiler.html) and [Zaber Motion Library toolbox](https://software.zaber.com/motion-library/docs/tutorials/install/matlab) (version `>=8.4.0`) installed.
Additionally, in order to run the `matlab -batch` command below, MATLAB must be added to the system [PATH](https://stackoverflow.com/questions/4822400/register-an-exe-so-you-can-run-it-from-any-command-line-in-windows).

This code example has been tested with MATLAB R2025b.

## Building the Application

There are several different ways of configuring MATLAB Compiler to build a standalone application.
In this example we use the [compiler.build.standaloneApplication](https://www.mathworks.com/help/compiler/compiler.build.standaloneapplication.html) function with [StandaloneApplicationOptions](https://www.mathworks.com/help/compiler/compiler.build.standaloneapplicationoptions.html) object.
It is also possible to configure and build an application using the [Standalone Application Compiler](https://www.mathworks.com/help/compiler/create-application-using-standalone-application-compiler-app.html) in the MATLAB IDE.

The `build_standalone_app.m` script contains all the logic for setting up and building an app with the Zaber Motion Library toolbox.
The most important thing to note is the following line where we assign the return value from `zaber.motion.Helper.getCompilerDependencies`
to the `AdditionalFiles` field of the build options object:

```matlab
buildOpts.AdditionalFiles = zaber.motion.Helper.getCompilerDependencies();
```

You can run the script either in your MATLAB IDE, or from the command line with:

```bash
cd examples/util_matlab_compiler
matlab -batch "build_standalone_app"
```

**Note**: If you are using the Standalone Application Compiler in the MATLAB IDE, the files whose paths are returned from `zaber.motion.Helper.getCompilerDependencies` need to be added manually under "Files Required for Standalone to Run".

## Running the Application (Windows)

To run the application in Windows, you can either locate the `ZaberTestApp.exe` file directly in File Explorer or use the following command in PowerShell:

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

Where `<deployedMcrRoot>` is the path to your MATLAB install.
