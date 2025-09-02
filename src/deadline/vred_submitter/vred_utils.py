# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""VRED-specific Convenience/Utility Functions"""

import re

from pathlib import Path
from typing import Dict, List, Set, Tuple

from .constants import Constants
from .utils import get_normalized_path, is_numerically_defined

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDialog, QMainWindow, QToolBar, QToolButton

from builtins import vrCameraService, vrFileIOService, vrMainWindow, vrReferenceService  # type: ignore[attr-defined]
from vrAnimWidgets import getAnimClips, getAnimClipNodes, getCurrentFrame
from vrController import getVredVersionYear
from vrOSGWidget import (
    getDLSSQuality,
    getRenderWindowHeight,
    getRenderWindowWidth,
    getSuperSamplingQuality,
    VR_QUALITY_ANALYTIC_HIGH,
    VR_QUALITY_ANALYTIC_LOW,
    VR_QUALITY_NPR,
    VR_QUALITY_RAYTRACING,
    VR_QUALITY_REALISTIC_HIGH,
    VR_QUALITY_REALISTIC_LOW,
    VR_SS_QUALITY_HIGH,
    VR_SS_QUALITY_LOW,
    VR_SS_QUALITY_MEDIUM,
    VR_SS_QUALITY_OFF,
    VR_SS_QUALITY_ULTRA_HIGH,
    VR_DLSS_BALANCED,
    VR_DLSS_PERFORMANCE,
    VR_DLSS_OFF,
    VR_DLSS_QUALITY,
    VR_DLSS_ULTRA_PERFORMANCE,
)
from vrRenderSettings import (
    getRaytracingMode,
    getRenderAlpha,
    getRenderAnimation,
    getRenderAnimationClip,
    getRenderAnimationType,
    getRenderFilename,
    getRenderFrameStep,
    getRenderPixelHeight,
    getRenderPixelPerInch,
    getRenderPixelWidth,
    getRenderPremultiply,
    getRenderStartFrame,
    getRenderStopFrame,
    getRenderTonemapHDR,
    getRenderUseClipRange,
    getRenderView,
    getUseRenderRegion,
)
from vrSequencer import getSequenceList

ANIMATION_TYPE_DICT: Dict[int, str] = {0: "Clip", 1: "Timeline"}

DLSS_QUALITY_DICT: Dict[int, str] = {
    VR_DLSS_OFF: "Off",
    VR_DLSS_PERFORMANCE: "Performance",
    VR_DLSS_BALANCED: "Balanced",
    VR_DLSS_QUALITY: "Quality",
    VR_DLSS_ULTRA_PERFORMANCE: "Ultra Performance",
}

RENDER_QUALITY_DICT: Dict[int, str] = {
    VR_QUALITY_ANALYTIC_LOW: "Analytic Low",
    VR_QUALITY_ANALYTIC_HIGH: "Analytic High",
    VR_QUALITY_REALISTIC_LOW: "Realistic Low",
    VR_QUALITY_REALISTIC_HIGH: "Realistic High",
    VR_QUALITY_RAYTRACING: "Raytracing",
    VR_QUALITY_NPR: "NPR",
}

SS_QUALITY_DICT: Dict[int, str] = {
    VR_SS_QUALITY_OFF: "Off",
    VR_SS_QUALITY_LOW: "Low",
    VR_SS_QUALITY_MEDIUM: "Medium",
    VR_SS_QUALITY_HIGH: "High",
    VR_SS_QUALITY_ULTRA_HIGH: "Ultra High",
}


def assign_scene_transition_event(callback_function) -> None:
    """
    Connects scene transition events (new scene and project load) to a callback function
    param: callback_function: function to invoke during scene transition events
    """
    vrFileIOService.newScene.connect(callback_function)
    vrFileIOService.projectLoad.connect(callback_function)


def get_active_camera_name() -> str:
    """
    Returns the name of the active camera
    return: name of the active camera
    """
    return vrCameraService.getActiveCamera().getName()


def get_animation_clips_list() -> List[str]:
    """
    Returns a sorted list of the names of animation clips in the scene
    return: sorted list of the names of animation clips
    """
    return [""] + sorted(getAnimClips())


def get_dlss_quality() -> str:
    """
    Returns the DLSS quality value
    return: DLSS quality value
    """
    return DLSS_QUALITY_DICT.get(getDLSSQuality(), "")


def get_supersampling_quality() -> str:
    """
    Returns the supersampling quality value
    return: supersampling quality value
    """
    return SS_QUALITY_DICT.get(getSuperSamplingQuality(), "")


def get_render_pixel_height() -> int:
    """
    Returns the pixel height for rendering
    return: pixel height value
    """
    return getRenderPixelHeight()


def get_render_pixel_width() -> int:
    """
    Returns the pixel height for rendering
    return: pixel height value
    """
    return getRenderPixelWidth()


def get_frame_range_string() -> str:
    """
    Returns a formatted string representing the current frame range configuration.
    Examples include:
        "1" (single frame),
        "1-100" (100 consecutive frames),
        "1-100x2" (frames 1,3,5,....99) - specific subset of frames within a sequence
    return: formatted frame range string
    """
    start_frame = getRenderStartFrame()
    end_frame = getRenderStopFrame()
    frame_step = getRenderFrameStep()
    frame_string = str(start_frame)
    if start_frame != end_frame:
        frame_string = f"{frame_string}-{str(end_frame)}"
        if frame_step > 1:
            frame_string = f"{frame_string}x{str(frame_step)}"
    return frame_string


def get_frame_current() -> int:
    """
    return: the current frame number
    """
    return getCurrentFrame()


def get_frame_start() -> int:
    """
    return: the current starting frame number
    """
    return getRenderStartFrame()


def get_frame_stop() -> int:
    """
    return: the current stopping frame number
    """
    return getRenderStopFrame()


def get_frame_step() -> int:
    """
    return: the current frame step value
    """
    return getRenderFrameStep()


def get_main_window() -> QMainWindow:
    """
    return: VRED main window
    """
    return vrMainWindow


def get_major_version() -> int:
    """
    return: VRED version year
    """
    return getVredVersionYear()


def get_populated_animation_clip_ranges() -> Dict[str, List[float]]:
    """
    return: a dictionary containing animation clip names as keys and their corresponding clip ranges as values
    in the format [start_frame, end_frame].
    """
    animation_clip_ranges_map = {"": [0.0, 0.0]}
    render_fps = get_scene_fps()
    # Are there referenced animation clips? Or a raw animation clip? (AnimWizClip or AnimBlock types.)
    #
    for anim_clip in getAnimClipNodes():
        clip_name = anim_clip.getName()
        # Extract the AnimClip's volume attribute's min x to max x (this encodes the start and end range)
        #
        start_range = anim_clip.getBoundingBox()[0]
        end_range = anim_clip.getBoundingBox()[3]

        # Calculate the animation clip ranges
        #
        animation_clip_ranges_map[clip_name] = [0.0, 0.0]
        if is_numerically_defined(str(start_range)) and is_numerically_defined(str(end_range)):
            duration = end_range - start_range
            clip_min = start_range * render_fps
            clip_max = clip_min + (duration * render_fps)
            animation_clip_ranges_map[clip_name] = [clip_min, clip_max]
    return animation_clip_ranges_map


def get_all_file_references() -> Set[Path]:
    """
    return: a set of all references in the scene
    """
    return {
        Path(path)
        for node in vrReferenceService.getSceneReferences()
        for path in (
            get_normalized_path(node.getSourcePath()),
            get_normalized_path(node.getSmartPath()),
        )
        if path
    }


def get_all_sequences() -> List[str]:
    """
    return: a sorted list of all sequence names in the scene
    """
    return sorted(getSequenceList())


def get_animation_clip() -> str:
    """
    return: the name of the current animation clip
    """
    return getRenderAnimationClip()


def get_animation_type() -> str:
    """
    return: the type of the current animation
    """
    return ANIMATION_TYPE_DICT.get(getRenderAnimationType(), "")


def get_render_window_size() -> List[int]:
    """
    return: width and height of the render window
    """
    return [getRenderWindowWidth(0), getRenderWindowHeight(0)]


def get_scene_full_path() -> str:
    """
    return: full path of the current scene file
    """
    return get_normalized_path(vrFileIOService.getFileName())


def get_scene_fps() -> float:
    """
    Get scene-file specific FPS count value.
    Note: This value is not directly exposed in the API; UI inspection is applied as a workaround.
    return: FPS count (assumes DEFAULT_SCENE_FILE_FPS_COUNT if FPS can't be determined).
    """
    timeline_action = None
    timeline_was_visible = False

    try:
        # Find the timeline object
        timeline_action = next(
            (
                obj
                for obj in vrMainWindow.findChildren(QAction)
                if obj.text() == Constants.TIMELINE_ACTION
            ),
            None,
        )
        if not timeline_action:
            raise LookupError(Constants.ERROR_TIMELINE_ACTION_NOT_FOUND)

        # Maintain timeline visibility state
        timeline_was_visible = timeline_action.isChecked()
        if not timeline_was_visible:
            timeline_action.activate(QAction.Trigger)

        # Find toolbar within timeline
        timeline_toolbar = next(
            (
                obj
                for obj in vrMainWindow.findChildren(QToolBar)
                if obj.objectName() == Constants.TIMELINE_TOOLBAR_NAME
            ),
            None,
        )
        if not timeline_toolbar:
            raise LookupError(Constants.ERROR_TIMELINE_TOOLBAR_NOT_FOUND)

        # Find and click preferences button toolbar
        prefs_button = next(
            (
                obj
                for obj in timeline_toolbar.findChildren(QToolButton)
                if obj.objectName() == Constants.TIMELINE_ANIMATION_PREFS_BUTTON_NAME
            ),
            None,
        )
        if not prefs_button:
            raise LookupError(Constants.ERROR_PREFERENCES_BUTTON_NOT_FOUND)

        prefs_button.click()

        # In the animation settings dialog, get the FPS value from settings dialog
        animation_settings_widget = vrMainWindow.findChild(
            QDialog, Constants.ANIMATION_SETTINGS_DIALOG
        )
        if not animation_settings_widget:
            raise LookupError(Constants.ERROR_ANIMATION_SETTINGS_DIALOG_NOT_FOUND)

        animation_settings_widget.hide()

        speed_widget = animation_settings_widget.findChild(QObject, Constants.CUSTOM_SPEED_NAME)
        if not speed_widget:
            raise LookupError(Constants.ERROR_SPEED_SETTINGS_WIDGET_NOT_FOUND)
        return float(speed_widget.text().split()[0])

    except (LookupError, IndexError, ValueError):
        return Constants.DEFAULT_SCENE_FILE_FPS_COUNT

    finally:
        # Always restore timeline visibility to its original state
        if timeline_action and not timeline_was_visible:
            timeline_action.activate(QAction.Trigger)


def get_render_alpha() -> bool:
    """
    return: True if an alpha channel should be exported; False otherwise.
    """
    return getRenderAlpha()


def get_render_animation() -> bool:
    """
    Get the render animation state.
    return: True if render animation is enabled; False otherwise.
    """
    return getRenderAnimation()


def get_render_pixel_per_inch() -> int:
    """
    Get the render pixel per inch value.
    return: pixel per inch value
    """
    return int(getRenderPixelPerInch())


def get_render_view() -> str:
    """
    Get the current render view (camera name).
    return: name of current render view
    """
    return getRenderView()


def get_render_filename() -> str:
    """
    return: filename of the image sequence to render
    """
    return get_normalized_path(getRenderFilename())


def get_premultiply_alpha() -> bool:
    """
    return: True if premultiplied alpha is enabled; False otherwise.
    """
    return getRenderPremultiply()


def get_tonemap_hdr() -> bool:
    """
    return: True if Tonemap HDR is enabled; False otherwise.
    """
    return getRenderTonemapHDR()


def get_use_clip_range() -> bool:
    """
    return: True if clip range is enabled; False otherwise.
    """
    return getRenderUseClipRange()


def get_use_gpu_ray_tracing() -> bool:
    """
    return: True if GPU raytracing is enabled, False otherwise
    """
    return getRaytracingMode()


def get_use_render_region() -> bool:
    """
    return: True if render region is enabled; False otherwise.
    """
    return getUseRenderRegion()


def get_views_list() -> List[str]:
    """
    Retrieves a sorted list of unique view names that are either cameras or viewpoints, but not both.
    Note: assumes there aren't identical camera names for now; could rely on an index or getPath()
    return: sorted list of view names that are either cameras or viewpoints, but not both.
    """
    camera_name_list = [camera.getName() for camera in vrCameraService.getCameras()]
    viewpoint_name_list = [vp.getName() for vp in vrCameraService.getAllViewpoints()]
    return sorted(set(camera_name_list).symmetric_difference(set(viewpoint_name_list)))


def is_scene_file_modified() -> bool:
    """
    Check if the current scene file has been modified.
    Examines the main window title to determine if the scene has unsaved changes (denoted with asterisk (*)).
    return: True if the scene has been modified; False otherwise.
    """
    return bool(re.findall(r"\*", get_main_window().windowTitle()))


def save_scene_file(filename: str) -> None:
    """
    Save the current scene to a file.
    param: filename: the path to the file to save the scene
    """
    if not filename:
        return
    vrFileIOService.saveFile(get_normalized_path(filename))


def get_frame_range_components(frame_string: str) -> Tuple[int, int, int]:
    """
    Extracts the frame range components from a given frame string.
    The current supported frame string format is expected to be one of the following:
    - "a-bxn" where a is start frame, b is end frame, n is the frame step
    - "a-b" where a is start frame, b is end frame (frame step defaults to 1)
    - "a" where a is a single frame (start frame==end frame, frame step defaults to 1)
    Note: negative frame numbers are supported in all positions.
    param: frame_string: the frame string to parse
    raise: ValueError: when the frame string format is invalid
    return: the deduced start frame, end frame, frame step
    """
    # Case: single frame
    if Constants.FRAME_START_STOP_DELIMITER not in frame_string:
        try:
            frame = int(frame_string)
            return frame, frame, 1
        except ValueError:
            raise ValueError(f"{Constants.ERROR_FRAME_RANGE_FORMAT_INVALID}: {frame_string}")

    # Case: frame range with optional step
    match = re.match(Constants.FRAME_RANGE_FORMAT_REGEX, frame_string)

    if not match:
        raise ValueError(f"{Constants.ERROR_FRAME_RANGE_FORMAT_INVALID}: {frame_string}")

    start_frame, end_frame = int(match.group(1)), int(match.group(2))

    # If step is specified, use it; otherwise default to 1
    step = int(match.group(3)) if match.group(3) else 1

    return start_frame, end_frame, step
