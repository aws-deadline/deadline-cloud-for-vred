# VRED Submitter Integration Tests

Comprehensive integration test suite for the VRED Deadline Cloud Submitter using pytest with real VRED application instances.

## Directory Structure

```
vred_submitter/test/integ/
├── __init__.py                                    # Package initialization
├── constants.py                                   # Test constants and configuration
├── output_comparison.py                           # Job bundle comparison utilities
├── path_resolver.py                               # Scene file and output path resolution
├── README.md                                      # This documentation
├── submitter_dialog_controller.py                # Qt dialog automation controller
├── test_vred_submitter.py                        # Main integration test suite
├── expected_output/                               # Expected test output baselines
│   ├── Cone-7x5_tiles/                           # Tiling test baseline
│   ├── FileReferencing-bundle_comparison/        # Asset reference test baseline
│   └── LightweightWith Spaces-basic_render/      # Basic render test baseline
├── output/                                        # Generated test output (temporary)
└── scene_files/                                   # Test scene files
    ├── Cone.vpb                                  # Simple geometry test scene
    ├── FileReferencing.vpb                       # Asset reference test scene
    ├── LightweightWith Spaces.vpb                # Basic test scene with spaces
```

## Prerequisites

- Python 3.10+
- pytest 8.1.1+
- PyYAML (for job bundle validation)
- VRED 2025+ (VRED Core or VRED Pro)

## Environment Setup

### VRED Installation
Set one of these environment variables:
```bash
# Windows
set VREDCORE=C:\Program Files\Autodesk\VREDPro-2024\bin\WIN64\VREDCore.exe
# or
set VREDPRO=C:\Program Files\Autodesk\VREDPro-2024\bin\WIN64\VREDPro.exe

# Linux
export VREDCORE=/opt/Autodesk/VREDCluster-2024/bin/VREDCore
```

### Dependencies
```bash
pip install pytest pyyaml
```

## Usage

### Run All Integration Tests
```bash
python -m pytest test_vred_submitter.py -v
hatch run integ:test
```

### Run Specific Test
```bash
python -m pytest test_vred_submitter.py::TestVREDSubmitter::test_submitter_dialog_bundle_comparison -v
```

### Run with Markers
```bash
python -m pytest -m submitter
```

## Test Architecture

### Core Components

**VREDRenderTestRunner** - Handles VRED process execution and environment setup
- Generates bootstrap code for VRED Python execution
- Manages VRED executable detection and validation
- Configures VRED environment variables

**SubmitterDialogController** - Automates Qt dialog interactions
- Creates and manages submitter dialog instances
- Sets job-specific rendering parameters via Qt widgets
- Exports job bundles and validates output files
- Handles dialog close/reopen scenarios for persistence testing

**Test Validation Framework**
- Parameter value comparison against expected baselines
- Asset reference validation with sorted filename comparison
- YAML template structure verification
- Job bundle completeness validation

### Test Data Flow

1. **Scene Loading**: Test scenes loaded from `scene_files/` directory
2. **Parameter Application**: Job settings applied via Qt dialog automation
3. **Bundle Generation**: Job bundles exported to temporary `output/` directory
4. **Validation**: Generated bundles compared against `expected_output/` baselines
5. **Cleanup**: Temporary files removed after test completion

## Test Cases

### Basic Render Test
- **Scene**: `LightweightWith Spaces.vpb`
- **Configuration**: Single frame, basic render settings
- **Validation**: Parameter values, asset references, template structure

### Tiling Test
- **Scene**: `Cone.vpb`
- **Configuration**: 7x5 tile rendering, animation frames
- **Validation**: Region rendering parameters, tile count validation

### Asset Reference Test
- **Scene**: `FileReferencing.vpb`
- **Configuration**: Multiple asset dependencies
- **Validation**: Compares asset references, file path resolution

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
- `VREDCORE` / `VREDPRO`: Path to VRED executable
- `VRED_DISABLE_WEB_INTERFACE`: Disables web interface (set automatically)
- `VRED_LICENSE_RELEASE_TIME`: License release timeout (set automatically)
- `FLEXLM_DIAGNOSTICS`: FlexLM diagnostic level (set automatically)

### Test Execution
- `VRED_PYTHON_BOOTSTRAP_CODE`: Bootstrap code injection (internal use)

## Troubleshooting

### Common Issues

1. **VRED Not Found**
   ```
   OSError: VRED executable not found
   ```
   - Verify VREDCORE or VREDPRO environment variable
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
Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Test Execution Examples

### Successful Test Run
```
============================= test session starts =============================
platform win32 -- Python 3.10.0, pytest-8.1.1
rootdir: C:\deadline-cloud-for-vred\test\integ
plugins: anyio-4.6.2.post1
collecting ... 
collected 1 items

test_vred_submitter.py::TestVREDSubmitter::test_submitter_dialog_bundle_comparison PASSED [100%]

============================= 1 passed in 45.23s ==============================
```

### Test Output Validation
```
test/integ/test_vred_submitter.py::TestVREDSubmitter::test_submitter_dialog_basic_settings
[gw0] [ 33%] PASSED test/integ/test_vred_submitter.py::TestVREDSubmitter::test_submitter_dialog_basic_settings
test/integ/test_vred_submitter.py::TestVREDSubmitter::test_submitter_dialog_tiling_settings
[gw0] [ 66%] PASSED test/integ/test_vred_submitter.py::TestVREDSubmitter::test_submitter_dialog_tiling_settings
test/integ/test_vred_submitter.py::TestVREDSubmitter::test_submitter_dialog_bundle_comparison
[gw0] [100%] PASSED test/integ/test_vred_submitter.py::TestVREDSubmitter::test_submitter_dialog_bundle_comparison
```