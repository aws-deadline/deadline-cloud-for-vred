# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Deadline Cloud for VRED Rendering - local semi-automated test module.

Tests output generated from main worker module. Launches VRED, loads a scene file, initializes rendering configuration
(via load_render_parameter_values.py and JSON configuration) and initiates VRED_RenderScript_DeadlineCloud.py to
launch the actual rendering process.

Note: requires either VREDCORE or VREDPRO environment variable to be set with a valid path to the VRED executable.

Example paths:
    Linux: /opt/Autodesk/VREDCluster-{version}/bin/VREDCore
    Windows: C:/Program Files/Autodesk/VREDPro-{version}/bin/WIN64/VREDCore.exe

Note:
    If both environment variables are set, then VREDCORE takes precedence.
"""

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

COMMAND_LINE_USAGE = f"Usage: python {sys.argv[0]} <job_bundle_config_name> [scene_file]"

sys.path.extend([os.path.realpath(os.path.dirname(os.path.abspath(__file__)))])
logging.basicConfig(format="%(message)s", level=logging.INFO)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


class VREDRenderTestRunner:
    """Handles VRED execution and rendering operations."""

    def __init__(self):
        self.current_module_path = Path(__file__).resolve().parent
        self.submitter_path = (
            self.current_module_path.parent.parent / Constants.VRED_SUBMITTER_SOURCE_PATH
        )

    def get_bootstrap_code(self, test_configuration_name: str) -> str:
        """
        Generate bootstrap code for VRED execution (via CODE_PASSING_ENV_VAR).
        returns: generated bootstrap code with paths and imports configured
        """
        # Inject render parameters into render script, loading both of them at startup, enforce universal exit
        return (
            rf"""
import importlib;
import os;
import sys;
from vrController import terminateVred, vrLogError;
sys.path.extend([r'{self.current_module_path}','{self.submitter_path}']);
render_module_name='VRED_RenderScript_DeadlineCloud';
render_param_module_name='load_render_parameter_values';
render_module = importlib.util.find_spec(render_module_name) is not None and importlib.import_module(
render_module_name) or None;
render_param_module = importlib.util.find_spec(render_param_module_name) is not None and importlib.import_module(
render_param_module_name) or None;
render_module.deadline_cloud_render(
render_param_module.get_vred_render_parameters(r'{test_configuration_name}')) if render_module and 
render_param_module else vrLogError('failed to import module for render script and/or render parameters');
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
        for env_var in [Constants.VRED_CORE_ENV_VAR, Constants.VRED_PRO_ENV_VAR]:
            if executable := os.environ.get(env_var):
                if os.path.isfile(executable):
                    return executable
        raise OSError(Constants.ERROR_UNKNOWN_VRED_PATH)

    def setup_environment(self) -> None:
        """
        Disable VRED's web interface, release license on idle, pass bootstrapping code via environment variable
        """
        env_settings = {
            Constants.DISABLE_WEBINTERFACE_ENV_VAR: Constants.DISABLE_WEBINTERFACE_VALUE,
            Constants.LICENSE_RELEASE_TIME_ENV_VAR: Constants.LICENSE_RELEASE_TIME_SECONDS_LIMIT,
            Constants.FLEXLM_DIAGNOSTICS_ENV_VAR: Constants.FLEXLM_DIAGNOSTICS_HIGH_VALUE,
        }
        os.environ.update(env_settings)

    def invoke_vred(self, test_configuration_name: str, scene_file: str) -> None:
        """
        Invoke VRED binary, passing it parameters to run headless, grant script access, load scene file,
        and execute code for the render process to complete
        :param: test_configuration_name: name of test configuration
        :param: scene_file: path to the scene file to render
        """
        os.environ[Constants.CODE_PASSING_ENV_VAR] = self.get_bootstrap_code(
            test_configuration_name
        )

        executable = self.get_vred_executable()
        if Constants.IS_WINDOWS:
            executable = f'"{executable}"'
            scene_file = f'"{scene_file}"'

        cmd = [
            executable,
            scene_file,
            Constants.DISABLE_PYTHON_SANDBOX_PARAM,
            Constants.FAST_START_PARAM,
            Constants.POST_PYTHON_PARAM,
            Constants.VRED_PYTHON_PRE_BOOTSTRAP_CODE,
        ]

        try:
            invocation = " ".join(cmd) if Constants.IS_WINDOWS else cmd
            result = subprocess.run(invocation, stderr=subprocess.STDOUT, check=True, text=True)
            logging.debug(result)
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {invocation}\n{e.output}\nReturn code: {e.returncode}")


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
    Processes command-line arguments to launch VRED to render based on a job bundle configuration and optional scene
    file override (to the scene file specified within the job bundle).
    Note: sample invocations:
        sys.argv[1]: Test configuration name (relative to "job_bundles" subdirectory)
        sys.argv[2]: Optional: scene file name (relative to "scene_files" subdirectory)
    """
    global COMMAND_LINE_USAGE

    logging.info(Constants.DEADLINE_CLOUD_FOR_VRED_RENDER_TEST_TITLE)
    logging.info("=" * (len(Constants.DEADLINE_CLOUD_FOR_VRED_RENDER_TEST_TITLE) - 1))

    if len(sys.argv) < 2:
        logging.error(COMMAND_LINE_USAGE)
        return

    test_config_name_arg = sys.argv[1]
    scene_filename_arg = sys.argv[2] if len(sys.argv) == 3 else None

    path_resolver = PathResolver()
    scene_file_path = (
        path_resolver.get_scene_file(scene_filename_arg) if scene_filename_arg else None
    )
    test_config_file_path = path_resolver.get_config_file(test_config_name_arg)

    if scene_file_path and not scene_file_path.exists():
        logging.error(f"Scene file '{scene_file_path.name}' does not exist")
        return
    if not test_config_file_path.exists():
        logging.error(f"Test config file '{test_config_file_path.name}' does not exist")
        return

    render_params = load_render_parameter_values.get_vred_render_parameters(
        test_config_name_arg, str(scene_file_path) if scene_file_path else None
    )
    generated_output_folder = Path(render_params[Constants.OUTPUT_DIRECTORY_FIELD])
    if not setup_output_directory(str(generated_output_folder)):
        logging.error(
            f"Error: output folder already exists or can't be accessed:\n  {generated_output_folder}"
        )
        return

    scene_file_basename = Path(render_params[Constants.SCENE_FILE_FIELD]).stem
    logging.info(f"Test configuration (job bundle): {test_config_name_arg}")
    logging.info(f"Scene file: {scene_file_basename}.vpb")

    vred_test_runner = VREDRenderTestRunner()
    vred_test_runner.setup_environment()
    vred_test_runner.invoke_vred(
        test_config_name_arg, str(Path(render_params[Constants.SCENE_FILE_FIELD]))
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
