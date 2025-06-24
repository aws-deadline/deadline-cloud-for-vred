# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import concurrent.futures
import io
import logging
import os
import platform
import subprocess
import sys

from output_comparison import are_images_similar

"""
Module for assembling image tiles into complete frames using ImageMagick including support for parallel processing of 
multiple frames.
"""

sys.path.extend([os.path.realpath(os.path.dirname(os.path.abspath(__file__)))])
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
logging.getLogger().setLevel(logging.INFO)

EVALUATE_SEQUENCE_PARAM = "-evaluate-sequence max"
IMAGE_SIMILARITY_FACTOR = 0.9
IS_WINDOWS = platform.system().lower() == "windows"
MAGICK_BIN = os.path.normpath(os.environ.get("MAGICK") or "").replace("\\", "/")
MIN_WORKERS_IF_UNKNOWN = 4
OUTPUT_DIRECTORY_NAME = "output"
EXPECTED_OUTPUT_DIRECTORY_NAME = "expected_output"
TILE_DIRECTORY_NAME = "tiles"
TEST_CONFIGURATION_DIRECTORY_NAME = "configurations"
TILED_IMAGE_OUTPUT_FILENAME = "image-00000.png"


def assemble_frame(
    frame_num: int,
    num_x_tiles: int,
    num_y_tiles: int,
    input_dir: str,
    output_dir: str,
    output_file_prefix: str,
    output_format: str,
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
    input_path = os.path.normpath(input_dir).replace("\\", "/")
    output_path = os.path.normpath(output_dir).replace("\\", "/")
    frame_str = f"{frame_num:05d}"
    # Note: tile value is not [rows]x[columns]; it is [columns]x[rows]
    tile_value = f"{num_x_tiles}x{num_y_tiles}"
    input_file_mask = rf"{input_path}/*_{tile_value}-{frame_str}.*"
    # Consider adding back capability to handle different tiled image formats
    output_file = rf"{output_path}/{TILED_IMAGE_OUTPUT_FILENAME}"
    command_and_arg_list: list[str] = [
        MAGICK_BIN,
        input_file_mask,
        EVALUATE_SEQUENCE_PARAM,
        output_file,
    ]
    try:
        invocation = " ".join(command_and_arg_list) if IS_WINDOWS else command_and_arg_list
        output = subprocess.run(invocation, stderr=subprocess.STDOUT, check=True, text=True)
        print(output)
    except subprocess.CalledProcessError as error:
        print(
            f"Command: [{invocation}] failed: \n{error.output}\n with return code {error.returncode}"
        )


def assemble_tiles(
    start_frame: int,
    end_frame: int,
    num_x_tiles: int,
    num_y_tiles: int,
    input_dir: str,
    output_dir: str,
    output_file_prefix: str,
    output_format: str,
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
    # Parallel processing of frames
    max_workers = os.cpu_count() or MIN_WORKERS_IF_UNKNOWN
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for frame_num in range(start_frame, end_frame + 1):
            executor.submit(
                assemble_frame,
                frame_num,
                num_x_tiles,
                num_y_tiles,
                input_dir,
                output_dir,
                output_file_prefix,
                output_format,
            )


def main_routine():
    """
    Processes command-line arguments to launch VRED with specified scene and configuration files.
    Note: expects one command-line arguments: python script.py test_config.json
        sys.argv[1]: Test configuration file name (relative to "configurations" subdirectory)
    """
    import load_render_parameter_values

    if len(sys.argv) <= 1:
        logging.error("Error: no test configuration file argument provided")
        return

    test_config_file_arg = sys.argv[1]
    current_module_path = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
    test_config = os.path.realpath(
        os.path.join(current_module_path, TEST_CONFIGURATION_DIRECTORY_NAME, test_config_file_arg)
    )
    if not os.path.isfile(test_config):
        logging.error(
            f"Error: JSON test configuration file '{test_config_file_arg}' does not exist"
        )
        return
    test_config_basename = os.path.splitext(os.path.basename(test_config_file_arg))[0]
    render_parameters = load_render_parameter_values.get_vred_render_parameters(
        test_config_file_arg
    )
    scene_file_basename = os.path.splitext(os.path.basename(render_parameters["SceneFile"]))[0]
    tile_path = os.path.join(
        current_module_path, TILE_DIRECTORY_NAME, f"{scene_file_basename}-{test_config_basename}"
    )
    render_parameters["OutputDir"] = os.path.join(current_module_path, OUTPUT_DIRECTORY_NAME)
    assemble_tiles(
        render_parameters["StartFrame"],
        render_parameters["EndFrame"],
        render_parameters["TileNumberX"],
        render_parameters["TileNumberY"],
        tile_path,
        render_parameters["OutputDir"],
        render_parameters["OutputFileNamePrefix"],
        render_parameters["OutputFormat"],
    )
    generated_output = os.path.realpath(
        os.path.join(render_parameters["OutputDir"], TILED_IMAGE_OUTPUT_FILENAME)
    )
    expected_output = os.path.realpath(
        os.path.join(
            current_module_path,
            EXPECTED_OUTPUT_DIRECTORY_NAME,
            f"{scene_file_basename}-{test_config_basename}",
            TILED_IMAGE_OUTPUT_FILENAME,
        )
    )
    result = are_images_similar(expected_output, generated_output, IMAGE_SIMILARITY_FACTOR)
    logging.info(f"Tiled image comparison result: {result}")


if __name__ == "__main__":
    main_routine()
