# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import logging
import numpy as np
import PIL.Image
import yaml

from pathlib import Path
from typing import Any

try:
    from .constants import Constants
except ImportError:
    from constants import Constants  # type: ignore[no-redef]


def are_images_similar_by_folder(expected_dir: Path, actual_dir: Path, tolerance: float) -> bool:
    """Compare all images in two directories for similarity.
    :param: expected_dir: directory containing expected images
    :param: actual_dir: directory containing actual images
    :param: tolerance: absolute tolerance for pixel value differences
    :return: True if all images are similar within tolerance
    """
    expected_dir = Path(expected_dir)
    actual_dir = Path(actual_dir)

    if not expected_dir.exists():
        logging.error(f"Expected directory does not exist: {expected_dir}")
        return False
    if not actual_dir.exists():
        logging.error(f"Actual directory does not exist: {actual_dir}")
        return False

    for image in expected_dir.iterdir():
        if image.is_file():
            actual_image = actual_dir / image.name
            if not actual_image.exists():
                logging.error(f"Missing actual image: {actual_image}")
                return False
            if not are_images_similar(str(image), str(actual_image), tolerance):
                logging.error(f"Image mismatch: {image.name}")
                return False
    return True


def are_images_similar(
    expected_image_file_path: str, actual_image_file_path: str, tolerance: float
) -> bool:
    """Compare two images for similarity.
    :param: expected_image_file_path: file containing expected image
    :param: actual_image_file_path: file containing actual image
    :param: tolerance: absolute tolerance for pixel value differences
    :return: True if images are similar within tolerance
    """
    try:
        actual = np.asarray(PIL.Image.open(actual_image_file_path))
        expected = np.asarray(PIL.Image.open(expected_image_file_path))

        if actual.shape != expected.shape:
            logging.error(f"Image shape mismatch: expected {expected.shape}, actual {actual.shape}")
            return False

        result = np.allclose(actual, expected, atol=tolerance)
        if not result:
            max_diff = np.max(np.abs(actual.astype(float) - expected.astype(float)))
            logging.error(f"Images differ beyond tolerance {tolerance}, max difference: {max_diff}")
        return result
    except (FileNotFoundError, PIL.UnidentifiedImageError, ValueError) as e:
        logging.error(f"Error comparing images: {e}")
        return False


def extract_parameter_value(parameter_values: dict, param_name: str) -> Any:
    """
    Extract parameter value by name.
    :param: parameter_values: dictionary containing parameterValues list
    :param: param_name: name of parameter to extract
    :return: parameter value if found; None otherwise
    """
    return next(
        (p["value"] for p in parameter_values["parameterValues"] if p["name"] == param_name), None
    )


def are_parameter_values_similar(
    job_history_dir: Path, expected_parameter_values: dict[str, list]
) -> None:
    """
    Verify that the parameter values in the job bundle match their expected values.
    :param job_history_dir: directory containing job history files
    :param expected_parameter_values: expected parameter values to compare against
    """
    with open(job_history_dir / Constants.PARAMETER_VALUES) as f:
        actual = yaml.safe_load(f)["parameterValues"]
        expected = expected_parameter_values["parameterValues"]
        assert len(actual) == len(expected)
        for param in expected:
            name, value = param["name"], param["value"]
            if not isinstance(value, int):
                value = value.replace("\\", "/")
            assert value == extract_parameter_value({"parameterValues": actual}, name)


def are_asset_references_similar(
    job_history_dir: Path, expected_asset_references: dict[str, dict[str, Any]]
) -> None:
    """
    Verify that the asset reference values in the job bundle match their expected values.
    :param: job_history_dir: directory containing job history files
    :param: expected_asset_references: expected asset references to compare against
    """
    with open(job_history_dir / Constants.ASSET_REFERENCES) as f:
        actual = yaml.safe_load(f)
        actual_filenames = set(actual["assetReferences"]["inputs"]["filenames"])
        expected_filenames = expected_asset_references["assetReferences"]["inputs"]["filenames"]
        assert len(actual_filenames) == len(expected_filenames)
        # Normalize paths in expected directories
        dirs = expected_asset_references["assetReferences"]["outputs"]["directories"]
        expected_asset_references["assetReferences"]["outputs"]["directories"] = [
            d.replace("\\", "/") for d in dirs
        ]
        actual["assetReferences"]["inputs"]["filenames"] = actual_filenames
        assert actual == expected_asset_references
