# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for Qt UI components used in VRED submitter."""
import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from vred_submitter.qt_components import (
    CustomGroupBox,
    AutoSizedButton,
    AutoSizedComboBox,
    AutoSizingMessageBox,
    FileSearchLineEdit,
)


class TestCustomGroupBox:
    """Test CustomGroupBox widget initialization and properties."""

    def test_init_default(self, qapp):
        # Test default initialization
        group_box = CustomGroupBox()
        assert group_box.title() == ""
        assert group_box.parent() is None

    def test_init_with_text_and_parent(self, qapp):
        # Test initialization with title and parent
        parent = QWidget()
        group_box = CustomGroupBox("Test Title", parent)
        assert group_box.title() == "Test Title"
        assert group_box.parent() == parent


class TestAutoSizedButton:
    """Test AutoSizedButton widget functionality and width calculations."""

    def test_init_default(self, qapp):
        # Test default button initialization
        button = AutoSizedButton()
        assert button.text() == ""
        assert button.parent() is None

    def test_init_with_text_and_parent(self, qapp):
        # Test button with text and parent
        parent = QWidget()
        button = AutoSizedButton("Test Button", parent)
        assert button.text() == "Test Button"
        assert button.parent() == parent

    @patch("vred_submitter.qt_components.QFontMetrics")
    def test_calculate_width_empty_text(self, mock_font_metrics, qapp):
        # Empty text should return zero width
        button = AutoSizedButton("")
        result = button.calculate_width()
        assert result == 0

    @patch("vred_submitter.qt_components.QFontMetrics")
    def test_calculate_width_with_text(self, mock_font_metrics, qapp):
        # Test width calculation with text
        mock_metrics = Mock()
        mock_metrics.horizontalAdvance.return_value = 100
        mock_font_metrics.return_value = mock_metrics

        button = AutoSizedButton("Test")
        button.calculate_width()

        # QFontMetrics called in __init__ and calculate_width
        assert mock_font_metrics.call_count == 2


class TestAutoSizedComboBox:
    """Test AutoSizedComboBox widget sizing and item selection."""

    def test_init_default(self, qapp):
        # Test default combo box initialization
        combo_box = AutoSizedComboBox()
        assert combo_box.parent() is None
        assert combo_box.forced_override_minimum_width == 0
        assert combo_box.max_width == 0

    def test_init_with_parent(self, qapp):
        # Test combo box with parent widget
        parent = QWidget()
        combo_box = AutoSizedComboBox(parent)
        assert combo_box.parent() == parent

    def test_set_current_entry_existing(self, qapp):
        # Test selecting existing item
        combo_box = AutoSizedComboBox()
        combo_box.addItems(["Item1", "Item2", "Item3"])
        combo_box.set_current_entry("Item2")
        assert combo_box.currentText() == "Item2"

    def test_set_current_entry_nonexistent(self, qapp):
        # Test selecting non-existent item defaults to first
        combo_box = AutoSizedComboBox()
        combo_box.addItems(["Item1", "Item2", "Item3"])
        combo_box.set_current_entry("NonExistent")
        assert combo_box.currentIndex() == 0

    def test_set_width(self, qapp):
        # Test width setting functionality
        combo_box = AutoSizedComboBox()
        combo_box.set_width(200)
        assert combo_box.forced_override_minimum_width == 200
        assert combo_box.max_width == 200

    def test_get_width(self, qapp):
        # Test width retrieval
        combo_box = AutoSizedComboBox()
        combo_box.max_width = 150
        assert combo_box.get_width() == 150


class TestAutoSizingMessageBox:
    """Test AutoSizingMessageBox widget initialization and formatting."""

    def test_init(self, qapp):
        # Test message box with rich text format
        parent = QWidget()
        message_box = AutoSizingMessageBox(parent)
        assert message_box.parent() == parent
        assert message_box.textFormat() == Qt.TextFormat.RichText


class TestFileSearchLineEdit:
    """Test FileSearchLineEdit widget for file/directory selection."""

    def test_init_default(self, qapp):
        # Test default file search widget
        widget = FileSearchLineEdit()
        assert widget.file_format == ""
        assert not widget.directory_only

    def test_init_with_file_format(self, qapp):
        # Test with specific file format filter
        widget = FileSearchLineEdit(file_format="*.txt")
        assert widget.file_format == "*.txt"
        assert not widget.directory_only

    def test_init_directory_only(self, qapp):
        # Test directory-only selection mode
        widget = FileSearchLineEdit(directory_only=True)
        assert widget.file_format == ""
        assert widget.directory_only

    def test_init_invalid_combination(self, qapp):
        # Test invalid combination raises error
        with pytest.raises(ValueError):
            FileSearchLineEdit(file_format="*.txt", directory_only=True)

    def test_text_method(self, qapp):
        # Test text retrieval from path text box
        widget = FileSearchLineEdit()
        widget.path_text_box.setText("/test/path")
        assert widget.text() == "/test/path"
