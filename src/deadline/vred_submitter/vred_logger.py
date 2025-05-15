# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Implements a basic global logger for the VRED submitter, proving console and file-based logging capabilities.
"""
import logging
import logging.handlers
import os
import tempfile

import vrController


class VREDConsoleHandler(logging.Handler):
    """Handles logging output to VRED's console with appropriate formatting."""

    def emit(self, record: logging.LogRecord) -> None:
        """
        Directs a given record to VRED's console based on log level.
        :param record: the log record to be emitted
        :return: None
        """
        msg = self.format(record)
        if record.levelno >= logging.ERROR:
            vrController.vrLogError(msg)
        elif record.levelno == logging.WARNING:
            vrController.vrLogWarning(msg)
        elif record.levelno <= logging.INFO:
            vrController.vrLogInfo(msg)


class VREDLogger(logging.Logger):
    """Custom logger providing both console and file-based logging capabilities."""

    ALTERNATIVE_LOGGING_FILENAME = f"rfm.{os.getpid()}.log"
    CONSOLE_LOG_FORMAT = (
        "[%(name)s] %(levelname)8s:  (%(threadName)-10s)" "  %(module)s %(funcName)s: %(message)s"
    )
    DISK_LOG_FORMAT = (
        "%(asctime)s %(levelname)8s {%(threadName)-10s}" ":  %(module)s %(funcName)s: %(message)s"
    )
    DEFAULT_LOGFILE_LOCATION = "~/.deadline/logs/submitters/vred.log"
    LOGFILE_BACKUP_COUNT = 5
    MAX_LOGFILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self, name: str):
        """
        Initialize the logger with console and file handlers.
        :param name: Name of the logger
        """
        super().__init__(name)
        self._setup_console_handler()
        self._setup_file_handler()
        self.propagate = False

    def _setup_console_handler(self) -> None:
        """
        Configures and adds console handler to the logger.
        :return: None
        """
        console_handler = VREDConsoleHandler()
        console_handler.setFormatter(logging.Formatter(self.CONSOLE_LOG_FORMAT))
        self.addHandler(console_handler)

    def _setup_file_handler(self) -> None:
        """
        Configures and adds file handler to the logger.
        :return: None
        """
        log_file = self._get_log_file_path()
        disk_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=self.MAX_LOGFILE_SIZE, backupCount=self.LOGFILE_BACKUP_COUNT
        )
        disk_handler.setFormatter(logging.Formatter(self.DISK_LOG_FORMAT))
        self.addHandler(disk_handler)

    def _get_log_file_path(self) -> str:
        """
        Determine the appropriate log file path. If the default path lacks sufficient
        permission, then attempt to use an alternative temporary path.
        :return: path to the log file
        """
        log_file = os.path.expanduser(self.DEFAULT_LOGFILE_LOCATION)
        if not os.path.exists(os.path.dirname(log_file)):
            try:
                os.makedirs(os.path.dirname(log_file))
            except (IOError, OSError):
                return os.path.join(tempfile.gettempdir(), self.ALTERNATIVE_LOGGING_FILENAME)
        if not os.access(os.path.dirname(log_file), os.W_OK | os.R_OK):
            return os.path.join(tempfile.gettempdir(), self.ALTERNATIVE_LOGGING_FILENAME)
        return log_file


def get_logger(name: str) -> logging.Logger:
    """
    High-level method for creating and returning a logger instance with the specified name.
    :param name: name for the logger
    :return: configured logger instance
    """
    logging_class = logging.getLoggerClass()
    logging.setLoggerClass(VREDLogger)
    logger = logging.getLogger(name)
    logging.setLoggerClass(logging_class)
    return logger
