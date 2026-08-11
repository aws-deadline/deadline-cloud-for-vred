# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import base64
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

# Skip this entire test module on non-Windows platforms
pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="Tests for VRED Pro submitter installer - VRED Pro only runs on Windows.",
)

# Add project's "scripts" directory to path for importing install_submitter
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Conditional import to avoid RuntimeError on non-Windows
if sys.platform == "win32":
    try:
        from install_submitter import SubmitterFiles, VREDSubmitterInstaller
    except ImportError as e:
        raise ImportError(f"Cannot import install_submitter from {scripts_dir}: {e}") from e
else:
    if TYPE_CHECKING:
        from install_submitter import SubmitterFiles, VREDSubmitterInstaller
    else:
        SubmitterFiles = None  # type: ignore
        VREDSubmitterInstaller = None  # type: ignore


class TestVREDSubmitterInstaller:
    """Test cases for VREDSubmitterInstaller class."""

    @pytest.fixture
    def installer(self):
        """Create a VREDSubmitterInstaller instance for testing."""
        with patch("builtins.print"):  # Suppress print output during tests
            return VREDSubmitterInstaller()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @patch("platform.system")
    def test_get_default_install_directory_windows(self, mock_system):
        """Test default install directory on Windows."""
        mock_system.return_value = "Windows"
        with patch("builtins.print"):
            installer = VREDSubmitterInstaller()

        expected = Path.home() / "DeadlineCloudSubmitter/Submitters/VRED"
        assert installer.get_default_install_directory() == expected

    @patch("platform.system")
    def test_init_non_windows_raises_error(self, mock_system):
        """Test that VREDSubmitterInstaller raises error on non-Windows."""
        mock_system.return_value = "Linux"
        with pytest.raises(RuntimeError, match="VRED Pro is only supported on Windows"):
            VREDSubmitterInstaller()

    def test_get_submitter_files_empty(self, installer, temp_dir):
        """Test get_submitter_files with no files present."""
        installer.package_root = temp_dir

        # Mock build_deps_bundle to avoid pyproject.toml dependency
        with patch("install_submitter.build_deps_bundle"):
            files = installer.get_submitter_files()

        assert len(files.plugin) == 0
        assert len(files.scripts) == 0
        assert len(files.dependency_bundle) == 0

    def test_get_submitter_files_with_files(self, installer, temp_dir):
        """Test get_submitter_files with files present."""
        installer.package_root = temp_dir

        # Create test directories and files
        plugin_dir = temp_dir / "vred_submitter_plugin" / "plug-ins"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "test_plugin.py").touch()

        scripts_dir = temp_dir / "src" / "deadline" / "vred_submitter"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "test_script.py").touch()

        bundle_dir = temp_dir / "dependency_bundle"
        bundle_dir.mkdir()
        (bundle_dir / "test_bundle.zip").touch()

        files = installer.get_submitter_files()

        assert len(files.plugin) == 1
        assert len(files.scripts) == 1
        assert len(files.dependency_bundle) == 1

    def test_create_directory_structure(self, installer, temp_dir):
        """Test directory structure creation."""
        install_dir = temp_dir / "install"

        directories = installer.create_directory_structure(install_dir)

        assert "base" in directories
        assert "python_modules" in directories
        assert "scripts" in directories
        assert "plugin" in directories

        # Check all directories were created
        for dir_path in directories.values():
            assert dir_path.exists()
            assert dir_path.is_dir()

    def test_copy_files_success(self, installer, temp_dir):
        """Test successful file copying."""
        installer.package_root = temp_dir / "package"
        installer.package_root.mkdir()

        # Create source files
        plugin_file = temp_dir / "test_plugin.py"
        plugin_file.write_text("# Test plugin")

        script_base = installer.package_root / "src"
        script_file = script_base / "deadline" / "vred_submitter" / "test_script.py"
        script_file.parent.mkdir(parents=True)
        script_file.write_text("# Test script")

        # Create destination directories
        install_dir = temp_dir / "install"
        directories = installer.create_directory_structure(install_dir)

        files = SubmitterFiles(plugin=[plugin_file], scripts=[script_file], dependency_bundle=[])

        installer.copy_files(files, directories)

        assert (directories["plugin"] / "test_plugin.py").exists()
        assert (directories["scripts"] / "deadline" / "vred_submitter" / "test_script.py").exists()

    def test_copy_files_failure(self, installer, temp_dir):
        """Test file copying failure."""
        directories = {"plugin": temp_dir / "nonexistent"}
        files = SubmitterFiles(
            plugin=[Path("/nonexistent/file.py")], scripts=[], dependency_bundle=[]
        )

        with pytest.raises(RuntimeError, match="Failed to copy files"):
            installer.copy_files(files, directories)

    def test_install_dependency_bundle(self, installer, temp_dir):
        """Test dependency bundle installation."""
        # Create a test zip file
        zip_file = temp_dir / "test_bundle.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("test_module.py", "# Test module")

        directories = {"python_modules": temp_dir / "modules"}
        directories["python_modules"].mkdir()

        installer._install_dependency_bundle([zip_file], directories)

        assert (directories["python_modules"] / "test_module.py").exists()

    def test_install_dependency_bundle_bad_zip(self, installer, temp_dir):
        """Test dependency bundle installation with bad zip file."""
        # Create a bad zip file
        bad_zip = temp_dir / "bad.zip"
        bad_zip.write_text("not a zip file")

        directories = {"python_modules": temp_dir / "modules"}
        directories["python_modules"].mkdir()

        with pytest.raises((zipfile.BadZipFile, OSError)):
            installer._install_dependency_bundle([bad_zip], directories)

    @patch("install_submitter.winreg", create=True)
    def test_set_environment_variable_windows(self, mock_winreg, installer, temp_dir):
        """Test environment variable setting on Windows."""
        # Mock winreg operations
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_winreg.KEY_SET_VALUE = "KEY_SET_VALUE"
        mock_winreg.REG_SZ = "REG_SZ"

        with patch.object(installer, "_notify_environment_change"):
            installer.set_deadline_vred_modules_env_var(temp_dir)

        mock_winreg.SetValueEx.assert_called_once()
        mock_winreg.CloseKey.assert_called_once_with(mock_key)

    def test_install_plugin_to_vred_versions_no_plugin(self, installer, temp_dir):
        """Test plugin installation when plugin file doesn't exist."""
        with pytest.raises(RuntimeError, match="Plugin file not found"):
            installer.install_plugin_to_vred_versions(temp_dir)

    def test_install_plugin_to_vred_versions_success(self, installer, temp_dir):
        """Test successful plugin installation."""
        # Create plugin file
        plugin_dir = temp_dir / "plug-ins"
        plugin_dir.mkdir()
        plugin_file = plugin_dir / "DeadlineCloudForVRED.py"
        plugin_file.write_text("# Test plugin")

        # Mock VRED installation paths
        vred_path = temp_dir / "vred"
        site_packages = vred_path / "lib" / "python" / "Lib" / "site-packages"
        site_packages.mkdir(parents=True)

        with patch.object(installer, "_get_vred_installation_paths") as mock_paths:
            mock_paths.return_value = {"VRED Test": vred_path}
            installer.install_plugin_to_vred_versions(temp_dir)

        assert (site_packages / "DeadlineCloudForVRED.py").exists()

    def test_get_vred_installation_paths_multiple_versions(self, installer, temp_dir):
        """Test VRED installation paths selection with multiple versions."""
        # Create mock Autodesk directory structure
        autodesk_dir = temp_dir / "Autodesk"
        autodesk_dir.mkdir()

        # Create multiple VRED Pro 2025 versions (17.x)
        (autodesk_dir / "VREDPro-17.1").mkdir()
        (autodesk_dir / "VREDPro-17.3").mkdir()
        (autodesk_dir / "VREDPro-17.2").mkdir()

        # Create multiple VRED Pro 2026 versions (18.x)
        (autodesk_dir / "VREDPro-18.0").mkdir()
        (autodesk_dir / "VREDPro-18.1").mkdir()

        # Create some non-VRED directories that should be ignored
        (autodesk_dir / "Maya2024").mkdir()
        (autodesk_dir / "VREDPro-16.5").mkdir()  # Older version

        # Patch the hardcoded Autodesk path to use our temp directory
        with patch("install_submitter.Path") as mock_path_class:
            mock_path_class.side_effect = lambda x: (
                autodesk_dir if "Autodesk" in str(x) else Path(x)
            )

            paths = installer._get_vred_installation_paths()

        # Should select the highest version for each major version
        assert "VRED Pro 2025" in paths
        assert "VRED Pro 2026" in paths
        assert paths["VRED Pro 2025"].name == "VREDPro-17.3"  # Highest 17.x version
        assert paths["VRED Pro 2026"].name == "VREDPro-18.1"  # Highest 18.x version

    def test_get_vred_installation_paths_no_autodesk_dir(self, installer, temp_dir):
        """Test VRED installation paths when Autodesk directory doesn't exist."""
        nonexistent_dir = temp_dir / "NotExist"

        with patch("install_submitter.Path") as mock_path_class:
            mock_path_class.side_effect = lambda x: (
                nonexistent_dir if "Autodesk" in str(x) else Path(x)
            )

            with pytest.raises(RuntimeError, match="Autodesk directory not found: "):
                installer._get_vred_installation_paths()

    def test_get_vred_installation_paths_partial_versions(self, installer, temp_dir):
        """Test VRED installation paths when only some versions are available."""
        autodesk_dir = temp_dir / "Autodesk"
        autodesk_dir.mkdir()

        # Only create VRED Pro 2026 versions
        (autodesk_dir / "VREDPro-18.0").mkdir()
        (autodesk_dir / "VREDPro-18.2").mkdir()
        (autodesk_dir / "VREDPro-18").mkdir()  # The directory name is in invalid format

        with patch("install_submitter.Path") as mock_path_class:
            mock_path_class.side_effect = lambda x: (
                autodesk_dir if "Autodesk" in str(x) else Path(x)
            )

            paths = installer._get_vred_installation_paths()

        assert "VRED Pro 2025" not in paths
        assert "VRED Pro 2026" in paths
        assert paths["VRED Pro 2026"].name == "VREDPro-18.2"

    def test_install_plugin_no_vred_versions(self, installer, temp_dir):
        """Test plugin installation when no VRED versions are found."""
        # Create plugin file
        plugin_dir = temp_dir / "plug-ins"
        plugin_dir.mkdir()
        plugin_file = plugin_dir / "DeadlineCloudForVRED.py"
        plugin_file.write_text("# Test plugin")

        with patch.object(installer, "_get_vred_installation_paths") as mock_paths:
            mock_paths.return_value = {}  # No VRED versions found

            with pytest.raises(RuntimeError, match="Plugin installation failed"):
                installer.install_plugin_to_vred_versions(temp_dir)

    def test_get_vred_installation_paths_version_sorting(self, installer, temp_dir):
        """Test that version sorting works correctly with numeric comparison."""
        autodesk_dir = temp_dir / "Autodesk"
        autodesk_dir.mkdir()

        # Create versions in non-alphabetical order to test numeric sorting
        (autodesk_dir / "VREDPro-17.10").mkdir()  # Should be highest numerically
        (autodesk_dir / "VREDPro-17.2").mkdir()
        (autodesk_dir / "VREDPro-17.9").mkdir()  # This is highest alphabetically

        with patch("install_submitter.Path") as mock_path_class:
            mock_path_class.side_effect = lambda x: (
                autodesk_dir if "Autodesk" in str(x) else Path(x)
            )

            paths = installer._get_vred_installation_paths()

        assert "VRED Pro 2025" in paths
        # Should correctly select the numerically highest version
        assert paths["VRED Pro 2025"].name == "VREDPro-17.10"

    def test_extract_version_number(self, installer):
        """Test version number extraction from VRED path names."""
        # Test normal version formats
        assert installer._extract_version_number(Path("VREDPro-17.3")) == (17, 3)
        assert installer._extract_version_number(Path("VREDPro-18.10")) == (18, 10)
        assert installer._extract_version_number(Path("VREDPro-17.0")) == (17, 0)

        # Test invalid formats raise ValueError
        with pytest.raises(ValueError, match="Invalid VRED version format"):
            installer._extract_version_number(Path("VREDPro-invalid"))
        with pytest.raises(ValueError, match="Invalid VRED version format"):
            installer._extract_version_number(Path("Maya2024"))

    def test_notify_environment_change_windows(self, installer):
        """Test environment change notification on Windows."""
        with patch("ctypes.windll.user32.SendMessageTimeoutW") as mock_send_message:
            mock_send_message.return_value = 1
            installer._notify_environment_change()
            mock_send_message.assert_called_once()

    @patch("logging.basicConfig")
    def test_install_no_files(self, mock_logging, installer, temp_dir):
        """Test installation with no files found."""
        with (
            patch.object(installer, "get_submitter_files") as mock_get_files,
            patch("builtins.print"),
        ):
            mock_get_files.return_value = SubmitterFiles(
                plugin=[], scripts=[], dependency_bundle=[]
            )

            result = installer.install(destination=temp_dir)

        assert result is False

    @patch("logging.basicConfig")
    def test_install_copy_failure(self, mock_logging, installer, temp_dir):
        """Test installation with copy failure."""
        with (
            patch.object(installer, "get_submitter_files") as mock_get_files,
            patch.object(installer, "create_directory_structure") as mock_create_dirs,
            patch.object(installer, "copy_files") as mock_copy,
            patch("builtins.print"),
        ):
            mock_get_files.return_value = SubmitterFiles(
                plugin=[Path("test.py")],
                scripts=[],
                dependency_bundle=[],
            )
            mock_create_dirs.return_value = {"base": temp_dir}
            mock_copy.side_effect = RuntimeError("Copy failed")

            result = installer.install(destination=temp_dir)

        assert result is False

    @patch("logging.basicConfig")
    def test_install_success(self, mock_logging, installer, temp_dir):
        """Test successful installation."""
        # Mock all the methods to return success
        with (
            patch.object(installer, "get_submitter_files") as mock_get_files,
            patch.object(installer, "create_directory_structure") as mock_create_dirs,
            patch.object(installer, "copy_files") as mock_copy,
            patch.object(installer, "set_deadline_vred_modules_env_var") as mock_set_env,
            patch.object(installer, "install_plugin_to_vred_versions") as mock_install_plugin,
            patch.object(installer, "configure_vred_preferences") as mock_configure,
            patch.object(installer, "_print_summary_for_success") as mock_print_success,
            patch("builtins.print"),
        ):
            mock_get_files.return_value = SubmitterFiles(
                plugin=[Path("test.py")],
                scripts=[],
                dependency_bundle=[],
            )
            mock_create_dirs.return_value = {"base": temp_dir}
            mock_configure.return_value = True
            result = installer.install(
                destination=temp_dir,
                verbose=False,
                auto_configure=True,
                force_update_preferences_override=False,
            )

        assert result is True
        mock_get_files.assert_called_once()
        mock_create_dirs.assert_called_once()
        mock_copy.assert_called_once()
        mock_set_env.assert_called_once()
        mock_install_plugin.assert_called_once()
        mock_configure.assert_called_once()
        mock_print_success.assert_called_once()

    def test_get_python_script_from_xml_file_not_exists(self, installer, temp_dir):
        """Test getting python script from non-existent XML file."""
        xml_file = temp_dir / "nonexistent.xml"

        result = installer._get_python_script_from_preferences_xml(xml_file)

        assert result == ""

    def test_get_python_script_from_xml_success(self, installer, temp_dir):
        """Test getting python script from XML file."""
        xml_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<message>
  <key name="python script" type="std_string">dGVzdCBzY3JpcHQ=</key>
</message>"""
        xml_file.write_text(xml_content)

        result = installer._get_python_script_from_preferences_xml(xml_file)

        assert result == "test script"

    def test_is_deadline_cloud_added_in_preferences_xml_file_not_exists(self, installer, temp_dir):
        """Test checking complete Deadline Cloud config when file doesn't exist."""
        xml_file = temp_dir / "nonexistent.xml"

        result = installer._is_deadline_cloud_added_in_preferences_xml(xml_file)

        assert result is False

    def test_is_deadline_cloud_added_in_preferences_xml_sandbox_enabled(self, installer, temp_dir):
        """Test checking complete Deadline Cloud config when sandbox is enabled."""
        xml_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<message>
  <key name="python enable sandbox" type="bool">1</key>
  <key name="python script" type="std_string">ZnJvbSBEZWFkbGluZUNsb3VkRm9yVlJFRCBpbXBvcnQgRGVhZGxpbmVDbG91ZEZvclZSRUQKRGVhZGxpbmVDbG91ZEZvclZSRUQoKQ==</key>
</message>"""
        # the "python script" is decoded to:
        # from DeadlineCloudForVRED import DeadlineCloudForVRED\nDeadlineCloudForVRED()
        xml_file.write_text(xml_content)

        result = installer._is_deadline_cloud_added_in_preferences_xml(xml_file)

        assert result is False

    def test_is_deadline_cloud_added_in_preferences_xml_true(self, installer, temp_dir):
        """Test checking complete Deadline Cloud config when all requirements are met."""
        xml_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<message>
  <key name="python enable sandbox" type="bool">0</key>
  <key name="python script" type="std_string">ZnJvbSBEZWFkbGluZUNsb3VkRm9yVlJFRCBpbXBvcnQgRGVhZGxpbmVDbG91ZEZvclZSRUQKRGVhZGxpbmVDbG91ZEZvclZSRUQoKQ==</key>
</message>"""
        xml_file.write_text(xml_content)

        result = installer._is_deadline_cloud_added_in_preferences_xml(xml_file)

        assert result is True

    def test_confirm_override_update_yes(self, installer):
        """Test user confirmation for override update - yes."""
        with patch("install_submitter.input", return_value="y"):
            result = installer._confirm_override_update()
        assert result is True

    def test_confirm_override_update_no(self, installer):
        """Test user confirmation for override update - no."""
        with patch("install_submitter.input", return_value="n"):
            result = installer._confirm_override_update()
        assert result is False

    def test_confirm_override_update_keyboard_interrupt(self, installer):
        """Test user confirmation for override update - keyboard interrupt."""
        with patch("install_submitter.input", side_effect=KeyboardInterrupt()):
            result = installer._confirm_override_update()
        assert result is False

    def test_get_merged_script_base64_no_existing(self, installer):
        """Test getting merged script when no existing script exists."""
        with (
            patch.object(installer, "_get_python_script_from_preferences_xml") as mock_get_existing,
            patch.object(installer, "_get_vred_default_preferences_xml_path") as mock_get_path,
        ):
            mock_get_existing.return_value = ""
            mock_get_path.return_value = Path("/fake/path/preferences.xml")

            result = installer._get_merged_script_base64(None)

            decoded = base64.b64decode(result).decode("utf-8")
            assert "from DeadlineCloudForVRED import DeadlineCloudForVRED" in decoded
            assert "DeadlineCloudForVRED()" in decoded

    def test_get_merged_script_base64_with_existing_override(self, installer):
        """Test getting merged script with existing override file."""
        with patch.object(
            installer, "_get_python_script_from_preferences_xml"
        ) as mock_get_existing:
            mock_get_existing.return_value = "print('existing script')"

            result = installer._get_merged_script_base64("/path/to/override.xml")

            decoded = base64.b64decode(result).decode("utf-8")
            assert "print('existing script')" in decoded
            assert "from DeadlineCloudForVRED import DeadlineCloudForVRED" in decoded
            assert "DeadlineCloudForVRED()" in decoded

    def test_create_merged_preferences_xml_no_existing(self, installer):
        """Test creating merged XML when no existing override exists."""
        with patch.object(installer, "_get_merged_script_base64") as mock_get_script:
            mock_get_script.return_value = "dGVzdCBzY3JpcHQ="  # base64 for "test script"

            result = installer._create_merged_preferences_xml(None)

            assert '<?xml version="1.0"?>' in result
            assert "<!DOCTYPE VRED>" in result
            assert "python enable sandbox" in result
            assert "python script" in result
            assert "dGVzdCBzY3JpcHQ=" in result

    def test_create_merged_preferences_xml_with_existing(self, installer, temp_dir):
        """Test creating merged XML with existing override file."""
        # Create existing override XML with other keys
        existing_xml = temp_dir / "existing.xml"
        existing_content = """<?xml version="1.0"?>
<message id="0" type="VRED" version="0.80000001">
  <key name="other setting" type="bool">1</key>
  <key name="python enable sandbox" type="bool">1</key>
</message>"""
        existing_xml.write_text(existing_content)

        with patch.object(installer, "_get_merged_script_base64") as mock_get_script:
            mock_get_script.return_value = "dGVzdCBzY3JpcHQ="

            result = installer._create_merged_preferences_xml(str(existing_xml))

            # Should preserve other keys but override sandbox and script
            assert "other setting" in result
            assert "python enable sandbox" in result
            assert "python script" in result
            assert "dGVzdCBzY3JpcHQ=" in result
