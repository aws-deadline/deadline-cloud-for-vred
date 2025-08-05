# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Independent bootstrapping logic for initializing the VRED (in-app) Submitter (includes
Deadline Cloud menu bar and its related dependencies.)
Note: the VRED (in-app) Submitter is only supported on Windows.

The following steps are required for successful installation of this script in VRED:
1) Open VRED Preferences (Edit menu -> Preferences)
2) In Preferences window's General Settings left section, choose Script:
3) Scroll to bottom of the Script right-hand section.
4) Add this code to bottom of the code in the Script section:
    from DeadlineCloudForVRED import DeadlineCloudForVRED
    DeadlineCloudForVRED()
5) In the Python Sandbox right-hand section, ensure that Python Sandbox is disabled
6) Save preferences (bottom right button) in Preferences window.
"""

import errno
import os
import sys
import traceback

from vrController import vrLogError

# It's recommended to maintain these variables (below) - to be in sync with convention changes
#
ERROR_MSG_CLIENT_MISSING = (
    "Please ensure that Deadline Cloud for VRED "
    "is fully installed and that its directory is present in the system DEADLINE_VRED_MODULES "
    "environment variable. Typical installation directories are:\n"
    "   %USERPROFILE%\\DeadlineCloudSubmitter\\Submitters\\VRED\\\n"
    "   %USERPROFILE%\\DeadlineCloudForVREDSubmitter\\n"
)

ERROR_MSG_LOAD_CLIENT = "Encountered an error while loading the Deadline Cloud Client"
ERROR_MSG_LOAD_SUBMITTER = "Encountered an error while loading the Deadline Cloud Submitter"
ERROR_MSG_MENU_INIT = "An error occurred when attempting to add Deadline menu."
ERROR_MSG_SCRIPT_NOT_FOUND = (
    "The vred_submitter.py script could not be found. "
    "Please ensure that Deadline Cloud for VRED has been fully installed on this machine. "
    "Typical directory locations for vred_submitter.py are:\n"
    "   %USERPROFILE%\\DeadlineCloudSubmitter\\Submitters\\VRED\\scripts\n"
    "   %USERPROFILE%\\DeadlineCloudForVREDSubmitter\\scripts\n"
)
SUBMITTER_BASE_FOLDER_ENV_VAR = "DEADLINE_VRED_MODULES"
SUBMITTER_PYTHON_MODULES_SUB_PATH = "python/modules"
SUBMITTER_PYTHON_SCRIPTS_SUB_PATH = "scripts"


class DeadlineCloudForVRED:
    """Provides logic for initializing the Deadline Cloud menu bar and its related dependencies."""

    def __init__(self):
        """
        Initialize the Deadline Cloud for VRED Submitter.
        """

        # An assumption is made that the Deadline Cloud Client installation path is the first
        # directory in the system PATH environment variable, which contains SUBMITTER_BASE_FOLDER_NAME
        # Note: stricter matching criteria can be applied in the future (including separate environment
        # variables, binaries within, especially if naming conventions change.)
        #
        self.base_dc_installation_path = os.environ.get(SUBMITTER_BASE_FOLDER_ENV_VAR, "")
        self.initialize_deadline_cloud_submitter()

    def initialize_deadline_cloud_submitter(self) -> bool:
        """
        Initialize the Deadline Cloud Submitter.
        raises:
            FileNotFoundError: If required paths or directories are not found.
            ImportError: If required modules cannot be imported.
            Exception: For other initialization failures.
        return: True if initialization succeeds, False otherwise.
        """
        if self._setup_deadline_cloud_client_modules() and self._setup_vred_scripts():
            return self._initialize_deadline_cloud_menu()
        return False

    def _setup_deadline_cloud_client_modules(self) -> bool:
        """
        Set up Deadline Cloud Client Python modules to be in Python search path, validate.
        raises:
            FileNotFoundError: If modules path doesn't exist.
            ImportError: If required modules cannot be imported.
        return: True if setup succeeds, False otherwise.
        """
        try:
            import deadline.client  # noqa: F401

            return True
        except ModuleNotFoundError:
            # We weren't able to find it in our site packages, so we'll check the env var
            pass

        try:
            modules_path = os.path.join(
                self.base_dc_installation_path, SUBMITTER_PYTHON_MODULES_SUB_PATH
            )
            modules_path = os.path.realpath(modules_path).replace("\\", "/")
            if not os.path.isdir(modules_path):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), modules_path)
            if modules_path not in sys.path:
                sys.path.append(modules_path)

            import deadline.client  # noqa: F401

            return True
        except FileNotFoundError:
            vrLogError(ERROR_MSG_CLIENT_MISSING)
        except Exception as e:
            vrLogError(f"{ERROR_MSG_LOAD_CLIENT}: {str(e)}")
            vrLogError(traceback.format_exc())
        return False

    def _setup_vred_scripts(self) -> bool:
        """
        Set up VRED-specific Python scripts to be in Python search path, validate.
        raises:
            FileNotFoundError: If scripts path doesn't exist.
            ImportError: If required modules cannot be imported.
        returns: True if setup succeeds, False otherwise.
        """
        try:
            import deadline.vred_submitter  # noqa: F401

            return True
        except ModuleNotFoundError:
            # We weren't able to find it in our site packages, so we'll check the env var
            pass

        try:
            # Determine the VRED-specific Python Scripts folder within Deadline Cloud
            #
            scripts_path = os.path.join(
                self.base_dc_installation_path, SUBMITTER_PYTHON_SCRIPTS_SUB_PATH
            )
            scripts_path = os.path.realpath(scripts_path).replace("\\", "/")
            if not os.path.isdir(scripts_path):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), scripts_path)
            if scripts_path not in sys.path:
                sys.path.append(scripts_path)
            import deadline.vred_submitter  # noqa: F401

            return True
        except FileNotFoundError:
            vrLogError(ERROR_MSG_SCRIPT_NOT_FOUND)
        except Exception as e:
            vrLogError(f"{ERROR_MSG_LOAD_SUBMITTER}: {str(e)}")
            vrLogError(traceback.format_exc())
        return False

    def _initialize_deadline_cloud_menu(self) -> bool:
        """
        Initialize the Deadline menu in the VRED interface.
        returns: True if initialization succeeds, False otherwise.
        """
        try:
            from deadline.vred_submitter import vred_submitter_wrapper  # type: ignore

            vred_submitter_wrapper.add_deadline_cloud_menu()
            return True
        except Exception as e:
            vrLogError(f"{ERROR_MSG_MENU_INIT}: {str(e)}")
            vrLogError(traceback.format_exc())
            return False
