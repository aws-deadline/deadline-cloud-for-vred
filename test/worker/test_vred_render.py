# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Deadline Cloud for VRED Rendering - local semi-automated test module.

Tests output generated from main worker module.
Launches VRED, loads a scene file, initializes rendering configuration
(via load_render_parameter_values.py and JSON configuration) and
initiates VRED_RenderScript_DeadlineCloud.py to launch the actual rendering process.

Note: requires either VREDCORE or VREDPRO environment variable to be set with
a valid path to the VRED executable.

Example paths:
    Linux: /opt/Autodesk/VREDCluster-{version}/bin/VREDCore
    Windows: C:/Program Files/Autodesk/VREDPro-{version}/bin/WIN64/VREDCore.exe

Note:
    If both environment variables are set, then VREDCORE takes precedence.
"""

import io
import logging
import pytest
import shutil
import sys
from pathlib import Path

from test.common.vred_runner import VREDRunner
from test.common.output_comparison import are_images_similar_by_folder
from test.worker.path_resolver import PathResolver

logging.basicConfig(format="%(message)s", level=logging.INFO)
# Only set unicode stdout when running as script, not under pytest
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def setup_render_output_directory(output_dir: str) -> bool:
    """
    Create output directory if it doesn't exist.
    :param: output_dir: Path to the output directory to create
    :return: True if directory was created successfully; False otherwise
    """
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return True
    except PermissionError:
        return False


def run_vred_render_test(test_config_name_arg: str, scene_filename: str):
    """
    Processes arguments to launch VRED to render based on a job bundle configuration and
    optional scene file override (to the scene file specified within the job bundle).
    """
    path_resolver = PathResolver()
    scene_file_path = path_resolver.get_scene_file(scene_filename)
    test_config_file_path = path_resolver.get_config_file(test_config_name_arg)

    if scene_file_path and not scene_file_path.exists():
        raise FileNotFoundError(f"Scene file '{scene_file_path.name}' does not exist")
    if not test_config_file_path.exists():
        raise FileNotFoundError(f"Test config file '{test_config_file_path.name}' does not exist")

    bundle_dir = path_resolver.get_job_bundles_folder() / test_config_name_arg

    # Set up the output directory wher the rendered image will be saved
    output_subdir_name = f"{scene_filename}-{test_config_name_arg}"
    output_subdir_path = path_resolver.get_output_folder() / output_subdir_name
    if not setup_render_output_directory(str(output_subdir_path)):
        raise RuntimeError(
            f"Error: output folder already exists or can't be accessed: {output_subdir_path}"
        )

    vred_runner = VREDRunner()
    vred_runner.setup_environment()
    vred_runner.invoke_vred_render(
        path_resolver.base_path, scene_file_path, bundle_dir, output_subdir_path
    )

    scene_file_basename = scene_file_path.stem

    expected_output_folder = path_resolver.get_expected_output_folder(
        test_config_name_arg, scene_file_basename
    )
    logging.debug(f"Expected output folder: {expected_output_folder}")
    logging.debug(f"Generated output folder: {output_subdir_path}")

    image_similarity_factor = 10.0
    result = are_images_similar_by_folder(
        expected_output_folder, output_subdir_path, image_similarity_factor
    )
    logging.info(f"Image comparison match across both folders: {'PASS' if result else 'FAIL'}")
    assert result, "Image comparison failed"


@pytest.fixture(scope="module", autouse=True)
def setup_and_cleanup_worker_output():
    """
    Module-scoped fixture to clean up output directory before and after all worker tests.
    This fixture runs automatically for all tests in this module.
    """
    output_dir = Path(__file__).parent / "output"

    # Setup: Clean output directory before tests
    logging.info("Cleaning up worker output directory before tests...")
    try:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(exist_ok=True)
        logging.info(f"Worker output directory prepared: {output_dir}")
    except (OSError, PermissionError) as e:
        logging.warning(f"Could not clean worker output directory: {e}")

    yield  # Run all tests

    # Teardown: Clean output directory after tests
    logging.info("Cleaning up worker output directory after tests...")
    try:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        logging.info("Worker output directory cleaned up")
    except (OSError, PermissionError) as e:
        logging.warning(f"Could not clean worker output directory: {e}")


def test_vred_render_one_frame_japanese():
    """Test VRED rendering one frame with Japanese filename."""
    run_vred_render_test("one_frame", "ここにテキストを入力.vpb")


def test_vred_render_one_frame_spaces():
    """Test VRED rendering one frame with spaces in filename."""
    run_vred_render_test("one_frame", "LightweightWith Spaces.vpb")


def test_vred_render_gpu_raytracing():
    """Test VRED rendering with GPU ray tracing enabled."""
    run_vred_render_test("gpu_raytracing", "Cone.vpb")
