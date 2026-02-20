# Dev Guide

> All commands use PowerShell syntax.

## Reading Command Output Reliably

When running PowerShell commands that produce output you need to verify, **always** use the temp-file pattern instead of reading terminal output directly:

1. Pipe command output to a temp file: `<command> | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8`
2. Read the file using the `readFile` tool on `deadline-cloud-for-vred/_check_result.txt`
3. Delete the temp file using the `deleteFile` tool on `deadline-cloud-for-vred/_check_result.txt`

## Python Environment

VRED uses Python 3.11+. Unlike 3ds Max, VRED does not have its own embedded Python — it uses the system Python or the Python bundled with VRED's installation.

## Build & Install Workflow

### Build

```powershell
hatch build
```

This creates a wheel file in `dist/` folder.

### Install Submitter to VRED

After building, copy submitter files and install dependencies:

```powershell
# Install dependencies
pip install --python-version 3.11 --only-binary=:all: "deadline[gui]" -t "$env:USERPROFILE\DeadlineCloudSubmitter\Submitters\VRED\python\modules"
```

Then follow the "After Code Changes" steps below to copy the source files.

### Code Quality

```powershell
hatch run fmt      # Format code (black + ruff)
hatch run lint     # Full lint (ruff + black check + mypy)
hatch run typing   # Type checking only
```

### Unit Tests

```powershell
hatch run unit:test                              # All tests
hatch run unit:test test/unit/test_scene.py      # Specific file
hatch run unit:test -k "test_render"             # Pattern match
```

## After Code Changes

Before copying, verify:
- `$env:USERPROFILE` is set
- `$env:VREDPRO` or `$env:VREDCORE` env var is set (derive `VRED_INSTALL` by going up 3 levels from the exe path)
- Both destination directories exist

Copy updated files:

1. Submitter source:
   ```powershell
   Copy-Item -Path "src\deadline\vred_submitter\*" -Destination "$env:USERPROFILE\DeadlineCloudSubmitter\Submitters\VRED\scripts\deadline\vred_submitter\" -Recurse -Force
   ```

2. Plugin bootstrapper:
   ```powershell
   Copy-Item -Path "vred_submitter_plugin\plug-ins\DeadlineCloudForVRED.py" -Destination "<VRED_INSTALL>\lib\python\Lib\site-packages\"
   ```
   Where `<VRED_INSTALL>` is your VRED installation root (e.g. `C:\Program Files\Autodesk\VREDPro-18.0`).
   Derive it from `$env:VREDPRO` or `$env:VREDCORE` by going up from the executable path.

3. Restart VRED to pick up changes.

## Submitter Development Workflow

1. Modify submitter code in `src/deadline/vred_submitter/`
2. Copy updated files to VRED's submitter directory
3. Restart VRED to reload the plugin
4. Set `DEADLINE_ENABLE_DEVELOPER_OPTIONS=true` for developer features
5. Use "Export Bundle" to inspect generated job bundles
6. Use "Submit" to test actual job submission

## Integration Tests

See **integration-testing.md** for full details.

| Test Type | Command | What It Tests |
|-----------|---------|---------------|
| Unit | `hatch run unit:test` | Function-level logic, no VRED needed |
| Worker | `hatch run worker:test` | Render script execution with VRED |
| Submitter | `hatch run submitter:test` | Submitter UI and job bundle generation |
| Integration | `hatch run integ:test` | Full E2E: submitter → render → validation |

## Test Infrastructure

### Bootstrap Code Injection

VRED tests use a bootstrap code injection technique:
1. Test parameters are encoded into Python code
2. Passed to VRED via `BOOTSTRAP_CODE` environment variable
3. VRED executes the bootstrap code on startup
4. Bootstrap imports the test controller or render script

This avoids the need for external GUI automation tools like Squish.

### Test Helpers (`test/integ/helpers/`)

| Helper | Purpose |
|--------|---------|
| `vred_runner.py` | VRED process execution and environment setup |
| `submitter_dialog_controller.py` | Automated submitter UI manipulation |
| `load_render_parameter_values.py` | Load render params from YAML |
| `job_bundle_output_comparison.py` | Compare generated vs expected job bundles |
| `output_comparison.py` | Image similarity comparison (PIL + NumPy) |
| `sticky_settings_verification.py` | Validate settings persistence |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `VREDPRO` | Path to VRED Pro executable |
| `VREDCORE` | Path to VRED Core executable |
| `DEADLINE_VRED_MODULES` | Path to submitter modules directory |
| `DEADLINE_ENABLE_DEVELOPER_OPTIONS` | Enable developer features in submitter |
| `MAGICK` | Path to ImageMagick executable |
| `CONDA_CHANNELS` | Override conda channels |
| `CONDA_PACKAGES` | Override conda packages |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No wheel found | `hatch build -t wheel` |
| Hatch not found | `pip install hatch` |
| Import errors | `hatch env prune` then retry |
| VRED hangs | `Get-Process VRED* \| Stop-Process -Force` |
| Python sandbox | Disable in VRED preferences or use `--disable-python-sandbox` |
| License error | Check `ADSKFLEX_LICENSE_FILE` env var |
| Submitter menu missing | Verify `DeadlineCloudForVRED.py` in site-packages |

**Logs:**
```powershell
Get-ChildItem "$env:TEMP\VREDPro\log" -Filter "*.log" | Sort-Object LastWriteTime -Descending
```
