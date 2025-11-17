# VRED Worker Tests

This is a test suite that exercises the Deadline Cloud VRED worker pipeline. It directly uses Job Bundle configurations to define settings for the rendering and tiling processes (locally) for test data using the identical worker pipeline code (found in: src/deadline/vred_submitter/VRED_RenderScript_DeadlineCloud.py).
Rendered output is visually compared against expected data. This is useful for confirming whether changes in a Job Bundle, render pipeline, 
environment (etc.) are impacting expected rendering results. There tests are intended to be ran on a local system that has VRED installed.

## Directory Structure

```
test/worker/
├── __init__.py                                    # Package initialization
├── path_resolver.py                               # Scene file and output path resolution
├── README.md                                      # This documentation
├── test_tile_assembler.py                         # Tile assembly tests using ImageMagick
├── test_vred_render.py                            # Direct VRED rendering tests
├── expected_output/                               # Expected test output baselines
├── job_bundles/                                   # OpenJD job bundle configurations
├── output/                                        # Generated test output (temporary, cleaned by fixture)
├── scene_files/                                   # Test scene files
└── tiles/                                         # Pre-rendered tile images for assembly tests
```

## Prerequisites

### Hardware Requirements

**GPU Requirements**: VRED rendering requires a dedicated graphics card for proper operation:

- **NVIDIA GPU**: Recommended (RTX series, Quadro, or Tesla)
- **GPU Memory**: Minimum 4GB VRAM
- **Driver Version**: NVIDIA driver 553.xx recommended for VRED 2025/2026
- **CUDA Support**: Required for GPU raytracing and DLSS features

### Environment Variables

Before invoking the test suite, please set these environment variables as appropriate, substituting for the intended 
VRED version below:

- **VREDCORE** or **VREDPRO** (Path to VRED executable)
    - Linux: `/opt/Autodesk/VREDCluster-[version]/bin/VREDCore`
    - Windows: `C:/Program Files/Autodesk/VREDPro-[version]/bin/WIN64/VREDCore.exe`
- **MAGICK** (Path to ImageMagick static-linked binary (for tile assembly))
    - Windows: `C:\Program Files\ImageMagick-[version]-Q16\magick.exe`
    - Linux: `/usr/local/bin/magick`

### Software Dependencies

- VRED Core or Pro (version 2025+) - https://www.autodesk.com/products/vred/overview
- ImageMagick (version 7+) - https://imagemagick.org/script/download.php (for tile assembly tests)
- Valid VRED licenses

## Usage: Running Tests

```
# Invocation via pytest
hatch run worker:test
```

## Test Configurations

### Job Bundle Parameters

Each test configuration includes these (and many additional settings):

- **Animation Settings**: `StartFrame`, `EndFrame`, `FrameStep`, `FramesPerTask`
- **Render Settings**: `ImageWidth`, `ImageHeight`, `OutputFormat`, `RenderQuality`
- **Tiling Settings**: `NumXTiles`, `NumYTiles`, `RegionRendering` (for distributed rendering by tile per frame)
- **Output Settings**: `OutputDir`, `OutputFileNamePrefix`
- **Advanced Settings**: `GPURaytracing`, `DLSSQuality`, `View`, `AnimationType`

## Test Validation

### Image Comparison Process

- Begins with a cleared output folder (which you manage)
- Generated images are stored in temporary output directories (within an "output" subdirectory)
- Compares all generated image output against expected reference images
  - This is done at the directory level (expected data directory v.s. generated output directory)
  - ex: expected_output/Cone-7x5_tiles/* v.s. output/Cone-7x5_tiles/*
- Applies a similarity factor for visual comparison, printing a PASS/FAIL result
- Note: supports Unicode filenames and special characters
