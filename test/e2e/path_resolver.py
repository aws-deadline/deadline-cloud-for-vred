# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

from pathlib import Path


class PathResolver:
    """Handles file path resolution for e2e tests"""

    SCENE_FILE_DIRECTORY_NAME = "scene_files"
    EXPECTED_OUTPUT_DIRECTORY_NAME = "expected_output"
    OUTPUT_DIRECTORY_NAME = "output"

    def __init__(self):
        self.base_path = Path(__file__).resolve().parent

    def get_scene_file(self, filename: str) -> Path | None:
        if not filename:
            return None
        return self.base_path / self.SCENE_FILE_DIRECTORY_NAME / filename

    def get_expected_output_render_folder(self, test_name: str, scene_file_basename: str) -> Path:
        """Get expected render output folder"""
        subdir = f"{scene_file_basename}-{test_name}"
        return self.base_path / self.EXPECTED_OUTPUT_DIRECTORY_NAME / subdir / "render"

    def get_expected_output_bundle_folder(self, test_name: str, scene_file_basename: str) -> Path:
        """Get expected job bundle output folder"""
        subdir = f"{scene_file_basename}-{test_name}"
        return self.base_path / self.EXPECTED_OUTPUT_DIRECTORY_NAME / subdir / "bundle"

    def get_output_folder(self) -> Path:
        return self.base_path / self.OUTPUT_DIRECTORY_NAME

    def get_output_folder_for_test(self, test_name: str, scene_file_basename: str) -> Path:
        subdir = f"{scene_file_basename}-{test_name}"
        return self.base_path / self.OUTPUT_DIRECTORY_NAME / subdir
