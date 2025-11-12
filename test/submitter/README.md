# VRED Submitter Integration Tests

Comprehensive integration test suite for the VRED Deadline Cloud Submitter using pytest with real VRED application instances.

**Test Process**: Each test opens VRED Pro, loads a test scene, applies specific settings through the submitter dialog, exports a job bundle, and validates the bundle contents against expected output files.
Submitter tests use scene files located in `test/submitter/scene_files/` and compare output against expected baselines in `test/submitter/expected_output/`. Test parameters are configured through parameter overrides passed to the submitter dialog controller.

The submitter tests include:

- **Job bundle generation tests** - Verify that VRED submitter UI can generate valid job bundles with correct structure
- **Render settings validation tests** - Validate that various render settings (tiling, GPU raytracing, DLSS, output formats, render quality) are properly applied through Qt dialog automation
- **Asset reference validation tests** - Ensure scene asset dependencies are correctly detected and included in job bundles
- **Sticky settings tests** - Ensure user-configured values are properly saved to sticky settings files and can be restored
- **Parameter comparison tests** - Compare generated parameter values against expected baselines for different render configurations

**Note**: This test requires opening VRED Pro and directly interacting with the Deadline Cloud submitter UI, so it can only be executed on a Windows system that supports VRED Pro.


## Directory Structure

```
test/submitter/
├── __init__.py                                    # Package initialization
├── path_resolver.py                               # Scene file and output path resolution
├── README.md                                      # This documentation
├── test_vred_submitter.py                         # Main submitter test suite
├── expected_output/                               # Expected test output baselines
├── output/                                        # Generated test output (temporary, cleaned by fixture)
└── scene_files/                                   # Test scene files
```

## Prerequisites

- Python 3.10+
- pytest 8.1.1+
- PyYAML (for job bundle validation)
- VRED 2025+ (VRED Pro)
- Deadline Cloud for VRED submitter installed

### Environment Setup

- Set the VRED Pro environment variable:
   ```bash
   # Windows
   set VREDPRO=C:\Program Files\Autodesk\VREDPro-2025\bin\WIN64\VREDPro.exe
   ```

- **VRED License Setup**: Ensure valid VRED licenses are configured before running tests:
   - **Verify**: Launch VRED manually to confirm licensing works
   - If VRED fails to start due to licensing, consult your license administrator or Autodesk documentation

- **Output Directory**: The tests use a hardcoded output directory path for the rendered images, which is set to `"C:\\vred-snapshots"`. Ensure that this path actually exists on the local where the test is being executed. Alternatively, replace the hardcoded path with a directory that does exist on the local.

### Dependencies
```bash
pip install pytest pyyaml
```

## Usage

### Run All Submitter Tests
```bash
hatch run submitter:test
```

### Run with Markers
```bash
python -m pytest -m submitter
```

## Test Architecture

### Core Components

**VREDRunner** (from `test/common/vred_runner.py`) - Handles VRED process execution and environment setup
- Generates bootstrap code for VRED Python execution
- Manages VRED executable detection and validation
- Configures VRED environment variables (licensing, web interface, etc.)

**SubmitterDialogController** (from `test/common/submitter_dialog_controller.py`) - Automates Qt dialog interactions
- Creates and manages submitter dialog instances
- Sets job-specific rendering parameters via Qt widgets
- Exports job bundles and validates output files
- Handles sticky settings save and restore

**PathResolver** - Resolves file paths for test resources
- Locates scene files in `scene_files/` directory
- Resolves expected output folders based on test configuration and scene name

**Test Validation Framework** (from `test/common/`)
- Parameter value comparison against expected baselines (`job_bundle_output_comparison.py`)
- Sticky settings file validation (`sticky_settings_verification.py`)
- YAML template structure verification
- Job bundle completeness validation

### Test Data Flow

1. **Setup**: Module-scoped fixture cleans output directory before tests
2. **Scene Loading**: Test scenes loaded from `scene_files/` directory
3. **Parameter Application**: Job settings applied via Qt dialog automation using `test_settings` list
4. **Bundle Generation**: Job bundles exported to `output/{scene_basename}-{test_name}/` directory
5. **Validation**: Generated bundles compared against `expected_output/` baselines
6. **Sticky Settings Verification**: Verify sticky settings file was created and contains correct values
7. **Cleanup**: Module-scoped fixture removes output directory after all tests complete

## Test Configuration Options

### Parameter Overrides - Example:
```python
parameter_overrides = {
    "EndFrame": 25,
    "OutputDir": "c:\\vred-snapshots",
    "OutputFileNamePrefix": "image",
    "RenderAnimation": "false",
    "View": "Back"
}
```

### Asset Overrides - Example:
```python
asset_overrides = [
    'C:\\WorkArea\\test.wire',
    'C:\\WorkArea\\Only\\LightweightWithoutSpaces.vpb'
]
```

## Environment Variables

### VRED Configuration
- `VREDPRO`: Path to VRED Pro executable (required)
- `VRED_DISABLE_WEBINTERFACE`: Disables web interface (set automatically by VREDRunner)
- `VRED_LICENSE_RELEASE_TIME`: License release timeout (set automatically)
- `FLEXLM_DIAGNOSTICS`: FlexLM diagnostic level (set automatically)

### Test Execution
- `BOOTSTRAP_CODE`: Bootstrap code injection for VRED Python environment (internal use)

## Troubleshooting

### Common Issues

1. **VRED Not Found**
   ```
   OSError: VRED executable not found
   ```
   - Verify VREDPRO environment variable
   - Check VRED installation path and permissions

2. **Dialog Creation Failed**
   ```
   Failed to create submitter dialog
   ```
   - Ensure Qt application can initialize
   - Check VRED Python environment compatibility

3. **Asset Reference Mismatch**
   ```
   AssertionError: asset references don't match
   ```
   - Verify scene file asset dependencies
   - Check asset override configuration

4. **Bundle Export Failed**
   ```
   Expected bundle file(s) not found
   ```
   - Verify output directory permissions
   - Check job bundle generation process

### Debug Mode
Enable detailed logging in test file:
```python
logging.basicConfig(format="%(message)s", level=logging.DEBUG)
```
