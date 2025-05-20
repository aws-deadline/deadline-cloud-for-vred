# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Defines the render script (part of a job bundle) that's invoked by a worker node on the Deadline Cloud."""

import json
import logging
import os
import traceback

from dataclasses import dataclass
from enum import auto, IntEnum, StrEnum
from typing import Any, Dict, List

from builtins import vrCameraService, vrReferenceService  # type: ignore[attr-defined]
from vrController import crashVred, terminateVred
from vrOSGWidget import (
    enableRaytracing,
    isDLSSSupported,
    setDLSSQuality,
    setRenderQuality,
    setSuperSampling,
    setSuperSamplingQuality,
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
from vrRenderQueue import runAllRenderJobs
from vrRenderSettings import (
    setRaytracingMode,
    setRaytracingRenderRegion,
    setRenderAlpha,
    setRenderAnimation,
    setRenderAnimationClip,
    setRenderAnimationFormat,
    setRenderAnimationType,
    setRenderFilename,
    setRenderFrameStep,
    setRenderPixelResolution,
    setRenderPremultiply,
    setRenderRegionEndX,
    setRenderRegionEndY,
    setRenderRegionStartX,
    setRenderRegionStartY,
    setRenderStartFrame,
    setRenderStopFrame,
    setRenderSupersampling,
    setRenderTonemapHDR,
    setRenderUseClipRange,
    setRenderView,
    setUseRenderPasses,
    setUseRenderRegion,
    startRenderToFile,
)
from vrSequencer import runAllSequences, runSequence


class DynamicKeyValueObject:
    def __init__(self, data_dict: Dict[str, Any]) -> None:
        """
        Assigns attributes and values to this object that reflect the contents of data_dict
        param: data_dict: attributes/properties and values
        """
        for k, v in data_dict.items():
            setattr(self, k, v)


class JobType(StrEnum):
    RENDER_QUEUE = "Render Queue"
    SEQUENCER = "Sequencer"
    RENDER = "Render"


class AnimationFormat(IntEnum):
    IMAGE = 0
    VIDEO = 1


class CurrentState(IntEnum):
    Off = 0
    On = 1


@dataclass
class PathMappingRule:
    source_path_format: str
    """The path format associated with the source path (windows vs posix)"""

    source_path: str
    """The path we're looking to change"""

    destination_path: str
    """The path to transform the source path to"""


class PathFormat(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name

    WINDOWS = auto()
    POSIX = auto()


class DeadlineCloudRenderer:
    # Enable when not debugging
    #
    WANT_VRED_TERMINATION_ON_ERROR = True

    LOGGING_FORMAT = "%(levelname)s - %(message)s"
    LOGGING_LEVEL = logging.DEBUG

    FRAME_STEP_DEFAULT = 1

    ANIMATION_TYPE_DICT = {"Clip": 0, "Timeline": 1}

    RENDER_QUALITY_DICT = {
        "Analytic Low": VR_QUALITY_ANALYTIC_LOW,
        "Analytic High": VR_QUALITY_ANALYTIC_HIGH,
        "Realistic Low": VR_QUALITY_REALISTIC_LOW,
        "Realistic High": VR_QUALITY_REALISTIC_HIGH,
        "Raytracing": VR_QUALITY_RAYTRACING,
        "NPR": VR_QUALITY_NPR,
    }

    SS_QUALITY_DICT = {
        "Off": VR_SS_QUALITY_OFF,
        "Low": VR_SS_QUALITY_LOW,
        "Medium": VR_SS_QUALITY_MEDIUM,
        "High": VR_SS_QUALITY_HIGH,
        "Ultra High": VR_SS_QUALITY_ULTRA_HIGH,
    }

    DLSS_QUALITY_DICT = {
        "Off": VR_DLSS_OFF,
        "Performance": VR_DLSS_PERFORMANCE,
        "Balanced": VR_DLSS_BALANCED,
        "Quality": VR_DLSS_QUALITY,
        "Ultra Performance": VR_DLSS_ULTRA_PERFORMANCE,
    }

    AWS_COMMAND = "aws"
    AWS_DEADLINE_UPDATE_JOB_PARAMETER = "deadline update-job"
    AWS_JOB_FAIL_STATUS = "FAILED"

    ERROR_INVALID_ANIMATION_TYPE = "Invalid animation type"
    ERROR_INVALID_RENDER_QUALITY = "Invalid render quality"
    ERROR_INVALID_SS_QUALITY = "Invalid Supersampling quality"
    ERROR_INVALID_DLSS_QUALITY = "Invalid DLSS quality"

    PATH_MAPPING_RULES_FIELD = "path_mapping_rules"

    RENDER_REGION_FIELD_NAME = "_region_"

    COMMAND_INVOCATION_TIMEOUT_SECONDS = 8

    def __init__(self, render_parameters_dict: Dict[str, Any]) -> None:
        """
        Initializes the Deadline Cloud for VRED logging and render parameters (prior to applying them later)
        param: render_parameters_dict: a dictionary containing the render parameters
        """
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            format=DeadlineCloudRenderer.LOGGING_FORMAT, level=DeadlineCloudRenderer.LOGGING_LEVEL
        )
        self.path_mapping_rules: List[PathMappingRule] = []
        self.render_parameters: Any = DynamicKeyValueObject(render_parameters_dict)
        output_directory = self.render_parameters.OutputDir.strip().replace("\\", "/")
        output_file_prefix = self.render_parameters.OutputFileNamePrefix.strip()
        output_file_suffix = self.render_parameters.OutputFormat.strip().lower()
        output_file_render_region_prefix = ""
        if self.render_parameters.RegionRendering:
            output_file_render_region_prefix = (
                f"{self.RENDER_REGION_FIELD_NAME}{self.render_parameters.TileNumberY}x"
                f"{self.render_parameters.TileNumberX}_{self.render_parameters.NumYTiles}"
                f"x{self.render_parameters.NumXTiles}"
            )
        self.output_filename = os.path.join(
            output_directory,
            f"{output_file_prefix}{output_file_render_region_prefix}.{output_file_suffix}",
        )

    def validate_parameter_in_dict(
        self, parameter_name: str, dictionary: Dict, error_message: str
    ) -> None:
        """
        Validates the existence of a parameter in a dictionary.
        If the parameter is not found, logs an error and raises a ValueError.
        param parameter_name: name of parameter
        param dictionary: dictionary to check for parameter_name as a key name
        param error_message: message to print when parameter_name is absent in dictionary's keys
        raises: ValueError: if parameter_name absent in dictionary's keys
        """
        if parameter_name not in dictionary:
            self.logger.error(f"{error_message}: {parameter_name}")
            raise ValueError(f"{error_message}: {parameter_name}")

    def validate_render_settings(self) -> None:
        """
        Validates the values of specific rendering-related settings
        raises: ValueError: if a render setting violates its constraints
        return: None
        """
        self.logger.info("Validating render settings")

        self.validate_parameter_in_dict(
            self.render_parameters.RenderQuality,
            DeadlineCloudRenderer.RENDER_QUALITY_DICT,
            DeadlineCloudRenderer.ERROR_INVALID_RENDER_QUALITY,
        )
        self.validate_parameter_in_dict(
            self.render_parameters.SSQuality,
            DeadlineCloudRenderer.SS_QUALITY_DICT,
            DeadlineCloudRenderer.ERROR_INVALID_SS_QUALITY,
        )
        self.validate_parameter_in_dict(
            self.render_parameters.DLSSQuality,
            DeadlineCloudRenderer.DLSS_QUALITY_DICT,
            DeadlineCloudRenderer.ERROR_INVALID_DLSS_QUALITY,
        )
        self.validate_parameter_in_dict(
            self.render_parameters.AnimationType,
            DeadlineCloudRenderer.ANIMATION_TYPE_DICT,
            DeadlineCloudRenderer.ERROR_INVALID_ANIMATION_TYPE,
        )
        if self.render_parameters.StartFrame > self.render_parameters.EndFrame:
            raise ValueError("StartFrame exceeds EndFrame")

    def init_sequencer_job(self) -> None:
        """
        Initializes settings related to Sequencer-typed jobs
        """
        sequence_name = self.render_parameters.SequenceName
        if not sequence_name:
            self.logger.info("Starting to run all Sequences")
            runAllSequences()
        else:
            self.logger.info(f"Starting to run the following sequence: {sequence_name}")
            runSequence(sequence_name)

    def init_render_quality_modes(self):
        """
        Initializes settings related to render quality modes
        """
        setRenderQuality(
            DeadlineCloudRenderer.RENDER_QUALITY_DICT[self.render_parameters.RenderQuality]
        )
        supersampling_quality = DeadlineCloudRenderer.SS_QUALITY_DICT[
            self.render_parameters.SSQuality
        ]
        dlss_quality = DeadlineCloudRenderer.DLSS_QUALITY_DICT[self.render_parameters.DLSSQuality]
        dlss_quality_applied = False
        if (dlss_quality is not VR_DLSS_OFF) and isDLSSSupported():
            self.logger.info(f"DLSS quality set to {dlss_quality}")
            setDLSSQuality(
                DeadlineCloudRenderer.DLSS_QUALITY_DICT[self.render_parameters.DLSSQuality]
            )
            dlss_quality_applied = True
        if supersampling_quality is not VR_SS_QUALITY_OFF:
            if dlss_quality_applied:
                self.process_warning(
                    "DLSS is already enabled. Non-DLSS Supersampling will be ignored."
                )
            else:
                setSuperSamplingQuality(
                    DeadlineCloudRenderer.SS_QUALITY_DICT[self.render_parameters.SSQuality]
                )
                self.logger.info(f"Supersampling quality set to {supersampling_quality}")
                setSuperSampling(CurrentState.On)
        self.logger.info(f"GPU Raytracing to {self.render_parameters.GPURaytracing}")
        enableRaytracing(bool(self.render_parameters.GPURaytracing))
        setRaytracingMode(self.render_parameters.GPURaytracing)

    def init_render_job(self) -> None:
        """
        Initializes settings related to Render-typed jobs
        """
        self.init_camera_view(self.render_parameters.View)
        self.init_render_quality_modes()

        setRenderPixelResolution(
            self.render_parameters.ImageWidth,
            self.render_parameters.ImageHeight,
            self.render_parameters.DPI,
        )

        setRenderAnimation(self.render_parameters.RenderAnimation)
        if self.render_parameters.RenderAnimation:
            self.init_render_animation()

        setRenderAlpha(self.render_parameters.IncludeAlphaChannel)

    def init_camera_view(self, view_name: str) -> None:
        """
        Initializes the camera view, which may be a viewpoint or camera
        If view_name is empty, then the scene file's current active view (i.e. getRenderView()=="Current") will remain,
        which is typically the default (Perspective) camera.
        param: view_name: the name of the viewport or camera.
        """
        if view_name:
            # Consider the camera or view name and use it for rendering. In case of an identically-named camera
            # and viewpoint, have that viewpoint take precedence over the camera.
            #
            view_list = [vp.getName() for vp in vrCameraService.getAllViewpoints()]
            cam_list = vrCameraService.getCameraNames()
            if view_name in view_list:
                self.logger.info(f'Found viewpoint "{view_name}" in view list.')
                setRenderView(view_name)
                vrCameraService.getViewpoint(view_name).activate()
            elif view_name in cam_list:
                self.logger.info(f'Found camera "{view_name}" in view list.')
                setRenderView(view_name)
                vrCameraService.getCamera(view_name).activate()
            else:
                self.process_warning(
                    f'Could not find the specified camera or viewpoint name "{view_name}".'
                )

    def init_render_animation(self) -> None:
        """
        Initializes render settings related to animations
        """
        setRenderStartFrame(self.render_parameters.StartFrame)
        setRenderStopFrame(self.render_parameters.EndFrame)
        setRenderFrameStep(self.render_parameters.FrameStep)
        setRenderAnimationFormat(AnimationFormat.IMAGE)
        setRenderAnimationType(
            DeadlineCloudRenderer.ANIMATION_TYPE_DICT[self.render_parameters.AnimationType]
        )
        setRenderAnimationClip(self.render_parameters.AnimationClip)
        # Tech note: when Supersampling is disabled, it can potentially render a black noisy frame when the GUI isn't
        # available (i.e. on Linux) for some scene files and not others. Enables basic antialiasing.
        #
        setRenderSupersampling(CurrentState.On)
        # Note: if enabled, then each task will render each of the specified frames, versus distributing them among
        # different tasks. Even when deriving the frame range from the clip, it's instructed to not render the entire
        # clip. Instead, the frame range to be rendered is provided if the clip range is used.
        #
        setRenderUseClipRange(False)

    def init_override_render_passes(self) -> None:
        """
        Initializes render settings related to overriding render passes
        """
        setUseRenderPasses(self.render_parameters.ExportRenderPasses)
        # TODO: reintroduce logic for render passes
        #

    def init_common_features(self) -> None:
        """
        Initializes render settings common to all render jobs
        """
        setRenderPremultiply(self.render_parameters.PremultiplyAlpha)
        setRenderTonemapHDR(self.render_parameters.TonemapHDR)

    def load_path_mapping_rules(self) -> bool:
        """
        Loads path mapping rules
        Returns True if successful; False otherwise
        """
        file_handle = None
        try:
            file_handle = open(self.render_parameters.PathMappingRulesFile, "r")
        except Exception as exc:
            self.logger.error(exc)
            return False
        else:
            with file_handle:
                data = json.load(file_handle)
                self.path_mapping_rules = [
                    PathMappingRule(**mapping)
                    for mapping in data.get(self.PATH_MAPPING_RULES_FIELD)
                ]
        finally:
            if file_handle and not file_handle.closed:
                file_handle.close()
        return True

    def map_path(self, path) -> str:
        """
        Maps the given path to the appropriate destination path based on established path mapping rules.
        Loads mapping rules if absent.
        param: path: the path to be mapped.
        return: the mapped destination path; note: this may be the same path if there is no appropriate mapping.
        """
        if not self.path_mapping_rules and not self.load_path_mapping_rules():
            return path
        for rule in self.path_mapping_rules:
            in_path = os.path.normpath(path)
            source_path = os.path.normpath(rule.source_path)
            in_path_norm = in_path.replace("\\", "/")
            source_path_norm = source_path.replace("\\", "/")
            # Check if path starts with source path (case-insensitive for Windows)
            if (
                rule.source_path_format == PathFormat.WINDOWS
                and in_path_norm.lower().startswith(source_path_norm.lower())
            ) or (
                rule.source_path_format == PathFormat.POSIX
                and in_path_norm.startswith(source_path_norm)
            ):
                dest_path = os.path.normpath(rule.destination_path)
                return os.path.normpath(f"{dest_path}{os.sep}{in_path[len(source_path):]}").replace(
                    "\\", os.sep
                )
        return path

    def init_file_references(self) -> None:
        """
        Initializes file references for the render job
        """
        for node in vrReferenceService.getSceneReferences():
            if node.hasSmartReference():
                orig_path = node.getSmartPath()
                node.setSmartPath(self.map_path(orig_path))
            else:
                orig_path = node.getSourcePath()
                node.setSourcePath(self.map_path(orig_path))

    def init_render_region(self) -> None:
        """
        Initializes render region settings
        - these are used for tile-rendering purposes, where the regions (sizes) are automatically computed
        - separate render jobs are normally generated for individual tile rendering tasks
        """
        setUseRenderRegion(self.render_parameters.RegionRendering)
        if self.render_parameters.RegionRendering:
            tile_num_x = self.render_parameters.TileNumberX
            tile_num_y = self.render_parameters.TileNumberY
            num_x_tiles = self.render_parameters.NumXTiles
            num_y_tiles = self.render_parameters.NumYTiles
            delta_x, width_remainder = divmod(self.render_parameters.ImageWidth, num_x_tiles)
            delta_y, height_remainder = divmod(self.render_parameters.ImageHeight, num_y_tiles)
            # Calculate the bounds for the tile.
            left = delta_x * (tile_num_x - 1)
            right = (delta_x * tile_num_x) - 1
            bottom = delta_y * (tile_num_y - 1)
            top = (delta_y * tile_num_y) - 1
            # Add any remainder to the last row and column
            if tile_num_x == num_x_tiles:
                right += width_remainder
            if tile_num_y == num_y_tiles:
                top += height_remainder
            setRenderRegionStartX(left)
            setRenderRegionEndX(right)
            setRenderRegionStartY(bottom)
            setRenderRegionEndY(top)
            # Sets active render region per: setRaytracingRenderRegion(xBegin, yBegin, xEnd, yEnd)
            # Each parameter is a relative normalized coordinate in [0.0,1.0].
            left = float(left) / self.render_parameters.ImageWidth
            right = float(right) / self.render_parameters.ImageWidth
            bottom = float(bottom) / self.render_parameters.ImageHeight
            top = float(top) / self.render_parameters.ImageHeight
            setRaytracingRenderRegion(left, 1 - top, right, 1 - bottom)
            enableRaytracing(True)

    def init_by_job_type(self) -> None:
        """
        Initializes render settings by render job type
        """
        job_type = self.render_parameters.JobType
        if job_type == JobType.RENDER_QUEUE:
            self.logger.info("Starting to render all jobs in the render queue")
            runAllRenderJobs()
        elif job_type == JobType.SEQUENCER:
            self.init_sequencer_job()
        elif job_type == JobType.RENDER:
            self.init_render_job()

    def init_render_settings(self) -> None:
        """
        High-level render settings initialization method (applies via VRED API)
        """
        self.init_by_job_type()

        if self.render_parameters.OverrideRenderPass:
            self.init_override_render_passes()

        self.init_common_features()
        self.init_render_region()

        setRenderFilename(self.output_filename)

    def process_warning(self, message) -> None:
        """
        Logs a warning message and raises a ValueError if JobFailureOnWarnings is True
        param: message: warning message to log and raise
        raises: ValueError: if JobFailureOnWarnings is True
        """
        self.logger.warning(message)
        if self.render_parameters.JobFailureOnWarnings:
            raise ValueError(message)

    def render(self) -> None:
        """
        High-level render initiation routine with error handling
        """
        try:
            self.validate_render_settings()
            self.init_file_references()
            self.init_render_settings()
            self.logger.info("Starting Render")
            startRenderToFile(True)
            # Important to close VRED for further frame rendering to proceed, release license
            #
            terminateVred()
        except Exception as exc:
            self.logger.error(exc)
            self.logger.error(traceback.format_exc())
            if DeadlineCloudRenderer.WANT_VRED_TERMINATION_ON_ERROR:
                crashVred(1)
        finally:
            if DeadlineCloudRenderer.WANT_VRED_TERMINATION_ON_ERROR:
                terminateVred()


def deadline_cloud_render(render_parameters_dict: Dict[str, Any]) -> None:
    """
    Main entry point (to be called externally from VRED "postpython" argument):
    - reads render parameters and values from a dictionary (render_parameters_dict)
    - applies render parameter values via VRED API
    - initiates rendering process with error handling
    param: render_parameters_dict: a dictionary containing the render parameters and values
    """
    if render_parameters_dict:
        renderer = DeadlineCloudRenderer(render_parameters_dict)
        renderer.render()
