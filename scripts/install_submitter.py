# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
CLI entry point for installing VRED Pro in-app submitter with automatic configuration.
Handles installation, environment setup, and VRED preferences configuration.

PREREQUISITES AND ASSUMPTIONS:

- System Requirements:
  - Windows OS: VRED Pro is Windows-only, other OS will be rejected
  - Python 3.x: Required for script execution
  - Administrator privileges: Needed for registry modification and system environment variables

- VRED PRO Installation:
  - VRED Pro 2025/2026: At least one version must be installed at:
    - C:/Program Files/Autodesk/VREDPro-17.3 (2025)
    - C:/Program Files/Autodesk/VREDPro-18.0 (2026)
  - Site-packages directory: [VRED_INSTALL]/lib/python/Lib/site-packages/ must exist

- Dependency Bundle:
  - If dependency_bundle/ directory is empty or missing:
    - Internet connection required for pip install commands
    - PyPI access needed to download packages (deadline, xxhash, psutil, etc.)
  - If dependency_bundle/*.zip files exist: Offline installation possible

- RUNTIME ASSUMPTIONS:
  - Single-user installation (not system-wide)
  - VRED should be closed during installation for best results
"""

import argparse
import base64
import binascii
import ctypes
import logging
import os
import platform
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Add the scripts directory to Python path for importing deps_bundle
project_scripts_dir = Path(__file__).parent
if str(project_scripts_dir) not in sys.path:
    sys.path.insert(0, str(project_scripts_dir))

# Import dependency bundle builder
try:
    from deps_bundle import build_deps_bundle
except ImportError as exc:
    raise ImportError("Could not import deps_bundle") from exc

# Import winreg. Raises an exception if not on Windows platform
if platform.system().lower() == "windows":
    try:
        import winreg
    except ImportError as exc:
        raise ImportError("winreg module is required for VRED on Windows") from exc
else:
    raise RuntimeError("VRED Pro is only supported on Windows")

logger = logging.getLogger(__name__)

ENV_VAR_DEADLINE_VRED_MODULES = "DEADLINE_VRED_MODULES"
ENV_VAR_VRED_PREFERENCES_OVERRIDE = "VRED_PREFERENCES_OVERRIDE"
VRED_PREF_KEY_PYTHON_SANDBOX = "python enable sandbox"
VRED_PREF_KEY_PYTHON_SCRIPT = "python script"

# Supported VRED versions
SUPPORTED_VRED_VERSIONS = {17: "VRED Pro 2025", 18: "VRED Pro 2026"}


@dataclass
class SubmitterFiles:
    """Type definition for submitter files"""

    plugin: List[Path] = field(default_factory=list)
    scripts: List[Path] = field(default_factory=list)
    dependency_bundle: List[Path] = field(default_factory=list)


class VREDSubmitterInstaller:
    """Handles complete installation and configuration for Deadline Cloud submitter in VRED Pro."""

    def __init__(self):
        if platform.system().lower() != "windows":
            raise RuntimeError("VRED Pro is only supported on Windows")
        self.package_root = Path(__file__).parent.parent

    def get_default_install_directory(self) -> Path:
        """Get the default installation directory based on VRED conventions."""
        return Path.home() / "DeadlineCloudSubmitter/Submitters/VRED"

    def get_submitter_files(self) -> SubmitterFiles:
        """
        Get categorized submitter files to be copied to the installation directory.
        After installation, the target directory will have the following structure:

        <install_dir>/
        ├── plug-ins/
        │   └── DeadlineCloudForVRED.py
        ├── scripts/
        │   └── deadline/
        │       └── vred_submitter/
        │           ├── __init__.py
        │           ├── _version.py
        │           ├── vred_submitter.py
        │           └── ... (other submitter modules)
        └── python/
            └── modules/
                └── ... (dependency packages)
        """
        files = SubmitterFiles()

        # Plugin files
        plugin_dir = self.package_root / "vred_submitter_plugin" / "plug-ins"
        if plugin_dir.exists():
            files.plugin = list(plugin_dir.rglob("*.py"))

        # Scripts (src/deadline/vred_submitter directory)
        scripts_dir = self.package_root / "src" / "deadline" / "vred_submitter"
        if scripts_dir.exists():
            files.scripts = list(scripts_dir.rglob("*"))

        # Dependency bundle - build if not exists
        dependency_bundle_dir = self.package_root / "dependency_bundle"
        if not dependency_bundle_dir.exists():
            logger.info("🧱 Building dependency bundle...")
            try:
                # Change to package root directory for deps_bundle to work correctly
                original_cwd = os.getcwd()
                os.chdir(self.package_root)
                build_deps_bundle()
                os.chdir(original_cwd)
                logger.info("🧱 Dependency bundle built successfully")
            except Exception as e:
                os.chdir(original_cwd)
                logger.error("Failed to build dependency bundle: %s", e)
                raise
        else:
            logger.info("🧱 Dependency bundle already exists (%s)", dependency_bundle_dir)

        if dependency_bundle_dir.exists():
            files.dependency_bundle = list(dependency_bundle_dir.glob("*.zip"))

        return files

    def create_directory_structure(self, install_dir: Path) -> dict[str, Path]:
        """Create the required directory structure for VRED submitter."""
        directories = {
            "base": install_dir,
            "python_modules": install_dir / "python" / "modules",
            "scripts": install_dir / "scripts",
            "plugin": install_dir / "plug-ins",
        }

        for dir_path in directories.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug("Created directory: %s", dir_path)

        return directories

    def copy_files(self, files: SubmitterFiles, directories: Dict[str, Path]) -> None:
        """Copy submitter files to appropriate directories."""
        try:
            # Copy plugin files
            for plugin_file in files.plugin:
                dest_file = directories["plugin"] / plugin_file.name
                shutil.copy2(plugin_file, dest_file)
                logger.debug("Copied plugin: %s", plugin_file.name)

            # Copy scripts (preserve directory structure from src/deadline/vred_submitter)
            scripts_base = self.package_root / "src"
            for script_file in files.scripts:
                if script_file.is_file():
                    rel_path = script_file.relative_to(scripts_base)
                    dest_file = directories["scripts"] / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(script_file, dest_file)
                    logger.debug("Copied script: %s", rel_path)

            # Install dependency bundle
            if files.dependency_bundle:
                self._install_dependency_bundle(files.dependency_bundle, directories)

            logger.info(
                "Copied %d plugin files, %d script files, %d dependency bundles",
                len(files.plugin),
                len([f for f in files.scripts if f.is_file()]),
                len(files.dependency_bundle),
            )

        except (OSError, IOError) as e:
            raise RuntimeError(f"Failed to copy files: {e}") from e

    def _install_dependency_bundle(
        self, dependency_bundles: List[Path], directories: dict[str, Path]
    ) -> None:
        """Install dependency bundle ZIP files to python/modules directory."""
        for bundle_zip in dependency_bundles:
            logger.info("Installing dependency bundle: %s", bundle_zip.name)
            try:
                with zipfile.ZipFile(bundle_zip, "r") as zip_ref:
                    zip_ref.extractall(directories["python_modules"])
                logger.info("Extracted dependency bundle to: %s", directories["python_modules"])
            except (zipfile.BadZipFile, OSError) as e:
                logger.error("Failed to extract dependency bundle %s: %s", bundle_zip.name, e)
                raise

    def set_deadline_vred_modules_env_var(self, install_dir: Path) -> None:
        """Set the DEADLINE_VRED_MODULES environment variable."""
        env_var_name = ENV_VAR_DEADLINE_VRED_MODULES
        install_path = str(install_dir)

        self._set_windows_environment_variable(env_var_name, install_path)

    def install_plugin_to_vred_versions(self, install_dir: Path) -> None:
        """Install plugin to VRED site-packages directories."""
        plugin_source = install_dir / "plug-ins" / "DeadlineCloudForVRED.py"

        if not plugin_source.exists():
            raise RuntimeError("Plugin file not found: %s", plugin_source)

        success_count = 0
        vred_versions_paths = self._get_vred_installation_paths()

        for version_name, vred_path in vred_versions_paths.items():
            if vred_path and vred_path.exists():
                site_packages = vred_path / "lib" / "python" / "Lib" / "site-packages"
                if site_packages.exists():
                    try:
                        plugin_dest = site_packages / "DeadlineCloudForVRED.py"
                        shutil.copy2(plugin_source, plugin_dest)
                        logger.info("Installed plugin to %s: %s", version_name, plugin_dest)
                        success_count += 1
                    except (OSError, IOError) as e:
                        logger.warning("Failed to install plugin to %s: %s", version_name, e)
                else:
                    logger.warning(
                        "Site-packages not found for %s: %s", version_name, site_packages
                    )
            else:
                logger.warning("%s not found at: %s", version_name, vred_path)

        if success_count > 0:
            logger.info("Plugin installed to %d VRED version(s)", success_count)
            return

        logger.warning("Plugin not installed to any VRED versions")
        raise RuntimeError("Plugin installation failed")

    def _get_vred_installation_paths(self) -> Dict[str, Optional[Path]]:
        """Get VRED installation paths for supported versions only."""
        autodesk_dir = Path("C:/Program Files/Autodesk")
        vred_paths = {}

        if not autodesk_dir.exists():
            raise RuntimeError("Autodesk directory not found: %s", autodesk_dir)

        # Find all VRED Pro installations
        all_vred_paths = [path for path in autodesk_dir.glob("VREDPro-*") if path.is_dir()]

        # Group by major version and select highest minor version for each supported version
        supported_versions_found = {}

        for path in all_vred_paths:
            try:
                major, minor = self._extract_version_number(path)
                if major in SUPPORTED_VRED_VERSIONS:
                    if (
                        major not in supported_versions_found
                        or minor > supported_versions_found[major][1]
                    ):
                        supported_versions_found[major] = (path, minor)
            except ValueError:
                logger.debug("Skipping invalid VREDPro path: %s", path)
                continue

        # Convert supported versions to user-friendly names
        for major, (path, _) in supported_versions_found.items():
            vred_paths[SUPPORTED_VRED_VERSIONS[major]] = path

        # Fail fast if no supported versions found
        if not vred_paths:
            supported_list = ", ".join([f"{maj}.x" for maj in SUPPORTED_VRED_VERSIONS.keys()])
            raise RuntimeError(
                f"No supported VRED Pro versions found. Please install one of: {supported_list}"
            )

        return vred_paths

    def _extract_version_number(self, path: Path) -> tuple[int, int]:
        """Extract version number from VRED path as a tuple (major, minor)"""
        # Extract version from "VREDPro-17.3" -> (17, 3)
        match = re.search(r"VREDPro-(\d+)\.(\d+)", path.name)
        if match:
            return tuple(int(x) for x in match.groups())
        raise ValueError(f"Invalid VRED version format in path: {path.name}")

    def _set_windows_environment_variable(self, name: str, value: str) -> None:
        """Set Windows environment variable using registry."""
        try:
            key = winreg.OpenKey(  # type: ignore
                winreg.HKEY_CURRENT_USER,
                "Environment",
                0,
                winreg.KEY_SET_VALUE,  # type: ignore
            )
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)  # type: ignore
            winreg.CloseKey(key)  # type: ignore
            logger.info("Set %s=%s", name, value)
            self._notify_environment_change()
        except (OSError, ImportError) as e:
            logger.error("Failed to set environment variable %s: %s", name, e)
            raise

    def _notify_environment_change(self) -> None:
        """
        Notify Windows system of environment variable changes.
        The system broadcast ensures all running applications and future processes can
        access the updated env vars immediately. Without this notification, newly launched
        VRED Pro will not recognize the VRED-specific env vars that this script added,
        causing the Deadline Cloud submitter to not appear in VRED's interface.
        """
        try:
            # Constants for Win32 API
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002

            # Send broadcast message to notify all windows of environment change
            result = ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "Environment",
                SMTO_ABORTIFHUNG,
                5000,  # 5 second timeout
                None,
            )

            if result:
                logger.info("Notified system of environment variable changes")
            else:
                logger.warning("Failed to notify system of environment variable changes")

        except Exception as e:
            logger.debug("Could not notify system of environment changes: %s", e)
            raise

    def configure_vred_preferences(
        self,
        install_dir: Path,
        force_update_preferences_override: bool = False,
    ) -> bool:
        """
        Configure VRED using preferences override mechanism to load Deadline Cloud submitter in app.
        Handles existing override file (if exists) by merging settings.
        """
        try:
            # Check for existing override environment variable
            existing_override = os.environ.get(ENV_VAR_VRED_PREFERENCES_OVERRIDE)

            if existing_override:
                existing_override_path = Path(existing_override)
                if self._is_deadline_cloud_added_in_preferences_xml(existing_override_path):
                    logger.info("Deadline Cloud already configured in existing override")
                    return True

                if not force_update_preferences_override and not self._confirm_override_update():
                    logger.info("User declined to update existing VRED preferences override")
                    return False
            else:
                if self._is_deadline_cloud_added_in_preferences_xml(
                    self._get_vred_default_preferences_xml_path()
                ):
                    logger.info("Deadline Cloud already configured in existing preferences.xml")
                    return True

            # Create merged XML with all existing keys preserved
            override_xml = self._create_merged_preferences_xml(existing_override)

            # Create override file in install directory
            override_file = install_dir / "vred_preferences_override.xml"
            override_file.write_text(override_xml, encoding="utf-8")

            # Set environment variable to point to override file
            env_var_name = ENV_VAR_VRED_PREFERENCES_OVERRIDE
            override_path = str(override_file.absolute())

            self._set_windows_environment_variable(env_var_name, override_path)

            logger.info("Created VRED preferences override: %s", override_file)
            return True

        except Exception as e:
            logger.debug("Failed to configure VRED preferences override: %s", e)
            raise

    def _is_deadline_cloud_added_in_preferences_xml(self, xml_path: Path) -> bool:
        """Check if the given XML file contains complete Deadline Cloud configuration.

        Validates that all required Deadline Cloud components are present:
        - Python sandbox disabled
        - `DeadlineCloudForVRED import` statement
        - `DeadlineCloudForVRED` instantiation call
        """
        if not xml_path.exists():
            return False

        # Check python sandbox is disabled
        is_sandbox_disabled = not self._get_python_sandbox_enabled_from_preferences_xml(xml_path)

        # Check python script contains complete Deadline Cloud setup
        has_deadline_cloud_in_script = False
        script = self._get_python_script_from_preferences_xml(xml_path)
        if script:
            try:
                has_deadline_cloud_in_script = (
                    "from DeadlineCloudForVRED import DeadlineCloudForVRED" in script
                    and "DeadlineCloudForVRED()" in script
                )
            except (UnicodeDecodeError, binascii.Error):
                # Ignore decode errors - script content may be corrupted or in unexpected format.
                # We'll treat this as if no Deadline Cloud configuration exists.
                pass

        return is_sandbox_disabled and has_deadline_cloud_in_script

    def _get_python_script_from_preferences_xml(self, xml_path: Path) -> str:
        """
        Extract python script (human-readable string) from the given preferences.xml file.
        Returns empty string if preferences file doesn't exist or can't be read.
        """
        if not xml_path.exists():
            logger.debug("VRED preferences.xml not found at: %s", xml_path)
            return ""

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Find "python script" key
            # XML structure: <key name="python script" type="std_string">base64_content</key>
            for key_elem in root.findall(f".//key[@name='{VRED_PREF_KEY_PYTHON_SCRIPT}']"):
                script_base64 = key_elem.text
                if script_base64 and script_base64.strip():
                    bytes_data = base64.b64decode(script_base64.strip())
                    return bytes_data.decode("utf-8")
            return ""

        except (ET.ParseError, OSError) as parse_error:
            logger.debug("Failed to read VRED preferences.xml: %s", parse_error)
        except (UnicodeDecodeError, binascii.Error) as decode_error:
            logger.debug(
                "Failed to decode base64 content in VRED preferences.xml: %s", decode_error
            )

        return ""

    def _get_python_sandbox_enabled_from_preferences_xml(self, xml_path: Path) -> bool:
        """
        Get the python sandbox-enabled status (boolean) from the given preferences.xml file.
        Returns True if preferences file doesn't exist or can't be read.
        """
        if not xml_path.exists():
            logger.debug("VRED preferences.xml not found at: %s", xml_path)
            return True

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Find "python enable sandbox" key
            # XML structure: <key name="python enable sandbox" type="bool">0</key>
            sandbox_enabled = True
            for key_elem in root.findall(f".//key[@name='{VRED_PREF_KEY_PYTHON_SANDBOX}']"):
                if key_elem.text == "0":
                    return False
            return sandbox_enabled

        except (ET.ParseError, OSError) as e:
            logger.debug("Failed to read VRED preferences.xml: %s", e)

        return True

    def _confirm_override_update(self) -> bool:
        """Ask user for confirmation to update existing VRED preferences override."""
        try:
            response = input(
                "Existing VRED preferences override detected. "
                "Do you want to update it with Deadline Cloud settings? (y/N): "
            )
            return response.lower().startswith("y")
        except (EOFError, KeyboardInterrupt):
            return False

    def _create_merged_preferences_xml(self, existing_override: Optional[str]) -> str:
        """
        Create merged preferences XML that preserves all existing keys while updating
        python sandbox and script settings for Deadline Cloud.
        """
        # Get merged script content
        script_base64 = self._get_merged_script_base64(existing_override)

        # Start with base XML structure
        root = ET.Element("message")
        root.set("id", "0")
        root.set("type", "VRED")
        root.set("version", "0.80000001")

        # Copy all existing keys from override file if it exists
        if existing_override:
            existing_path = Path(existing_override)
            if existing_path.exists():
                try:
                    existing_tree = ET.parse(existing_path)
                    existing_root = existing_tree.getroot()

                    # Copy all keys except the ones we'll override
                    for key_elem in existing_root.findall(".//key"):
                        key_name = key_elem.get("name")
                        if key_name not in [
                            VRED_PREF_KEY_PYTHON_SANDBOX,
                            VRED_PREF_KEY_PYTHON_SCRIPT,
                        ]:
                            root.append(key_elem)
                except (ET.ParseError, OSError) as e:
                    logger.debug("Failed to parse existing override XML: %s", e)

        # Add/update Deadline Cloud specific keys
        sandbox_key = ET.SubElement(root, "key")
        sandbox_key.set("name", VRED_PREF_KEY_PYTHON_SANDBOX)
        sandbox_key.set("type", "bool")
        sandbox_key.text = "0"

        script_key = ET.SubElement(root, "key")
        script_key.set("name", VRED_PREF_KEY_PYTHON_SCRIPT)
        script_key.set("type", "std_string")
        script_key.text = script_base64

        # Format XML with proper indentation
        try:
            ET.indent(root, space=" ")
        except AttributeError:
            # ET.indent is only available in Python 3.9+, fallback for older versions
            pass
        xml_str = ET.tostring(root, encoding="unicode")
        return f'<?xml version="1.0"?>\n<!DOCTYPE VRED>\n{xml_str}'

    def _get_merged_script_base64(self, existing_override: Optional[str]) -> str:
        """
        Get merged script content from existing override or VRED preferences.
        Assumes the existing preferences.xml (either default one or override one) does NOT
        contain Deadline Cloud settings.
        """
        deadline_init = (
            "\nfrom DeadlineCloudForVRED import DeadlineCloudForVRED\nDeadlineCloudForVRED()"
        )

        # Try to get existing script from override file first (if given)
        if existing_override:
            existing_override_script = self._get_python_script_from_preferences_xml(
                Path(existing_override)
            )
            if existing_override_script:
                new_script = existing_override_script + deadline_init
                return base64.b64encode(new_script.encode("utf-8")).decode("ascii")

        # Fall back to VRED default preferences.xml
        existing_default_script = self._get_python_script_from_preferences_xml(
            self._get_vred_default_preferences_xml_path()
        )
        if existing_default_script:
            new_script = existing_default_script + deadline_init
            return base64.b64encode(new_script.encode("utf-8")).decode("ascii")

        # No existing script, use only deadline init
        return base64.b64encode(deadline_init.encode("utf-8")).decode("ascii")

    def _get_vred_default_preferences_xml_path(self) -> Path:
        return Path.home() / "AppData" / "Roaming" / "VREDPro" / "preferences.xml"

    def install(
        self,
        destination: Optional[Path] = None,
        verbose: bool = False,
        auto_configure: bool = True,
        force_update_preferences_override: bool = False,
    ) -> bool:
        """Install VRED submitter with optional automatic configuration."""
        try:
            if verbose:
                logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
            else:
                logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

            # Determine installation directory
            install_dir = destination or self.get_default_install_directory()
            logger.info("Installing VRED submitter to: %s", install_dir)

            # Get files to install
            files = self.get_submitter_files()
            total_files = len(files.plugin) + len(files.scripts) + len(files.dependency_bundle)

            if total_files == 0:
                logger.error("No submitter files found to install")
                return False

            logger.info("Found %d files to install", total_files)

            # Create directory structure and copy files
            directories = self.create_directory_structure(install_dir)
            self.copy_files(files, directories)

            # Set DEADLINE_VRED_MODULES env var so VRED can find submitter modules
            self.set_deadline_vred_modules_env_var(install_dir)

            # Install plugin to VRED site-packages
            self.install_plugin_to_vred_versions(install_dir)

            # Configure VRED to load the submitter
            auto_configure_done = False
            if auto_configure:
                logger.info("Configuring VRED preferences...")
                auto_configure_done = self.configure_vred_preferences(
                    install_dir, force_update_preferences_override
                )

            # Show installation summary
            if auto_configure_done:
                self._print_summary_for_success(install_dir)
            else:
                self._print_summary_for_manual_config(install_dir)
            return True

        except Exception as e:
            logger.error("Installation failed: %s", e)
            return False

    def _print_summary_for_success(self, install_dir: Path) -> None:
        """Print installation success summary with auto-configuration."""
        print(
            f"""
{self._get_summary_common_section(install_dir)}

✅ Environment Variables:
   • {ENV_VAR_DEADLINE_VRED_MODULES}={install_dir}
   • {ENV_VAR_VRED_PREFERENCES_OVERRIDE}={install_dir}/vred_preferences_override.xml

✅ VRED Integration:
   ✓ Plugin copied to VRED site-packages directories

✅ VRED Configuration:
   ✓ Preferences override file created
   ✓ Python Sandbox automatically disabled

🚀 READY TO USE:
================
1. Restart VRED (if it was running during installation)
2. Look for "Deadline Cloud" in the VRED menu bar
3. Start submitting jobs to AWS Deadline Cloud!

💡 TROUBLESHOOTING:
==================
- If menu doesn't appear, check VRED console for errors or warnings
- Verify environment variables are set correctly
- Check installation files exist in: {install_dir}
"""
        )

    def _print_summary_for_manual_config(self, install_dir: Path) -> None:
        """Print installation summary with manual configuration steps."""
        print(
            f"""
{self._get_summary_common_section(install_dir)}

✅ Environment Variable:
   • {ENV_VAR_DEADLINE_VRED_MODULES}={install_dir}

✅ VRED Integration:
   ✓ Plugin copied to VRED site-packages directories

📋 MANUAL VRED CONFIGURATION REQUIRED:
=====================================
To complete the setup, configure VRED preferences:

1. In VRED, go to Edit → Preferences → Python
2. Disable "Enable Sandbox" (uncheck the box)
3. In the "Script" field, add these lines:
   from DeadlineCloudForVRED import DeadlineCloudForVRED
   DeadlineCloudForVRED()
4. Click OK and restart VRED

After configuration, look for "Deadline Cloud" in the VRED menu bar.
"""
        )

    def _get_summary_common_section(self, install_dir: Path) -> str:
        """Get common summary section used in both success and manual config messages."""
        return f"""
🎉 VRED Submitter Installation Complete!

📁 Installation Directory: {install_dir}
📂 Directory Structure:
   • Plugin files: {install_dir}/plug-ins/
   • Script files: {install_dir}/scripts/deadline/vred_submitter/
   • Dependencies: {install_dir}/python/modules/"""


def main():
    """CLI entry point for VRED submitter installation."""
    # Check if running on Windows
    if platform.system().lower() != "windows":
        print(
            "Error: VRED Pro is only supported on Windows. "
            "This installer cannot run on other operating systems."
        )
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Install Deadline Cloud for VRED submitter with automatic configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install with automatic VRED configuration (recommended)
  install-deadline-cloud-for-vred

  # Install to custom location
  install-deadline-cloud-for-vred --destination /path/to/install

  # Install without automatic VRED configuration
  install-deadline-cloud-for-vred --no-configure

  # Install with verbose output
  install-deadline-cloud-for-vred --verbose
        """,
    )
    parser.add_argument(
        "--destination",
        "-d",
        type=Path,
        help="Directory to install the submitter to "
        "(default: ~/DeadlineCloudSubmitter/Submitters/VRED)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--no-configure",
        action="store_true",
        help="Skip automatic VRED configuration (manual setup required)",
    )
    parser.add_argument(
        "--force-update-preferences-override",
        action="store_true",
        help="Overwrite existing VRED preferences override without prompting",
    )

    args = parser.parse_args()

    # Perform installation
    installer = VREDSubmitterInstaller()
    success = installer.install(
        destination=args.destination,
        verbose=args.verbose,
        auto_configure=not args.no_configure,
        force_update_preferences_override=args.force_update_preferences_override,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
