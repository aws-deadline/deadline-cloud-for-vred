---
inclusion: manual
---

# Deadline Cloud for VRED Architecture Guide

This guide explains the architecture of the Deadline Cloud for VRED integration to help with design decisions.

## High-Level Architecture

```
+------------------------------------------------------------------+
|                     VRED Pro (Artist Workstation)                |
|  +------------------------------------------------------------+  |
|  |                    Submitter Dialog                        |  |
|  |  - Collects job settings from user                         |  |
|  |  - Reads scene information via VRED Python API             |  |
|  |  - Creates job bundle                                      |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
                              |
                              | Job Bundle (YAML + assets)
                              v
+------------------------------------------------------------------+
|                      AWS Deadline Cloud                          |
|  - Schedules jobs                                                |
|  - Distributes tasks to workers                                  |
|  - Manages job queues                                            |
+------------------------------------------------------------------+
                              |
                              | Task assignment
                              v
+------------------------------------------------------------------+
|                    Worker (Render Node)                          |
|  +------------------------------------------------------------+  |
|  |              VRED_RenderScript_DeadlineCloud.py            |  |
|  |  - Launched by OpenJD inside VRED Core/Pro process         |  |
|  |  - Reads job parameters from environment                   |  |
|  |  - Configures render settings via VRED Python API          |  |
|  |  - Executes rendering                                      |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

## Key Difference from other DCCs

VRED does NOT use the adaptor/client pattern. Instead:
- The render script (`VRED_RenderScript_DeadlineCloud.py`) runs directly inside the VRED process
- Bootstrap code injection is used to launch the render script
- Parameters are passed via environment variables and job bundle YAML files

## Component Details

### 1. Submitter (`src/deadline/vred_submitter/`)

The submitter runs inside VRED Pro on the artist's workstation.

**Key Files:**
- `vred_submitter.py` - Main VREDSubmitter class, orchestrates job submission
- `vred_submitter_wrapper.py` - Wrapper for standalone submitter mode
- `ui/components/` - Qt UI components for the submitter dialog
- `data_classes.py` - RenderSubmitterUISettings dataclass
- `scene.py` - Scene file information and utilities
- `assets.py` - AssetIntrospector for detecting scene dependencies
- `vred_utils.py` - VRED Python API interface utilities
- `qt_utils.py` - Qt-specific utilities and helpers
- `qt_components.py` - Reusable Qt components
- `constants.py` - Shared constants
- `utils.py` - General utilities
- `default_vred_job_template.yaml` - Default job template

**Responsibilities:**
- Display job submission dialog
- Collect user settings (render quality, dimensions, animation, tiling, etc.)
- Analyze scene (viewpoints, animation clips, file references)
- Create job bundle with template, parameters, and asset references
- Submit to Deadline Cloud

### 2. UI Layer Components

#### SceneSettingsWidget
- **Purpose**: Main Qt widget container for render configuration UI
- **Key Functions**: `_build_ui()`, `update_settings()`, `eventFilter()`
- **UI Sections**: General options, render options, sequencer options, tiling settings

#### SceneSettingsCallbacks
- **Purpose**: Handles all Qt signal/slot connections and UI event responses
- **Key Functions**: `_register_all_qt_callbacks()`, `job_type_changed_callback()`, `image_size_preset_selection_changed_callback()`, `animation_clip_selection_changed_callback()`, `enable_region_rendering_changed_callback()`
- **State Management**: Persists UI settings between dialog sessions

#### SceneSettingsPopulator
- **Purpose**: Manages UI value population and persistence between sessions
- **Key Functions**: `_store_runtime_derived_settings()`, `_populate_runtime_ui_options_values()`, `_restore_persisted_ui_settings_states()`, `update_settings_callback()`

### 3. Data and Utility Components

#### RenderSubmitterUISettings
- **Purpose**: Data class containing all render job parameters
- **Categories**: Internal settings, render settings, output settings, animation settings, tiling settings, advanced settings
- **Validation**: Field types match OpenJD parameter requirements

#### AssetIntrospector
- **Purpose**: Analyzes scene files to detect asset dependencies
- **Asset Detection**: Combines scene file path with VRED file references

#### Scene
- **Purpose**: Provides scene file information and utilities
- **Animation Subclass**: Handles frame range and animation queries

### 4. Render Script (`VRED_RenderScript_DeadlineCloud.py`)

The render script runs on the worker inside the VRED process.

**Responsibilities:**
- Read job parameters from environment/bootstrap
- Configure VRED render settings
- Execute rendering (single frame or animation)
- Handle region rendering (tiling) if enabled
- Save output images

### 5. VRED Integration Layer

#### vred_utils Module
- **Purpose**: Interfaces with VRED Python API
- **Key Functions**: `get_scene_full_path()`, `get_render_filename()`, `get_frame_start()`, `get_frame_stop()`, `get_animation_clips_list()`, `get_render_quality()`, `get_render_view()`, `get_views_list()`, `get_all_file_references()`

### 6. Plugin (`vred_submitter_plugin/plug-ins/DeadlineCloudForVRED.py`)

Entry point that registers the "Deadline Cloud" menu in VRED's menu bar.

## Job Bundle

The job bundle is a directory containing:
- `template.yaml` - Job template with parameters and steps
- `parameter_values.yaml` - User-provided parameter values
- `asset_references.yaml` - Scene file and dependency references
- `scripts/VRED_RenderScript_DeadlineCloud.py` - Render script

**Template Structure:**
```yaml
specificationVersion: jobtemplate-2023-09
name: "VRED Render"
parameterDefinitions:
  - name: VREDSceneFile
    type: PATH
    objectType: FILE
  - name: Frames
    type: STRING
  - name: RenderQuality
    type: STRING
  # ... more parameters

steps:
  - name: Render
    parameterSpace:
      taskParameterDefinitions:
        - name: Frame
          type: INT
          range: "{{Param.Frames}}"
    script:
      actions:
        onRun:
          command: "..."
```

## Data Flow: Submitter to Render

### 1. Job Submission
```
User fills dialog → Submitter creates bundle → Submit to Deadline Cloud
                         |
                         +-- template.yaml (job definition)
                         +-- parameter_values.yaml (user settings)
                         +-- asset_references.yaml
                         +-- scripts/VRED_RenderScript_DeadlineCloud.py
```

### 2. Task Execution
```
Deadline Cloud assigns task to worker
         |
         v
Worker launches VRED with bootstrap code
         |
         v
VRED_RenderScript_DeadlineCloud.py executes
         |
         +-- Load scene file
         +-- Configure render settings
         +-- Set frame number
         +-- Execute render
         +-- Save output
```

## Adding a New Feature

### Step 1: Submitter Changes
1. Add UI controls to SceneSettingsWidget
2. Add callbacks to SceneSettingsCallbacks
3. Add population logic to SceneSettingsPopulator
4. Add fields to RenderSubmitterUISettings
5. Add parameters to default_vred_job_template.yaml
6. Write parameter values to bundle in VREDSubmitter

### Step 2: Render Script Changes
1. Read new parameters in VRED_RenderScript_DeadlineCloud.py
2. Configure VRED settings via VRED Python API
3. Handle the new feature during rendering

### Step 3: Utility Changes (if needed)
1. Add VRED API wrapper functions to vred_utils.py
2. Add shared utilities to utils.py

## Render Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `RenderQuality` | STRING | Analytic Low/High, Realistic Low/High, Raytracing, NPR |
| `ImageWidth` | INT | Output image width |
| `ImageHeight` | INT | Output image height |
| `OutputDirectory` | PATH | Output directory |
| `OutputFilename` | STRING | Output filename prefix |
| `OutputFormat` | STRING | PNG, EXR, JPEG, TIFF, BMP, HDR |
| `Frames` | STRING | Frame range expression |
| `AnimationType` | STRING | Clip or Timeline |
| `EnableRegionRendering` | STRING | Enable tiling |
| `TilesX` | INT | Horizontal tile count |
| `TilesY` | INT | Vertical tile count |
| `UseGPURayTracing` | STRING | Enable GPU raytracing |

## Testing Strategy

1. **Unit tests** (`test/unit/`): Mock VRED APIs, test submitter logic
2. **Submitter tests**: Automated GUI interaction, validate job bundle output
3. **Worker tests** (`test/worker/`): Execute render script with VRED, compare output images
4. **Integration tests** (`test/integ/`): End-to-end submitter-to-render validation

## Project Structure

```
src/deadline/vred_submitter/
├── ui/components/          # Qt UI components
├── vred_submitter.py       # Main submitter orchestrator
├── data_classes.py         # RenderSubmitterUISettings
├── scene.py                # Scene utilities
├── assets.py               # Asset introspection
├── vred_utils.py           # VRED Python API interface
├── qt_utils.py             # Qt utilities
├── VRED_RenderScript_DeadlineCloud.py  # Worker render script
└── default_vred_job_template.yaml      # Job template

vred_submitter_plugin/
└── plug-ins/
    └── DeadlineCloudForVRED.py  # VRED plugin entry point

test/
├── unit/                   # Unit tests
├── integ/                  # Integration tests (submitter + render)
│   ├── helpers/            # Test utilities
│   ├── scene_files/        # Test scene files
│   └── expected_output/    # Expected outputs
└── worker/                 # Worker render tests (if present)
```
