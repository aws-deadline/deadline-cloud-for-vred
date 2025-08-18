# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Provides backend UI value population and interpretation in ("Job-specific settings")"""

import os

from enum import auto
from typing import Any

from .constants import Constants
from ...data_classes import RenderSubmitterUISettings
from ...utils import (
    DynamicKeyValueObject,
    DynamicKeyNamedValueObject,
    StrEnum,
    get_normalized_path,
    get_file_name_path_components,
)
from ...vred_utils import (
    get_all_sequences,
    get_animation_clip,
    get_animation_clips_list,
    get_animation_type,
    get_dlss_quality,
    get_frame_start,
    get_frame_step,
    get_frame_stop,
    get_frame_range_components,
    get_populated_animation_clip_ranges,
    get_premultiply_alpha,
    get_render_alpha,
    get_render_animation,
    get_render_filename,
    get_render_pixel_height,
    get_render_pixel_per_inch,
    get_render_pixel_width,
    get_render_view,
    get_scene_full_path,
    get_supersampling_quality,
    get_tonemap_hdr,
    get_use_render_region,
    get_use_gpu_ray_tracing,
    get_views_list,
)

from PySide6.QtWidgets import QWidget


class PersistedUISettingsNames(StrEnum):
    """
    Refers to UI elements to track (for persisting their settings/states between submitter dialog sessions)
    """

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list) -> str:
        return name.lower()

    ANIMATION_TYPE = auto()
    ANIMATION_CLIP = auto()
    DLSS_QUALITY = auto()
    ENABLE_RENDER_REGIONS = auto()
    FRAME_RANGE = auto()
    FRAMES_PER_TASK = auto()
    JOB_TYPE = auto()
    IMAGE_SIZE_X = auto()
    IMAGE_SIZE_Y = auto()
    RENDER_ANIMATION = auto()
    RESOLUTION = auto()
    RENDER_QUALITY = auto()
    RENDER_OUTPUT = auto()
    SEQUENCE_NAME = auto()
    SS_QUALITY = auto()
    TILES_IN_X = auto()
    TILES_IN_Y = auto()
    USE_CLIP_RANGE = auto()
    USE_GPU_RAY_TRACING = auto()
    VIEW = auto()


class SceneSettingsPopulator:
    """UI value population logic applied to a parent class (SceneSettingsWidget) - defines corresponding UI objects"""

    # Initializes persisted setting ui state storage; persists between the times when the Deadline Cloud submitter
    # dialog is re-opened (for UX purposes: prevents having to re-choose the same options when re-opening that dialog)
    # Intended for easy attribute access - i.e.: persisted_ui_settings_states.ss_quality="value". Settings reset
    # when the next scene file is opened.
    #
    persisted_ui_settings_states: Any = None

    def __init__(self, parent_cls: QWidget, initial_settings: RenderSubmitterUISettings) -> None:
        """
        Prepares UI elements with populated render settings values from initial_settings and manages persisted settings.
        param: parent_cls: parent widget containing UI elements.
        param: initial_settings: maintains values for all render submission parameters.
        """
        self.parent = parent_cls
        # Note: valid values are updated when the submitter dialog is re-opened
        #
        self.animation_clip_ranges_map = {"": [0.0, 0.0]}
        # Is the same scene file being used? Need to re-initialize persisted settings?
        # See: SceneSettingsCallbacks.scene_file_changed_callback()
        #
        if SceneSettingsPopulator.persisted_ui_settings_states is None:
            # Initialize persisted settings storage
            SceneSettingsPopulator.persisted_ui_settings_states = DynamicKeyValueObject(
                {str(key).lower(): "" for key in PersistedUISettingsNames}
            )
            # Capture sticky settings from initial_settings before they get overwritten
            SceneSettingsPopulator._configure_ui_persisted_settings(initial_settings)
            # Now get VRED scene values (this will overwrite initial_settings but we've already captured the sticky values)
            self._store_runtime_derived_settings(initial_settings)
        self._populate_runtime_ui_options_values(initial_settings)
        # Persisted settings will take precedence (in UI elements) over initial settings/defaults
        self._restore_persisted_ui_settings_states()

    def populate_post_ui_setup(self):
        """
        Triggers UI callbacks (after UI values applied - without callbacks emitting) to adjust neighboring UI control
        states in response and register correct states in those controls. Order of callback triggering will matter.
        """
        self.parent.enable_region_rendering_widget.stateChanged.emit(
            self.parent.enable_region_rendering_widget.checkState()
        )
        self.parent.render_animation_widget.stateChanged.emit(
            self.parent.render_animation_widget.checkState()
        )
        self.parent.animation_type_widget.currentIndexChanged.emit(
            self.parent.animation_type_widget.currentIndex()
        )
        self.parent.callbacks._update_image_presets_selection(
            int(self.parent.image_size_x_widget.text()),
            int(self.parent.image_size_y_widget.text()),
            int(self.parent.resolution_widget.text()),
        )
        # UX: keep uniform widget width for widgets known to contain fixed element content
        widgets = [
            self.parent.render_quality_widget,
            self.parent.dlss_quality_widget,
            self.parent.ss_quality_widget,
            self.parent.animation_type_widget,
            self.parent.image_size_presets_widget,
        ]
        max_width = max(widget.get_width() for widget in widgets)
        [widget.set_width(max_width) for widget in widgets]
        self.parent.animation_clip_widget.setFixedWidth(max_width)

    @staticmethod
    def _store_runtime_derived_settings(settings: RenderSubmitterUISettings) -> None:
        """
        Intended as a one-time call per scene file session. Initializes render settings values from the stock render
        settings - they provide default values for the submitter (initially). Then, any changes made to the submitter
        UI settings will override the stock settings in VRED upon submission.
        Note: there isn't any synchronization of values occurring except during the initial opening of the submitter
        in a new scene file session.
        param: settings: maintains values for all render submission parameters.
        """
        directory, filename_prefix, extension = get_file_name_path_components(get_render_filename())
        settings.AnimationClip = get_animation_clip()
        settings.AnimationType = get_animation_type()
        settings.DPI = get_render_pixel_per_inch()
        settings.DLSSQuality = get_dlss_quality()
        settings.EndFrame = get_frame_stop()
        settings.FrameStep = get_frame_step()
        settings.GPURaytracing = get_use_gpu_ray_tracing()
        settings.ImageHeight = get_render_pixel_height()
        settings.ImageWidth = get_render_pixel_width()
        settings.OutputDir = directory
        settings.OutputFileNamePrefix = filename_prefix
        settings.OutputFormat = extension.upper()
        settings.RenderAnimation = get_render_animation()
        settings.RegionRendering = get_use_render_region()
        settings.SceneFile = get_scene_full_path()
        settings.SSQuality = get_supersampling_quality()
        settings.StartFrame = get_frame_start()
        settings.View = get_render_view()

    @staticmethod
    def _configure_ui_persisted_settings(settings: RenderSubmitterUISettings) -> None:
        """
        Intended as a one-time call per scene file session to initialize submitter (default) UI options before they
        appear. They will persist beyond the lifetime of the settings object (after the submitter dialog closes).
        param: settings: maintains values for all render submission parameters.
        """
        output_filename = os.path.normpath(
            os.path.join(
                settings.OutputDir,
                f"{settings.OutputFileNamePrefix}.{settings.OutputFormat.lower()}",
            )
        )
        """
        Note: excluded unimplemented settings (not traditionally submitter UI exposed):
           IncludeAlphaChannel, OverrideRenderPass, PremultiplyAlpha, TonemapHDR
        Note: excluded internal settings (not submitter UI exposed):
           JobScriptDir OutputFileNamePrefix, OutputFormat, OutputDir, SceneFile
        Note: excluded (pending implementation changes) - settings exposed as one aggregate field:
           EndFrame, FrameStep, StartFrame
        """
        SceneSettingsPopulator.persisted_ui_settings_states.__dict__.update(
            {
                PersistedUISettingsNames.ANIMATION_CLIP: settings.AnimationClip,
                PersistedUISettingsNames.ANIMATION_TYPE: settings.AnimationType,
                PersistedUISettingsNames.DLSS_QUALITY: settings.DLSSQuality,
                PersistedUISettingsNames.ENABLE_RENDER_REGIONS: bool(settings.RegionRendering),
                PersistedUISettingsNames.FRAME_RANGE: f"{settings.StartFrame}-{settings.EndFrame}",
                PersistedUISettingsNames.FRAMES_PER_TASK: settings.FramesPerTask,
                PersistedUISettingsNames.IMAGE_SIZE_X: int(settings.ImageWidth),
                PersistedUISettingsNames.IMAGE_SIZE_Y: int(settings.ImageHeight),
                PersistedUISettingsNames.JOB_TYPE: settings.JobType,
                PersistedUISettingsNames.RENDER_ANIMATION: bool(settings.RenderAnimation),
                PersistedUISettingsNames.RENDER_OUTPUT: output_filename,
                PersistedUISettingsNames.RENDER_QUALITY: settings.RenderQuality,
                PersistedUISettingsNames.RESOLUTION: int(settings.DPI),
                PersistedUISettingsNames.SEQUENCE_NAME: settings.SequenceName,
                PersistedUISettingsNames.SS_QUALITY: settings.SSQuality,
                PersistedUISettingsNames.TILES_IN_X: int(settings.NumXTiles),
                PersistedUISettingsNames.TILES_IN_Y: int(settings.NumYTiles),
                PersistedUISettingsNames.USE_CLIP_RANGE: False,
                PersistedUISettingsNames.USE_GPU_RAY_TRACING: bool(settings.GPURaytracing),
                PersistedUISettingsNames.VIEW: settings.View,
            }
        )

    def _populate_runtime_ui_options_values(self, settings: RenderSubmitterUISettings) -> None:
        """
        Populates runtime-derived values and standard option choices into UI elements and resets their state.
        param: settings: maintains values for all render submission parameters.
        """
        # Populate job types
        self.parent.render_job_type_widget.addItems(Constants.JOB_TYPE_OPTIONS)

        # Populate camera view settings
        views_list = get_views_list()
        self.parent.render_view_widget.addItems(views_list)
        self.parent.render_view_widget.set_current_entry(settings.View)

        # Populate Animation Clips - includes 'empty' clip
        self.parent.animation_clip_widget.setEnabled(False)
        anim_clips_list = get_animation_clips_list()
        if len(anim_clips_list) > 1:
            self.parent.animation_clip_widget.addItems(anim_clips_list)
            # Empty clip name is at the top of the list (for no animation clip)
            self.parent.animation_clip_widget.setCurrentIndex(0)
            self.animation_clip_ranges_map = get_populated_animation_clip_ranges()

        # Populate render quality-related options
        self.parent.dlss_quality_widget.addItems(Constants.DLSS_QUALITY_OPTIONS)
        self.parent.dlss_quality_widget.set_current_entry(settings.DLSSQuality)
        self.parent.render_quality_widget.addItems(Constants.RENDER_QUALITY_OPTIONS)
        self.parent.render_quality_widget.set_current_entry(Constants.RENDER_QUALITY_DEFAULT)
        self.parent.ss_quality_widget.addItems(Constants.SS_QUALITY_OPTIONS)
        self.parent.ss_quality_widget.set_current_entry(settings.SSQuality)

        # Populate image size presets options (for image size and resolution). Entry set via image X/Y callbacks.
        self.parent.image_size_presets_widget.addItems(Constants.IMAGE_SIZE_PRESETS_MAP.keys())

        # Populate animation types
        self.parent.animation_type_widget.addItems(Constants.ANIMATION_TYPE_OPTIONS)
        self.parent.animation_type_widget.set_current_entry(settings.AnimationType)

        # Populate sequencer options
        self.parent.sequence_name_widget.addItems(get_all_sequences())
        self.parent.sequence_name_widget.setCurrentIndex(0)

    def _restore_persisted_ui_settings_states(self) -> None:
        """
        Populates persisted settings states into UI individual widgets. Any default field values may originate from
        within the RenderSubmitterUISettings object, which populated into persisted_ui_settings_states.
        """
        self.parent.animation_clip_widget.set_current_entry(
            self.persisted_ui_settings_states.animation_clip
        )
        self.parent.animation_type_widget.set_current_entry(
            self.persisted_ui_settings_states.animation_type
        )
        self.parent.dlss_quality_widget.set_current_entry(
            self.persisted_ui_settings_states.dlss_quality
        )
        self.parent.enable_region_rendering_widget.setChecked(
            self.persisted_ui_settings_states.enable_render_regions
        )
        self.parent.frame_range_widget.setText(self.persisted_ui_settings_states.frame_range)
        self.parent.frames_per_task_widget.setValue(
            self.persisted_ui_settings_states.frames_per_task
        )
        self.parent.gpu_ray_tracing_widget.setChecked(
            self.persisted_ui_settings_states.use_gpu_ray_tracing
        )
        # Order sensitive computation (DPI impacts image size, so change image size after)
        self.parent.resolution_widget.setText(str(self.persisted_ui_settings_states.resolution))
        self.parent.image_size_x_widget.setText(str(self.persisted_ui_settings_states.image_size_x))
        self.parent.image_size_y_widget.setText(str(self.persisted_ui_settings_states.image_size_y))
        self.parent.render_animation_widget.setChecked(
            self.persisted_ui_settings_states.render_animation
        )
        self.parent.render_job_type_widget.set_current_entry(
            self.persisted_ui_settings_states.job_type
        )
        self.parent.render_output_widget.setText(self.persisted_ui_settings_states.render_output)

        self.parent.render_quality_widget.set_current_entry(
            self.persisted_ui_settings_states.render_quality
        )
        self.parent.render_view_widget.setCurrentText(self.persisted_ui_settings_states.view)
        self.parent.sequence_name_widget.set_current_entry(
            self.persisted_ui_settings_states.sequence_name
        )
        self.parent.ss_quality_widget.set_current_entry(
            self.persisted_ui_settings_states.ss_quality
        )
        self.parent.tiles_in_x_widget.setValue(self.persisted_ui_settings_states.tiles_in_x)
        self.parent.tiles_in_y_widget.setValue(self.persisted_ui_settings_states.tiles_in_y)

        self.parent.use_clip_range_widget.setChecked(
            self.persisted_ui_settings_states.use_clip_range
        )

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
        try:
            settings.StartFrame, settings.EndFrame, settings.FrameStep = get_frame_range_components(
                self.parent.frame_range_widget.text()
            )
        except ValueError:
            settings.StartFrame, settings.EndFrame, settings.FrameStep = (0, 0, 0)

        render_output_path = self.parent.render_output_widget.text()
        directory, filename_prefix, extension = get_file_name_path_components(render_output_path)
        attrs: Any = DynamicKeyNamedValueObject(settings.__dict__)
        settings.__dict__.update(
            {
                attrs.output_directories.__name__: [
                    get_normalized_path(os.path.dirname(render_output_path))
                ],
                attrs.AnimationClip.__name__: str(self.parent.animation_clip_widget.currentText()),
                attrs.AnimationType.__name__: str(self.parent.animation_type_widget.currentText()),
                attrs.DLSSQuality.__name__: str(self.parent.dlss_quality_widget.currentText()),
                attrs.DPI.__name__: int(self.parent.resolution_widget.text()),
                attrs.FramesPerTask.__name__: int(self.parent.frames_per_task_widget.value()),
                attrs.GPURaytracing.__name__: self.parent.gpu_ray_tracing_widget.isChecked(),
                attrs.ImageHeight.__name__: int(self.parent.image_size_y_widget.text()),
                attrs.ImageWidth.__name__: int(self.parent.image_size_x_widget.text()),
                attrs.IncludeAlphaChannel.__name__: get_render_alpha(),
                attrs.JobType.__name__: str(self.parent.render_job_type_widget.currentText()),
                attrs.NumXTiles.__name__: int(self.parent.tiles_in_x_widget.value()),
                attrs.NumYTiles.__name__: int(self.parent.tiles_in_y_widget.value()),
                attrs.OutputDir.__name__: str(directory),
                attrs.OutputFileNamePrefix.__name__: str(filename_prefix),
                attrs.OutputFormat.__name__: str(extension.upper()),
                attrs.PremultiplyAlpha.__name__: get_premultiply_alpha(),
                attrs.RegionRendering.__name__: self.parent.enable_region_rendering_widget.isChecked(),
                attrs.RenderAnimation.__name__: self.parent.render_animation_widget.isChecked(),
                attrs.RenderQuality.__name__: str(self.parent.render_quality_widget.currentText()),
                attrs.SSQuality.__name__: str(self.parent.ss_quality_widget.currentText()),
                attrs.SceneFile.__name__: get_scene_full_path(),
                attrs.SequenceName.__name__: str(self.parent.sequence_name_widget.currentText()),
                attrs.TonemapHDR.__name__: get_tonemap_hdr(),
                attrs.View.__name__: str(self.parent.render_view_widget.currentText()),
            }
        )
