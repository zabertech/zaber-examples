# Example Subdirectory Naming Conventions

Please follow this guideline when naming example subdirectories under [`examples/`](../examples/).
This will help make the repository more consistent and easier to browse on GitHub.

Subdirectory names should consist only of lower-case letters and underscores, for example:

    microscope_autofocus
    microplate_scanning_basic
    microplate_scanning_high_speed

Each subdirectory is made up of two parts, joined by underscore:

    <category_name>_<example_name>

The `<category_name>` and `<example_name>` could be a single word or multiple worlds joined by underscore.
For example, the subdirectory `microplate_scanning_basic`
is composed of `microplate` as the `<category_name>`, and `scanning_basic` as the `<example_name>`

We currently have the following category names. More may be added as required:

- `calibration`: Routines and algorithms for calibrating the accuracy of stages
- `gui`: Graphical User Interface examples
- `hid`: Human Interface Devices (HID) examples
- `microplate`: Examples involving manipulating micro well plates
- `microscope`: Microscope related examples and scripts
- `motion`: Kinematic and motion-related examples that are not tied to a specific application area
- `self_test`: Scripts for performing self test on motion control products
- `util`: Miscellaneous utilities and tools
