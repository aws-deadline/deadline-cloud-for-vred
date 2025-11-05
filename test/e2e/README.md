# End-to-End Tests for VRED Deadline Cloud Integration

## Overview

End-to-end tests validate the complete workflow from submitter UI to final rendered output:

1. **Submitter Phase**: Launch VRED Pro, configure submitter UI, export job bundle
2. **Render Phase**: Load job bundle, execute VRED rendering
3. **Validation Phase**: Compare rendered output against expected results

## Directory Structure

```
test/e2e/
├── scene_files/          # Test scene files (.vpb)
├── expected_output/      # Expected outputs for validation
│   └── {SceneName}-{TestName}/
│       ├── bundle/       # Expected job bundle files
│       │   ├── template.yaml
│       │   ├── parameter_values.yaml
│       │   └── asset_references.yaml
│       └── render/       # Expected rendered images
├── output/               # Generated test outputs (cleaned after tests)
│   └── {SceneName}-{TestName}/
│       ├── bundle/       # Generated job bundle
│       └── render/       # Rendered output images
├── test_vred_e2e.py     # E2E test cases
├── constants.py          # E2E-specific constants
└── path_resolver.py      # Path resolution utilities
```

## Prerequisites

- VRED Pro (required for GUI submitter testing)
- Set `VREDPRO` environment variable to VRED Pro executable path
- Scene files in `scene_files/` directory
- Expected output images in `expected_output/{SceneName}-{TestName}/` directories

## Running Tests

```bash
# Run all e2e tests
pytest test/e2e/ -m e2e

# Run specific test
pytest test/e2e/test_vred_e2e.py::TestVREDE2E::test_e2e_basic_render -v
```

## Adding New Tests

1. Add scene file to `test/e2e/scene_files/`
2. Create expected output directory structure:
   ```
   test/e2e/expected_output/{SceneName}-{TestName}/
   ├── bundle/              # Expected job bundle (optional)
   │   ├── template.yaml
   │   ├── parameter_values.yaml
   │   └── asset_references.yaml
   └── render/              # Expected rendered images (required)
       └── *.png/jpg/etc
   ```
3. Add test method to `TestVREDE2E` class with appropriate test settings

## Test Settings Format

```python
test_settings = [
    {"name": "OutputDir", "value": "c:\\vred-snapshots"},
    {"name": "OutputFileNamePrefix", "value": "image"},
    {"name": "OutputFormat", "value": "PNG"},
    {"name": "RenderAnimation", "value": "false"},
    {"name": "View", "value": "Front"},
]
```

## Shared Infrastructure

E2E tests leverage shared utilities from `test/common/`:
- `VREDRunner`: Common VRED execution logic
- `Constants`: Shared constants across test suites

This reduces code duplication and ensures consistency across submitter, worker, and e2e tests.
