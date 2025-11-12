# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

from pathlib import Path


class PathResolver:
    """Handles file path resolution and validation."""

    SCENE_FILE_DIRECTORY_NAME = "scene_files"
    JOB_BUNDLES_DIRECTORY_NAME = "job_bundles"
    TILES_DIRECTORY_NAME = "tiles"
    OUTPUT_DIRECTORY_NAME = "output"
    EXPECTED_OUTPUT_DIRECTORY_NAME = "expected_output"
    PARAMETER_VALUES_FILENAME = "parameter_values.yaml"

    def __init__(self):
        self.base_path = Path(__file__).resolve().parent

    def get_scene_file(self, filename: str) -> Path:
        """
        Get the full path to scene file
        :param: filename: provided path to scene file
        :return: None is filename is empty; else the full path to the scene file
        """
        return self.base_path / self.SCENE_FILE_DIRECTORY_NAME / filename

    def get_config_file(self, config_name: str) -> Path:
        """
        Get the full path to the configuration file.
        :param: config_name: test configuration within the job bundles directory
        :return: full path to the configuration file.
        """
        return (
            self.base_path
            / self.JOB_BUNDLES_DIRECTORY_NAME
            / config_name
            / self.PARAMETER_VALUES_FILENAME
        )

    def get_job_bundles_folder(self) -> Path:
        """Get the path to the job bundles folder"""
        return self.base_path / self.JOB_BUNDLES_DIRECTORY_NAME

    def get_output_folder(self) -> Path:
        """Get the path to the output folder"""
        return self.base_path / self.OUTPUT_DIRECTORY_NAME

    def get_expected_output_folder(self, config_name: str, scene_file_basename: str) -> Path:
        """
        Get the path to the expected output folder.
        :param: config_name: test configuration within the job bundles directory
        :param: scene_file_basename: filename prefix (excluding extension)
        return: expected output directory as a path
        """
        subdir = f"{scene_file_basename}-{config_name}"
        return self.base_path / self.EXPECTED_OUTPUT_DIRECTORY_NAME / subdir

    def get_input_tiles_folder(self, config_name: str, scene_file_basename: str) -> Path:
        """
        Get the path to the input tiles folder.
        :param: config_name: test configuration within the job bundles directory
        :param: scene_file_basename: filename prefix (excluding extension)
        return: input tile directory as a path
        """
        subdir = f"{scene_file_basename}-{config_name}"
        return self.base_path / self.TILES_DIRECTORY_NAME / subdir
