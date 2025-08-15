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

    def test_render_output_path_changed_callback(self, callbacks, mock_parent):
        mock_parent.render_output_widget.text.return_value = "/output/path"

        callbacks.render_output_path_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.render_output == "/output/path"

    def test_enable_region_rendering_changed_callback(self, callbacks, mock_parent):
        mock_parent.enable_region_rendering_widget.isChecked.return_value = True
        mock_parent.tiles_in_x_label = Mock()
        mock_parent.tiles_in_x_widget = Mock()
        mock_parent.tiles_in_y_label = Mock()
        mock_parent.tiles_in_y_widget = Mock()

        callbacks.enable_region_rendering_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.enable_render_regions
        # Verify GPU Ray Tracing is automatically enabled and disabled
        mock_parent.gpu_ray_tracing_widget.setChecked.assert_called_with(True)
        mock_parent.gpu_ray_tracing_widget.setEnabled.assert_called_with(False)
        # Verify tiling controls are enabled
        mock_parent.tiles_in_x_label.setEnabled.assert_called_with(True)
        mock_parent.tiles_in_x_widget.setEnabled.assert_called_with(True)
        mock_parent.tiles_in_y_label.setEnabled.assert_called_with(True)
        mock_parent.tiles_in_y_widget.setEnabled.assert_called_with(True)

    def test_enable_region_rendering_changed_callback_disabled(self, callbacks, mock_parent):
        mock_parent.enable_region_rendering_widget.isChecked.return_value = False
        mock_parent.tiles_in_x_label = Mock()
        mock_parent.tiles_in_x_widget = Mock()
        mock_parent.tiles_in_y_label = Mock()
        mock_parent.tiles_in_y_widget = Mock()

        callbacks.enable_region_rendering_changed_callback()

        assert not mock_parent.populator.persisted_ui_settings_states.enable_render_regions
        # Verify GPU Ray Tracing control is re-enabled
        mock_parent.gpu_ray_tracing_widget.setEnabled.assert_called_with(True)
        # Verify tiling controls are disabled
        mock_parent.tiles_in_x_label.setEnabled.assert_called_with(False)
        mock_parent.tiles_in_x_widget.setEnabled.assert_called_with(False)
        mock_parent.tiles_in_y_label.setEnabled.assert_called_with(False)
        mock_parent.tiles_in_y_widget.setEnabled.assert_called_with(False)

    @patch("vred_submitter.ui.components.scene_settings_callbacks.is_all_numbers")
    def test_image_size_text_changed_callback_valid_numbers(
        self, mock_is_all_numbers, callbacks, mock_parent
    ):
        mock_is_all_numbers.return_value = True
        mock_parent.image_size_x_widget.text.return_value = "1920"
        mock_parent.image_size_y_widget.text.return_value = "1080"
        mock_parent.resolution_widget.text.return_value = "72"
        mock_parent.image_size_presets_widget.setCurrentIndex = Mock()

        callbacks.image_size_text_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.image_size_x == 1920
        assert mock_parent.populator.persisted_ui_settings_states.image_size_y == 1080

    @patch("vred_submitter.ui.components.scene_settings_callbacks.is_all_numbers")
    def test_image_size_text_changed_callback_invalid_numbers(
        self, mock_is_all_numbers, callbacks, mock_parent
    ):
        mock_is_all_numbers.return_value = False
        mock_parent.image_size_x_widget.text.return_value = "invalid"

        callbacks.image_size_text_changed_callback()

        # Should not update persisted settings when numbers are invalid
        # Just verify the method doesn't crash

    @patch(
        "vred_submitter.ui.components.scene_settings_callbacks.get_populated_animation_clip_ranges"
    )
    def test_animation_clip_selection_changed_callback(
        self, mock_get_ranges, callbacks, mock_parent
    ):
        mock_parent.animation_clip_widget.currentText.return_value = "test_clip"
        mock_parent.use_clip_range_widget.isChecked.return_value = True
        mock_parent.populator.animation_clip_ranges_map = {"test_clip": [1, 100]}
        mock_parent.frame_range_widget.setText = Mock()

        callbacks.animation_clip_selection_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.animation_clip == "test_clip"
        mock_parent.frame_range_widget.setText.assert_called_with("1-100")

    def test_animation_type_selection_changed_callback_clip_type(self, callbacks, mock_parent):
        mock_parent.animation_type_widget.currentText.return_value = "Clip"
        mock_parent.render_animation_widget.isChecked.return_value = True
        mock_parent.use_clip_range_widget.isChecked.return_value = False

        callbacks.animation_type_selection_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.animation_type == "Clip"
        mock_parent.animation_clip_widget.setEnabled.assert_called_with(True)
        mock_parent.use_clip_range_widget.setEnabled.assert_called_with(True)
        mock_parent.frame_range_widget.setEnabled.assert_called_with(True)

    def test_animation_type_selection_changed_callback_timeline_type(self, callbacks, mock_parent):
        mock_parent.animation_type_widget.currentText.return_value = "Timeline"
        mock_parent.render_animation_widget.isChecked.return_value = True

        callbacks.animation_type_selection_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.animation_type == "Timeline"
        mock_parent.animation_clip_widget.setEnabled.assert_called_with(False)
        mock_parent.use_clip_range_widget.setEnabled.assert_called_with(False)
        mock_parent.frame_range_widget.setEnabled.assert_called_with(True)

    def test_use_clip_range_changed_callback(self, callbacks, mock_parent):
        mock_parent.use_clip_range_widget.isChecked.return_value = True
        mock_parent.use_clip_range_widget.isEnabled.return_value = True
        # Mock the animation_clip_ranges_map to have length > 1
        mock_parent.populator.animation_clip_ranges_map = {"clip1": [1, 100], "clip2": [50, 150]}

        callbacks.use_clip_range_changed_callback()

        assert mock_parent.populator.persisted_ui_settings_states.use_clip_range
        mock_parent.frame_range_widget.setEnabled.assert_called_with(False)

    @patch("vred_submitter.ui.components.scene_settings_callbacks.QFileDialog")
    def test_render_output_file_dialog_callback(self, mock_file_dialog, callbacks, mock_parent):
        mock_file_dialog.getSaveFileName.return_value = ("/path/to/output.png", "PNG Files (*.png)")
        mock_parent.render_output_widget.text.return_value = "/current/path"

        callbacks.render_output_file_dialog_callback()

        mock_parent.render_output_widget.setText.assert_called_with("/path/to/output.png")

    @patch("vred_submitter.ui.components.scene_settings_callbacks.SceneSettingsPopulator")
    def test_scene_file_changed_callback(self, mock_populator_class, callbacks):
        # Create a real object with __dict__ to avoid Mock issues
        class MockSettings:
            def __init__(self):
                self.test = "value"

        mock_settings = MockSettings()
        mock_populator_class.persisted_ui_settings_states = mock_settings

        callbacks.scene_file_changed_callback()

        assert len(mock_settings.__dict__) == 0
        assert mock_populator_class.persisted_ui_settings_states is None

    def test_deregister_all_callbacks(self, callbacks, mock_parent):
        # Test that all disconnect methods are called
        callbacks.deregister_all_callbacks()

        mock_parent.animation_clip_widget.currentIndexChanged.disconnect.assert_called_once()
        mock_parent.animation_type_widget.currentIndexChanged.disconnect.assert_called_once()
        mock_parent.dlss_quality_widget.currentIndexChanged.disconnect.assert_called_once()
        # ... and so on for all widgets
