---
name: vred-dev-setup
version: 1.0.0
displayName: VRED Dev Setup
description: Automated development environment setup for deadline-cloud-for-vred - builds packages, installs dependencies, and configures environment variables
keywords:
  - vred
  - deadline
  - setup
  - build
  - install
  - environment
  - development
  - hatch
author: AWS Deadline Cloud
---

# VRED Dev Setup Power

> All commands use PowerShell syntax.

> **Terminal Output Pattern:** When running PowerShell commands that produce output you need to verify, always pipe to a temp file (`<command> | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8`), read it with `readFile`, then delete it. This avoids terminal output parsing issues.

Automated development environment setup for deadline-cloud-for-vred project.

## What This Power Does

This power automates the complete development environment setup for working on the deadline-cloud-for-vred project. It handles everything from reading documentation to building packages, installing the submitter, and configuring environment variables.

## Setup Steps Performed

1. **Documentation Review** - Reads README.md and DEVELOPMENT.md to understand project requirements
2. **Hatch Installation** - Installs and configures Hatch build tool
3. **Package Build** - Builds wheel and source distributions
4. **Installer Build** - Builds the Windows installer (if InstallBuilder is available)
5. **VRED Detection** - Verifies VRED Pro or VRED Core installation
6. **Submitter Installation** - Copies submitter files and installs dependencies to VRED modules directory
7. **Plugin Installation** - Copies DeadlineCloudForVRED.py to VRED's site-packages
8. **Test Dependencies** - Installs pytest, coverage, pillow, numpy, and other test packages
9. **Environment Configuration** - Sets up required environment variables (VREDCORE, VREDPRO, DEADLINE_VRED_MODULES)

## Prerequisites

- Python 3.11+ installed on system
- VRED Pro 2025/2026 or VRED Core 2025/2026 installed
- Windows operating system
- Valid VRED BYOL (Bring Your Own License)
- (Optional) InstallBuilder for building installers
- (Optional) ImageMagick for tile assembly testing

## Usage

The power will automatically scan `C:\Program Files\Autodesk\` for all installed VRED products and versions (e.g. VREDPro-18.0, VREDCore-17.3, VREDPro-17.0). It presents the discovered installations and lets you choose which one to set up for.

If no VRED installation is found, the setup will abort with instructions to install VRED first.

## What Gets Installed

### System Python Packages
- `hatch` - Build tool and environment manager
- Development requirements from `requirements-development.txt`

### Submitter Dependencies (installed to VRED modules directory)
- `deadline[gui]` - AWS Deadline Cloud client library with GUI support
- All required dependencies

### Test Packages (via hatch environments)
- `pytest` - Test framework
- `pytest-cov` - Coverage plugin
- `pytest-xdist` - Parallel test execution
- `coverage` - Code coverage measurement
- `pillow` - Image processing for render output comparison
- `numpy` - Numerical operations for image comparison

### Environment Variables
- `VREDCORE` - Path to VRED Core executable (if using Core)
- `VREDPRO` - Path to VRED Pro executable (if using Pro)
- `DEADLINE_VRED_MODULES` - Path to submitter modules directory
- `DEADLINE_ENABLE_DEVELOPER_OPTIONS` - Enables developer features in submitter UI
- `MAGICK` - (Optional) Path to ImageMagick executable for tile assembly

## VRED Installation Paths

VRED uses versioned directory names under `C:\Program Files\Autodesk\`. The power dynamically discovers all installed versions. Common examples:
- VRED Pro 2026: `C:\Program Files\Autodesk\VREDPro-18.0`
- VRED Core 2026: `C:\Program Files\Autodesk\VREDCore-18.0`
- VRED Pro 2025.3: `C:\Program Files\Autodesk\VREDPro-17.3`
- VRED Pro 2025: `C:\Program Files\Autodesk\VREDPro-17.0`
- VRED Core 2025: `C:\Program Files\Autodesk\VREDCore-17.0`

Any version matching the pattern `VRED{Pro|Core}-X.Y` will be detected automatically.

Executables are located at:
- `C:\Program Files\Autodesk\VREDPro-18.0\bin\WIN64\VREDPro.exe`
- `C:\Program Files\Autodesk\VREDCore-18.0\bin\WIN64\VREDCore.exe`

## Submitter Installation Layout

```
$env:USERPROFILE\DeadlineCloudSubmitter\Submitters\VRED\
├── scripts\deadline\vred_submitter\    # Submitter source files
└── python\modules\                      # deadline[gui] and dependencies
```

The plugin file `DeadlineCloudForVRED.py` is copied to VRED's site-packages:
- `C:\Program Files\Autodesk\VREDPro-18.0\lib\python\Lib\site-packages\`

## After Setup

Once setup is complete, you can:

### Run Unit Tests
```powershell
hatch run unit:test
```

### Run Worker Tests (requires VRED + GPU)
```powershell
hatch run worker:test
```

### Run Integration Tests (requires VRED Pro)
```powershell
hatch run integ:test
```

### Build Package
```powershell
hatch build
```

### Format and Lint Code
```powershell
hatch run fmt
hatch run lint
```

## Troubleshooting

### Hatch Not Found
If hatch is not found after installation, restart your terminal or add to PATH:
```powershell
$env:PATH = "C:\Users\$env:USERNAME\AppData\Roaming\Python\Python311\Scripts;$env:PATH"
```

### VRED Not Found
Verify VRED is installed at the expected location (write to temp file and read back):
```powershell
Test-Path "C:\Program Files\Autodesk\VREDPro-18.0\bin\WIN64\VREDPro.exe" | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
```
Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

### Environment Variables Not Applied
Environment variables are set at machine level. You may need to:
1. Restart your terminal
2. Restart VRED to pick up new environment variables

### VRED Licensing Issues
VRED requires BYOL licensing. Ensure your license server is accessible and `ADSKFLEX_LICENSE_FILE` is configured if needed.

### Python Sandbox Issues
If VRED blocks submitter execution, ensure Python Sandbox is disabled:
- `Edit menu → Preferences → General Settings → Script → Uncheck "Enable Python Sandbox"`
- Or launch VRED with `--disable-python-sandbox` flag

## Notes

- Setup requires Administrator privileges for setting machine-level environment variables
- VRED requires BYOL licensing (no Hammersmark UBL support)
- InstallBuilder is optional - installer build will be skipped if not found
- ImageMagick is optional but required for tile assembly / region rendering tests
- VRED Pro is required for submitter/integration tests (GUI dialog access)
- VRED Core is sufficient for worker/render tests (headless rendering)
