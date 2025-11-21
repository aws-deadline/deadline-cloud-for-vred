# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Local end-to-end tests for VRED Deadline Cloud integration.

Tests complete workflow: submitter UI -> job bundle validation -> rendering -> output validation.
Note: These are local tests that do not submit to the cloud render farm.
"""

import logging
import pytest
import shutil
import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from deadline.vred_submitter.constants import Constants as SubmitterConstants

from test.integ.helpers.constants import Constants as TestConstants
from test.integ.helpers.job_bundle_output_comparison import assert_job_bundle_matches
from test.integ.helpers.output_comparison import are_images_similar_by_folder
from test.integ.helpers.sticky_settings_verification import verify_sticky_settings_file
from test.integ.helpers.vred_runner import VREDRunner
from test.integ.path_resolver import PathResolver

logging.basicConfig(format="%(message)s", level=logging.INFO)

OUTPUT_DIRECTORY_NAME = "output"


@pytest.fixture(scope="module", autouse=True)
def setup_and_cleanup_local_e2e_output():
    """
    Module-scoped fixture to clean up output directory before and after running the tests.
    """
    output_dir = Path(__file__).parent / OUTPUT_DIRECTORY_NAME

    try:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(exist_ok=True)
    except (OSError, PermissionError) as e:
        logging.warning("Could not clean local-e2e test output directory: %s", e)

    yield

    try:
        if output_dir.exists():
            shutil.rmtree(output_dir)
    except (OSError, PermissionError) as e:
        logging.warning("Could not clean local-e2e test output directory: %s", e)


class LocalE2ETestRunner:
    """
    Class to run local end-to-end tests for VRED Deadline Cloud integration
    """

    def __init__(self):
        self.vred_runner = VREDRunner()
        self.path_resolver = PathResolver()

    def run_local_e2e_test(
        self, test_name: str, scene_filename: str, test_settings: list
    ) -> tuple[Path, Path, Path, Path]:
        """
        Run a local end-to-end test which does following:
          1. Launch VRED with submitter dialog to generate a job bundle
          2. Launch VRED to render an image from the job bundle

        param: test_name (str): The name/ID of the test
        param: scene_filename (str): The name of the scene file
        param: test_settings (list): The test settings
        return: A tuple containing the paths to actual outout directory, expected output directory,
            job bundle directory, and sticky settings file
        """
        scene_file_path = self.path_resolver.get_scene_file(scene_filename)
        if not scene_file_path or not scene_file_path.exists():
            raise FileNotFoundError(f"Scene file '{scene_filename}' does not exist")

        scene_basename = scene_file_path.stem
        bundle_path = (
            self.path_resolver.get_output_folder_for_test(test_name, scene_basename) / "bundle"
        )
        render_output_dir = (
            self.path_resolver.get_output_folder_for_test(test_name, scene_basename) / "render"
        )

        bundle_path.mkdir(parents=True, exist_ok=True)
        render_output_dir.mkdir(parents=True, exist_ok=True)

        logging.info("Test: %s", test_name)
        logging.info("Scene: %s.vpb", scene_basename)
        logging.info("Bundle: %s", bundle_path)
        logging.info("Output: %s", render_output_dir)

        # Clean up sticky settings file before test (if exists)
        sticky_settings_file = scene_file_path.with_suffix(
            SubmitterConstants.RENDER_SUBMITTER_SETTINGS_FILE_EXT
        )
        if sticky_settings_file.exists():
            sticky_settings_file.unlink()
            logging.info("Removed existing sticky settings file")
        assert (
            not sticky_settings_file.exists()
        ), f"Sticky settings file should not exist yet: {sticky_settings_file}"

        self.vred_runner.setup_environment()

        # Phase 1: Submitter - Generate job bundle (requires VRED Pro)
        logging.info("\n[Phase 1] Running submitter to generate job bundle...")
        if not self.vred_runner.invoke_vred_submitter(scene_file_path, test_settings, bundle_path):
            raise RuntimeError("Submitter phase failed")

        # Verify job bundle was created
        bundle_template = bundle_path / TestConstants.TEMPLATE_FILENAME
        bundle_params = bundle_path / TestConstants.PARAMETER_VALUES_FILENAME
        if not bundle_template.exists() or not bundle_params.exists():
            raise RuntimeError(f"Job bundle not created at {bundle_path}")
        logging.info("Job bundle created successfully")

        # Quick validation on template YAML
        self._validate_template(bundle_template)

        # Quick validation to check if sticky settings file was created
        assert (
            sticky_settings_file.exists()
        ), f"Sticky settings file should exist in: {sticky_settings_file}"

        # Phase 2: Worker - Render from job bundle
        logging.info("\n[Phase 2] Running worker to render from job bundle...")
        if not self.vred_runner.invoke_vred_render(
            self.path_resolver.base_path, scene_file_path, bundle_path, render_output_dir
        ):
            raise RuntimeError("Render phase failed")
        logging.info("Rendering completed")

        expected_output_folder = self.path_resolver.get_expected_render_folder(
            test_name, scene_basename
        )
        return render_output_dir, expected_output_folder, bundle_path, sticky_settings_file

    def _validate_template(self, template_path: Path) -> None:
        """Validate that template.yaml is valid YAML"""
        try:
            with open(template_path, encoding="utf-8") as f:
                yaml.safe_load(f)
            logging.info("✅ Template YAML is valid")
        except Exception as e:
            raise RuntimeError(f"Invalid template YAML: {e}") from e

    def validate_submitter_outputs(
        self,
        test_name: str,
        scene_basename: str,
        bundle_path: Path,
        sticky_settings_file: Path,
        test_settings: list,
    ) -> None:
        """Validate all submitter outputs: job bundle and sticky settings"""
        logging.info("\n[Validation] Checking submitter outputs...")

        # Validate job bundle against expected output (if exists)
        expected_bundle_dir = self.path_resolver.get_expected_bundle_folder(
            test_name, scene_basename
        )
        if expected_bundle_dir.exists():
            comparison_context = {"test_name": test_name}
            assert_job_bundle_matches(bundle_path, expected_bundle_dir, comparison_context)
            logging.info("✅ Job bundle matches expected output")

        # Verify sticky settings
        parameter_overrides = {item["name"]: item["value"] for item in test_settings}
        verify_sticky_settings_file(sticky_settings_file, parameter_overrides)
        logging.info("✅ Sticky settings verified")

    def validate_render_outputs(self, render_output_dir: Path, expected_output_dir: Path) -> None:
        """Validate render outputs against expected images"""
        logging.info("\n[Validation] Checking render outputs...")

        assert (
            expected_output_dir.exists()
        ), f"Expected output folder not found: {expected_output_dir}"

        image_singularity_factor = 10.0
        result = are_images_similar_by_folder(
            expected_output_dir, render_output_dir, image_singularity_factor
        )
        assert result, "Image comparison failed"
        logging.info("✅ Rendered images match expected output")


@pytest.mark.local_e2e
class TestVREDLocalE2E:
    """Local end-to-end test suite for VRED Deadline Cloud integration"""

    def test_local_e2e_gpu_raytracing(self):
        """Test complete local workflow with GPU raytracing enabled"""
        runner = LocalE2ETestRunner()
        test_settings = [
            {"name": "output_directories", "value": ["c:\\vred-snapshots"]},
            {"name": "OutputDir", "value": "c:\\vred-snapshots"},
            {"name": "OutputFileNamePrefix", "value": "gpu_test"},
            {"name": "StartFrame", "value": 0},
            {"name": "EndFrame", "value": 5},
            {"name": "OutputFormat", "value": "PNG"},
            {"name": "RenderAnimation", "value": "false"},
            {"name": "GPURaytracing", "value": "true"},
            {"name": "View", "value": "Perspective"},
        ]

        render_output, expected_render_output, bundle_path, sticky_settings_file = (
            runner.run_local_e2e_test("gpu_raytracing", "Cone.vpb", test_settings)
        )

        runner.validate_submitter_outputs(
            "gpu_raytracing", "Cone", bundle_path, sticky_settings_file, test_settings
        )
        runner.validate_render_outputs(render_output, expected_render_output)
