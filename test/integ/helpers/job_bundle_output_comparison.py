# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Job Bundle output comparison utilities for VRED submitter tests.
Provides functions to compare actual job bundle outputs with expected job bundle files.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_expected_parameters(
    base_template_path: Path, overrides: dict[str, Any]
) -> dict[str, Any]:
    """
    Generate expected parameter values by applying overrides to base template.

    Args:
        base_template_path: Path to _base_parameter_values.yaml
        overrides: Dict of parameter names to values (from test settings)

    Returns:
        Complete parameter values dict ready for comparison

    Example:
        base_template has: {"parameterValues": [{"name": "DLSSQuality", "value": "Off"}, ...]}
        overrides has: {"DLSSQuality": "Performance"}
        result: {"parameterValues": [{"name": "DLSSQuality", "value": "Performance"}, ...]}
    """
    with open(base_template_path, encoding="utf-8") as f:
        base = yaml.safe_load(f)

    result: dict[str, Any] = {"parameterValues": []}

    # Loop through each parameter in base template
    for param in base.get("parameterValues", []):
        # Start with a copy of the base parameter
        param_copy = param.copy()  # e.g., {"name": "DLSSQuality", "value": "Off"}
        param_name = param["name"]  # e.g., "DLSSQuality"

        # If test provides an override for this parameter, use it
        if param_name in overrides:
            param_copy["value"] = overrides[param_name]  # Replace "Off" with "Performance"

        # Add the (possibly overridden) parameter to result
        result["parameterValues"].append(param_copy)

    return result


def normalize_file_path(file_path: str, context: dict[str, Any] | None = None) -> str:
    """
    Normalize file paths for comparison by extracting just the filename.
    For asset referencing tests, preserve specific known valid paths.

    Args:
        file_path: The file path to normalize
        context: Test context containing test_name and other info

    Returns:
        Normalized path string
    """
    if context is None:
        context = {}

    test_name = context.get("test_name", "")

    # Special handling for asset referencing test - preserve known valid paths
    if "bundle_comparison" in test_name:
        known_valid_paths = [
            "C:\\WorkArea\\Only\\LightweightWithoutSpaces.vpb",
            "C:\\WorkArea\\test.wire",
        ]
        if file_path in known_valid_paths:
            return file_path

    # For all other cases, extract just the filename
    return Path(file_path).name


def normalize_parameter_values(
    param_values: dict[str, Any], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Normalize parameter values for comparison by handling environment-specific values.

    Args:
        param_values: Parameter values dictionary to normalize
        context: Test context containing test_name and other info

    Returns:
        Normalized parameter values dictionary
    """
    if context is None:
        context = {}

    normalized = param_values.copy()

    for param in normalized.get("parameterValues", []):
        param_name = param.get("name", "")
        param_value = param.get("value", "")

        # Normalize file paths
        if param_name in ["SceneFile"] and isinstance(param_value, str):
            param["value"] = normalize_file_path(param_value, context)

        # Normalize JobScriptDir to relative path
        elif param_name == "JobScriptDir" and isinstance(param_value, str):
            param["value"] = "scripts"

    return normalized


def normalize_asset_references(
    asset_refs: dict[str, Any], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Normalize asset references for comparison by handling environment-specific paths.

    Args:
        asset_refs: Asset references dictionary to normalize
        context: Test context containing test_name and other info

    Returns:
        Normalized asset references dictionary
    """
    if context is None:
        context = {}

    normalized = asset_refs.copy()

    # Normalize input filenames
    if "assetReferences" in normalized and "inputs" in normalized["assetReferences"]:
        filenames = normalized["assetReferences"]["inputs"].get("filenames", [])
        normalized_filenames = []

        for filename in filenames:
            if isinstance(filename, str):
                normalized_filenames.append(normalize_file_path(filename, context))
            else:
                normalized_filenames.append(filename)

        # Sort for consistent comparison
        normalized["assetReferences"]["inputs"]["filenames"] = sorted(normalized_filenames)

    return normalized


def _load_parameter_files(
    actual_dir: Path, expected_dir: Path, overrides: dict[str, Any] | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load and return parameter values from actual and expected directories."""
    actual_file = actual_dir / "parameter_values.yaml"

    if not actual_file.exists():
        raise FileNotFoundError(f"Actual parameter values file not found: {actual_file}")

    with open(actual_file, encoding="utf-8") as f:
        actual_params = yaml.safe_load(f)

    # Priority 1: Use expected directory file if it exists
    expected_file = expected_dir / "parameter_values.yaml"
    if expected_file.exists():
        with open(expected_file, encoding="utf-8") as f:
            expected_params = yaml.safe_load(f)
    # Priority 2: Generate from base template if overrides provided
    elif overrides is not None:
        base_template = expected_dir.parent / "_base_parameter_values.yaml"
        if base_template.exists():
            expected_params = generate_expected_parameters(base_template, overrides)
        else:
            raise FileNotFoundError(
                f"Neither expected parameter file nor base template found for {expected_dir}"
            )
    else:
        raise FileNotFoundError(f"Expected parameter values file not found: {expected_file}")

    return actual_params, expected_params


def _compare_parameter_counts(
    normalized_actual: dict[str, Any], normalized_expected: dict[str, Any]
) -> None:
    """Compare parameter counts between actual and expected."""
    actual_count = len(normalized_actual.get("parameterValues", []))
    expected_count = len(normalized_expected.get("parameterValues", []))

    assert (
        actual_count == expected_count
    ), f"Parameter count mismatch: expected {expected_count}, got {actual_count}"


def _compare_parameter_values(
    normalized_actual: dict[str, Any], normalized_expected: dict[str, Any]
) -> None:
    """Compare individual parameter values."""
    actual_lookup = {
        param["name"]: param["value"] for param in normalized_actual.get("parameterValues", [])
    }
    expected_lookup = {
        param["name"]: param["value"] for param in normalized_expected.get("parameterValues", [])
    }

    for param_name, expected_value in expected_lookup.items():
        actual_value = actual_lookup.get(param_name)
        assert actual_value is not None, f"Parameter '{param_name}' missing in actual output"
        assert actual_value == expected_value, (
            f"Parameter '{param_name}' mismatch:\n"
            f"  Expected: {expected_value}\n"
            f"  Actual: {actual_value}"
        )


def assert_parameter_values_match(
    actual_dir: Path, expected_dir: Path, context: dict[str, Any] | None = None
) -> None:
    """
    Compare actual parameter values with expected parameter values.

    Args:
        actual_dir: Directory containing actual parameter_values.yaml
        expected_dir: Directory containing expected parameter_values.yaml
        context: Test context containing test_name, parameter_overrides, etc.

    Raises:
        AssertionError: If parameter values don't match expected values
        FileNotFoundError: If required files are missing
    """
    if context is None:
        context = {}

    # Extract overrides from context if provided
    overrides = context.get("parameter_overrides")

    actual_params, expected_params = _load_parameter_files(actual_dir, expected_dir, overrides)

    # Normalize both for comparison
    normalized_actual = normalize_parameter_values(actual_params, context)
    normalized_expected = normalize_parameter_values(expected_params, context)

    # Compare parameter counts and values
    _compare_parameter_counts(normalized_actual, normalized_expected)
    _compare_parameter_values(normalized_actual, normalized_expected)


def assert_asset_references_match(
    actual_dir: Path, expected_dir: Path, context: dict[str, Any] | None = None
) -> None:
    """
    Compare actual asset references with expected asset references values.

    Args:
        actual_dir: Directory containing actual asset_references.yaml
        expected_dir: Directory containing expected asset_references.yaml
        context: Test context containing test_name and other info

    Raises:
        AssertionError: If asset references don't match expected values
        FileNotFoundError: If required files are missing
    """
    if context is None:
        context = {}

    actual_file = actual_dir / "asset_references.yaml"

    if not actual_file.exists():
        raise FileNotFoundError(f"Actual asset references file not found: {actual_file}")

    with open(actual_file, encoding="utf-8") as f:
        actual_assets = yaml.safe_load(f)

    # Priority 1: Use expected directory file if it exists
    expected_file = expected_dir / "asset_references.yaml"
    if expected_file.exists():
        with open(expected_file, encoding="utf-8") as f:
            expected_assets = yaml.safe_load(f)
    # Priority 2: Try base asset template if scene_file provided
    elif scene_file := context.get("scene_file"):
        scene_basename = Path(scene_file).stem
        base_asset_template = expected_dir.parent / f"_base_asset_{scene_basename}.yaml"

        if base_asset_template.exists():
            with open(base_asset_template, encoding="utf-8") as f:
                expected_assets = yaml.safe_load(f)
        else:
            raise FileNotFoundError(
                f"Neither expected asset file nor base asset template found for {expected_dir}"
            )
    else:
        raise FileNotFoundError(f"Expected asset references file not found: {expected_file}")

    # Normalize both for comparison
    normalized_actual = normalize_asset_references(actual_assets, context)
    normalized_expected = normalize_asset_references(expected_assets, context)

    # Compare the normalized structures
    assert normalized_actual == normalized_expected, (
        f"Asset references mismatch:\n"
        f"  Expected: {normalized_expected}\n"
        f"  Actual: {normalized_actual}"
    )

    logger.info("✓ Asset references match expected output")


def assert_job_bundle_matches(
    actual_dir: Path, expected_dir: Path, context: dict[str, Any] | None = None
) -> None:
    """
    Compare the actual job bundle with expected job bundle output.

    Args:
        actual_dir: Directory containing actual job bundle output
        expected_dir: Directory containing expected job bundle output
        context: Test context containing test_name and other info
    """
    if context is None:
        context = {}

    test_name = context.get("test_name", "unknown")
    logger.info("Comparing job bundle: %s vs %s", actual_dir.name, expected_dir.name)

    # Compare parameter values
    assert_parameter_values_match(actual_dir, expected_dir, context)

    # Compare asset references
    assert_asset_references_match(actual_dir, expected_dir, context)

    # Template comparison is optional (only if expected template exists)
    expected_template = expected_dir / "template.yaml"
    if expected_template.exists():
        actual_template = actual_dir / "template.yaml"
        assert actual_template.exists(), f"Actual template file missing: {actual_template}"

        # For now, just verify it's valid YAML
        with open(actual_template, encoding="utf-8") as f:
            yaml.safe_load(f)  # Will raise exception if invalid

        logger.info("✓ Template file is valid YAML")

    logger.info("✅ Job bundle matches expected output: %s", test_name)
