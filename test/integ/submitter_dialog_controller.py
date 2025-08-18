# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Controller module for interacting with the VRED submitter Qt dialog.
This module provides functionality to access dialog elements, set job-specific settings,
and trigger job bundle export for integration testing.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add the source path to access submitter modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from deadline.client.ui.dialogs.submit_job_to_deadline_dialog import JobBundlePurpose

from deadline.vred_submitter.data_classes import RenderSubmitterUISettings
from deadline.vred_submitter.vred_submitter import VREDSubmitter

from test.integ.constants import Constants

from PySide6.QtWidgets import QWidget
from PySide6.QtTest import QTest

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class SubmitterDialogController:
    """Controller for interacting with the VRED submitter dialog UI."""

    def __init__(self):
        self.dialog = None
        self.scene_settings_widget = None
        self.submitter = None

    def create_submitter_dialog(self) -> bool:
        """
        Create and initialize VRED submitter dialog for testing.
        return: True if dialog created and scene settings widget found; False otherwise
        """
        try:
            # Create submitter instance
            self.submitter = VREDSubmitter(QWidget())

            # Show the submitter dialog
            self.dialog = self.submitter.show_submitter()

            if self.dialog:
                # Wait for dialog to be fully loaded
                QTest.qWait(2000)

                # Find the scene settings widget (Job-specific settings tab)
                for child in self.dialog.findChildren(QWidget):
                    if hasattr(child, "render_output_widget"):
                        logger.info(f"Found scene settings widget: {type(child).__name__}")
                        self.scene_settings_widget = child
                        return self.scene_settings_widget is not None
            return False

        except Exception as e:
            logger.error(f"Error creating submitter dialog: {e}")
            return False

    def set_job_specific_settings(self, settings_list) -> bool:
        """
        Apply job template-specific settings to all relevant submitter dialog widgets.
        param: settings_list: list of dictionaries with 'name' and 'value' keys
        return: True if all settings applied successfully; False otherwise
        """
        if not self.scene_settings_widget:
            logger.error("Scene settings widget not found")
            return False

        settings = {item["name"]: item["value"] for item in settings_list}
        success = True

        try:
            logger.info(f"Setting {len(settings)} job-specific settings")

            if "AnimationClip" in settings:
                self.scene_settings_widget.animation_clip_widget.set_current_entry(
                    settings["AnimationClip"]
                )
            if "AnimationType" in settings:
                self.scene_settings_widget.animation_type_widget.set_current_entry(
                    settings["AnimationType"]
                )
            if "DLSSQuality" in settings:
                self.scene_settings_widget.dlss_quality_widget.set_current_entry(
                    settings["DLSSQuality"]
                )
            if "DPI" in settings:
                self.scene_settings_widget.resolution_widget.clear()
                self.scene_settings_widget.resolution_widget.setText(str(settings["DPI"]))
            if "FramesPerTask" in settings:
                self.scene_settings_widget.frames_per_task_widget.setValue(
                    settings["FramesPerTask"]
                )
            # Note: GPU Ray Tracing will be automatically enabled when Region Rendering is enabled
            # This setting will only take effect if Region Rendering is disabled
            if "GPURaytracing" in settings:
                self.scene_settings_widget.gpu_ray_tracing_widget.setChecked(
                    settings["GPURaytracing"] == "true"
                )
            if "ImageHeight" in settings:
                self.scene_settings_widget.image_size_y_widget.clear()
                self.scene_settings_widget.image_size_y_widget.setText(str(settings["ImageHeight"]))
            if "ImageWidth" in settings:
                self.scene_settings_widget.image_size_x_widget.clear()
                self.scene_settings_widget.image_size_x_widget.setText(str(settings["ImageWidth"]))
            if "JobType" in settings:
                self.scene_settings_widget.render_job_type_widget.set_current_entry(
                    settings["JobType"]
                )
            if "NumXTiles" in settings:
                self.scene_settings_widget.tiles_in_x_widget.setValue(settings["NumXTiles"])
            if "NumYTiles" in settings:
                self.scene_settings_widget.tiles_in_y_widget.setValue(settings["NumYTiles"])
            if (
                "OutputFileNamePrefix" in settings
                and "OutputFormat" in settings
                and "OutputDir" in settings
            ):
                prefix = settings["OutputFileNamePrefix"]
                format_ext = settings["OutputFormat"].lower()
                output_path = f"{settings['OutputDir']}/{prefix}.{format_ext}"
                self.scene_settings_widget.render_output_widget.clear()
                self.scene_settings_widget.render_output_widget.setText(output_path)
            # Note: If Region Rendering is enabled, GPU Ray Tracing is also automatically enabled
            if "RegionRendering" in settings:
                self.scene_settings_widget.enable_region_rendering_widget.setChecked(
                    settings["RegionRendering"] == "true"
                )
            if "RenderAnimation" in settings:
                self.scene_settings_widget.render_animation_widget.setChecked(
                    settings["RenderAnimation"] == "true"
                )
            if "RenderQuality" in settings:
                self.scene_settings_widget.render_quality_widget.set_current_entry(
                    settings["RenderQuality"]
                )
            if "SSQuality" in settings:
                self.scene_settings_widget.ss_quality_widget.set_current_entry(
                    settings["SSQuality"]
                )
            if "SequenceName" in settings:
                self.scene_settings_widget.sequence_name_widget.set_current_entry(
                    settings["SequenceName"]
                )
            if "StartFrame" in settings and "EndFrame" in settings:
                self.scene_settings_widget.frame_range_widget.clear()
                self.scene_settings_widget.frame_range_widget.setText(
                    f"{settings['StartFrame']}-{settings['EndFrame']}"
                )
            if "View" in settings:
                self.scene_settings_widget.render_view_widget.setCurrentText(settings["View"])

            # Trigger UI callbacks to update dependent controls
            self.scene_settings_widget.enable_region_rendering_widget.stateChanged.emit(
                self.scene_settings_widget.enable_region_rendering_widget.checkState()
            )
            self.scene_settings_widget.render_animation_widget.stateChanged.emit(
                self.scene_settings_widget.render_animation_widget.checkState()
            )
            self.scene_settings_widget.animation_type_widget.currentIndexChanged.emit(
                self.scene_settings_widget.animation_type_widget.currentIndex()
            )

            logger.info("Job-specific settings applied successfully")

        except Exception as e:
            logger.error(f"Error while setting job-specific settings: {e}")
            success = False

        return success

    def export_job_bundle(self, bundle_path: str) -> bool:
        """
        Export the job bundle using an internal method (versus clicking Qt export button to export).
        param: bundle_path: path where the job bundle should be exported
        return: True if the job bundle export was successful; False otherwise.
        """
        if not self.dialog:
            logger.error("Dialog not available for export")
            return False

        try:
            # Populate UI-based settings
            settings = RenderSubmitterUISettings()
            if self.scene_settings_widget:
                self.scene_settings_widget.update_settings(settings)

            # Call the submitter's bundle creation method
            if self.submitter:
                self.submitter._create_job_bundle_callback(
                    self.dialog,
                    bundle_path,
                    settings,
                    self.dialog.shared_job_settings.get_parameters(),
                    self.dialog.job_attachments.get_asset_references(),
                    self.dialog.host_requirements.get_requirements(),
                    JobBundlePurpose.EXPORT,
                )
                # Verify that job bundle files were created
                bundle_dir = Path(bundle_path)
                expected_files = [
                    Constants.TEMPLATE_FILENAME,
                    Constants.PARAMETER_VALUES_FILENAME,
                    Constants.ASSET_REFERENCES_FILENAME,
                ]
                if not all((bundle_dir / file_name).exists() for file_name in expected_files):
                    missing_files = [
                        file for file in expected_files if not (bundle_dir / file).exists()
                    ]
                    logger.error(f"Expected bundle file(s) not found: {', '.join(missing_files)}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Error exporting job bundle: {e}")
        return False

    def reopen_submitter_dialog(self):
        """
        Close and reopen the submitter dialog to test settings persistence.
        """
        if self.dialog and self.submitter:
            self.dialog.close()
            self.dialog = self.submitter.show_submitter()
            QTest.qWait(2000)


def run_submitter_integration_test(test_settings: Dict[str, Any], bundle_output_path: str) -> bool:
    """
    Run integration test specifically for the submitter dialog.
    param: test_settings: list of setting dictionaries of settings to apply to the dialog's Qt controls
    bundle_output_path: directory path to where the job bundle should be exported
    return: True if the integration test completed successfully; False otherwise
    """

    controller = SubmitterDialogController()

    try:
        if not test_settings:
            logger.error("Invalid test settings")
            return False

        if not bundle_output_path:
            logger.error("Invalid bundle output path")
            return False

        if not controller.create_submitter_dialog():
            logger.error("Failed to create submitter dialog")
            return False

        logger.info("Submitter dialog created successfully")

        if not controller.set_job_specific_settings(test_settings):
            logger.error(f"Failed to set job-specific settings: {test_settings}")
            return False

        logger.info("Job-specific settings applied successfully")

        # Test settings persistence between dialog close/open in the same session.
        controller.reopen_submitter_dialog()

        if not controller.export_job_bundle(bundle_output_path):
            logger.error(f"Failed to export job bundle to {bundle_output_path}")
            return False

        logger.info(f"Job bundle exported successfully to {bundle_output_path}")
        return True

    except Exception as e:
        logger.error(f"Integration test for Submitter failed: {e}")
        return False
