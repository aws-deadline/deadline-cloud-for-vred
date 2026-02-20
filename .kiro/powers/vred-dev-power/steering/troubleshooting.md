# Troubleshooting Guide

> All commands use PowerShell syntax.

Common issues and solutions when developing deadline-cloud-for-vred.

## Reading Command Output Reliably

When running PowerShell commands that produce output you need to verify, **always** use the temp-file pattern instead of reading terminal output directly:

1. Pipe command output to a temp file: `<command> | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8`
2. Read the file using the `readFile` tool on `deadline-cloud-for-vred/_check_result.txt`
3. Delete the temp file using the `deleteFile` tool on `deadline-cloud-for-vred/_check_result.txt`

## Build Issues

### "No wheel files found in dist directory"
```powershell
hatch build -t wheel
```

### Hatch not found
```powershell
pip install hatch
```

### Build fails with version error
Ensure git is initialized (hatch-vcs requires git tags):
```powershell
git status
git describe --tags
```

## Test Issues

### Unit tests fail with import errors
```powershell
# Prune and recreate hatch environments
hatch env prune
hatch run unit:test
```

Or install requirements manually:
```powershell
pip install -r requirements-testing.txt
pip install -r requirements-unit-testing.txt
```

### Integration test hangs
VRED may be waiting for user input or stuck. Kill processes:
```powershell
Get-Process VRED* | Stop-Process -Force
```

### Submitter tests fail - "VRED Pro not found"
Submitter tests require VRED Pro (not Core). Write the check to a temp file:
```powershell
Test-Path $env:VREDPRO | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
```
Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.
The VREDPRO env var should point to VREDPro.exe, e.g.:
`C:\Program Files\Autodesk\VREDPro-18.0\bin\WIN64\VREDPro.exe`

### Worker tests fail - no GPU
Worker tests require an NVIDIA GPU. Write the check to a temp file:
```powershell
nvidia-smi 2>&1 | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
```
Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.
Check driver version (553.xx recommended for VRED 2025/2026).

### Tile assembly tests fail
Verify ImageMagick is installed and accessible. Write the check to a temp file:
```powershell
magick --version 2>&1 | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
```
Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.
Also check the MAGICK env var:
```powershell
$env:MAGICK | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
```
Then read and delete as above.

## VRED Issues

### VRED won't start - license error
VRED requires BYOL licensing:
1. Check license server accessibility
2. Verify `ADSKFLEX_LICENSE_FILE` environment variable
3. For developer licensing: `$env:ADSKFLEX_LICENSE_FILE = "2705@127.0.0.1"`

### "builtins.builtins.exec blocked by python sandbox"
Disable Python Sandbox:
1. In VRED: `Edit → Preferences → General Settings → Script → Uncheck "Enable Python Sandbox"`
2. Or launch with: `--disable-python-sandbox` flag
3. Or add modules from `python-sandbox-module-allowlist.txt` to VRED preferences

### Submitter menu not appearing in VRED
1. Verify plugin file exists (write to temp file and read back):
   ```powershell
   Test-Path "C:\Program Files\Autodesk\VREDPro-18.0\lib\python\Lib\site-packages\DeadlineCloudForVRED.py" | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8 -NoNewline
   ```
   Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.
2. Verify VRED preferences have the startup script configured
3. Check VRED Console for errors

### VRED renders solid black
- Verify scene is configured for Raytracing (region rendering requires it)
- Check lighting setup (raytracing needs proper light sources)
- Verify camera exposure settings
- Check render quality settings

## Logging Issues

### Can't find VRED logs
```powershell
# VRED Pro logs
Get-ChildItem "$env:TEMP\VREDPro\log" -Filter "*.log" | Sort-Object LastWriteTime -Descending

# VRED Core logs
Get-ChildItem "$env:TEMP\VREDCore\log" -Filter "*.log" | Sort-Object LastWriteTime -Descending
```

### Need more verbose logging
Set `FLEXLM_DIAGNOSTICS=3` for license diagnostics:
```powershell
$env:FLEXLM_DIAGNOSTICS = "3"
```

## Path Issues

### Scene file not found
1. Verify file exists: `Test-Path "path/to/scene.vpb"`
2. Use forward slashes in YAML/JSON
3. Check `parameter_values.yaml` paths

### Output directory doesn't exist
```powershell
New-Item -ItemType Directory -Path "test/integ/output" -Force
```

### Submitter modules not found
Verify `DEADLINE_VRED_MODULES` points to correct location. Write checks to a temp file:
```powershell
@"
DEADLINE_VRED_MODULES=$($env:DEADLINE_VRED_MODULES)
scripts_exist=$(Test-Path "$env:DEADLINE_VRED_MODULES\scripts\deadline\vred_submitter")
modules_exist=$(Test-Path "$env:DEADLINE_VRED_MODULES\python\modules\deadline")
"@ | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
```
Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

## Python Environment Issues

### Wrong Python version
VRED requires Python 3.11+. Write the check to a temp file:
```powershell
python --version 2>&1 | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
```
Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

### Hatch environment corrupted
```powershell
hatch env prune
hatch run unit:test
```

## Render Issues

### Region rendering produces black tiles
- Region rendering only works with Raytracing quality
- "Use GPU Ray Tracing" is automatically enabled with region rendering
- Verify scene has proper lighting for raytracing

### Color inconsistencies between Windows and Linux
- Check tone mapper settings
- Verify color space settings (sRGB/Reinhard/Linear)
- Use compatible NVIDIA driver (553.xx)

### Output images don't match expected
- Check render quality settings
- Verify image dimensions match
- Check if DLSS or Super Sampling settings differ
- Image comparison uses tolerance threshold - check if difference is within acceptable range

## Getting Help

If issues persist:

1. Check project documentation:
   - README.md
   - DEVELOPMENT.md

2. Check VRED logs for detailed error messages

3. Verify all prerequisites:
   - Python 3.11+
   - VRED Pro/Core 2025/2026
   - Valid BYOL license
   - NVIDIA GPU + driver 553.xx (for worker tests)
   - ImageMagick (for tile tests)

4. Try a clean setup:
   - `hatch env prune`
   - `hatch build`
   - Re-run tests
