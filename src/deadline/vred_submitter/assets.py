# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Provides an Asset Searching class"""

import os

from pathlib import Path

from .constants import Constants
from .scene import Scene


class AssetIntrospector:
    def parse_scene_assets(self) -> set[Path]:
        """
        Adds the current scene file and Render Script to the set of assets to pass to Deadline Cloud for rendering.
        Note: in the future, this may be modified to search the scene for assets, and filter out assets that are not
        needed for rendering.
        return: a set containing file paths of assets needed for Rendering
        """
        assets: set[Path] = set()
        assets.add(Path(os.path.join(Scene.project_path(), Scene.name())))
        assets.add(Path(os.path.join(Path(__file__).parent, Constants.VRED_RENDER_SCRIPT_FILENAME)))
        return assets
