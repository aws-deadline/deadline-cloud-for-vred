# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Hosts the lower-level Deadline Cloud UI. Pipes the relevant render job parameters that the Deadline Cloud UI
requires to populate its UI elements. Processes VRED render job submission requests via Deadline Cloud API.
Generates job bundles for render job submission/export purposes.
"""

import os
from copy import deepcopy
from dataclasses import fields
from pathlib import Path
from shutil import copy
from typing import Any

from PySide6.QtCore import Qt

from deadline.client.api import (
    get_deadline_cloud_library_telemetry_client,
)
from deadline.client.config import get_setting, str2bool
from deadline.client.exceptions import (
    DeadlineOperationCanceled,
    DeadlineOperationError,
    UserInitiatedCancel,
)
from deadline.client.job_bundle._yaml import deadline_yaml_dump
from deadline.client.job_bundle.parameters import JobParameter
from deadline.client.job_bundle.submission import AssetReferences
from deadline.client.ui.dialogs.submit_job_to_deadline_dialog import (
    JobBundlePurpose,
    SubmitJobToDeadlineDialog,
)
from deadline.client.ui.pre_gui_hooks import (
    PreGuiHookContext,
    apply_pre_gui_output,
    qt_hook_confirmation,
    run_pre_gui_hooks,
)

from ._version import version
from .assets import AssetIntrospector
from .constants import Constants
from .data_classes import RenderSubmitterUISettings
from .qt_utils import (
    center_widget,
    get_dpi_scale_factor,
    get_qt_yes_no_dialog_prompt_result,
    show_qt_ok_message_dialog,
)
from .scene import Scene
from .ui.components.constants import Constants as UIConstants
from .ui.components.constants import _global_dpi_scale
from .ui.components.scene_settings_widget import SceneSettingsWidget
from .utils import (
    get_normalized_path,
    get_yaml_contents,
    is_valid_filename,
)
from .vred_logger import get_logger
from .vred_utils import get_major_version, is_scene_file_modified, save_scene_file

# Note: this logger can be repurposed/used later
# Need to initialize to be used inside VRED context
_global_logger = get_logger(__name__)


def _pre_gui_hook_confirm_callback(parent):
    """Choose the confirmation callback for pre-GUI hooks based on the auto_accept setting.

    Returns ``None`` (run hooks without prompting) when ``settings.auto_accept`` is enabled,
    otherwise the standard Qt confirmation dialog from ``qt_hook_confirmation``. Kept as a small
    helper so the auto_accept branch can be unit-tested headlessly.
    """
    if str2bool(get_setting("settings.auto_accept")):
        return None
    return qt_hook_confirmation(parent)


# The deadline-cloud shared job properties the Shared-settings tab recognizes, mapped to the
# matching RenderSubmitterUISettings field, the type each expects, and (where the widget enforces a
# fixed set) the allowed values. Anything else raises inside SharedJobPropertiesWidget's
# set_parameter_value (deadline-cloud); mirrored from that widget. Numeric ranges are intentionally
# left to the spin boxes (which clamp) and the service (which validates at submit) rather than
# duplicating deadline-cloud's bounds here.
_DEADLINE_SHARED_PROPERTIES: dict[str, tuple[str, type, "frozenset[str] | None"]] = {
    "deadline:targetTaskRunStatus": ("initial_status", str, frozenset({"READY", "SUSPENDED"})),
    "deadline:maxFailedTasksCount": ("max_failed_tasks_count", int, None),
    "deadline:maxRetriesPerTask": ("max_retries_per_task", int, None),
    "deadline:priority": ("priority", int, None),
    "deadline:maxWorkerCount": ("max_worker_count", int, None),
}


def _sanitize_hook_deadline_properties(
    shared_parameter_values: dict[str, Any],
    render_settings: RenderSubmitterUISettings,
) -> None:
    """Validate and mirror hook-supplied ``deadline:`` shared job properties.

    ``apply_pre_gui_output`` routes every ``deadline:``-prefixed hook parameter into the shared
    parameter values with no validation. The submitter dialog replays each onto its Shared-settings
    tab during construction (outside the pre-GUI try/except), where an unrecognized key raises
    ``KeyError`` and a wrong-typed value raises ``TypeError`` — so a single mistyped hook key would
    crash the submitter with a raw traceback instead of opening.

    To keep "a faulty hook must not block submission" true end to end, this: (a) drops and logs any
    unrecognized ``deadline:`` key, (b) coerces the int-typed properties, dropping and logging values
    that can't coerce, (c) drops and logs values outside a fixed allowed set (e.g. an initial status
    other than READY/SUSPENDED), and (d) mirrors each accepted value onto the matching
    ``RenderSubmitterUISettings`` field so the settings object (persisted by ``save_sticky_settings``)
    stays consistent with the value the dialog shows. Numeric ranges are left to the spin boxes
    (which clamp) and the service (which validates at submit).
    """
    for key in list(shared_parameter_values):
        if not key.startswith("deadline:"):
            continue
        mapping = _DEADLINE_SHARED_PROPERTIES.get(key)
        if mapping is None:
            _global_logger.warning(
                "Pre-GUI hook set unrecognized shared job property '%s'; ignoring it.", key
            )
            del shared_parameter_values[key]
            continue
        field_name, value_type, allowed_values = mapping
        try:
            coerced = value_type(shared_parameter_values[key])
        except (TypeError, ValueError):
            _global_logger.warning(
                "Pre-GUI hook set '%s' to an invalid value %r; ignoring it.",
                key,
                shared_parameter_values[key],
            )
            del shared_parameter_values[key]
            continue
        if allowed_values is not None and coerced not in allowed_values:
            _global_logger.warning(
                "Pre-GUI hook set '%s' to an unsupported value %r (allowed: %s); ignoring it.",
                key,
                coerced,
                ", ".join(sorted(allowed_values)),
            )
            del shared_parameter_values[key]
            continue
        shared_parameter_values[key] = coerced
        setattr(render_settings, field_name, coerced)


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
        if settings.name:
            job_template[Constants.NAME_FIELD] = settings.name
        if settings.description:
            job_template[Constants.DESCRIPTION_FIELD] = settings.description
        if not settings.RegionRendering:
            # For regular render jobs (not relying on region rendering), exclude tile assembly step from job template
            job_template[Constants.STEPS_FIELD] = [
                step
                for step in job_template[Constants.STEPS_FIELD]
                if step.get(Constants.NAME_FIELD) != Constants.TILE_ASSEMBLY_STEP
            ]
        return job_template

    def _get_parameter_values(
        self,
        settings: RenderSubmitterUISettings,
        queue_parameters: list[JobParameter],
    ) -> list[dict[str, Any]]:
        """
        Produce a list of parameter values for the job template.
        param: settings: render settings for the submitter UI
        param: queue_parameters: parameters from the queue tab of the submitter UI
        return: list of parameter value dictionaries
        """

        # Exclude deadline-cloud shared parameters that are handled at a higher level
        # These should remain sticky for UI persistence but not be included in job bundle parameters
        shared_parameters = {
            "priority",
            "initial_status",
            "max_failed_tasks_count",
            "max_retries_per_task",
            "max_worker_count",
        }

        # Note: represent the bool-typed settings values as string-equivalents of "true" or "false" value for OpenJD
        parameter_values = []
        for field in fields(type(settings)):
            if field.name not in shared_parameters:
                field_value = getattr(settings, field.name)

                # Override NumXTiles and NumYTiles to 1 when region rendering is disabled
                # to prevent creating multiple tasks (rendering the same output image) when tiling is not intended
                if not settings.RegionRendering and field.name in [
                    Constants.NUM_X_TILES_JOB_PARAM,
                    Constants.NUM_Y_TILES_JOB_PARAM,
                ]:
                    field_value = 1

                parameter_values.append(
                    {
                        Constants.NAME_FIELD: field.name,  # type: ignore
                        Constants.VALUE_FIELD: (  # type: ignore
                            str(field_value).lower()
                            if isinstance(field_value, bool)
                            else field_value
                        ),
                    }
                )

        # Check for any overlap between the job parameters we've defined and the queue parameters. This is an error,
        # as we weren't synchronizing the values between the two different tabs where they came from.
        parameter_names = {param[Constants.NAME_FIELD] for param in parameter_values}  # type: ignore
        queue_parameter_names = {param[Constants.NAME_FIELD] for param in queue_parameters}  # type: ignore
        parameter_overlap = parameter_names.intersection(queue_parameter_names)
        if parameter_overlap:
            raise DeadlineOperationError(
                f"{Constants.ERROR_QUEUE_PARAM_CONFLICT}{', '.join(parameter_overlap)}"
            )
        parameter_values.extend(
            {
                Constants.NAME_FIELD: param[Constants.NAME_FIELD],  # type: ignore
                Constants.VALUE_FIELD: param[Constants.VALUE_FIELD],  # type: ignore
            }
            for param in queue_parameters
        )
        return parameter_values

    def show_submitter(self) -> SubmitJobToDeadlineDialog | None:
        """
        Populates the necessary settings for showing the VRED render submitter dialog, then displays it.
        return: SubmitJobToDeadlineDialog instance if successful, None otherwise.
        """
        render_settings = self._initialize_render_settings()
        attachments = self._setup_attachments(render_settings)
        # Initialize the telemetry client, opt-out is respected
        get_deadline_cloud_library_telemetry_client().update_common_details(
            {
                Constants.DEADLINE_CLOUD_FOR_VRED_SUBMITTER_VERSION_KEY: version,
                Constants.VRED_VERSION_KEY: get_major_version(),
            }
        )
        submitter_dialog = self._create_submitter_dialog(render_settings, attachments)
        if submitter_dialog is None:
            # A pre-GUI hook confirmation was declined; abort opening the submitter silently.
            return None
        submitter_dialog.show()
        center_widget(submitter_dialog)
        return submitter_dialog

    def _initialize_render_settings(self) -> RenderSubmitterUISettings:
        """
        Initialize render UI settings using scene defaults.
        return: configured settings
        """
        render_settings = RenderSubmitterUISettings()

        # Load sticky settings first if they exist for this scene
        scene_full_path = Scene.project_full_path()
        if scene_full_path:
            render_settings.load_sticky_settings(scene_full_path)

        # Note: all UI-based render settings populate through the SceneSettingsWidget - update_settings() callback!
        # Note: render_settings.input_directories is kept empty to avoid including more content than intended
        # Note: render_settings.output_directories is kept dynamic/user-defined (via update_settings() callback)
        #
        # Only set default values if they weren't loaded from sticky settings
        if not render_settings.name:
            render_settings.name = Scene.name()
        if not render_settings.input_filenames:
            render_settings.input_filenames = Scene.get_input_filenames()

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
            get_normalized_path(str(path)) for path in introspector.parse_scene_assets()
        }
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
    ) -> SubmitJobToDeadlineDialog | None:
        """
        Configures and creates a job submission dialog for Deadline Cloud.
        Supports overriding conda packages and channels via environment variables (CONDA_CHANNELS, CONDA_PACKAGES)
        param: render_settings: render settings for the submitter UI
        param: attachments auto-detected asset references and user-defined asset references
        return: configured dialog instance, or None if a pre-GUI hook confirmation was declined
        """
        auto_detected_attachments, user_attachments = attachments
        conda_packages = (
            f"{Constants.VRED_CORE_CONDA_PACKAGE_PREFIX.lower()}={get_major_version()}*"
        )
        conda_packages = os.getenv(Constants.CONDA_PACKAGES_OVERRIDE_ENV_VAR) or conda_packages
        conda_channels = os.getenv(Constants.CONDA_CHANNELS_OVERRIDE_ENV_VAR)
        shared_parameter_values = {Constants.CONDA_PACKAGES_JOB_PARAM: conda_packages}
        if conda_channels:
            shared_parameter_values[Constants.CONDA_CHANNELS_JOB_PARAM] = conda_channels

        # Run pre-GUI hooks so studios can pre-populate dialog fields before it opens. VRED has
        # no on-disk job bundle at this point, so hooks are sourced from DEADLINE_HOOKS_DIR only
        # (bundle_dir=None), gated by settings.allow_environment_hooks. The confirmation prompt is
        # skipped when auto_accept is set; otherwise the standard dialog is shown.
        try:
            pre_gui_output = run_pre_gui_hooks(
                PreGuiHookContext(
                    bundle_dir=None,
                    job_name=render_settings.name,
                    # Seed the hook with the priority the dialog will actually show (loaded from
                    # sticky settings), not the PreGuiHookContext default, so a hook that reads
                    # priority sees a value consistent with the upcoming dialog.
                    priority=render_settings.priority,
                    submitter_name="vred",
                    parameters=dict(shared_parameter_values),
                ),
                confirm_callback=_pre_gui_hook_confirm_callback(self.parent_window),
            )
            # Apply the merged output onto COPIES and commit only on success, so a hook that raises
            # partway through apply leaves render_settings / shared_parameter_values pristine. This
            # matters because render_settings is later persisted by save_sticky_settings, so a
            # half-applied value from malformed hook output must not leak to the scene's sticky file.
            # deepcopy (not dataclasses.replace) so the copy's mutable list fields are isolated too.
            # RenderSubmitterUISettings has no .parameters list, so apply_pre_gui_output writes
            # name/description onto the settings and routes every hook parameter into
            # shared_parameter_values (queue parameters, deadline: job properties). VRED's render
            # options are driven by the Job-specific settings tab / scene, not by pre-GUI hooks — see
            # the README. Guard with `or {}`: run_pre_gui_hooks returns {} for the no-hooks case, and
            # this stays safe if a future release returns None instead.
            candidate_settings = deepcopy(render_settings)
            candidate_shared = dict(shared_parameter_values)
            apply_pre_gui_output(pre_gui_output or {}, candidate_settings, candidate_shared)
            # Validate/coerce and mirror the deadline: shared job properties before they reach the
            # dialog constructor (which would otherwise raise on an unrecognized or wrong-typed key).
            _sanitize_hook_deadline_properties(candidate_shared, candidate_settings)
            render_settings = candidate_settings
            shared_parameter_values = candidate_shared
        except DeadlineOperationCanceled:
            # The user declined the hook confirmation prompt. This is a normal cancellation, not a
            # failure, so abort opening the submitter silently by returning None; show_submitter
            # then skips showing the dialog. An uncaught DeadlineOperationCanceled would otherwise
            # propagate into VRED as a raw traceback.
            return None
        except Exception:
            # A pre-GUI hook — or applying its output — failed. Pre-GUI hooks are opt-in and
            # advisory, so a single faulty hook must not block submission: log the failure and open
            # the dialog with the pristine defaults (the failed apply ran only on the discarded
            # copies, so render_settings / shared_parameter_values are unchanged).
            _global_logger.exception(
                "A pre-GUI hook failed; opening the submitter without applying hook output."
            )
            # Only surface a dialog when a hooks directory is configured. Otherwise, on the default
            # no-hooks path (the majority of users, who never set DEADLINE_HOOKS_DIR), an unrelated
            # failure inside the try — e.g. a config read — would pop a confusing "hook failed"
            # dialog every time the submitter opens. A silently dropped studio default is worth a
            # visible warning; a phantom one is not. os.environ.get can't raise, so this check is safe
            # here (gating on the env var alone, without re-reading settings that could themselves
            # raise from within this handler).
            if os.environ.get("DEADLINE_HOOKS_DIR"):
                show_qt_ok_message_dialog(
                    Constants.PRE_GUI_HOOK_FAILED_TITLE, Constants.PRE_GUI_HOOK_FAILED_BODY
                )

        # Need to apply these settings prior in order to ensure that Qt Controls are sized as expected!
        _global_dpi_scale.factor = get_dpi_scale_factor()
        submitter_dialog = SubmitJobToDeadlineDialog(
            job_setup_widget_type=SceneSettingsWidget,
            initial_job_settings=render_settings,
            initial_shared_parameter_values=shared_parameter_values,
            auto_detected_attachments=auto_detected_attachments,
            attachments=user_attachments,
            on_create_job_bundle_callback=self._create_job_bundle_callback,
            parent=self.parent_window,
            f=self.window_flags,
            show_host_requirements_tab=True,
            use_deadline_cloud_v2_channel=True,
        )
        submitter_dialog.setMinimumSize(
            UIConstants.SUBMITTER_DIALOG_WINDOW_DIMENSIONS[0],
            UIConstants.SUBMITTER_DIALOG_WINDOW_DIMENSIONS[1],
        )
        return submitter_dialog

    def _create_job_bundle_callback(
        self,
        widget: SubmitJobToDeadlineDialog,
        job_bundle_dir: str,
        settings: RenderSubmitterUISettings,
        queue_parameters: list[JobParameter],
        asset_references: AssetReferences,
        host_requirements: dict[str, Any] | None = None,
        purpose: JobBundlePurpose = JobBundlePurpose.SUBMISSION,
    ) -> dict[str, Any]:
        """
        Triggered (via on_create_job_bundle_callback) when there is a dialog-based request to create a job bundle
        Note: if the current scene file isn't saved, then a job_bundle won't be created
        param: widget: reference to the widget hosting the dialog, which triggered this callback
        param: job_bundle_dir: directory path where bundle files will be written
        param: settings: render settings for the submitter UI
        param: queue_parameters: parameters from the queue tab of the submitter UI
        param: asset_references: collection of asset paths/references
        param: host_requirements: constraints on host requirements
        param: purpose: catalyst for creating the job bundle
        raises: UserInitiatedCancel: settings validation failure (cancels job/export attempts, displays error message)
        """
        if is_scene_file_modified() and purpose == JobBundlePurpose.SUBMISSION:
            dialog_result = get_qt_yes_no_dialog_prompt_result(
                title=Constants.SCENE_FILE_NOT_SAVED_TITLE,
                message=Constants.SCENE_FILE_NOT_SAVED_BODY,
                default_to_yes=False,
            )
            if dialog_result:
                save_scene_file(Scene.project_full_path())
        scene_full_path = Scene.project_full_path()
        if scene_full_path:
            # Note: file permissions checks further handled by Deadline Cloud API
            #
            if not settings.OutputDir or not os.path.exists(settings.OutputDir):
                raise UserInitiatedCancel(Constants.ERROR_OUTPUT_PATH_INVALID)
            if not is_valid_filename(f"{settings.OutputFileNamePrefix}.{settings.OutputFormat}"):
                raise UserInitiatedCancel(Constants.ERROR_OUTPUT_FILENAME_INVALID)
            if not settings.FrameStep:
                raise UserInitiatedCancel(Constants.ERROR_FRAME_RANGE_FORMAT_INVALID)
            self._create_job_bundle(
                Path(job_bundle_dir),
                settings,
                queue_parameters,
                asset_references,
                host_requirements,
            )
            attachments: AssetReferences = widget.job_attachments.attachments
            settings.input_filenames = sorted(attachments.input_filenames)
            settings.input_directories = sorted(attachments.input_directories)
            # Save sticky settings for this scene
            settings.save_sticky_settings(scene_full_path)
        else:
            # This scene was never saved to a scene file (i.e. none to upload/submit). Bail with a message.
            raise UserInitiatedCancel(Constants.ERROR_SCENE_FILE_UNDEFINED_BODY)

        return {}

    def _create_job_bundle(
        self,
        job_bundle_path: Path,
        settings: RenderSubmitterUISettings,
        queue_parameters: list[JobParameter],
        asset_references: AssetReferences,
        host_requirements: dict[str, Any] | None,
    ) -> None:
        """
        Create job bundle files (template, parameter values, asset references)
        param: job_bundle_path: directory path where bundle files will be written
        param: settings: render settings for the submitter UI
        param: queue_parameters: parameters from the queue tab of the submitter UI
        param: asset_references: collection of asset paths/references
        param: host_requirements: constraints on host requirements
        raise: IOError: If unable to write any of the bundle-related files
        raise: OSError: If the bundle directory is not accessible
        """
        # Keep the job bundle render script contained in its own directory to avoid accumulating recursive references.
        # Ensure no spaces in the job bundle render script path (spaces can interfere with module path searches).
        settings.JobScriptDir = Constants.JOB_BUNDLE_SCRIPTS_FOLDER_PATH
        try:
            if not os.path.exists(settings.JobScriptDir):
                os.mkdir(settings.JobScriptDir)
            copy(
                str(Path(__file__).parent / Constants.VRED_RENDER_SCRIPT_FILENAME),
                settings.JobScriptDir,
            )
        except Exception as exc:
            raise OSError(
                f"{Constants.ERROR_FILE_WRITE_PERMISSION_DENIED}: {settings.JobScriptDir} {exc}"
            ) from exc
        job_template = self._get_job_template(
            default_job_template=self.default_job_template, settings=settings
        )
        if host_requirements:
            for step in job_template[Constants.STEPS_FIELD]:
                step[Constants.HOST_REQUIREMENTS_FIELD] = host_requirements
        parameter_values = self._get_parameter_values(
            settings=settings, queue_parameters=queue_parameters
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
