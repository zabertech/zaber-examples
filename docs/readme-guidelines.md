# README Guidelines

This is a set of guidelines for writing README.md to describe each example.

Each example should have a comprehensive readme file that describes the
the purpose of the example, and explains how the example works.
It should contain enough information about the hardware setup
and the software dependencies, as well as clear instructions on how to install
and configure the script to run.

Since these example are also meant to be educational, each example should have a clear
explanation of the theory, and intent behind the central concept of the code to aid comprehension.

## Writing in GitHub's flavour of Markdown

`README.md` is written in [GitHub's flavour of Markdown](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).

There are some cool features, such as the ability to insert [permanent links to code snippets](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-a-permanent-link-to-a-code-snippet)
directly in the document.

- Note: if the code is changed in a subsequent commit, be sure to update the permanent link to the latest commit
(requires a second, separate commit to update README.md).

## README.md template

There is a [`README.md` template](../src/_template/README.md) with suggested headings.
You can make a copy of this template and edit as you see fit,
or browse some of the other examples for inspiration.

## Linting Markdown Files

The [`check_examples` script](../tools/check_examples/) can lint markdown files.
By default, the main [`README.md`](../README.md) and all markdown files in [`/docs/`](../docs/)
subdirectory are automatically linted using [`pymarkdownlnt`](https://github.com/jackdewinter/pymarkdown).
Optionally, markdown files in each example can be linted by passing `-m` option to certain commands:

- `check all -m`
- `check <example> -m`
