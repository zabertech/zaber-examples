# OME-TIFF Metadata Generation for Image Acquistion

*By Arjun Swani*

Put an introduction paragraph here

## Hardware Requirements

This example does not require any hardware to run. The example assumes that an image acquisition has been completed using a [Zaber microscope](https://www.zaber.com/products/microscopes).

## Dependencies / Software Requirements / Prerequisites

This example uses [`uv`](https://docs.astral.sh/uv/getting-started/installation/) to manage the virtual environment and dependencies. The dependencies are listed in `pyproject.toml`.

This example requires an image acquisition to completed prior, preferably with Zaber Launcher Microscope App, and requires the following to run:

- OME XML metadata: Exported using the Zaber Launcher Microscope App
- Image Acquistion Directory: Contains acquisition images captured using third party imaging software.

## Running the Script

- `-m, --ome-metadata`: Path to the `.ome.xml` metadata file.
- `-d, --acquisition-dir`: Directory containing acquisition images.
- `-o, --output-file` (Optional): Path for generated `.ome.tiff` file.

## Customising Example

The `OMETiffWriter` class provided in the example can be modified or extended to suit your specific use case. The example can be easily modified to extend supported image formats or add/customise metadata for the generated `.ome.tiff` file.

### Acquistion image Format / File Structure

The example assumes that images in the acquisition directory are named corresponding to the acquisition order for e.g `image001.png`, `image002.png` etc. If your files are sorted in a different way, you can override or modify the `get_acquisition_order` function to match your setup.

The example only looks for image file names matching the patterns in the `IMAGE_FORMAT_PATTERN`. Modify this constant to filter or extend image files discovered.

### Modifying Metadata

This example uses the [`ome_types`](https://pypi.org/project/ome-types/) library to parse metadata XML into a python object. The the `modify_metadata` function can be modified to mutate this object.
