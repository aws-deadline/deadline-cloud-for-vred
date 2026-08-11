# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for VRED render script functionality."""

import json
import logging
import os
import sys
import tempfile
from unittest.mock import Mock, patch

import pytest
from vred_submitter.VRED_RenderScript_DeadlineCloud import DeadlineCloudRenderer, PathFormat

# Shared mock parameters for all test classes to reduce duplication
DEFAULT_MOCK_PARAMS = {
    "OutputDir": "/mock/output",
    "OutputFileNamePrefix": "test",
    "OutputFormat": "PNG",
    "RegionRendering": False,
    "TileNumberX": 1,
    "TileNumberY": 1,
    "NumXTiles": 1,
    "NumYTiles": 1,
    "RenderQuality": "Realistic High",
    "SSQuality": "Off",
    "DLSSQuality": "Off",
    "AnimationType": "Clip",
    "StartFrame": 0,
    "EndFrame": 10,
    "FrameStep": 1,
    "GPURaytracing": 0,
    "View": "Perspective",
    "PathMappingRulesFile": "",
    "RenderAnimation": True,
    "AnimationClip": "",
    "IncludeAlphaChannel": False,
    "PremultiplyAlpha": False,
    "TonemapHDR": False,
    "JobType": "Render",
    "SequenceName": "",
    "OverrideRenderPass": False,
    "ExportRenderPasses": False,
    "ImageHeight": 600,
    "ImageWidth": 800,
    "DPI": 72,
}


class TestDeadlineCloudRenderer:
    """Test DeadlineCloudRenderer class for render script functionality."""

    def get_mock_params(self):
        # Return mock parameters for renderer testing
        params = DEFAULT_MOCK_PARAMS.copy()
        params["PathMappingRulesFile"] = "/mock/path_mapping.json"
        return params

    def test_logging_level_not_debug(self):
        """Test that the logging level is not set to DEBUG."""
        # Verify the LOGGING_LEVEL constant is not set to DEBUG
        assert DeadlineCloudRenderer.LOGGING_LEVEL != logging.DEBUG
        assert DeadlineCloudRenderer.LOGGING_LEVEL == logging.INFO

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.logging")
    def test_logger_configured_with_non_debug_level(self, mock_logging):
        """Test that the logger is configured with a non-debug level."""
        # Setup
        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger
        mock_logging.DEBUG = logging.DEBUG
        mock_logging.INFO = logging.INFO

        # Create minimal mock parameters
        mock_params = self.get_mock_params()

        # Create a renderer with mocked dependencies
        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            # Don't need to store the renderer
            DeadlineCloudRenderer(mock_params)

            # Verify that basicConfig was called with the correct level
            mock_logging.basicConfig.assert_called_once()
            _args, kwargs = mock_logging.basicConfig.call_args
            assert kwargs["level"] == DeadlineCloudRenderer.LOGGING_LEVEL
            assert kwargs["level"] != logging.DEBUG

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.logging")
    def test_render_method_calls_terminate(self, mock_logging):
        """Test that render method calls terminateVred."""
        # Setup
        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger

        mock_params = self.get_mock_params()

        # Mock terminateVred directly
        mock_terminate_vred = Mock()

        with (
            patch(
                "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
                return_value=Mock(**mock_params),
            ),
            patch(
                "vred_submitter.VRED_RenderScript_DeadlineCloud.terminateVred", mock_terminate_vred
            ),
            patch("vred_submitter.VRED_RenderScript_DeadlineCloud.startRenderToFile"),
            patch(
                "vred_submitter.VRED_RenderScript_DeadlineCloud.getRenderFilename",
                return_value="/mock/output.png",
            ),
        ):

            renderer = DeadlineCloudRenderer(mock_params)

            # Mock methods
            renderer.validate_render_settings = Mock()
            renderer.init_file_references = Mock()
            renderer.init_render_settings = Mock()

            # Test
            renderer.render()

            # Verify - terminateVred is called twice (once in try block, once in finally block)
            assert mock_terminate_vred.call_count == 2

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.logging")
    def test_render_exception_handling(self, mock_logging):
        """Test render method exception handling."""
        # Setup
        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger

        mock_params = self.get_mock_params()

        # Mock terminateVred directly
        mock_terminate_vred = Mock()

        with (
            patch(
                "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
                return_value=Mock(**mock_params),
            ),
            patch(
                "vred_submitter.VRED_RenderScript_DeadlineCloud.terminateVred", mock_terminate_vred
            ),
        ):

            renderer = DeadlineCloudRenderer(mock_params)

            # Mock methods to throw exception
            renderer.validate_render_settings = Mock(side_effect=ValueError("Test error"))

            # Test
            renderer.render()

            # Verify
            mock_logger.error.assert_called()
            # terminateVred is called once in finally block for exception handling
            mock_terminate_vred.assert_called()


class TestGetConventionalOutputFilename:
    """Tests for _get_conventional_output_filename method"""

    def get_mock_params(self):
        # Return mock parameters for testing
        return DEFAULT_MOCK_PARAMS.copy()

    def test_standard_filename(self):
        """Test standard filename generation"""
        mock_params = self.get_mock_params()
        mock_params["RegionRendering"] = False

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            result = renderer._get_conventional_output_filename()
            assert "test" in result
            assert result.endswith(".png")

    def test_region_rendering_filename(self):
        """Test filename generation for region rendering"""
        mock_params = self.get_mock_params()
        mock_params["RegionRendering"] = True
        mock_params["TileNumberX"] = 2
        mock_params["TileNumberY"] = 3

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            result = renderer._get_conventional_output_filename()
            # Actual format is like "test3x2_1x1.png" not "_tile_2_3"
            assert "test" in result
            assert "x" in result


class TestValidateParameterInDictAndRenderSettings:
    """Tests for validate_parameter_in_dict method and the validate_render_settings method"""

    def get_mock_params(self):
        # Return mock parameters
        return DEFAULT_MOCK_PARAMS.copy()

    def test_missing_parameter(self):
        """Verify error handling for missing parameters"""
        mock_params = self.get_mock_params()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            with pytest.raises(ValueError):
                renderer.validate_parameter_in_dict("MissingKey", {}, "Error message")

    def test_type_validation(self):
        """Test parameter type validation and conversion"""
        mock_params = self.get_mock_params()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            # validate_parameter_in_dict doesn't do type conversion, just validation
            # It should not raise if key exists
            renderer.validate_parameter_in_dict("TestKey", {"TestKey": "123"}, "Not a Real Error")

    def test_invalid_frame_range(self):
        """Verify frame range validation logic"""
        mock_params = self.get_mock_params()
        mock_params["StartFrame"] = 10
        mock_params["EndFrame"] = 5

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            with pytest.raises(ValueError):
                renderer.validate_render_settings()


class TestMapPath:
    """Tests for map_path method"""

    def get_mock_params(self):
        # Return mock parameters
        return DEFAULT_MOCK_PARAMS.copy()

    def test_path_no_mapping_rules(self):
        """Test path mapping with no rules returns original path"""
        mock_params = self.get_mock_params()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.path_mapping_rules = []
            result = renderer.map_path("/test/path")
            assert result == "/test/path"

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="This test is for paths in Windows format and will be skipped on non-Windows systems.",
    )
    def test_path_mapping_happy_path_windows(self):
        """Test successful path mapping with Windows format"""

        mock_params = self.get_mock_params()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)

            # Create mock path mapping rules
            mock_rule_windows = Mock()
            mock_rule_windows.source_path_format = PathFormat.WINDOWS
            mock_rule_windows.source_path = "C:\\source"
            mock_rule_windows.destination_path = "/mnt/shared"

            renderer.path_mapping_rules = [mock_rule_windows]

            # Test Windows path mapping
            result = renderer.map_path("C:\\source\\file.txt")
            assert result == "\\mnt\\shared\\file.txt"

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="This test is for paths in POSIX format and will be skipped on Windows.",
    )
    def test_path_mapping_happy_path_posix(self):
        """Test successful path mapping with POSIX format"""

        mock_params = self.get_mock_params()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)

            # Create mock path mapping rules
            mock_rule_posix = Mock()
            mock_rule_posix.source_path_format = PathFormat.POSIX
            mock_rule_posix.source_path = "/local/data"
            mock_rule_posix.destination_path = "/remote/data"

            renderer.path_mapping_rules = [mock_rule_posix]

            # Test POSIX path mapping
            result = renderer.map_path("/local/data/file.txt")
            assert result == "/remote/data/file.txt"


class TestInitRenderQualityModes:
    """Tests for init_render_quality_modes method"""

    def get_mock_params(self):
        return DEFAULT_MOCK_PARAMS.copy()

    def test_quality_modes_initialization(self):
        """Test quality mode initialization executes"""
        mock_params = self.get_mock_params()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            # Just verify it can be called without error
            # VRED API functions are mocked in conftest
            renderer.init_render_quality_modes()


class TestPerformSequencerJob:
    """Tests for perform_sequencer_job method"""

    def get_mock_params(self):
        # Getting the parameter mock and adding parameter we need
        params = DEFAULT_MOCK_PARAMS.copy()
        params["JobType"] = "Sequencer"
        return params

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.runAllSequences")
    def test_run_all_sequences(self, mock_run_all):
        """Test running all sequences when no specific sequence name"""
        mock_params = self.get_mock_params()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.perform_sequencer_job()

            mock_run_all.assert_called_once()

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.runSequence")
    def test_run_specific_sequence(self, mock_run_seq):
        """Test running a specific sequence"""
        mock_params = self.get_mock_params()
        mock_params["SequenceName"] = "TestSequence"

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.perform_sequencer_job()

            mock_run_seq.assert_called_once_with("TestSequence")


class TestInitCameraView:
    """Tests for init_camera_view method"""

    def get_mock_params(self):
        return DEFAULT_MOCK_PARAMS.copy()

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.vrCameraService")
    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.setRenderView")
    def test_empty_view_name(self, mock_set_view, mock_camera_service):
        """Test with empty view name - should use current view"""
        mock_params = self.get_mock_params()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.init_camera_view("")

            mock_set_view.assert_not_called()

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.vrCameraService")
    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.setRenderView")
    def test_viewpoint_found(self, mock_set_view, mock_camera_service):
        """Test when viewpoint is found"""
        mock_params = self.get_mock_params()

        mock_vp = Mock()
        mock_vp.getName.return_value = "TestView"
        mock_camera_service.getAllViewpoints.return_value = [mock_vp]
        mock_camera_service.getCameraNames.return_value = []
        mock_camera_service.getViewpoint.return_value = Mock()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.init_camera_view("TestView")

            mock_set_view.assert_called_once_with("TestView")

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.vrCameraService")
    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.setRenderView")
    def test_camera_found(self, mock_set_view, mock_camera_service):
        """Test when camera is found but no viewpoint"""
        mock_params = self.get_mock_params()

        mock_camera_service.getAllViewpoints.return_value = []
        mock_camera_service.getCameraNames.return_value = ["TestCamera"]
        mock_camera_service.getCamera.return_value = Mock()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.init_camera_view("TestCamera")

            mock_set_view.assert_called_once_with("TestCamera")

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.vrCameraService")
    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.setRenderView")
    def test_view_not_found(self, mock_set_view, mock_camera_service):
        """Test when view name is not found in viewpoints or cameras"""
        mock_params = self.get_mock_params()

        mock_camera_service.getAllViewpoints.return_value = []
        mock_camera_service.getCameraNames.return_value = []

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.process_warning = Mock()
            renderer.init_camera_view("NonExistentView")

            mock_set_view.assert_not_called()
            renderer.process_warning.assert_called_once()

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.vrCameraService")
    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.setRenderView")
    def test_viewpoint_precedence_over_camera(self, mock_set_view, mock_camera_service):
        """Test viewpoint takes precedence when same name exists in both lists"""
        mock_params = self.get_mock_params()

        mock_vp = Mock()
        mock_vp.getName.return_value = "SameName"
        mock_camera_service.getAllViewpoints.return_value = [mock_vp]
        mock_camera_service.getCameraNames.return_value = ["SameName"]
        mock_camera_service.getViewpoint.return_value = Mock()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.init_camera_view("SameName")

            mock_set_view.assert_called_once_with("SameName")
            mock_camera_service.getViewpoint.assert_called_once_with("SameName")


class TestInitRenderAnimation:
    """Test for init_render_animation method"""

    def get_mock_params(self):
        return DEFAULT_MOCK_PARAMS.copy()

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.setRenderStartFrame")
    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.setRenderStopFrame")
    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.setRenderFrameStep")
    def test_animation_initialization(self, mock_step, mock_stop, mock_start):
        """Test animation settings initialization"""
        mock_params = self.get_mock_params()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.init_render_animation()

            mock_start.assert_called_once_with(0)
            mock_stop.assert_called_once_with(10)
            mock_step.assert_called_once_with(1)


class TestInitRenderRegion:
    """Tests for init_render_region method"""

    def get_mock_params(self):
        params = DEFAULT_MOCK_PARAMS.copy()
        params.update(
            {
                "RegionRendering": True,
                "TileNumberX": 2,
                "TileNumberY": 2,
                "NumXTiles": 2,
                "NumYTiles": 2,
            }
        )
        return params

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.setUseRenderRegion")
    def test_region_rendering_disabled(self, mock_set_use_region):
        """Test render region initialization when disabled"""
        mock_params = DEFAULT_MOCK_PARAMS.copy()
        mock_params["RegionRendering"] = False

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.init_render_region()

            mock_set_use_region.assert_called_once_with(False)

    def test_region_rendering_enabled(self):
        """Test render region initialization when enabled"""
        mock_params = self.get_mock_params()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            # Just verify it can be called without error
            # VRED API functions are mocked in conftest
            renderer.init_render_region()


class TestInitFileReferences:
    """Tests for init_file_references method"""

    def get_mock_params(self):
        return DEFAULT_MOCK_PARAMS.copy()

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.vrReferenceService")
    def test_file_references_with_smart_ref(self, mock_ref_service):
        """Test file reference remapping with smart references"""
        mock_params = self.get_mock_params()

        mock_node = Mock()
        mock_node.hasSmartReference.return_value = True
        mock_node.getSmartPath.return_value = "/original/path.jpg"
        mock_ref_service.getSceneReferences.return_value = [mock_node]

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.path_mapping_rules = []
            renderer.init_file_references()

            mock_node.setSmartPath.assert_called_once()

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.vrReferenceService")
    def test_file_references_with_source_ref(self, mock_ref_service):
        """Test file reference remapping with source references (else case)"""
        mock_params = self.get_mock_params()

        mock_node = Mock()
        mock_node.hasSmartReference.return_value = False
        mock_node.getSourcePath.return_value = "/original/source.jpg"
        mock_ref_service.getSceneReferences.return_value = [mock_node]

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.path_mapping_rules = []
            renderer.init_file_references()

            mock_node.setSourcePath.assert_called_once()


class TestLoadPathMappingRules:
    """Tests for load_path_mapping_rules method"""

    def get_mock_params(self):
        params = DEFAULT_MOCK_PARAMS.copy()
        params["PathMappingRulesFile"] = ""  # Use empty string instead of /tmp path
        return params

    def test_load_path_mapping_file_not_found(self):
        """Test path mapping rules loading with missing file"""
        mock_params = self.get_mock_params()

        with patch(
            "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
            return_value=Mock(**mock_params),
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            result = renderer.load_path_mapping_rules()

            assert result is False

    def test_load_path_mapping_rules_success(self):
        """Test successful path mapping rules loading"""
        mock_params = self.get_mock_params()

        # Create a temporary file with the mapping rules
        mapping_data = {
            "path_mapping_rules": [
                {
                    "source_path_format": "WINDOWS",
                    "source_path": "C:\\source",
                    "destination_path": "/dest",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            json.dump(mapping_data, temp_file)
            temp_file_path = temp_file.name

        try:
            # Update the mock params to use the temporary file
            mock_params["PathMappingRulesFile"] = temp_file_path

            renderer = DeadlineCloudRenderer(mock_params)
            result = renderer.load_path_mapping_rules()

            assert result is True
            assert len(renderer.path_mapping_rules) == 1
            assert renderer.path_mapping_rules[0].source_path == "C:\\source"
            assert renderer.path_mapping_rules[0].destination_path == "/dest"
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)


class TestInitRenderJob:
    """Tests for init_render_job method"""

    def get_mock_params(self):
        params = DEFAULT_MOCK_PARAMS.copy()
        params["RenderAnimation"] = False
        return params

    def test_render_job_no_animation(self):
        """Test render job initialization without animation"""
        mock_params = self.get_mock_params()

        with (
            patch(
                "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
                return_value=Mock(**mock_params),
            ),
            patch.object(DeadlineCloudRenderer, "init_render_animation") as mock_init_anim,
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.init_render_job()

            # Should not call init_render_animation when RenderAnimation is False
            mock_init_anim.assert_not_called()

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.setRenderAnimation")
    def test_render_job_with_animation(self, mock_set_animation):
        """Test render job initialization with animation"""
        mock_params = self.get_mock_params()
        mock_params["RenderAnimation"] = True

        with (
            patch(
                "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
                return_value=Mock(**mock_params),
            ),
            patch.object(DeadlineCloudRenderer, "init_camera_view") as mock_init_camera,
            patch.object(DeadlineCloudRenderer, "init_render_quality_modes") as mock_init_quality,
            patch.object(DeadlineCloudRenderer, "init_render_animation") as mock_init_anim,
        ):
            renderer = DeadlineCloudRenderer(mock_params)
            renderer.init_render_job()

            # Verify all methods were called
            mock_init_camera.assert_called_once()
            mock_init_quality.assert_called_once()
            mock_init_anim.assert_called_once()
            mock_set_animation.assert_called_once_with(True)
