#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
"""Setup runner for VRED integration tests in CodeBuild."""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

VRED_VERSIONS = ["2025", "2026"]

# S3 paths for VRED installers (relative to INSTALLER_BUCKET)
VRED_S3_PATHS = {
    "2025": "vred/2025/VREDPro2025.zip",
    "2026": "vred/2026/VREDPro2026.zip",
}

# Install paths for VRED Pro on Windows
VRED_INSTALL_PATHS = {
    "2025": r"C:\Program Files\Autodesk\VREDPro-17.3",
    "2026": r"C:\Program Files\Autodesk\VREDPro-18.0",
}

VRED_EXE_PATHS = {
    "2025": r"C:\Program Files\Autodesk\VREDPro-17.3\bin\WIN64\VREDPro.exe",
    "2026": r"C:\Program Files\Autodesk\VREDPro-18.0\bin\WIN64\VREDPro.exe",
}


def run(cmd, check=True, shell=False):
    """Run a command and optionally check for errors."""
    print(f"Running: {cmd if shell else ' '.join(cmd)}")
    result = subprocess.run(cmd, shell=shell)
    if check and result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        sys.exit(result.returncode)
    return result


def download_from_s3(s3_path, local_path):
    """Download a file from S3 installer bucket."""
    bucket = os.environ.get("INSTALLER_BUCKET")
    if not bucket:
        print("ERROR: INSTALLER_BUCKET environment variable not set")
        return False

    cmd = ["aws", "s3", "cp", f"s3://{bucket}/{s3_path}", str(local_path), "--no-progress"]

    run(cmd)
    return True


def find_setup_exe(extract_path):
    """Locate Setup.exe in the extracted installer directory."""
    setup_exe = extract_path / "Setup.exe"
    if setup_exe.exists():
        return setup_exe

    for subdir in extract_path.iterdir():
        if subdir.is_dir():
            potential_setup = subdir / "Setup.exe"
            if potential_setup.exists():
                return potential_setup

    return None


def run_installer(setup_exe):
    """Run the VRED silent installer and log output."""
    print(f"Running silent install: {setup_exe} -q -i install")
    result = subprocess.run(
        [str(setup_exe), "-q", "-i", "install"],
        capture_output=True,
        text=True,
    )
    print(f"Installer exit code: {result.returncode}")
    if result.stdout:
        print(f"Installer stdout: {result.stdout}")
    if result.stderr:
        print(f"Installer stderr: {result.stderr}")


def print_autodesk_logs():
    """Print recent Autodesk installer logs for debugging."""
    autodesk_log_dir = (
        Path(os.environ.get("LOCALAPPDATA", "C:/Users/Default/AppData/Local"))
        / "Autodesk"
        / "ODIS"
        / "logs"
    )
    if not autodesk_log_dir.exists():
        return

    print(f"Autodesk logs found at: {autodesk_log_dir}")
    recent_logs = sorted(
        autodesk_log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True
    )[:3]
    for log in recent_logs:
        print(f"--- {log.name} (last 50 lines) ---")
        try:
            lines = log.read_text(errors="ignore").splitlines()[-50:]
            print("\n".join(lines))
        except Exception as e:
            print(f"Could not read log: {e}")


def verify_installation(install_path, marker_file, version):
    """Verify VRED installation and create marker file on success."""
    if install_path.exists():
        marker_file.touch()
        print(f"VRED Pro {version} installed successfully")
        return

    print(f"WARNING: Install path {install_path} not found after installation")
    autodesk_dir = Path("C:/Program Files/Autodesk")
    if autodesk_dir.exists():
        print(f"Contents of {autodesk_dir}:")
        for item in autodesk_dir.iterdir():
            print(f"  {item.name}")


def download_and_extract(version):
    """Download and extract the VRED installer. Returns (zip_path, extract_path)."""
    zip_path = Path(f"C:/Temp/VREDPro{version}.zip")
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    if not download_from_s3(VRED_S3_PATHS[version], zip_path):
        print(f"ERROR: Failed to download VRED {version} installer")
        sys.exit(1)

    extract_path = Path(f"C:/Temp/VREDPro{version}")
    run(
        [
            "powershell",
            "-Command",
            f"Expand-Archive -Path '{zip_path}' -DestinationPath '{extract_path}' -Force",
        ]
    )
    return zip_path, extract_path


def install_vred_version(version):
    """Install a single VRED version."""
    install_path = Path(VRED_INSTALL_PATHS[version])
    marker_file = install_path / ".installed"

    if marker_file.exists():
        print(f"VRED Pro {version} already installed at {install_path}")
        return

    print(f"Installing VRED Pro {version}...")
    zip_path, extract_path = download_and_extract(version)

    setup_exe = find_setup_exe(extract_path)
    if not setup_exe:
        print(f"ERROR: Setup.exe not found in {extract_path}")
        sys.exit(1)

    run_installer(setup_exe)
    print_autodesk_logs()
    verify_installation(install_path, marker_file, version)
    zip_path.unlink(missing_ok=True)


def setup_windows(versions):
    """Set up VRED Pro on Windows."""
    for version in versions:
        install_vred_version(version)

    print("Installing VRED submitter from current branch...")
    run(["pip", "install", "--force-reinstall", "-e", "."])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup VRED test environment")
    parser.add_argument(
        "--versions",
        nargs="+",
        default=VRED_VERSIONS,
        help="VRED versions to install (e.g., 2025 2026)",
    )

    args = parser.parse_args()

    system = platform.system()
    print(f"Setting up {system} with VRED {', '.join(args.versions)}")

    if system != "Windows":
        print("ERROR: VRED Pro is only supported on Windows")
        sys.exit(1)

    setup_windows(args.versions)

    print("Setup complete!")
