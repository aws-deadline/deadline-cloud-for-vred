# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Provides an Asset Searching class"""

from pathlib import Path

from .scene import Scene
from .vred_utils import get_all_file_references


class AssetIntrospector:
    def parse_scene_assets(self) -> set[Path]:
        """
        Adds the current scene file and file references to the set of assets to pass to Deadline Cloud for rendering.
        return: a set containing file paths of assets needed for rendering.
        """
        return {Path(Scene.project_full_path())} | set(get_all_file_references())
