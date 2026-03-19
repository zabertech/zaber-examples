# Calling the Zaber Motion Library from LabVIEW

*By Soleil Lapierre*

It's possible to call the Zaber Motion Library's functions from LabVIEW by using LabVIEW's
support for using .NET assemblies.

The advantage of this approach is that you can make use of the huge range of functionality that the Zaber
Motion Library provides, with minimal extra implementation within LabVIEW.

The downsides are that initial setup of your LabVIEW project is a little technical, and updating to a new
version of the Zaber Motion Library can also be a bit of extra work.

This article provides both a working example project to refer to, and instructions on how to set up
a new LabVIEW project to work with the Zaber Motion Library.

## Hardware Requirements

To try out this example you will need at least one Zaber stage available to connect to via USB or RS-232.

## Software Requirements

This example will only work correctly with LabVIEW 2026 Q1 (64-bit) or later.

This example is specific to Windows only. While it may be possible to make something similar work on
other platforms supported by LabVIEW, we have not tested it.

## The Example Project

In `labview/zaber.lvproj` you will find a working example project created in LabVIEW 2026 Q1 (64-bit). This project
has two example VIs:

* `basic.vi` is a minimal example showing how to open a connection, get a reference to a Zaber device object,
  invoke its methods, and dispose of resources. This one will only work with RS-232 or USB device connections on your
  local computer.
* `demo.vi` is a more advanced example that can open RS-232 or USB connections, or connections shared over the
  network by Zaber Launcher, or over IoT from the Zaber Cloud system, including Virtual Devices, and allows you to
  perform several operations on a selected device.

## How it Works

LabVIEW has the ability to call functions in external libraries written in C, C# or Python using special node
types called Invoke nodes. Of the programming languages supported by the Zaber Motion Library, C# is the most
convenient one to use.

The general pattern is that you create an Invoke node with a reference to the Zaber Motion Library C# DLL to
call either an object constructor or a static method that returns an object, then use other Invoke nodes to call
methods on that object, or Property nodes to read or write properties.

When you are finished with an object, you should use a Dispose Reference node to free up its memory and cause it
to deallocate any system resources it may have reserved. You can sometimes get away with not disposing C# objects
and let the .NET garbage collector take care of it for you, but it's a better practice to explicitly dispose
objects when you know it is safe to do so.

## Creating Your Own Project

To create a LabVIEW project that calls C# code, you must obtain the C# DLL that contains the functions you want
to use, and all of its dependency DLLs. Then you can create a LabVIEW project file or VI and create Invoke
nodes that call the C# functions.

### Obtaining the DLLs

First, create a directory on disk for your LabVIEW project (you can also create the project file now if you want),
and create a subdirectory to put the DLLs in. You should put the DLLs in a subdirectory of the project directory
so that LabVIEW can consistently find them using reference paths relative to the project file. For this example
we'll use `dlls` as the subdirectory name.

The next step is to obtain the DLLs for the Zaber Motion Library and all its dependencies. Create and navigate to
a temporary directory anywhere on disk. This should not be inside your LabVIEW project directory, unless you 
remember to delete it when finished.

You can use [nuget.exe](https://www.nuget.org/downloads) to obtain the packages. Once you have NuGet downloaded
and available to run, open a command shell in your temporary directory and enter:

    nuget install zaber.motion

This will download the required packages from the NuGet Gallery.

When the NuGet command is complete, use Windows Explorer or your favorite file copying tool to copy DLLs from
all the packages in your temporary directory to the `dlls` directory you made under your LabVIEW project.
Look in the `lib` directory of each package. You may find multiple subdirectories for each supported framework
version; don't copy from all of them! Prefer to copy from the highest-numbered `net#.#` directory that
is supported by LabVIEW (note NOT `net##` without the dot, as those are for the old .NET Framework).
If there isn't a `net#.#` directory, use the highest-numbered `netstandard#.#` one.

From the Zaber Motion Library package specifically, you will also need to copy the DLLs from the
`runtimes/win/native` subdirectory of the package. You only need the one that is specific to your computer's
CPU architecture, but it is safe to copy them all.


You should also add references to the DLLs to your LabVIEW project !!!

### Invoking C# Functions

Setting up a LabVIEW project is outside the scope of this article but is not difficult; refer to the LabVIEW
documentation to get started.

Once you have a project created in the same directory where your `dlls` subdirectory is, create a new blank VI.

!!!



## Optional Troubleshooting Tips or FAQ

Can provide additional information as needed.
