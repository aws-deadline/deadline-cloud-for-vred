# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Provides backend UI value population and interpretation in ("Job-specific settings")"""

import os

from typing import Any, Dict

from .constants import Constants
from ...data_classes import RenderSubmitterUISettings
from ...utils import bool_to_str, DynamicKeyValueObject
from ...vred_utils import (
    get_active_camera_name,
    get_all_sequences,
    get_animation_clips_list,
    get_frame_range_string,
    get_frame_range_components,
    get_populated_animation_clip_ranges,
    get_render_animation,
    get_render_filename,
    get_scene_full_path,
    get_views_list,
)

from PySide6.QtWidgets import QWidget


class SceneSettingsPopulator:
    """UI value population logic applied to a parent class (SceneSettingsWidget) - defines corresponding UI objects"""

    # Persist setting states between times when the Deadline Cloud submitter dialog is re-opened
    # (for UX purposes: prevents having to re-choose the same options when re-opening that dialog)
    #
    persisted_settings_states: Dict[str, Any] = {}

    def __init__(self, parent_cls: QWidget, initial_settings: RenderSubmitterUISettings) -> None:
        """
        Prepares UI elements with populated render settings values from initial_settings and manages persisted settings.
        param: parent_cls: parent widget containing UI elements.
        param: initial_settings: maintains values for all render submission parameters.
        """
        self.parent = parent_cls
        # Note: values are updated when the submitter dialog is re-opened!
        #
        self.animation_clip_ranges_map = {"": [0.0, 0.0]}
        self._configure_ui_settings_base_options()
        self._configure_ui_settings(initial_settings)
        # Persisted settings will take precedence (in UI elements) over initial settings/defaults
        self._load_persisted_settings_states()

    def _configure_ui_settings(self, settings: RenderSubmitterUISettings) -> None:
        """
        Populates default field values (contained within the settings object) into individual UI widgets
        param: settings: maintains values for all render submission parameters.
        Note: excluded unimplemented settings (not traditionally submitter UI exposed):
           IncludeAlphaChannel, OverrideRenderPass, PremultiplyAlpha, TonemapHDR
        Note: excluded internal settings (not submitter UI exposed):
           JobScriptDir OutputFileNamePrefix, OutputFormat, OutputDir, SceneFile
        Note: excluded (pending implementation changes) - settings exposed as one aggregate field:
           EndFrame, FrameStep, StartFrame
        """
        self.parent.abort_on_missing_tiles_widget.setChecked(settings.AbortOnMissingTiles)
        self.parent.animation_clip_widget.setCurrentText(settings.AnimationClip)
        self.parent.animation_type_widget.setCurrentText(settings.AnimationType)
        self.parent.cleanup_tiles_widget.setChecked(settings.CleanupTilesAfterAssembly)
        self.parent.dlss_quality_widget.setCurrentText(settings.DLSSQuality)
        self.parent.resolution_widget.setText(str(settings.DPI))
        self.parent.frames_per_task_widget.setValue(settings.FramesPerTask)
        self.parent.gpu_ray_tracing_widget.setChecked(settings.GPURaytracing)
        self.parent.image_size_y_widget.setText(str(settings.ImageHeight))
        self.parent.image_size_x_widget.setText(str(settings.ImageWidth))
        self.parent.render_job_type_widget.setCurrentText(settings.JobType)
        self.parent.enable_region_rendering_widget.setChecked(settings.RegionRendering)
        self.parent.render_animation_widget.setChecked(settings.RenderAnimation)
        self.parent.tiles_in_x_widget.setValue(Constants.MIN_TILES_PER_DIMENSION)
        self.parent.tiles_in_y_widget.setValue(Constants.MIN_TILES_PER_DIMENSION)
        self.parent.render_quality_widget.setCurrentText(settings.RenderQuality)
        self.parent.ss_quality_widget.setCurrentText(settings.SSQuality)
        self.parent.sequence_name_widget.setCurrentText(settings.SequenceName)
        self.parent.render_view_widget.setCurrentText(str(settings.View))

    def _configure_ui_settings_base_options(self) -> None:
        """
        Populates runtime-known values and standard option choices into UI elements and resets their state.
        """
        # Initialize job type options
        self.parent.render_job_type_widget.addItems(Constants.JOB_TYPE_OPTIONS)

        # Set output path and frame range
        self.parent.render_output_widget.setText(get_render_filename())
        self.parent.frame_range_widget.setText(get_frame_range_string())
        self.parent.frame_range_widget.setEnabled(False)
        self.parent.render_animation_widget.setChecked(get_render_animation())

        # Configure camera view settings
        views_list = get_views_list()
        self.parent.render_view_widget.addItems(views_list)
        self.parent.render_view_widget.setCurrentIndex(views_list.index(get_active_camera_name()))

        # Animation Clips Support - includes 'empty' clip
        self.parent.animation_clip_widget.setEnabled(False)
        anim_clips_list = get_animation_clips_list()
        if len(anim_clips_list) > 1:
            self.parent.animation_clip_widget.addItems(anim_clips_list)
            # Should be empty clip name at top of list (for no animation clip)
            self.parent.animation_clip_widget.setCurrentIndex(0)
            self.animation_clip_ranges_map = get_populated_animation_clip_ranges()

        # Configure quality settings
        self.parent.render_quality_widget.addItems(Constants.RENDER_QUALITY_OPTIONS)
        self.parent.render_quality_widget.setCurrentIndex(
            self.parent.render_quality_widget.findText(Constants.RENDER_QUALITY_DEFAULT)
        )
        self.parent.dlss_quality_widget.addItems(Constants.DLSS_QUALITY_OPTIONS)
        self.parent.dlss_quality_widget.setCurrentIndex(0)
        self.parent.ss_quality_widget.addItems(Constants.SS_QUALITY_OPTIONS)
        self.parent.ss_quality_widget.setCurrentIndex(0)

        # Set the default image size preset (for image size and resolution)
        image_size_preset_index = 0
        self.parent.image_size_presets_widget.addItems(Constants.IMAGE_SIZE_PRESETS_MAP.keys())
        if Constants.DEFAULT_IMAGE_SIZE_PRESET in Constants.IMAGE_SIZE_PRESETS_MAP:
            image_size_preset_index = list(Constants.IMAGE_SIZE_PRESETS_MAP.keys()).index(
                Constants.DEFAULT_IMAGE_SIZE_PRESET
            )
        self.parent.image_size_presets_widget.setCurrentIndex(image_size_preset_index)
        self.parent.callbacks.image_size_preset_selection_changed_callback()

        # Configure animation settings
        self.parent.animation_type_widget.addItems(Constants.ANIMATION_TYPE_OPTIONS)
        self.parent.animation_type_widget.setCurrentIndex(0)

        # Configure sequencer settings
        self.parent.sequence_name_widget.addItems(get_all_sequences())
        self.parent.sequence_name_widget.setCurrentIndex(0)

    def _load_persisted_settings_states(self) -> None:
        """
        Populates persisted settings states into UI elements (if available)
        """
        try:
            if Constants.RENDER_OUTPUT_LABEL in self.persisted_settings_states:
                self.parent.render_output_widget.setText(
                    self.persisted_settings_states[Constants.RENDER_OUTPUT_LABEL]
                )
            if Constants.IMAGE_SIZE_PRESETS_LABEL in self.persisted_settings_states:
                self.parent.image_size_presets_widget.setCurrentIndex(
                    self.persisted_settings_states[Constants.IMAGE_SIZE_PRESETS_LABEL]
                )
            if Constants.USE_GPU_RAY_TRACING_LABEL in self.persisted_settings_states:
                self.parent.gpu_ray_tracing_widget.setChecked(
                    self.persisted_settings_states[Constants.USE_GPU_RAY_TRACING_LABEL]
                )
            if Constants.JOB_TYPE_LABEL in self.persisted_settings_states:
                self.parent.render_job_type_widget.setCurrentIndex(
                    self.persisted_settings_states[Constants.JOB_TYPE_LABEL]
                )
            if self.parent.render_job_type_widget.currentIndex() == 0:
                if Constants.RENDER_ANIMATION_LABEL in self.persisted_settings_states:
                    self.parent.render_animation_widget.setChecked(
                        self.persisted_settings_states[Constants.RENDER_ANIMATION_LABEL]
                    )
                if Constants.ANIMATION_TYPE_LABEL in self.persisted_settings_states:
                    self.parent.animation_type_widget.setCurrentIndex(
                        self.persisted_settings_states[Constants.ANIMATION_TYPE_LABEL]
                    )
                if Constants.USE_CLIP_RANGE_LABEL in self.persisted_settings_states:
                    self.parent.use_clip_range_widget.setChecked(
                        self.persisted_settings_states[Constants.USE_CLIP_RANGE_LABEL]
                    )
                if Constants.ANIMATION_CLIP_LABEL in self.persisted_settings_states:
                    self.parent.animation_clip_widget.setCurrentIndex(
                        self.persisted_settings_states[Constants.ANIMATION_CLIP_LABEL]
                    )
                if Constants.RENDER_QUALITY_LABEL in self.persisted_settings_states:
                    self.parent.render_quality_widget.setCurrentIndex(
                        self.persisted_settings_states[Constants.RENDER_QUALITY_LABEL]
                    )
                if Constants.SS_QUALITY_LABEL in self.persisted_settings_states:
                    self.parent.ss_quality_widget.setCurrentIndex(
                        self.persisted_settings_states[Constants.SS_QUALITY_LABEL]
                    )
                if Constants.DLSS_QUALITY_LABEL in self.persisted_settings_states:
                    self.parent.dlss_quality_widget.setCurrentIndex(
                        self.persisted_settings_states[Constants.DLSS_QUALITY_LABEL]
                    )
        except Exception:
            pass

    def update_settings_callback(self, settings: RenderSubmitterUISettings) -> None:
        """
        Updates a scene settings object - populates it with the latest UI values using the OpenJD typing convention.
        (This is typically called when Deadline Cloud is exporting or submitting a render job)
        param: settings: maintains values for all render submission parameters.
        Note: important to synchronize to the data fields exposed in template.yaml - matching those to Qt controls.
        Note: if an attribute's value isn't exporting to the parameters YAML, first check that its attribute is
              included in the RenderSubmitterUISettings (settings) dataclass definition.
        Note: some values are set to False defaults - they aren't currently UI exposed or are pending implementation
        Note: some settings like input_filenames, input_directories are determined automatically in AssetIntrospector
        """
        settings.StartFrame, settings.EndFrame, settings.FrameStep = get_frame_range_components(
            self.parent.frame_range_widget.text()
        )
        attrs: Any = DynamicKeyValueObject(settings.__dict__)
        settings.__dict__.update(
            {
                attrs.output_directories.__name__: [
                    os.path.normpath(os.path.dirname(self.parent.render_output_widget.text()))
                ],
                attrs.AbortOnMissingTiles.__name__: bool_to_str(
                    self.parent.abort_on_missing_tiles_widget.isChecked()
                ),
                attrs.AnimationClip.__name__: str(self.parent.animation_clip_widget.currentText()),
                attrs.AnimationType.__name__: str(self.parent.animation_type_widget.currentText()),
                attrs.CleanupTilesAfterAssembly.__name__: bool_to_str(
                    self.parent.cleanup_tiles_widget.isChecked()
                ),
                attrs.DLSSQuality.__name__: str(self.parent.dlss_quality_widget.currentText()),
                attrs.DPI.__name__: int(self.parent.resolution_widget.text()),
                attrs.FramesPerTask.__name__: int(self.parent.frames_per_task_widget.value()),
                attrs.GPURaytracing.__name__: bool_to_str(
                    self.parent.gpu_ray_tracing_widget.isChecked()
                ),
                attrs.ImageHeight.__name__: int(self.parent.image_size_y_widget.text()),
                attrs.ImageWidth.__name__: int(self.parent.image_size_x_widget.text()),
                attrs.IncludeAlphaChannel.__name__: bool_to_str(False),
                attrs.JobType.__name__: str(self.parent.render_job_type_widget.currentText()),
                attrs.NumXTiles.__name__: int(self.parent.tiles_in_x_widget.value()),
                attrs.NumYTiles.__name__: int(self.parent.tiles_in_y_widget.value()),
                attrs.OutputDir.__name__: str(
                    os.path.normpath(os.path.dirname(self.parent.render_output_widget.text()))
                ),
                attrs.OutputFileNamePrefix.__name__: str(
                    os.path.splitext(os.path.basename(self.parent.render_output_widget.text()))[0]
                ),
                attrs.OutputFormat.__name__: str(
                    os.path.splitext(self.parent.render_output_widget.text())[1][1:].upper()
                ),
                attrs.OverrideRenderPass.__name__: bool_to_str(False),
                attrs.PremultiplyAlpha.__name__: bool_to_str(False),
                attrs.RegionRendering.__name__: bool_to_str(
                    self.parent.enable_region_rendering_widget.isChecked()
                ),
                attrs.RenderAnimation.__name__: bool_to_str(
                    self.parent.render_animation_widget.isChecked()
                ),
                attrs.RenderQuality.__name__: str(self.parent.render_quality_widget.currentText()),
                attrs.SSQuality.__name__: str(self.parent.ss_quality_widget.currentText()),
                attrs.SceneFile.__name__: get_scene_full_path(),
                attrs.SequenceName.__name__: str(self.parent.sequence_name_widget.currentText()),
                attrs.TonemapHDR.__name__: bool_to_str(False),
                attrs.View.__name__: str(self.parent.render_view_widget.currentText()),
            }
        )
