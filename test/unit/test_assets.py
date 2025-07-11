# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for asset introspection and file reference parsing."""
import pytest
from unittest.mock import patch
from pathlib import Path

from vred_submitter.assets import AssetIntrospector


class TestAssetIntrospector:
    """Test AssetIntrospector for parsing scene assets and file references."""

    @pytest.fixture
    def asset_introspector(self):
        return AssetIntrospector()

    @patch("vred_submitter.assets.get_all_file_references")
    @patch("vred_submitter.assets.Scene.project_full_path")
    def test_parse_scene_assets(
        self, mock_project_full_path, mock_get_all_file_references, asset_introspector
    ):
        mock_project_full_path.return_value = "/path/to/scene.vpb"
        mock_get_all_file_references.return_value = {
            Path("/path/to/texture1.jpg"),
            Path("/path/to/texture2.png"),
        }

        result = asset_introspector.parse_scene_assets()

        expected = {
            Path("/path/to/scene.vpb"),
            Path("/path/to/texture1.jpg"),
            Path("/path/to/texture2.png"),
        }
        assert result == expected
        mock_project_full_path.assert_called_once()
        mock_get_all_file_references.assert_called_once()

    @patch("vred_submitter.assets.get_all_file_references")
    @patch("vred_submitter.assets.Scene.project_full_path")
    def test_parse_scene_assets_empty_references(
        self, mock_project_full_path, mock_get_all_file_references, asset_introspector
    ):
        mock_project_full_path.return_value = "/path/to/scene.vpb"
        mock_get_all_file_references.return_value = set()

        result = asset_introspector.parse_scene_assets()

        expected = {Path("/path/to/scene.vpb")}
        assert result == expected
