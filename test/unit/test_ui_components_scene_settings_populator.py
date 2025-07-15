# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for SceneSettingsPopulator UI data population and persistence."""
import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QWidget

from vred_submitter.ui.components.scene_settings_populator import (
    SceneSettingsPopulator,
    PersistedUISettingsNames,
)
from vred_submitter.data_classes import RenderSubmitterUISettings


class TestPersistedUISettingsNames:
    """Test PersistedUISettingsNames enum for UI state persistence."""

    def test_enum_values(self):
        # Test key enum values are lowercase versions of names
        assert PersistedUISettingsNames.ANIMATION_TYPE == "animation_type"
        assert PersistedUISettingsNames.JOB_TYPE == "job_type"
        assert PersistedUISettingsNames.RENDER_QUALITY == "render_quality"
        assert PersistedUISettingsNames.VIEW == "view"


class TestSceneSettingsPopulator:
    """Test SceneSettingsPopulator for UI widget data population and settings management."""

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
            "render_output_widget",
            "render_quality_widget",
            "render_view_widget",
            "resolution_widget",
            "ss_quality_widget",
            "sequence_name_widget",
            "tiles_in_x_widget",
            "tiles_in_y_widget",
            "use_clip_range_widget",
        ]
        for widget_name in widget_names:
            setattr(parent, widget_name, Mock())

        parent.callbacks = Mock()
        return parent

    @pytest.fixture
    def initial_settings(self):
        settings = RenderSubmitterUISettings()
        settings.AnimationClip = "test_clip"
        settings.AnimationType = "Clip"
        settings.DLSSQuality = "High"
        settings.ImageWidth = 1920
        settings.ImageHeight = 1080
        settings.OutputDir = "/output"
        settings.OutputFileNamePrefix = "render"
        settings.OutputFormat = "PNG"
        return settings

    @patch("vred_submitter.ui.components.scene_settings_populator.get_views_list")
    @patch("vred_submitter.ui.components.scene_settings_populator.get_animation_clips_list")
    @patch("vred_submitter.ui.components.scene_settings_populator.get_all_sequences")
    @patch(
        "vred_submitter.ui.components.scene_settings_populator.get_populated_animation_clip_ranges"
    )
    def test_init_new_persisted_settings(
        self,
        mock_get_ranges,
        mock_get_sequences,
        mock_get_clips,
        mock_get_views,
        mock_parent,
        initial_settings,
    ):
        # Reset class variable to simulate first time initialization
        SceneSettingsPopulator.persisted_ui_settings_states = None

        mock_get_views.return_value = ["Camera1", "Camera2"]
        mock_get_clips.return_value = ["", "clip1", "clip2"]
        mock_get_sequences.return_value = ["seq1", "seq2"]
        mock_get_ranges.return_value = {"clip1": [1, 100]}

        with (
            patch.object(SceneSettingsPopulator, "_store_runtime_derived_settings") as mock_store,
            patch.object(
                SceneSettingsPopulator, "_configure_ui_persisted_settings"
            ) as mock_configure,
        ):

            populator = SceneSettingsPopulator(mock_parent, initial_settings)

            assert populator.parent == mock_parent
            assert populator.animation_clip_ranges_map == {"clip1": [1, 100]}
            mock_store.assert_called_once_with(initial_settings)
            mock_configure.assert_called_once_with(initial_settings)

    @patch("vred_submitter.ui.components.scene_settings_populator.get_views_list")
    @patch("vred_submitter.ui.components.scene_settings_populator.get_animation_clips_list")
    @patch("vred_submitter.ui.components.scene_settings_populator.get_all_sequences")
    def test_init_existing_persisted_settings(
        self, mock_get_sequences, mock_get_clips, mock_get_views, mock_parent, initial_settings
    ):
        # Set up existing persisted settings
        SceneSettingsPopulator.persisted_ui_settings_states = Mock()

        mock_get_views.return_value = ["Camera1"]
        mock_get_clips.return_value = [""]
        mock_get_sequences.return_value = ["seq1"]

        with (
            patch.object(SceneSettingsPopulator, "_store_runtime_derived_settings") as mock_store,
            patch.object(
                SceneSettingsPopulator, "_configure_ui_persisted_settings"
            ) as mock_configure,
        ):

            SceneSettingsPopulator(mock_parent, initial_settings)

            # Should not call store and configure when persisted settings exist
            mock_store.assert_not_called()
            mock_configure.assert_not_called()

    @patch("vred_submitter.ui.components.scene_settings_populator.get_file_name_path_components")
    @patch("vred_submitter.ui.components.scene_settings_populator.get_render_filename")
    @patch("vred_submitter.ui.components.scene_settings_populator.get_animation_clip")
    def test_store_runtime_derived_settings(
        self, mock_get_clip, mock_get_render_filename, mock_get_components
    ):
        mock_get_render_filename.return_value = "/output/render.png"
        mock_get_components.return_value = ("/output", "render", "png")
        mock_get_clip.return_value = "test_clip"

        settings = RenderSubmitterUISettings()

        with (
            patch(
                "vred_submitter.ui.components.scene_settings_populator.get_animation_type"
            ) as mock_get_type,
            patch(
                "vred_submitter.ui.components.scene_settings_populator.get_dlss_quality"
            ) as mock_get_dlss,
            patch(
                "vred_submitter.ui.components.scene_settings_populator.get_frame_stop"
            ) as mock_get_stop,
            patch(
                "vred_submitter.ui.components.scene_settings_populator.get_frame_step"
            ) as mock_get_step,
            patch(
                "vred_submitter.ui.components.scene_settings_populator.get_use_gpu_ray_tracing"
            ) as mock_get_gpu,
        ):

            mock_get_type.return_value = "Timeline"
            mock_get_dlss.return_value = "Quality"
            mock_get_stop.return_value = 100
            mock_get_step.return_value = 2
            mock_get_gpu.return_value = True

            SceneSettingsPopulator._store_runtime_derived_settings(settings)

            assert settings.AnimationClip == "test_clip"
            assert settings.AnimationType == "Timeline"
            assert settings.DLSSQuality == "Quality"
            assert settings.EndFrame == 100
            assert settings.FrameStep == 2
            assert settings.GPURaytracing
            assert settings.OutputDir == "/output"
            assert settings.OutputFileNamePrefix == "render"
            assert settings.OutputFormat == "PNG"

    def test_configure_ui_persisted_settings(self):
        settings = RenderSubmitterUISettings()
        settings.AnimationClip = "test_clip"
        settings.AnimationType = "Clip"
        settings.DLSSQuality = "High"
        settings.RegionRendering = True
        settings.StartFrame = 1
        settings.EndFrame = 100
        settings.FramesPerTask = 5
        settings.ImageWidth = 1920
        settings.ImageHeight = 1080
        settings.JobType = "Render"
        settings.RenderAnimation = True
        settings.OutputDir = "/output"
        settings.OutputFileNamePrefix = "render"
        settings.OutputFormat = "PNG"

        # Initialize persisted settings
        from vred_submitter.utils import DynamicKeyValueObject

        SceneSettingsPopulator.persisted_ui_settings_states = DynamicKeyValueObject(
            {str(key).lower(): "" for key in PersistedUISettingsNames}
        )

        SceneSettingsPopulator._configure_ui_persisted_settings(settings)

        assert SceneSettingsPopulator.persisted_ui_settings_states.animation_clip == "test_clip"
        assert SceneSettingsPopulator.persisted_ui_settings_states.animation_type == "Clip"
        assert SceneSettingsPopulator.persisted_ui_settings_states.dlss_quality == "High"
        assert SceneSettingsPopulator.persisted_ui_settings_states.enable_render_regions
        assert SceneSettingsPopulator.persisted_ui_settings_states.frame_range == "1-100"
        assert SceneSettingsPopulator.persisted_ui_settings_states.frames_per_task == 5

    def test_populate_post_ui_setup(self, mock_parent, initial_settings):
        SceneSettingsPopulator.persisted_ui_settings_states = Mock()

        with (
            patch("vred_submitter.ui.components.scene_settings_populator.get_views_list"),
            patch("vred_submitter.ui.components.scene_settings_populator.get_animation_clips_list"),
            patch("vred_submitter.ui.components.scene_settings_populator.get_all_sequences"),
        ):

            populator = SceneSettingsPopulator(mock_parent, initial_settings)

            # Mock additional widgets needed for post setup
            mock_parent.render_quality_widget.get_width.return_value = 100
            mock_parent.dlss_quality_widget.get_width.return_value = 120
            mock_parent.ss_quality_widget.get_width.return_value = 110
            mock_parent.animation_type_widget.get_width.return_value = 90
            mock_parent.image_size_presets_widget.get_width.return_value = 150
            mock_parent.animation_clip_widget.setFixedWidth = Mock()
            mock_parent.image_size_x_widget.text.return_value = "1920"
            mock_parent.image_size_y_widget.text.return_value = "1080"
            mock_parent.resolution_widget.text.return_value = "72"

            populator.populate_post_ui_setup()

            # Should emit signals to trigger callbacks
            mock_parent.enable_region_rendering_widget.stateChanged.emit.assert_called_once()
            mock_parent.render_animation_widget.stateChanged.emit.assert_called_once()
            mock_parent.animation_type_widget.currentIndexChanged.emit.assert_called_once()

            # Should set uniform width for widgets
            mock_parent.animation_clip_widget.setFixedWidth.assert_called_with(150)  # max width

    @patch("vred_submitter.ui.components.scene_settings_populator.get_frame_range_components")
    @patch("vred_submitter.ui.components.scene_settings_populator.get_file_name_path_components")
    @patch("vred_submitter.ui.components.scene_settings_populator.get_normalized_path")
    def test_update_settings_callback(
        self,
        mock_get_normalized,
        mock_get_components,
        mock_get_frame_components,
        mock_parent,
        initial_settings,
    ):
        SceneSettingsPopulator.persisted_ui_settings_states = Mock()

        with (
            patch("vred_submitter.ui.components.scene_settings_populator.get_views_list"),
            patch("vred_submitter.ui.components.scene_settings_populator.get_animation_clips_list"),
            patch("vred_submitter.ui.components.scene_settings_populator.get_all_sequences"),
        ):

            populator = SceneSettingsPopulator(mock_parent, initial_settings)

            # Set up mocks for update_settings_callback
            mock_get_frame_components.return_value = (1, 100, 2)
            mock_get_components.return_value = ("/output", "render", "png")
            mock_get_normalized.return_value = "/output"

            # Mock widget values
            mock_parent.frame_range_widget.text.return_value = "1-100x2"
            mock_parent.render_output_widget.text.return_value = "/output/render.png"
            mock_parent.animation_clip_widget.currentText.return_value = "test_clip"
            mock_parent.animation_type_widget.currentText.return_value = "Clip"
            mock_parent.dlss_quality_widget.currentText.return_value = "High"
            mock_parent.resolution_widget.text.return_value = "72"
            mock_parent.frames_per_task_widget.value.return_value = 5
            mock_parent.gpu_ray_tracing_widget.isChecked.return_value = True
            mock_parent.image_size_y_widget.text.return_value = "1080"
            mock_parent.image_size_x_widget.text.return_value = "1920"
            mock_parent.render_job_type_widget.currentText.return_value = "Render"
            mock_parent.tiles_in_x_widget.value.return_value = 2
            mock_parent.tiles_in_y_widget.value.return_value = 2
            mock_parent.enable_region_rendering_widget.isChecked.return_value = True
            mock_parent.render_animation_widget.isChecked.return_value = True
            mock_parent.render_quality_widget.currentText.return_value = "High"
            mock_parent.ss_quality_widget.currentText.return_value = "Medium"
            mock_parent.sequence_name_widget.currentText.return_value = "seq1"
            mock_parent.render_view_widget.currentText.return_value = "Camera1"

            settings = RenderSubmitterUISettings()

            with (
                patch(
                    "vred_submitter.ui.components.scene_settings_populator.get_render_alpha"
                ) as mock_get_alpha,
                patch(
                    "vred_submitter.ui.components.scene_settings_populator.get_premultiply_alpha"
                ) as mock_get_premult,
                patch(
                    "vred_submitter.ui.components.scene_settings_populator.get_scene_full_path"
                ) as mock_get_scene,
                patch(
                    "vred_submitter.ui.components.scene_settings_populator.get_tonemap_hdr"
                ) as mock_get_tonemap,
            ):

                mock_get_alpha.return_value = False
                mock_get_premult.return_value = False
                mock_get_scene.return_value = "/scene/test.vpb"
                mock_get_tonemap.return_value = False

                populator.update_settings_callback(settings)

                assert settings.StartFrame == 1
                assert settings.EndFrame == 100
                assert settings.FrameStep == 2
                assert settings.AnimationClip == "test_clip"
                assert settings.AnimationType == "Clip"
                assert settings.DLSSQuality == "High"
                assert settings.DPI == 72
                assert settings.FramesPerTask == 5
                assert settings.GPURaytracing
                assert settings.ImageHeight == 1080
                assert settings.ImageWidth == 1920
                assert settings.JobType == "Render"
                assert settings.NumXTiles == 2
                assert settings.NumYTiles == 2
                assert settings.OutputDir == "/output"
                assert settings.OutputFileNamePrefix == "render"
                assert settings.OutputFormat == "PNG"
                assert settings.RegionRendering
                assert settings.RenderAnimation
                assert settings.RenderQuality == "High"
                assert settings.SSQuality == "Medium"
                assert settings.SceneFile == "/scene/test.vpb"
                assert settings.SequenceName == "seq1"
                assert settings.View == "Camera1"
