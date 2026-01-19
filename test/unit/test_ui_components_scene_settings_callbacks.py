# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for SceneSettingsCallbacks UI event handling."""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QWidget

from vred_submitter.ui.components.scene_settings_callbacks import SceneSettingsCallbacks


class TestSceneSettingsCallbacks:
    """Test SceneSettingsCallbacks for UI widget event handling and state management."""

    @pytest.fixture
    def mock_parent(self, qapp):
        parent = Mock(spec=QWidget)
        # Create all required widget mocks
        widget_names = [
            "animation_clip_widget",
            "animation_type_widget",
            "dlss_quality_widget",
            "enable_region_rendering_widget",
            "frame_range_widget",
            "frames_per_task_widget",
            "gpu_ray_tracing_widget",
            "image_size_presets_widget",
            "image_size_x_widget",
            "image_size_y_widget",
            "printing_size_x_widget",
            "printing_size_y_widget",
            "render_animation_widget",
            "render_job_type_widget",
            "render_output_button",
            "render_output_widget",
            "render_quality_widget",
            "render_view_widget",
            "resolution_widget",
            "ss_quality_widget",
            "sequence_name_widget",
            "tiles_in_x_widget",
            "tiles_in_y_widget",
            "use_clip_range_widget",
            "group_box_render_options",
            "group_box_sequencer_options",
            "group_box_tiling_settings",
            "tiles_in_x_label",
            "tiles_in_y_label",
        ]
        for widget_name in widget_names:
            setattr(parent, widget_name, Mock())

        parent.init_complete = True
        parent.populator = Mock()
        parent.populator.persisted_ui_settings_states = Mock()
        parent.populator.animation_clip_ranges_map = {}
        return parent

    @pytest.fixture
    @patch("vred_submitter.ui.components.scene_settings_callbacks.assign_scene_transition_event")
    def callbacks(self, mock_assign_scene_transition, mock_parent):
        return SceneSettingsCallbacks(mock_parent)

    def test_init(self, mock_parent):
        with patch(
            "vred_submitter.ui.components.scene_settings_callbacks.assign_scene_transition_event"
        ):
            callbacks = SceneSettingsCallbacks(mock_parent)
            assert callbacks.parent == mock_parent
            assert not callbacks._updating_values

    def test_job_type_changed_callback_render_job(self, callbacks, mock_parent):
        mock_parent.render_job_type_widget.currentText.return_value = "Render"
        mock_parent.render_animation_widget.isChecked.return_value = True
        mock_parent.gpu_ray_tracing_widget.isChecked.return_value = False

        callbacks.job_type_changed_callback()

        mock_parent.group_box_render_options.setVisible.assert_called_with(True)
        mock_parent.group_box_sequencer_options.setVisible.assert_called_with(False)
        mock_parent.group_box_tiling_settings.setVisible.assert_called_with(True)

    def test_job_type_changed_callback_sequencer_job(self, callbacks, mock_parent):
        mock_parent.render_job_type_widget.currentText.return_value = "Sequencer"
        mock_parent.render_animation_widget.isChecked.return_value = False

        callbacks.job_type_changed_callback()

        mock_parent.group_box_render_options.setVisible.assert_called_with(False)
        mock_parent.group_box_sequencer_options.setVisible.assert_called_with(True)
        mock_parent.group_box_tiling_settings.setVisible.assert_called_with(False)

    def test_sequence_name_changed_callback(self, callbacks, mock_parent):
        mock_parent.sequence_name_widget.currentText.return_value = "test_sequence"

        callbacks.sequence_name_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.sequence_name == "test_sequence"

    def test_render_view_changed_callback(self, callbacks, mock_parent):
        mock_parent.render_view_widget.currentText.return_value = "Camera1"

        callbacks.render_view_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.view == "Camera1"

    # Test animation callbacks
    def test_animation_clip_selection_changed_callback_with_clip_range(
        self, callbacks, mock_parent
    ):
        """Test animation clip selection when using clip range"""
        mock_parent.animation_clip_widget.currentText.return_value = "test_clip"
        mock_parent.use_clip_range_widget.isChecked.return_value = True
        mock_parent.populator.animation_clip_ranges_map = {"test_clip": (10, 50)}

        callbacks.animation_clip_selection_changed_callback()

        mock_parent.frame_range_widget.setText.assert_called_with("10-50")
        assert mock_parent.populator.persisted_ui_settings_states.animation_clip == "test_clip"

    def test_animation_clip_selection_changed_callback_without_clip_range(
        self, callbacks, mock_parent
    ):
        """Test animation clip selection when not using clip range"""
        mock_parent.use_clip_range_widget.isChecked.return_value = False

        callbacks.animation_clip_selection_changed_callback()

        mock_parent.frame_range_widget.setText.assert_not_called()

    def test_animation_clip_selection_changed_callback_missing_clip(self, callbacks, mock_parent):
        """Test animation clip selection with missing clip"""
        mock_parent.animation_clip_widget.currentText.return_value = "missing_clip"
        mock_parent.use_clip_range_widget.isChecked.return_value = True
        mock_parent.populator.animation_clip_ranges_map = {}

        callbacks.animation_clip_selection_changed_callback()

        mock_parent.frame_range_widget.setText.assert_called_with("0-0")  # Default empty range

    def test_animation_type_selection_changed_callback_clip_type(self, callbacks, mock_parent):
        """Test animation type selection for clip type"""
        mock_parent.animation_type_widget.currentText.return_value = "Clip"
        mock_parent.render_animation_widget.isChecked.return_value = True
        mock_parent.use_clip_range_widget.isChecked.return_value = False

        callbacks.animation_type_selection_changed_callback()

        mock_parent.animation_clip_widget.setEnabled.assert_called_with(True)
        mock_parent.use_clip_range_widget.setEnabled.assert_called_with(True)
        mock_parent.frame_range_widget.setEnabled.assert_called_with(True)

    def test_animation_type_selection_changed_callback_timeline_type(self, callbacks, mock_parent):
        """Test animation type selection for timeline type"""
        mock_parent.animation_type_widget.currentText.return_value = "Timeline"
        mock_parent.render_animation_widget.isChecked.return_value = True

        callbacks.animation_type_selection_changed_callback()

        mock_parent.frame_range_widget.setEnabled.assert_called_with(True)
        mock_parent.animation_clip_widget.setEnabled.assert_called_with(False)
        mock_parent.use_clip_range_widget.setEnabled.assert_called_with(False)

    def test_animation_type_selection_changed_callback_no_animation(self, callbacks, mock_parent):
        """Test animation type selection when animation disabled"""
        mock_parent.render_animation_widget.isChecked.return_value = False

        callbacks.animation_type_selection_changed_callback()

        mock_parent.use_clip_range_widget.setEnabled.assert_called_with(False)

    def test_use_clip_range_changed_callback_enabled(self, callbacks, mock_parent):
        """Test use clip range callback when enabled"""
        mock_parent.use_clip_range_widget.isChecked.return_value = True
        mock_parent.use_clip_range_widget.isEnabled.return_value = True
        mock_parent.populator.animation_clip_ranges_map = {"clip1": (1, 100)}

        with patch(
            "vred_submitter.ui.components.scene_settings_callbacks.get_populated_animation_clip_ranges"
        ) as mock_get_ranges:
            mock_get_ranges.return_value = {"clip1": (1, 100)}
            callbacks.use_clip_range_changed_callback()

        mock_parent.frame_range_widget.setEnabled.assert_called_with(False)
        assert mock_parent.populator.persisted_ui_settings_states.use_clip_range

    def test_use_clip_range_changed_callback_disabled(self, callbacks, mock_parent):
        """Test use clip range callback when disabled"""
        mock_parent.use_clip_range_widget.isChecked.return_value = False
        mock_parent.use_clip_range_widget.isEnabled.return_value = True

        callbacks.use_clip_range_changed_callback()

        mock_parent.frame_range_widget.setEnabled.assert_called_with(True)
        assert not mock_parent.populator.persisted_ui_settings_states.use_clip_range

    # Test image size calculations
    @patch("vred_submitter.ui.components.scene_settings_callbacks.is_all_numbers")
    def test_image_size_text_changed_callback_valid_numbers(
        self, mock_is_all_numbers, callbacks, mock_parent
    ):
        """Test image size calculation with valid numbers"""
        mock_is_all_numbers.return_value = True
        mock_parent.image_size_x_widget.text.return_value = "1920"
        mock_parent.image_size_y_widget.text.return_value = "1080"
        mock_parent.resolution_widget.text.return_value = "300"

        callbacks.image_size_text_changed_callback()

        # Should update printing size fields
        mock_parent.printing_size_x_widget.setText.assert_called()
        mock_parent.printing_size_y_widget.setText.assert_called()

    @patch("vred_submitter.ui.components.scene_settings_callbacks.is_all_numbers")
    def test_image_size_text_changed_callback_invalid_numbers(
        self, mock_is_all_numbers, callbacks, mock_parent
    ):
        """Test image size calculation with invalid numbers"""
        mock_is_all_numbers.return_value = False

        callbacks.image_size_text_changed_callback()

        # Should not update printing size fields
        mock_parent.printing_size_x_widget.setText.assert_not_called()

    @patch("vred_submitter.ui.components.scene_settings_callbacks.is_all_numbers")
    def test_printing_size_text_changed_callback_valid_numbers(
        self, mock_is_all_numbers, callbacks, mock_parent
    ):
        """Test printing size calculation with valid numbers"""
        mock_is_all_numbers.return_value = True
        mock_parent.printing_size_x_widget.text.return_value = "10.0"
        mock_parent.printing_size_y_widget.text.return_value = "7.5"
        mock_parent.resolution_widget.text.return_value = "300"
        mock_parent.image_size_x_widget.text.return_value = "1181"  # Mock return value
        mock_parent.image_size_y_widget.text.return_value = "885"  # Mock return value

        callbacks.printing_size_text_changed_callback()

        # Should update image size fields
        mock_parent.image_size_x_widget.setText.assert_called()
        mock_parent.image_size_y_widget.setText.assert_called()

    @patch("vred_submitter.ui.components.scene_settings_callbacks.is_all_numbers")
    def test_printing_size_text_changed_callback_empty_values(
        self, mock_is_all_numbers, callbacks, mock_parent
    ):
        """Test printing size calculation with empty values"""
        mock_is_all_numbers.return_value = False  # Return False for empty values
        mock_parent.printing_size_x_widget.text.return_value = ""
        mock_parent.printing_size_y_widget.text.return_value = ""
        mock_parent.resolution_widget.text.return_value = "300"

        callbacks.printing_size_text_changed_callback()

        # Should return early due to invalid numbers
        mock_parent.image_size_x_widget.setText.assert_not_called()

    # Test render quality callbacks
    def test_dlss_quality_changed_callback(self, callbacks, mock_parent):
        """Test DLSS quality change callback"""
        mock_parent.dlss_quality_widget.currentText.return_value = "Quality"

        callbacks.dlss_quality_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.dlss_quality == "Quality"

    def test_ss_quality_changed_callback(self, callbacks, mock_parent):
        """Test supersampling quality change callback"""
        mock_parent.ss_quality_widget.currentText.return_value = "High"

        callbacks.ss_quality_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.ss_quality == "High"

    def test_render_quality_changed_callback(self, callbacks, mock_parent):
        """Test render quality change callback"""
        mock_parent.render_quality_widget.currentText.return_value = "Raytracing"

        callbacks.render_quality_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.render_quality == "Raytracing"

    # Test tiling callbacks
    def test_enable_region_rendering_changed_callback_enabled(self, callbacks, mock_parent):
        """Test enable region rendering callback when enabled"""
        mock_parent.enable_region_rendering_widget.isChecked.return_value = True

        callbacks.enable_region_rendering_changed_callback()

        mock_parent.gpu_ray_tracing_widget.setChecked.assert_called_with(True)
        # Check that the correct value was assigned to the correct attribute
        assert mock_parent.populator.persisted_ui_settings_states.enable_render_regions is True

    def test_enable_region_rendering_changed_callback_disabled(self, callbacks, mock_parent):
        """Test enable region rendering callback when disabled"""
        mock_parent.enable_region_rendering_widget.isChecked.return_value = False

        callbacks.enable_region_rendering_changed_callback()

        # Check that the correct value was assigned to the correct attribute
        assert mock_parent.populator.persisted_ui_settings_states.enable_render_regions is False

    def test_tiles_in_x_changed_callback(self, callbacks, mock_parent):
        """Test tiles in X change callback"""
        mock_parent.tiles_in_x_widget.value.return_value = 4

        callbacks.tiles_in_x_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.tiles_in_x == 4

    def test_tiles_in_y_changed_callback(self, callbacks, mock_parent):
        """Test tiles in Y change callback"""
        mock_parent.tiles_in_y_widget.value.return_value = 3

        callbacks.tiles_in_y_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.tiles_in_y == 3

    # Test frame range callbacks
    def test_frame_range_changed_callback(self, callbacks, mock_parent):
        """Test frame range change callback"""
        mock_parent.frame_range_widget.text.return_value = "1-100"

        callbacks.frame_range_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.frame_range == "1-100"

    def test_frames_per_task_changed_callback(self, callbacks, mock_parent):
        """Test frames per task change callback"""
        mock_parent.frames_per_task_widget.value.return_value = 10

        callbacks.frames_per_task_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.frames_per_task == 10

    # Test callbacks when init not complete
    def test_callbacks_when_init_not_complete(self, callbacks, mock_parent):
        """Test callbacks return early when initialization not complete"""
        mock_parent.init_complete = False

        callbacks.animation_clip_selection_changed_callback()
        callbacks.animation_type_selection_changed_callback()
        callbacks.sequence_name_changed_callback()
        callbacks.render_view_changed_callback()

        # Should not have called setText on frame_range_widget
        mock_parent.frame_range_widget.setText.assert_not_called()

    # Test updating values flag
    def test_image_size_callback_prevents_recursive_updates(self, callbacks, mock_parent):
        """Test that _updating_values flag prevents recursive updates"""
        callbacks._updating_values = True

        callbacks.image_size_text_changed_callback()
        callbacks.printing_size_text_changed_callback()

        # Should return early and not update anything
        mock_parent.printing_size_x_widget.setText.assert_not_called()
        mock_parent.image_size_x_widget.setText.assert_not_called()

    def test_render_output_path_changed_callback(self, callbacks, mock_parent):
        """Test render output path persistence"""
        mock_parent.render_output_widget.text.return_value = "/path/to/output"

        callbacks.render_output_path_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.render_output == "/path/to/output"

    @patch("vred_submitter.ui.components.scene_settings_callbacks.is_all_numbers")
    def test_resolution_changed_callback(self, mock_is_all_numbers, callbacks, mock_parent):
        """Test resolution change updates persistent state and calls printing size callback"""
        mock_is_all_numbers.return_value = True
        mock_parent.resolution_widget.text.return_value = "150"
        mock_parent.printing_size_x_widget.text.return_value = "10.0"
        mock_parent.printing_size_y_widget.text.return_value = "7.5"
        mock_parent.image_size_x_widget.text.return_value = "1181"
        mock_parent.image_size_y_widget.text.return_value = "885"

        callbacks.resolution_changed_callback()

        # Should update persistent state
        assert mock_parent.populator.persisted_ui_settings_states.resolution == 150

    def test_deregister_all_callbacks_with_exceptions(self, callbacks, mock_parent):
        """Test deregister handles exceptions during disconnect"""
        # Make one disconnect method raise an exception
        mock_parent.animation_clip_widget.currentIndexChanged.disconnect.side_effect = RuntimeError(
            "Disconnect failed"
        )

        # Should not raise exception, should continue with other disconnects
        callbacks.deregister_all_callbacks()

        # Verify other disconnects were still attempted
        mock_parent.animation_type_widget.currentIndexChanged.disconnect.assert_called_once()

    @patch(
        "vred_submitter.ui.components.scene_settings_callbacks.get_populated_animation_clip_ranges"
    )
    def test_use_clip_range_changed_callback_with_clip_refresh(
        self, mock_get_ranges, callbacks, mock_parent
    ):
        """Test clip range refresh when enabled with multiple clips"""
        mock_parent.use_clip_range_widget.isChecked.return_value = True
        mock_parent.use_clip_range_widget.isEnabled.return_value = True
        mock_parent.populator.animation_clip_ranges_map = {"clip1": (1, 100), "clip2": (50, 150)}
        mock_parent.animation_clip_widget.currentText.return_value = "clip1"

        # Mock the function to return updated ranges
        mock_get_ranges.return_value = {"clip1": (1, 100), "clip2": (50, 150)}

        callbacks.use_clip_range_changed_callback()

        # Should refresh ranges and update frame range
        mock_get_ranges.assert_called_once()
        mock_parent.frame_range_widget.setText.assert_called_with("1-100")

    @patch("vred_submitter.ui.components.scene_settings_callbacks.QFileDialog")
    def test_render_output_file_dialog_callback(self, mock_file_dialog, callbacks, mock_parent):
        """Test file dialog for render output selection"""
        mock_file_dialog.getSaveFileName.return_value = (
            "/new/path/output.png",
            "PNG Files (*.png)",
        )

        callbacks.render_output_file_dialog_callback()

        mock_parent.render_output_widget.setText.assert_called_with("/new/path/output.png")

    @patch("vred_submitter.ui.components.scene_settings_callbacks.QFileDialog")
    def test_render_output_file_dialog_callback_cancelled(
        self, mock_file_dialog, callbacks, mock_parent
    ):
        """Test file dialog cancelled"""
        mock_file_dialog.getSaveFileName.return_value = ("", "")

        callbacks.render_output_file_dialog_callback()

        # Should not update widget when dialog cancelled
        mock_parent.render_output_widget.setText.assert_not_called()
