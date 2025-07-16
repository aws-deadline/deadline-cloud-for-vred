# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for VRED render script functionality."""
import logging
from unittest.mock import Mock, patch, mock_open

from vred_submitter.VRED_RenderScript_DeadlineCloud import DeadlineCloudRenderer


class TestDeadlineCloudRenderer:
    """Test DeadlineCloudRenderer class for render script functionality."""

    def get_mock_params(self):
        """Return mock parameters for renderer testing."""
        return {
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
            "PathMappingRulesFile": "/mock/path_mapping.json",
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
            args, kwargs = mock_logging.basicConfig.call_args
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

    @patch("vred_submitter.VRED_RenderScript_DeadlineCloud.logging")
    def test_load_path_mapping_rules(self, mock_logging):
        """Test load_path_mapping_rules method."""
        # Setup
        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger

        mock_params = self.get_mock_params()

        # Mock file open and json load
        mock_json_data = '{"path_mapping_rules": [{"source_path_format": "WINDOWS", "source_path": "C:\\\\source", "destination_path": "/dest"}]}'

        with (
            patch(
                "vred_submitter.VRED_RenderScript_DeadlineCloud.DynamicKeyValueObject",
                return_value=Mock(**mock_params),
            ),
            patch("builtins.open", mock_open(read_data=mock_json_data)),
            patch("vred_submitter.VRED_RenderScript_DeadlineCloud.json.load") as mock_json_load,
        ):

            # Setup mock json load to return proper data
            mock_json_load.return_value = {
                "path_mapping_rules": [
                    {
                        "source_path_format": "WINDOWS",
                        "source_path": "C:\\source",
                        "destination_path": "/dest",
                    }
                ]
            }

            renderer = DeadlineCloudRenderer(mock_params)

            # Mock the return value of load_path_mapping_rules
            with patch.object(renderer, "load_path_mapping_rules", return_value=True):
                # Test
                result = renderer.load_path_mapping_rules()

                # Verify
                assert result is True
