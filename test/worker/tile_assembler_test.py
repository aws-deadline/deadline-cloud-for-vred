# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Deadline Cloud for VRED (Tile Assembly) - local semi-automated test module.

Tests assembling image tiles into complete frames using ImageMagick. Includes support for parallel processing of
multiple frames.
"""

import concurrent.futures
import io
import logging
import os
import subprocess
import sys

import load_render_parameter_values

from pathlib import Path

from constants import Constants
from output_comparison import are_images_similar_by_folder
from path_resolver import PathResolver

COMMAND_LINE_USAGE = f"Usage: python {sys.argv[0]} <job_bundle_config_name>"

sys.path.extend([os.path.realpath(os.path.dirname(os.path.abspath(__file__)))])
logging.basicConfig(format="%(message)s", level=logging.INFO)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def assemble_frame(
    frame_num: int, num_x_tiles: int, num_y_tiles: int, input_dir: str, output_dir: str
) -> None:
    """
    Produce a single frame from its respective tiles. Expected input filename format: prefix_YxX_AxB.suffix.
    Note: assumes tiles are in sequential order: left to right from top to bottom.
    :param: frame_num: frame number to assemble
    :param: num_x_tiles: number of tiles in X direction
    :param: num_y_tiles: number of tiles in Y direction
    :param: input_dir: directory containing the tile images
    :param: output_dir: directory containing the combined tile images
    :param: output_file_prefix: prefix for output filename
    :param: output_format: file format for input (tile) and output (combined) image files
    """
    frame_str = f"{frame_num:05d}"
    tile_value = f"{num_x_tiles}x{num_y_tiles}"

    input_pattern = f"{input_dir}/*_{tile_value}-{frame_str}.*"
    output_file = f"{output_dir}/{Constants.TILED_IMAGE_OUTPUT_FILENAME}"

    cmd = [Constants.MAGICK_BIN, input_pattern, Constants.EVALUATE_SEQUENCE_PARAM, output_file]

    try:
        subprocess.run(
            cmd if not Constants.IS_WINDOWS else " ".join(cmd),
            stderr=subprocess.STDOUT,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.output} (code {e.returncode})")


def assemble_tiles(
    start_frame: int,
    end_frame: int,
    num_x_tiles: int,
    num_y_tiles: int,
    input_dir: str,
    output_dir: str,
) -> None:
    """
    Assemble multiple frames in parallel.
    :param: start_frame: first frame number to process
    :param: end_frame: last frame number to process
    :param: num_x_tiles: number of tiles in X direction
    :param: num_y_tiles: number of tiles in Y direction
    :param: input_dir: directory containing the tile images
    :param: output_dir: directory containing the combined tile images
    :param: output_file_prefix: prefix for output filename
    :param: output_format: file format for input (tile) and output (combined) image files
    """
    """Assemble multiple frames in parallel."""
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=os.cpu_count() or Constants.MIN_WORKERS_IF_UNKNOWN
    ) as executor:
        for frame_num in range(start_frame, end_frame + 1):
            executor.submit(
                assemble_frame, frame_num, num_x_tiles, num_y_tiles, input_dir, output_dir
            )


def setup_output_directory(output_dir: str) -> bool:
    """
    Create output directory if it doesn't exist.
    :param: output_dir: Path to the output directory to create
    :return: True if directory was created successfully; False otherwise
    """
    try:
        os.makedirs(output_dir, exist_ok=False)
        return True
    except (PermissionError, FileExistsError):
        return False


def main_routine():
    """
    Processes command-line arguments to process tiles based on a job bundle configuration.
    Note: sample invocation:
        sys.argv[1]: Test configuration name (relative to "job_bundles" subdirectory)
    """
    global COMMAND_LINE_USAGE

    logging.info(Constants.DEADLINE_CLOUD_FOR_VRED_TILE_ASSEMBLER_TEST_TITLE)
    logging.info("=" * (len(Constants.DEADLINE_CLOUD_FOR_VRED_TILE_ASSEMBLER_TEST_TITLE) - 1))

    if len(sys.argv) < 2:
        logging.error(COMMAND_LINE_USAGE)
        return

    test_config_name_arg = sys.argv[1]
    path_resolver = PathResolver()
    test_config_file_path = path_resolver.get_config_file(test_config_name_arg)

    if not test_config_file_path.exists():
        logging.error(f"Test config file '{test_config_file_path.name}' does not exist")
        return

    render_params = load_render_parameter_values.get_vred_render_parameters(test_config_name_arg)
    generated_output_folder = Path(render_params[Constants.OUTPUT_DIRECTORY_FIELD])
    if not setup_output_directory(str(generated_output_folder)):
        logging.error(
            f"Error: output folder already exists or can't be accessed:\n  {generated_output_folder}"
        )
        return

    logging.info(f"Test configuration (job bundle): {test_config_name_arg}")

    scene_file_basename = Path(render_params[Constants.SCENE_FILE_FIELD]).stem
    assemble_tiles(
        render_params[Constants.START_FRAME_FIELD],
        render_params[Constants.END_FRAME_FIELD],
        render_params[Constants.NUM_X_TILES],
        render_params[Constants.NUM_Y_TILES],
        str(path_resolver.get_input_tiles_folder(test_config_name_arg, scene_file_basename)),
        render_params[Constants.OUTPUT_DIRECTORY_FIELD],
    )

    expected_output_folder = path_resolver.get_expected_output_folder(
        test_config_name_arg, scene_file_basename
    )
    logging.debug(f"Expected output folder: {expected_output_folder}")
    logging.debug(f"Generated output folder: {generated_output_folder}")

    result = are_images_similar_by_folder(
        expected_output_folder, generated_output_folder, Constants.IMAGE_SIMILARITY_FACTOR
    )
    logging.info(f"Image comparison match across both folders: {'PASS' if result else 'FAIL'}")


if __name__ == "__main__":
    main_routine()
