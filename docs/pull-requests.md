# Pull Requests

All submissions to the Zaber Community Code Examples repository on GitHub will be reviewed by a member
of Zaber Technologies for inclusion.

Before creating a Pull Request, please read and follow
the [Contribution Guidelines](CONTRIBUTING.md), and make sure all of the code examples are
linted and formatted according to the corresponding Language Checklist.

Pull Requests will automatically trigger [CI script](../.github/workflows/check_examples.yml), which will
call [`check_examples` script](../tools/check_examples/) to run linters on the whole repository.
Pull Requests can only be merged after passing the checks.
The [`check_examples` script](../tools/check_examples/) can be run manually to verify that the code pass
before submitting a Pull Request.

(Insert more detailed instructions on how to do a Pull Request as needed.)
