# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Deadline Cloud for VRED Rendering Test

Tests VRED rendering using OpenJD CLI to execute the job template used in production.

Note: requires either VREDCORE or VREDPRO environment variable to be set with
a valid path to the VRED executable.
Example paths:
    Linux: /opt/Autodesk/VREDCluster-{version}/bin/VREDCore
    Windows: C:/Program Files/Autodesk/VREDPro-{version}/bin/WIN64/VREDCore.exe
"""

import io
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from deadline.client.job_bundle.parameters import read_job_bundle_parameters
from test.integ.helpers.output_comparison import are_images_similar_by_folder
from test.integ.path_resolver import PathResolver

logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
# Only set unicode stdout when running as script, not under pytest
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUTPUT_DIRECTORY_NAME = "output"


@pytest.fixture(scope="module", autouse=True)
def setup_and_cleanup_openjd_output():
    """
    Module-scoped fixture to clean up output directory before and after the render tests.
    This fixture runs automatically for all tests in this module.
    """
    output_dir = Path(__file__).parent / OUTPUT_DIRECTORY_NAME

    # Setup: Clean output directory before tests
    logger.info("Cleaning up OpenJD test output directory before tests...")
    try:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(exist_ok=True)
        logger.info(f"Render test output directory prepared: {output_dir}")
    except (OSError, PermissionError) as e:
        logger.warning(f"Could not clean Render test output directory: {e}")

    yield  # Run all tests

    # Teardown: Clean output directory after tests
    logger.info("Cleaning up Render test output directory after tests...")
    try:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        logger.info("Render test output directory cleaned up")
    except (OSError, PermissionError) as e:
        logger.warning(f"Could not clean Render test output directory: {e}")


def get_job_template_path() -> Path:
    """
    Get the path to the VRED default job template.
    """
    return (
        Path(__file__).parent.parent.parent
        / "src"
        / "deadline"
        / "vred_submitter"
        / "default_vred_job_template.yaml"
    )


def load_job_parameters_from_bundle(bundle_dir: Path) -> dict[str, Any]:
    """
    Load job parameters from the job bundle using the Deadline Cloud client library.

    This uses the same parameter reading logic as the Deadline Cloud client,
    ensuring consistency with how parameters are processed in production.

    Note: This function does NOT perform type conversion because OpenJD Runtime
    expects string values and performs type conversion during template variable
    substitution (e.g., int({{Param.StartFrame}})).

    :param bundle_dir: Path to the job bundle directory
    :return: Dictionary of parameter name to value mappings (as strings)
    """
    # Use Deadline Cloud client's job bundle parameter reader
    job_bundle_parameters = read_job_bundle_parameters(str(bundle_dir))

    # Convert list of {name, value} dicts to a simple dict
    # Keep values as strings for OpenJD Runtime
    # Filter out Deadline Cloud service parameters (deadline:*) as they are not
    # defined in the job template and are only used by Deadline Cloud service
    params = {}
    for param in job_bundle_parameters:
        if "value" in param:
            param_name = param["name"]
            # Skip Deadline Cloud service parameters
            if not param_name.startswith("deadline:"):
                params[param_name] = param["value"]

    return params


def run_openjd_render(
    template_path: Path, job_params: dict[str, Any], output_dir: Path
) -> subprocess.CompletedProcess:
    """
    Execute VRED rendering using OpenJD CLI.

    :param template_path: Path to the job template YAML file
    :param job_params: Dictionary of job parameters
    :param output_dir: Directory path where rendered output will be saved
    :return: CompletedProcess object from subprocess.run
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build OpenJD command
    cmd = [
        "openjd",
        "run",
        str(template_path),
        "--job-param",
        json.dumps(job_params),
    ]

    # Execute OpenJD
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,  # Don't raise exception, we'll check returncode manually
    )

    # Log output
    if result.stdout:
        logger.debug(f"OpenJD stdout:\n{result.stdout}")
    if result.stderr:
        logger.debug(f"OpenJD stderr:\n{result.stderr}")

    return result


def run_vred_render_test_openjd(test_bundle_name: str, scene_filename: str):
    """
    Execute VRED rendering test using OpenJD CLI.

    This function:
    1. Loads job parameters from the test bundle
    2. Overrides scene file and output directory for test environment
    3. Executes rendering via OpenJD CLI
    4. Validates output images against expected results

    :param test_bundle_name: Name of the test configuration (job bundle directory)
    :param scene_filename: Name of the scene file to render
    """
    path_resolver = PathResolver()

    # Resolve paths
    scene_file_path = path_resolver.get_scene_file(scene_filename)
    bundle_dir = path_resolver.get_job_bundles_folder() / test_bundle_name
    template_path = get_job_template_path()

    # Validate paths
    if not scene_file_path.exists():
        raise FileNotFoundError(f"Scene file not found: {scene_file_path}")
    if not bundle_dir.exists():
        raise FileNotFoundError(f"Job bundle not found: {bundle_dir}")
    if not template_path.exists():
        raise FileNotFoundError(f"Job template not found: {template_path}")

    # Load parameters from bundle
    job_params = load_job_parameters_from_bundle(bundle_dir)

    # Override parameters for test environment
    output_subdir_name = f"{scene_filename}-{test_bundle_name}"
    output_dir = path_resolver.get_output_folder() / output_subdir_name

    job_params["SceneFile"] = str(scene_file_path)
    job_params["OutputDir"] = str(output_dir)
    job_params["JobScriptDir"] = str(
        Path(__file__).parent.parent.parent / "src" / "deadline" / "vred_submitter"
    )

    # Execute rendering via OpenJD
    result = run_openjd_render(template_path, job_params, output_dir)

    # Check execution result
    if result.returncode != 0:
        logger.error(f"OpenJD execution failed with return code {result.returncode}")
        raise RuntimeError(f"OpenJD rendering failed: {result.stderr}")

    # Validate output images
    scene_file_basename = scene_file_path.stem
    expected_output_folder = path_resolver.get_expected_render_folder(
        test_bundle_name, scene_file_basename
    )

    logger.debug(f"Expected output folder: {expected_output_folder}")
    logger.debug(f"Generated output folder: {output_dir}")

    if not expected_output_folder.exists():
        raise FileNotFoundError(f"Expected output folder not found: {expected_output_folder}")

    # Compare images
    image_similarity_factor = 30.0
    image_comparison_result = are_images_similar_by_folder(
        expected_output_folder, output_dir, image_similarity_factor
    )

    assert (
        image_comparison_result
    ), "Image comparison failed: rendered output does not match expected images"


def test_vred_render_openjd_gpu_raytracing():
    """
    Test VRED rendering (via OpenJD CLI) with GPU ray tracing.
    """
    run_vred_render_test_openjd("gpu_raytracing", "Cone.vpb")
