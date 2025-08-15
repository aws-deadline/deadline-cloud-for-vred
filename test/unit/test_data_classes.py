# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for data classes used in VRED submitter."""
import json
import os
import tempfile
from pathlib import Path
import pytest

from vred_submitter.data_classes import RenderSubmitterUISettings


class TestRenderSubmitterUISettingsStickySettings:
    """Test sticky settings functionality in RenderSubmitterUISettings."""

    @pytest.fixture
    def render_settings(self):
        return RenderSubmitterUISettings()

    @pytest.fixture
    def sticky_settings_data(self):
        """Comprehensive test data for ALL sticky setting fields."""
        return {
            # String fields
            "description": "Test job description",
            "name": "Test Job Name",
            "AnimationClip": "TestClip",
            "AnimationType": "Timeline",
            "DLSSQuality": "Quality",
            "JobType": "Animation",
            "OutputDir": "/test/output/dir",
            "OutputFileNamePrefix": "test_render",
            "OutputFormat": "EXR",
            "RenderQuality": "Realistic Ultra",
            "SSQuality": "High",
            "SequenceName": "TestSequence",
            "View": "Camera01",
            # Integer fields
            "DPI": 150,
            "EndFrame": 100,
            "FrameStep": 2,
            "FramesPerTask": 5,
            "ImageHeight": 1080,
            "ImageWidth": 1920,
            "NumXTiles": 3,
            "NumYTiles": 2,
            "StartFrame": 10,
            # Boolean fields
            "GPURaytracing": True,
            "IncludeAlphaChannel": True,
            "OverrideRenderPass": True,
            "PremultiplyAlpha": True,
            "RegionRendering": True,
            "RenderAnimation": False,
            "TonemapHDR": True,
            # List fields
            "input_filenames": ["test1.vpb", "test2.vpb"],
            "input_directories": ["/test/input1", "/test/input2"],
            "output_directories": ["/test/output1", "/test/output2"],
        }

    def test_save_sticky_settings_handles_write_errors(self, render_settings):
        """Test saving sticky settings handles file write errors gracefully."""
        # Try to save to a directory that doesn't exist or is read-only
        invalid_path = "/invalid/path/that/does/not/exist/scene.vpb"

        # Should not crash, but may log a warning
        render_settings.save_sticky_settings(invalid_path)

    def test_save_all_sticky_settings_fields(self, render_settings, sticky_settings_data):
        """Test that ALL sticky settings fields are properly saved to JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vpb", delete=False) as scene_file:
            scene_filename = scene_file.name

        try:
            # Set ALL sticky field values from test data
            for field_name, value in sticky_settings_data.items():
                setattr(render_settings, field_name, value)

            # Save sticky settings
            render_settings.save_sticky_settings(scene_filename)

            # Verify file was created
            sticky_filename = Path(scene_filename).with_suffix(".deadline_render_settings.json")
            assert sticky_filename.exists()

            # Load and verify file contents
            with open(sticky_filename, "r") as f:
                saved_data = json.load(f)

            # Verify ALL string fields are saved
            assert saved_data["description"] == "Test job description"
            assert saved_data["name"] == "Test Job Name"
            assert saved_data["AnimationClip"] == "TestClip"
            assert saved_data["AnimationType"] == "Timeline"
            assert saved_data["DLSSQuality"] == "Quality"
            assert saved_data["JobType"] == "Animation"
            assert saved_data["OutputDir"] == "/test/output/dir"
            assert saved_data["OutputFileNamePrefix"] == "test_render"
            assert saved_data["OutputFormat"] == "EXR"
            assert saved_data["RenderQuality"] == "Realistic Ultra"
            assert saved_data["SSQuality"] == "High"
            assert saved_data["SequenceName"] == "TestSequence"
            assert saved_data["View"] == "Camera01"

            # Verify ALL integer fields are saved
            assert saved_data["DPI"] == 150
            assert saved_data["EndFrame"] == 100
            assert saved_data["FrameStep"] == 2
            assert saved_data["FramesPerTask"] == 5
            assert saved_data["ImageHeight"] == 1080
            assert saved_data["ImageWidth"] == 1920
            assert saved_data["NumXTiles"] == 3
            assert saved_data["NumYTiles"] == 2
            assert saved_data["StartFrame"] == 10

            # Verify ALL boolean fields are saved
            assert saved_data["GPURaytracing"] is True
            assert saved_data["IncludeAlphaChannel"] is True
            assert saved_data["OverrideRenderPass"] is True
            assert saved_data["PremultiplyAlpha"] is True
            assert saved_data["RegionRendering"] is True
            assert saved_data["RenderAnimation"] is False
            assert saved_data["TonemapHDR"] is True

            # Verify ALL list fields are saved
            assert saved_data["input_filenames"] == ["test1.vpb", "test2.vpb"]
            assert saved_data["input_directories"] == ["/test/input1", "/test/input2"]
            assert saved_data["output_directories"] == ["/test/output1", "/test/output2"]

            # Verify the correct number of fields are saved (should be exactly the sticky fields)
            import dataclasses

            sticky_field_count = len(
                [
                    field.name
                    for field in dataclasses.fields(render_settings)
                    if field.metadata.get("sticky")
                ]
            )
            assert len(saved_data) == sticky_field_count

        finally:
            sticky_filename = Path(scene_filename).with_suffix(".deadline_render_settings.json")
            if sticky_filename.exists():
                os.remove(sticky_filename)

    def test_sticky_settings_roundtrip(self, render_settings, sticky_settings_data):
        """Test that ALL settings can be saved and loaded correctly (complete roundtrip test)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vpb", delete=False) as scene_file:
            scene_filename = scene_file.name

        try:
            # Set ALL values from test data
            for field_name, value in sticky_settings_data.items():
                setattr(render_settings, field_name, value)

            # Save sticky settings
            render_settings.save_sticky_settings(scene_filename)

            # Create new instance and load
            new_settings = RenderSubmitterUISettings()
            new_settings.load_sticky_settings(scene_filename)

            # Verify ALL values match exactly
            for field_name, expected_value in sticky_settings_data.items():
                actual_value = getattr(new_settings, field_name)
                assert (
                    actual_value == expected_value
                ), f"Field {field_name}: expected {expected_value}, got {actual_value}"

        finally:
            sticky_filename = Path(scene_filename).with_suffix(".deadline_render_settings.json")
            if sticky_filename.exists():
                os.remove(sticky_filename)

    def test_load_sticky_settings_invalid_data_type(self, render_settings):
        """Test loading sticky settings when file contains non-dict data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vpb", delete=False) as scene_file:
            scene_filename = scene_file.name

        sticky_filename = None
        try:
            # Create file with array instead of object
            sticky_filename = Path(scene_filename).with_suffix(".deadline_render_settings.json")
            with open(sticky_filename, "w") as f:
                json.dump(["not", "a", "dictionary"], f)

            original_width = render_settings.ImageWidth

            # Should not crash and should log warning
            render_settings.load_sticky_settings(scene_filename)

            # Values should remain unchanged
            assert render_settings.ImageWidth == original_width

        finally:
            if sticky_filename and sticky_filename.exists():
                os.remove(sticky_filename)
