# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Deadline Cloud for VRED Submitter - integration testing - local semi-automated test module.

Tests submitter UI and related job bundle output. Launches VRED, loads a scene file, applies settings to submitter,
exports a job bundle.

High-level routine of this test module:

- Opens a VRED session (one per test - for exercising different render parameters, reference referencing)
- In VRED session,a Qt-based Submitter UI dialog appears
- Values are entered into Qt controls in that dialog
- A callback (in regular submitter code) is triggered that pulls UI values from Qt into a backend render settings object
- Exports render settings object to a job bundle
- Compares actual (generated) job bundle v.s. expected job bundle (parameter values, asset references).
* Results are scene file-specific / test configuration-specific.

Note: requires either VREDCORE or VREDPRO environment variable to be set with a valid path to the VRED executable.

Example paths:
    Linux: /opt/Autodesk/VREDCluster-{version}/bin/VREDCore
    Windows: C:/Program Files/Autodesk/VREDPro-{version}/bin/WIN64/VREDCore.exe

Note:
    If both environment variables are set, then VREDCORE takes precedence.
"""

import logging
import os
import pytest
import shutil
import subprocess
from pathlib import Path

from deadline.vred_submitter.constants import Constants

from .constants import Constants as TestConstants
from .output_comparison import assert_parameter_values_similar, assert_asset_references_similar
from .path_resolver import PathResolver
from .sticky_settings_verification import verify_sticky_settings_file

# Add path to access data classes
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

logging.basicConfig(format="%(message)s", level=logging.INFO)


class VREDRenderTestRunner:
    """Handles VRED execution and UI operations."""

    def __init__(self):
        self.current_module_path = Path(__file__).resolve().parent
        self.submitter_path = (
            self.current_module_path.parent.parent / TestConstants.VRED_SUBMITTER_SOURCE_PATH
        )

    def get_bootstrap_code(self, test_settings: list, bundle_path: str) -> str:
        """
        Generate bootstrap code for submitter dialog testing.
        param: test_settings: List of setting dictionaries having 'name' and 'value' keys
        param: bundle_path: Path where job bundle should be exported
        return: generated bootstrap code for submitter dialog interaction
        """
        return (
            rf"""
import importlib;
import os;
import sys;
from vrController import terminateVred, vrLogError;
sys.path.extend([r'{self.current_module_path}','{self.submitter_path}']);
controller_module_name='submitter_dialog_controller';
controller_module = importlib.util.find_spec(controller_module_name) is not None and importlib.import_module(
controller_module_name) or None;
controller_module.run_submitter_integration_test({test_settings}, r'{bundle_path}');
terminateVred();
""".replace(
                "\n", ""
            )
            .replace("\\", "/")
            .replace("\t", "")
        )

    def get_vred_executable(self) -> str:
        """
        Determine VRED binary to use based on environment variable state and binary availability
        return: path to VRED binary
        raise: OSError: if a valid VRED binary cannot be determined.
        """

        for env_var in [TestConstants.VRED_CORE_ENV_VAR, TestConstants.VRED_PRO_ENV_VAR]:
            if executable := os.environ.get(env_var):
                if os.path.isfile(executable):
                    return executable
        raise OSError(TestConstants.ERROR_UNKNOWN_VRED_PATH)

    def setup_environment(self) -> None:
        """
        Configure VRED environment variables for web interface disabling, license release timing, and diagnostics.
        """
        env_settings = {
            TestConstants.DISABLE_WEBINTERFACE_ENV_VAR: TestConstants.DISABLE_WEBINTERFACE_VALUE,
            TestConstants.LICENSE_RELEASE_TIME_ENV_VAR: TestConstants.LICENSE_RELEASE_TIME_SECONDS_LIMIT,
            TestConstants.FLEXLM_DIAGNOSTICS_ENV_VAR: TestConstants.FLEXLM_DIAGNOSTICS_HIGH_VALUE,
        }
        os.environ.update(env_settings)

    def invoke_vred(self, test_settings: list, bundle_path: str, scene_file: str) -> bool:
        """
        Invoke VRED binary with submitter dialog controller for integration testing.
        :param: test_settings: list of settings dictionaries to apply to the Qt dialog
        :param: bundle_path: path where the job bundle should be exported
        :param: scene_file: path to the scene file to load
        :return: True if VRED invocation succeeded; False otherwise
        """
        os.environ[TestConstants.CODE_PASSING_ENV_VAR] = self.get_bootstrap_code(
            test_settings, bundle_path
        )

        executable = self.get_vred_executable()
        if TestConstants.IS_WINDOWS:
            executable = f'"{executable}"'
            scene_file = f'"{scene_file}"'

        cmd = [
            executable,
            scene_file,
            TestConstants.DISABLE_PYTHON_SANDBOX_PARAM,
            TestConstants.FAST_START_PARAM,
            TestConstants.POST_PYTHON_PARAM,
            TestConstants.VRED_PYTHON_PRE_BOOTSTRAP_CODE,
        ]

        try:
            invocation = " ".join(cmd) if TestConstants.IS_WINDOWS else cmd
            result = subprocess.run(invocation, stderr=subprocess.STDOUT, check=True, text=True)
            logging.debug(result)
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {invocation}\n{e.output}\nReturn code: {e.returncode}")
            return False
        return True


def run_vred_submitter_test(
    test_config_name_arg: str,
    scene_filename_arg: str | None = None,
    test_settings: list | None = None,
):
    """
    Launch VRED with submitter dialog with a specific tests integration testing.
    param: test_config_name_arg: Test configuration name for expected output folder
    param: :scene_filename_arg: Optional scene file name override
    param: test_settings: Optional list of setting dictionaries for dialog
    return: True if test execution succeeded, False otherwise
    raise: FileNotFoundError: If scene file or expected output folder doesn't exist
    raise: RuntimeError: If output directory setup fails
    """
    logging.info(TestConstants.DEADLINE_CLOUD_FOR_VRED_SUBMITTER_UI_TEST_TITLE)
    logging.info("=" * (len(TestConstants.DEADLINE_CLOUD_FOR_VRED_SUBMITTER_UI_TEST_TITLE) - 1))

    path_resolver = PathResolver()
    scene_file_path = (
        path_resolver.get_scene_file(scene_filename_arg) if scene_filename_arg else None
    )
    scene_file_basename = Path(scene_file_path).stem if scene_file_path else "default"
    expected_output_folder = path_resolver.get_expected_output_folder(
        test_config_name_arg, scene_file_basename
    )

    if scene_file_path and not scene_file_path.exists():
        raise FileNotFoundError(f"Scene file '{scene_file_path.name}' does not exist")
    if not expected_output_folder.exists():
        raise FileNotFoundError(
            f"Expected output folder '{expected_output_folder.name}' does not exist"
        )

    # Clean up resources that may be left over from a previous run
    cleanup_output_directory()

    generated_output_folder = Path(__file__).parent / TestConstants.OUTPUT_DIRECTORY_NAME
    if not setup_output_directory(str(generated_output_folder)):
        raise RuntimeError(
            f"Error: output folder already exists or can't be accessed: {generated_output_folder}"
        )

    logging.info(f"Scene file: {scene_file_basename}.vpb")
    logging.info(f"Test configuration (job bundle): {test_config_name_arg}")
    logging.debug(f"Expected output folder: {expected_output_folder}")
    logging.debug(f"Generated output folder: {generated_output_folder}")

    vred_test_runner = VREDRenderTestRunner()
    vred_test_runner.setup_environment()
    return vred_test_runner.invoke_vred(
        test_settings if test_settings is not None else [],
        str(generated_output_folder),
        str(scene_file_path) if scene_file_path else "",
    )


def setup_output_directory(output_dir: str) -> bool:
    """
    Create output directory if it doesn't exist.
    param: output_dir: path to output directory
    return: True if directory was created successfully; False otherwise
    """
    try:
        os.makedirs(output_dir, exist_ok=False)
        return True
    except (PermissionError, FileExistsError):
        return False


def cleanup_output_directory():
    """Remove existing output directory and its contents."""
    output_dir = Path(__file__).parent / TestConstants.OUTPUT_DIRECTORY_NAME
    if output_dir.exists():
        shutil.rmtree(output_dir)


def is_valid_template(template_path: Path) -> bool:
    """
    Validate YAML template file structure.
    param: template_path: path to template.yaml file
    returns: True if valid YAML, False otherwise
    """
    try:
        import yaml

        with open(template_path) as f:
            yaml.safe_load(f)
        return True
    except Exception:
        return False


def get_reference_parameter_values():
    """
    Generate reference parameter values for test validation.
    return: dictionary containing parameterValues list with default settings
    """
    # Mock vred_logger before importing data_classes to avoid vrController import issues
    from unittest.mock import MagicMock
    import sys

    sys.modules["deadline.vred_submitter.vred_logger"] = MagicMock()

    from deadline.vred_submitter.data_classes import RenderSubmitterUISettings

    settings = RenderSubmitterUISettings()
    param_values = []

    # Exclude the same shared parameters that are filtered out in the actual submitter
    shared_parameters = {
        "priority",
        "initial_status",
        "max_failed_tasks_count",
        "max_retries_per_task",
        "max_worker_count",
    }

    # Add parameters from RenderSubmitterUISettings defaults (excluding shared parameters)
    for field_name, field_value in settings.__dict__.items():
        if field_name in shared_parameters:
            continue  # Skip shared parameters that are filtered out
        if isinstance(field_value, bool):
            field_value = "true" if field_value else "false"
        elif isinstance(field_value, list):
            field_value = ""
        param_values.append(
            {TestConstants.NAME_FIELD: field_name, TestConstants.VALUE_FIELD: field_value}
        )

    # Override specific values
    [
        param.update({TestConstants.VALUE_FIELD: "scripts"})
        for param in param_values
        if param[TestConstants.NAME_FIELD] == "JobScriptDir"
    ]

    # Add deadline-specific fields
    param_values.extend(
        [
            {"name": "deadline:targetTaskRunStatus", "value": "READY"},
            {"name": "deadline:maxFailedTasksCount", "value": 20},
            {"name": "deadline:maxRetriesPerTask", "value": 5},
            {"name": "deadline:priority", "value": 50},
        ]
    )

    # Note: Shared parameters (priority, initial_status, max_failed_tasks_count,
    # max_retries_per_task, max_worker_count) are now filtered out of job bundle
    # parameters and handled by deadline-cloud library at a higher level

    return {"parameterValues": param_values}


def get_reference_asset_references():
    """
    Generate reference asset references structure for test validation.
    return: dictionary containing assetReferences structure with empty input, output, referenced paths
    """
    return {
        "assetReferences": {
            "inputs": {"filenames": [], "directories": []},
            "outputs": {"directories": []},
            "referencedPaths": [],
        }
    }


@pytest.mark.submitter
class TestVREDSubmitter:
    """Tests that ensure VRED submitters produce the correct job bundle."""

    def _run_submitter_dialog_field_value_compare_test(
        self, test_name: str, scene_name: str, parameter_overrides=None, asset_overrides=None
    ):
        """Helper method for VRED submitter dialog tests"""
        job_history_dir = Path(__file__).parent / TestConstants.OUTPUT_DIRECTORY_NAME
        job_history_dir.mkdir(parents=True, exist_ok=True)

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

        # Convert parameter_overrides to test_settings format expected by submitter_dialog_controller
        test_settings = [{"name": k, "value": v} for k, v in parameter_overrides.items()]

        assert run_vred_submitter_test(test_name, scene_name, test_settings)
        assert is_valid_template(job_history_dir / TestConstants.TEMPLATE_FILENAME)

        expected_parameter_values = get_reference_parameter_values().copy()
        base_parameter_overrides = {
            TestConstants.SCENE_FILE_FIELD: str(scene_file_path),
            TestConstants.OUTPUT_DIRECTORY_FIELD: str(job_history_dir),
            "input_directories": [],
            "input_filenames": [],
            "JobScriptDir": str(TestConstants.JOB_BUNDLE_SCRIPTS_FOLDER_PATH),
        }
        all_parameter_overrides = {**base_parameter_overrides, **parameter_overrides}
        for param in expected_parameter_values[TestConstants.PARAMETER_VALUES_FIELD]:
            if param[TestConstants.NAME_FIELD] in all_parameter_overrides:
                param[TestConstants.VALUE_FIELD] = all_parameter_overrides[
                    param[TestConstants.NAME_FIELD]
                ]

        expected_asset_references = get_reference_asset_references().copy()
        expected_asset_references["assetReferences"]["inputs"]["filenames"] = [str(scene_file_path)]
        if asset_overrides:
            expected_asset_references["assetReferences"]["inputs"]["filenames"].extend(
                asset_overrides
            )

        assert_parameter_values_similar(job_history_dir, expected_parameter_values)
        assert_asset_references_similar(job_history_dir, expected_asset_references)
        assert (
            expected_sticky_settings_filename.exists()
        ), f"Sticky settings file should exist in: {expected_sticky_settings_filename}"

        # Verify sticky settings file contents
        verify_sticky_settings_file(expected_sticky_settings_filename, parameter_overrides)

    @pytest.mark.scene_files(Path("scene_files") / "LightweightWith Spaces.vpb")
    def test_submitter_dialog_basic_settings(self):
        # Test submitter dialog with basic render settings.
        self._run_submitter_dialog_field_value_compare_test(
            "basic_render",
            "LightweightWith Spaces.vpb",
            {
                "output_directories": ["c:\\vred-snapshots"],
                "StartFrame": 0,
                "EndFrame": 25,
                "OutputDir": "c:\\vred-snapshots",
                "OutputFileNamePrefix": "image",
                "OutputFormat": "PNG",
                "RenderAnimation": "false",
                "View": "Back",
            },
        )

    @pytest.mark.scene_files(Path("scene_files") / "Cone.vpb")
    def test_submitter_dialog_tiling_settings(self):
        # Test submitter dialog with tiling/region rendering settings.
        self._run_submitter_dialog_field_value_compare_test(
            "7x5_tiles",
            "Cone.vpb",
            {
                "output_directories": ["c:\\vred-snapshots"],
                "EndFrame": 100,
                TestConstants.NUM_X_TILES_FIELD: 7,
                TestConstants.NUM_Y_TILES_FIELD: 5,
                "OutputDir": "c:\\vred-snapshots",
                "OutputFileNamePrefix": "testimage",
                "OutputFormat": "JPG",
                "RenderAnimation": "true",
                "RegionRendering": "true",
                "StartFrame": -3,
                "View": "Front",
            },
        )

    @pytest.mark.scene_files(Path("scene_files") / "FileReferencing.vpb")
    def test_submitter_dialog_bundle_comparison(self):
        # Test that input file references match the expected list.
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
                TestConstants.NUM_X_TILES_FIELD: 1,
                TestConstants.NUM_Y_TILES_FIELD: 1,
                "SequenceName": "Sequence",
                "View": "Back",
            },
            ["C:\\WorkArea\\test.wire", "C:\\WorkArea\\Only\\LightweightWithoutSpaces.vpb"],
        )
