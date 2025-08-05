# Development documentation

This documentation provides guidance on developer workflows for working with the code in this repository.

Table of Contents:

* [Development Environment Setup](#development-environment-setup)
* [Development Processes/Tools](#development-processestools)
    * [Submitter Development Workflow](#submitter-development-workflow)
        * [Running the Plug-In](#running-the-plug-in)
        * [Making Code Changes](#making-submitter-code-changes)
        * [Testing the Submitter](#testing-the-submitter)

## Development Environment Setup

To develop the Python code in this repository you will need:

1. Python 3.11 or higher. We recommend [mise](https://github.com/jdx/mise) if you would like to run more than one
   version of Python on the same system. When running unit tests against all supported Python versions, for instance.
2. The [hatch](https://github.com/pypa/hatch) package installed (`pip install hatch`) into your Python
   environment.
3. A supported version of VRED Pro or VRED Core with valid bring your own licensing (BYOL).
4. ImageMagick installed for tile assembly testing (download
   from [imagemagick.org](https://imagemagick.org/script/download.php)).
5. A valid AWS Account.
6. An AWS Deadline Cloud Farm to run jobs on. We recommend following the quickstart in the Deadline Cloud console to
   create a Queue with the default Queue Environment, and a Service Managed Fleet.

**Important**: VRED requires **bring your own licensing (BYOL)**. Ensure you have valid VRED licenses available for both
development and production render farm usage.

## Software Architecture

The VRED submitter plugin follows a modular architecture:

### Core Components

#### VREDSubmitter

- **Purpose**: Main orchestrator for job submission workflow
- **Key Functions**:
    - `show_submitter()`: Initializes and displays the submission dialog
    - `_create_job_bundle()`: Generates job bundle files (template.yaml, parameter_values.yaml, asset_references.yaml)
    - `_get_job_template()`: Processes default template with current settings
    - `_get_parameter_values()`: Converts UI settings to OpenJD parameter format
- **Interactions**: Creates SceneSettingsWidget, manages AssetIntrospector, interfaces with Deadline Cloud API

#### UI Layer Components

##### SceneSettingsWidget

- **Purpose**: Main Qt widget container for render configuration UI
- **Key Functions**:
    - `_build_ui()`: Constructs the complete UI layout with group boxes and controls
    - `update_settings()`: Callback invoked by Deadline Cloud API to extract current UI values
    - `eventFilter()`: Handles dialog close events and callback cleanup
- **UI Sections**: General options, render options, sequencer options, tiling settings
- **Interactions**: Manages SceneSettingsCallbacks and SceneSettingsPopulator

##### SceneSettingsCallbacks

- **Purpose**: Handles all Qt signal/slot connections and UI event responses
- **Key Functions**:
    - `_register_all_qt_callbacks()`: Connects UI elements to their respective callback methods
    - `job_type_changed_callback()`: Updates UI visibility based on render vs sequencer job types
    - `image_size_preset_selection_changed_callback()`: Handles preset selection and dimension updates
    - `animation_clip_selection_changed_callback()`: Updates frame range based on clip selection
    - `enable_region_rendering_changed_callback()`: Toggles tiling controls availability
- **State Management**: Persists UI settings between dialog sessions via `persisted_ui_settings_states`
- **Interactions**: Responds to user input, updates SceneSettingsPopulator state, triggers UI updates

##### SceneSettingsPopulator

- **Purpose**: Manages UI value population and persistence between sessions
- **Key Functions**:
    - `_store_runtime_derived_settings()`: Initializes settings from VRED scene defaults
    - `_populate_runtime_ui_options_values()`: Populates dropdown lists and UI options
    - `_restore_persisted_ui_settings_states()`: Restores previous session settings
    - `update_settings_callback()`: Converts UI values to RenderSubmitterUISettings format
- **Persistence**: Maintains `persisted_ui_settings_states` across dialog reopenings
- **Interactions**: Interfaces with VRED API via vred_utils, updates RenderSubmitterUISettings

#### Data and Utility Components

##### RenderSubmitterUISettings

- **Purpose**: Data class containing all render job parameters
- **Structure**: Synchronized with template.yaml parameter definitions
- **Categories**:
    - Internal settings (name, description, file paths)
    - Render settings (quality, dimensions, animation)
    - Output settings (format, directory, filename)
    - Advanced settings (tiling, GPU raytracing, alpha channel)
- **Validation**: Field types match OpenJD parameter requirements

##### AssetIntrospector

- **Purpose**: Analyzes scene files to detect asset dependencies
- **Key Functions**:
    - `parse_scene_assets()`: Returns set of all required asset file paths
- **Asset Detection**: Combines scene file path with VRED file references
- **Interactions**: Called by VREDSubmitter for job attachment setup

##### Scene

- **Purpose**: Provides scene file information and utilities
- **Key Functions**:
    - `name()`: Extracts scene name from file path
    - `project_full_path()`: Returns complete scene file path
    - `get_input_filenames()`: Lists input files for job submission
    - `get_output_directories()`: Determines output directory paths
- **Animation Subclass**: Handles frame range and animation queries
- **Interactions**: Used by VREDSubmitter and UI components for scene data

#### VRED Integration Layer

##### vred_utils Module

- **Purpose**: Interfaces with VRED Python API
- **Key Functions**:
    - Scene queries: `get_scene_full_path()`, `get_render_filename()`
    - Animation data: `get_frame_start()`, `get_frame_stop()`, `get_animation_clips_list()`
    - Render settings: `get_render_quality()`, `get_render_view()`, `get_views_list()`
    - File references: `get_all_file_references()`
- **Error Handling**: Manages VRED API exceptions and fallback values
- **Interactions**: Called by all components needing VRED scene data

##### qt_utils Module

- **Purpose**: Qt-specific utilities and helpers
- **Key Functions**:
    - `get_dpi_scale_factor()`: Handles high-DPI display scaling
    - `center_widget()`: Centers dialogs on screen
    - `get_qt_yes_no_dialog_prompt_result()`: Standard dialog prompts
- **UI Support**: Provides consistent Qt behavior across components

### Component Interactions

1. **Initialization**:
    - VREDSubmitter → SceneSettingsWidget → SceneSettingsCallbacks + SceneSettingsPopulator
    - SceneSettingsPopulator queries VRED via vred_utils
    - UI populated with scene defaults and persisted settings

2. **User Interaction**:
    - User modifies UI → SceneSettingsCallbacks handles events
    - Callbacks update persisted state and trigger related UI changes
    - Complex interactions (image sizing, animation clips) handled by specialized callback methods

3. **Submission**:
    - User clicks Submit → Deadline Cloud API calls `update_settings()`
    - SceneSettingsPopulator converts UI values to RenderSubmitterUISettings
    - VREDSubmitter creates job bundle with template, parameters, and assets
    - AssetIntrospector provides asset dependencies for job attachments

## Development Processes/Tools

We have configured [hatch](https://github.com/pypa/hatch) commands to support standard development. You can run the
following from any directory of this repository:

* `hatch shell` - Enter a shell environment that will have Python set up to import your development version of this
  package.
* `hatch build` - To build the installable Python wheel and sdist packages into the `dist/` directory.
* `hatch run unit:test` - To run the PyTest unit tests found in the `test/unit` directory.
* `hatch run worker:test` - (Windows only) To run the PyTest worker tests found in the `test/worker` directory.
* `hatch run integ:test` - (Windows only) To run the integration tests found in the `test/integ` directory.
* `hatch run all:test` - To run the PyTest unit tests against all available supported versions of Python.
* `hatch run lint` - To check that the package's formatting adheres to formatting standards.
* `hatch run fmt` - To automatically reformat all code to adhere to formatting standards.
* `hatch env prune` - Delete all of your isolated workspace [environments](https://hatch.pypa.io/1.12/environment/) for
  this package.

Note: Hatch uses [environments](https://hatch.pypa.io/1.12/environment/) to isolate the Python development workspace for
this package from your system or virtual environment Python. If your build/test run is not making sense, then sometimes
pruning (`hatch env prune`) all of these environments for the package can fix the issue.

### Submitter Development Workflow

The submitter plug-in generates job bundles to submit to AWS Deadline Cloud. Developing a change to the submitter
involves iteratively changing the plug-in code, then running the plug-in within VRED to generate or submit a job bundle,
inspecting the generated job bundle to ensure that it is as you expect, and ultimately running that job to ensure that
it works as desired.

#### Running the Plug-In

To run the plug-in for development:

1. Follow the installation instructions in the main README.md to set up the plug-in in VRED.

2. Set the environment variable to enable developer options:
   ```cmd
   set DEADLINE_ENABLE_DEVELOPER_OPTIONS=true
   ```

3. Start VRED and load a test scene.

4. Access the submitter through the "Deadline Cloud" menu in VRED.

You can use the "Export Bundle" option in the submitter to save the job bundle for a submission to your local disk to
inspect it, or the "Submit" button (after selecting your Deadline Cloud Farm and Queue in the submitter UI) to submit
the job to your farm to run.

#### Making Submitter Code Changes

Whenever you modify code for the plug-in, or one of its supporting Python libraries, you will need to:

1. Copy the updated files to the appropriate VRED directories as described in the installation instructions.
2. Restart VRED to reload the plug-in with your changes.

#### Testing the Submitter

The tests for the plug-in have two forms:

1. Unit tests focused on ensuring that function-level behavior of the implementation behaves as expected.
   These can always be run locally on your workstation without requiring an AWS account.
2. Integration tests - In-application tests that verify that job submissions generate expected job bundles.

##### Unit Tests

Unit tests are all located under the `test/unit` directory of this repository. If you are adding or modifying
functionality, then you will almost always want to be writing one or more unit tests to demonstrate that your logic
behaves as expected and that future changes do not accidentally break your change.

To run the unit tests, use hatch:

```bash
hatch run unit:test
```

##### Worker Tests

Worker tests are located under the `test/worker` directory and test the VRED render script and tile assembly
functionality.

To run the worker tests:

```bash
hatch run worker:test
```

##### Integration Tests

Integration tests are located under the `test/integ` directory. These tests verify that the submitter generates correct
job bundles and that the VRED render script functions properly.

To run the integration tests:

1. Ensure VRED is installed and the `VREDCORE` or `VREDPRO` environment variable is set:
   ```cmd
   set VREDCORE=C:\Program Files\Autodesk\VREDCore-18.0\bin\WIN64\VREDCore.exe
   ```
   or
   ```cmd
   set VREDPRO=C:\Program Files\Autodesk\VREDPro-18.0\bin\WIN64\VREDPro.exe
   ```

2. Run the integration tests:
   ```bash
   hatch run integ:test
   ```

The integration tests include:

- **Basic render tests** - Verify that single frame rendering with basic settings
- **Tiling tests** - Test render region assembly via ImageMagick across multiple tiles
- **Asset reference tests** - Validate scene asset dependency detection
- **Bundle comparison tests** - Compare generated job bundles against expected output

##### Test Configuration

Integration tests use scene files located in `test/integ/scene_files/` and compare output against expected baselines in
`test/integ/expected_output/`. Test parameters can be customized through parameter and asset overrides in the test
configuration.

## Environment Variables

### Required for VRED Execution

- `VREDCORE`: Path to VRED Core executable (e.g., `C:\Program Files\Autodesk\VREDCore-18.0\bin\WIN64\VREDCore.exe`)
- `VREDPRO`: Path to VRED Pro executable (e.g., `C:\Program Files\Autodesk\VREDPro-18.0\bin\WIN64\VREDPro.exe`)

### Automatic Configuration (Set by Submitter)

- `VRED_DISABLE_WEBINTERFACE`: Disables VRED web interface (set to "1")
- `VRED_IDLE_LICENSE_TIME`: License release timeout in seconds (set to "60")
- `FLEXLM_DIAGNOSTICS`: FlexLM diagnostic level for licensing  (set to "3")
- `BOOTSTRAP_CODE`: Internal code injection for render script execution

### Development and Customization

- `DEADLINE_ENABLE_DEVELOPER_OPTIONS`: Enables developer features in the submitter UI
- `CONDA_CHANNELS`: Override default conda channels for job environments
- `CONDA_PACKAGES`: Override default conda packages (default: `vredcore=2026*`)

### Required for Tile Assembly

- `MAGICK`: Path to ImageMagick executable (e.g., `C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe`)
    - **Required** for region rendering tests and tile assembly functionality
    - Download from [https://imagemagick.org/script/download.php](https://imagemagick.org/script/download.php)
    - Install 64-bit static release for best compatibility

## Submitter UI Configuration

The submitter UI is configured through parameters defined in `default_vred_job_template.yaml` and UI constants in
`ui/components/constants.py`:

### Render Parameters

- **Output settings**: directory, filename prefix, file format
- **Image settings**: width, height, DPI, size presets
- **Quality settings**: render quality, DLSS, Super Sampling
- **Animation settings**: frame range, animation type, clips
- **Tiling settings**: region rendering with configurable tile counts (requires Raytracing render quality)
- **Advanced options**: GPU raytracing, alpha channel (not exposed in UI), tone mapping (not exposed in UI)

### UI Components

- **Image size presets**: From VGA (640x480) to UHDV (7680x4320)
- **Quality options**: Analytic Low/High, Realistic Low/High, Raytracing, NPR
- **Format support**: PNG, EXR, JPEG, TIFF, BMP, HDR
- **DPI scaling**: Automatic UI scaling based on system DPI settings

### Debug Mode

Enable detailed logging by setting the log level in your test environment or by modifying the logger configuration in
the VRED submitter code.

### Parameter Validation

The submitter validates:

- Output directory existence and permissions
- Filename validity using Unicode regex patterns
- Frame range format and step values
- Image dimensions and DPI limits
- Tile count constraints for region rendering

## Worker Process Development

For local testing and development, the worker process can be invoked directly:

### Installation

```bash
pip install deadline-cloud-worker-agent
```

Reference: [deadline-cloud-worker-agent](https://github.com/aws-deadline/deadline-cloud-worker-agent)

### Running the Worker

```bash
python -m deadline_worker_agent --run-jobs-as-agent-user
```

This allows you to test job execution locally without requiring a full Deadline Cloud farm setup.

### Submitter Installer Development Workflow
#### Build the package

```bash
hatch build
```

#### Build the installer

```bash
hatch run installer:build-installer --local-dev-build --platform <PLATFORM> [--install-builder-location <LOCATION> --output-dir <DIR>]
```

Run `hatch run installer:build-installer -h` to see the full list of arguments.


#### Test a local installer
```bash
hatch run test-installer
```
