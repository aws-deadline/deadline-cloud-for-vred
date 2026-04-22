# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QWidget


@pytest.fixture
def mock_main_window():
    # Create a mock main window with menu bar
    window = MagicMock()
    menu_bar = MagicMock()
    window.menuBar.return_value = menu_bar
    menu_bar.findChildren.return_value = []
    return window


@pytest.fixture
def mock_submitter():
    # Create a mock VREDSubmitter
    submitter = MagicMock()
    dialog = MagicMock(spec=QWidget)
    dialog.isVisible.return_value = False
    submitter.show_submitter.return_value = dialog
    return submitter


class TestSceneFileChangedCallback:
    """Tests for scene_file_changed_callback function"""

    @patch("vred_submitter.vred_submitter_wrapper._global_submitter_dialog", None)
    def test_handles_none_dialog(self):
        # Ensure graceful handling when dialog is None
        from vred_submitter.vred_submitter_wrapper import scene_file_changed_callback

        # Should not raise exception
        scene_file_changed_callback()

    @patch("vred_submitter.vred_submitter_wrapper._global_submitter_dialog")
    def test_closes_dialog(self, mock_dialog):
        # Verify dialog cleanup on scene file change
        from vred_submitter import vred_submitter_wrapper

        mock_dialog_instance = MagicMock()
        vred_submitter_wrapper._global_submitter_dialog = mock_dialog_instance

        vred_submitter_wrapper.scene_file_changed_callback()

        mock_dialog_instance.close.assert_called_once()
        assert vred_submitter_wrapper._global_submitter_dialog is None


class TestAddDeadlineCloudMenu:
    """Tests for add_deadline_cloud_menu function"""

    @patch("vred_submitter.vred_submitter_wrapper.assign_scene_transition_event")
    @patch("vred_submitter.vred_submitter_wrapper.get_main_window")
    @patch("vred_submitter.vred_submitter_wrapper.QMenu")
    @patch("vred_submitter.vred_submitter_wrapper.QAction")
    def test_creates_menu(self, mock_action_cls, mock_menu_cls, mock_get_window, mock_assign):
        # Verify menu creation with proper action connections
        from vred_submitter.vred_submitter_wrapper import add_deadline_cloud_menu

        mock_window = MagicMock()
        mock_menu_bar = MagicMock()
        mock_window.menuBar.return_value = mock_menu_bar
        mock_menu_bar.findChildren.return_value = []
        mock_get_window.return_value = mock_window

        mock_menu = MagicMock()
        mock_menu_cls.return_value = mock_menu
        mock_menu.actions.return_value = []

        mock_action = MagicMock()
        mock_action_cls.return_value = mock_action

        add_deadline_cloud_menu()

        mock_assign.assert_called_once()
        mock_menu_bar.addMenu.assert_called_once_with(mock_menu)
        mock_action.triggered.connect.assert_called_once()
        mock_menu.addAction.assert_called_once_with(mock_action)

    @patch("vred_submitter.vred_submitter_wrapper.assign_scene_transition_event")
    @patch("vred_submitter.vred_submitter_wrapper.get_main_window")
    def test_prevents_duplicates(self, mock_get_window, mock_assign):
        # Ensure duplicate menu prevention logic works
        from vred_submitter.vred_submitter_wrapper import add_deadline_cloud_menu, Constants

        mock_window = MagicMock()
        mock_menu_bar = MagicMock()
        mock_window.menuBar.return_value = mock_menu_bar

        existing_menu = MagicMock()
        existing_menu.title.return_value = Constants.DEADLINE_CLOUD_MENU
        existing_action = MagicMock()
        existing_action.text.return_value = Constants.SUBMIT_TO_DEADLINE_CLOUD_ACTION
        existing_menu.actions.return_value = [existing_action]

        mock_menu_bar.findChildren.return_value = [existing_menu]
        mock_get_window.return_value = mock_window

        add_deadline_cloud_menu()

        mock_menu_bar.addMenu.assert_not_called()
        existing_menu.addAction.assert_not_called()

    @patch("vred_submitter.vred_submitter_wrapper.assign_scene_transition_event")
    @patch("vred_submitter.vred_submitter_wrapper.get_main_window", return_value=None)
    def test_no_main_window(self, mock_get_window, mock_assign):
        # Verify error handling when main window unavailable
        from vred_submitter.vred_submitter_wrapper import add_deadline_cloud_menu

        with pytest.raises(AttributeError):
            add_deadline_cloud_menu()


class TestSubmitToDeadlineCloud:
    """Tests for submit_to_deadline_cloud function"""

    @patch("vred_submitter.vred_submitter_wrapper.check_and_show_update_dialog", return_value=False)
    @patch("vred_submitter.vred_submitter_wrapper.get_main_window")
    @patch("vred_submitter.vred_submitter_wrapper.VREDSubmitter")
    def test_singleton_behavior(self, mock_submitter_cls, mock_get_window, mock_check_update):
        # Verify dialog singleton pattern implementation
        from vred_submitter import vred_submitter_wrapper

        vred_submitter_wrapper._global_submitter_dialog = None

        mock_window = MagicMock()
        mock_get_window.return_value = mock_window

        mock_submitter = MagicMock()
        mock_dialog = MagicMock()
        mock_dialog.isVisible.return_value = False
        mock_submitter.show_submitter.return_value = mock_dialog
        mock_submitter_cls.return_value = mock_submitter

        vred_submitter_wrapper.submit_to_deadline_cloud()

        mock_submitter_cls.assert_called_once()
        mock_submitter.show_submitter.assert_called_once()
        assert vred_submitter_wrapper._global_submitter_dialog == mock_dialog

    @patch("vred_submitter.vred_submitter_wrapper.check_and_show_update_dialog", return_value=False)
    @patch("vred_submitter.vred_submitter_wrapper.get_main_window")
    @patch("vred_submitter.vred_submitter_wrapper.VREDSubmitter")
    def test_reuses_existing_dialog(self, mock_submitter_cls, mock_get_window, mock_check_update):
        # Ensure existing dialog is reused and raised
        from vred_submitter import vred_submitter_wrapper

        mock_dialog = MagicMock()
        mock_dialog.isVisible.return_value = True
        vred_submitter_wrapper._global_submitter_dialog = mock_dialog

        vred_submitter_wrapper.submit_to_deadline_cloud()

        mock_dialog.raise_.assert_called_once()
        mock_dialog.activateWindow.assert_called_once()
        mock_submitter_cls.assert_not_called()
