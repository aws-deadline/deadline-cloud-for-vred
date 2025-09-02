# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Provides a high-level interface to the DeadlineCloudForVRED bootstrapper to create a persistent
VRED menu for Deadline Cloud. This menu effectively triggers the Deadline Cloud UI via VREDSubmitter.
"""

from typing import Any, Optional

from .constants import Constants
from .vred_submitter import VREDSubmitter
from .vred_utils import assign_scene_transition_event, get_main_window

from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QWidget

# Track deadline Deadline Cloud dialog instance
#
_global_submitter_dialog: Optional[QWidget] = None


def scene_file_changed_callback(*dummy_args: Any) -> None:
    """
    Callback to close and reset the existing Deadline Cloud dialog.
    param: dummy_args: conventional variable arguments passed by signal connections (unused)
    """
    global _global_submitter_dialog
    if _global_submitter_dialog is not None:
        _global_submitter_dialog.close()
        _global_submitter_dialog = None


def add_deadline_cloud_menu() -> None:
    """
    Add the Deadline Cloud menu to VRED's main menu bar. Includes:
    - "Submit to Deadline Cloud" menu item action that triggers the submission dialog
    - Initialization of necessary callbacks for dialog management between scene file sessions
    - Note: this should only be invoked once per entire VRED session.
    """
    # Initialize callbacks to manage Deadline Cloud dialog state. Connects scene transition events (new scene and
    # project load) to ensure that the Deadline Cloud dialog is properly closed and reset, preventing a stale state.
    assign_scene_transition_event(scene_file_changed_callback)
    vred_menu_bar = get_main_window().menuBar()
    deadline_cloud_menu = None
    for child in vred_menu_bar.findChildren(QMenu):
        if child.title() == Constants.DEADLINE_CLOUD_MENU:
            deadline_cloud_menu = child
            break
    if deadline_cloud_menu is None:
        deadline_cloud_menu = QMenu(Constants.DEADLINE_CLOUD_MENU, vred_menu_bar)
        deadline_cloud_menu.setObjectName(Constants.DEADLINE_CLOUD_MENU)
        vred_menu_bar.addMenu(deadline_cloud_menu)
    submit_action_exists = any(
        action.text() == Constants.SUBMIT_TO_DEADLINE_CLOUD_ACTION
        for action in deadline_cloud_menu.actions()
    )
    if not submit_action_exists:
        deadline_action = QAction(Constants.SUBMIT_TO_DEADLINE_CLOUD_ACTION, deadline_cloud_menu)
        deadline_action.triggered.connect(submit_to_deadline_cloud)
        deadline_cloud_menu.addAction(deadline_action)


def submit_to_deadline_cloud() -> None:
    """Show the Deadline Cloud submission dialog, while preventing  duplicate dialogs from appearing."""
    global _global_submitter_dialog
    if _global_submitter_dialog is not None and _global_submitter_dialog.isVisible():
        _global_submitter_dialog.raise_()
        _global_submitter_dialog.activateWindow()
        return
    submitter = VREDSubmitter(get_main_window(), Qt.Tool)
    _global_submitter_dialog = submitter.show_submitter()
