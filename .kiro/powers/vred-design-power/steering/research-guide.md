---
inclusion: manual
---

# Research Guide for VRED Designs

This guide covers how to research and validate design decisions for VRED features.

## VRED Documentation Sources

### Official Autodesk Documentation

1. **VRED Python API**
   - Search: "VRED Python API [topic]"
   - Covers: VRED Python modules and functions

2. **VRED System Requirements**
   - URL: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/System-requirements-for-Autodesk-VRED-2026-products.html
   - Note: Autodesk websites are JS-rendered and may not be fetchable by web tools. If fetching fails, prompt the user to copy paste page contents, or use webscraping tools.

## VRED Python API Patterns

VRED exposes Python APIs through modules like `vrController`, `vrFileIO`, `vrRenderSettings`, etc. These are available when running inside the VRED process.

### Common VRED API Modules

| Module | Purpose |
|--------|---------|
| `vrController` | Application control, scene management |
| `vrFileIO` | File I/O operations |
| `vrRenderSettings` | Render configuration |
| `vrCamera` | Camera/viewpoint management |
| `vrScenegraph` | Scene graph access |
| `vrNodeUtils` | Node utilities |

### Bootstrap Code Injection

VRED tests and the render script use bootstrap code injection to execute Python code inside VRED:

```python
# Bootstrap code is passed via BOOTSTRAP_CODE environment variable
# VRED executes it on startup, which imports and runs the target module
import os
bootstrap = os.environ.get("BOOTSTRAP_CODE", "")
if bootstrap:
    exec(bootstrap)
```

## Key Integration Patterns

### Scene File Access
```python
# Get current scene file path
scene_path = vred_utils.get_scene_full_path()
```

### Render Settings
```python
# Get render quality, dimensions, etc.
quality = vred_utils.get_render_quality()
width, height = vred_utils.get_image_width(), vred_utils.get_image_height()
```

### Animation Data
```python
# Get animation information
clips = vred_utils.get_animation_clips_list()
start = vred_utils.get_frame_start()
stop = vred_utils.get_frame_stop()
```

### File References
```python
# Get all file references for asset introspection
references = vred_utils.get_all_file_references()
```

## Internet Research Guidelines

### When to Search

1. Documentation is unclear or incomplete
2. Looking for version-specific behavior
3. Finding community workarounds
4. Verifying API behavior

### Effective Search Queries

- `"VRED" "Python API" "[feature]"`
- `"VRED" "render settings" "[property]"`
- `"Autodesk VRED" "[topic]" site:forums.autodesk.com`

## Knowledge Gap Protocol

When you encounter a knowledge gap:

1. **Document what you know**
   - What API/feature is involved?
   - What have you found so far?
   - What specific information is missing?

2. **Ask the user clearly**
   > "I need clarification on [topic]. Specifically:
   > - [Question 1]
   > - [Question 2]
   > 
   > Do you have documentation or code examples for this?"

3. **Don't guess** - It's better to leave a gap clearly marked than to fill it with incorrect information. We can always add more detail later.
