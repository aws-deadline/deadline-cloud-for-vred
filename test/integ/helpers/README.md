# VRED Test Common Utilities

This directory contains utility modules commonly used across integration tests for VRED. (`test/integ`)

## Core Module Descriptions

### vred_runner.py
Handles VRED process execution and environment setup. Locates VRED executables, generates bootstrap code, and configures appropriate environment variables to run VRED.

- Automatic VRED executable detection (VREDCore/VREDPro)
- Python bootstrap code generation and injection
- VRED environment variable configuration (licensing, web interface, etc.)
- VRED process execution and management

### submitter_dialog_controller.py
Controller for automating the VRED Submitter UI Qt dialog. Programmatically manipulates UI elements in tests to generate and validate Job Bundles.

- Submitter dialog creation and management
- Render parameter configuration (frame ranges, output paths, tiling, etc.)
- Job Bundle export
- Sticky settings save and restore testing

### load_render_parameter_values.py
Loads render parameters required for the VRED environment from YAML files. Parses the Job Bundle's `parameter_values.yaml` file to configure rendering settings.

### job_bundle_output_comparison.py
Utility for comparing generated Job Bundles against expected results. Validates that Job Bundles created in Submitter tests have the correct structure and values.

- Load YAML files from actual and expected output directories
- Path normalization considering environment-specific differences
- Template validation (`template.yaml`)
- Parameter count and value comparison (`parameter_values.yaml`)
- Asset reference filename comparison (after sorting) (`asset_references.yaml`)

### output_comparison.py
Utility for comparing rendered images and output files. Validates that render images generated in Worker tests visually match expected results.

- Image size and format validation
- Image similarity comparison using NumPy and PIL (pixel-level): similarity determination based on tolerance threshold

### sticky_settings_verification.py
Validates the Submitter UI's Sticky settings functionality. Confirms that user-configured values are properly saved and restored on subsequent runs.

- Sticky settings file (JSON) validation
- Verification of parameters that should be saved, confirmation that parameters that shouldn't be saved are excluded

## Dependencies

These utilities use the following libraries:

- **PyYAML** - YAML file parsing
- **NumPy** - Image array processing
- **Pillow (PIL)** - Image loading and comparison
- **pytest** - Test framework
