# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Qt-based Convenience/Utility Functions"""

from .qt_components import AutoSizingMessageBox

from PySide6.QtWidgets import QMessageBox


def show_qt_ok_message_dialog(title: str, message: str) -> None:
    """
    Display a modal information dialog box containing an OK button.
    param: title: the title of the dialog window
    param: message: the message to display in the dialog
    """
    message_box = AutoSizingMessageBox(parent=None)
    message_box.setWindowTitle(title)
    message_box.setText(message)
    message_box.setIcon(QMessageBox.Icon.Information)
    message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    message_box.exec()


def get_qt_yes_no_dialog_prompt_result(title: str, message: str, default_to_yes: bool) -> bool:
    """
    Display a modal question dialog box containing Yes/No buttons and return the user's choice.
    param: title: the title of the dialog window
    param: message: the question to display in the dialog
    param: default_to_yes: if True, the "Yes" button will be the default selection; else "No" button
    return: True if the user selected the "Yes" button; False otherwise
    """
    message_box = AutoSizingMessageBox(parent=None)
    message_box.setWindowTitle(title)
    message_box.setText(message)
    message_box.setIcon(QMessageBox.Icon.Question)
    message_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    default_button = (
        QMessageBox.StandardButton.Yes if default_to_yes else QMessageBox.StandardButton.No
    )
    message_box.setDefaultButton(default_button)
    return message_box.exec() == QMessageBox.StandardButton.Yes
