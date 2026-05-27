# OME-TIFF Metadata Generation for Image Acquisition

*By Arjun Swani*

The [Open Microscopy Environment (OME) data model](https://ome-model.readthedocs.io/en/stable/index.html) was developed to structure experiment data for biological microscopy imaging. The model can be expressed as just metadata in [OME-XML](https://ome-model.readthedocs.io/en/stable/ome-xml/) files or embedded with image data in [OME-TIFF](https://ome-model.readthedocs.io/en/stable/ome-tiff/specification.html) files.

This example demonstrates how to combine an `.ome.xml` file with image data to create an `.ome.tiff` file. OME-TIFF organises frames along TCZYX axes (Time, Channel, Z, Y, X) allowing multi-dimensional acquisitions to be stored in a single file alongside structured metadata. The generated OME-TIFF files can be opened directly in bioimaging tools or libraries and can be further processed for image analysis, stitching, or other workflows.

The example was specifically developed to be used with the [Zaber Launcher Microscopy app](https://www.zaber.com/zaber-launcher) that exports image metadata as OME-XML files after image acquisition.

## Hardware Requirements

This example does not require any hardware to run. The example assumes that an image acquisition has been completed using a [Zaber microscope](https://www.zaber.com/products/microscopes).

## Dependencies / Software Requirements / Prerequisites

This example uses [`uv`](https://docs.astral.sh/uv/getting-started/installation/) to manage the virtual environment and dependencies. The dependencies are listed in `pyproject.toml`.

This example requires an image acquisition to be completed prior to runnning, preferably with Zaber Launcher Microscope App, and requires the following to run:

- OME XML metadata: Exported using the Zaber Launcher Microscope App
- Image Acquisition Directory: Contains acquisition images captured using third party imaging software. The example assumes all images have the same dimensions.

## Running the Script

- `-m, --ome-metadata`: Path to the `.ome.xml` metadata file.
- `-d, --acquisition-dir`: Directory containing acquisition images.
- `-o, --output-directory` (Optional): Output directory for generated `.ome.tiff` file.

To run the example: 

```shell
cd src/microscope_ome_tiff_generation/
uv install
uv run ome_tiff.py -m ./sample_data/xy.ome.xml -d ./sample_data -o ./output
```

## Customising Example

The `OMETiffWriter` class provided in the example can be modified to suit your specific use case. The example can be easily modified to extend supported image formats or add/customise metadata for the generated `.ome.tiff` file.

### Acquisition image Format / File Structure

`OMETiffWriter` assumes that images in the acquisition directory are named corresponding to the acquisition order for e.g `image001.png`, `image002.png` etc. If your files are sorted in a different way, you can override or modify the `get_acquisition_order` function to match your setup.

The example only looks for image file names matching the patterns in the `IMAGE_FORMAT_PATTERN`. Modify this constant to filter or extend image files discovered.

### Modifying Metadata

`OMETiffWriter` uses the [`ome_types`](https://pypi.org/project/ome-types/) library to parse metadata XML into a python object which is further modified in `modify_metadata`.

The code in `modify_metadata` looks at the image data to derive the `pixel_type`, `interleaved` and `samples_per_pixel` attributes for OME `Image` and `Pixels` objects. These are often required by OME-TIFF readers for rendereing. 

Additional logic to moify metadata can be added to this method. 

```python 
    def modify_metadata(self, sample: np.ndarray) -> str:

        # get OME metadata object
        ome = from_xml(self.metadata)
        pixel_type = self.DTYPE_TO_OME.get(sample.dtype) 

        if sample.ndim == self.NUM_CHANNELS_GREYSCALE:  
            # derive metadata from image shape
        else:  
            # ...

        for image in ome.images:
            # add derived metadata to metadata object
        
        # your metadata logic here
        
        return ome.to_xml()

```
