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

    @patch("vred_submitter.vred_logger.VREDLogger")
    def test_logger_does_not_include_debug_logging(self, mock_vred_logger):
        """Test that the logger used in vred_submitter doesn't include debug logging."""
        import logging

        mock_logger_instance = Mock()
        mock_vred_logger.return_value = mock_logger_instance

        # Set up the mock logger to have a level higher than DEBUG
        mock_logger_instance.level = logging.INFO
        mock_logger_instance.isEnabledFor.return_value = False

        # Import the module to trigger the logger initialization
        with patch("vred_submitter.vred_submitter.get_logger", return_value=mock_logger_instance):
            from vred_submitter.vred_submitter import _global_logger

            # Verify debug messages aren't logged
            _global_logger.debug("This is a debug message")

            # Verify the logger's level is not set to DEBUG
            assert _global_logger.level != logging.DEBUG

            # Verify debug messages aren't enabled
            assert not _global_logger.isEnabledFor(logging.DEBUG)

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
        mock_get_normalized_path.side_effect = str

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

    def test_parameter_values_input_validation_type_checking(self, submitter):
        settings = RenderSubmitterUISettings()
        settings.ImageWidth = "invalid_integer"  # Should be int
        settings.ImageHeight = 1080
        settings.GPURaytracing = "not_a_bool"  # Should be bool
        queue_parameters: list[dict] = []

        # Test that non-boolean values are handled correctly
        result = submitter._get_parameter_values(settings, queue_parameters)

        # Find the GPURaytracing parameter
        gpu_param = next((p for p in result if p["name"] == "GPURaytracing"), None)
        assert gpu_param is not None
        # Non-boolean should be converted to string representation
        assert gpu_param["value"] == "not_a_bool"

    def test_parameter_values_string_length_validation(self, submitter):
        settings = RenderSubmitterUISettings()
        # Test with excessively long string values
        settings.name = "a" * 1000  # Very long name
        settings.description = "b" * 2000  # Very long description
        queue_parameters: list[dict] = []

        result = submitter._get_parameter_values(settings, queue_parameters)

        # Should handle long strings without error
        name_param = next((p for p in result if p["name"] == "name"), None)
        assert name_param is not None
        assert len(name_param["value"]) == 1000

    def test_parameter_values_queue_conflict_validation(self, submitter):
        settings = RenderSubmitterUISettings()
        settings.ImageWidth = 1920
        # Create conflicting queue parameter
        queue_parameters = [{"name": "ImageWidth", "value": "different_value"}]

        with pytest.raises(Exception):  # DeadlineOperationError
            submitter._get_parameter_values(settings, queue_parameters)

    def test_job_bundle_callback_output_path_validation(self, submitter):
        widget = Mock()
        widget.job_attachments.attachments.input_filenames = ["test.vpb"]
        widget.job_attachments.attachments.input_directories = ["/test/dir"]

        settings = Mock()
        settings.OutputDir = "/nonexistent/path"  # Invalid path
        settings.OutputFileNamePrefix = "render"
        settings.OutputFormat = "PNG"
        settings.FrameStep = 1

        with patch("vred_submitter.vred_submitter.Scene") as mock_scene:
            mock_scene.name.return_value = "test_scene"
            with patch("vred_submitter.vred_submitter.os.path.exists") as mock_exists:
                mock_exists.return_value = False  # Path doesn't exist

                with pytest.raises(Exception):  # UserInitiatedCancel
                    submitter._create_job_bundle_callback(
                        widget, "/job/bundle", settings, [], Mock(), None
                    )

    def test_job_bundle_callback_filename_validation(self, submitter):
        widget = Mock()
        widget.job_attachments.attachments.input_filenames = ["test.vpb"]
        widget.job_attachments.attachments.input_directories = ["/test/dir"]

        settings = Mock()
        settings.OutputDir = "/valid/path"
        settings.OutputFileNamePrefix = "invalid<>filename"  # Invalid characters
        settings.OutputFormat = "PNG"
        settings.FrameStep = 1

        with patch("vred_submitter.vred_submitter.Scene") as mock_scene:
            mock_scene.name.return_value = "test_scene"
            with patch("vred_submitter.vred_submitter.os.path.exists") as mock_exists:
                mock_exists.return_value = True
                with patch("vred_submitter.vred_submitter.is_valid_filename") as mock_valid:
                    mock_valid.return_value = False  # Invalid filename

                    with pytest.raises(Exception):  # UserInitiatedCancel
                        submitter._create_job_bundle_callback(
                            widget, "/job/bundle", settings, [], Mock(), None
                        )

    def test_job_bundle_callback_frame_step_validation(self, submitter):
        widget = Mock()
        widget.job_attachments.attachments.input_filenames = ["test.vpb"]
        widget.job_attachments.attachments.input_directories = ["/test/dir"]

        settings = Mock()
        settings.OutputDir = "/valid/path"
        settings.OutputFileNamePrefix = "render"
        settings.OutputFormat = "PNG"
        settings.FrameStep = 0  # Invalid frame step

        with patch("vred_submitter.vred_submitter.Scene") as mock_scene:
            mock_scene.name.return_value = "test_scene"
            with patch("vred_submitter.vred_submitter.os.path.exists") as mock_exists:
                mock_exists.return_value = True
                with patch("vred_submitter.vred_submitter.is_valid_filename") as mock_valid:
                    mock_valid.return_value = True

                    with pytest.raises(Exception):  # UserInitiatedCancel
                        submitter._create_job_bundle_callback(
                            widget, "/job/bundle", settings, [], Mock(), None
                        )

    def test_job_template_name_description_validation(self, submitter):
        settings = RenderSubmitterUISettings()
        # Test with empty/None values
        settings.name = None
        settings.description = None
        template = {"name": "Default Name", "description": "Default Description", "steps": []}

        result = submitter._get_job_template(template, settings)

        # Should keep default values when settings are None/empty
        assert result["name"] == "Default Name"
        assert result["description"] == "Default Description"

        # Test with valid values
        settings.name = "Valid Job Name"
        settings.description = "Valid Description"

        result = submitter._get_job_template(template, settings)

        assert result["name"] == "Valid Job Name"
        assert result["description"] == "Valid Description"

    def test_job_template_string_length_limits(self, submitter):
        settings = RenderSubmitterUISettings()
        # Test with very long strings
        settings.name = "a" * 500  # Very long name
        settings.description = "b" * 1000  # Very long description
        template = {"name": "Default", "description": "Default", "steps": []}

        result = submitter._get_job_template(template, settings)

        # Should handle long strings without truncation or error
        assert result["name"] == "a" * 500
        assert result["description"] == "b" * 1000

    def test_boolean_parameter_conversion_validation(self, submitter):
        settings = RenderSubmitterUISettings()
        settings.GPURaytracing = True
        settings.RegionRendering = False
        settings.RenderAnimation = True
        queue_parameters: list[dict] = []

        result = submitter._get_parameter_values(settings, queue_parameters)

        # Test that boolean values are converted to lowercase strings
        gpu_param = next((p for p in result if p["name"] == "GPURaytracing"), None)
        assert gpu_param is not None
        assert gpu_param["value"] == "true"

        region_param = next((p for p in result if p["name"] == "RegionRendering"), None)
        assert region_param is not None
        assert region_param["value"] == "false"

        render_param = next((p for p in result if p["name"] == "RenderAnimation"), None)
        assert render_param is not None
        assert render_param["value"] == "true"

    def test_shared_parameters_filtered_out(self, submitter):
        """Test that deadline-cloud shared parameters are filtered out of job bundle parameters."""
        settings = RenderSubmitterUISettings()
        settings.priority = 75
        settings.initial_status = "SUSPENDED"
        settings.max_failed_tasks_count = 10
        settings.max_retries_per_task = 3
        settings.max_worker_count = 5
        # Set some regular parameters that should be included
        settings.ImageWidth = 1920
        settings.OutputDir = "/test/output"
        queue_parameters: list[dict] = []

        result = submitter._get_parameter_values(settings, queue_parameters)

        # Shared parameters should NOT be included in job bundle parameters
        parameter_names = {param["name"] for param in result}
        shared_parameters = {
            "priority",
            "initial_status",
            "max_failed_tasks_count",
            "max_retries_per_task",
            "max_worker_count",
        }

        for shared_param in shared_parameters:
            assert (
                shared_param not in parameter_names
            ), f"Shared parameter '{shared_param}' should be filtered out"

        # Regular parameters should still be included
        assert "ImageWidth" in parameter_names
        assert "OutputDir" in parameter_names

    def test_text_elements_enforce_length_checks(self, submitter):
        import sys
        from unittest.mock import Mock

        try:
            # Create new mocks for Qt widgets
            class MockQWidget:
                setEnabled = Mock()
                installEventFilter = Mock()

                def __init__(self, parent=None):
                    pass

            mock_q_widgets = Mock()
            mock_line_edit = Mock()

            sys.modules["PySide6.QtWidgets"] = mock_q_widgets
            mock_q_widgets.QWidget = MockQWidget
            mock_q_widgets.QLineEdit = mock_line_edit

            # Reload SceneSettingsWidget with new mocks
            if "vred_submitter.ui.components.scene_settings_widget" in sys.modules:
                del sys.modules["vred_submitter.ui.components.scene_settings_widget"]
            from vred_submitter.ui.components.scene_settings_widget import SceneSettingsWidget

            # Mock required dependencies
            with patch("vred_submitter.ui.components.scene_settings_widget.SceneSettingsCallbacks"):
                with patch(
                    "vred_submitter.ui.components.scene_settings_widget.SceneSettingsPopulator"
                ):
                    with patch("vred_submitter.ui.components.scene_settings_widget.CustomGroupBox"):
                        # Create the scene widget
                        mock_parent = MockQWidget()
                        SceneSettingsWidget(Mock(), mock_parent)

                        # Verify that line edits are created and some have max length constraints
                        assert mock_line_edit.call_count > 0
                        assert mock_line_edit.return_value.setMaxLength.call_count > 0
        finally:
            # Reset Qt widgets mock
            sys.modules["PySide6.QtWidgets"] = Mock()

    def test_render_submitter_ui_settings_validation(self, submitter):
        settings = RenderSubmitterUISettings()

        # Test string length validation
        settings.name = "a" * 500
        settings.description = "b" * 1000
        settings.OutputFileNamePrefix = "c" * 100

        template = {"name": "default", "description": "default", "steps": []}
        result = submitter._get_job_template(template, settings)

        # Should handle long strings without truncation
        assert len(result["name"]) == 500
        assert len(result["description"]) == 1000

        # Test parameter conversion
        queue_parameters: list[dict] = []
        params = submitter._get_parameter_values(settings, queue_parameters)

        prefix_param = next((p for p in params if p["name"] == "OutputFileNamePrefix"), None)
        assert prefix_param is not None
        assert len(prefix_param["value"]) == 100
