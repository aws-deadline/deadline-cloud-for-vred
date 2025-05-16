# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Hosts the lower-level Deadline Cloud UI. Pipes the relevant render job parameters that the Deadline Cloud UI
requires to populate its UI elements. Processes VRED render job submission requests via Deadline Cloud API.
Generates job bundles for render job submission/export purposes.
"""

import os

from copy import deepcopy
from dataclasses import fields
from pathlib import Path
from typing import Any, Optional

from .assets import AssetIntrospector
from .constants import Constants
from .data_classes import RenderSubmitterUISettings
from .qt_utils import get_qt_yes_no_dialog_prompt_result
from .scene import Animation, Scene
from .ui.components.scene_settings_widget import SceneSettingsWidget
from .utils import get_yaml_contents
from .vred_logger import get_logger
from .vred_utils import is_scene_file_modified, get_major_version, save_scene_file
from ._version import version

from deadline.client.api import (
    get_deadline_cloud_library_telemetry_client,
)
from deadline.client.exceptions import DeadlineOperationError
from deadline.client.job_bundle._yaml import deadline_yaml_dump
from deadline.client.job_bundle.submission import AssetReferences
from deadline.client.ui.dialogs.submit_job_to_deadline_dialog import (
    SubmitJobToDeadlineDialog,
    JobBundlePurpose,
)

from PySide6.QtCore import Qt

# Note: this logger can be repurposed/used later
#
_global_logger = get_logger(__name__)


class VREDSubmitter:

    def __init__(self, parent_window: Any, window_flags: Qt.WindowFlags = Qt.WindowFlags()):
        """
        Track parent window, flags, and default job template contents.
        param: parent_window: the parent Qt window instance that will contain the submitter.
        param: window_flags: Qt window flags to control window behavior and appearance.
        """
        self.parent_window = parent_window
        self.window_flags = window_flags
        self.default_job_template = get_yaml_contents(
            str(Path(__file__).parent / Constants.DEFAULT_JOB_TEMPLATE_FILENAME)
        )

    def _get_job_template(
        self,
        default_job_template: dict[str, Any],
        settings: RenderSubmitterUISettings,
    ) -> dict[str, Any]:
        """
        Generate a job template based on default template and current settings.
        param: default_job_template: base template dictionary containing default render job configuration.
        param settings: Current render submitter UI settings to incorporate into template.
        raise: KeyError: if required template keys are missing.
        raise: ValueError: if template values are invalid.
        return: modified job template with current settings applied.
        """
        job_template = deepcopy(default_job_template)
        job_template[Constants.NAME_FIELD] = settings.name
        if settings.description:
            job_template[Constants.DESCRIPTION_FIELD] = settings.description
        return job_template

    def _get_parameter_values(
        self,
        settings: RenderSubmitterUISettings,
        queue_parameters: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Produce a list of parameter values for the job template.
        param: settings: render settings for the submitter UI
        param: queue_parameters: parameters from the queue tab of the submitter UI
        return: list of parameter value dictionaries
        """
        parameter_values = [
            {Constants.NAME_FIELD: field.name, Constants.VALUE_FIELD: getattr(settings, field.name)}
            for field in fields(type(settings))
        ]
        # Check for any overlap between the job parameters we've defined and the queue parameters. This is an error,
        # as we weren't synchronizing the values between the two different tabs where they came from.
        #
        parameter_names = {param[Constants.NAME_FIELD] for param in parameter_values}
        queue_parameter_names = {param[Constants.NAME_FIELD] for param in queue_parameters}
        parameter_overlap = parameter_names.intersection(queue_parameter_names)
        if parameter_overlap:
            raise DeadlineOperationError(
                f"{Constants.ERROR_QUEUE_PARAM_CONFLICT}{', '.join(parameter_overlap)}"
            )
        parameter_values.extend(
            {
                Constants.NAME_FIELD: param[Constants.NAME_FIELD],
                Constants.VALUE_FIELD: param[Constants.VALUE_FIELD],
            }
            for param in queue_parameters
        )
        return parameter_values

    def show_submitter(self) -> Optional[SubmitJobToDeadlineDialog]:
        """
        Populates the necessary settings for showing the VRED render submitter dialog, then displays it.
        return: SubmitJobToDeadlineDialog instance if successful, None otherwise.
        """
        render_settings = self._initialize_render_settings()
        attachments = self._setup_attachments(render_settings)
        # Initialize the telemetry client, opt-out is respected
        get_deadline_cloud_library_telemetry_client().update_common_details(
            {
                Constants.DEADLINE_CLOUD_FOR_VRED_SUBMITTER_VERSION_FIELD: version,
                Constants.VRED_VERSION_FIELD: get_major_version(),
            }
        )
        submitter_dialog = self._create_submitter_dialog(render_settings, attachments)
        submitter_dialog.setMinimumSize(
            Constants.MINIMUM_WINDOW_SIZE[0], Constants.MINIMUM_WINDOW_SIZE[1]
        )
        submitter_dialog.show()
        return submitter_dialog

    def _initialize_render_settings(self) -> RenderSubmitterUISettings:
        """
        Initialize render UI settings using scene defaults.
        return: configured settings
        """
        render_settings = RenderSubmitterUISettings()
        # Note: further render settings will be populated through the SceneSettingsWidget's
        # update_settings()/update_settings_callback() mechanism.
        render_settings.name = Path(Scene.name()).name
        render_settings.frame_list = str(Animation.frame_list())
        render_settings.project_path = Scene.project_path()
        render_settings.output_path = Scene.output_path()
        return render_settings

    def _setup_attachments(
        self, render_settings: RenderSubmitterUISettings
    ) -> tuple[AssetReferences, AssetReferences]:
        """
        Set up auto-detected and user-defined attachments for the render job.
        param: render_settings: render settings for the submitter UI
        return: auto-detected and user-defined attachments
        """
        auto_detected_attachments = AssetReferences()
        introspector = AssetIntrospector()
        auto_detected_attachments.input_filenames = {
            os.path.normpath(path) for path in introspector.parse_scene_assets()
        }
        # Note: additional logic can be added here for auto_detected_attachments.output_directories
        user_defined_attachments = AssetReferences(
            input_filenames=set(render_settings.input_filenames),
            input_directories=set(render_settings.input_directories),
            output_directories=set(render_settings.output_directories),
        )
        return auto_detected_attachments, user_defined_attachments

    def _create_submitter_dialog(
        self,
        render_settings: RenderSubmitterUISettings,
        attachments: tuple[AssetReferences, AssetReferences],
    ) -> SubmitJobToDeadlineDialog:
        """
        Configures and creates a job submission dialog for Deadline Cloud.
        param: render_settings: render settings for the submitter UI
        param: attachments auto-detected asset references and user-defined asset references
        return: configured dialog instance
        """
        auto_detected_attachments, user_attachments = attachments
        conda_packages = f"{Constants.VRED_PRODUCT_NAME.lower()}={get_major_version()}*"
        return SubmitJobToDeadlineDialog(
            job_setup_widget_type=SceneSettingsWidget,
            initial_job_settings=render_settings,
            initial_shared_parameter_values={
                Constants.CONDA_PACKAGES_FIELD: conda_packages,
            },
            auto_detected_attachments=auto_detected_attachments,
            attachments=user_attachments,
            on_create_job_bundle_callback=self._create_job_bundle_callback,
            parent=self.parent_window,
            f=self.window_flags,
            show_host_requirements_tab=True,
        )

    def _create_job_bundle_callback(
        self,
        widget: SubmitJobToDeadlineDialog,
        job_bundle_dir: str,
        settings: RenderSubmitterUISettings,
        queue_parameters: list[dict[str, Any]],
        asset_references: AssetReferences,
        host_requirements: Optional[dict[str, Any]] = None,
        purpose: JobBundlePurpose = JobBundlePurpose.SUBMISSION,
    ) -> None:
        """
        Triggered (via on_create_job_bundle_callback) when there is a dialog-based request to create a job bundle
        param: widget: reference to the widget hosting the dialog, which triggered this callback
        param: job_bundle_dir: directory path where bundle files will be written
        param: settings: render settings for the submitter UI
        param: queue_parameters: parameters from the queue tab of the submitter UI
        param: asset_references: collection of asset paths/references
        param: host_requirements: constraints on host requirements
        param: purpose: catalyst for creating the job bundle
        """
        if is_scene_file_modified() and purpose == JobBundlePurpose.SUBMISSION:
            dialog_result = get_qt_yes_no_dialog_prompt_result(
                title=Constants.SCENE_FILE_NOT_SAVED_TITLE,
                message=Constants.SCENE_FILE_NOT_SAVED_BODY,
                default_to_yes=False,
            )
            if dialog_result:
                save_scene_file(Scene.name)
        self._create_job_bundle(
            job_bundle_dir, settings, queue_parameters, asset_references, host_requirements
        )
        attachments: AssetReferences = widget.job_attachments.attachments
        settings.input_filenames = sorted(attachments.input_filenames)
        settings.input_directories = sorted(attachments.input_directories)

    def _create_job_bundle(
        self,
        job_bundle_dir: str,
        settings: RenderSubmitterUISettings,
        queue_parameters: list[dict[str, Any]],
        asset_references: AssetReferences,
        host_requirements: Optional[dict[str, Any]],
    ) -> None:
        """
        Create job bundle files (template, parameter values, asset references)
        param: job_bundle_dir: directory path where bundle files will be written
        param: settings: render settings for the submitter UI
        param: queue_parameters: parameters from the queue tab of the submitter UI
        param: asset_references: collection of asset paths/references
        param: host_requirements: constraints on host requirements
        raise: IOError: If unable to write any of the bundle files
        raise: OSError: If the bundle directory is not accessible
        """
        job_bundle_path = Path(job_bundle_dir)
        job_template = self._get_job_template(
            default_job_template=self.default_job_template, settings=settings
        )
        if host_requirements:
            for step in job_template[Constants.STEPS_FIELD]:
                step[Constants.HOST_REQUIREMENTS_FIELD] = host_requirements
        parameter_values = self._get_parameter_values(
            queue_parameters=queue_parameters, settings=settings
        )
        with open(
            job_bundle_path / Constants.TEMPLATE_FILENAME,
            Constants.WRITE_FLAG,
            encoding=Constants.UTF8_FLAG,
        ) as file_handle:
            deadline_yaml_dump(job_template, file_handle, indent=1)
        with open(
            job_bundle_path / Constants.PARAMETER_VALUES_FILENAME,
            Constants.WRITE_FLAG,
            encoding=Constants.UTF8_FLAG,
        ) as file_handle:
            deadline_yaml_dump(
                {Constants.PARAMETER_VALUES_FIELD: parameter_values}, file_handle, indent=1
            )
        with open(
            job_bundle_path / Constants.ASSET_REFERENCES_FILENAME,
            Constants.WRITE_FLAG,
            encoding=Constants.UTF8_FLAG,
        ) as file_handle:
            deadline_yaml_dump(asset_references.to_dict(), file_handle, indent=1)
