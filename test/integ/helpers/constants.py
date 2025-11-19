# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Shared constants for all test suites"""

import platform
from typing import Final


class ConstantsMeta(type):
    def __setattr__(cls, name, value):
        raise AttributeError(f"Cannot modify constant '{name}'")

    def __delattr__(cls, name):
        raise AttributeError(f"Cannot delete constant '{name}'")


class Constants(metaclass=ConstantsMeta):
    ASSET_REFERENCES_FILENAME: Final[str] = "asset_references.yaml"
    CODE_PASSING_ENV_VAR: Final[str] = "BOOTSTRAP_CODE"
    DISABLE_PYTHON_SANDBOX_PARAM: Final[str] = "-insecure_python"
    DISABLE_WEBINTERFACE_ENV_VAR: Final[str] = "VRED_DISABLE_WEBINTERFACE"
    DISABLE_WEBINTERFACE_VALUE: Final[str] = "1"
    FAST_START_PARAM: Final[str] = "-fast_start"
    FLEXLM_DIAGNOSTICS_ENV_VAR: Final[str] = "FLEXLM_DIAGNOSTICS"
    FLEXLM_DIAGNOSTICS_HIGH_VALUE: Final[str] = "3"
    IS_WINDOWS: Final[bool] = platform.system().lower() == "windows"
    LICENSE_RELEASE_TIME_ENV_VAR: Final[str] = "VRED_IDLE_LICENSE_TIME"
    LICENSE_RELEASE_TIME_SECONDS_LIMIT: Final[str] = "60"
    OUTPUT_DIRECTORY_FIELD: Final[str] = "OutputDir"
    OUTPUT_DIRECTORY_NAME: Final[str] = "output"
    PARAMETER_VALUES_FILENAME: Final[str] = "parameter_values.yaml"
    POST_PYTHON_PARAM: Final[str] = "-postpython"
    SCENE_FILE_DIRECTORY_NAME: Final[str] = "scene_files"
    SCENE_FILE_FIELD: Final[str] = "SceneFile"
    TEMPLATE_FILENAME: Final[str] = "template.yaml"
    UNKNOWN_SCENE_FILENAME: Final[str] = "untitled"

    VRED_CORE_ENV_VAR: Final[str] = "VREDCORE"
    VRED_PRO_ENV_VAR: Final[str] = "VREDPRO"
    VRED_SUBMITTER_SOURCE_PATH: Final[str] = "src/deadline/vred_submitter"

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
        raise TypeError("Constants class cannot be instantiated")
