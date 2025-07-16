# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for VRED logging functionality and console output."""
import pytest
from unittest.mock import Mock, patch
import logging
from pathlib import Path
import tempfile

from vred_submitter.vred_logger import VREDConsoleHandler, VREDLogger, get_logger


class TestVREDConsoleHandler:
    """Test VREDConsoleHandler for routing log messages to VRED console."""

    @pytest.fixture
    def handler(self):
        return VREDConsoleHandler()

    @patch("vred_submitter.vred_logger.vrController")
    def test_emit_error_level(self, mock_vr_controller, handler):
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Test error message",
            args=(),
            exc_info=None,
        )
        handler.format = Mock(return_value="Formatted error message")

        handler.emit(record)

        mock_vr_controller.vrLogError.assert_called_once_with("Formatted error message")

    @patch("vred_submitter.vred_logger.vrController")
    def test_emit_warning_level(self, mock_vr_controller, handler):
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="Test warning message",
            args=(),
            exc_info=None,
        )
        handler.format = Mock(return_value="Formatted warning message")

        handler.emit(record)

        mock_vr_controller.vrLogWarning.assert_called_once_with("Formatted warning message")

    @patch("vred_submitter.vred_logger.vrController")
    def test_emit_info_level(self, mock_vr_controller, handler):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test info message",
            args=(),
            exc_info=None,
        )
        handler.format = Mock(return_value="Formatted info message")

        handler.emit(record)

        mock_vr_controller.vrLogInfo.assert_called_once_with("Formatted info message")


class TestVREDLogger:
    """Test VREDLogger for file and console logging setup."""

    @patch("vred_submitter.vred_logger.logging.handlers.RotatingFileHandler")
    @patch("vred_submitter.vred_logger.VREDConsoleHandler")
    def test_init(self, mock_console_handler, mock_file_handler):
        mock_console_handler_instance = Mock()
        mock_console_handler.return_value = mock_console_handler_instance
        mock_file_handler_instance = Mock()
        mock_file_handler.return_value = mock_file_handler_instance

        logger = VREDLogger("test_logger")

        assert logger.name == "test_logger"
        assert not logger.propagate
        mock_console_handler.assert_called_once()
        mock_file_handler.assert_called_once()

    @patch("vred_submitter.vred_logger.logging.handlers.RotatingFileHandler")
    @patch("vred_submitter.vred_logger.VREDConsoleHandler")
    def test_default_logging_level_not_debug(self, mock_console_handler, mock_file_handler):
        """Test that the default logging level is not DEBUG."""
        logger = VREDLogger("test_logger")
        # Verify the logger's level is not set to DEBUG
        assert logger.level != logging.DEBUG

        # Set the logger level explicitly to ensure debug messages aren't processed
        logger.setLevel(logging.INFO)

        # Verify that DEBUG messages won't be logged
        with patch.object(logger, "callHandlers") as mock_call_handlers:
            logger.debug("This is a debug message")
            mock_call_handlers.assert_not_called()

    @patch("vred_submitter.vred_logger.os.path.expanduser")
    @patch("vred_submitter.vred_logger.os.path.exists")
    @patch("vred_submitter.vred_logger.os.access")
    @patch("vred_submitter.vred_logger.VREDLogger._setup_file_handler")
    def test_get_log_file_path_default(
        self, mock_setup_file_handler, mock_access, mock_exists, mock_expanduser
    ):
        from pathlib import Path

        expected_path = str(Path.home() / ".deadline" / "logs" / "submitters" / "vred.log")
        mock_expanduser.return_value = expected_path
        mock_exists.return_value = True
        mock_access.return_value = True

        logger = VREDLogger("test")
        result = logger._get_log_file_path()

        assert result == expected_path

    @patch("vred_submitter.vred_logger.tempfile.gettempdir")
    @patch("vred_submitter.vred_logger.os.path.expanduser")
    @patch("vred_submitter.vred_logger.os.path.exists")
    @patch("vred_submitter.vred_logger.os.makedirs")
    @patch("vred_submitter.vred_logger.os.path.dirname")
    @patch("vred_submitter.vred_logger.VREDLogger._setup_file_handler")
    def test_get_log_file_path_create_directory_fails(
        self,
        mock_setup_file_handler,
        mock_dirname,
        mock_makedirs,
        mock_exists,
        mock_expanduser,
        mock_gettempdir,
    ):
        log_file_path = str(Path.home() / ".deadline" / "logs" / "submitters" / "vred.log")
        log_dir_path = str(Path.home() / ".deadline" / "logs" / "submitters")
        mock_expanduser.return_value = log_file_path
        mock_dirname.return_value = log_dir_path
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")
        temp_dir = Path(tempfile.gettempdir())
        mock_gettempdir.return_value = str(temp_dir)

        logger = VREDLogger("test")
        result = logger._get_log_file_path()

        expected = str(temp_dir / logger.ALTERNATIVE_LOGGING_FILENAME)
        assert result == expected

    @patch("vred_submitter.vred_logger.tempfile.gettempdir")
    @patch("vred_submitter.vred_logger.os.path.expanduser")
    @patch("vred_submitter.vred_logger.os.path.exists")
    @patch("vred_submitter.vred_logger.os.access")
    @patch("vred_submitter.vred_logger.os.path.dirname")
    @patch("vred_submitter.vred_logger.VREDLogger._setup_file_handler")
    def test_get_log_file_path_no_write_access(
        self,
        mock_setup_file_handler,
        mock_dirname,
        mock_access,
        mock_exists,
        mock_expanduser,
        mock_gettempdir,
    ):
        log_file_path = str(Path.home() / ".deadline" / "logs" / "submitters" / "vred.log")
        log_dir_path = str(Path.home() / ".deadline" / "logs" / "submitters")
        mock_expanduser.return_value = log_file_path
        mock_dirname.return_value = log_dir_path
        mock_exists.return_value = True
        mock_access.return_value = False
        temp_dir = Path(tempfile.gettempdir())
        mock_gettempdir.return_value = str(temp_dir)

        logger = VREDLogger("test")
        result = logger._get_log_file_path()

        expected = str(temp_dir / logger.ALTERNATIVE_LOGGING_FILENAME)
        assert result == expected


class TestGetLogger:
    """Test get_logger function for creating VRED loggers."""

    @patch("vred_submitter.vred_logger.logging.getLogger")
    @patch("vred_submitter.vred_logger.logging.setLoggerClass")
    @patch("vred_submitter.vred_logger.logging.getLoggerClass")
    def test_get_logger(self, mock_get_logger_class, mock_set_logger_class, mock_get_logger):
        mock_original_class = Mock()
        mock_get_logger_class.return_value = mock_original_class
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        result = get_logger("test_logger")

        # Should set VREDLogger class, get logger, then restore original class
        assert mock_set_logger_class.call_count == 2
        mock_set_logger_class.assert_any_call(VREDLogger)
        mock_set_logger_class.assert_any_call(mock_original_class)
        mock_get_logger.assert_called_once_with("test_logger")
        assert result == mock_logger_instance
