# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Provides Qt-based Custom UI Controls"""

from typing import Optional

from .ui.components.constants import Constants as UIConstants

from PySide6.QtCore import QEvent, Qt, QSize
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpacerItem,
    QWidget,
)


class CustomGroupBox(QGroupBox):
    """
    A QGroupBox that has a custom stylesheet applied
    """

    def __init__(self, text: str = "", parent: QWidget = None):
        """
        param: text: the text to be displayed in the group box's title.
        param: parent: the parent widget
        """
        super().__init__(text, parent)
        self.setStyleSheet(UIConstants.QT_GROUP_BOX_STYLESHEET)

    def setLayout(self, layout):
        """
        Set the layout for this group box.
        param: layout: the layout to set for this group box
        """
        QGroupBox.setLayout(self, layout)


class AutoSizedButton(QPushButton):
    """
    A QPushButton that automatically adjusts its size based on its text content.
    """

    def __init__(self, text: str = "", parent: QPushButton = None):
        """
        param: text: the text to be displayed on the push button.
        param: parent: the parent widget
        """
        super().__init__(text, parent)
        self.setMinimumWidth(self.calculate_width())

    def calculate_width(self) -> int:
        """
        Calculate the width of the button based on its text content.
        return: the calculated width
        """
        if not self.text():
            return 0
        text_width = int(QFontMetrics(self.font()).horizontalAdvance(self.text()))
        return int(
            (text_width + UIConstants.PUSH_BUTTON_PADDING_PIXELS)
            / UIConstants.PUSH_BUTTON_WIDTH_FACTOR
        )

    def sizeHint(self) -> QSize:
        """
        Overrides to adjust the width of the button.
        return: the size hint
        """
        super().sizeHint().setWidth(self.calculate_width())
        return super().sizeHint()


class AutoSizedComboBox(QComboBox):
    """
    A QComboBox that automatically adjusts its size based on the maximum length of its entries.
    """

    def __init__(self, parent: QComboBox = None):
        """
        param: parent: the parent widget
        """

        super().__init__(parent)
        self.forced_override_minimum_width = 0
        self.max_width = 0
        # Perform automatic resizing when entries are changed
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.model().rowsInserted.connect(self.adjust_size_callback)
        self.model().rowsRemoved.connect(self.adjust_size_callback)

    def set_current_entry(self, entry_name: str) -> None:
        """
        Sets the current entry of the combo box to match entry_name; else sets the 0th index as active entry.
        param: entry_name: entry to match
        """
        super().setCurrentIndex(max(0, super().findText(entry_name)))

    def adjust_size_callback(self) -> None:
        """
        Adjust the size of the combo box based on the maximum length of its entries (if that size wasn't overridden)
        """
        if self.forced_override_minimum_width > 0:
            return
        # Avoid shrinking and find the widest entry
        self.setMinimumWidth(self.sizeHint().width())
        metrics = QFontMetrics(self.font())
        max_width = 0
        for i in range(self.count()):
            width = metrics.horizontalAdvance(self.itemText(i))
            max_width = max(max_width, width)
        # Add padding for dropdown arrow and frame
        self.max_width = max(
            max_width + UIConstants.COMBO_BOX_PADDING, UIConstants.COMBO_BOX_MIN_WIDTH
        )
        self.setFixedWidth(self.max_width)
        # Popup view should also be sufficiently wide
        if self.view():
            self.view().setMinimumWidth(self.max_width)

    def set_width(self, width: int) -> None:
        """
        Sets the minimum width of the combo box - this overrides any prior automatically determined settings
        param: width: the minimum width to be set
        """
        self.forced_override_minimum_width = width
        self.setMinimumWidth(width)
        self.setFixedWidth(width)
        if self.view():
            self.view().setMinimumWidth(width)
        self.max_width = width

    def get_width(self) -> int:
        """
        Gets the width of the combo box
        return: the width of the combo box
        """
        return self.max_width


class AutoSizingMessageBox(QMessageBox):
    """
    A QMessageBox that automatically adjusts its size based on its text content.
    """

    def __init__(self, parent):
        """
        param: parent: the parent widget
        """
        super().__init__(parent)
        # Rich text improves formatting
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setMinimumWidth(UIConstants.MESSAGE_BOX_MIN_WIDTH)
        self.setMaximumWidth(UIConstants.MESSAGE_BOX_MAX_WIDTH)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())

    def resizeEvent(self, event: QEvent) -> None:
        """
        Overrides resize event handler to adjust the layout.
        param: event: resize event
        """
        result = super().resizeEvent(event)
        # Horizontal spacer helps to adjust layout width
        layout = self.layout()
        if layout is not None and isinstance(layout, QGridLayout):
            spacer = QSpacerItem(UIConstants.MESSAGE_BOX_SPACER_PREFERRED_WIDTH, 0)
            layout.addItem(spacer, layout.rowCount(), 0, 1, layout.columnCount())
        return result


class FileSearchLineEdit(QWidget):
    """
    A widget containing a QLineEdit and QPushButton object for specifying a file or directory.
    """

    def __init__(
        self, file_format: str = "", directory_only: bool = False, parent: Optional[QWidget] = None
    ):
        """
        param: file_format: the file format from which to filter
        param: directory_only: whether to allow directory selection only
        param: parent: the parent widget
        raise: ValueError: file_format missing when directory_only specified
        """
        super().__init__(parent=parent)
        if directory_only and file_format:
            raise ValueError
        self.file_format = file_format
        self.directory_only = directory_only
        self.path_text_box = QLineEdit(self)
        self.button = QPushButton(UIConstants.ELLIPSIS_LABEL, parent=self)
        self.setup()

    def setup(self) -> None:
        """
        Sets up the layout of the QLineEdit and push button controls.
        """
        self.path_text_box.setFixedWidth(UIConstants.VERY_LONG_TEXT_ENTRY_WIDTH)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.button.setMaximumSize(
            QSize(UIConstants.PUSH_BUTTON_MAXIMUM_WIDTH, UIConstants.PUSH_BUTTON_MAXIMUM_HEIGHT)
        )
        self.button.clicked.connect(self.common_file_dialog_callback)
        layout.addWidget(self.path_text_box)
        layout.addWidget(self.button)

    def common_file_dialog_callback(self) -> None:
        """
        Open a common file dialog for selecting a file or directory (depending on self.directory_only) and
        put its path (if specified) into a QLineEdit text box (self.path_text_box) for future use.
        """
        if self.directory_only:
            new_path_str = QFileDialog.getExistingDirectory(
                self,
                UIConstants.SELECT_DIRECTORY_PROMPT,
                self.path_text_box.text(),
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
            )
        else:
            new_path_str = QFileDialog.getOpenFileName(
                self, UIConstants.SELECT_FILE_PROMPT, self.path_text_box.text()
            )

        if new_path_str:
            self.path_text_box.setText(new_path_str)

    def text(self) -> str:
        """
        return: the path text from the internal QLineEdit control
        """
        return self.path_text_box.text()
