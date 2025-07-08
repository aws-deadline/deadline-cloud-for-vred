# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

from pathlib import Path
from typing import Any, Dict, Optional

from deadline.client.job_bundle.parameters import read_job_bundle_parameters

try:
    from .constants import Constants
except ImportError:
    from constants import Constants  # type: ignore[no-redef]


class DynamicKeyValueObject:
    def __init__(self, data_dict: Dict[str, Any]) -> None:
        """
        Assigns attributes and values to this object; reflect the contents of data_dict for easy attribute-based access.
        :param: data_dict: attributes/properties and values
        """
        for k, v in data_dict.items():
            setattr(self, k, v)


def str_to_bool(s: str) -> bool:
    return s.lower() == "true"


def convert_from_openjd_value(value, type_info):
    """
    Convert OpenJD parameter value to the appropriate Python type.
    :param value: the value to convert
    :param type_info: type information ('INT', 'STRING', etc.)
    :return: converted value (as int, bool, or str)
    """
    if type_info == "INT":
        return int(value)
    elif type_info == "STRING" and value in ("true", "false"):
        return str_to_bool(value)
    else:
        return str(value)


def get_vred_render_parameters(
    test_configuration_name: str, scene_filename_override: Optional[str] = ""
) -> Dict[str, Any]:
    """
    Provide JSON render configuration object (based on YAML job bundle file associated scene file).
    :param: test_configuration_name: name (w/o path) of the YAML job bundle configuration to apply
    :param: scene_filename_override: optionally overrides the scene file name defined in the job bundle
    :return: a dictionary containing values (non-inferred) with appropriate types for use in VRED API calls.
    """
    base_dir = Path(__file__).parent.resolve()
    job_bundle_dir = base_dir / Constants.JOB_BUNDLES_DIRECTORY_NAME / test_configuration_name

    try:
        job_bundle_parameters = read_job_bundle_parameters(str(job_bundle_dir))
        render_parameters = {
            item["name"]: convert_from_openjd_value(item["value"], item.get("type"))
            for item in job_bundle_parameters
            if "value" in item
        }
    except (FileNotFoundError, KeyError, PermissionError):
        return {}

    # Set scene file path
    if scene_filename_override:
        scene_file = scene_filename_override
    else:
        try:
            # Assume scene file is already loaded (if accessing in VRED)
            from builtins import vrFileIOService  # type: ignore

            scene_file = vrFileIOService.getFileName() or Constants.UNKNOWN_SCENE_FILENAME
        except ImportError:
            scene_file = render_parameters.get(
                Constants.SCENE_FILE_FIELD, Constants.UNKNOWN_SCENE_FILENAME
            )

    render_parameters[Constants.SCENE_FILE_FIELD] = str(
        base_dir / Constants.SCENE_FILE_DIRECTORY_NAME / Path(scene_file).name
    )

    # Set unique output directory
    scene_basename = Path(render_parameters[Constants.SCENE_FILE_FIELD]).stem
    output_subdir = f"{scene_basename}_{test_configuration_name}"
    render_parameters[Constants.OUTPUT_DIRECTORY_FIELD] = str(
        base_dir / Constants.OUTPUT_DIRECTORY_NAME / output_subdir
    )

    return render_parameters
