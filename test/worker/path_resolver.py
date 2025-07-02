# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

from pathlib import Path

from constants import Constants


class PathResolver:
    """Handles file path resolution and validation."""

    def __init__(self):
        self.base_path = Path(__file__).resolve().parent

    def get_scene_file(self, filename: str) -> Path | None:
        """
        Get the full path to scene file
        :param: filename: provided path to scene file
        :return: None is filename is empty; else the full path to the scene file
        """
        if not filename:
            return None
        return self.base_path / Constants.SCENE_FILE_DIRECTORY_NAME / filename

    def get_config_file(self, config_name: str) -> Path:
        """
        Get the full path to the configuration file.
        :param: config_name: test configuration within the job bundles directory
        :return: full path to the configuration file.
        """
        return (
            self.base_path
            / Constants.JOB_BUNDLES_DIRECTORY_NAME
            / config_name
            / Constants.PARAMETER_VALUES_FILENAME
        )

    def get_expected_output_folder(self, config_name: str, scene_file_basename: str) -> Path:
        """
        Get the path to the expected output folder.
        :param: config_name: test configuration within the job bundles directory
        :param: scene_file_basename: filename prefix (excluding extension)
        return: expected output directory as a path
        """
        subdir = f"{scene_file_basename}-{config_name}"
        return self.base_path / Constants.EXPECTED_OUTPUT_DIRECTORY_NAME / subdir

    def get_input_tiles_folder(self, config_name: str, scene_file_basename: str) -> Path:
        """
        Get the path to the input tiles folder.
        :param: config_name: test configuration within the job bundles directory
        :param: scene_file_basename: filename prefix (excluding extension)
        return: input tile directory as a path
        """
        subdir = f"{scene_file_basename}-{config_name}"
        return self.base_path / Constants.TILES_DIRECTORY_NAME / subdir
