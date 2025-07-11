# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for Qt utility functions for dialogs and widget management."""
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QWidget, QMessageBox

from vred_submitter.qt_utils import (
    show_qt_ok_message_dialog,
    get_qt_yes_no_dialog_prompt_result,
    center_widget,
    get_dpi_scale_factor,
)


class TestShowQtOkMessageDialog:
    """Test OK message dialog display functionality."""

    @patch("vred_submitter.qt_utils.AutoSizingMessageBox")
    def test_show_qt_ok_message_dialog(self, mock_message_box_class, qapp):
        mock_message_box = Mock()
        mock_message_box_class.return_value = mock_message_box

        show_qt_ok_message_dialog("Test Title", "Test Message")

        mock_message_box_class.assert_called_once_with(parent=None)
        mock_message_box.setWindowTitle.assert_called_once_with("Test Title")
        mock_message_box.setText.assert_called_once_with("Test Message")
        mock_message_box.setIcon.assert_called_once_with(QMessageBox.Icon.Information)
        mock_message_box.setStandardButtons.assert_called_once_with(QMessageBox.StandardButton.Ok)
        mock_message_box.exec.assert_called_once()


class TestGetQtYesNoDialogPromptResult:
    """Test Yes/No dialog prompt functionality."""

    @patch("vred_submitter.qt_utils.AutoSizingMessageBox")
    def test_get_qt_yes_no_dialog_prompt_result_yes_default(self, mock_message_box_class, qapp):
        mock_message_box = Mock()
        mock_message_box.exec.return_value = QMessageBox.StandardButton.Yes
        mock_message_box_class.return_value = mock_message_box

        result = get_qt_yes_no_dialog_prompt_result("Test Title", "Test Message", True)

        assert result
        mock_message_box.setDefaultButton.assert_called_once_with(QMessageBox.StandardButton.Yes)

    @patch("vred_submitter.qt_utils.AutoSizingMessageBox")
    def test_get_qt_yes_no_dialog_prompt_result_no_default(self, mock_message_box_class, qapp):
        mock_message_box = Mock()
        mock_message_box.exec.return_value = QMessageBox.StandardButton.No
        mock_message_box_class.return_value = mock_message_box

        result = get_qt_yes_no_dialog_prompt_result("Test Title", "Test Message", False)

        assert not result
        mock_message_box.setDefaultButton.assert_called_once_with(QMessageBox.StandardButton.No)

    @patch("vred_submitter.qt_utils.AutoSizingMessageBox")
    def test_get_qt_yes_no_dialog_prompt_result_user_selects_yes(
        self, mock_message_box_class, qapp
    ):
        mock_message_box = Mock()
        mock_message_box.exec.return_value = QMessageBox.StandardButton.Yes
        mock_message_box_class.return_value = mock_message_box

        result = get_qt_yes_no_dialog_prompt_result("Test Title", "Test Message", False)

        assert result


class TestCenterWidget:
    """Test widget centering on screen functionality."""

    @patch("vred_submitter.qt_utils.QGuiApplication")
    def test_center_widget(self, mock_qgui_app, qapp):
        mock_size = Mock()
        mock_size.width.return_value = 1920
        mock_size.height.return_value = 1080

        mock_screen = Mock()
        mock_screen.size.return_value = mock_size
        mock_qgui_app.primaryScreen.return_value = mock_screen

        widget = QWidget()
        widget.width = Mock(return_value=800)
        widget.height = Mock(return_value=600)
        widget.move = Mock()

        center_widget(widget)

        expected_x = (1920 - 800) // 2
        expected_y = (1080 - 600) // 2
        widget.move.assert_called_once_with(expected_x, expected_y)


class TestGetDpiScaleFactor:
    """Test DPI scale factor calculation for high-DPI displays."""

    @patch("vred_submitter.qt_utils.QGuiApplication")
    def test_get_dpi_scale_factor(self, mock_qgui_app, qapp):
        mock_screen = Mock()
        mock_screen.logicalDotsPerInch.return_value = 144.0
        mock_qgui_app.primaryScreen.return_value = mock_screen

        result = get_dpi_scale_factor()

        # 144 / 96 = 1.5
        assert result == 1.5

    @patch("vred_submitter.qt_utils.QGuiApplication")
    def test_get_dpi_scale_factor_standard_dpi(self, mock_qgui_app, qapp):
        mock_screen = Mock()
        mock_screen.logicalDotsPerInch.return_value = 96.0
        mock_qgui_app.primaryScreen.return_value = mock_screen

        result = get_dpi_scale_factor()

        # 96 / 96 = 1.0
        assert result == 1.0
