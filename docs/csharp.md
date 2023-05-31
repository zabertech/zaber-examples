# C# Checklist
This is a checklist for contributing C# example code to this repository.

## Tool & Runtime Versions
We recommend using the latest Visual Studio Community, latest LTS .NET version and latest C# language version.

## Files to Include
When creating the project, ensure the `.sln` file is in the same directory as the top-level
code - that is, don't use the project structure where the `.sln` is by itself at the top level
with everything else in a subdirectory.

Include the `.sln` and `.vsproj` files but do not commit the `obj/`, `bin/` or `.vs/` directories.
Add them to the `.gitignore` file if needed.

## Style
Configure the solution to treat warnings as errors.
