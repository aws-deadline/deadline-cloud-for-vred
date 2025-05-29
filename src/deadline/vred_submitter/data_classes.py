# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Defines data models for render parameters and their values.
This module include parameter field definitions, job parameter containers, UI-based render settings support
(for transporting render parameters and their values).
"""

import os

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RenderSubmitterUISettings:
    """
    VRED-specific render settings that the submitter UI will reference.
    Note: these case-sensitive settings need to be synchronized with exact field names in template.yaml, UI.
    Note: these settings can't be dynamically loaded in-place using the existing dataclass/field mechanism.
    Note: values set to False might not be exposed in the submitter UI, but are exposed in the stock UI and backend
    """

    # Internal settings
    #
    description: str = field(default="")
    input_filenames: list[str] = field(default_factory=list)
    input_directories: list[str] = field(default_factory=list)
    JobScriptDir: str = field(default=os.path.normpath(os.path.join(Path(__file__).parent)))
    name: str = field(default="")
    output_directories: list[str] = field(default_factory=list)
    submitter_name: str = field(default="VRED")

    # Render settings - some settings that have a False value aren't currently exposed in the UI
    #
    AnimationClip: str = field(default="")
    AnimationType: str = field(default="Clip")
    DLSSQuality: str = field(default="Off")
    DPI: int = field(default=72)
    EndFrame: int = field(default=24)
    FrameStep: int = field(default=1)
    FramesPerTask: int = field(default=1)
    GPURaytracing: bool = field(default=False)
    ImageHeight: int = field(default=600)
    ImageWidth: int = field(default=800)
    IncludeAlphaChannel: bool = field(default=False)
    JobType: str = field(default="Render")
    NumXTiles: int = field(default=1)
    NumYTiles: int = field(default=1)
    OutputDir: str = field(default="")
    OutputFileNamePrefix: str = field(default="output")
    OutputFormat: str = field(default="PNG")
    OverrideRenderPass: bool = field(default=False)
    PremultiplyAlpha: bool = field(default=False)
    RegionRendering: bool = field(default=False)
    RenderAnimation: bool = field(default=True)
    RenderQuality: str = field(default="Realistic High")
    SSQuality: str = field(default="Off")
    SceneFile: str = field(default="")
    SequenceName: str = field(default="")
    StartFrame: int = field(default=0)
    TonemapHDR: bool = field(default=False)
    View: str = field(default="")
