# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Deadline Cloud for VRED Submitter semi-automated test module.

Tests submitter UI and related job bundle output. Launches VRED, loads a scene file, applies
settings to submitter, exports a job bundle.

High-level routine of this test module:

- Opens a VRED session (one per test for exercising different render parameters, reference
  referencing)
- In VRED session, a Qt-based Submitter UI dialog appears
- Values are entered into Qt controls in that dialog
- A callback (in regular submitter code) is triggered that pulls UI values from Qt into a backend
  render settings object
- Exports render settings object to a job bundle
- Compares generated job bundle v.s. expected job bundle (parameter values, asset references)
  - Results are scene file-specific / test configuration-specific.

Note: requires VREDPRO environment variable to be set with a valid path to the VREDPro executable

Example paths:
    Windows: C:/Program Files/Autodesk/VREDPro-{version}/bin/WIN64/VREDPro.exe
"""

import logging
import pytest
import shutil
import yaml
from pathlib import Path

from deadline.vred_submitter.constants import Constants

from test.integ.helpers.vred_runner import VREDRunner
from test.integ.helpers.job_bundle_output_comparison import assert_job_bundle_matches
from test.integ.helpers.sticky_settings_verification import verify_sticky_settings_file
from test.integ.path_resolver import PathResolver

logging.basicConfig(format="%(message)s", level=logging.INFO)

OUTPUT_DIRECTORY_NAME = "output"


@pytest.fixture(scope="module", autouse=True)
def setup_and_cleanup_submitter_output():
    """
    Module-scoped fixture to clean up output directory before and after all submitter tests.
    This fixture runs automatically for all tests in this module.
    """
    output_dir = Path(__file__).parent / OUTPUT_DIRECTORY_NAME

    try:
        # Clean output directory before tests
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(exist_ok=True)
        logging.info(f"Submitter test output directory prepared: {output_dir}")
    except (OSError, PermissionError) as e:
        logging.warning(f"Could not clean submitter test output directory: {e}")

    yield  # Run all tests

    # Teardown: Clean output directory after tests
    try:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        logging.info("Submitter test output directory cleaned up")
    except (OSError, PermissionError) as e:
        logging.warning(f"Could not clean submitter test output directory: {e}")


def run_vred_submitter_test(
    test_config_name_arg: str,
    test_output_dir: str,
    scene_filename_arg: str | None = None,
    test_settings: list | None = None,
) -> bool:
    """
    Launch VRED Pro with submitter dialog with a specific tests submitter testing.
    param: test_config_name_arg: Test configuration name for expected output folder
    param: scene_filename_arg: Optional scene file name override
    param: test_settings: Optional list of setting dictionaries for dialog
    return: True if test execution succeeded, False otherwise
    raise: FileNotFoundError: If scene file or expected output folder doesn't exist
    raise: RuntimeError: If output directory setup fails
    """
    path_resolver = PathResolver()
    scene_file_path = (
        path_resolver.get_scene_file(scene_filename_arg) if scene_filename_arg else None
    )
    scene_file_basename = Path(scene_file_path).stem if scene_file_path else "default"
    expected_output_folder = path_resolver.get_expected_bundle_folder(
        test_config_name_arg, scene_file_basename
    )

    if scene_file_path and not scene_file_path.exists():
        raise FileNotFoundError(f"Scene file '{scene_file_path.name}' does not exist")
    if not expected_output_folder.exists():
        raise FileNotFoundError(
            f"Expected output folder '{expected_output_folder.name}' does not exist"
        )

    # Output directory cleanup is handled by module-scoped fixture

    if not setup_output_directory(str(test_output_dir)):
        raise RuntimeError(f"Error: output folder can't be accessed: {test_output_dir}")

    logging.info(f"Scene file: {scene_file_basename}.vpb")
    logging.info(f"Test configuration (job bundle): {test_config_name_arg}")
    logging.debug(f"Expected output folder: {expected_output_folder}")
    logging.debug(f"Generated output folder: {test_output_dir}")

    vred_runner = VREDRunner()
    vred_runner.setup_environment()
    bootstrap_code = vred_runner.get_submitter_bootstrap_code(
        test_settings if test_settings is not None else [], str(test_output_dir)
    )
    return vred_runner.invoke_vred(
        bootstrap_code, str(scene_file_path) if scene_file_path else "", require_pro=True
    )


def setup_output_directory(output_dir: str) -> bool:
    """
    Create output directory if it doesn't exist.
    param: output_dir: path to output directory
    return: True if directory was created successfully; False otherwise
    """
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return True
    except PermissionError:
        return False


def is_valid_template(template_path: Path) -> bool:
    """
    Validate YAML template file structure.
    param: template_path: path to template.yaml file
    returns: True if valid YAML, False otherwise
    """
    try:
        with open(template_path) as f:
            yaml.safe_load(f)
        return True
    except Exception:
        return False


@pytest.mark.submitter
class TestVREDSubmitter:
    """Tests that ensure VRED submitters produce the correct job bundle."""

    def _run_submitter_dialog_field_value_compare_test(
        self, test_name: str, scene_name: str, parameter_overrides=None, asset_overrides=None
    ):
        """Helper method for VRED submitter dialog tests"""
        test_subdir = f"{Path(scene_name).stem}-{test_name}"
        test_output_dir = Path(__file__).parent / OUTPUT_DIRECTORY_NAME / test_subdir
        test_output_dir.mkdir(parents=True, exist_ok=True)

        path_resolver = PathResolver()
        scene_file_path = path_resolver.get_scene_file(scene_name)
        assert (
            scene_file_path is not None
        ), f"Scene file path should not be None for scene: {scene_name}"
        expected_sticky_settings_filename = scene_file_path.with_suffix(
            Constants.RENDER_SUBMITTER_SETTINGS_FILE_EXT
        )
        if expected_sticky_settings_filename.exists():
            expected_sticky_settings_filename.unlink()
        assert (
            not expected_sticky_settings_filename.exists()
        ), f"Sticky settings file should not exist yet: {expected_sticky_settings_filename}"

        # Convert parameter_overrides to test_settings format expected by
        # submitter_dialog_controller
        test_settings = [{"name": k, "value": v} for k, v in parameter_overrides.items()]

        assert run_vred_submitter_test(test_name, str(test_output_dir), scene_name, test_settings)
        assert is_valid_template(test_output_dir / "template.yaml")

        expected_output_dir = path_resolver.get_expected_bundle_folder(
            test_name, Path(scene_name).stem
        )

        # Pass asset_overrides info to comparison for special handling
        comparison_context = {"test_name": test_name, "asset_overrides": asset_overrides or []}
        assert_job_bundle_matches(test_output_dir, expected_output_dir, comparison_context)
        assert (
            expected_sticky_settings_filename.exists()
        ), f"Sticky settings file should exist in: {expected_sticky_settings_filename}"

        # Verify sticky settings file contents
        verify_sticky_settings_file(expected_sticky_settings_filename, parameter_overrides)

    @pytest.mark.scene_files(Path("scene_files") / "Cone.vpb")
    def test_submitter_dialog_basic_settings(self):
        """Test submitter dialog with basic render settings."""
        self._run_submitter_dialog_field_value_compare_test(
            "basic_render",
            "Cone.vpb",
            {
                "output_directories": ["c:\\vred-snapshots"],
                "StartFrame": 0,
                "EndFrame": 25,
                "OutputDir": "c:\\vred-snapshots",
                "OutputFileNamePrefix": "image",
                "OutputFormat": "PNG",
                "RenderAnimation": "false",
                "View": "Front",
            },
        )

    @pytest.mark.scene_files(Path("scene_files") / "Cone.vpb")
    def test_submitter_dialog_tiling_settings(self):
        """Test submitter dialog with tiling/region rendering settings."""
        self._run_submitter_dialog_field_value_compare_test(
            "7x5_tiles",
            "Cone.vpb",
            {
                "output_directories": ["c:\\vred-snapshots"],
                "StartFrame": -3,
                "EndFrame": 100,
                "NumXTiles": 7,
                "NumYTiles": 5,
                "OutputDir": "c:\\vred-snapshots",
                "OutputFileNamePrefix": "testimage",
                "OutputFormat": "JPG",
                "RenderAnimation": "true",
                "RegionRendering": "true",
                "View": "Front",
            },
        )

    @pytest.mark.scene_files(Path("scene_files") / "FileReferencing.vpb")
    def test_submitter_dialog_bundle_comparison(self):
        """Test that input file references match the expected list."""
        self._run_submitter_dialog_field_value_compare_test(
            "bundle_comparison",
            "FileReferencing.vpb",
            {
                "output_directories": ["c:\\vred-snapshots"],
                "StartFrame": 0,
                "EndFrame": 25,
                "OutputDir": "c:\\vred-snapshots",
                "OutputFileNamePrefix": "image",
                "OutputFormat": "PNG",
                "RenderAnimation": "false",
                "RegionRendering": "false",
                "NumXTiles": 1,
                "NumYTiles": 1,
                "SequenceName": "Sequence",
                "View": "Back",
            },
            ["C:\\WorkArea\\test.wire", "C:\\WorkArea\\Only\\LightweightWithoutSpaces.vpb"],
        )

    @pytest.mark.scene_files(Path("scene_files") / "Cone.vpb")
    def test_submitter_dialog_gpu_raytracing_settings(self):
        """Test GPU ray tracing job bundle generation."""
        self._run_submitter_dialog_field_value_compare_test(
            "gpu_raytracing",
            "Cone.vpb",
            {
                "output_directories": ["c:\\vred-snapshots"],
                "StartFrame": 0,
                "EndFrame": 5,
                "OutputDir": "c:\\vred-snapshots",
                "OutputFileNamePrefix": "gpu_test",
                "OutputFormat": "PNG",
                "RenderAnimation": "false",
                "GPURaytracing": "true",
                "View": "Perspective",
            },
        )

    @pytest.mark.scene_files(Path("scene_files") / "Cone.vpb")
    def test_submitter_dialog_animation_type_settings(self):
        """Test animation type job bundle generation."""
        self._run_submitter_dialog_field_value_compare_test(
            "animation_type",
            "Cone.vpb",
            {
                "output_directories": ["c:\\vred-snapshots"],
                "StartFrame": 1,
                "EndFrame": 10,
                "FrameStep": 2,  # Every other frame
                "FramesPerTask": 2,
                "OutputDir": "c:\\vred-snapshots",
                "OutputFileNamePrefix": "anim",
                "OutputFormat": "JPG",
                "RenderAnimation": "true",
                "AnimationType": "Timeline",
                "View": "Front",
            },
        )

    @pytest.mark.scene_files(Path("scene_files") / "Cone.vpb")
    def test_submitter_dialog_dlss_settings(self):
        """Test DLSS quality job bundle generation."""
        self._run_submitter_dialog_field_value_compare_test(
            "dlss_quality",
            "Cone.vpb",
            {
                "output_directories": ["c:\\vred-snapshots"],
                "StartFrame": 0,
                "EndFrame": 1,
                "OutputDir": "c:\\vred-snapshots",
                "OutputFileNamePrefix": "dlss_test",
                "OutputFormat": "PNG",
                "RenderAnimation": "false",
                "DLSSQuality": "Quality",
                "GPURaytracing": "true",
                "ImageWidth": 1920,
                "ImageHeight": 1080,
                "View": "Front",
            },
        )

    @pytest.mark.scene_files(Path("scene_files") / "Cone.vpb")
    def test_submitter_dialog_output_formats(self):
        """Test various output format job bundle generation."""
        self._run_submitter_dialog_field_value_compare_test(
            "output_format",
            "Cone.vpb",
            {
                "output_directories": ["c:\\vred-snapshots"],
                "StartFrame": 0,
                "EndFrame": 1,
                "OutputDir": "c:\\vred-snapshots",
                "OutputFileNamePrefix": "output_format_test",
                "OutputFormat": "TIFF",
                "RenderAnimation": "false",
                "View": "Front",
            },
        )

    @pytest.mark.scene_files(Path("scene_files") / "Cone.vpb")
    def test_submitter_dialog_render_quality(self):
        """Test different render quality job bundle generation."""
        self._run_submitter_dialog_field_value_compare_test(
            "render_quality",
            "Cone.vpb",
            {
                "output_directories": ["c:\\vred-snapshots"],
                "StartFrame": 0,
                "EndFrame": 1,
                "OutputDir": "c:\\vred-snapshots",
                "OutputFileNamePrefix": "quality",
                "OutputFormat": "PNG",
                "RenderAnimation": "false",
                "RenderQuality": "Analytic Low",
                "View": "Front",
            },
        )

    @pytest.mark.scene_files(Path("scene_files") / "Cone.vpb")
    def test_submitter_dialog_high_resolution(self):
        """Test high resolution rendering job bundle generation."""
        self._run_submitter_dialog_field_value_compare_test(
            "high_resolution",
            "Cone.vpb",
            {
                "output_directories": ["c:\\vred-snapshots"],
                "StartFrame": 0,
                "EndFrame": 1,
                "OutputDir": "c:\\vred-snapshots",
                "OutputFileNamePrefix": "hires",
                "OutputFormat": "PNG",
                "RenderAnimation": "false",
                "ImageWidth": 3840,  # 4K width
                "ImageHeight": 2160,  # 4K height
                "DPI": 300,  # High DPI
                "RenderQuality": "Realistic High",
                "View": "Front",
            },
        )
