# VRED Worker Tests

This is a test suite that exercises the Deadline Cloud VRED worker pipeline. It directly uses Job Bundle 
configurations to define settings for the rendering and tiling processes (locally) for test data using the identical 
worker pipeline code (found in: src/deadline/vred_submitter/VRED_RenderScript_DeadlineCloud.py). Rendered output is 
visually compared against expected data. This is useful for confirming whether changes in a Job Bundle, render pipeline, 
environment (etc.) are impacting expected rendering results.

## Directory Structure

### Core Test Launching Files

- **tile_assembler_test.py** - contains logic for image tile assembly using ImageMagick with parallel processing
- **vred_render_test.py** - launches VRED, loads VRED project (scene file), renders, performs render output validation

### Test Data Folders

- **expected_output/** - contains directories representing scene file and test configuration pairs, each of which 
  contains reference images for visual comparison testing.
  - ex: "Automotive_Genesis-5x2_tiles" represents a scene file "Automotive_Genesis.vbp" with a configuration "5x2_tiles"
- **job_bundles/** - contains subdirectories representing OpenJD job bundle test configurations
  - each job bundle contains: asset_references.yaml, parameter_values.yaml, template.yaml
  - ex: 5x2_tiles represents a job bundle directory for the test configuration "5x2_tiles"
- **scene_files/** - contains VRED scene files (.vpb) and dependent files (for file referencing)
  - ex: LightweightWith Spaces.vpb, test.wire
- **tiles/** - contains subdirectories representing pre-rendered tiled images
  - these subdirectories are named by scene filename and test configuration pairs (as above)

## Prerequisites

### Environment Variables

Before invoking the test suite, please set these environment variables as appropriate, substituting for the intended 
VRED version below:

- **VREDCORE** or **VREDPRO** (Path to VRED executable)
    - Linux: `/opt/Autodesk/VREDCluster-[version]/bin/VREDCore`
    - Windows: `C:/Program Files/Autodesk/VREDPro-[version]/bin/WIN64/VREDCore.exe`
- **MAGICK—** (Path to ImageMagick static-linked binary (for tile assembly))
    - Windows: `C:\Program Files\ImageMagick-[version]-Q16\magick.exe`
    - Linux: `/usr/local/bin/magick`

### Dependencies

Please install these dependencies:

- VRED Core or Pro (version 2025+) - https://www.autodesk.com/products/vred/overview
- ImageMagick (version 7+) - https://imagemagick.org/script/download.php

## Usage: Running Tests

### Batch Test Invocation

```
# Tile Assembly Tests
run-tile-assembler-tests.bat
./run-tile-assembler-tests.sh

# VRED Rendering Tests
run-vred-render-tests.bat
./run-vred-render-tests.sh
```

```
# Tile Assembly Test
python tile_assembler_test.py [test configuration]

# VRED Rendering Test
python vred_render_test.py [test configuration] [scene_file]
```

## Test Configurations

### Job Bundle Parameters

Each test configuration includes these (and many additional settings):

- **Animation Settings**: Frame ranges, step size, frames per task
- **Render Settings**: Resolution quality, image format, etc.
- **Tiling Settings**: NumXTiles (number of horizontal tiles), NumYTiles (number of vertical tiles) for distributed
rendering by tile per frame. Note: tile assembly creates combined frames from individual tiles.

## Test Validation

### Image Comparison Process

- Begins with a cleared output folder (which you manage)
- Generated images are stored in temporary output directories (within an "output" subdirectory)
- Compares all generated image output against expected reference images
  - This is done at the directory level (expected data directory v.s. generated output directory)
  - ex: expected_output/Cone-7x5_tiles/* v.s. output/Cone-7x5_tiles/*
- Applies a similarity factor for visual comparison, printing a PASS/FAIL result
- Note: supports Unicode filenames and special characters

## Output Examples

```
./run-tile-assembler-tests.sh

Deadline Cloud for VRED (Tile Assembler Test)
=============================================
Test configuration (job bundle): 7x5_tiles
Image comparison match across both folders: PASS

./run-vred-render-tests.sh

Deadline Cloud for VRED (Worker Render Test)
============================================
Test configuration (job bundle): one_frame
Scene file: Automotive_Genesis.vpb
Image comparison match across both folders: FAIL
```