# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import json
import dataclasses
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock
import sys


def verify_sticky_settings_file(
    sticky_settings_file: Path, parameter_overrides: Dict[str, Any]
) -> None:
    """
    Verify the contents of the sticky settings file match expected values.

    :param sticky_settings_file: Path to the sticky settings JSON file
    :param parameter_overrides: Dictionary of parameters that were overridden in the test
    :raise AssertionError: If sticky settings file contents don't match expectations
    """
    # Mock vred_logger before importing data_classes to avoid vrController import issues
    sys.modules["deadline.vred_submitter.vred_logger"] = MagicMock()
    from deadline.vred_submitter.data_classes import RenderSubmitterUISettings

    # Load the sticky settings file
    with open(sticky_settings_file, "r", encoding="utf8") as f:
        sticky_data = json.load(f)

    assert isinstance(
        sticky_data, dict
    ), f"Sticky settings should be a dictionary, got {type(sticky_data)}"

    # Get all sticky-enabled fields from the data class
    sticky_fields = {
        field.name: field
        for field in dataclasses.fields(RenderSubmitterUISettings)
        if field.metadata.get("sticky")
    }

    # Verify that test parameters that should be sticky are present in the file
    sticky_test_params = {k: v for k, v in parameter_overrides.items() if k in sticky_fields}

    for param_name, expected_value in sticky_test_params.items():
        assert (
            param_name in sticky_data
        ), f"Sticky parameter '{param_name}' should be saved to sticky settings file"
        actual_value = sticky_data[param_name]

        # Handle type conversions (JSON stores everything as basic types)
        if isinstance(expected_value, str) and expected_value.lower() in ["true", "false"]:
            # Convert string booleans to actual booleans for comparison
            expected_bool = expected_value.lower() == "true"
            assert (
                actual_value == expected_bool
            ), f"Sticky parameter '{param_name}': expected {expected_bool}, got {actual_value}"
        else:
            assert (
                actual_value == expected_value
            ), f"Sticky parameter '{param_name}': expected {expected_value}, got {actual_value}"

    # Verify that only sticky-enabled fields are in the file (no non-sticky fields leaked in)
    for param_name in sticky_data.keys():
        assert (
            param_name in sticky_fields
        ), f"Non-sticky parameter '{param_name}' should not be saved to sticky settings file"
