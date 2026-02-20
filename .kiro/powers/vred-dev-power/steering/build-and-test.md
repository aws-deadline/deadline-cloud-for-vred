# Build and Test Workflow

> All commands use PowerShell syntax.

Complete build and test workflow for deadline-cloud-for-vred.

## Step 1: Build the Wheel

Always build a fresh wheel before testing:

```powershell
hatch build
```

This creates files in `dist/`:
- `deadline_cloud_for_vred-*.whl`
- `deadline_cloud_for_vred-*.tar.gz`

To build only the wheel:
```powershell
hatch build -t wheel
```

## Step 2: Run Linting and Formatting

Before committing, ensure code passes all checks:

```powershell
# Format code (black + ruff)
hatch run fmt

# Run full lint suite (ruff + black check + mypy)
hatch run lint

# Type checking only
hatch run typing
```

Note: VRED uses both `ruff` and `black` for formatting (unlike 3ds Max which uses only ruff).

## Step 3: Run Unit Tests

Run the full unit test suite:

```powershell
hatch run unit:test
```

For faster iteration, run specific tests:

```powershell
# Run a single test file
hatch run unit:test test/unit/test_vred_submitter.py

# Run tests matching a pattern
hatch run unit:test -k "test_render"

# Run with verbose output
hatch run unit:test -vvv
```

Unit tests do NOT require VRED to be installed. They mock VRED APIs.

## Step 4: Run Worker Tests

Worker tests execute actual VRED rendering and compare output images.

**Prerequisites:**
- VRED Core or Pro installed
- NVIDIA GPU with 4GB+ VRAM
- NVIDIA driver 553.xx recommended
- `VREDCORE` or `VREDPRO` environment variable set
- ImageMagick for tile assembly tests

```powershell
hatch run worker:test
```

## Step 5: Run Integration Tests

Integration tests validate the complete workflow including submitter UI automation and rendering.

**Prerequisites:**
- VRED Pro installed (required for GUI dialog access)
- `VREDPRO` environment variable set
- Valid VRED license

```powershell
# All integration tests
hatch run integ:test

# Specific test file
hatch run integ:test test/integ/test_vred_submitter.py

# Only integ-marked tests
hatch run integ:test_integ
```

## Step 6: Check Logs

After running tests:

```powershell
# VRED Pro logs
Get-ChildItem "$env:TEMP\VREDPro\log" -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# View latest log
$latestLog = Get-ChildItem "$env:TEMP\VREDPro\log" -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latestLog.FullName -Tail 100

# Search for errors
Select-String -Path "$env:TEMP\VREDPro\log\*.log" -Pattern "error|exception" -CaseSensitive:$false | Select-Object -Last 20
```

## Subnmitter Develpoment Workflow

When changes to submitter, refer to DEVELOPMENT.md section on Submitter Development Workflow, make sure to follow the steps so that local development is reflected.

## Common Issues

### Hatch Environment Issues
If tests behave unexpectedly, prune hatch environments:
```powershell
hatch env prune
```

### Wrong Python Version
Ensure Python 3.11+ is being used. Write the check to a temp file:
```powershell
python --version 2>&1 | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8
```
Then read `deadline-cloud-for-vred/_check_result.txt` with `readFile` and delete after.

### VRED Process Stuck
Kill stuck VRED processes:
```powershell
Get-Process VRED* | Stop-Process -Force
```

### Wheel Not Found
Build the wheel first:
```powershell
hatch build -t wheel
```
