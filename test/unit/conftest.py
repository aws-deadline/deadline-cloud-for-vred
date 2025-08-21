# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import pytest
import sys

# Used to prevent MemoryError messages
import yaml  # noqa: F401
from pathlib import Path
from unittest.mock import MagicMock

# Add submitter parent directory to Python path
SUBMITTER_PARENT_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "deadline"
if str(SUBMITTER_PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(SUBMITTER_PARENT_DIR))

# Mock qtpy modules
sys.modules["qtpy"] = MagicMock()
sys.modules["qtpy.QtCore"] = MagicMock()
sys.modules["qtpy.QtWidgets"] = MagicMock()
sys.modules["qtpy.QtGui"] = MagicMock()

# Mock Deadline Cloud modules
deadline_mock = MagicMock()
deadline_mock.client.ui.dialogs.submit_job_to_deadline_dialog.DeadlineAuthenticationStatus.getInstance.return_value = (
    MagicMock()
)
sys.modules["deadline.client.ui.dialogs.submit_job_to_deadline_dialog"] = (
    deadline_mock.client.ui.dialogs.submit_job_to_deadline_dialog
)

# Mock VRED API (V1)
for module in ["vrAnimWidgets", "vrController", "vrRenderSettings", "vrSequencer"]:
    sys.modules[module] = MagicMock()

# vrOSGWidget with required constants
mock_osg = MagicMock()
mock_osg.getDLSSQuality.return_value = 0
mock_osg.getSuperSamplingQuality.return_value = 0

# Add VRED quality constants
quality_constants = {
    "VR_DLSS_": ["OFF", "PERFORMANCE", "BALANCED", "QUALITY", "ULTRA_PERFORMANCE"],
    "VR_SS_QUALITY_": ["OFF", "LOW", "MEDIUM", "HIGH", "ULTRA_HIGH"],
    "VR_QUALITY_": [
        "ANALYTIC_LOW",
        "ANALYTIC_HIGH",
        "REALISTIC_LOW",
        "REALISTIC_HIGH",
        "RAYTRACING",
        "NPR",
    ],
}
for prefix, suffixes in quality_constants.items():
    for i, suffix in enumerate(suffixes):
        setattr(mock_osg, f"{prefix}{suffix}", i)
sys.modules["vrOSGWidget"] = mock_osg

# Mock VRED API (V2)
mock_builtins = MagicMock()
for service in ["vrCameraService", "vrFileIOService", "vrMainWindow", "vrReferenceService"]:
    setattr(mock_builtins, service, MagicMock())
sys.modules["builtins"] = mock_builtins


# Mock PySide6 modules
class MockQtWidget:
    """Base mock Qt widget with common functionality."""

    def __init__(self, *args, **kwargs):
        self._current_text = ""
        self._items = []
        self._parent = (
            args[0]
            if args and not isinstance(args[0], str)
            else (args[1] if len(args) > 1 else None)
        )
        self._text = args[0] if args and isinstance(args[0], str) else ""
        self.directory_only = kwargs.get("directory_only", False)
        self.file_format = kwargs.get("file_format", "")
        self.forced_override_minimum_width = 0
        self.max_width = 0

        if self.directory_only and self.file_format:
            raise ValueError()

        # Create path_text_box for FileSearchLineEdit
        self.path_text_box = type(
            "MockLineEdit", (), {"text": lambda: "/test/path", "setText": lambda x: None}
        )()

    def addItems(self, items):
        self._items = items

    def calculate_width(self):
        return 0

    def click(self):
        pass

    def clicked(self):
        return type("MockSignal", (), {"connect": lambda x: None})()

    def count(self):
        return 3

    def currentIndex(self):
        return 0

    def currentText(self):
        return self._current_text

    def eventFilter(self, obj, event):
        return False

    def findText(self, text):
        return self._items.index(text) if text in self._items else -1

    def font(self):
        return type("MockFont", (), {})()

    def get_button(self):
        if not hasattr(self, "_button"):
            self._button = MockQtWidget()
        return self._button

    def get_width(self):
        return self.max_width

    def horizontalAdvance(self, text):
        return 100

    def installEventFilter(self, filter):
        pass

    def itemText(self, i):
        return f"Item{i + 1}"

    def layout(self):
        from types import SimpleNamespace

        mock_layout = SimpleNamespace()
        mock_layout.addLayout = lambda x: None
        mock_layout.addWidget = lambda *args, **kwargs: None
        return mock_layout

    def maximum(self):
        return 10000

    def minimum(self):
        return 1

    def maxLength(self):
        return 31

    def hasAcceptableInput(self):
        # Simple validation logic for testing
        text = self._text
        if not text:
            return True

        # Check for non-numeric input in numeric fields
        if text in ["abc", "invalid"]:
            return False

        # Check boundary values for integer fields
        if text.isdigit():
            value = int(text)
            if value == 0 or value > 10000:
                return False

        # Check boundary values for float fields
        try:
            float_value = float(text)
            if float_value < 0.04 or float_value > 25400.0:
                return False
        except ValueError:
            # Not a float, must be a string, just continue on
            pass

        return True

    def setValue(self, value):
        self._value = max(self.minimum(), min(self.maximum(), value))

    def value(self):
        return getattr(self, "_value", 1)

    def model(self):
        return type(
            "MockModel",
            (),
            {
                "rowsInserted": type("MockSignal", (), {"connect": lambda self, x: None})(),
                "rowsRemoved": type("MockSignal", (), {"connect": lambda self, x: None})(),
            },
        )()

    def parent(self):
        return self._parent

    def set_current_entry(self, entry):
        index = self.findText(entry)
        if index >= 0:
            self.setCurrentIndex(index)
        else:
            self.setCurrentIndex(0)

    def set_width(self, width):
        self.forced_override_minimum_width = width
        self.max_width = width

    def setCurrentIndex(self, index):
        if 0 <= index < len(self._items):
            self._current_text = self._items[index]

    def setFixedWidth(self, width):
        pass

    def setLayout(self, layout):
        self._layout = layout

    def setMaxLength(self, length):
        pass

    def setMaximum(self, value):
        pass

    def setMaximumSize(self, size):
        pass

    def setMaximumWidth(self, width):
        pass

    def setMinimum(self, value):
        pass

    def setMinimumWidth(self, width):
        pass

    def setSizeAdjustPolicy(self, policy):
        pass

    def setSizePolicy(self, h, v):
        pass

    def setStyleSheet(self, style):
        pass

    def setText(self, text):
        self._text = text

    def setTextFormat(self, format):
        pass

    def setToolTip(self, tooltip):
        pass

    def setValidator(self, validator):
        pass

    def sizeHint(self):
        return type("MockSize", (), {"width": lambda: 100})()

    def sizePolicy(self):
        return type(
            "MockSizePolicy",
            (),
            {"horizontalPolicy": lambda self: 0, "verticalPolicy": lambda self: 0},
        )()

    def text(self):
        return self._text

    def textFormat(self):
        return 1

    def title(self):
        return self._text

    def toolTip(self):
        return "Mock tooltip"

    def validator(self):
        return type("MockValidator", (), {"validate": lambda self, text, pos: (2, text, pos)})()

    def view(self):
        return None


# Specialized widget classes
class MockQPushButton(MockQtWidget):
    """Mock QPushButton with signal support."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._clicked_signal = type("MockSignal", (), {"connect": lambda self, x: None})()

    @property
    def clicked(self):
        return self._clicked_signal


class MockQComboBox(MockQtWidget):
    """Mock QComboBox with size adjustment policy."""

    def __init__(self, parent=None):
        super().__init__(parent)


class MockQMessageBox(MockQtWidget):
    """Mock QMessageBox with icon and button constants."""

    def __init__(self, parent=None):
        super().__init__(parent)


# Create QtWidgets module mock
mock_qt_widgets = MagicMock()
mock_qt_widgets.QWidget = MockQtWidget
mock_qt_widgets.QGroupBox = MockQtWidget
mock_qt_widgets.QLabel = MockQtWidget
mock_qt_widgets.QCheckBox = MockQtWidget
mock_qt_widgets.QSpinBox = MockQtWidget
mock_qt_widgets.QLineEdit = MockQtWidget
mock_qt_widgets.QPushButton = MockQPushButton
mock_qt_widgets.QComboBox = MockQComboBox
mock_qt_widgets.QMessageBox = MockQMessageBox

# Add constants to widget classes
setattr(MockQComboBox, "SizeAdjustPolicy", type("SizeAdjustPolicy", (), {"AdjustToContents": 0})())
setattr(MockQMessageBox, "Icon", type("Icon", (), {"Information": 1, "Question": 2})())
setattr(
    MockQMessageBox, "StandardButton", type("StandardButton", (), {"Ok": 1, "Yes": 2, "No": 4})()
)


# Mock layout classes
class MockLayout:
    """Mock Qt layout with common layout methods."""

    def __init__(self, *args, **kwargs):
        pass

    def addItem(self, item, *args, **kwargs):
        pass

    def addLayout(self, layout, *args, **kwargs):
        pass

    def addWidget(self, widget, *args, **kwargs):
        pass

    def columnCount(self):
        return 1

    def rowCount(self):
        return 1

    def setContentsMargins(self, *args):
        pass

    def setSpacing(self, spacing):
        pass


# Add layout classes and QApplication
mock_qt_widgets.QHBoxLayout = MockLayout
mock_qt_widgets.QVBoxLayout = MockLayout
mock_qt_widgets.QGridLayout = MockLayout
mock_qt_widgets.QApplication = MagicMock()
mock_qt_widgets.QApplication.instance.return_value = None

# Mock QtCore module
mock_qt_core = MagicMock()
mock_qt_core.Qt = MagicMock()
mock_qt_core.Qt.TextFormat = MagicMock()
mock_qt_core.Qt.TextFormat.RichText = 1
mock_qt_core.QSize = MagicMock()


# Mock QtGui module
class MockQFontMetrics:
    """Mock QFontMetrics for text measurement."""

    def __init__(self, font):
        pass

    def horizontalAdvance(self, text):
        return 100


class MockValidator:
    """Mock validator classes for input validation."""

    def __init__(self, *args, **kwargs):
        pass

    def setNotation(self, notation):
        pass

    def validate(self, text, pos):
        return (2, text, pos)  # QValidator.Acceptable

    class Notation:
        StandardNotation = 0


mock_qt_gui = MagicMock()
mock_qt_gui.QFontMetrics = MockQFontMetrics
mock_qt_gui.QDoubleValidator = MockValidator
mock_qt_gui.QIntValidator = MockValidator
mock_qt_gui.QRegularExpressionValidator = MockValidator

# Register PySide6 modules in sys.modules
sys.modules["PySide6"] = MagicMock()
sys.modules["PySide6.QtCore"] = mock_qt_core
sys.modules["PySide6.QtGui"] = mock_qt_gui
sys.modules["PySide6.QtWidgets"] = mock_qt_widgets


# Pytest fixtures
@pytest.fixture(scope="session")
def qapp():
    """Shared QApplication fixture for all Qt-based tests."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
