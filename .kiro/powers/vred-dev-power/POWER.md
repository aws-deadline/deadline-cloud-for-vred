---
name: "vred-dev-power"
displayName: "VRED Dev Power"
description: "Development power for deadline-cloud-for-vred - build, lint, test, and run integration tests with VRED."
keywords: ["vred", "deadline", "build", "test", "lint", "integration", "render", "submitter"]
author: "AWS Deadline Cloud Team"
---

# VRED Dev Power

> All commands use PowerShell syntax.

> **Terminal Output Pattern:** When running PowerShell commands that produce output you need to verify, always pipe to a temp file (`<command> | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8`), read it with `readFile`, then delete it. This avoids terminal output parsing issues.

Development power for building, testing, and debugging the deadline-cloud-for-vred project.

## Overview

This project is a Python package that provides:
- **VRED Submitter**: UI plugin for submitting render jobs from VRED to Deadline Cloud
- **VRED Render Script**: `VRED_RenderScript_DeadlineCloud.py` that executes rendering on workers

## Available Steering Files

- **build-and-test.md** - Complete build and test workflow
- **integration-testing.md** - Guide for running submitter, worker, and E2E integration tests
- **troubleshooting.md** - Common issues and solutions

## Prerequisites

- Python 3.11+
- VRED Pro 2025/2026 (for submitter/integration tests) or VRED Core (for worker tests)
- Hatch (Python build tool): `pip install hatch`
- Valid VRED BYOL license
- (Optional) NVIDIA GPU with 4GB+ VRAM for worker tests
- (Optional) ImageMagick for tile assembly tests

## Quick Commands

### Build
```powershell
hatch build
```

### Lint & Format
```powershell
hatch run fmt    # Format code (black + ruff)
hatch run lint   # Run linter + type checker (ruff + black + mypy)
hatch run typing # Type checking only (mypy)
```

### Unit Tests
```powershell
hatch run unit:test                          # All unit tests
hatch run unit:test test/unit/test_scene.py  # Specific file
hatch run unit:test -k "test_render"         # Pattern match
```

### Worker Tests (requires VRED + GPU)
```powershell
hatch run worker:test
```

### Integration Tests (requires VRED Pro)
```powershell
hatch run integ:test
```

## Test Types

| Test Type | Command | Requirements |
|-----------|---------|-------------|
| Unit | `hatch run unit:test` | Python only |
| Worker | `hatch run worker:test` | VRED Core/Pro + GPU |
| Submitter | `hatch run submitter:test` | VRED Pro |
| Integration | `hatch run integ:test` | VRED Pro + GPU |

## Checking Logs

```powershell
# VRED Pro logs
Get-ChildItem "$env:TEMP\VREDPro\log" -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# VRED Core logs
Get-ChildItem "$env:TEMP\VREDCore\log" -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

## Project Structure

```
src/deadline/vred_submitter/
├── ui/components/          # Qt UI components
├── vred_submitter.py       # Main submitter
├── data_classes.py         # Settings dataclass
├── scene.py                # Scene utilities
├── assets.py               # Asset introspection
├── vred_utils.py           # VRED API wrappers
├── VRED_RenderScript_DeadlineCloud.py  # Worker render script
└── default_vred_job_template.yaml      # Job template

vred_submitter_plugin/
└── plug-ins/
    └── DeadlineCloudForVRED.py  # VRED plugin entry point

test/
├── unit/                   # Unit tests (no VRED required)
├── integ/                  # Integration tests
│   ├── helpers/            # Test utilities (vred_runner, dialog controller, etc.)
│   ├── scene_files/        # Test scene files (.vpb, .wire)
│   └── expected_output/    # Expected outputs (bundle/ and render/)
└── worker/                 # Worker render tests (if present)
```
