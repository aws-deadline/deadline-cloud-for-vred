# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Provides a Constants class that focuses on UI design, values to populate"""

from types import MappingProxyType
from typing import List, Final

# Note: For all Qt Widgets, 1920x1080 @ 100% scale was used to determine baseline X,Y dimension values
# (at DPIScale.factor=1.0). Changing resolution and scale will maintain the sizing/layout of widgets.
# Avoid circular dependencies by storing DPI factor here and changing from outside.


class DPIScale:
    factor: float = 1.0


_global_dpi_scale = DPIScale()


class ClassProperty:
    def __init__(self, func):
        if not callable(func):
            raise TypeError("ClassProperty requires a callable function")
        self.func = func

    def __get__(self, instance, owner):
        if owner is None:
            return self
        if not isinstance(owner, type):
            raise TypeError("ClassProperty can only be used on classes")
        return self.func(owner)


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

    ANIMATION_SETTINGS_DIALOG: Final[str] = "Animation Settings"
    ANIMATION_CLIP_LABEL: Final[str] = "Animation Clip"
    ANIMATION_CLIP_LABEL_DESCRIPTION: Final[str] = "The name of the animation clip to render."
    ANIMATION_TYPE_LABEL: Final[str] = "Animation Type"
    ANIMATION_TYPE_LABEL_DESCRIPTION: Final[str] = "The type of animation (Clip or Timeline)."
    ANIMATION_TYPE_OPTIONS: Final[List[str]] = ["Clip", "Timeline"]
    CLIP_LABEL: Final[str] = "Clip"

    @ClassProperty
    def COLUMN_SMALL_SPACING_OFFSET_PIXELS(cls) -> int:
        return int(15 * _global_dpi_scale.factor)

    @ClassProperty
    def COMBO_BOX_MIN_WIDTH(cls) -> int:
        return int(55 * _global_dpi_scale.factor)

    @ClassProperty
    def COMBO_BOX_PADDING(cls) -> int:
        return int(24 * _global_dpi_scale.factor)

    CUSTOM_SPEED_NAME: Final[str] = "_customSpeed"
    DEFAULT_IMAGE_SIZE_PRESET: Final[str] = "SVGA (800 x 600)"
    DEFAULT_SCENE_FILE_FPS_COUNT: Final[float] = 24.0
    DEFAULT_DPI_RESOLUTION: Final[int] = 72
    DLSS_QUALITY_LABEL: Final[str] = "DLSS Quality"
    DLSS_QUALITY_LABEL_DESCRIPTION: Final[str] = (
        "The Deep Learning Super Sampling (DLSS) quality level to apply."
    )
    DLSS_QUALITY_OPTIONS: Final[List[str]] = [
        "Off",
        "Performance",
        "Balanced",
        "Quality",
        "Ultra Performance",
    ]
    DPI_LABEL: Final[str] = "Resolution (px/inch)"
    DPI_LABEL_DESCRIPTION: Final[str] = (
        "The dots-per-inch (DPI) physical scaling factor (pixels per inch)."
    )
    ELLIPSIS_LABEL: Final[str] = "..."
    EMPTY_FRAME_RANGE: Final[str] = "0-0"
    ENABLE_REGION_RENDERING_LABEL: Final[str] = "Enable Region Rendering"
    ENABLE_REGION_RENDERING_LABEL_DESCRIPTION: Final[str] = (
        "When enabled, the output rendered image will be divided into multiple tiles (sub-regions) that are first "
        "rendered as separate tasks for a given frame. These tiles will then be assembled (combined) into one output "
        "image for a given frame (in a separate task)."
    )
    FILE_PATH_REGEX_UNICODE_FILTER: Final[str] = r"^[\p{L}\p{N}_\-\. /\\:]+$"
    FRAME_RANGE_BASIC_FORMAT: Final[str] = "%d-%d"
    FRAME_RANGE_LABEL: Final[str] = "Frame Range"
    FRAME_RANGE_LABEL_DESCRIPTION: Final[str] = (
        "The list of frames to render (format: 'a', 'a-b', or 'a-bxn', "
        "where 'a' is the start frame, 'b' is the end frame, and 'n' is "
        "the frame step)."
    )
    FRAME_RANGE_MAX_LENGTH: Final[int] = 31
    FRAME_RANGE_REGEX_FILTER: Final[str] = r"^[0-9x\-]+$"
    FRAMES_PER_TASK_LABEL: Final[str] = "Frames Per Task"
    FRAMES_PER_TASK_LABEL_DESCRIPTION: Final[str] = (
        "The number of frames that will be rendered at a time for each task within a render job."
    )
    IMAGE_SIZE_LABEL: Final[str] = "Image Size (px w,h)"
    IMAGE_SIZE_LABEL_DESCRIPTION: Final[str] = "The image size in pixels (width and height)."
    IMAGE_SIZE_PRESET_CUSTOM: Final[str] = "Custom"
    IMAGE_SIZE_PRESET_FROM_RENDER_WINDOW: Final[str] = "From Render Window"
    IMAGE_SIZE_PRESETS_LABEL: Final[str] = "Image Size Presets"
    IMAGE_SIZE_PRESETS_LABEL_DESCRIPTION: Final[str] = (
        "The available presets for image size and resolution."
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
    JOB_TYPE_SEQUENCER: Final[str] = "Sequencer"
    JOB_TYPE_OPTIONS: Final[List[str]] = [
        JOB_TYPE_RENDER,
        JOB_TYPE_SEQUENCER,
    ]

    @ClassProperty
    def LONG_TEXT_ENTRY_WIDTH(cls) -> int:
        return int(200 * _global_dpi_scale.factor)

    @ClassProperty
    def MESSAGE_BOX_MIN_WIDTH(cls) -> int:
        return int(100 * _global_dpi_scale.factor)

    @ClassProperty
    def MESSAGE_BOX_SPACER_PREFERRED_WIDTH(cls) -> int:
        return int(150 * _global_dpi_scale.factor)

    @ClassProperty
    def MESSAGE_BOX_MAX_WIDTH(cls) -> int:
        return int(200 * _global_dpi_scale.factor)

    MIN_FRAMES_PER_TASK: Final[int] = 1
    MIN_DPI: Final[int] = 1
    MIN_IMAGE_DIMENSION: Final[int] = 1
    MIN_PRINT_DIMENSION: Final[float] = 0.04
    MAX_PRINT_DIMENSION: Final[float] = 25400.0
    MIN_TILES_PER_DIMENSION: Final[int] = 1
    MAX_DPI: Final[int] = 1000
    MAX_FRAMES_PER_TASK: Final[int] = 10000
    MAX_IMAGE_DIMENSION: Final[int] = 10000
    MAX_TILES_PER_DIMENSION: Final[int] = 10000

    @ClassProperty
    def MODERATE_TEXT_ENTRY_WIDTH(cls) -> int:
        return int(145 * _global_dpi_scale.factor)

    @ClassProperty
    def PUSH_BUTTON_MAXIMUM_WIDTH(cls) -> int:
        return int(40 * _global_dpi_scale.factor)

    @ClassProperty
    def PUSH_BUTTON_MAXIMUM_HEIGHT(cls) -> int:
        return int(40 * _global_dpi_scale.factor)

    @ClassProperty
    def PUSH_BUTTON_PADDING_PIXELS(cls) -> int:
        return int(10 * _global_dpi_scale.factor)

    PUSH_BUTTON_WIDTH_FACTOR: Final[int] = 4
    PRINTING_PRECISION_DIGITS_COUNT: Final[int] = 2
    PRINTING_SIZE_LABEL: Final[str] = "Printing Size (cm w,h)"
    PRINTING_SIZE_LABEL_DESCRIPTION: Final[str] = (
        "The printing size in centimeters (width and height)."
    )
    QT_GROUP_BOX_STYLESHEET: Final[
        str
    ] = """
            QGroupBox {
                border: 4px solid #999999;
                border-radius: 10px;
                margin-top: 5ex;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background-color: #444444;
            }
    """
    RENDER_ANIMATION_LABEL: Final[str] = "Render Animation"
    RENDER_ANIMATION_LABEL_DESCRIPTION: Final[str] = (
        "If checked, allows specifying an animation type (which can also include a specific animation clip), "
        "corresponding frame range and frames per task."
    )
    RENDER_QUALITY_LABEL: Final[str] = "Render Quality"
    RENDER_QUALITY_LABEL_DESCRIPTION: Final[str] = "The render quality level to apply."
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
    RENDER_OUTPUT_LABEL_DESCRIPTION: Final[str] = (
        "The path and filename prefixing of the image(s) to be rendered."
    )
    RENDER_VIEW_LABEL: Final[str] = "Render Viewpoint/Camera"
    RENDER_VIEW_LABEL_DESCRIPTION: Final[str] = (
        "The name of the viewpoint or camera from which to render."
    )
    SECTION_RENDER_OPTIONS: Final[str] = "Render Options"
    SECTION_SEQUENCER_OPTIONS: Final[str] = "Sequencer Options"
    SECTION_TILING_SETTINGS: Final[str] = "Tiling Settings"
    SELECT_DIRECTORY_PROMPT: Final[str] = "Select Directory"
    SELECT_FILE_PROMPT: Final[str] = "Select File"
    SELECTED_IMAGE_LABEL: Final[str] = "Selected Image"
    SEQUENCE_NAME_LABEL: Final[str] = "Sequence Name"
    SEQUENCE_NAME_LABEL_DESCRIPTION: Final[str] = (
        "The name of the sequence to run; if empty all sequences will be run."
    )

    @ClassProperty
    def SHORT_TEXT_ENTRY_WIDTH(cls) -> int:
        return int(70 * _global_dpi_scale.factor)

    SS_QUALITY_LABEL: Final[str] = "SS Quality"
    SS_QUALITY_LABEL_DESCRIPTION: Final[str] = (
        "The Super Sampling quality level to apply; note: DLSS quality level takes precedence."
    )
    SS_QUALITY_OPTIONS: Final[List[str]] = ["Off", "Low", "Medium", "High", "Ultra High"]

    @ClassProperty
    def SUBMITTER_DIALOG_WINDOW_DIMENSIONS(cls) -> List[int]:
        return [int(600 * _global_dpi_scale.factor), int(600 * _global_dpi_scale.factor)]

    TILES_IN_X_LABEL: Final[str] = "Tiles In X"
    TILES_IN_X_LABEL_DESCRIPTION: Final[str] = (
        "The number of tiles to horizontally divide the specified image size."
    )
    TILES_IN_Y_LABEL: Final[str] = "Tiles In Y"
    TILES_IN_Y_LABEL_DESCRIPTION: Final[str] = (
        "The number of tiles to vertically divide the specified  image size."
    )
    TIMELINE_ACTION: Final[str] = "Timeline"
    TIMELINE_ANIMATION_PREFS_BUTTON_NAME: Final[str] = "_prefs"
    TIMELINE_TOOLBAR_NAME: Final[str] = "Timeline_Toolbar"
    USE_CLIP_RANGE_LABEL: Final[str] = "Use Clip Range"
    USE_CLIP_RANGE_LABEL_DESCRIPTION: Final[str] = (
        "When enabled, the frame range will be fixed to the range defined by the "
        "selected animation clip."
    )
    USE_GPU_RAY_TRACING_LABEL: Final[str] = "Use GPU Ray Tracing"
    USE_GPU_RAY_TRACING_LABEL_DESCRIPTION: Final[str] = (
        "Attempts to apply GPU raytracing to the rendering process (if sufficient hardware is available)."
    )
    UTF8_FLAG = "utf-8"

    @ClassProperty
    def VERY_LONG_TEXT_ENTRY_WIDTH(cls) -> int:
        return int(280 * _global_dpi_scale.factor)

    @ClassProperty
    def VERY_SHORT_TEXT_ENTRY_WIDTH(cls) -> int:
        return int(50 * _global_dpi_scale.factor)

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
