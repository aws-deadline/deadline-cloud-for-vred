# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Provides a Constants class that focuses on the test suite component"""

import platform

from pathlib import Path
from typing import Final


class ConstantsMeta(type):
    """Metaclass to prevent modification of class attributes."""

    def __setattr__(cls, name, value):
        """Prevent modification of class attributes."""
        raise AttributeError(f"Cannot modify constant '{name}'")

    def __delattr__(cls, name):
        """Prevent deletion of class attributes."""
        raise AttributeError(f"Cannot delete constant '{name}'")


class Constants(metaclass=ConstantsMeta):
    """Constants class for test suite component"""

    ASSET_REFERENCES_FILENAME: Final[str] = "asset_references.yaml"
    CODE_PASSING_ENV_VAR: Final[str] = "BOOTSTRAP_CODE"
    DEADLINE_CLOUD_FOR_VRED_SUBMITTER_UI_TEST_TITLE: Final[str] = (
        "\nDeadline Cloud for VRED (Submitter UI Test)"
    )
    DEADLINE_HOME: Final[str] = str(Path.home() / ".deadline")
    DISABLE_PYTHON_SANDBOX_PARAM: Final[str] = "-insecure_python"
    DISABLE_PYTHON_SANDBOX_ENV_VAR: Final[str] = "DISABLE_VRED_PYTHON_SANDBOX"
    DISABLE_WEBINTERFACE_ENV_VAR: Final[str] = "VRED_DISABLE_WEBINTERFACE"
    DISABLE_WEBINTERFACE_VALUE: Final[str] = "1"
    END_FRAME_FIELD: Final[str] = "EndFrame"
    ERROR_UNKNOWN_VRED_PATH: Final[str] = (
        "Cannot determine a valid VRED binary to invoke from VREDCORE and VREDPRO environment "
        "variables."
    )
    EXPECTED_OUTPUT_DIRECTORY_NAME: Final[str] = "expected_output"
    FAST_START_PARAM: Final[str] = "-fast_start"
    FLEXLM_DIAGNOSTICS_ENV_VAR: Final[str] = "FLEXLM_DIAGNOSTICS"
    FLEXLM_DIAGNOSTICS_HIGH_VALUE: Final[str] = "3"
    HIDE_GUI_PARAM: Final[str] = "-hide_gui"
    IMAGE_SIMILARITY_FACTOR: Final[float] = 10.0
    IS_WINDOWS: Final[bool] = platform.system().lower() == "windows"
    JOB_BUNDLES_DIRECTORY_NAME: Final[str] = "job_bundles"
    JOB_BUNDLE_SCRIPTS_FOLDER_PATH: Final[str] = str(Path(DEADLINE_HOME) / "scripts")
    LICENSE_RELEASE_TIME_ENV_VAR: Final[str] = "VRED_IDLE_LICENSE_TIME"
    LICENSE_RELEASE_TIME_SECONDS_LIMIT: Final[str] = "60"
    NAME_FIELD: Final[str] = "name"
    NUM_X_TILES_FIELD: Final[str] = "NumXTiles"
    NUM_Y_TILES_FIELD: Final[str] = "NumYTiles"
    OUTPUT_DIRECTORY_NAME: Final[str] = "output"
    OUTPUT_DIRECTORY_FIELD: Final[str] = "OutputDir"
    PARAMETER_VALUES_FIELD: Final[str] = "parameterValues"
    PARAMETER_VALUES_FILENAME: Final[str] = "parameter_values.yaml"
    POST_PYTHON_PARAM: Final[str] = "-postpython"
    SCENE_FILE_DIRECTORY_NAME: Final[str] = "scene_files"
    SCENE_FILE_FIELD: Final[str] = "SceneFile"
    START_FRAME_FIELD: Final[str] = "StartFrame"
    TEMPLATE_FILENAME: Final[str] = "template.yaml"
    TEST_SCENE_FOLDER: Final[str] = "scene"
    UNKNOWN_SCENE_FILENAME: Final[str] = "untitled"
    VALUE_FIELD: Final[str] = "value"
    VRED_CORE_ENV_VAR: Final[str] = "VREDCORE"
    VRED_PRO_ENV_VAR: Final[str] = "VREDPRO"
    VRED_SUBMITTER_SOURCE_PATH: Final[str] = "src/deadline/vred_submitter"

    # Invoke code found in get_python_bootstrap_code() (indirectly via CODE_PASSING_ENV_VAR) without using import
    # statements. Removes all spaces to prevent VRED from assuming non-intended arguments.
    #
    VRED_PYTHON_PRE_BOOTSTRAP_CODE: Final[str] = (
        rf"""
    load_module = getattr(__builtins__, '__import__');
    os = load_module('os');
    exec(os.environ.get('{CODE_PASSING_ENV_VAR}'));
    """.replace(
            "\n", ""
        ).replace(
            " ", ""
        )
    )

    def __new__(cls):
        """Prevent instantiation of this class."""
        raise TypeError("Constants class cannot be instantiated")
