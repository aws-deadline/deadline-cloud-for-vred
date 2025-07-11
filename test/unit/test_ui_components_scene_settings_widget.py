# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for SceneSettingsWidget UI component."""
import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QEvent

from vred_submitter.ui.components.scene_settings_widget import SceneSettingsWidget
from vred_submitter.data_classes import RenderSubmitterUISettings


class TestSceneSettingsWidget:
    """Test SceneSettingsWidget for render settings UI management."""

    @pytest.fixture
    def initial_settings(self):
        return RenderSubmitterUISettings()

    @pytest.fixture
    def mock_parent(self, qapp):
        return Mock(spec=QWidget)

    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks")
    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator")
    @patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox")
    def test_init(
        self,
        mock_custom_group_box,
        mock_populator_class,
        mock_callbacks_class,
        initial_settings,
        mock_parent,
        qapp,
    ):
        mock_callbacks = Mock()
        mock_callbacks_class.return_value = mock_callbacks
        mock_populator = Mock()
        mock_populator_class.return_value = mock_populator

        # Set up mock CustomGroupBox to return objects with layout() method
        mock_group_box_instance = Mock()
        mock_layout = Mock()
        mock_layout.addLayout = Mock()
        mock_group_box_instance.layout.return_value = mock_layout
        mock_custom_group_box.return_value = mock_group_box_instance

        widget = SceneSettingsWidget(initial_settings, mock_parent)

        assert widget.init_complete
        assert widget.parent == mock_parent
        assert widget.callbacks == mock_callbacks
        assert widget.populator == mock_populator

        mock_callbacks_class.assert_called_once_with(widget)
        mock_populator_class.assert_called_once_with(widget, initial_settings)
        mock_populator.populate_post_ui_setup.assert_called_once()

    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks")
    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator")
    @patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox")
    def test_event_filter_close_event(
        self,
        mock_custom_group_box,
        mock_populator_class,
        mock_callbacks_class,
        initial_settings,
        mock_parent,
        qapp,
    ):
        mock_callbacks = Mock()
        mock_callbacks_class.return_value = mock_callbacks
        mock_populator = Mock()
        mock_populator_class.return_value = mock_populator

        # Set up mock CustomGroupBox
        mock_group_box_instance = Mock()
        mock_layout = Mock()
        mock_layout.addLayout = Mock()
        mock_group_box_instance.layout.return_value = mock_layout
        mock_custom_group_box.return_value = mock_group_box_instance

        widget = SceneSettingsWidget(initial_settings, mock_parent)

        # Test close event
        close_event = Mock()
        close_event.type.return_value = QEvent.Close

        result = widget.eventFilter(mock_parent, close_event)

        assert not result
        mock_callbacks.deregister_all_callbacks.assert_called_once()

    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks")
    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator")
    @patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox")
    def test_event_filter_other_event(
        self,
        mock_custom_group_box,
        mock_populator_class,
        mock_callbacks_class,
        initial_settings,
        mock_parent,
        qapp,
    ):
        mock_callbacks = Mock()
        mock_callbacks_class.return_value = mock_callbacks
        mock_populator = Mock()
        mock_populator_class.return_value = mock_populator

        # Set up mock CustomGroupBox
        mock_group_box_instance = Mock()
        mock_layout = Mock()
        mock_layout.addLayout = Mock()
        mock_group_box_instance.layout.return_value = mock_layout
        mock_custom_group_box.return_value = mock_group_box_instance

        widget = SceneSettingsWidget(initial_settings, mock_parent)

        # Test non-close event
        other_event = Mock()
        other_event.type.return_value = QEvent.MouseButtonPress

        with patch.object(QWidget, "eventFilter") as mock_super_event_filter:
            mock_super_event_filter.return_value = True

            result = widget.eventFilter(mock_parent, other_event)

            assert result
            mock_callbacks.deregister_all_callbacks.assert_not_called()
            mock_super_event_filter.assert_called_once_with(mock_parent, other_event)

    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks")
    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator")
    @patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox")
    def test_build_ui_creates_layouts(
        self,
        mock_custom_group_box,
        mock_populator_class,
        mock_callbacks_class,
        initial_settings,
        qapp,
    ):
        mock_callbacks = Mock()
        mock_callbacks_class.return_value = mock_callbacks
        mock_populator = Mock()
        mock_populator_class.return_value = mock_populator

        # Set up mock CustomGroupBox
        mock_group_box_instance = Mock()
        mock_layout = Mock()
        mock_layout.addLayout = Mock()
        mock_group_box_instance.layout.return_value = mock_layout
        mock_custom_group_box.return_value = mock_group_box_instance

        # Provide a mock parent since the widget expects one
        mock_parent = Mock()
        mock_parent.installEventFilter = Mock()
        widget = SceneSettingsWidget(initial_settings, mock_parent)

        # Check that group boxes are created
        assert hasattr(widget, "group_box_render_options")
        assert hasattr(widget, "group_box_sequencer_options")
        assert hasattr(widget, "group_box_tiling_settings")

    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks")
    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator")
    @patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox")
    def test_build_general_options_creates_widgets(
        self,
        mock_custom_group_box,
        mock_populator_class,
        mock_callbacks_class,
        initial_settings,
        qapp,
    ):
        mock_callbacks = Mock()
        mock_callbacks_class.return_value = mock_callbacks
        mock_populator = Mock()
        mock_populator_class.return_value = mock_populator

        # Set up mock CustomGroupBox
        mock_group_box_instance = Mock()
        mock_layout = Mock()
        mock_layout.addLayout = Mock()
        mock_group_box_instance.layout.return_value = mock_layout
        mock_custom_group_box.return_value = mock_group_box_instance

        # Provide a mock parent since the widget expects one
        mock_parent = Mock()
        mock_parent.installEventFilter = Mock()
        widget = SceneSettingsWidget(initial_settings, mock_parent)

        # Check that job type widgets are created
        assert hasattr(widget, "render_job_type_label")
        assert hasattr(widget, "render_job_type_widget")

    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks")
    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator")
    @patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox")
    def test_build_render_options_creates_widgets(
        self,
        mock_custom_group_box,
        mock_populator_class,
        mock_callbacks_class,
        initial_settings,
        qapp,
    ):
        mock_callbacks = Mock()
        mock_callbacks_class.return_value = mock_callbacks
        mock_populator = Mock()
        mock_populator_class.return_value = mock_populator

        # Set up mock CustomGroupBox
        mock_group_box_instance = Mock()
        mock_layout = Mock()
        mock_layout.addLayout = Mock()
        mock_group_box_instance.layout.return_value = mock_layout
        mock_custom_group_box.return_value = mock_group_box_instance

        # Provide a mock parent since the widget expects one
        mock_parent = Mock()
        mock_parent.installEventFilter = Mock()
        widget = SceneSettingsWidget(initial_settings, mock_parent)

        # Check that render option widgets are created
        assert hasattr(widget, "render_output_label")
        assert hasattr(widget, "render_output_widget")
        assert hasattr(widget, "render_output_button")
        assert hasattr(widget, "render_view_widget")
        assert hasattr(widget, "render_quality_widget")
        assert hasattr(widget, "dlss_quality_widget")
        assert hasattr(widget, "ss_quality_widget")
        assert hasattr(widget, "render_animation_widget")
        assert hasattr(widget, "gpu_ray_tracing_widget")
        assert hasattr(widget, "animation_type_widget")
        assert hasattr(widget, "animation_clip_widget")
        assert hasattr(widget, "use_clip_range_widget")
        assert hasattr(widget, "frame_range_widget")
        assert hasattr(widget, "frames_per_task_widget")
        assert hasattr(widget, "image_size_presets_widget")
        assert hasattr(widget, "image_size_x_widget")
        assert hasattr(widget, "image_size_y_widget")
        assert hasattr(widget, "printing_size_x_widget")
        assert hasattr(widget, "printing_size_y_widget")
        assert hasattr(widget, "resolution_widget")

    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks")
    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator")
    @patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox")
    def test_build_sequencer_options_creates_widgets(
        self,
        mock_custom_group_box,
        mock_populator_class,
        mock_callbacks_class,
        initial_settings,
        qapp,
    ):
        mock_callbacks = Mock()
        mock_callbacks_class.return_value = mock_callbacks
        mock_populator = Mock()
        mock_populator_class.return_value = mock_populator

        # Set up mock CustomGroupBox
        mock_group_box_instance = Mock()
        mock_layout = Mock()
        mock_layout.addLayout = Mock()
        mock_group_box_instance.layout.return_value = mock_layout
        mock_custom_group_box.return_value = mock_group_box_instance

        # Provide a mock parent since the widget expects one
        mock_parent = Mock()
        mock_parent.installEventFilter = Mock()
        widget = SceneSettingsWidget(initial_settings, mock_parent)

        # Check that sequencer option widgets are created
        assert hasattr(widget, "sequence_name_label")
        assert hasattr(widget, "sequence_name_widget")

    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks")
    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator")
    @patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox")
    def test_build_tiling_settings_creates_widgets(
        self,
        mock_custom_group_box,
        mock_populator_class,
        mock_callbacks_class,
        initial_settings,
        qapp,
    ):
        mock_callbacks = Mock()
        mock_callbacks_class.return_value = mock_callbacks
        mock_populator = Mock()
        mock_populator_class.return_value = mock_populator

        # Set up mock CustomGroupBox
        mock_group_box_instance = Mock()
        mock_layout = Mock()
        mock_layout.addLayout = Mock()
        mock_group_box_instance.layout.return_value = mock_layout
        mock_custom_group_box.return_value = mock_group_box_instance

        # Provide a mock parent since the widget expects one
        mock_parent = Mock()
        mock_parent.installEventFilter = Mock()
        widget = SceneSettingsWidget(initial_settings, mock_parent)

        # Check that tiling setting widgets are created
        assert hasattr(widget, "enable_region_rendering_widget")
        assert hasattr(widget, "tiles_in_x_label")
        assert hasattr(widget, "tiles_in_x_widget")
        assert hasattr(widget, "tiles_in_y_label")
        assert hasattr(widget, "tiles_in_y_widget")

    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks")
    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator")
    @patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox")
    def test_update_settings(
        self,
        mock_custom_group_box,
        mock_populator_class,
        mock_callbacks_class,
        initial_settings,
        qapp,
    ):
        mock_callbacks = Mock()
        mock_callbacks_class.return_value = mock_callbacks
        mock_populator = Mock()
        mock_populator_class.return_value = mock_populator

        # Set up mock CustomGroupBox
        mock_group_box_instance = Mock()
        mock_layout = Mock()
        mock_layout.addLayout = Mock()
        mock_group_box_instance.layout.return_value = mock_layout
        mock_custom_group_box.return_value = mock_group_box_instance

        # Provide a mock parent since the widget expects one
        mock_parent = Mock()
        mock_parent.installEventFilter = Mock()
        widget = SceneSettingsWidget(initial_settings, mock_parent)

        test_settings = RenderSubmitterUISettings()
        widget.update_settings(test_settings)

        mock_populator.update_settings_callback.assert_called_once_with(test_settings)

    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks")
    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator")
    @patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox")
    def test_widget_properties_and_validators(
        self,
        mock_custom_group_box,
        mock_populator_class,
        mock_callbacks_class,
        initial_settings,
        qapp,
    ):
        mock_callbacks = Mock()
        mock_callbacks_class.return_value = mock_callbacks
        mock_populator = Mock()
        mock_populator_class.return_value = mock_populator

        # Set up mock CustomGroupBox
        mock_group_box_instance = Mock()
        mock_layout = Mock()
        mock_layout.addLayout = Mock()
        mock_group_box_instance.layout.return_value = mock_layout
        mock_custom_group_box.return_value = mock_group_box_instance

        # Provide a mock parent since the widget expects one
        mock_parent = Mock()
        mock_parent.installEventFilter = Mock()
        widget = SceneSettingsWidget(initial_settings, mock_parent)

        # Test that widgets have proper validators and properties set
        assert widget.render_output_widget.validator() is not None
        assert widget.frame_range_widget.validator() is not None
        assert widget.image_size_x_widget.validator() is not None
        assert widget.image_size_y_widget.validator() is not None
        assert widget.printing_size_x_widget.validator() is not None
        assert widget.printing_size_y_widget.validator() is not None
        assert widget.resolution_widget.validator() is not None

        # Test spin box ranges
        assert widget.frames_per_task_widget.minimum() > 0
        assert widget.frames_per_task_widget.maximum() > widget.frames_per_task_widget.minimum()
        assert widget.tiles_in_x_widget.minimum() > 0
        assert widget.tiles_in_x_widget.maximum() > widget.tiles_in_x_widget.minimum()
        assert widget.tiles_in_y_widget.minimum() > 0
        assert widget.tiles_in_y_widget.maximum() > widget.tiles_in_y_widget.minimum()

    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks")
    @patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator")
    @patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox")
    def test_widget_tooltips_set(
        self,
        mock_custom_group_box,
        mock_populator_class,
        mock_callbacks_class,
        initial_settings,
        qapp,
    ):
        mock_callbacks = Mock()
        mock_callbacks_class.return_value = mock_callbacks
        mock_populator = Mock()
        mock_populator_class.return_value = mock_populator

        # Set up mock CustomGroupBox
        mock_group_box_instance = Mock()
        mock_layout = Mock()
        mock_layout.addLayout = Mock()
        mock_group_box_instance.layout.return_value = mock_layout
        mock_custom_group_box.return_value = mock_group_box_instance

        # Provide a mock parent since the widget expects one
        mock_parent = Mock()
        mock_parent.installEventFilter = Mock()
        widget = SceneSettingsWidget(initial_settings, mock_parent)

        # Test that labels have tooltips set
        assert widget.render_job_type_label.toolTip() != ""
        assert widget.render_output_label.toolTip() != ""
        assert widget.image_size_presets_label.toolTip() != ""
        assert widget.image_size_label.toolTip() != ""
        assert widget.printing_size_label.toolTip() != ""
        assert widget.resolution_label.toolTip() != ""
        assert widget.animation_type_label.toolTip() != ""
        assert widget.animation_clip_label.toolTip() != ""
        assert widget.frame_range_label.toolTip() != ""
        assert widget.frames_per_task_label.toolTip() != ""
        assert widget.sequence_name_label.toolTip() != ""
        assert widget.tiles_in_x_label.toolTip() != ""
        assert widget.tiles_in_y_label.toolTip() != ""

        # Test that checkboxes have tooltips set
        assert widget.render_animation_widget.toolTip() != ""
        assert widget.gpu_ray_tracing_widget.toolTip() != ""
        assert widget.use_clip_range_widget.toolTip() != ""
        assert widget.enable_region_rendering_widget.toolTip() != ""
