# VRED Dev Setup Guide

> All commands use PowerShell syntax.

Complete automated setup workflow for deadline-cloud-for-vred development environment.

## Reading Command Output Reliably

When running PowerShell commands that produce output you need to verify, **always** use the temp-file pattern instead of reading terminal output directly. Terminal output can be truncated or mixed with command echoes, making it unreliable.

**Pattern:**
1. Pipe command output to a temp file: `<command> | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8`
2. Read the file using the `readFile` tool on `deadline-cloud-for-vred/_check_result.txt`
3. Delete the temp file using the `deleteFile` tool on `deadline-cloud-for-vred/_check_result.txt`

Use `-NoNewline` when you expect a single value (e.g. `True`/`False`). Omit it when expecting multi-line output.

## Setup Workflow

### Step 1: Discover Installed VRED Versions
Instead of asking the user for a product and version upfront, dynamically scan for all installed VRED products. Write the result to a temp file and read it back (this avoids terminal output parsing issues):

```powershell
Get-ChildItem "C:\Program Files\Autodesk\VRED*" -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.Name } | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
```

Then read the file using the `readFile` tool on `deadline-cloud-for-vred/_check_result.txt`. After reading, delete the temp file.

**Interpreting the result:**
- If the file lists one or more directory names (e.g. `VREDPro-18.0`, `VREDCore-17.3`), present them all to the user and ask which one to set up for.
- If the file is empty, abort the setup. Tell the user: "No VRED installation found under C:\Program Files\Autodesk\. Please install VRED from https://manage.autodesk.com"

Parse the chosen directory name to extract the product (`VREDPro` or `VREDCore`) and version (e.g. `18.0`, `17.3`, `17.0`). These values are used in all subsequent steps.

**IMPORTANT:** Do NOT hardcode version numbers. Always use the values discovered from the filesystem. Do NOT use PowerShell variable interpolation (`${product}`) in commands — substitute the actual product name and version directly into path strings.

### Step 2: Verify VRED Executable
After the user picks an installation, confirm the executable exists. Write the result to a temp file and read it back:

```powershell
Test-Path "C:\Program Files\Autodesk\VREDPro-18.0\bin\WIN64\VREDPro.exe" | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
```

(Replace `VREDPro` and `18.0` with the user's chosen product and version.)

Then read the file using the `readFile` tool on `deadline-cloud-for-vred/_check_result.txt`. After reading, delete the temp file.

- If the file contains `True`: continue with setup.
- If the file contains `False`: the directory exists but the executable is missing. Warn the user that the installation may be incomplete.

Do NOT loop or retry this check — run it once and move on.

### Step 3: Read Project Documentation
Read and summarize key information from:
1. `README.md` - Project overview, compatibility, requirements
2. `DEVELOPMENT.md` - Development workflow, build instructions, manual installation steps

### Step 4: Install Development Requirements
```powershell
pip install --upgrade -r requirements-development.txt
```

This installs hatch and other development tools.

### Step 5: Install Hatch (if not already installed)
Check if hatch is already installed by writing the result to a temp file:
```powershell
hatch --version 2>&1 | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
```

Then read the file using the `readFile` tool on `deadline-cloud-for-vred/_check_result.txt`. After reading, delete the temp file.

- If the file contains a version number (e.g. `0.x.x`): hatch is installed, continue.
- If the file contains an error or "not recognized": install hatch:

```powershell
pip install hatch
```

### Step 6: Build the Package
Build wheel and source distributions:
```powershell
hatch build
```

Expected output:
- `dist/deadline_cloud_for_vred-{VERSION}-py3-none-any.whl`
- `dist/deadline_cloud_for_vred-{VERSION}.tar.gz`

### Step 7: Build the Installer (Optional)
Check if InstallBuilder is available. If available:
```powershell
hatch run installer:build-installer --local-dev-build --platform windows
```

If InstallBuilder is not found, skip this step.

### Step 8: Install Submitter to VRED
Follow the manual installation steps from DEVELOPMENT.md:

1. Create submitter directory and copy files:
```powershell
Copy-Item -Path "src\deadline\vred_submitter\*" -Destination "$env:USERPROFILE\DeadlineCloudSubmitter\Submitters\VRED\scripts\deadline\vred_submitter\" -Recurse -Force
```

2. Install submitter dependencies:
```powershell
pip install --python-version 3.11 --only-binary=:all: "deadline[gui]" -t "$env:USERPROFILE\DeadlineCloudSubmitter\Submitters\VRED\python\modules"
```

3. Copy plugin file to VRED's site-packages:
```powershell
$product = "VREDPro"  # or "VREDCore"
$version = "18.0"
Copy-Item "vred_submitter_plugin\plug-ins\DeadlineCloudForVRED.py" "C:\Program Files\Autodesk\${product}-${version}\lib\python\Lib\site-packages\"
```

### Step 9: Configure Environment Variables
Set environment variables (Machine level):

1. **VREDPRO or VREDCORE**
```powershell
# For VRED Pro:
[Environment]::SetEnvironmentVariable('VREDPRO', 'C:\Program Files\Autodesk\VREDPro-18.0\bin\WIN64\VREDPro.exe', 'Machine')
# For VRED Core:
[Environment]::SetEnvironmentVariable('VREDCORE', 'C:\Program Files\Autodesk\VREDCore-18.0\bin\WIN64\VREDCore.exe', 'Machine')
```

2. **DEADLINE_VRED_MODULES**
```powershell
[Environment]::SetEnvironmentVariable('DEADLINE_VRED_MODULES', "$env:USERPROFILE\DeadlineCloudSubmitter\Submitters\VRED", 'Machine')
```

3. **DEADLINE_ENABLE_DEVELOPER_OPTIONS**
```powershell
[Environment]::SetEnvironmentVariable('DEADLINE_ENABLE_DEVELOPER_OPTIONS', 'true', 'Machine')
```

4. **MAGICK (Optional - if ImageMagick is detected)**
Prompt user something like:

" Do you want to check for ImageMagick? This is used for Tile Assembly Testing. "

If yes, write the check result to a temp file and read it back:
```powershell
Get-ChildItem "C:\Program Files\ImageMagick*\magick.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
```

Then read the file using the `readFile` tool on `deadline-cloud-for-vred/_check_result.txt`. After reading, delete the temp file.

- If the file contains a path: ImageMagick is installed. Set the environment variable:
```powershell
[Environment]::SetEnvironmentVariable('MAGICK', '<path from file>', 'Machine')
```
- If the file is empty: ImageMagick is not installed. Skip this step.

### Step 10: Configure VRED Plugin Startup
Remind the user to configure VRED to load the plugin on startup:
1. Start VRED Pro
2. Go to `Edit menu → Preferences → General Settings → Script`
3. Uncheck "Enable Python Sandbox"
4. Append to the script section:
```python
from DeadlineCloudForVRED import DeadlineCloudForVRED
DeadlineCloudForVRED()
```
5. Click Save

### Step 11: Display Setup Summary
Show a summary of what was installed and configured:
- Hatch version
- Built packages
- Submitter installation location
- Environment variables set
- Next steps

## Example Summary Output

```
=== VRED Dev Setup Complete ===

✅ Hatch installed
✅ Package built: deadline_cloud_for_vred-{VERSION}
✅ Submitter installed to $env:USERPROFILE\DeadlineCloudSubmitter\Submitters\VRED
✅ Plugin copied to VREDPro-18.0 site-packages
✅ Environment variables configured

Environment Variables Set:
- VREDPRO = C:\Program Files\Autodesk\VREDPro-18.0\bin\WIN64\VREDPro.exe
- DEADLINE_VRED_MODULES = $env:USERPROFILE\DeadlineCloudSubmitter\Submitters\VRED
- DEADLINE_ENABLE_DEVELOPER_OPTIONS = true

Next Steps:
1. Restart your terminal for environment variables to take effect
2. Configure VRED to load the plugin (see Step 10 above)
3. Restart VRED
4. Run unit tests: hatch run unit:test
5. Run worker tests: hatch run worker:test
```

## Important Notes

- VRED Pro is required for submitter/integration tests (GUI dialog access)
- VRED Core is sufficient for worker/render tests (headless rendering)
- VRED requires BYOL licensing
- Environment variables require terminal restart to take effect
- Administrator privileges needed for machine-level environment variables
- Python Sandbox must be disabled in VRED for the submitter to work
