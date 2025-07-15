# VRED Submitter Unit Tests

Comprehensive unit test suite for the VRED Deadline Cloud Submitter modules (via pytest with mocking).

## Directory Structure

```
vred_submitter/test/unit/
├── __init__.py                                    # Package initialization
├── conftest.py                                    # Pytest configuration and global mocks
├── README.md                                      # This documentation
├── requirements.txt                               # Test dependencies
├── run-unit-tests.bat                           # Windows test runner
├── run-unit-tests.sh                            # Unix/Linux test runner
├── test_assets.py                                # Asset introspection tests
├── test_data_classes.py                          # Data structure tests
├── test_qt_components.py                         # Qt UI component tests
├── test_qt_utils.py                              # Qt utility function tests
├── test_scene.py                                 # Scene management tests
├── test_ui_components_scene_settings_callbacks.py # UI callback tests
├── test_ui_components_scene_settings_populator.py # UI populator tests
├── test_ui_components_scene_settings_widget.py   # UI widget tests
├── test_utils.py                                 # General utility tests
├── test_vred_logger.py                           # Logging system tests
├── test_vred_submitter.py                        # Main submitter tests
└── test_vred_utils.py                            # VRED-specific utility tests
```

## Prerequisites

- Python 3.10+
- pytest 8.1.1+
- PyYAML (real YAML processing, not mocked)
- boto3 (for AWS integration tests)

## Dependencies

Install from requirements.txt:
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install pyyaml pytest boto3
```

## Usage


### Run All Tests
```bash
# Windows
run-unit-tests.bat

# Unix/Linux/Mac
./run-unit-tests.sh
```

### Run Specific Test Modules
```
python -m pytest test_utils.py
```



### Testing Configuration and Mocking

**conftest.py** - contains the global test/mocking configuration

## Test Validation Strategies

### Exception Handling
- **FileNotFoundError**: YAML file missing scenarios
- **TypeError**: Invalid data type validation
- **ValueError**: Invalid parameter ranges
- **PermissionError**: File access restrictions
- **yaml.YAMLError**: Malformed YAML content

### Edge Case Coverage
- Empty strings, None values, empty collections
- Numeric edge cases: NaN, infinity, negative infinity
- Platform differences: Windows vs Unix path separators
- Unicode filename validation
- Large file handling and memory constraints

### Mock Verification
- Function call counts and arguments
- Return value consistency
- Side effect validation
- State change verification

## Test Execution Examples

### Successful Full Test Run
```
============================= test session starts =============================
platform win32 -- Python 3.10.0, pytest-8.1.1, pluggy-1.4.0
rootdir: C:\DeadlineCloudSubmitter\Submitters\VRED\scripts\deadline\vred_submitter\test\unit
plugins: anyio-4.6.2.post1, cov-6.2.1, typeguard-2.13.3
collecting ... 
collected 120 items

test_assets.py::TestAssetIntrospector::test_parse_scene_assets PASSED    [  1%]
test_assets.py::TestAssetIntrospector::test_parse_scene_assets_empty_references PASSED [  2%]
test_utils.py::TestNamedValue::test_init PASSED                          [  3%]
test_utils.py::TestGetYamlContents::test_valid_yaml PASSED               [ 15%]
test_utils.py::TestIsNumericallyDefined::test_not_numerically_defined PASSED [ 30%]
test_vred_utils.py::TestVredUtils::test_get_dlss_quality PASSED          [ 45%]
test_vred_utils.py::TestVredUtils::test_get_supersampling_quality PASSED [ 60%]
test_vred_logger.py::TestVREDLogger::test_get_log_file_path_default PASSED [ 75%]
...

============================= 120 passed in 0.45s ==============================
```

### Individual Module Results
```
# Utils module (comprehensive utility testing)
$ pytest test_utils.py -v
============================= 40 passed in 0.08s ==============================

# VRED utilities (VRED API integration)
$ pytest test_vred_utils.py -v
============================= 50 passed in 0.12s ==============================

# Asset management
$ pytest test_assets.py -v
============================= 2 passed in 0.06s ==============================
```


### Coverage Summary
- **Core Utilities**: 40/40 tests passing (100%)
- **VRED Integration**: 50/50 tests passing (100%)
- **Asset Management**: 2/2 tests passing (100%)
- **Logging System**: 8/8 tests passing (100%)
- **Qt Components**: Mocked for isolation testing
- **Total Coverage**: 120+ unit tests with comprehensive edge case validation

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure `conftest.py` mocking is properly configured
2. **Path Failures**: Use `pathlib.Path` for cross-platform compatibility
3. **Mock Conflicts**: Check mock setup order in `conftest.py`
4. **YAML Errors**: Real PyYAML is used - ensure proper exception handling
5. **Qt Test Failures**: Verify MockQtWidget class provides required methods