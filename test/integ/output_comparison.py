# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import logging
import yaml

from pathlib import Path
from typing import Any

from test.integ.constants import Constants

logging.basicConfig(format="%(message)s", level=logging.INFO)


def extract_parameter_value(parameter_values: dict, param_name: str) -> Any:
    """
    Extract parameter value by name from parameterValues structure.

    Args:
        parameter_values: Dictionary containing parameterValues list
        param_name: Name of parameter to extract

    Returns:
        Any: Parameter value if found, None otherwise
    """
    return next(
        (
            parameter[Constants.VALUE_FIELD]
            for parameter in parameter_values[Constants.PARAMETER_VALUES_FIELD]
            if parameter[Constants.NAME_FIELD] == param_name
        ),
        None,
    )


def assert_parameter_values_similar(
    job_history_dir: Path, expected_parameter_values: dict[str, list]
) -> None:
    """
    Verify that the parameter values in the job bundle match their expected values.
    :param job_history_dir: directory containing job history files
    :param expected_parameter_values: expected parameter values to compare
    :raise AssertionError: If parameter values don't match expected values
    """
    with open(job_history_dir / Constants.PARAMETER_VALUES_FILENAME) as file_handle:
        actual = yaml.safe_load(file_handle)[Constants.PARAMETER_VALUES_FIELD]
        expected = expected_parameter_values[Constants.PARAMETER_VALUES_FIELD]
        assert len(actual) == len(expected)
        for param in expected:
            name, value = param[Constants.NAME_FIELD], param[Constants.VALUE_FIELD]
            assert value == extract_parameter_value(
                {Constants.PARAMETER_VALUES_FIELD: actual}, name
            )


def assert_asset_references_similar(
    job_history_dir: Path, expected_asset_references: dict[str, dict[str, Any]]
) -> None:
    """
    Verify that the asset reference values in the job bundle match their expected values.
    :param: job_history_dir: directory containing job history files
    :param: expected_asset_references: expected asset references to compare against
    :raise AssertionError: If asset references don't match expected values
    """
    with open(job_history_dir / Constants.ASSET_REFERENCES_FILENAME) as file_handle:
        actual = yaml.safe_load(file_handle)
        actual["assetReferences"]["inputs"]["filenames"] = sorted(
            actual["assetReferences"]["inputs"]["filenames"]
        )
        expected_asset_references["assetReferences"]["inputs"]["filenames"] = sorted(
            expected_asset_references["assetReferences"]["inputs"]["filenames"]
        )
        actual["assetReferences"]["inputs"]["directories"] = sorted(
            actual["assetReferences"]["inputs"]["directories"]
        )
        expected_asset_references["assetReferences"]["inputs"]["directories"] = sorted(
            expected_asset_references["assetReferences"]["inputs"]["directories"]
        )
        dirs = expected_asset_references["assetReferences"]["outputs"]["directories"]
        expected_asset_references["assetReferences"]["outputs"]["directories"] = [
            d.replace("\\", "/") for d in dirs
        ]
        assert actual == expected_asset_references
