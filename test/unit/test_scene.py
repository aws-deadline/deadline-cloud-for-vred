# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for VRED scene management and frame range functionality."""
from unittest.mock import patch

from vred_submitter.scene import FrameRange, Animation, Scene


class TestFrameRange:
    """Test FrameRange class for animation frame sequences."""

    def test_init_single_frame(self):
        # Test single frame initialization
        frame_range = FrameRange(10)
        assert frame_range.start == 10
        assert frame_range.stop is None
        assert frame_range.step is None

    def test_init_with_stop(self):
        # Test frame range with start and stop
        frame_range = FrameRange(1, 10)
        assert frame_range.start == 1
        assert frame_range.stop == 10
        assert frame_range.step is None

    def test_init_with_step(self):
        # Test frame range with custom step
        frame_range = FrameRange(1, 10, 2)
        assert frame_range.start == 1
        assert frame_range.stop == 10
        assert frame_range.step == 2

    def test_repr_single_frame(self):
        frame_range = FrameRange(10)
        assert repr(frame_range) == "10"

    def test_repr_same_start_stop(self):
        frame_range = FrameRange(10, 10)
        assert repr(frame_range) == "10"

    def test_repr_range_no_step(self):
        frame_range = FrameRange(1, 10)
        assert repr(frame_range) == "1-10"

    def test_repr_range_step_one(self):
        frame_range = FrameRange(1, 10, 1)
        assert repr(frame_range) == "1-10"

    def test_repr_range_with_step(self):
        frame_range = FrameRange(1, 10, 2)
        assert repr(frame_range) == "1-10:2"

    def test_iter_single_frame(self):
        frame_range = FrameRange(5)
        frames = list(frame_range)
        assert frames == [5]

    def test_iter_range(self):
        frame_range = FrameRange(1, 5)
        frames = list(frame_range)
        assert frames == [1, 2, 3, 4, 5]

    def test_iter_range_with_step(self):
        frame_range = FrameRange(1, 10, 2)
        frames = list(frame_range)
        assert frames == [1, 3, 5, 7, 9]


class TestAnimation:
    """Test Animation class for VRED animation frame management."""

    @patch("vred_submitter.scene.get_frame_current")
    def test_current_frame(self, mock_get_frame_current):
        # Test current frame retrieval (float to int conversion)
        mock_get_frame_current.return_value = 42.5
        result = Animation.current_frame()
        assert result == 42
        mock_get_frame_current.assert_called_once()

    @patch("vred_submitter.scene.get_frame_start")
    def test_start_frame(self, mock_get_frame_start):
        mock_get_frame_start.return_value = 1.0
        result = Animation.start_frame()
        assert result == 1
        mock_get_frame_start.assert_called_once()

    @patch("vred_submitter.scene.get_frame_stop")
    def test_end_frame(self, mock_get_frame_stop):
        mock_get_frame_stop.return_value = 100.0
        result = Animation.end_frame()
        assert result == 100
        mock_get_frame_stop.assert_called_once()

    @patch("vred_submitter.scene.get_frame_step")
    def test_frame_step(self, mock_get_frame_step):
        mock_get_frame_step.return_value = 2.0
        result = Animation.frame_step()
        assert result == 2
        mock_get_frame_step.assert_called_once()

    @patch("vred_submitter.scene.get_frame_step")
    @patch("vred_submitter.scene.get_frame_stop")
    @patch("vred_submitter.scene.get_frame_start")
    def test_frame_list(self, mock_get_frame_start, mock_get_frame_stop, mock_get_frame_step):
        mock_get_frame_start.return_value = 1
        mock_get_frame_stop.return_value = 10
        mock_get_frame_step.return_value = 2

        result = Animation.frame_list()

        assert isinstance(result, FrameRange)
        assert result.start == 1
        assert result.stop == 10
        assert result.step == 2


class TestScene:
    """Test Scene class for VRED scene file management."""

    @patch("vred_submitter.scene.get_scene_full_path")
    def test_name_with_extension(self, mock_get_scene_full_path):
        # Test scene name extraction from file path
        mock_get_scene_full_path.return_value = "/path/to/scene.vpb"
        result = Scene.name()
        assert result == "scene"

    @patch("vred_submitter.scene.get_scene_full_path")
    def test_name_without_extension(self, mock_get_scene_full_path):
        mock_get_scene_full_path.return_value = "/path/to/scene"
        result = Scene.name()
        assert result == "scene"

    @patch("vred_submitter.scene.get_scene_full_path")
    def test_name_dot_file(self, mock_get_scene_full_path):
        mock_get_scene_full_path.return_value = "/path/to/."
        result = Scene.name()
        assert result == ""

    @patch("vred_submitter.scene.Scene.project_path")
    def test_get_input_directories(self, mock_project_path):
        mock_project_path.return_value = "/path/to/project"
        result = Scene.get_input_directories()
        assert result == ["/path/to/project"]

    @patch("vred_submitter.scene.Scene.project_full_path")
    def test_get_input_filenames(self, mock_project_full_path):
        mock_project_full_path.return_value = "/path/to/scene.vpb"
        result = Scene.get_input_filenames()
        assert result == ["/path/to/scene.vpb"]

    @patch("vred_submitter.scene.Scene.output_path")
    def test_get_output_directories(self, mock_output_path):
        mock_output_path.return_value = "/path/to/output"
        result = Scene.get_output_directories()
        assert result == ["/path/to/output"]

    @patch("vred_submitter.scene.get_scene_full_path")
    def test_project_path(self, mock_get_scene_full_path):
        mock_get_scene_full_path.return_value = "/path/to/project/scene.vpb"
        result = Scene.project_path()
        assert result == "/path/to/project"

    @patch("vred_submitter.scene.get_scene_full_path")
    def test_project_full_path(self, mock_get_scene_full_path):
        mock_get_scene_full_path.return_value = "/path/to/project/scene.vpb"
        result = Scene.project_full_path()
        assert result == "/path/to/project/scene.vpb"

    @patch("vred_submitter.scene.get_render_filename")
    def test_output_path(self, mock_get_render_filename):
        mock_get_render_filename.return_value = "/path/to/output/render.png"
        result = Scene.output_path()
        assert result == "/path/to/output"
