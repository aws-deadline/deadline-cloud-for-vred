# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Defines data models for render parameters and their values.
This module include parameter field definitions, job parameter containers, UI-based render settings support
(for transporting render parameters and their values).
"""

import dataclasses
import json
import os
import traceback
from dataclasses import dataclass, field
from pathlib import Path

from .constants import Constants
from .vred_logger import get_logger


_global_logger = get_logger(__name__)


@dataclass
class RenderSubmitterUISettings:
    """
    VRED-specific render settings that the submitter UI will reference.
    Note: these case-sensitive settings need to be synchronized with exact field names in template.yaml, UI.
    Note: these settings can't be dynamically loaded in-place using the existing dataclass/field mechanism.
    Note: values set to False might not be exposed in the submitter UI, but are exposed in the stock UI and backend
    """

    # Shared settings
    #
    description: str = field(default="", metadata={"sticky": True})
    input_filenames: list[str] = field(default_factory=list, metadata={"sticky": True})
    input_directories: list[str] = field(default_factory=list, metadata={"sticky": True})
    JobScriptDir: str = field(default=os.path.normpath(os.path.join(Path(__file__).parent)))
    name: str = field(default="", metadata={"sticky": True})
    output_directories: list[str] = field(default_factory=list, metadata={"sticky": True})
    priority: int = field(default=50, metadata={"sticky": True})
    submitter_name: str = field(default="VRED")
    initial_status: str = field(default="READY", metadata={"sticky": True})
    max_failed_tasks_count: int = field(default=20, metadata={"sticky": True})
    max_retries_per_task: int = field(default=5, metadata={"sticky": True})
    max_worker_count: int = field(
        default=-1, metadata={"sticky": True}
    )  # -1 indicates unlimited max worker count

    # Render settings - some settings that have a False value aren't currently exposed in the UI
    #
    AnimationClip: str = field(default="", metadata={"sticky": True})
    AnimationType: str = field(default="Clip", metadata={"sticky": True})
    DLSSQuality: str = field(default="Off", metadata={"sticky": True})
    DPI: int = field(default=72, metadata={"sticky": True})
    EndFrame: int = field(default=24, metadata={"sticky": True})
    FrameStep: int = field(default=1, metadata={"sticky": True})
    FramesPerTask: int = field(default=1, metadata={"sticky": True})
    GPURaytracing: bool = field(default=False, metadata={"sticky": True})
    ImageHeight: int = field(default=600, metadata={"sticky": True})
    ImageWidth: int = field(default=800, metadata={"sticky": True})
    IncludeAlphaChannel: bool = field(default=False, metadata={"sticky": True})
    JobType: str = field(default="Render", metadata={"sticky": True})
    NumXTiles: int = field(default=1, metadata={"sticky": True})
    NumYTiles: int = field(default=1, metadata={"sticky": True})
    OutputDir: str = field(default="", metadata={"sticky": True})
    OutputFileNamePrefix: str = field(default="output", metadata={"sticky": True})
    OutputFormat: str = field(default="PNG", metadata={"sticky": True})
    OverrideRenderPass: bool = field(default=False, metadata={"sticky": True})
    PremultiplyAlpha: bool = field(default=False, metadata={"sticky": True})
    RegionRendering: bool = field(default=False, metadata={"sticky": True})
    RenderAnimation: bool = field(default=True, metadata={"sticky": True})
    RenderQuality: str = field(default="Realistic High", metadata={"sticky": True})
    SSQuality: str = field(default="Off", metadata={"sticky": True})
    SceneFile: str = field(default="")
    SequenceName: str = field(default="", metadata={"sticky": True})
    StartFrame: int = field(default=0, metadata={"sticky": True})
    TonemapHDR: bool = field(default=False, metadata={"sticky": True})
    View: str = field(default="", metadata={"sticky": True})

    def load_sticky_settings(self, scene_filename: str):
        sticky_settings_filename = Path(scene_filename).with_suffix(
            Constants.RENDER_SUBMITTER_SETTINGS_FILE_EXT
        )
        if sticky_settings_filename.exists() and sticky_settings_filename.is_file():
            try:
                with open(sticky_settings_filename, encoding="utf8") as fh:
                    sticky_settings = json.load(fh)

                if isinstance(sticky_settings, dict):
                    _global_logger.info(f"Loaded sticky settings file: {sticky_settings_filename}")
                    sticky_fields = {
                        field.name: field
                        for field in dataclasses.fields(self)
                        if field.metadata.get("sticky")
                    }
                    for name, value in sticky_settings.items():
                        # Only set fields that are defined in the dataclass
                        if name in sticky_fields:
                            setattr(self, name, value)
                else:
                    _global_logger.warning(
                        f"Sticky settings file contains invalid data type: {type(sticky_settings)}"
                    )

            except (OSError, json.JSONDecodeError) as e:
                # If something bad happened to the sticky settings file,
                # just use the defaults instead of producing an error.
                traceback.print_exc()
                _global_logger.warning(
                    f"Failed to load sticky settings file {sticky_settings_filename.absolute()}: {e}, reverting to default settings"
                )

    def save_sticky_settings(self, scene_filename: str):
        sticky_settings_filename = Path(scene_filename).with_suffix(
            Constants.RENDER_SUBMITTER_SETTINGS_FILE_EXT
        )
        sticky_settings_path = str(sticky_settings_filename.absolute())

        try:
            obj = {
                field.name: getattr(self, field.name)
                for field in dataclasses.fields(self)
                if field.metadata.get("sticky")
            }

            _global_logger.info(f"Saving sticky settings to: {sticky_settings_path}")
            with open(sticky_settings_filename, "w", encoding="utf8") as fh:
                json.dump(obj, fh, indent=1)

        except OSError as e:
            _global_logger.warning(
                f"Failed to save sticky settings file to {sticky_settings_path}: {e}", exc_info=True
            )
