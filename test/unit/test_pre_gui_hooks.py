# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Unit tests for the VRED submitter's pre-GUI hook integration.

``VREDSubmitter._create_submitter_dialog`` calls deadline-cloud's ``run_pre_gui_hooks``
(env-only, since VRED has no on-disk bundle) and then maps the merged output onto its own
``RenderSubmitterUISettings`` + the dialog's shared parameter values via deadline-cloud's
generic ``apply_pre_gui_output``.

The full submitter needs a running VRED and Qt, so it is exercised in the integration suite.
This module covers the DCC-owned pieces at unit level:

* ``TestApplyPreGuiOutputForVred`` pins the contract that matters for VRED: its
  ``RenderSubmitterUISettings`` has assignable ``name`` / ``description`` and **no**
  ``.parameters`` list, so ``apply_pre_gui_output`` must write name/description onto the settings
  and route every hook parameter into the shared values dict. It drives the real core function
  against the real settings dataclass rather than re-testing core internals.
* ``TestPreGuiHookConfirmCallback`` covers ``_pre_gui_hook_confirm_callback`` — the
  ``settings.auto_accept`` branch — including that the returned callback actually fires the Qt
  confirmation dialog (via the real ``qt_hook_confirmation``) when auto_accept is disabled.
* ``TestCreateSubmitterDialogPreGuiWiring`` covers the wiring added to
  ``_create_submitter_dialog`` — the ``PreGuiHookContext`` construction and that
  ``apply_pre_gui_output`` is applied onto ``render_settings`` / the shared values before the
  dialog is built — plus its error handling: a declined confirmation
  (``DeadlineOperationCanceled``) aborts the open by returning ``None``, and a faulty studio hook
  (any other exception) is logged and swallowed so the dialog still opens with its pristine
  defaults. deadline-cloud is mocked.

``apply_pre_gui_output`` first ships in deadline-cloud 0.60.1 (the floor this change sets); it is
absent from 0.60.0.
"""

from unittest.mock import Mock, patch

from vred_submitter.data_classes import RenderSubmitterUISettings
from vred_submitter.vred_submitter import (
    VREDSubmitter,
    _pre_gui_hook_confirm_callback,
    _sanitize_hook_deadline_properties,
)

from deadline.client.exceptions import DeadlineOperationCanceled
from deadline.client.ui.pre_gui_hooks import apply_pre_gui_output


def _settings() -> RenderSubmitterUISettings:
    s = RenderSubmitterUISettings()
    s.name = "Original"
    s.description = ""
    return s


class TestApplyPreGuiOutputForVred:
    """The generic core ``apply_pre_gui_output`` driven against VRED's real settings dataclass."""

    def test_settings_dataclass_has_no_parameters_list(self):
        """The premise for VRED's mapping: RenderSubmitterUISettings has no .parameters list, so
        apply_pre_gui_output treats every hook parameter as a shared value."""
        assert not hasattr(RenderSubmitterUISettings(), "parameters")

    def test_name_and_description_applied_to_settings(self):
        """A hook's name/description overwrite the settings fields (VRED has no .parameters list,
        so these land directly on the dataclass)."""
        settings = _settings()
        shared = {"CondaPackages": "vredcore=2024*"}

        apply_pre_gui_output(
            {"name": "PREGUI RAN", "description": "from pipeline"}, settings, shared
        )

        assert settings.name == "PREGUI RAN"
        assert settings.description == "from pipeline"

    def test_hook_parameters_merged_into_shared_values(self):
        """With no template-parameter list, all hook parameters (queue params, deadline:
        properties) flow into the shared values the dialog is seeded with, overriding defaults on
        key collision."""
        settings = _settings()
        shared = {"CondaPackages": "vredcore=2024*", "CondaChannels": "deadline-cloud"}

        apply_pre_gui_output(
            {
                "parameters": {
                    "deadline:priority": 88,
                    "CondaPackages": "vredcore=2025* custom_pkg",  # overrides the default
                }
            },
            settings,
            shared,
        )

        assert shared["deadline:priority"] == 88
        assert shared["CondaPackages"] == "vredcore=2025* custom_pkg"
        assert shared["CondaChannels"] == "deadline-cloud"  # untouched keys preserved

    def test_empty_output_is_a_noop(self):
        """No pre-GUI hook output leaves the settings and shared values unchanged."""
        settings = _settings()
        shared = {"CondaPackages": "pkg"}

        apply_pre_gui_output({}, settings, shared)

        assert settings.name == "Original"
        assert settings.description == ""
        assert shared == {"CondaPackages": "pkg"}

    def test_partial_output_only_touches_present_keys(self):
        """Only the keys present in the output are applied; others keep their prior values."""
        settings = _settings()
        settings.description = "keep me"
        shared: dict = {}

        apply_pre_gui_output({"name": "NewName"}, settings, shared)

        assert settings.name == "NewName"
        assert settings.description == "keep me"  # not overwritten
        assert shared == {}  # no parameters in output


# Patch targets live on the submitter module, since it imports these names directly.
_MOD = "vred_submitter.vred_submitter"


class TestSanitizeHookDeadlineProperties:
    """``_sanitize_hook_deadline_properties`` guards the ``deadline:`` shared job properties so a
    mistyped hook key can't crash the dialog constructor, and mirrors recognized values onto the
    settings dataclass (which ``save_sticky_settings`` persists)."""

    def test_recognized_keys_coerced_and_mirrored(self):
        """Recognized deadline: keys are coerced to their expected type and mirrored onto the
        matching settings field; non-deadline: keys are left alone."""
        settings = _settings()
        shared = {
            "deadline:priority": "88",  # string coerces to int
            "deadline:maxFailedTasksCount": 5,
            "deadline:targetTaskRunStatus": "SUSPENDED",
            "CondaPackages": "vredcore=2026*",
        }

        _sanitize_hook_deadline_properties(shared, settings)

        assert shared["deadline:priority"] == 88 and isinstance(shared["deadline:priority"], int)
        assert shared["deadline:maxFailedTasksCount"] == 5
        assert shared["deadline:targetTaskRunStatus"] == "SUSPENDED"
        assert shared["CondaPackages"] == "vredcore=2026*"  # non-deadline: untouched
        # Mirrored onto the settings fields so save_sticky_settings stays consistent.
        assert settings.priority == 88
        assert settings.max_failed_tasks_count == 5
        assert settings.initial_status == "SUSPENDED"

    def test_unrecognized_deadline_key_is_dropped_and_logged(self):
        """An unrecognized deadline: key (e.g. a typo) is removed before it can reach the dialog and
        raise KeyError, and the drop is logged."""
        settings = _settings()
        shared = {"deadline:maxFailedTaskCount": 3}  # typo: missing the 's'

        with patch(f"{_MOD}._global_logger") as mock_logger:
            _sanitize_hook_deadline_properties(shared, settings)

        assert "deadline:maxFailedTaskCount" not in shared
        mock_logger.warning.assert_called_once()

    def test_uncoercible_value_is_dropped_and_logged(self):
        """A recognized key with a value that can't coerce to the expected type is dropped (so the
        dialog's setValue can't raise) and the settings field is left unchanged."""
        settings = _settings()
        shared = {"deadline:priority": "high"}  # not an int

        with patch(f"{_MOD}._global_logger") as mock_logger:
            _sanitize_hook_deadline_properties(shared, settings)

        assert "deadline:priority" not in shared
        assert settings.priority == 50  # unchanged
        mock_logger.warning.assert_called_once()

    def test_out_of_domain_status_is_dropped_and_logged(self):
        """targetTaskRunStatus has a fixed allowed set; a valid-type but out-of-domain value (e.g.
        'ready' or 'PAUSED') is dropped rather than mirrored onto the settings, so it can't persist
        an unsupported status the combobox would silently ignore."""
        settings = _settings()  # initial_status default "READY"
        shared = {"deadline:targetTaskRunStatus": "PAUSED"}  # not READY/SUSPENDED

        with patch(f"{_MOD}._global_logger") as mock_logger:
            _sanitize_hook_deadline_properties(shared, settings)

        assert "deadline:targetTaskRunStatus" not in shared
        assert settings.initial_status == "READY"  # unchanged
        mock_logger.warning.assert_called_once()


class TestPreGuiHookConfirmCallback:
    """The ``settings.auto_accept`` branch in ``_pre_gui_hook_confirm_callback``."""

    @patch(f"{_MOD}.get_setting", return_value="true")
    def test_none_when_auto_accept_enabled(self, mock_get_setting):
        """With settings.auto_accept enabled, hooks run without a confirmation prompt."""
        assert _pre_gui_hook_confirm_callback(parent=None) is None
        mock_get_setting.assert_called_once_with("settings.auto_accept")

    @patch("qtpy.QtWidgets.QMessageBox")
    @patch(f"{_MOD}.get_setting", return_value="false")
    def test_dialog_fires_when_auto_accept_disabled(self, mock_get_setting, mock_msgbox):
        """With settings.auto_accept disabled, invoking the returned callback actually shows the
        confirmation dialog (QMessageBox.question), parented to the passed-in window.

        This exercises the real ``qt_hook_confirmation`` callback rather than mocking it out, so it
        verifies the prompt fires — not merely that a non-None callback was selected.
        ``run_pre_gui_hooks`` invokes ``confirm_callback(sources)`` with the hook sources; an empty
        list is enough to reach the dialog. The user's answer maps from the QMessageBox reply.
        """
        mock_msgbox.question.return_value = mock_msgbox.Yes

        callback = _pre_gui_hook_confirm_callback(parent="mainwin")
        assert callback is not None

        result = callback([])  # no hook sources needed to reach the dialog

        assert mock_msgbox.question.call_count == 1
        # The dialog is parented to the window passed into the submitter.
        assert mock_msgbox.question.call_args[0][0] == "mainwin"
        # "Yes" reply → proceed.
        assert result is True


@patch(f"{_MOD}.SubmitJobToDeadlineDialog")
@patch(f"{_MOD}.get_dpi_scale_factor", return_value=1.0)
@patch(f"{_MOD}.get_major_version", return_value="2024")
@patch(f"{_MOD}.os.getenv", return_value=None)
@patch(f"{_MOD}.apply_pre_gui_output")
@patch(f"{_MOD}.run_pre_gui_hooks", return_value={})
@patch(f"{_MOD}._pre_gui_hook_confirm_callback")
class TestCreateSubmitterDialogPreGuiWiring:
    """Unit coverage for the pre-GUI wiring in ``_create_submitter_dialog``.

    deadline-cloud is mocked (as in conftest), so these tests pin the DCC-owned wiring — the
    ``PreGuiHookContext`` build, the confirm-callback selection delegated to
    ``_pre_gui_hook_confirm_callback``, and applying the merged output — that
    ``TestApplyPreGuiOutputForVred`` / ``TestPreGuiHookConfirmCallback`` and the integration suite
    don't cover.
    """

    @staticmethod
    def _submitter():
        with patch(f"{_MOD}.get_yaml_contents", return_value={"steps": []}):
            return VREDSubmitter(Mock())

    def test_hooks_run_and_output_applied_before_dialog(
        self,
        mock_confirm_cb,
        mock_run_hooks,
        mock_apply,
        mock_getenv,
        mock_version,
        mock_dpi,
        mock_dialog,
    ):
        """run_pre_gui_hooks is invoked with a VRED PreGuiHookContext and the confirm callback from
        _pre_gui_hook_confirm_callback; its output is applied onto the settings + shared values via
        apply_pre_gui_output before the dialog is built."""
        mock_run_hooks.return_value = {"name": "FromHook"}
        settings = _settings()

        submitter = self._submitter()
        submitter._create_submitter_dialog(settings, (Mock(), Mock()))

        mock_run_hooks.assert_called_once()
        context = mock_run_hooks.call_args.args[0]
        assert context.bundle_dir is None  # VRED has no on-disk bundle at pre-GUI time
        assert context.submitter_name == "vred"
        assert context.job_name == settings.name
        # The hook is seeded with the settings' priority (from sticky settings), not the default.
        assert context.priority == settings.priority
        assert context.parameters["CondaPackages"] == "vredcore=2024*"

        # The confirm callback is delegated to the helper, parented to the submitter's window.
        mock_confirm_cb.assert_called_once_with(submitter.parent_window)
        assert mock_run_hooks.call_args.kwargs["confirm_callback"] is mock_confirm_cb.return_value

        # The merged output is applied onto copies that (on success) become the settings + shared
        # values the dialog receives — all-or-nothing, committed only if apply doesn't raise.
        mock_apply.assert_called_once()
        applied_output, applied_settings, applied_shared = mock_apply.call_args.args
        assert applied_output == {"name": "FromHook"}
        assert applied_settings is mock_dialog.call_args.kwargs["initial_job_settings"]
        assert applied_settings is not settings  # a copy, not the original
        assert applied_settings.name == settings.name  # ...but a faithful one
        seeded_shared = mock_dialog.call_args.kwargs["initial_shared_parameter_values"]
        assert applied_shared is seeded_shared

    def test_declined_confirmation_aborts_without_dialog(
        self,
        mock_confirm_cb,
        mock_run_hooks,
        mock_apply,
        mock_getenv,
        mock_version,
        mock_dpi,
        mock_dialog,
    ):
        """Declining the hook confirmation makes run_pre_gui_hooks raise DeadlineOperationCanceled;
        _create_submitter_dialog swallows it and returns None (so show_submitter skips showing
        anything) without applying output or building the dialog."""
        mock_run_hooks.side_effect = DeadlineOperationCanceled("user declined hooks")

        submitter = self._submitter()
        result = submitter._create_submitter_dialog(_settings(), (Mock(), Mock()))

        assert result is None
        mock_apply.assert_not_called()
        mock_dialog.assert_not_called()

    def test_faulty_hook_is_logged_and_dialog_still_opens(
        self,
        mock_confirm_cb,
        mock_run_hooks,
        mock_apply,
        mock_getenv,
        mock_version,
        mock_dpi,
        mock_dialog,
    ):
        """A studio hook that raises a non-cancellation exception must not block submission: the
        error is logged, a warning dialog is shown to the artist (env hooks are configured here),
        apply_pre_gui_output is skipped (so the dialog keeps its pristine, un-augmented shared
        values), and the dialog is still built."""
        mock_run_hooks.side_effect = RuntimeError("hook script blew up")

        submitter = self._submitter()
        with (
            patch(f"{_MOD}._global_logger") as mock_logger,
            patch(f"{_MOD}.show_qt_ok_message_dialog") as mock_warn,
            patch.dict("os.environ", {"DEADLINE_HOOKS_DIR": "/tmp/hooks"}),
        ):
            result = submitter._create_submitter_dialog(_settings(), (Mock(), Mock()))

        mock_logger.exception.assert_called_once()
        mock_warn.assert_called_once()  # the degraded state is surfaced to the artist
        mock_apply.assert_not_called()
        mock_dialog.assert_called_once()
        assert result is mock_dialog.return_value
        # The dialog is seeded with the default conda packages, untouched by the failed hook.
        seeded_shared = mock_dialog.call_args.kwargs["initial_shared_parameter_values"]
        assert seeded_shared == {"CondaPackages": "vredcore=2024*"}

    def test_faulty_apply_does_not_leak_partial_mutations(
        self,
        mock_confirm_cb,
        mock_run_hooks,
        mock_apply,
        mock_getenv,
        mock_version,
        mock_dpi,
        mock_dialog,
    ):
        """Applying runs on copies committed only on success. A malformed hook whose apply mutates
        then raises must not leak onto the real settings: the error is logged, the original settings
        object is untouched, and the dialog opens from it (so nothing half-applied can reach the
        later save_sticky_settings)."""
        mock_run_hooks.return_value = {"name": "HALF APPLIED", "parameters": "not-a-dict"}

        def _mutate_then_raise(output, settings_arg, shared_arg):
            # Mutate the (copy) arguments before failing, mimicking apply_pre_gui_output writing
            # name/description before it chokes on a non-dict "parameters".
            settings_arg.name = "HALF APPLIED"
            shared_arg["leaked"] = True
            raise TypeError("malformed hook output")

        mock_apply.side_effect = _mutate_then_raise
        settings = _settings()  # name == "Original"

        submitter = self._submitter()
        with (
            patch(f"{_MOD}._global_logger") as mock_logger,
            patch(f"{_MOD}.show_qt_ok_message_dialog") as mock_warn,
            patch.dict("os.environ", {"DEADLINE_HOOKS_DIR": "/tmp/hooks"}),
        ):
            result = submitter._create_submitter_dialog(settings, (Mock(), Mock()))

        mock_apply.assert_called_once()
        mock_logger.exception.assert_called_once()
        mock_warn.assert_called_once()
        mock_dialog.assert_called_once()
        assert result is mock_dialog.return_value
        # The original settings is untouched and is what the dialog is built from — not a half-applied copy.
        assert settings.name == "Original"
        assert mock_dialog.call_args.kwargs["initial_job_settings"] is settings
        seeded_shared = mock_dialog.call_args.kwargs["initial_shared_parameter_values"]
        assert "leaked" not in seeded_shared
        assert seeded_shared == {"CondaPackages": "vredcore=2024*"}

    def test_no_warning_dialog_when_env_hooks_not_configured(
        self,
        mock_confirm_cb,
        mock_run_hooks,
        mock_apply,
        mock_getenv,
        mock_version,
        mock_dpi,
        mock_dialog,
    ):
        """When no hooks directory is configured (the default for most users), a failure on the
        hook path is logged but shows NO dialog — a config-read error must not pop a phantom
        "hook failed" dialog for someone who never set DEADLINE_HOOKS_DIR. The submitter still opens.
        """
        mock_run_hooks.side_effect = RuntimeError("config read blew up")

        submitter = self._submitter()
        with (
            patch(f"{_MOD}._global_logger") as mock_logger,
            patch(f"{_MOD}.show_qt_ok_message_dialog") as mock_warn,
            patch.dict("os.environ", {"DEADLINE_HOOKS_DIR": ""}),  # unset -> falsy gate
        ):
            result = submitter._create_submitter_dialog(_settings(), (Mock(), Mock()))

        mock_logger.exception.assert_called_once()
        mock_warn.assert_not_called()  # no phantom dialog on the no-hooks path
        mock_dialog.assert_called_once()
        assert result is mock_dialog.return_value
