---
inclusion: manual
---

# Design Document Structure

Every design document for VRED features MUST follow this three-section structure:

## 1. Data Structures to Change or Add

Define all data model changes including:
- New dataclasses or TypedDicts
- Modifications to RenderSubmitterUISettings
- Job parameter schemas
- Configuration objects
- Type annotations

## 2. UX Changes (Submitter Dialog)

Document all user-facing changes:
- New UI controls (dropdowns, checkboxes, text fields)
- Control placement and grouping
- Default values and validation
- Tooltips and help text
- Conditional visibility logic
- SceneSettingsCallbacks changes
- SceneSettingsPopulator changes

## 3. Job Template, Render Script, and Bundle Changes

Specify modifications to:
- `default_vred_job_template.yaml` structure
- New parameters and their types
- `VRED_RenderScript_DeadlineCloud.py` changes
- Parameter dependencies and conditions
- Asset references and attachments
- VRED Python API calls needed for the feature
