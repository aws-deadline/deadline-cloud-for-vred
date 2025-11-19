# VRED Integration Tests

This directory contains integration tests for the VRED Deadline Cloud integration, including both submitter and rendering functionality.

## Directory Structure

```
integ/
├── helpers/                    # Common helper modules for integration tests
├── scene_files/               # Shared scene files for all tests
├── expected_output/           # Expected test outputs
│   ├── bundle/                # Expected job bundle outputs (submitter tests)
│   └── render/                # Expected render outputs (render tests)
├── tiles/                     # Tile test data for region rendering
├── output/                    # Generated test outputs (created/deleted during test runs)
├── test_vred_submitter.py     # Submitter integration tests
├── test_vred_render.py        # Rendering tests (via OpenJD CLI)
├── test_vred_local_e2e.py     # Local end-to-end tests (submitter + render)
├── test_tile_assembler.py     # Tile assembly tests
└── path_resolver.py           # Path resolution utilities

```

## Test Categories

### Submitter Tests (`test_vred_submitter.py`)

Tests the VRED submitter UI and job bundle generation.

### Render Tests (`test_vred_render.py`)

Tests VRED rendering using OpenJD CLI to execute the job template.

### Local End-to-End Tests (`test_vred_local_e2e.py`)

Tests the complete workflow from submitter UI to final rendered output:
1. **Submitter Phase**: Launch VRED Pro, configure submitter UI, export job bundle
2. **Render Phase**: Load job bundle, execute VRED rendering
3. **Validation Phase**: Compare both job bundle and rendered output against expected results

### Tile Assembly Tests (`test_tile_assembler.py`)

Tests assembling image tiles into complete frames:
- Tile assembly with ImageMagick
- Parallel processing of multiple frames

**Requirements:**
- ImageMagick must be installed

## Test Resources

### Scene Files

All integration tests share scene files from `scene_files/` directory.

### Expected Outputs

Expected outputs are organized by type:
- **bundle/**: Expected job bundle YAML files and asset references (for submitter tests)
- **render/**: Expected rendered images (for render tests)

Each test configuration has its own subdirectory named `{scene_basename}-{config_name}`.

### Tiles

Pre-generated tile images for testing tile assembly functionality.

## Helper Modules

The `helpers/` directory contains shared utilities. For detailed usage of helper functions, refer to the [README](./helpers/README.md)

## Notes

- Test output directories are automatically cleaned up before and after test runs
- All tests use the same shared scene files and helper modules
- Expected outputs are separated by type (bundle vs render) for clarity
