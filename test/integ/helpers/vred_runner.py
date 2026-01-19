# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Common VRED execution utilities"""

import logging
import os
import subprocess
from pathlib import Path

from .constants import Constants


class VREDRunner:
    """Base class for VRED execution operations for tesing"""

    def __init__(self):
        self.current_module_path = Path(__file__).resolve().parent.parent
        self.submitter_path = (
            self.current_module_path.parent.parent / Constants.VRED_SUBMITTER_SOURCE_PATH
        )

    def get_submitter_bootstrap_code(self, test_settings: list, bundle_output_path: str) -> str:
        """
        Generate bootstrap code for submitter dialog testing (job bundle creation)
        param: test_settings: List of setting dictionaries having 'name' and 'value' keys
        param: bundle_output_path: Path where job bundle should be exported
        return: generated bootstrap code for submitter dialog interaction
        """
        return rf"""
import importlib;
import sys;
from vrController import terminateVred;
sys.path.extend([r'{self.current_module_path}/helpers']);
controller = importlib.import_module('submitter_dialog_controller');
controller.run_submitter_test({test_settings}, r'{bundle_output_path}');
terminateVred();
""".replace("\n", "").replace("\\", "/")

    def get_render_bootstrap_code(
        self,
        base_dir: Path,
        bundle_path: str,
        scene_file_path: str,
        render_output_dir: str,
    ) -> str:
        """
        Generate bootstrap code for worker testing (rendering from job bundle)
        param: base_dir: absolute path to the directory where tests are located (e.g., test/worker, test/e2e)
        param: bundle_path: Absolute Path where job bundle should be exported
        param: scene_file_path: Absolute Path to the scene file
        param: render_output_dir: Aboluste Path where rendered image should be generated
        return:  generated bootstrap code for render execution
        """
        return rf"""
import importlib;
import sys;
from vrController import terminateVred, vrLogError;
sys.path.extend([r'{self.current_module_path}/helpers',
                 '{self.submitter_path}']);
render_params = importlib.import_module('load_render_parameter_values');
render_script = importlib.import_module('VRED_RenderScript_DeadlineCloud');
params = render_params.get_vred_render_parameters_from_bundle('{base_dir}','{bundle_path}','{scene_file_path}','{render_output_dir}');
render_script.deadline_cloud_render(params) if render_script and render_params else vrLogError('failed to import modules');
terminateVred();
""".replace("\n", "").replace("\\", "/")

    def get_vred_executable(self, require_pro: bool = False) -> str:
        """
        Get the path to the VRED executable based on environment variables
        param: require_pro: Flag to indicate if VRED Pro is required
        return: Path to the VRED executable
        """
        if require_pro:
            if executable := os.environ.get(Constants.VRED_PRO_ENV_VAR):
                if os.path.isfile(executable):
                    return executable
            raise OSError("VRED Pro required but not found in VREDPRO environment variable")

        for env_var in [Constants.VRED_CORE_ENV_VAR, Constants.VRED_PRO_ENV_VAR]:
            if executable := os.environ.get(env_var):
                if os.path.isfile(executable):
                    return executable
        raise OSError("Cannot determine valid VRED binary from environment variables")

    def setup_environment(self) -> None:
        """Set up environment variables required for VRED execution"""
        os.environ.update(
            {
                Constants.DISABLE_WEBINTERFACE_ENV_VAR: Constants.DISABLE_WEBINTERFACE_VALUE,
                Constants.LICENSE_RELEASE_TIME_ENV_VAR: Constants.LICENSE_RELEASE_TIME_SECONDS_LIMIT,
                Constants.FLEXLM_DIAGNOSTICS_ENV_VAR: Constants.FLEXLM_DIAGNOSTICS_HIGH_VALUE,
            }
        )

    def invoke_vred(self, bootstrap_code: str, scene_file: str, require_pro: bool = False) -> bool:
        """
        Invoke VRED with the given bootstrap code and scene file
        param: bootstrap_code: Bootstrap code to be executed
        param: scene_file: Absolute Path to the scene file
        param: require_pro: Flag to indicate if VRED Pro is required
        return: True if VRED execution was successful, False otherwise
        """
        os.environ[Constants.CODE_PASSING_ENV_VAR] = bootstrap_code
        executable = self.get_vred_executable(require_pro)

        if Constants.IS_WINDOWS:
            executable = f'"{executable}"'
            scene_file = f'"{scene_file}"'

        cmd = [
            executable,
            scene_file,
            Constants.DISABLE_PYTHON_SANDBOX_PARAM,
            Constants.FAST_START_PARAM,
            Constants.POST_PYTHON_PARAM,
            Constants.VRED_PYTHON_PRE_BOOTSTRAP_CODE,
        ]

        try:
            invocation = " ".join(cmd) if Constants.IS_WINDOWS else cmd
            result = subprocess.run(invocation, stderr=subprocess.STDOUT, check=True, text=True)
            logging.debug(result)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {invocation}\n{e.output}\nReturn code: {e.returncode}")
            return False

    def invoke_vred_submitter(self, scene_file_path: Path, test_settings: list, bundle_path: Path):
        """
        Invoke VRED submitter with the given scene file and test settings
        param: scene_file_path: Absolute Path to the scene file
        param: test_settings: List of setting dictionaries having 'name' and 'value' keys
        param: bundle_path: Absolute Path where job bundle should be exported
        return: True if VRED execution was successful, False otherwise
        """
        submitter_bootstrap = self.get_submitter_bootstrap_code(test_settings, str(bundle_path))
        return self.invoke_vred(submitter_bootstrap, str(scene_file_path), require_pro=True)

    def invoke_vred_render(
        self, base_dir: Path, scene_file_path: Path, bundle_path: Path, render_output_dir: Path
    ):
        """
        Invoke VRED render with the given scene file and job bundle
        param: base_dir: absolute path to the directory where tests are located (e.g., test/worker, test/e2e)
        param: scene_file_path: Absolute Path to the scene file
        param: bundle_path: Absolute Path where job bundle should be exported
        param: render_output_dir: Aboluste Path where rendered image should be generated
        return: True if VRED execution was successful, False otherwise
        """
        render_bootstrap = self.get_render_bootstrap_code(
            base_dir,
            str(bundle_path),
            str(scene_file_path),
            str(render_output_dir),
        )
        return self.invoke_vred(render_bootstrap, str(scene_file_path), require_pro=False)
