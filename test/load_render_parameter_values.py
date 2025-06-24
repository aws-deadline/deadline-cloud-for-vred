# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import json
import os

from typing import Any, Dict

OUTPUT_DIRECTORY_NAME = "output"
TEST_CONFIGURATION_DIRECTORY_NAME = "configurations"
UNKNOWN_SCENE_FILENAME = "untitled"


def str_to_bool(s: str) -> bool:
    return s.lower() == "true"


def get_vred_render_parameters(test_configuration_filename: str) -> Dict[str, Any]:
    """
    Provides adjusted JSON render configuration (based on choice of JSON test configuration file and active scene file)
    :param test_configuration_filename: filename (w/o path) of the JSON-based render configuration to apply
    :return: a dictionary containing appropriately-typed values (non-inferred) for use in VRED API calls.
    """
    path_to_configuration_data = os.path.join(
        os.path.realpath(os.path.dirname(os.path.abspath(__file__))),
        TEST_CONFIGURATION_DIRECTORY_NAME,
        test_configuration_filename,
    )
    configuration_data = {}
    try:
        with open(path_to_configuration_data, "r") as file_handle:
            configuration_data = json.load(file_handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    configuration_data["OutputDir"] = os.path.join(
        os.path.realpath(os.path.dirname(os.path.abspath(__file__))), OUTPUT_DIRECTORY_NAME
    )
    try:
        # Assume scene file is already loaded (if accessing in VRED)
        from builtins import vrFileIOService  # type: ignore

        configuration_data["SceneFile"] = vrFileIOService.getFileName() or UNKNOWN_SCENE_FILENAME
    except ImportError:
        configuration_data["SceneFile"] = (
            configuration_data.get("SceneFile") or UNKNOWN_SCENE_FILENAME
        )

    return configuration_data
