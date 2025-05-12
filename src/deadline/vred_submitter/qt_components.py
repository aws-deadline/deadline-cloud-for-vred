# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Provides Qt-based Custom UI Controls"""

from typing import Optional

from .constants import Constants

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

    def __init__(self, text: str = "", parent: QGroupBox = None):
        """
        param: text: the text to be displayed in the group box's title.
        param: parent: the parent widget
        """
        super().__init__(text, parent)
        self.setStyleSheet(Constants.QT_GROUP_BOX_STYLESHEET)


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
            (text_width + Constants.PUSH_BUTTON_PADDING_PIXELS) / Constants.PUSH_BUTTON_WIDTH_FACTOR
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
        # Perform automatic resizing when entries are changed
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.model().rowsInserted.connect(self.adjust_size_callback)
        self.model().rowsRemoved.connect(self.adjust_size_callback)

    def adjust_size_callback(self) -> None:
        """
        Adjust the size of the combo box based on the maximum length of its entries.
        """
        # Avoid shrinking and find the widest entry
        self.setMinimumWidth(self.sizeHint().width())
        metrics = QFontMetrics(self.font())
        max_width = 0
        for i in range(self.count()):
            width = metrics.horizontalAdvance(self.itemText(i))
            max_width = max(max_width, width)
        # Add padding for dropdown arrow and frame
        max_width = max(max_width + Constants.COMBO_BOX_PADDING, Constants.COMBO_BOX_MIN_WIDTH)
        self.setFixedWidth(max_width)
        # Popup view should also be sufficiently wide
        if self.view():
            self.view().setMinimumWidth(max_width)


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
        self.setMinimumWidth(Constants.MESSAGE_BOX_MIN_WIDTH)
        self.setMaximumWidth(Constants.MESSAGE_BOX_MAX_WIDTH)
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
            spacer = QSpacerItem(Constants.MESSAGE_BOX_SPACER_PREFERRED_WIDTH, 0)
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
        self.button = QPushButton(Constants.ELLIPSIS_LABEL, parent=self)
        self.setup()

    def setup(self) -> None:
        """
        Sets up the layout of the QLineEdit and push button controls.
        """
        self.path_text_box.setFixedWidth(Constants.VERY_LONG_TEXT_ENTRY_WIDTH)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.button.setMaximumSize(
            QSize(Constants.PUSH_BUTTON_MAXIMUM_WIDTH, Constants.PUSH_BUTTON_MAXIMUM_HEIGHT)
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
                Constants.SELECT_DIRECTORY_PROMPT,
                self.path_text_box.text(),
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
            )
        else:
            new_path_str = QFileDialog.getOpenFileName(
                self, Constants.SELECT_FILE_PROMPT, self.path_text_box.text()
            )

        if new_path_str:
            self.path_text_box.setText(new_path_str)

    def text(self) -> str:
        """
        return: the path text from the internal QLineEdit control
        """
        return self.path_text_box.text()
