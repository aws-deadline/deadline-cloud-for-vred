# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from deadline.client.job_bundle.parameters import read_job_bundle_parameters
from test.common.constants import Constants


def str_to_bool(s: str) -> bool:
    return s.lower() == "true"


def convert_from_openjd_value(value, type_info):
    """
    Convert OpenJD parameter value to the appropriate Python type.
    param: value: the value to convert
    param: type_info: type information ('INT', 'STRING', etc.)
    return: converted value (as int, bool, or str)
    """
    if type_info == "INT":
        return int(value)
    elif type_info == "STRING" and value in ("true", "false"):
        return str_to_bool(value)
    else:
        return str(value)


def get_vred_render_parameters_from_bundle(
    base_dir: Path,
    bundle_path_str: str,
    scene_file_override: Optional[str] = None,
    output_dir_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load render parameters from exported job bundle.
    param: base_dir: absolute path to the directory where tests are located (e.g., test/worker, test/e2e)
    param: bundle_path_str: absolute path to the job bundle directory (that includes YAML files)
    param: (Optional) scene_file_override: absolute path of the scene file to override
    param: (Optional) output_dir_override: absolute path to the directory where the output will be generated
    return: a dictionary containing values with appropriate types for use in VRED API calls.
    Note: SceneFile and OutputDir should be set by caller as needed.
    """
    bundle_dir = Path(bundle_path_str)

    try:
        job_bundle_parameters = read_job_bundle_parameters(str(bundle_dir))
        render_parameters = {
            item["name"]: convert_from_openjd_value(item["value"], item.get("type"))
            for item in job_bundle_parameters
            if "value" in item
        }
    except (FileNotFoundError, KeyError, PermissionError) as e:
        # If the file is not found or there's an issue reading it, return an empty dictionary
        error_msg = f"Failed to read job bundle parameters from {bundle_dir}"
        raise type(e)(error_msg) from e

    # Find the scene file path
    if scene_file_override:
        scene_file_path_str = scene_file_override
    else:
        try:
            # Try to get current scene file from VRED if available
            from builtins import vrFileIOService  # type: ignore

            scene_file = vrFileIOService.getFileName() or Constants.UNKNOWN_SCENE_FILENAME
        except ImportError:
            scene_file = render_parameters.get(
                Constants.SCENE_FILE_FIELD, Constants.UNKNOWN_SCENE_FILENAME
            )
        # Resolve scene file to absolute path
        scene_file_path_str = str(
            base_dir / Constants.SCENE_FILE_DIRECTORY_NAME / Path(scene_file).name
        )

    # Set the "SceneFile" parameter
    render_parameters[Constants.SCENE_FILE_FIELD] = scene_file_path_str

    # Get the absolute path of the output directory
    if output_dir_override:
        output_dir_path_str = output_dir_override
    else:
        scene_basename = Path(render_parameters[Constants.SCENE_FILE_FIELD]).stem
        output_subdir = f"{scene_basename}-{bundle_dir.name}"
        output_dir_path_str = str(base_dir / Constants.OUTPUT_DIRECTORY_NAME / output_subdir)

    # Set the "OutputDir" parameter
    render_parameters[Constants.OUTPUT_DIRECTORY_FIELD] = output_dir_path_str

    return render_parameters
