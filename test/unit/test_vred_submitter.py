# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for VREDSubmitter main class functionality."""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from PySide6.QtCore import Qt

from vred_submitter.vred_submitter import VREDSubmitter
from vred_submitter.data_classes import RenderSubmitterUISettings


class TestVREDSubmitter:
    """Test VREDSubmitter class for job submission functionality."""

    @pytest.fixture
    def mock_parent_window(self):
        # Mock parent window for submitter dialog
        return Mock()

    @pytest.fixture
    @patch("vred_submitter.vred_submitter.get_yaml_contents")
    def submitter(self, mock_get_yaml_contents, mock_parent_window):
        # Create submitter instance with mocked template
        mock_get_yaml_contents.return_value = {"test": "template"}
        return VREDSubmitter(mock_parent_window)

    @patch("vred_submitter.vred_submitter.get_yaml_contents")
    def test_init(self, mock_get_yaml_contents, mock_parent_window):
        # Test submitter initialization with template loading
        mock_template = {"name": "test_template"}
        mock_get_yaml_contents.return_value = mock_template

        submitter = VREDSubmitter(mock_parent_window, Qt.WindowFlags())

        assert submitter.parent_window == mock_parent_window
        assert submitter.window_flags == Qt.WindowFlags()
        assert submitter.default_job_template == mock_template

    def test_get_job_template_basic(self, submitter):
        # Test job template generation with basic settings
        settings = RenderSubmitterUISettings()
        settings.name = "Test Job"
        settings.description = "Test Description"
        settings.RegionRendering = False

        template = {
            "name": "Default Name",
            "description": "Default Description",
            "steps": [{"name": "Render Step"}, {"name": "Tile Assembly"}],
        }

        result = submitter._get_job_template(template, settings)

        assert result["name"] == "Test Job"
        assert result["description"] == "Test Description"
        # Should exclude Tile Assembly step when RegionRendering is False
        step_names = [step["name"] for step in result["steps"]]
        assert "Tile Assembly" not in step_names
        assert "Render Step" in step_names

    def test_get_job_template_region_rendering_disabled(self, submitter):
        settings = RenderSubmitterUISettings()
        settings.RegionRendering = False
        template = {
            "steps": [{"name": "Render Step"}, {"name": "Tile Assembly"}, {"name": "Other Step"}]
        }

        result = submitter._get_job_template(template, settings)

        # Should exclude Tile Assembly step
        step_names = [step["name"] for step in result["steps"]]
        assert "Tile Assembly" not in step_names
        assert "Render Step" in step_names
        assert "Other Step" in step_names

    def test_get_parameter_values_basic(self, submitter):
        settings = RenderSubmitterUISettings()
        settings.ImageWidth = 1920
        settings.ImageHeight = 1080
        settings.GPURaytracing = True
        queue_parameters: list[dict] = []

        result = submitter._get_parameter_values(settings, queue_parameters)

        # Should convert bool to string
        gpu_param = next((p for p in result if p["name"] == "GPURaytracing"), None)
        assert gpu_param is not None
        assert gpu_param["value"] == "true"

        # Should keep other values as-is
        width_param = next((p for p in result if p["name"] == "ImageWidth"), None)
        assert width_param is not None
        assert width_param["value"] == 1920

    def test_get_parameter_values_with_queue_params(self, submitter):
        settings = RenderSubmitterUISettings()
        queue_parameters = [{"name": "CustomParam", "value": "custom_value"}]

        result = submitter._get_parameter_values(settings, queue_parameters)

        # Should include queue parameters
        custom_param = next((p for p in result if p["name"] == "CustomParam"), None)
        assert custom_param is not None
        assert custom_param["value"] == "custom_value"

    def test_get_parameter_values_conflict_error(self, submitter):
        settings = RenderSubmitterUISettings()
        # Create conflict with existing parameter
        queue_parameters = [{"name": "ImageWidth", "value": "different_value"}]

        with pytest.raises(Exception):  # DeadlineOperationError
            submitter._get_parameter_values(settings, queue_parameters)

    @patch("vred_submitter.vred_submitter.center_widget")
    @patch("vred_submitter.vred_submitter.get_deadline_cloud_library_telemetry_client")
    def test_show_submitter(self, mock_telemetry_client, mock_center_widget, submitter):
        mock_client = Mock()
        mock_telemetry_client.return_value = mock_client

        with (
            patch.object(submitter, "_initialize_render_settings") as mock_init_settings,
            patch.object(submitter, "_setup_attachments") as mock_setup_attachments,
            patch.object(submitter, "_create_submitter_dialog") as mock_create_dialog,
        ):

            mock_settings = Mock()
            mock_init_settings.return_value = mock_settings
            mock_attachments = (Mock(), Mock())
            mock_setup_attachments.return_value = mock_attachments
            mock_dialog = Mock()
            mock_create_dialog.return_value = mock_dialog

            result = submitter.show_submitter()

            mock_init_settings.assert_called_once()
            mock_setup_attachments.assert_called_once_with(mock_settings)
            mock_create_dialog.assert_called_once_with(mock_settings, mock_attachments)
            mock_dialog.show.assert_called_once()
            mock_center_widget.assert_called_once_with(mock_dialog)
            assert result == mock_dialog

    @patch("vred_submitter.vred_submitter.Scene")
    def test_initialize_render_settings(self, mock_scene, submitter):
        mock_scene.name.return_value = "test_scene"
        mock_scene.get_input_filenames.return_value = ["test.vpb"]

        result = submitter._initialize_render_settings()

        assert isinstance(result, RenderSubmitterUISettings)
        assert result.name == "test_scene"
        assert result.input_filenames == ["test.vpb"]

    @patch("vred_submitter.vred_submitter.AssetIntrospector")
    @patch("vred_submitter.vred_submitter.AssetReferences")
    @patch("vred_submitter.vred_submitter.get_normalized_path")
    def test_setup_attachments(
        self, mock_get_normalized_path, mock_asset_references, mock_introspector_class, submitter
    ):
        mock_introspector = Mock()
        mock_introspector.parse_scene_assets.return_value = {
            Path("/test/asset1"),
            Path("/test/asset2"),
        }
        mock_introspector_class.return_value = mock_introspector
        mock_get_normalized_path.side_effect = lambda x: str(x)

        mock_auto_detected = Mock()
        mock_user_defined = Mock()
        mock_asset_references.side_effect = [mock_auto_detected, mock_user_defined]

        settings = RenderSubmitterUISettings()
        settings.input_filenames = ["test.vpb"]
        settings.input_directories = ["/test/dir"]
        settings.output_directories = ["/output/dir"]

        result = submitter._setup_attachments(settings)

        assert result == (mock_auto_detected, mock_user_defined)
        mock_introspector.parse_scene_assets.assert_called_once()

    @patch("vred_submitter.vred_submitter.os.getenv")
    @patch("vred_submitter.vred_submitter.get_major_version")
    @patch("vred_submitter.vred_submitter.get_dpi_scale_factor")
    @patch("vred_submitter.vred_submitter.SubmitJobToDeadlineDialog")
    def test_create_submitter_dialog(
        self, mock_dialog_class, mock_get_dpi_scale, mock_get_version, mock_getenv, submitter
    ):
        mock_get_version.return_value = "2023"
        mock_get_dpi_scale.return_value = 1.0
        mock_getenv.side_effect = lambda key, default=None: {
            "CONDA_PACKAGES": None,
            "CONDA_CHANNELS": "test-channel",
        }.get(key, default)

        mock_dialog = Mock()
        mock_dialog_class.return_value = mock_dialog

        settings = Mock()
        attachments = (Mock(), Mock())

        result = submitter._create_submitter_dialog(settings, attachments)

        assert result == mock_dialog
        mock_dialog_class.assert_called_once()
        mock_dialog.setMinimumSize.assert_called_once()

    @patch("vred_submitter.vred_submitter.is_scene_file_modified")
    @patch("vred_submitter.vred_submitter.Scene")
    @patch("vred_submitter.vred_submitter.is_valid_filename")
    @patch("vred_submitter.vred_submitter.os.path.exists")
    def test_create_job_bundle_callback_validation_success(
        self, mock_exists, mock_is_valid_filename, mock_scene, mock_is_modified, submitter
    ):
        mock_is_modified.return_value = False
        mock_scene.name.return_value = "test_scene"
        mock_exists.return_value = True
        mock_is_valid_filename.return_value = True

        widget = Mock()
        widget.job_attachments.attachments.input_filenames = ["test.vpb"]
        widget.job_attachments.attachments.input_directories = ["/test/dir"]

        settings = Mock()
        settings.OutputDir = "/output"
        settings.OutputFileNamePrefix = "render"
        settings.OutputFormat = "PNG"
        settings.FrameStep = 1

        with patch.object(submitter, "_create_job_bundle") as mock_create_bundle:
            submitter._create_job_bundle_callback(widget, "/job/bundle", settings, [], Mock(), None)

            mock_create_bundle.assert_called_once()

    @patch("vred_submitter.vred_submitter.Scene")
    def test_create_job_bundle_callback_no_scene_name(self, mock_scene, submitter):
        mock_scene.name.return_value = ""

        with pytest.raises(Exception):  # UserInitiatedCancel
            submitter._create_job_bundle_callback(Mock(), "/job/bundle", Mock(), [], Mock(), None)
