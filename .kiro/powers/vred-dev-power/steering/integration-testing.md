# Integration Testing Guide

> All commands use PowerShell syntax.

How to run and create integration tests for the VRED Deadline Cloud integration.

## Test Architecture

VRED has a three-tier testing architecture beyond unit tests:

### 1. Submitter Tests (`test/integ/test_vred_submitter.py`)
- Tests submitter UI and job bundle generation
- Uses automated GUI interaction via bootstrap code injection
- Requires VRED Pro (for GUI dialog access)
- Compares generated job bundles against expected output in `test/integ/expected_output/bundle/`

### 2. Worker/Render Tests (`test/integ/test_vred_render.py`)
- Tests VRED rendering using OpenJD CLI to execute the job template
- Requires VRED Core or Pro + NVIDIA GPU
- Compares rendered images against expected output in `test/integ/expected_output/render/`

### 3. Local E2E Tests (`test/integ/test_vred_local_e2e.py`)
- Tests complete workflow: submitter UI → job bundle → render → validation
- Phase 1: Launch VRED Pro, configure submitter, export job bundle
- Phase 2: Load job bundle, execute VRED rendering
- Phase 3: Compare both job bundle and rendered output against expected results

### 4. Tile Assembly Tests (`test/integ/test_tile_assembler.py`)
- Tests assembling image tiles into complete frames
- Requires ImageMagick
- Uses pre-generated tile images from `test/integ/tiles/`

## Running Tests

### Prerequisites

| Test Type | VRED Pro | VRED Core | GPU | ImageMagick | License |
|-----------|----------|-----------|-----|-------------|---------|
| Submitter | ✅ Required | ❌ | ❌ | ❌ | ✅ BYOL |
| Worker/Render | ❌ | ✅ Either | ✅ | ❌ | ✅ BYOL |
| E2E | ✅ Required | ❌ | ✅ | ❌ | ✅ BYOL |
| Tile Assembly | ❌ | ❌ | ❌ | ✅ | ❌ |

### Commands

```powershell
# All integration tests
hatch run integ:test

# Submitter tests only
hatch run integ:test test/integ/test_vred_submitter.py

# Render tests only
hatch run integ:test test/integ/test_vred_render.py

# E2E tests only
hatch run integ:test test/integ/test_vred_local_e2e.py

# Tile assembly tests only
hatch run integ:test test/integ/test_tile_assembler.py

# Worker tests (separate hatch environment)
hatch run worker:test
```

## How GUI Automation Works (No Squish Required)

VRED's submitter tests use bootstrap code injection instead of external GUI tools:

1. **Bootstrap Code Generation**: Test parameters (render settings) are encoded into Python code
2. **Environment Variable Injection**: Bootstrap code is passed via `BOOTSTRAP_CODE` env var
3. **VRED Launch**: VRED Pro launches with `--disable-python-sandbox` flag
4. **Code Execution**: VRED executes the bootstrap code, which imports `submitter_dialog_controller`
5. **Dialog Control**: Controller uses VRED's internal APIs (`vrController`, Qt widget access) to manipulate the submitter dialog programmatically
6. **Bundle Export**: Controller triggers job bundle generation via the export button callback
7. **VRED Termination**: Controller terminates VRED after export
8. **Comparison**: Generated bundles are compared against expected output

```
Test runner → VRED launch → Bootstrap injection → Dialog controller
    → Submitter API calls → Job bundle export → Output comparison
```

## Test Directory Structure

```
test/integ/
├── helpers/
│   ├── vred_runner.py                    # VRED process execution
│   ├── submitter_dialog_controller.py    # Automated UI control
│   ├── load_render_parameter_values.py   # YAML parameter loading
│   ├── job_bundle_output_comparison.py   # Bundle comparison
│   ├── output_comparison.py             # Image comparison (PIL + NumPy)
│   ├── sticky_settings_verification.py  # Settings persistence validation
│   └── constants.py                     # Shared constants
├── scene_files/                         # Test scene files
│   ├── Cone.vpb
│   ├── FileReferencing.vpb
│   └── test.wire
├── expected_output/
│   ├── bundle/                          # Expected job bundle outputs
│   └── render/                          # Expected rendered images
├── tiles/                               # Pre-generated tiles for assembly tests
├── test_vred_submitter.py               # Submitter tests
├── test_vred_render.py                  # Render tests
├── test_vred_local_e2e.py              # E2E tests
├── test_tile_assembler.py              # Tile assembly tests
└── path_resolver.py                     # Path resolution utilities
```

## Output Comparison

### Job Bundle Comparison
- Template validation (`template.yaml`)
- Parameter count and value comparison (`parameter_values.yaml`)
- Asset reference filename comparison (`asset_references.yaml`)
- Path normalization for environment-specific differences

### Image Comparison
- Image size and format validation
- Pixel-level similarity using PIL and NumPy
- Tolerance threshold for acceptable differences

## E2E Testing Modes

The testing strategy supports two execution modes:

### Local Mode (Current)
```
Submitter → Job bundle → OpenJD CLI → VRED renders locally → Output comparison
```
- Runs entirely on local machine
- Fast development iteration
- No cloud infrastructure needed

### Deadline Cloud Mode (Future)
```
Submitter → Job bundle → Submit to Deadline Cloud → SMF worker renders → Output download → Comparison
```
- Validates complete cloud workflow
- Requires AWS account and Deadline Cloud farm

## Developer Licensing for CI/CD

For automated testing in CodeBuild environments, VRED requires developer licenses via SSM port forwarding:

1. Assume cross-account role for developer licensing access
2. Establish SSM port forwarding to license bastion
3. Set `ADSKFLEX_LICENSE_FILE=2705@127.0.0.1`
4. Run tests
5. Clean up SSM sessions

See the E2E testing documentation for full CodeBuild integration details.

## Debugging

### Check VRED Logs
```powershell
# Latest VRED Pro log
Get-ChildItem "$env:TEMP\VREDPro\log" -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 100

# Search for errors
Select-String -Path "$env:TEMP\VREDPro\log\*.log" -Pattern "error|exception" -CaseSensitive:$false | Select-Object -Last 20
```

### Kill Stuck VRED Processes
```powershell
Get-Process VRED* | Stop-Process -Force
```

### Verify Environment
Write environment checks to a temp file and read back:
```powershell
@"
VREDPRO=$($env:VREDPRO)
VREDPRO_exists=$(Test-Path $env:VREDPRO)
DEADLINE_VRED_MODULES=$($env:DEADLINE_VRED_MODULES)
MODULES_exists=$(Test-Path $env:DEADLINE_VRED_MODULES)
"@ | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
```
Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

For ImageMagick:
```powershell
magick --version 2>&1 | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
```
Then read and delete as above.
