# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Represents backend callbacks and UX interaction logic for UI within ("Job-specific settings")"""

from .constants import Constants
from .scene_settings_populator import SceneSettingsPopulator
from ...utils import ceil, clamp, is_all_numbers
from ...vred_utils import (
    assign_scene_transition_event,
    get_populated_animation_clip_ranges,
    get_render_window_size,
)

from PySide6.QtWidgets import (
    QFileDialog,
    QWidget,
)


class SceneSettingsCallbacks:
    """Callback handler logic applied to a parent class (SceneSettingsWidget) that contains UI objects"""

    # Restrict one-time events to be per scene file session (not on every submission dialog reopening)
    #
    invoked_once = False

    def __init__(self, parent_cls: QWidget) -> None:
        """
        Initialize the callback handler
        param: parent_cls: parent widget containing UI elements
        """
        self.parent = parent_cls
        self._register_all_qt_callbacks()
        # Support scene transition events (new scene and project load resetting settings persistent state and UI)
        #
        if not SceneSettingsCallbacks.invoked_once:
            assign_scene_transition_event(self.scene_file_changed_callback)
            SceneSettingsCallbacks.invoked_once = True
        self._updating_values = False

    def _register_all_qt_callbacks(self) -> None:
        """Registers all UI element-related callbacks"""
        self.parent.animation_clip_widget.currentIndexChanged.connect(
            self.animation_clip_selection_changed_callback
        )
        self.parent.animation_type_widget.currentIndexChanged.connect(
            self.animation_type_selection_changed_callback
        )
        self.parent.dlss_quality_widget.currentIndexChanged.connect(
            self.dlss_quality_changed_callback
        )
        self.parent.enable_region_rendering_widget.stateChanged.connect(
            self.enable_region_rendering_changed_callback
        )
        self.parent.frame_range_widget.textChanged.connect(self.frame_range_changed_callback)
        self.parent.frames_per_task_widget.valueChanged.connect(
            self.frames_per_task_changed_callback
        )
        self.parent.gpu_ray_tracing_widget.stateChanged.connect(self.job_type_changed_callback)
        self.parent.image_size_presets_widget.currentIndexChanged.connect(
            self.image_size_preset_selection_changed_callback
        )
        self.parent.image_size_x_widget.textChanged.connect(self.image_size_text_changed_callback)
        self.parent.image_size_y_widget.textChanged.connect(self.image_size_text_changed_callback)
        self.parent.printing_size_x_widget.textChanged.connect(
            self.printing_size_text_changed_callback
        )
        self.parent.printing_size_y_widget.textChanged.connect(
            self.printing_size_text_changed_callback
        )
        self.parent.render_animation_widget.stateChanged.connect(self.job_type_changed_callback)
        self.parent.render_job_type_widget.currentIndexChanged.connect(
            self.job_type_changed_callback
        )
        self.parent.render_output_button.pressed.connect(self.render_output_file_dialog_callback)
        self.parent.render_output_widget.textChanged.connect(
            self.render_output_path_changed_callback
        )
        self.parent.render_quality_widget.currentIndexChanged.connect(
            self.render_quality_changed_callback
        )
        self.parent.render_view_widget.currentIndexChanged.connect(
            self.render_view_changed_callback
        )
        self.parent.resolution_widget.textChanged.connect(self.resolution_changed_callback)
        self.parent.ss_quality_widget.currentIndexChanged.connect(self.ss_quality_changed_callback)
        self.parent.sequence_name_widget.currentIndexChanged.connect(
            self.sequence_name_changed_callback
        )
        self.parent.tiles_in_x_widget.valueChanged.connect(self.tiles_in_x_changed_callback)
        self.parent.tiles_in_y_widget.valueChanged.connect(self.tiles_in_y_changed_callback)
        self.parent.use_clip_range_widget.stateChanged.connect(self.use_clip_range_changed_callback)

    def deregister_all_callbacks(self) -> None:
        """Deregister most callbacks to avoid unintentional triggering and prepare for new scene file state reset"""
        disconnect_functions = [
            lambda: self.parent.animation_clip_widget.currentIndexChanged.disconnect(),
            lambda: self.parent.animation_type_widget.currentIndexChanged.disconnect(),
            lambda: self.parent.dlss_quality_widget.currentIndexChanged.disconnect(),
            lambda: self.parent.enable_region_rendering_widget.stateChanged.disconnect(),
            lambda: self.parent.frame_range_widget.textChanged.disconnect(),
            lambda: self.parent.frames_per_task_widget.valueChanged.disconnect(),
            lambda: self.parent.gpu_ray_tracing_widget.stateChanged.disconnect(),
            lambda: self.parent.image_size_presets_widget.currentIndexChanged.disconnect(),
            lambda: self.parent.image_size_x_widget.textChanged.disconnect(),
            lambda: self.parent.image_size_y_widget.textChanged.disconnect(),
            lambda: self.parent.printing_size_x_widget.textChanged.disconnect(),
            lambda: self.parent.printing_size_y_widget.textChanged.disconnect(),
            lambda: self.parent.render_animation_widget.stateChanged.disconnect(),
            lambda: self.parent.render_job_type_widget.currentIndexChanged.disconnect(),
            lambda: self.parent.render_output_button.pressed.disconnect(),
            lambda: self.parent.render_output_widget.textChanged.disconnect(),
            lambda: self.parent.render_quality_widget.currentIndexChanged.disconnect(),
            lambda: self.parent.render_view_widget.currentIndexChanged.disconnect(),
            lambda: self.parent.resolution_widget.textChanged.disconnect(),
            lambda: self.parent.sequence_name_widget.currentIndexChanged.disconnect(),
            lambda: self.parent.ss_quality_widget.currentIndexChanged.disconnect(),
            lambda: self.parent.tiles_in_x_widget.valueChanged.disconnect(),
            lambda: self.parent.tiles_in_y_widget.valueChanged.disconnect(),
            lambda: self.parent.use_clip_range_widget.stateChanged.disconnect(),
        ]
        for disconnect_function in disconnect_functions:
            try:
                disconnect_function()
            except Exception:
                # if any disconnections fail, we continue to ensure we disconnect all of them
                pass

    def job_type_changed_callback(self) -> None:
        """
        Updates UI elements based on the selected job type and animation settings.
        """
        render_job_type = self.parent.render_job_type_widget.currentText()
        is_render_job = render_job_type == Constants.JOB_TYPE_RENDER
        is_sequencer_job = render_job_type == Constants.JOB_TYPE_SEQUENCER
        is_render_animation_job = self.parent.render_animation_widget.isChecked()
        is_animation_enabled = is_render_job and is_render_animation_job

        self.parent.group_box_render_options.setVisible(is_render_job)
        self.parent.group_box_sequencer_options.setVisible(not is_render_job)
        self.parent.group_box_tiling_settings.setVisible(is_render_job)

        render_controls = [
            self.parent.render_output_widget,
            self.parent.render_view_widget,
            self.parent.render_animation_widget,
            self.parent.render_quality_widget,
        ]
        for control in render_controls:
            control.setEnabled(is_render_job)

        animation_controls = [
            self.parent.animation_type_widget,
            self.parent.animation_clip_widget,
            self.parent.use_clip_range_widget,
            self.parent.frame_range_widget,
            self.parent.frames_per_task_widget,
        ]
        for control in animation_controls:
            control.setEnabled(is_animation_enabled)

        self.parent.sequence_name_widget.setEnabled(is_sequencer_job)

        # Keep state consistent, especially when reinitializing persistent UI
        self.parent.use_clip_range_widget.stateChanged.emit(
            self.parent.use_clip_range_widget.checkState()
        )
        self.parent.animation_type_widget.currentIndexChanged.emit(
            self.parent.animation_type_widget.currentIndex()
        )

        # Update persisted settings if initialization is complete
        if self.parent.init_complete:
            self.parent.populator.persisted_ui_settings_states.job_type = render_job_type
            self.parent.populator.persisted_ui_settings_states.render_animation = (
                is_render_animation_job
            )
            self.parent.populator.persisted_ui_settings_states.use_gpu_ray_tracing = (
                self.parent.gpu_ray_tracing_widget.isChecked()
            )

    def sequence_name_changed_callback(self) -> None:
        """
        Persists sequence name state
        """
        if not self.parent.init_complete:
            return
        self.parent.populator.persisted_ui_settings_states.sequence_name = (
            self.parent.sequence_name_widget.currentText()
        )

    def render_view_changed_callback(self) -> None:
        """
        Persists render view state
        """
        if not self.parent.init_complete:
            return
        self.parent.populator.persisted_ui_settings_states.view = (
            self.parent.render_view_widget.currentText()
        )

    def render_output_path_changed_callback(self) -> None:
        """
        Persists render output path
        """
        if not self.parent.init_complete:
            return
        self.parent.populator.persisted_ui_settings_states.render_output = (
            self.parent.render_output_widget.text()
        )

    def render_quality_changed_callback(self) -> None:
        """
        Persists render quality state
        """
        if not self.parent.init_complete:
            return
        self.parent.populator.persisted_ui_settings_states.render_quality = (
            self.parent.render_quality_widget.currentText()
        )

    def dlss_quality_changed_callback(self) -> None:
        """
        Persists DLSS quality state
        """
        if not self.parent.init_complete:
            return
        self.parent.populator.persisted_ui_settings_states.dlss_quality = (
            self.parent.dlss_quality_widget.currentText()
        )

    def ss_quality_changed_callback(self) -> None:
        """
        Persists Supersampling quality state
        """
        if not self.parent.init_complete:
            return
        self.parent.populator.persisted_ui_settings_states.ss_quality = (
            self.parent.ss_quality_widget.currentText()
        )

    def frame_range_changed_callback(self) -> None:
        """
        Persists frame range state
        """
        if not self.parent.init_complete:
            return
        self.parent.populator.persisted_ui_settings_states.frame_range = (
            self.parent.frame_range_widget.text()
        )

    def frames_per_task_changed_callback(self) -> None:
        """
        Persists frame per task state
        """
        if not self.parent.init_complete:
            return
        self.parent.populator.persisted_ui_settings_states.frames_per_task = int(
            self.parent.frames_per_task_widget.value()
        )

    def enable_region_rendering_changed_callback(self) -> None:
        """
        Updates UI elements when region rendering is enabled/disabled.
        When region rendering is enabled, GPU Ray Tracing is automatically enabled and disabled.
        """
        if not self.parent.init_complete:
            return
        state = self.parent.enable_region_rendering_widget.isChecked()
        self.parent.populator.persisted_ui_settings_states.enable_render_regions = state

        # When region rendering is enabled, auto-enable GPU Ray Tracing and disable the control.
        # Region rendering requires GPU Ray Tracing to ensure proper tile rendering,
        # so we disable the control to prevent users from accidentally turning it off.
        # When region rendering is disabled, re-enable the GPU Ray Tracing control.
        if state:
            self.parent.gpu_ray_tracing_widget.setChecked(True)
            self.parent.gpu_ray_tracing_widget.setEnabled(False)
        else:
            self.parent.gpu_ray_tracing_widget.setEnabled(True)

        # All UI elements that should be enabled/disabled together
        region_rendering_controls = [
            self.parent.tiles_in_x_label,
            self.parent.tiles_in_x_widget,
            self.parent.tiles_in_y_label,
            self.parent.tiles_in_y_widget,
        ]
        for control in region_rendering_controls:
            control.setEnabled(state)

    def tiles_in_x_changed_callback(self) -> None:
        """
        Persists horizontal tiles count state
        """
        if not self.parent.init_complete:
            return
        self.parent.populator.persisted_ui_settings_states.tiles_in_x = (
            self.parent.tiles_in_x_widget.value()
        )

    def tiles_in_y_changed_callback(self) -> None:
        """
        Persists vertical tiles count state
        """
        if not self.parent.init_complete:
            return
        self.parent.populator.persisted_ui_settings_states.tiles_in_y = (
            self.parent.tiles_in_y_widget.value()
        )

    def image_size_preset_selection_changed_callback(self) -> None:
        """
        Updates image dimensions and resolution when an image size preset is selected.
        """
        preset_name = self.parent.image_size_presets_widget.currentText()
        if preset_name == Constants.IMAGE_SIZE_PRESET_CUSTOM:
            return
        elif preset_name == Constants.IMAGE_SIZE_PRESET_FROM_RENDER_WINDOW:
            # Consider determining the current render window used and resolution DPI.
            #
            width, height = get_render_window_size()
            self._set_render_pixel_resolution(width, height, Constants.DEFAULT_DPI_RESOLUTION)
        elif preset_name and preset_name in Constants.IMAGE_SIZE_PRESETS_MAP:
            [width, height, resolution] = Constants.IMAGE_SIZE_PRESETS_MAP[preset_name]
            self._set_render_pixel_resolution(width, height, resolution)
            self._update_image_presets_selection(width, height, resolution)

    def image_size_text_changed_callback(self):
        """
        Updates printing size based on image dimensions and resolution.
        It recalculates the printing dimensions based on the new pixel dimensions.
        Note: this callback is triggered when the user changes the image width or height.
        """
        if not self.parent.init_complete:
            return

        # Avoid recursive updates and validate inputs
        if self._updating_values:
            return

        text = self.parent.image_size_x_widget.text() or str(Constants.MIN_IMAGE_DIMENSION)
        if not self.parent.image_size_x_widget.text():
            self.parent.image_size_x_widget.setText(text)

        text = self.parent.image_size_y_widget.text() or str(Constants.MIN_IMAGE_DIMENSION)
        if not self.parent.image_size_y_widget.text():
            self.parent.image_size_y_widget.setText(text)

        if not is_all_numbers(
            [
                self.parent.image_size_x_widget.text(),
                self.parent.image_size_y_widget.text(),
                self.parent.resolution_widget.text(),
            ]
        ):
            return

        self._updating_values = True
        self.parent.populator.persisted_ui_settings_states.image_size_x = int(
            self.parent.image_size_x_widget.text()
        )
        self.parent.populator.persisted_ui_settings_states.image_size_y = int(
            self.parent.image_size_y_widget.text()
        )
        width, height, resolution = 0, 0, 0

        try:
            # Set to custom preset
            self.parent.image_size_presets_widget.setCurrentIndex(0)
            # Apply clamping constraints to dimensions and resolution and only update UI if values match
            width = int(
                clamp(
                    int(self.parent.image_size_x_widget.text()),
                    Constants.MIN_IMAGE_DIMENSION,
                    Constants.MAX_IMAGE_DIMENSION,
                )
            )
            height = int(
                clamp(
                    int(self.parent.image_size_y_widget.text()),
                    Constants.MIN_IMAGE_DIMENSION,
                    Constants.MAX_IMAGE_DIMENSION,
                )
            )
            resolution = int(
                clamp(
                    int(self.parent.resolution_widget.text()), Constants.MIN_DPI, Constants.MAX_DPI
                )
            )
            self._update_dimension_fields_if_changed(width, height, resolution)
            # Compute and update printing size
            printing_width = float(
                ceil(
                    width * Constants.INCH_TO_CM_FACTOR / resolution,
                    Constants.PRINTING_PRECISION_DIGITS_COUNT,
                )
            )
            printing_height = float(
                ceil(
                    height * Constants.INCH_TO_CM_FACTOR / resolution,
                    Constants.PRINTING_PRECISION_DIGITS_COUNT,
                )
            )
            self._update_printing_size_fields(printing_width, printing_height)
        finally:
            self._update_image_presets_selection(width, height, resolution)
            self._updating_values = False

    def _update_dimension_fields_if_changed(self, width: int, height: int, resolution: int) -> None:
        """
        Updates dimension fields if their values were changed.
        param: width : Clamped width value
        param: height: Clamped height value
        param: resolution: Clamped resolution value
        """
        if int(self.parent.image_size_x_widget.text()) != width:
            self.parent.image_size_x_widget.setText(str(width))
        if int(self.parent.image_size_y_widget.text()) != height:
            self.parent.image_size_y_widget.setText(str(height))
        if int(self.parent.resolution_widget.text()) != resolution:
            self.parent.resolution_widget.setText(str(resolution))

    def _update_printing_size_fields(self, width: float, height: float) -> None:
        """
        Updates printing size fields without triggering callbacks.
        param: width: printing width in cm
        param: height: printing height in cm
        """
        self.parent.printing_size_x_widget.blockSignals(True)
        self.parent.printing_size_y_widget.blockSignals(True)
        self.parent.printing_size_x_widget.setText(str(width))
        self.parent.printing_size_y_widget.setText(str(height))
        self.parent.printing_size_x_widget.blockSignals(False)
        self.parent.printing_size_y_widget.blockSignals(False)

    def _update_image_size_fields(self, width: int, height: int) -> None:
        """
        Updates image size fields without triggering callbacks.
        param: width: printing width in pixels
        param: height: printing height in pixel
        """
        self.parent.image_size_x_widget.blockSignals(True)
        self.parent.image_size_y_widget.blockSignals(True)
        self.parent.image_size_x_widget.setText(str(width))
        self.parent.image_size_y_widget.setText(str(height))
        if self.parent.init_complete:
            self.parent.populator.persisted_ui_settings_states.image_size_x = int(
                self.parent.image_size_x_widget.text()
            )
            self.parent.populator.persisted_ui_settings_states.image_size_y = int(
                self.parent.image_size_y_widget.text()
            )
        self.parent.image_size_x_widget.blockSignals(False)
        self.parent.image_size_y_widget.blockSignals(False)

    def printing_size_text_changed_callback(self):
        """
        Update image dimensions based on printing size and resolution.
        Note: This callback is triggered when the user changes the printing width or height.
        """
        # Avoid recursive updates and validate inputs
        if self._updating_values:
            return

        text = self.parent.printing_size_x_widget.text() or str(Constants.MIN_PRINT_DIMENSION)
        if not self.parent.printing_size_x_widget.text():
            self.parent.printing_size_x_widget.setText(text)

        text = self.parent.printing_size_y_widget.text() or str(Constants.MIN_PRINT_DIMENSION)
        if not self.parent.printing_size_y_widget.text():
            self.parent.printing_size_y_widget.setText(text)

        if not is_all_numbers(
            [
                self.parent.printing_size_x_widget.text(),
                self.parent.printing_size_y_widget.text(),
                self.parent.resolution_widget.text(),
            ]
        ):
            return

        self._updating_values = True
        width, height, resolution = 0, 0, 0

        try:
            # Set to custom preset
            self.parent.image_size_presets_widget.setCurrentIndex(0)
            printing_width = float(self.parent.printing_size_x_widget.text())
            printing_height = float(self.parent.printing_size_y_widget.text())
            resolution = int(
                clamp(
                    int(self.parent.resolution_widget.text()), Constants.MIN_DPI, Constants.MAX_DPI
                )
            )
            # Update resolution if it was clamped
            if int(self.parent.resolution_widget.text()) != resolution:
                self.parent.resolution_widget.setText(str(resolution))

            width = int(
                self._calculate_clamped_pixel_dimension(
                    printing_width,
                    resolution,
                    Constants.MIN_IMAGE_DIMENSION,
                    Constants.MAX_IMAGE_DIMENSION,
                )
            )
            height = int(
                self._calculate_clamped_pixel_dimension(
                    printing_height,
                    resolution,
                    Constants.MIN_IMAGE_DIMENSION,
                    Constants.MAX_IMAGE_DIMENSION,
                )
            )
            self._update_image_size_fields(width, height)
            # Recalculate printing dimensions based on clamped values
            self._recalculate_and_update_printing_dimensions_if_needed(
                width, height, printing_width, printing_height, resolution
            )
        finally:
            self._update_image_presets_selection(width, height, resolution)
            self._updating_values = False

    def _recalculate_and_update_printing_dimensions_if_needed(
        self,
        width: int,
        height: int,
        printing_width: float,
        printing_height: float,
        resolution: int,
    ) -> None:
        """
        Recalculates and updates clamped printing dimensions if pixel dimensions were changed.
        param: width: current pixel width.
        param: height: current pixel height.
        param: printing_width: original printing width.
        param: printing_height: original printing height.
        param: resolution: current resolution.
        """
        expected_width = int(
            ceil(
                float(printing_width * resolution / Constants.INCH_TO_CM_FACTOR),
                Constants.PRINTING_PRECISION_DIGITS_COUNT,
            )
        )
        expected_height = int(
            ceil(
                float(printing_height * resolution / Constants.INCH_TO_CM_FACTOR),
                Constants.PRINTING_PRECISION_DIGITS_COUNT,
            )
        )
        if width != expected_width or height != expected_height:
            # Recalculate printing dimensions based on clamped pixel dimensions
            new_printing_width = ceil(
                width * Constants.INCH_TO_CM_FACTOR / resolution,
                Constants.PRINTING_PRECISION_DIGITS_COUNT,
            )
            new_printing_height = ceil(
                height * Constants.INCH_TO_CM_FACTOR / resolution,
                Constants.PRINTING_PRECISION_DIGITS_COUNT,
            )
            self.parent.printing_size_x_widget.setText(str(new_printing_width))
            self.parent.printing_size_y_widget.setText(str(new_printing_height))

    def _set_render_pixel_resolution(self, width: int, height: int, resolution: int) -> None:
        """
        Set the render pixel resolution and update related UI elements.
        param: width: image width in pixels
        param: height: image height in pixels
        param: resolution: resolution in pixels per inch
        """
        # Apply constraints to all values
        self.parent.image_size_x_widget.setText(
            str(clamp(int(width), Constants.MIN_IMAGE_DIMENSION, Constants.MAX_IMAGE_DIMENSION))
        )
        self.parent.image_size_y_widget.setText(
            str(clamp(int(height), Constants.MIN_IMAGE_DIMENSION, Constants.MAX_IMAGE_DIMENSION))
        )
        self.parent.resolution_widget.setText(
            str(clamp(int(resolution), Constants.MIN_DPI, Constants.MAX_DPI))
        )
        printing_width = ceil(
            float(width / resolution * Constants.INCH_TO_CM_FACTOR),
            Constants.PRINTING_PRECISION_DIGITS_COUNT,
        )
        printing_height = ceil(
            float(height / resolution * Constants.INCH_TO_CM_FACTOR),
            Constants.PRINTING_PRECISION_DIGITS_COUNT,
        )
        self.parent.printing_size_x_widget.setText(str(printing_width))
        self.parent.printing_size_y_widget.setText(str(printing_height))

    def _calculate_clamped_pixel_dimension(
        self, printing_dimension: float, resolution: int, min_dimension: int, max_dimension: int
    ) -> int:
        """
        Calculates and clamps pixel dimension from printing dimension.
        param: printing_dimension: dimension in cm
        param: resolution (int): resolution in DPI
        param: min_dimension: minimum allowed pixel dimension
        param: max_dimension: maximum allowed pixel dimension
        return: calculated clamped pixel dimension
        """
        pixel_dimension = int(
            ceil(
                float(printing_dimension * resolution / Constants.INCH_TO_CM_FACTOR),
                Constants.PRINTING_PRECISION_DIGITS_COUNT,
            )
        )
        return int(clamp(pixel_dimension, min_dimension, max_dimension))

    def _update_image_presets_selection(self, width: int, height: int, resolution: int) -> None:
        """
        Update the image preset selection based on specified image dimensions
        param: width: image width in pixels
        param: height: image height in pixels
        param: resolution: resolution in pixels per inch
        """
        # Match to a custom resolution or an existing resolution preset
        changed_render_dimension = [width, height, resolution]
        render_dimensions_list = list(Constants.IMAGE_SIZE_PRESETS_MAP.values())
        # Custom preset index (by convention)
        preset_index = 0
        if changed_render_dimension in render_dimensions_list:
            preset_index = render_dimensions_list.index(changed_render_dimension)
        self.parent.image_size_presets_widget.setCurrentIndex(preset_index)

    def resolution_changed_callback(self) -> None:
        """Adjusts image resolution based on constant printing size and DPI"""
        if self.parent.init_complete:
            text = self.parent.resolution_widget.text() or str(Constants.MIN_DPI)
            if not self.parent.resolution_widget.text():
                self.parent.resolution_widget.setText(text)
            self.parent.populator.persisted_ui_settings_states.resolution = int(text)
        self.printing_size_text_changed_callback()

    def animation_clip_selection_changed_callback(self) -> None:
        """
        Adjusts frame range data based on a clip's range when the 'use clip range' option is enabled.
        """
        if not self.parent.init_complete:
            return
        self.parent.populator.persisted_ui_settings_states.animation_clip = (
            self.parent.animation_clip_widget.currentText()
        )
        if not self.parent.use_clip_range_widget.isChecked():
            return
        anim_clip_name = self.parent.animation_clip_widget.currentText()
        # Set frame range based on selected clip
        if anim_clip_name and anim_clip_name in self.parent.populator.animation_clip_ranges_map:
            start_frame, end_frame = self.parent.populator.animation_clip_ranges_map[anim_clip_name]
            frame_range_text = Constants.FRAME_RANGE_BASIC_FORMAT % (start_frame, end_frame)
        else:
            frame_range_text = Constants.EMPTY_FRAME_RANGE
        self.parent.frame_range_widget.setText(frame_range_text)

    def animation_type_selection_changed_callback(self) -> None:
        """
        Adjusts UI options based on the selected animation type (clip or timeline).
        """
        if not self.parent.init_complete:
            return
        if not self.parent.render_animation_widget.isChecked():
            self.parent.use_clip_range_widget.setEnabled(False)
            return
        self.parent.populator.persisted_ui_settings_states.animation_type = (
            self.parent.animation_type_widget.currentText()
        )
        # Update UI controls based on the animation type
        clip_type_enabled = self.parent.animation_type_widget.currentText() == Constants.CLIP_LABEL
        self.parent.animation_clip_widget.setEnabled(clip_type_enabled)
        self.parent.use_clip_range_widget.setEnabled(clip_type_enabled)
        if clip_type_enabled:
            # For clips: frame range is editable only when not using clip's predefined range
            self.parent.frame_range_widget.setEnabled(
                not self.parent.use_clip_range_widget.isChecked()
            )
        else:
            # For timelines: frame range is always editable
            self.parent.frame_range_widget.setEnabled(True)
            self.parent.animation_clip_widget.setEnabled(False)
            self.parent.use_clip_range_widget.setEnabled(False)

    def use_clip_range_changed_callback(self) -> None:
        """
        Adjusts frame range data based on the 'use clip range' option being enabled/disabled.
        """
        if not self.parent.init_complete:
            return
        enabled = self.parent.use_clip_range_widget.isChecked()
        self.parent.populator.persisted_ui_settings_states.use_clip_range = enabled
        if self.parent.use_clip_range_widget.isEnabled():
            self.parent.frame_range_widget.setEnabled(not enabled)
        if enabled:
            # Check if there are animation clips available (beyond the empty one)
            if len(self.parent.populator.animation_clip_ranges_map) > 1:
                # Get current clip name and refresh clip ranges
                anim_clip_name = self.parent.animation_clip_widget.currentText()
                self.parent.populator.animation_clip_ranges_map = (
                    get_populated_animation_clip_ranges()
                )
                # Get range for selected clip and update UI
                if anim_clip_name in self.parent.populator.animation_clip_ranges_map:
                    start_frame, end_frame = self.parent.populator.animation_clip_ranges_map[
                        anim_clip_name
                    ]
                    frame_range_text = Constants.FRAME_RANGE_BASIC_FORMAT % (start_frame, end_frame)
                    self.parent.frame_range_widget.setText(frame_range_text)

    def render_output_file_dialog_callback(self) -> None:
        """Opens a file dialog to select a background image file."""
        new_output_file = QFileDialog.getSaveFileName(
            self.parent,
            Constants.RENDER_OUTPUT_LABEL,
            self.parent.render_output_widget.text(),
            Constants.VRED_IMAGE_EXPORT_FILTER,
        )
        if new_output_file:
            if isinstance(new_output_file, tuple) and len(new_output_file) > 0:
                new_output_file = new_output_file[0]
                if not new_output_file:
                    return
            self.parent.render_output_widget.setText(new_output_file)

    def scene_file_changed_callback(self, *dummy_args) -> None:
        """
        Removes persisted settings (normally called on scene file reset)
        param: dummy_args: conventional variable arguments passed by signal connections (unused)
        """
        if SceneSettingsPopulator.persisted_ui_settings_states:
            SceneSettingsPopulator.persisted_ui_settings_states.__dict__.clear()
            SceneSettingsPopulator.persisted_ui_settings_states = None
