"""Microscope Autofocus with Python and OpenCV."""

import argparse
import math
from typing import Any

import cv2
from matplotlib import pyplot as plt
from simple_pyspin import Camera  # type: ignore
from zaber_motion.ascii import Connection
from zaber_motion.units import Units


def get_image(cam: Camera) -> Any:
    """
    Capture an image and return it.

    :param cam: The camera to use
    """
    cam.start()
    image = cam.get_array()
    cam.stop()
    return image


def figure_file_name(position: float) -> str:
    """
    Return a filename for a plot of data at a specific position.

    :param position: The position in mm.
    """
    position_mm = int(position // 1)
    position_frac = round((position - position_mm) * 1000)
    return f"at_{position_mm}_{position_frac}.png"


def calculate_focus_score(image: Any, blur: int, position: float) -> float:
    """
    Calculate a score representing how well the image is focussed.

    :param image: The image to evaluate.
    :param blur: The blur to apply.
    :param position: The position in mm the image was captured at.
    """
    image_filtered = cv2.medianBlur(image, blur)
    laplacian = cv2.Laplacian(image_filtered, cv2.CV_64F)  # type: ignore
    focus_score: float = laplacian.var()

    if SHOW_STEP_IMAGES:
        focus_scores.append(focus_score)
        grayscale_laplacian = cv2.convertScaleAbs(laplacian, alpha=50)
        fig = plt.figure(figsize=(10, 2))

        ax1 = fig.add_subplot(131)
        ax1.imshow(image_filtered)
        ax1.set_title("Filtered")
        ax1.set_xticks([])
        ax1.set_yticks([])

        ax2 = fig.add_subplot(132)
        ax2.imshow(grayscale_laplacian)
        ax2.set_title("Laplacian")
        ax2.set_xticks([])
        ax2.set_yticks([])

        ax3 = fig.add_subplot(133)
        ax3.plot(range(len(focus_scores)), focus_scores, color="red")
        ax3.set_title("Variance")
        ax3.set_xticks([])
        ax3.set_yticks([])

        plt.savefig(figure_file_name(position))
        plt.close()

    return focus_score


def find_best_focus(
    start_mm: float, end_mm: float, step_size_mm: float, microscope_serial_port: str, blur: int
) -> None:
    """
    Find best focus by changing the focal distance and taking images with the camera.

    :param start_mm: The position, in mm, to start at.
    :param end_mm: The position, in mm, to end at.
    :param step_size_mm: The distance, in mm, to move between taking images with the camera.
    :param microscope_serial_port: The name of the serial port connected to the microscope.
    :param blur: The blur to apply to images during processing.
    """
    # pylint: disable=too-many-locals
    with Connection.open_serial_port(microscope_serial_port) as connection, Camera() as cam:
        # Initialize control of the the vertical axis of the microscope
        z_axis_device = connection.get_device(3)
        z_axis_device.identify()
        z_axis = z_axis_device.get_axis(1)
        if not z_axis.is_homed():
            z_axis.home()

        # Set the camera to take individual shots
        cam.AcquisitionMode = "SingleFrame"

        best_focus_score = 0.0
        best_focus_position = 0.0
        # How many steps to take to achieve the desired step size, +1 to check end_mm
        steps = math.ceil((end_mm - start_mm) / step_size_mm) + 1
        for step in range(0, steps):
            position = min(start_mm + step * step_size_mm, end_mm)
            z_axis.move_absolute(position, Units.LENGTH_MILLIMETRES)
            image = get_image(cam)
            focus_score = calculate_focus_score(image, blur, position)
            if focus_score > best_focus_score:
                best_focus_position = position
                best_focus_score = focus_score
            if SHOW_STEP_INFO:
                print(f"focus {position}: {focus_score}")

        z_axis.move_absolute(best_focus_position, Units.LENGTH_MILLIMETRES)
        best_image = get_image(cam)
        cv2.imshow("Best Image", best_image)
        print(f"The best focus ({best_focus_score}) was found at {best_focus_position}.")
        print("Press any key to exit.")
        cam.stop()
        cv2.waitKey(0)
        cv2.destroyAllWindows()


SHOW_STEP_INFO = False
SHOW_STEP_IMAGES = False

focus_scores: list[float] = []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find the position with the best focus.")
    parser.add_argument(
        "start",
        action="store",
        type=float,
        help="The position to begin the search at, in mm",
    )
    parser.add_argument(
        "end",
        action="store",
        type=float,
        help="The position to end the search at, in mm",
    )
    parser.add_argument(
        "step", action="store", type=float, help="The granularity of the search, in mm"
    )
    parser.add_argument(
        "serial_port",
        action="store",
        type=str,
        help="The serial port to use to control the motor",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Log debug information to standard out"
    )
    parser.add_argument(
        "--show-images",
        action="store_true",
        help="Show captured images for debugging. Should be used for at most ~10 steps.",
    )
    parser.add_argument(
        "--blur",
        "-b",
        action="store",
        type=int,
        required=False,
        default=9,
        help="Applies some blur to the image to remove random noise",
    )
    args = parser.parse_args()

    SHOW_STEP_INFO = args.verbose
    SHOW_STEP_IMAGES = args.show_images

    if args.blur % 2 != 1:
        parser.error(
            f"Bad value for blur, {args.blur} is not an odd number (required for median blurring)"
        )

    find_best_focus(args.start, args.end, args.step, args.serial_port, args.blur)
