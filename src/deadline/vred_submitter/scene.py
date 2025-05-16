# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import os

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from .vred_utils import (
    get_frame_current,
    get_frame_start,
    get_frame_stop,
    get_frame_step,
    get_scene_full_path,
)


@dataclass
class FrameRange:
    """
    Class used to represent a frame range.
    """

    start: int
    stop: Optional[int] = None
    step: Optional[int] = None

    def __repr__(self) -> str:
        if self.stop is None or self.stop == self.start:
            return str(self.start)

        if self.step is None or self.step == 1:
            return f"{self.start}-{self.stop}"

        return f"{self.start}-{self.stop}:{self.step}"

    def __iter__(self) -> Iterator[int]:
        stop: int = self.stop if self.stop is not None else self.start
        step: int = self.step if self.step is not None else 1

        return iter(range(self.start, stop + step, step))


"""
Functionality used for querying scene settings
"""


class Animation:
    """
    Functionality for retrieving Animation related settings from the active scene
    """

    @staticmethod
    def current_frame() -> int:
        """
        Returns the current frame number.
        """
        return int(get_frame_current())

    @staticmethod
    def start_frame() -> int:
        """
        Returns the start frame for the scenes render
        """
        return int(get_frame_start())

    @staticmethod
    def end_frame() -> int:
        """
        Returns the End frame for the scenes Render
        """
        return int(get_frame_stop())

    @staticmethod
    def frame_step() -> int:
        """
        Returns the frame step of the current render.
        """
        return int(get_frame_step())

    @classmethod
    def frame_list(cls) -> FrameRange:
        """
        Returns a FrameRange object representing the full framelist.
        """
        return FrameRange(start=get_frame_start(), stop=get_frame_stop(), step=get_frame_step())


class Scene:
    """
    Functionality for retrieving settings from the active scene
    """

    @staticmethod
    def name() -> str:
        """
        Returns the full path to the active scene
        """
        return get_scene_full_path()

    @staticmethod
    def get_output_directories() -> list[str]:
        """
        Returns a list of directories files will be output to.
        """
        """
        return [os.path.dirname(path) for path in image_paths]
        """
        return [""]

    @staticmethod
    def project_path() -> Path:
        """
        Returns the base path to the project the current scene is in
        """
        return Path(os.path.normpath(get_scene_full_path())).parent

    @staticmethod
    def output_path() -> Path:
        """
        Returns the path to the default output directory.
        """
        return Scene.project_path()
