"""Example utility function module."""

import cv2
import numpy as np
from cv2.typing import MatLike
from numpy.typing import NDArray
from zaber_motion import Units
from zaber_motion import UnitsAndLiterals

CV2_ERR_DICT: dict[int, str] = {
    cv2.STITCHER_OK: "STITCHER_OK",
    cv2.STITCHER_ERR_NEED_MORE_IMGS: "STITCHER_ERR_NEED_MORE_IMGS",
    cv2.STITCHER_ERR_HOMOGRAPHY_EST_FAIL: "STITCHER_ERR_HOMOGRAPHY_EST_FAIL",
    cv2.STITCHER_ERR_CAMERA_PARAMS_ADJUST_FAIL: "STITCHER_ERR_CAMERA_PARAMS_ADJUST_FAIL",
}


def convert_length_to_microns(length: float, unit: UnitsAndLiterals) -> float:
    """
        Convert number from specified unit of length to microns.

    Args:
        length: numeric type (numpy arrays are ok)
        unit: unit of measurement for length param

    Returns:
        float or MatLike with each component converted to microns
    """
    ret: float = 0.0
    match unit:
        case Units.LENGTH_METRES:
            ret = length * 10**9
        case Units.LENGTH_CENTIMETRES:
            ret = length * 10**6
        case Units.LENGTH_MILLIMETRES:
            ret = length * 10**3
        case Units.LENGTH_MICROMETRES:
            ret = length
        case Units.LENGTH_NANOMETRES:
            ret = length / 1000.0
        case Units.LENGTH_INCHES:
            ret = length * 25400.0
        case _:
            print(
                "Warning: Measurement unit must be LENGTH, instead received ",
                unit,
            )
    return ret


def convert_point_to_microns(
    point: NDArray[np.float64], units: UnitsAndLiterals
) -> NDArray[np.float64]:
    """
        Convert 2d point to microns.

    Args:
        point (NDArray[np.float64]): 2d point
        units: units of point to be converted to microns

    Returns:
        NDArray: resulting point with x, y coords in microns
    """
    return np.array(
        [
            convert_length_to_microns(point[0], units),
            convert_length_to_microns(point[1], units),
        ]
    )


def resize_image(img: MatLike, scale: float) -> MatLike:
    """
        Resize image by scale.

    Args:
        img: image to be resized
        scale: scale value between 0.0 and 1.0

    Returns:
        MatLike: resized image
    """
    assert 0.0 < scale <= 1.0, "scale must be on [0.0, 1.0]"
    return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)


def try_stitch_images(tiles: list[MatLike], file_name: str, scale: float = 1.0) -> None:
    """
        Attempt to stitch tiled images row by row using openCV's high level stitching API.

        This function is not guaranteed to succeed, but in general the more overlap the better.

    Args:
        tiles (list[list[MatLike]]): list of tile rows
        file_name: name of file to be saved
        scale: decimal percentage representing scale of final image
    """
    if scale < 1.0:
        tiles = list(map(lambda img: resize_image(img, scale), tiles))

    stitcher = cv2.Stitcher.create(cv2.Stitcher_SCANS)
    status, stitched_final = stitcher.stitch(tiles)

    if status == cv2.Stitcher_OK:
        cv2.imwrite(file_name, stitched_final)
    else:
        print(f"cv2.Stitcher failed with error code: {status}: {CV2_ERR_DICT[status]}.")


def join_tiles(
    tiles: list[list[MatLike]], num_rows: int, file_name: str, scale: float = 1.0
) -> None:
    """
        Join tiles into single image.

    Args:
        tiles (list[MatLike]): list of tile rows
        num_rows: number of tile rows
        file_name: name of file to be saved
        scale: decimal percentage representing scale of final image
    """
    tiled_rows = []
    for i in range(num_rows):
        row = tiles[i]
        row_img: MatLike = row[0]
        if scale < 1.0:
            row_img = resize_image(row_img, scale)

        for i in range(1, len(row)):
            row_img = cv2.hconcat([row_img, row[i]])
        tiled_rows.append(row_img)

    final_img: MatLike = tiled_rows[0]
    for i in range(1, len(tiled_rows)):
        final_img = cv2.vconcat([final_img, tiled_rows[i]])
    cv2.imwrite(file_name, final_img)
