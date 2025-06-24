# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
VRED Rendering (local) semi-automated test module.

Launches VRED, loads a scene file, initializes rendering configuration (via load_render_parameter_values.py and JSON
configuration) and initiates VRED_RenderScript_DeadlineCloud.py to launch actual rendering process.

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
import platform
import subprocess
import sys

from output_comparison import are_images_similar

logging.getLogger().setLevel(logging.INFO)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CODE_PASSING_ENV_VAR = "BOOTSTRAP_CODE"
DISABLE_PYTHON_SANDBOX_PARAM = "-insecure_python"
DISABLE_PYTHON_SANDBOX_ENV_VAR = "DISABLE_VRED_PYTHON_SANDBOX"
DISABLE_WEBINTERFACE_ENV_VAR = "VRED_DISABLE_WEBINTERFACE"
DISABLE_WEBINTERFACE_VALUE = "1"
ERROR_UNKNOWN_VRED_PATH = (
    "Cannot determine valid VRED binary to invoke from VREDCORE and VREDPRO environment "
    "variables."
)
EXPECTED_OUTPUT_DIRECTORY_NAME = "expected_output"
FAST_START_PARAM = "-fast_start"
FLEXLM_DIAGNOSTICS_ENV_VAR = "FLEXLM_DIAGNOSTICS"
FLEXLM_DIAGNOSTICS_HIGH_VALUE = "3"
HIDE_GUI_PARAM = "-hide_gui"
IMAGE_OUTPUT_FILENAME = "image-00000.png"
IMAGE_SIMILARITY_FACTOR = 0.9
IS_WINDOWS = platform.system().lower() == "windows"
LICENSE_RELEASE_TIME_ENV_VAR = "VRED_IDLE_LICENSE_TIME"
LICENSE_RELEASE_TIME_SECONDS_LIMIT = "60"
POST_PYTHON_PARAM = "-postpython"
SCENE_FILE_DIRECTORY_NAME = "scene_files"
TEST_CONFIGURATION_DIRECTORY_NAME = "configurations"
VRED_CORE_ENV_VAR = "VREDCORE"
VRED_PRO_ENV_VAR = "VREDPRO"

# Invoke code found in get_python_bootstrap_code() (indirectly via CODE_PASSING_ENV_VAR) without using import
# statements. Removes all spaces to prevent VRED from assuming non-intended arguments.
#
VRED_PYTHON_PRE_BOOTSTRAP_CODE = rf"""
load_module = getattr(__builtins__, '__import__');
os = load_module('os');
exec(os.environ.get('{CODE_PASSING_ENV_VAR}'));
""".replace(
    "\n", ""
).replace(
    " ", ""
)


def get_python_bootstrap_code(test_configuration_file: str) -> str:
    """
    Generate bootstrap code for VRED execution (via CODE_PASSING_ENV_VAR).
    :param: test_configuration_file: path to the test configuration file
    returns: generated bootstrap code with paths and imports configured
    #
    """
    current_module_path = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
    submitter_module_path = os.path.dirname(current_module_path)
    # Inject render parameters into render script, loading both of them at startup, enforce universal exit
    return (
        rf"""
import importlib;
import os;
import sys;
from vrController import terminateVred, vrLogError;
sys.path.extend([r'{current_module_path}','{submitter_module_path}']);
render_module_name='VRED_RenderScript_DeadlineCloud';
render_param_module_name='load_render_parameter_values';
render_module = importlib.util.find_spec(render_module_name) is not None and importlib.import_module(
render_module_name) or None;
render_param_module = importlib.util.find_spec(render_param_module_name) is not None and importlib.import_module(
render_param_module_name) or None;
render_module.deadline_cloud_render(
render_param_module.get_vred_render_parameters(r'{test_configuration_file}')) if render_module and 
render_param_module else vrLogError('failed to import module for render script and/or render parameters');
terminateVred();
""".replace(
            "\n", ""
        )
        .replace("\\", "/")
        .replace("\t", "")
    )


def get_vred_executable() -> str:
    """
    Determine VRED binary to use based on environment variable state and binary availability
    return: path to VRED binary
    raise: OSError: if a valid VRED binary cannot be determined.
    """
    try:
        vred_executable = os.environ[VRED_CORE_ENV_VAR]
        if not os.path.isfile(vred_executable):
            raise FileNotFoundError(f"VREDCORE binary not found at: {vred_executable}")
    except (KeyError, FileNotFoundError):
        try:
            vred_executable = os.environ[VRED_PRO_ENV_VAR]
            if not os.path.isfile(vred_executable):
                raise FileNotFoundError(f"VREDPRO binary not found at: {vred_executable}")
        except (KeyError, FileNotFoundError):
            raise OSError(ERROR_UNKNOWN_VRED_PATH)
    return vred_executable


def setup_vred_environment() -> None:
    """
    Disable VRED's web interface, release license on idle, pass bootstrapping code via environment variable
    """
    os.environ[DISABLE_WEBINTERFACE_ENV_VAR] = DISABLE_WEBINTERFACE_VALUE
    os.environ[LICENSE_RELEASE_TIME_ENV_VAR] = LICENSE_RELEASE_TIME_SECONDS_LIMIT
    os.environ[FLEXLM_DIAGNOSTICS_ENV_VAR] = FLEXLM_DIAGNOSTICS_HIGH_VALUE


def invoke_vred(vred_executable: str, scene_file: str, test_configuration_file: str) -> None:
    """
    Invoke VRED binary, passing it parameters to run headless, grant script access, load scene file,
    and execute code for the render process to complete
    :param: vred_executable: path to VRED binary
    :param: scene_file: path to scene file to render
    :param: test_configuration_file: path to test configuration file
    """
    os.environ[CODE_PASSING_ENV_VAR] = get_python_bootstrap_code(test_configuration_file)
    executable = f'"{vred_executable}"' if IS_WINDOWS else vred_executable
    scene_file_path = rf'"{scene_file}"' if IS_WINDOWS else rf"{scene_file}"
    command_and_arg_list: list[str] = [
        executable,
        scene_file_path,
        (
            DISABLE_PYTHON_SANDBOX_PARAM
            if os.environ.get(DISABLE_PYTHON_SANDBOX_ENV_VAR)
            else DISABLE_PYTHON_SANDBOX_PARAM
        ),
        FAST_START_PARAM,
        POST_PYTHON_PARAM,
        VRED_PYTHON_PRE_BOOTSTRAP_CODE,
    ]
    try:
        invocation = " ".join(command_and_arg_list) if IS_WINDOWS else command_and_arg_list
        output = subprocess.run(invocation, stderr=subprocess.STDOUT, check=True, text=True)
        print(output)
    except subprocess.CalledProcessError as error:
        print(
            f"Command: [{invocation}] failed: \n{error.output}\n with return code {error.returncode}"
        )


def main_routine():
    """
    Processes command-line arguments to launch VRED with specified scene and configuration files.
    Note: expects two command-line arguments: python script.py my_scene.vpb test_config.json
        sys.argv[1]: Scene file name (relative to "scene_files" subdirectory)
        sys.argv[2]: Test configuration file name (relative to "configurations" subdirectory)
    TODO: add more refactoring
    """
    import load_render_parameter_values

    current_module_path = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
    scene_file_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    test_config_file_arg = sys.argv[2] if len(sys.argv) > 2 else ""
    scene_file = os.path.realpath(
        os.path.join(current_module_path, SCENE_FILE_DIRECTORY_NAME, scene_file_arg)
    )
    test_config = os.path.realpath(
        os.path.join(current_module_path, TEST_CONFIGURATION_DIRECTORY_NAME, test_config_file_arg)
    )
    if not scene_file_arg:
        logging.error("No scene file argument provided")
        return
    elif not test_config_file_arg:
        logging.error("No test configuration file argument provided")
        return
    elif not os.path.isfile(scene_file):
        logging.error(f"Scene file '{scene_file_arg}' does not exist")
        return
    elif not os.path.isfile(test_config):
        logging.error(f"Test configuration file '{test_config_file_arg}' does not exist")
        return

    setup_vred_environment()
    render_parameters = load_render_parameter_values.get_vred_render_parameters(
        test_config_file_arg
    )
    test_config_basename = os.path.splitext(os.path.basename(test_config_file_arg))[0]
    scene_file_basename = os.path.splitext(os.path.basename(render_parameters["SceneFile"]))[0]
    invoke_vred(get_vred_executable(), scene_file, test_config_file_arg)
    expected_output = os.path.realpath(
        os.path.join(
            current_module_path,
            EXPECTED_OUTPUT_DIRECTORY_NAME,
            f"{scene_file_basename}-{test_config_basename}",
            IMAGE_OUTPUT_FILENAME,
        )
    )
    generated_output = os.path.realpath(
        os.path.join(render_parameters["OutputDir"], IMAGE_OUTPUT_FILENAME)
    )
    result = are_images_similar(expected_output, generated_output, IMAGE_SIMILARITY_FACTOR)
    logging.info(f"Image comparison result: {result}")


if __name__ == "__main__":
    main_routine()
