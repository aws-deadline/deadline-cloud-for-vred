# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Path resolution utilities for integration tests."""

from pathlib import Path


class PathResolver:
    """Handles file path resolution for integration tests."""

    SCENE_FILE_DIRECTORY_NAME = "scene_files"
    EXPECTED_OUTPUT_DIRECTORY_NAME = "expected_output"
    BUNDLE_SUBDIRECTORY_NAME = "bundle"
    RENDER_SUBDIRECTORY_NAME = "render"
    TILES_DIRECTORY_NAME = "tiles"
    OUTPUT_DIRECTORY_NAME = "output"
    PARAMETER_VALUES_FILENAME = "parameter_values.yaml"

    def __init__(self):
        # Absolute path to the directory where tests are located (e.g., test/integ)
        self.base_path = Path(__file__).resolve().parent

    def get_scene_file(self, filename: str) -> Path:
        """
        Get the full path to scene file.

        :param filename: provided path to scene file
        :return: The full path to the scene file
        """
        return self.base_path / self.SCENE_FILE_DIRECTORY_NAME / filename

    def get_param_values_file(self, config_name: str) -> Path:
        """
        Get the full path to the parameter_values file.

        :param config_name: test configuration within the job bundles directory
        :return: full path to the parameter_values file
        """
        return (
            self.base_path
            / self.EXPECTED_OUTPUT_DIRECTORY_NAME
            / self.BUNDLE_SUBDIRECTORY_NAME
            / config_name
            / self.PARAMETER_VALUES_FILENAME
        )

    def get_expected_bundle_folder(self, config_name: str, scene_file_basename: str) -> Path:
        """
        Get the path to the expected bundle output folder (for submitter tests).

        :param config_name: test configuration name
        :param scene_file_basename: filename prefix (excluding extension)
        :return: expected bundle output directory as a path
        """
        subdir = f"{scene_file_basename}-{config_name}"
        return (
            self.base_path
            / self.EXPECTED_OUTPUT_DIRECTORY_NAME
            / self.BUNDLE_SUBDIRECTORY_NAME
            / subdir
        )

    def get_expected_render_folder(self, config_name: str, scene_file_basename: str) -> Path:
        """
        Get the path to the expected render output folder (for worker tests).

        :param config_name: test configuration name
        :param scene_file_basename: filename prefix (excluding extension)
        :return: expected render output directory as a path
        """
        subdir = f"{scene_file_basename}-{config_name}"
        return (
            self.base_path
            / self.EXPECTED_OUTPUT_DIRECTORY_NAME
            / self.RENDER_SUBDIRECTORY_NAME
            / subdir
        )

    def get_job_bundles_folder(self) -> Path:
        """
        Get the path to the job bundles folder.

        :return: job bundles directory path
        """
        return self.base_path / self.EXPECTED_OUTPUT_DIRECTORY_NAME / self.BUNDLE_SUBDIRECTORY_NAME

    def get_output_folder(self) -> Path:
        """
        Get the path to the (actual) output folder. The creation/deletion of this folder is
        managed by the pytest fixture.

        :return: output directory path
        """
        return self.base_path / self.OUTPUT_DIRECTORY_NAME

    def get_output_folder_for_test(self, test_name: str, scene_file_basename: str) -> Path:
        """
        Get the path to the output folder for a specific test.

        :param test_name: test name/ID
        :param scene_file_basename: filename prefix (excluding extension)
        :return: output directory path for the test
        """
        subdir = f"{scene_file_basename}-{test_name}"
        return self.base_path / self.OUTPUT_DIRECTORY_NAME / subdir

    def get_input_tiles_folder(self, config_name: str, scene_file_basename: str) -> Path:
        """
        Get the path to the input tiles folder.

        :param config_name: test configuration name
        :param scene_file_basename: filename prefix (excluding extension)
        :return: input tile directory as a path
        """
        subdir = f"{scene_file_basename}-{config_name}"
        return self.base_path / self.TILES_DIRECTORY_NAME / subdir
