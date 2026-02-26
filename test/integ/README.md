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

## Running the Tests

From the repository root (Windows only, requires VRED installed):

```bash
hatch run integ:test
```

To run a specific test category or individual test:

```bash
hatch run integ:test -m submitter
hatch run integ:test test/integ/test_vred_submitter.py::TestVREDSubmitter::test_submitter_dialog_basic_settings
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

## Adding New Submitter Tests

### The Test Helper Pattern

All submitter tests in `test_vred_submitter.py` use the `_run_submitter_dialog_field_value_compare_test` helper. To add a new test, call it with:

- `test_name`: A short identifier (e.g., `"dlss_quality"`, `"dpi"`)
- `scene_name`: The scene file in `scene_files/` (e.g., `"Cone.vpb"`)
- `parameter_overrides`: A dict of parameter names to values that the submitter UI should apply
- `asset_overrides` (optional): A list of extra file reference paths, for tests that verify input file detection

```python
@pytest.mark.scene_files(Path("scene_files") / "Cone.vpb")
def test_submitter_dialog_my_feature(self):
    self._run_submitter_dialog_field_value_compare_test(
        "my_feature",
        "Cone.vpb",
        {
            "output_directories": ["c:\\vred-snapshots"],
            "StartFrame": 0,
            "EndFrame": 25,
            "OutputDir": "c:\\vred-snapshots",
            "OutputFileNamePrefix": "image",
            "OutputFormat": "PNG",
            "RenderAnimation": "false",
            "View": "Front",
            "MyNewParam": "some_value",
        },
    )
```

### Base Templates (Avoiding Per-Test Expected Output Folders)

Instead of creating a full `parameter_values.yaml` and `asset_references.yaml` for every test case, the comparison helper can generate expected output at runtime by merging your `parameter_overrides` onto base templates in `expected_output/bundle/`:

- `_base_parameter_values.yaml` — Default values for all job parameters
- `_base_asset_{SceneName}.yaml` — Default asset references per scene file (e.g., `_base_asset_Cone.yaml`)

When a test runs, the helper checks for a per-test expected folder (`expected_output/bundle/{SceneName}-{test_name}/`). If one exists, it uses those files directly. If not, it falls back to the base templates and applies your `parameter_overrides` on top.

This means most new tests don't need an expected output folder, just provide the overrides and the base templates handle the rest. Only create a per-test folder when the expected output can't be expressed as overrides on the base (e.g., custom tiling templates, file referencing tests with unique asset structures).

### Parametrize for Multi-Value Coverage

Use `@pytest.mark.parametrize` to test multiple values of a single parameter without duplicating test methods or expected output:

```python
@pytest.mark.scene_files(Path("scene_files") / "Cone.vpb")
@pytest.mark.parametrize("quality", ["Off", "Low", "Medium", "High", "Ultra High"])
def test_submitter_dialog_ss_quality(self, quality):
    self._run_submitter_dialog_field_value_compare_test(
        "supersampling_quality",
        "Cone.vpb",
        {
            ...
            "SSQuality": quality,
        },
    )
```

Each parametrized value runs as a separate test case, all sharing the same base template logic.

### Adding a New Scene File

If your test requires a new scene file:

1. Place the `.vpb` file in `scene_files/`
2. Create a `_base_asset_{SceneName}.yaml` in `expected_output/bundle/` with the default asset references for that scene
3. Use `@pytest.mark.scene_files(Path("scene_files") / "YourScene.vpb")` on the test
4. If the new scene needs different base parameter defaults, consider whether a per-test expected folder is more appropriate

## Notes

- Test output directories are automatically cleaned up before and after test runs
- All tests use the same shared scene files and helper modules
- Expected outputs are separated by type (bundle vs render) for clarity
