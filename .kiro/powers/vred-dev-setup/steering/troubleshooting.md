# Troubleshooting Guide

> All commands use PowerShell syntax.

Common issues and solutions for VRED dev setup.

## Reading Command Output Reliably

When running PowerShell commands that produce output you need to verify, **always** use the temp-file pattern instead of reading terminal output directly:

1. Pipe command output to a temp file: `<command> | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8`
2. Read the file using the `readFile` tool on `deadline-cloud-for-vred/_check_result.txt`
3. Delete the temp file using the `deleteFile` tool on `deadline-cloud-for-vred/_check_result.txt`

## VRED Not Found

**Problem:** Setup aborts with "VRED is not installed"

**Solutions:**
1. Verify VRED is installed at the standard location:
   ```
   C:\Program Files\Autodesk\VREDPro-18.0\  (VRED Pro 2026)
   C:\Program Files\Autodesk\VREDCore-18.0\ (VRED Core 2026)
   ```

2. Check the version number matches (18.0 for 2026, 17.0 for 2025)

3. Install VRED from https://manage.autodesk.com

## Hatch Installation Issues

**Problem:** `hatch: The term 'hatch' is not recognized`

**Solutions:**
1. Verify hatch is installed (write to temp file and read back):
   ```powershell
   python -m pip list 2>&1 | Select-String "hatch" | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

2. Add Scripts directory to PATH:
   ```powershell
   $env:PATH = "C:\Users\$env:USERNAME\AppData\Roaming\Python\Python311\Scripts;$env:PATH"
   ```

3. Restart terminal after installation

## Build Failures

**Problem:** `hatch build` fails

**Solutions:**
1. Ensure you're in the repository root directory

2. Check if git is initialized (hatch-vcs requires git):
   ```powershell
   git status
   ```

3. Verify Python version (write to temp file and read back):
   ```powershell
   python --version 2>&1 | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

4. Clean build artifacts and retry:
   ```powershell
   Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
   hatch build
   ```

## Submitter Installation Issues

**Problem:** Submitter files not found or not loading in VRED

**Solutions:**
1. Verify submitter files were copied (write to temp file and read back):
   ```powershell
   Test-Path "$env:USERPROFILE\DeadlineCloudSubmitter\Submitters\VRED\scripts\deadline\vred_submitter" | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

2. Verify plugin file was copied to VRED site-packages:
   ```powershell
   Test-Path "C:\Program Files\Autodesk\VREDPro-18.0\lib\python\Lib\site-packages\DeadlineCloudForVRED.py" | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

3. Verify DEADLINE_VRED_MODULES is set:
   ```powershell
   [Environment]::GetEnvironmentVariable('DEADLINE_VRED_MODULES', 'Machine') | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

4. Verify deadline[gui] dependencies are installed:
   ```powershell
   Test-Path "$env:USERPROFILE\DeadlineCloudSubmitter\Submitters\VRED\python\modules\deadline" | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

## VRED Licensing Issues

**Problem:** VRED fails to start or reports license errors

**Solutions:**
1. VRED requires BYOL (Bring Your Own License) - ensure your license server is accessible

2. Check ADSKFLEX_LICENSE_FILE environment variable (write to temp file and read back):
   ```powershell
   $env:ADSKFLEX_LICENSE_FILE | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

3. For developer licensing with SSM port forwarding:
   ```powershell
   $env:ADSKFLEX_LICENSE_FILE = "2705@127.0.0.1"
   ```

4. Check FlexLM diagnostics:
   ```powershell
   $env:FLEXLM_DIAGNOSTICS = "3"
   ```

## Python Sandbox Issues

**Problem:** VRED reports "builtins.builtins.exec blocked by python sandbox"

**Solutions:**
1. Disable Python Sandbox in VRED preferences:
   - `Edit menu → Preferences → General Settings → Script`
   - Uncheck "Enable Python Sandbox"

2. Or launch VRED with the flag:
   ```powershell
   & "C:\Program Files\Autodesk\VREDPro-18.0\bin\WIN64\VREDPro.exe" --disable-python-sandbox
   ```

3. If Python Sandbox must be enabled, add modules from `python-sandbox-module-allowlist.txt` to VRED's preferences

## Environment Variables Not Applied

**Problem:** Environment variables not recognized after setup

**Solutions:**
1. Restart terminal/PowerShell session

2. Check if variables are set (write to temp file and read back):
   ```powershell
   @"
   VREDPRO=$([Environment]::GetEnvironmentVariable('VREDPRO', 'Machine'))
   DEADLINE_VRED_MODULES=$([Environment]::GetEnvironmentVariable('DEADLINE_VRED_MODULES', 'Machine'))
   "@ | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

3. Restart VRED to pick up new environment variables

## Integration Test Failures

**Problem:** Integration tests fail to run

**Solutions:**
1. Ensure VRED Pro is installed (not just Core) - submitter tests require Pro for GUI access

2. Verify VREDPRO environment variable (write to temp file and read back):
   ```powershell
   $env:VREDPRO | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

3. Check that `C:\vred-snapshots` directory exists (used by submitter tests):
   ```powershell
   New-Item -ItemType Directory -Path "C:\vred-snapshots" -Force
   ```

4. Check VRED logs (write to temp file and read back):
   ```powershell
   Get-ChildItem "$env:TEMP\VREDPro\log" -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Format-Table Name, LastWriteTime -AutoSize | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

## Worker Test Failures

**Problem:** Worker tests fail or produce incorrect output

**Solutions:**
1. Verify GPU is available (write to temp file and read back):
   ```powershell
   nvidia-smi 2>&1 | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

2. Check NVIDIA driver version (553.xx recommended):
   ```powershell
   nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>&1 | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

3. Verify VREDCORE or VREDPRO environment variable is set

4. For tile assembly tests, verify ImageMagick (write to temp file and read back):
   ```powershell
   magick --version 2>&1 | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.
   Also check MAGICK env var:
   ```powershell
   $env:MAGICK | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
   ```
   Then read and delete as above.

## Permission Denied Errors

**Problem:** Access denied when setting environment variables or copying files

**Solutions:**
1. Run PowerShell as Administrator for machine-level environment variables

2. For copying to Program Files, use elevated permissions:
   ```powershell
   Start-Process powershell -Verb RunAs -ArgumentList "Copy-Item 'vred_submitter_plugin\plug-ins\DeadlineCloudForVRED.py' 'C:\Program Files\Autodesk\VREDPro-18.0\lib\python\Lib\site-packages\'"
   ```

## Module Import Errors

**Problem:** `ModuleNotFoundError` when running tests

**Solutions:**
1. Verify test dependencies are installed:
   ```powershell
   hatch run unit:test --collect-only
   ```

2. Reinstall test requirements:
   ```powershell
   pip install -r requirements-testing.txt
   pip install -r requirements-unit-testing.txt
   ```

3. Prune hatch environments and retry:
   ```powershell
   hatch env prune
   hatch run unit:test
   ```
