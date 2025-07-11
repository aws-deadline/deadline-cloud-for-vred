# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for VRED-specific utility functions and API wrappers."""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from vred_submitter.vred_utils import (
    assign_scene_transition_event,
    get_active_camera_name,
    get_animation_clips_list,
    get_dlss_quality,
    get_supersampling_quality,
    get_render_pixel_height,
    get_render_pixel_width,
    get_frame_range_string,
    get_frame_current,
    get_frame_start,
    get_frame_stop,
    get_frame_step,
    get_main_window,
    get_major_version,
    get_populated_animation_clip_ranges,
    get_all_file_references,
    get_all_sequences,
    get_animation_clip,
    get_animation_type,
    get_render_window_size,
    get_scene_full_path,
    get_scene_fps,
    get_render_alpha,
    get_render_animation,
    get_render_pixel_per_inch,
    get_render_view,
    get_render_filename,
    get_premultiply_alpha,
    get_tonemap_hdr,
    get_use_clip_range,
    get_use_gpu_ray_tracing,
    get_use_render_region,
    get_views_list,
    is_scene_file_modified,
    save_scene_file,
    get_frame_range_components,
    ANIMATION_TYPE_DICT,
    DLSS_QUALITY_DICT,
    RENDER_QUALITY_DICT,
    SS_QUALITY_DICT,
)


class TestVredUtils:
    """Test VRED utility functions for scene data access and manipulation."""

    @patch("vred_submitter.vred_utils.vrFileIOService")
    def test_assign_scene_transition_event(self, mock_file_io_service):
        callback = Mock()
        assign_scene_transition_event(callback)

        mock_file_io_service.newScene.connect.assert_called_once_with(callback)
        mock_file_io_service.projectLoad.connect.assert_called_once_with(callback)

    @patch("vred_submitter.vred_utils.vrCameraService")
    def test_get_active_camera_name(self, mock_camera_service):
        mock_camera = Mock()
        mock_camera.getName.return_value = "Camera1"
        mock_camera_service.getActiveCamera.return_value = mock_camera

        result = get_active_camera_name()
        assert result == "Camera1"

    @patch("vred_submitter.vred_utils.getAnimClips")
    def test_get_animation_clips_list(self, mock_get_anim_clips):
        mock_get_anim_clips.return_value = ["clip2", "clip1", "clip3"]

        result = get_animation_clips_list()
        assert result == ["", "clip1", "clip2", "clip3"]

    @patch("vred_submitter.vred_utils.getDLSSQuality")
    def test_get_dlss_quality(self, mock_get_dlss_quality):
        mock_get_dlss_quality.return_value = 1

        result = get_dlss_quality()
        assert result in DLSS_QUALITY_DICT.values()

    @patch("vred_submitter.vred_utils.getSuperSamplingQuality")
    def test_get_supersampling_quality(self, mock_get_ss_quality):
        mock_get_ss_quality.return_value = 2

        result = get_supersampling_quality()
        assert result in SS_QUALITY_DICT.values()

    @patch("vred_submitter.vred_utils.getRenderPixelHeight")
    def test_get_render_pixel_height(self, mock_get_height):
        mock_get_height.return_value = 1080

        result = get_render_pixel_height()
        assert result == 1080

    @patch("vred_submitter.vred_utils.getRenderPixelWidth")
    def test_get_render_pixel_width(self, mock_get_width):
        mock_get_width.return_value = 1920

        result = get_render_pixel_width()
        assert result == 1920

    @patch("vred_submitter.vred_utils.getRenderFrameStep")
    @patch("vred_submitter.vred_utils.getRenderStopFrame")
    @patch("vred_submitter.vred_utils.getRenderStartFrame")
    def test_get_frame_range_string_single_frame(self, mock_start, mock_stop, mock_step):
        mock_start.return_value = 10
        mock_stop.return_value = 10
        mock_step.return_value = 1

        result = get_frame_range_string()
        assert result == "10"

    @patch("vred_submitter.vred_utils.getRenderFrameStep")
    @patch("vred_submitter.vred_utils.getRenderStopFrame")
    @patch("vred_submitter.vred_utils.getRenderStartFrame")
    def test_get_frame_range_string_range(self, mock_start, mock_stop, mock_step):
        mock_start.return_value = 1
        mock_stop.return_value = 100
        mock_step.return_value = 1

        result = get_frame_range_string()
        assert result == "1-100"

    @patch("vred_submitter.vred_utils.getRenderFrameStep")
    @patch("vred_submitter.vred_utils.getRenderStopFrame")
    @patch("vred_submitter.vred_utils.getRenderStartFrame")
    def test_get_frame_range_string_with_step(self, mock_start, mock_stop, mock_step):
        mock_start.return_value = 1
        mock_stop.return_value = 100
        mock_step.return_value = 2

        result = get_frame_range_string()
        assert result == "1-100x2"

    @patch("vred_submitter.vred_utils.getCurrentFrame")
    def test_get_frame_current(self, mock_get_current):
        mock_get_current.return_value = 42

        result = get_frame_current()
        assert result == 42

    @patch("vred_submitter.vred_utils.getRenderStartFrame")
    def test_get_frame_start(self, mock_get_start):
        mock_get_start.return_value = 1

        result = get_frame_start()
        assert result == 1

    @patch("vred_submitter.vred_utils.getRenderStopFrame")
    def test_get_frame_stop(self, mock_get_stop):
        mock_get_stop.return_value = 100

        result = get_frame_stop()
        assert result == 100

    @patch("vred_submitter.vred_utils.getRenderFrameStep")
    def test_get_frame_step(self, mock_get_step):
        mock_get_step.return_value = 2

        result = get_frame_step()
        assert result == 2

    @patch("vred_submitter.vred_utils.vrMainWindow")
    def test_get_main_window(self, mock_main_window):
        result = get_main_window()
        assert result == mock_main_window

    @patch("vred_submitter.vred_utils.getVredVersionYear")
    def test_get_major_version(self, mock_get_version):
        mock_get_version.return_value = 2023

        result = get_major_version()
        assert result == 2023

    @patch("vred_submitter.vred_utils.is_numerically_defined")
    @patch("vred_submitter.vred_utils.get_scene_fps")
    @patch("vred_submitter.vred_utils.getAnimClipNodes")
    def test_get_populated_animation_clip_ranges(
        self, mock_get_nodes, mock_get_fps, mock_is_numeric
    ):
        mock_get_fps.return_value = 24.0
        mock_is_numeric.return_value = True

        mock_clip = Mock()
        mock_clip.getName.return_value = "test_clip"
        mock_clip.getBoundingBox.return_value = [0.0, 0.0, 0.0, 2.0, 0.0, 0.0]
        mock_get_nodes.return_value = [mock_clip]

        result = get_populated_animation_clip_ranges()

        assert "" in result
        assert "test_clip" in result
        assert result[""] == [0.0, 0.0]

    @patch("vred_submitter.vred_utils.get_normalized_path")
    @patch("vred_submitter.vred_utils.vrReferenceService")
    def test_get_all_file_references(self, mock_ref_service, mock_get_normalized):
        mock_node = Mock()
        mock_node.getSourcePath.return_value = "/path/to/source"
        mock_node.getSmartPath.return_value = "/path/to/smart"
        mock_ref_service.getSceneReferences.return_value = [mock_node]
        mock_get_normalized.side_effect = lambda x: x

        result = get_all_file_references()

        assert isinstance(result, set)
        assert Path("/path/to/source") in result
        assert Path("/path/to/smart") in result

    @patch("vred_submitter.vred_utils.getSequenceList")
    def test_get_all_sequences(self, mock_get_sequences):
        mock_get_sequences.return_value = ["seq2", "seq1", "seq3"]

        result = get_all_sequences()
        assert result == ["seq1", "seq2", "seq3"]

    @patch("vred_submitter.vred_utils.getRenderAnimationClip")
    def test_get_animation_clip(self, mock_get_clip):
        mock_get_clip.return_value = "test_clip"

        result = get_animation_clip()
        assert result == "test_clip"

    @patch("vred_submitter.vred_utils.getRenderAnimationType")
    def test_get_animation_type(self, mock_get_type):
        mock_get_type.return_value = 0

        result = get_animation_type()
        assert result == "Clip"

    @patch("vred_submitter.vred_utils.getRenderWindowHeight")
    @patch("vred_submitter.vred_utils.getRenderWindowWidth")
    def test_get_render_window_size(self, mock_get_width, mock_get_height):
        mock_get_width.return_value = 1920
        mock_get_height.return_value = 1080

        result = get_render_window_size()
        assert result == [1920, 1080]

    @patch("vred_submitter.vred_utils.get_normalized_path")
    @patch("vred_submitter.vred_utils.vrFileIOService")
    def test_get_scene_full_path(self, mock_file_io, mock_get_normalized):
        mock_file_io.getFileName.return_value = "/path/to/scene.vpb"
        mock_get_normalized.return_value = "/path/to/scene.vpb"

        result = get_scene_full_path()
        assert result == "/path/to/scene.vpb"

    @patch("vred_submitter.vred_utils.vrMainWindow")
    def test_get_scene_fps_exception_handling(self, mock_main_window):
        mock_main_window.findChildren.return_value = []

        result = get_scene_fps()
        assert result == 24.0  # DEFAULT_SCENE_FILE_FPS_COUNT

    @patch("vred_submitter.vred_utils.getRenderAlpha")
    def test_get_render_alpha(self, mock_get_alpha):
        mock_get_alpha.return_value = True

        result = get_render_alpha()
        assert result

    @patch("vred_submitter.vred_utils.getRenderAnimation")
    def test_get_render_animation(self, mock_get_animation):
        mock_get_animation.return_value = True

        result = get_render_animation()
        assert result

    @patch("vred_submitter.vred_utils.getRenderPixelPerInch")
    def test_get_render_pixel_per_inch(self, mock_get_ppi):
        mock_get_ppi.return_value = 72.5

        result = get_render_pixel_per_inch()
        assert result == 72

    @patch("vred_submitter.vred_utils.getRenderView")
    def test_get_render_view(self, mock_get_view):
        mock_get_view.return_value = "Camera1"

        result = get_render_view()
        assert result == "Camera1"

    @patch("vred_submitter.vred_utils.get_normalized_path")
    @patch("vred_submitter.vred_utils.getRenderFilename")
    def test_get_render_filename(self, mock_get_filename, mock_get_normalized):
        mock_get_filename.return_value = "/path/to/render.png"
        mock_get_normalized.return_value = "/path/to/render.png"

        result = get_render_filename()
        assert result == "/path/to/render.png"

    @patch("vred_submitter.vred_utils.getRenderPremultiply")
    def test_get_premultiply_alpha(self, mock_get_premult):
        mock_get_premult.return_value = False

        result = get_premultiply_alpha()
        assert not result

    @patch("vred_submitter.vred_utils.getRenderTonemapHDR")
    def test_get_tonemap_hdr(self, mock_get_tonemap):
        mock_get_tonemap.return_value = True

        result = get_tonemap_hdr()
        assert result

    @patch("vred_submitter.vred_utils.getRenderUseClipRange")
    def test_get_use_clip_range(self, mock_get_clip_range):
        mock_get_clip_range.return_value = True

        result = get_use_clip_range()
        assert result

    @patch("vred_submitter.vred_utils.getRaytracingMode")
    def test_get_use_gpu_ray_tracing(self, mock_get_raytracing):
        mock_get_raytracing.return_value = True

        result = get_use_gpu_ray_tracing()
        assert result

    @patch("vred_submitter.vred_utils.getUseRenderRegion")
    def test_get_use_render_region(self, mock_get_region):
        mock_get_region.return_value = False

        result = get_use_render_region()
        assert not result

    @patch("vred_submitter.vred_utils.vrCameraService")
    def test_get_views_list(self, mock_camera_service):
        mock_camera1 = Mock()
        mock_camera1.getName.return_value = "Camera1"
        mock_camera2 = Mock()
        mock_camera2.getName.return_value = "Camera2"

        mock_viewpoint1 = Mock()
        mock_viewpoint1.getName.return_value = "Viewpoint1"
        mock_viewpoint2 = Mock()
        mock_viewpoint2.getName.return_value = "Camera1"  # Same name as camera

        mock_camera_service.getCameras.return_value = [mock_camera1, mock_camera2]
        mock_camera_service.getAllViewpoints.return_value = [mock_viewpoint1, mock_viewpoint2]

        result = get_views_list()

        # Should return symmetric difference (items in one set but not both)
        assert "Camera2" in result
        assert "Viewpoint1" in result
        assert "Camera1" not in result  # Exists in both sets

    @patch("vred_submitter.vred_utils.get_main_window")
    def test_is_scene_file_modified_true(self, mock_get_main_window):
        mock_window = Mock()
        mock_window.windowTitle.return_value = "VRED - scene.vpb*"
        mock_get_main_window.return_value = mock_window

        result = is_scene_file_modified()
        assert result

    @patch("vred_submitter.vred_utils.get_main_window")
    def test_is_scene_file_modified_false(self, mock_get_main_window):
        mock_window = Mock()
        mock_window.windowTitle.return_value = "VRED - scene.vpb"
        mock_get_main_window.return_value = mock_window

        result = is_scene_file_modified()
        assert not result

    @patch("vred_submitter.vred_utils.get_normalized_path")
    @patch("vred_submitter.vred_utils.vrFileIOService")
    def test_save_scene_file(self, mock_file_io, mock_get_normalized):
        mock_get_normalized.return_value = "/path/to/scene.vpb"

        save_scene_file("/path/to/scene.vpb")

        mock_file_io.saveFile.assert_called_once_with("/path/to/scene.vpb")

    @patch("vred_submitter.vred_utils.get_normalized_path")
    @patch("vred_submitter.vred_utils.vrFileIOService")
    def test_save_scene_file_empty_filename(self, mock_file_io, mock_get_normalized):
        save_scene_file("")

        mock_file_io.saveFile.assert_not_called()

    def test_get_frame_range_components_single_frame(self):
        result = get_frame_range_components("42")
        assert result == (42, 42, 1)

    def test_get_frame_range_components_range(self):
        result = get_frame_range_components("1-100")
        assert result == (1, 100, 1)

    def test_get_frame_range_components_range_with_step(self):
        result = get_frame_range_components("1-100x2")
        assert result == (1, 100, 2)

    def test_get_frame_range_components_negative_frames(self):
        result = get_frame_range_components("-10-10x3")
        assert result == (-10, 10, 3)

    def test_get_frame_range_components_invalid_format(self):
        with pytest.raises(ValueError):
            get_frame_range_components("invalid")

    def test_get_frame_range_components_invalid_single_frame(self):
        with pytest.raises(ValueError):
            get_frame_range_components("abc")

    def test_animation_type_dict(self):
        assert ANIMATION_TYPE_DICT[0] == "Clip"
        assert ANIMATION_TYPE_DICT[1] == "Timeline"

    def test_quality_dicts(self):
        # Test that quality dictionaries contain expected values
        assert "Off" in DLSS_QUALITY_DICT.values()
        assert "Quality" in DLSS_QUALITY_DICT.values()
        assert "Realistic High" in RENDER_QUALITY_DICT.values()
        assert "Raytracing" in RENDER_QUALITY_DICT.values()
        assert "Off" in SS_QUALITY_DICT.values()
        assert "Ultra High" in SS_QUALITY_DICT.values()
