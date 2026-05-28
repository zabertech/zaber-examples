from collections.abc import Iterator
from pathlib import Path
from typing import Final

import click
import numpy as np
from ome_types import from_xml
from ome_types.model import PixelType
from PIL import Image
from tifffile import TiffWriter


class OMETiffWriter:
    """Generate an OME-TIFF from acquisition images and an OME-XML metadata file.

    Reads image files from a directory, derives pixel properties from the image
    data, updates the provided OME-XML to match, and writes a multi-frame OME-TIFF.

    Args:
        metadata: .ome.xml file path.
        image_dir: Acquisition directory.
        output_directory (Optional): Output directory.
    """

    IMAGE_FORMAT_PATTERNS: Final = ["*.jpg", "*.bmp", "*.png", "*.tif"]

    DTYPE_TO_OME: Final[dict[np.dtype, PixelType]] = {
        np.dtype("uint8"): PixelType.UINT8,
        np.dtype("uint16"): PixelType.UINT16,
        np.dtype("uint32"): PixelType.UINT32,
        np.dtype("int8"): PixelType.INT8,
        np.dtype("int16"): PixelType.INT16,
        np.dtype("int32"): PixelType.INT32,
        np.dtype("float32"): PixelType.FLOAT,
        np.dtype("float64"): PixelType.DOUBLE,
    }

    NUM_CHANNELS_GREYSCALE: Final = 2

    def __init__(self, metadata: Path, image_dir: Path, output_directory: Path | None) -> None:
        self.metadata = metadata
        self.image_dir = image_dir
        self.output_directory = output_directory

    def write_ome_tiff(self) -> None:
        """Write a OME-TIFF file."""
        ome_tiff_dir = self.output_directory or self.metadata.parent

        with TiffWriter(ome_tiff_dir / self.metadata.with_suffix(".tiff").name, kind="generic") as tif:
            for index, frame in enumerate(self.get_acquisition_images()):
                if index == 0:
                    metadata_str = self.modify_metadata(frame)
                    tif.write(frame, contiguous=True, description=metadata_str.encode())
                else:
                    tif.write(frame, contiguous=True)

    def get_acquisition_order(self, acquisition_filenames: list[str]) -> list[str]:
        """Sorts acquisition image file names by acquisition order.

        Assumes alphabetically sorted image file names correspond to order of acquisition.
        """
        return sorted(acquisition_filenames)

    def get_acquisition_images(self) -> Iterator[np.ndarray]:
        """Yield acquisition images from the image directory as numpy arrays in acquisition order.

        Assumes alphabetically sorted image file names correspond to order of acquisition.

        Yields:
            Numpy array of shape ``(H, W)`` or ``(H, W, C)`` per image.
        """
        filenames: list[Path] = []
        for pattern in self.IMAGE_FORMAT_PATTERNS:
            pattern_filenames = self.image_dir.glob(pattern)
            filenames += list(pattern_filenames)

        sorted_filenames = self.get_acquisition_order(filenames)

        for filename in sorted_filenames:
            yield np.asarray(Image.open(filename))

    def modify_metadata(self, sample: np.ndarray) -> str:
        """Update OME-XML pixel properties to match the acquired image data.

        Derives pixel type and interleaving from ``sample``.

        Args:
            sample: Representative image used to derive pixel properties.

        Returns:
            Updated OME-XML as a UTF-8 string.
        """
        ome = from_xml(self.metadata)
        pixel_type = self.DTYPE_TO_OME.get(sample.dtype)

        if sample.ndim == self.NUM_CHANNELS_GREYSCALE:  # greyscale (H, W)
            samples_per_pixel = 1
            interleaved = False
        else:  # color (H, W, C)
            samples_per_pixel = sample.shape[2]
            interleaved = True

        for image in ome.images:
            if pixel_type is not None:
                image.pixels.type = pixel_type
            image.pixels.interleaved = interleaved
            for channel in image.pixels.channels:
                channel.samples_per_pixel = samples_per_pixel
        return ome.to_xml()


@click.command()
@click.option(
    "-m",
    "--ome-metadata",
    help="Path to the .ome.xml metadata file.",
    required=True,
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
@click.option(
    "-d",
    "--acquisition-dir",
    help="Directory containing acquisition images.",
    required=True,
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
@click.option(
    "-o",
    "--output-directory",
    help="Output file directory.",
    required=False,
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
def generate(ome_metadata: Path, acquisition_dir: Path, output_directory: Path | None) -> None:
    if not (ome_metadata.name.endswith(".ome.xml")):
        raise click.BadParameter("must have extension .ome.xml", param_hint="--ome-metadata")

    OMETiffWriter(ome_metadata, acquisition_dir, output_directory).write_ome_tiff()


if __name__ == "__main__":
    generate()
