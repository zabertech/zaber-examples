from argparse import ArgumentError, ArgumentParser
from collections.abc import Iterator
from os import path
from pathlib import Path
from typing import Final

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
        metadata: Path to the source .ome.xml file.
        image_dir: Directory containing acquisition images.
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

    NUM_COLOR_CHANNELS: Final = 3

    def __init__(self, metadata: Path, image_dir: Path) -> None:
        self.metadata = metadata
        self.image_dir = image_dir

    def write_ome_tiff(self) -> None:
        """Write a OME-TIFF file."""
        ome_tiff_filename = f"{self.metadata.stem}.tiff"
        sample = next(self.get_acquisition_images())
        metadata_str = self.modify_metadata(sample)

        with TiffWriter(ome_tiff_filename, ome=False, shaped=False) as tif:
            first = True
            for frame in self.get_acquisition_images():
                if first:
                    tif.write(frame, contiguous=True, description=metadata_str.encode())
                    first = False
                else:
                    tif.write(frame, contiguous=True)

    def get_acquisition_images(self) -> Iterator[np.ndarray]:
        """Yield acquisition images from the image directory as numpy arrays in acquistion roder.

        Assumes acquisition images were created in order of capture.

        Yields:
            Numpy array of shape ``(H, W)`` or ``(H, W, C)`` per image.
        """
        filenames: list[Path] = []
        for pattern in self.IMAGE_FORMAT_PATTERNS:
            pattern_filenames = self.image_dir.glob(pattern)
            filenames += list(pattern_filenames)

        filenames.sort(key=path.getctime)

        for filename in filenames:
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

        if sample.ndim == self.NUM_COLOR_CHANNELS:
            num_pixel_channels = sample.shape[2]
            samples_per_pixel = num_pixel_channels
            interleaved = num_pixel_channels in (3, 4)
        else:
            samples_per_pixel = 1
            interleaved = False

        for image in ome.images:
            if pixel_type is not None:
                image.pixels.type = pixel_type
            image.pixels.interleaved = interleaved
            for channel in image.pixels.channels:
                channel.samples_per_pixel = samples_per_pixel
        return ome.to_xml()


def validate_xml(value: str) -> Path:
    if not value.endswith(".ome.xml"):
        raise ArgumentError(None, "Metadata must be a .ome.xml file.")
    file_path = Path(value)
    if not file_path.is_file():
        raise ArgumentError(None, f"Metadata file not found: {value}")
    return file_path


def validate_directory(value: str) -> Path:
    dir_path = Path(value)
    if not dir_path.is_dir():
        raise ArgumentError(None, f"Image directory not found: {value}")
    return dir_path


if __name__ == "__main__":
    parser = ArgumentParser(
        description=(
            "Generate an OME-TIFF from an OME-XML metadata file and an acquisition image directory."
        )
    )
    parser.add_argument(
        "-m",
        "--metadata",
        required=True,
        type=validate_xml,
        help="Path to the .ome.xml metadata file.",
    )
    parser.add_argument(
        "-d",
        "--image_dir",
        required=True,
        type=validate_directory,
        help="Directory containing acquisition images.",
    )

    args = parser.parse_args()
    OMETiffWriter(args.metadata, args.image_dir).write_ome_tiff()
