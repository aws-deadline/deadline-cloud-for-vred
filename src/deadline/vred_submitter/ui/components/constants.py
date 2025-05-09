# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Provides a Constants class that focuses on UI design, values to populate"""

from types import MappingProxyType
from typing import List, Final


class ConstantsMeta(type):
    """Metaclass to prevent modification of class attributes."""

    def __setattr__(cls, name, value):
        """Prevent modification of class attributes."""
        raise AttributeError(f"Cannot modify constant '{name}'")

    def __delattr__(cls, name):
        """Prevent deletion of class attributes."""
        raise AttributeError(f"Cannot delete constant '{name}'")


class Constants(metaclass=ConstantsMeta):
    """Constants class for UI settings."""

    ABORT_ON_MISSING_TILES_LABEL: Final[str] = "Abort on Missing Tiles"
    ABORT_ON_MISSING_TILES_LABEL_DESCRIPTION: Final[str] = (
        "If enabled, the assembly job will fail if it cannot find any of the tiles."
    )
    ABORT_ON_MISSING_BACKGROUND_LABEL: Final[str] = "Abort on Missing Background"
    ABORT_ON_MISSING_BACKGROUND_LABEL_DESCRIPTION: Final[str] = (
        "If enabled, the render will fail if the background image specified does not exist."
    )
    ANIMATION_SETTINGS_DIALOG_NAME: Final[str] = "Animation Settings"
    ANIMATION_CLIP_LABEL: Final[str] = "Animation Clip"
    ANIMATION_CLIP_LABEL_DESCRIPTION: Final[str] = "The specific animation clip to render."
    ANIMATION_TYPE_LABEL: Final[str] = "Animation Type"
    ANIMATION_TYPE_LABEL_DESCRIPTION: Final[str] = "The type of animation."
    ANIMATION_TYPE_OPTIONS: Final[List[str]] = ["Clip", "Timeline"]
    ASSEMBLE_OVER_LABEL: Final[str] = "Assemble Over"
    ASSEMBLE_OVER_LABEL_DESCRIPTION: Final[str] = "The initial image to assemble over."
    BACKGROUND_IMAGE_LABEL: Final[str] = "Background Image"
    BACKGROUND_IMAGE_LABEL_DESCRIPTION: Final[str] = (
        "The background image file to be used for the assemble over option."
    )
    BACKGROUND_IMAGE_OPTIONS: Final[List[str]] = [
        "Blank Image",
        "Previous Output",
        "Selected Image",
    ]
    CLEAN_UP_TILES_AFTER_ASSEMBLY_LABEL: Final[str] = "Cleanup Tiles After Assembly"
    CLEAN_UP_TILES_AFTER_ASSEMBLY_LABEL_DESCRIPTION: Final[str] = (
        "If enabled, tiles will be deleted after the assembly job is completed."
    )
    CLIP_LABEL: Final[str] = "Clip"
    CUSTOM_SPEED_FIELD_NAME: Final[str] = "_customSpeed"
    DEFAULT_IMAGE_SIZE_PRESET: Final[str] = "SVGA (800 x 600)"
    DEFAULT_SCENE_FILE_FPS_COUNT: Final[float] = 24.0
    DEFAULT_DPI_RESOLUTION: Final[int] = 72
    DLSS_QUALITY_LABEL: Final[str] = "DLSS Quality"
    DLSS_QUALITY_LABEL_DESCRIPTION: Final[str] = (
        "Sets the deep learning supersampling (DLSS) quality."
    )
    DLSS_QUALITY_OPTIONS: Final[List[str]] = [
        "Off",
        "Performance",
        "Balance",
        "Quality",
        "Ultra Performance",
    ]
    ELLIPSIS_LABEL: Final[str] = "..."
    EMPTY_FRAME_RANGE: Final[str] = "0-0"
    ENABLE_REGION_RENDERING_LABEL: Final[str] = "Enable Region Rendering"
    ENABLE_REGION_RENDERING_LABEL_DESCRIPTION: Final[str] = (
        "If this option is enabled, then the image will be divided into multiple tasks and assembled afterwards."
    )
    FRAME_RANGE_BASIC_FORMAT: Final[str] = "%d-%d"
    FRAME_RANGE_LABEL: Final[str] = "Frame Range"
    FRAME_RANGE_LABEL_DESCRIPTION: Final[str] = "The list of frames to render."
    FRAMES_PER_TASK_LABEL: Final[str] = "Frames Per Task"
    FRAMES_PER_TASK_LABEL_DESCRIPTION: Final[str] = (
        "The number of frames that will be rendered at a time for each job's task."
    )
    IMAGE_SIZE_LABEL: Final[str] = "Image Size (px w,h)"
    IMAGE_SIZE_LABEL_DESCRIPTION: Final[str] = "The image size in pixels (width and height)"
    IMAGE_SIZE_PRESET_CUSTOM: Final[str] = "Custom"
    IMAGE_SIZE_PRESET_FROM_RENDER_WINDOW: Final[str] = "From Render Window"
    IMAGE_SIZE_PRESETS_LABEL: Final[str] = "Image Size Presets"
    IMAGE_SIZE_PRESETS_LABEL_DESCRIPTION: Final[str] = (
        "The available presets for image size and resolution"
    )
    IMAGE_SIZE_PRESETS_MAP: MappingProxyType[str, list[int]] = MappingProxyType(
        {
            "Custom": [-2, -2, -2],
            "From Render Window": [-1, -1, -1],
            "A0 portrait": [9933, 14043, 300],
            "A0 landscape": [14043, 9933, 300],
            "A1 portrait": [7016, 9933, 300],
            "A1 landscape": [9933, 7016, 300],
            "A2 portrait": [4961, 7016, 300],
            "A2 landscape": [7016, 4961, 300],
            "A3 portrait": [3508, 4961, 300],
            "A3 landscape": [4961, 3508, 300],
            "A4 portrait": [2480, 3508, 300],
            "A4 landscape": [3508, 2480, 300],
            "A5 portrait": [1748, 2480, 300],
            "A5 landscape": [2480, 1748, 300],
            "A6 portrait": [1240, 1748, 300],
            "A6 landscape": [1748, 1240, 300],
            "UHDV (7680 x 4320)": [7680, 4320, 72],
            "DCI 4K (4096 x 3112)": [4096, 3112, 72],
            "4K (4096 x 2160)": [4096, 2160, 72],
            "QSXGA (2560 x 2048)": [2560, 2048, 72],
            "WQXGA (2560 x 1600)": [2560, 1600, 72],
            "DCI 2K (2048 x 1556)": [2048, 1556, 72],
            "QXGA (2048 x 1536)": [2048, 1536, 72],
            "WUXGA (1920 x 1200)": [1920, 1200, 72],
            "HD 1080 (1920 x 1080)": [1920, 1080, 72],
            "WSXGA+ (1680 x 1050)": [1680, 1050, 72],
            "UXGA (1600 x 1200)": [1600, 1200, 72],
            "SXGA+ (1400 x 1050)": [1400, 1050, 72],
            "SXGA (1280 x 1024)": [1280, 1024, 72],
            "HD 720 (1280 x 720)": [1280, 720, 72],
            "XGA (1024 x 768)": [1024, 768, 72],
            "PAL WIDE (1024 x 576)": [1024, 576, 72],
            "SVGA (800 x 600)": [800, 600, 72],
            "WVGA (854 x 480)": [853, 480, 72],
            "PAL (768 x 576)": [768, 576, 72],
            "NTSC (720 x 480)": [720, 480, 72],
            "VGA (640 x 480)": [640, 480, 72],
            "QVGA (320 x 240)": [320, 240, 72],
            "CGA (320 x 200)": [320, 200, 72],
        }
    )
    INCH_TO_CM_FACTOR: Final[float] = 2.54
    JOB_TYPE_LABEL: Final[str] = "Job Type"
    JOB_TYPE_LABEL_DESCRIPTION: Final[str] = "The type of job to Render."
    JOB_TYPE_RENDER: Final[str] = "Render"
    JOB_TYPE_RENDER_QUEUE: Final[str] = "Render Queue"
    JOB_TYPE_SEQUENCER: Final[str] = "Sequencer"
    JOB_TYPE_OPTIONS: Final[List[str]] = [
        JOB_TYPE_RENDER,
        JOB_TYPE_RENDER_QUEUE,
        JOB_TYPE_SEQUENCER,
    ]
    LONG_TEXT_ENTRY_WIDTH: Final[int] = 500
    MIN_FRAMES_PER_TASK: Final[int] = 1
    MIN_DPI: Final[int] = 1
    MIN_IMAGE_DIMENSION: Final[int] = 1
    MIN_TILES_PER_DIMENSION: Final[int] = 1
    MAX_DPI: Final[int] = 1000
    MAX_FRAMES_PER_TASK: Final[int] = 10000
    MAX_IMAGE_DIMENSION: Final[int] = 10000
    MAX_TILES_PER_DIMENSION: Final[int] = 10000
    MODERATE_TEXT_ENTRY_WIDTH: Final[int] = 300
    PRINTING_PRECISION_DIGITS_COUNT: Final[int] = 2
    PRINTING_SIZE_LABEL: Final[str] = "Printing Size (cm w,h)"
    PRINTING_SIZE_LABEL_DESCRIPTION: Final[str] = (
        "The printing size in centimeters (width and height)"
    )
    RENDER_ANIMATION_LABEL: Final[str] = "Render Animation"
    RENDER_ANIMATION_LABEL_DESCRIPTION: Final[str] = (
        "The animation to use, if left blank it will use all enabled clips."
    )
    RENDER_QUALITY_LABEL: Final[str] = "Render Quality"
    RENDER_QUALITY_LABEL_DESCRIPTION: Final[str] = "The Render quality to use."
    RENDER_QUALITY_OPTIONS: Final[List[str]] = [
        "Analytic Low",
        "Analytic High",
        "Realistic Low",
        "Realistic High",
        "Raytracing",
        "NPR",
    ]
    RENDER_QUALITY_DEFAULT: Final[str] = "Realistic High"
    RENDER_OUTPUT_LABEL: Final[str] = "Render Output"
    RENDER_OUTPUT_LABEL_DESCRIPTION: Final[str] = "The filename of the image(s) to be rendered."
    RENDER_VIEW_LABEL: Final[str] = "Render Viewpoint/Camera"
    RENDER_VIEW_LABEL_DESCRIPTION: Final[str] = "The viewpoint or camera to render"
    RESOLUTION_LABEL: Final[str] = "Resolution (px/inch)"
    RESOLUTION_LABEL_DESCRIPTION: Final[str] = "The resolution (pixels per inch)"
    SECTION_RENDER_OPTIONS: Final[str] = "Render Options"
    SECTION_SEQUENCER_OPTIONS: Final[str] = "Sequencer Options"
    SECTION_TILING_SETTINGS: Final[str] = "Tiling Settings"
    SELECTED_IMAGE_LABEL: Final[str] = "Selected Image"
    SEQUENCE_NAME_LABEL: Final[str] = "Sequence Name"
    SEQUENCE_NAME_LABEL_DESCRIPTION: Final[str] = (
        "The name of the sequence to run, if empty all sequences will be run."
    )
    SHORT_TEXT_ENTRY_WIDTH: Final[int] = 200
    SS_QUALITY_LABEL: Final[str] = "SS Quality"
    SS_QUALITY_LABEL_DESCRIPTION: Final[str] = (
        "Sets the regular (non-DLSS) supersampling quality. DLSS quality takes precedence."
    )
    SS_QUALITY_OPTIONS: Final[List[str]] = ["Off", "Low", "Medium", "High", "Ultra High"]
    SUBMIT_DEPENDENT_ASSEMBLY_JOB_LABEL: Final[str] = "Submit Dependent Assembly Job"
    SUBMIT_DEPENDENT_ASSEMBLY_JOB_LABEL_DESCRIPTION: Final[str] = (
        "If this option is enabled then an assembly job will be submitted."
    )
    TILES_IN_X_LABEL: Final[str] = "Tiles In X"
    TILES_IN_X_LABEL_DESCRIPTION: Final[str] = (
        "The number of tiles to horizontally divide the region into."
    )
    TILES_IN_Y_LABEL: Final[str] = "Tiles In Y"
    TILES_IN_Y_LABEL_DESCRIPTION: Final[str] = (
        "The number of tiles to vertically divide the region into."
    )
    TIMELINE_ACTION_NAME: Final[str] = "Timeline"
    TIMELINE_ANIMATION_PREFS_BUTTON_NAME: Final[str] = "_prefs"
    TIMELINE_TOOLBAR_NAME: Final[str] = "Timeline_Toolbar"
    USE_CLIP_RANGE_LABEL: Final[str] = "Use Clip Range"
    USE_CLIP_RANGE_LABEL_DESCRIPTION: Final[str] = (
        "When enabled, the frame range will be fixed to the range defined by the "
        "selected animation clip."
    )
    USE_GPU_RAY_TRACING_LABEL: Final[str] = "Use GPU Ray Tracing"
    USE_GPU_RAY_TRACING_LABEL_DESCRIPTION: Final[str] = "Use GPU Ray Tracing."
    UTF8_FLAG = "utf-8"
    VERY_LONG_TEXT_ENTRY_WIDTH: Final[int] = 700
    VERY_SHORT_TEXT_ENTRY_WIDTH: Final[int] = 150
    VRED_ALL_FILES_FILTER: Final[str] = "All Files (*.*)"
    VRED_IMAGE_EXPORT_FILTER: Final[str] = (
        "*.png (*.png);;*.bmp (*.bmp);;*.dds (*.dds);;*.dib (*.dib);;"
        "*.exr (*.exr);;*.hdr (*.hdr);;*.jfif (*.jfif);;*.jpe (*.jpe);;"
        "*.jpeg (*.jpeg);;*.jpg (*.jpg);;*.nrrd (*.nrrd);;*.pbm (*.pbm);;"
        "*.pgm (*.pgm);;*.png (*.png);;*.pnm (*.pnm);;*.ppm (*.ppm);;"
        "*.psb (*.psb);;*.psd (*.psd);;*.rle (*.rle);;*.tif (*.tif);;"
        "*.tiff (*.tiff);;*.vif (*.vif)"
    )

    def __new__(cls):
        """Prevent instantiation of this class."""
        raise TypeError("Constants class cannot be instantiated")
