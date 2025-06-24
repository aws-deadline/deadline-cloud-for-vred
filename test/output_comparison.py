# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import yaml
import PIL.Image
import numpy as np

from pathlib import Path
from test_const import ASSET_REFERENCES, PARAMETER_VALUES
from typing import Any


def are_images_similar_by_folder(
    expected_image_directory: Path, actual_image_directory: Path, tolerance: float
) -> bool:
    """Helper function to compare render output"""
    for image in expected_image_directory.iterdir():
        if not image.is_file():
            continue

        actual = np.asarray(PIL.Image.open(actual_image_directory / image.name))
        expected = np.asarray(PIL.Image.open(image))

        if not np.allclose(actual, expected, atol=tolerance):
            return False
    return True


def are_images_similar(
    expected_image_file_path: str, actual_image_file_path: str, tolerance: float
) -> bool:
    """Helper function to compare render output"""
    try:
        actual = np.asarray(PIL.Image.open(actual_image_file_path))
        expected = np.asarray(PIL.Image.open(expected_image_file_path))
        return np.allclose(actual, expected, atol=tolerance)
    except (FileNotFoundError, PIL.UnidentifiedImageError, ValueError):
        return False


def extract_parameter_value(expected_parameter_values, param_name):
    """Extracts a parameter value"""
    for param in expected_parameter_values["parameterValues"]:
        if param["name"] == param_name:
            return param["value"]
    return None


def are_parameter_values_similar(job_history_dir: Path, expected_parameter_values: dict[str, list]):
    """Asserts that parameter values in the job bundle are as expected"""
    with open(job_history_dir / PARAMETER_VALUES) as actual:
        actual_parameter_values = yaml.safe_load(actual)

        assert len(actual_parameter_values["parameterValues"]) == len(
            expected_parameter_values["parameterValues"]
        )

        for parameter_value in expected_parameter_values["parameterValues"]:
            name = parameter_value["name"]
            value = parameter_value["value"]

            if not isinstance(value, int):
                value = value.replace("\\", "/")

            assert value == extract_parameter_value(actual_parameter_values, name)


def are_asset_references_similar(
    job_history_dir: Path, expected_asset_references: dict[str, dict[str, Any]]
):
    """Helper function that asserts that asset reference values in the job bundle are what's expected."""
    with open(job_history_dir / ASSET_REFERENCES) as actual:
        actual_asset_reference = yaml.safe_load(actual)

        assert len(actual_asset_reference["assetReferences"]["inputs"]["filenames"]) == len(
            expected_asset_references["assetReferences"]["inputs"]["filenames"]
        )

        actual_asset_reference["assetReferences"]["inputs"]["filenames"] = set(
            actual_asset_reference["assetReferences"]["inputs"]["filenames"]
        )

        directories = expected_asset_references["assetReferences"]["outputs"]["directories"]
        expected_asset_references["assetReferences"]["outputs"]["directories"] = [
            d.replace("\\", "/") for d in directories
        ]

        assert actual_asset_reference == expected_asset_references
