# Changelog Guidelines

This document provides formal guidance on structuring and writing changelog entries for the AWS Deadline Cloud for VRED repository.

## Table of Contents

* [Changelog Structure](#changelog-structure)
* [Writing Guidelines](#writing-guidelines)
* [Breaking Changes](#breaking-changes)
* [Deprecations](#deprecations)
* [Features](#features)
* [Bug Fixes](#bug-fixes)
* [Performance Improvements](#performance-improvements)
* [Experimental](#experimental)
* [Fixes to Unreleased Changes](#fixes-to-unreleased-changes)
* [Examples](#examples)
* [Review Checklist](#review-checklist)

## Changelog Structure

Each release in the changelog MUST follow this standardized section order:

1. **BREAKING CHANGES** (if applicable)
2. **DEPRECATIONS** (if applicable)
3. **Features**
4. **Bug Fixes**
5. **Performance Improvements** (if applicable)
6. **Experimental** (if applicable)

### Section Descriptions

**BREAKING CHANGES**: Changes that break backward compatibility and require user action.

**DEPRECATIONS**: Features or APIs that will be removed in a future release. Users should be warned but functionality still works.

**Features**: New functionality or enhancements to existing features.

**Bug Fixes**: Corrections to defects in existing functionality.

**Performance Improvements**: Changes that improve performance without altering functionality.

**Experimental**: Features behind feature flags or marked as subject to change.

## Writing Guidelines

### General Principles

1. **User-focused language**: Write from the customer's perspective, not the implementation perspective
2. **Action-oriented**: Describe what changed and the impact, not how it was implemented
3. **Concise but complete**: Provide enough context to understand the change without being verbose
4. **Present tense**: Use present tense for describing the state after the change

## Breaking Changes

Breaking changes require special attention and MUST include:

1. **Clear description of what broke**
2. **Migration path or workaround**
3. **Code examples when applicable**

### Format

```markdown
### BREAKING CHANGES

* [Brief description of the change] (#PR) ([commit])
  * [Detailed explanation of what broke]
  * [Migration path or how to adapt]
  * [Code example if applicable]
```

### Example

```markdown
### BREAKING CHANGES

* `RenderSubmitterUISettings.RenderQuality`: The `RenderQuality` field now uses enum values instead of display strings. (#123) ([`a1b2c3d`])
  * Previously accepted display strings like `"Realistic High"`, now requires enum values like `RenderQuality.REALISTIC_HIGH`
  * **Migration**: Replace `settings.RenderQuality = "Realistic High"` with `settings.RenderQuality = RenderQuality.REALISTIC_HIGH`
```

## Deprecations

Deprecations MUST include:

1. **What is being deprecated**
2. **What to use instead**
3. **When it will be removed** (if known)

### Format

```markdown
## DEPRECATIONS

* [What is deprecated] has been deprecated. [What to use instead] should now be used. [When removal will occur if known]
```

### Example

```markdown
## DEPRECATIONS

* The `RenderSubmitterUISettings.OverrideRenderPass` field has been deprecated. Use `RenderPassSettings` with explicit pass configuration instead. This field will be removed in version 1.0.0.
```

## Fixes to Unreleased Changes

Fixes that only impact unreleased changes (changes not yet in a published release) should generally **NOT** be included in the changelog as separate entries.

### Guidelines

Fixes to unreleased changes should generally be omitted from the changelog. Instead, describe features in their final working state without mentioning intermediate bugs or fixes. The changelog is for released functionality, not development history.

### Example

Consider two commits that were merged for the same feature:

```
feat: add tile rendering functionality
fix: tile rendering fails when NumXTiles or NumYTiles exceeds 100
```

Let's assume that the `fix:` commit fixes a bug in the `feat:` commit, but the `feat:` commit had not been released before the `fix:` commit was merged.

When drafting the changelog for the release, these two changes would be merged into a single changelog entry:

**GOOD:**

```markdown
### Features
* Add tile rendering functionality with configurable tile counts
```

**BAD:**

```markdown
### Features
* Add tile rendering functionality
### Bug Fixes
* Fix tile rendering failing when NumXTiles or NumYTiles exceeds 100
```

## Features

Features should describe **what the user can now do** and when it's useful.

**Good examples:**
```markdown
* Add CLI-based installer for VRED in-app submitter
* Add sticky settings to remember render configuration between submitter sessions
* Support animation clip selection in the submitter UI
```

**Poor examples:**
```markdown
* Implemented new CLI command
* Added new function to API
* Updated UI
```

## Bug Fixes

Bug fixes should describe **the problem that was fixed** as the customer experienced it, not the technical implementation.

**Good examples:**
```markdown
* License error detection now properly identifies VRED licensing issues during rendering
* Multiple tasks no longer created when region rendering is not enabled
* Sticky settings now persist correctly between submitter dialog sessions
```

**Poor examples:**
```markdown
* Fixed a bug in the submission code
* Updated the render logic
* Changed the settings handler
```

## Performance Improvements

Performance improvements:
1. **SHOULD quantify the improvement** when possible (e.g., "2x faster", "50% reduction")
2. **MUST specify when it applies** (e.g., "for large scenes", "during job submission")

**Good examples:**
```markdown
* Improve scene asset detection by caching file reference lookups (40% faster for scenes with 100+ references)
* Speed up job bundle submissions by reducing redundant stat calls (2x faster for bundles with deep directory structures)
```

**Poor examples:**
```markdown
* Made rendering faster
* Improved performance
* Optimized code
```

## Experimental

Use a dedicated **Experimental** section at the end of the changelog for features that:
- Are behind feature flags
- Have public APIs and functional behavior under development and subject to change without following normal breaking change policies

Experimental features must be grouped under parent bullets by feature name, with specific changes as sub-bullets. When a feature group requires a feature flag, document the flag name in the parent bullet point.

### Format

```markdown
### Experimental

These changes are experimental and are subject to change.

* [Feature name] (requires `FEATURE_FLAG_NAME=true`):
  * [Specific change description]
  * [Another change for same feature]
* [Another feature name]:
  * [Change description]
```

### Example

```markdown
### Experimental

These changes are experimental and are subject to change.

* Advanced Render Settings (requires `DEADLINE_ENABLE_DEVELOPER_OPTIONS=true`):
  * Add support for custom render presets (#87) ([`e4f5g6h`])
* Batch Scene Processing:
  * Add internal functions to support multi-scene job bundles (#92) ([`i7j8k9l`])
```

### Graduating from Experimental

When a feature graduates from experimental to stable:

1. Move it to the appropriate section (Features, etc.)
2. Note that it's now stable
3. Document any API changes made during the experimental phase

**Example:**
```markdown
### Features

* Tile rendering is now stable and enabled by default (previously experimental)
  * API changes from experimental version: `render_tiles()` renamed to `render_with_tiling()`
```

## Examples

### Complete Release Example

```markdown
## 0.2.0 (2025-02-15)

### BREAKING CHANGES

* Remove deprecated `legacy_render_mode` parameter from `VREDSubmitter` (#156) ([`m1n2o3p`])
  * This parameter was deprecated in 0.1.3 and always returned a warning
  * **Migration**: Use the `render_quality` parameter instead

## DEPRECATIONS

* The `--output-format` option has been deprecated. Use `--format` instead. This option will be removed in version 1.0.0.

### Features

* Add sticky settings to remember render configuration between submitter sessions
* Support automatic download of rendered output for completed jobs
* Add detailed tooltips to grayed-out submit button explaining why submission is disabled

### Bug Fixes

* License error detection now properly identifies VRED licensing issues during rendering
* Multiple tasks no longer created when region rendering is not enabled
* Sticky settings now persist correctly between submitter dialog sessions

### Performance Improvements

* Improve scene asset detection by caching file reference lookups (40% faster for scenes with 100+ references) (#178) ([`q4r5s6t`])

### Experimental

These changes are experimental and are subject to change.

* Advanced Render Presets:
  * Add support for custom quality presets (requires `DEADLINE_ENABLE_DEVELOPER_OPTIONS=true`) (#134) ([`u7v8w9x`])
```

## Review Checklist

Before finalizing a changelog, verify:

- [ ] Sections are in the correct order
- [ ] Breaking changes describe what broke and include migration paths
- [ ] Deprecations specify what to use instead
- [ ] Bug fixes describe the problem that was fixed from the user perspective
- [ ] Performance improvements specify when they apply and ideally quantify improvements
- [ ] Experimental features are grouped by feature name with feature flags documented
- [ ] All entries are user-focused, not implementation-focused
- [ ] Fixes to unreleased changes are omitted or merged with original features
