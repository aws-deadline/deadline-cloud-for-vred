# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for data classes used in VRED submitter."""
import pytest

from vred_submitter.data_classes import RenderSubmitterUISettings


class TestRenderSubmitterUISettings:
    """Test RenderSubmitterUISettings data class for render job configuration."""

    @pytest.fixture
    def render_settings(self):
        return RenderSubmitterUISettings()

    def test_default_values(self, render_settings):
        # Test key default values
        assert render_settings.submitter_name == "VRED"
        assert render_settings.AnimationType == "Clip"
        assert render_settings.JobType == "Render"
        assert render_settings.RenderAnimation
        assert render_settings.ImageWidth == 800
        assert render_settings.ImageHeight == 600
        assert render_settings.OutputFormat == "PNG"

    def test_field_assignment(self, render_settings):
        # Test that fields can be assigned new values
        render_settings.name = "Test Job"
        render_settings.ImageWidth = 1920
        render_settings.input_filenames.append("test.vpb")

        assert render_settings.name == "Test Job"
        assert render_settings.ImageWidth == 1920
        assert "test.vpb" in render_settings.input_filenames
