# Contribution Guidelines

We welcome public contribution to the example code repository.

To maintain a high quality of example code, please review the guidelines in this document
before submitting your contribution.

- The goal of this repository is to help users of [Zaber](https://www.zaber.com) devices,
and more generally to help people working on motion control and automation projects
get up and running quickly.
- Examples are in the [`examples/`](../examples/) directory in a flat structure and can be browsed directly on GitHub.
For an overview of the repository, please see document on [Directory Structure](directory-structure.md)

## Issues and Bugs

If you notice a bug or typo in any of our example code or documentation and you want us to fix it,
please feel free to [open an issue](https://github.com/zabertech/zaber-examples/issues).

Alternately you are welcome to contribute directly to the bug fix.  For example, if you found a bug
in `/examples/<example_directory>/`:

1. Fork the repository
2. Make the suggested fixes
3. Run through the appropriate [Language Checklist](#language-checklist)
4. Do a Pull Request

## Adding a new Example

If you want to contribute a new example:

1. Take a look at all the examples under [`examples/`](../examples/) directory and make sure the new example
is not a duplicate or closely related to another example already in the repository.
2. Make sure that the example you want to add is illustrating a single concept or task,
or is a building block that that is likely to be useful to others.  Consider how to structure
and write the example code to avoid excessive boilerplate that does not contribute to explaining
the central concept.
3. Fork
4. Create a subdirectory `<example_directory>` under [`examples/`](../examples/)
    - i.e. `/examples/microplate_scanning_basic`
    - See [Example Subdirectory Naming Convention](example-subdirectory-naming.md)
5. Create a `README.md` file in the example directory following this [README guidelines](readme-guidelines.md)
6. If the example is intended to be implementation in multiple languages,
make a subdirectory with the language you want to implement:
    - i.e. `/examples/hid_joystick/csharp` and `/examples/hid_joystick/python`
    - See [list of valid language subdirectory names](directory-structure.md#language-subdirectories).
7. Implement the example in the language(s) of your choice.
You can start with our [example template](../examples/_template/).
8. Add a file, [`article.yml`](article_yml.md) with metadata specifying how to publish to
[Zaber Code Examples](https://software.zaber.com/examples), if the example is meant to be included there.
9. Add an image to be used with the link to the article from the main website. The picture should be less than 1000
pixels wide and have a horizontal aspect. Reference it with the `picture:` key in `article.yml`. The image
doesn't have to be used in the readme, but ideally should be similar to a readme image if there are any suitable.
10. Run through the appropriate [Language Checklist](#language-checklist)
11. Do a Pull Request

## Updating an Existing Example

If you change the code or documentation of an example in a way that would matter to readers, remember
to update the `updated_date` field in the `article.yml` file.

This is used by the Zaber website to display a last modified date in addition to the creation date.

## Language Checklist

Here are the checklists for the various languages:

- [Python](python.md)
- [MATLAB](matlab.md)
- [C#](csharp.md)
- [C++](cpp.md)
- [TypeScript](typescript.md)
- [Java](java.md)
- [Swift](swift.md)

By contributing to this repository you agree that all of your work will be governed by the terms of the [LICENSE](../LICENSE) file.

## Tooling

Install the EditorConfig plugin for your editor if needed in order to capitalize on the top-level `.editorconfig`
file in this repository.
