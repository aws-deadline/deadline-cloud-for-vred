---
name: "vred-design-power"
displayName: "VRED Design Power"
description: "Structured design assistant for VRED features in Deadline Cloud. Creates comprehensive design documents covering data structures, UX changes, job templates, and render script modifications."
keywords: ["vred", "design", "submitter", "render", "tiling"]
author: "AWS Deadline Cloud Team"
---

# VRED Design Power

## Overview

> **Terminal Output Pattern:** When running PowerShell commands that produce output you need to verify, always pipe to a temp file (`<command> | Out-File "deadline-cloud-for-vred\_check_result.txt" -Encoding utf8`), read it with `readFile`, then delete it. This avoids terminal output parsing issues.

A structured design assistant for creating comprehensive feature designs for VRED integration with AWS Deadline Cloud. This power helps create well-structured design documents following a consistent format that covers all aspects of implementation.

## Code Snippet Style Guide

When including code in design documents, use **concise inline snippets** in the main sections and put **full implementations in an appendix**.

### Inline Code Format

Show only the relevant changes with context:

```python
def existing_function():
    ...existing logic...
    
    # NEW: Add feature X support
    if feature_x_enabled:
        self._configure_feature_x(data)
    
    ...rest of function...
```

### Appendix Format

Put complete implementations in a clearly marked appendix section:

```markdown
---

## Appendix: Full Code Implementations

<!-- REVIEW: New render script change -->

### A.1 RenderScript.configure_feature (Full Implementation)

\`\`\`python
def configure_feature(self, data: dict) -> None:
    """Full implementation here..."""
    # Complete code
\`\`\`
```

### Guidelines

1. **Data structures are the exception**: Always show full definitions - they anchor the design
2. **Other sections**: Show what changes and where, not full implementations
3. **Use `...` or comments** to indicate existing/unchanged code
4. **Flag new sections** with `<!-- REVIEW: description -->` comments in the appendix
5. **Don't include review tags** in final generated code

## Research Requirements

Before finalizing any design, research VRED Python APIs and existing implementation patterns. Refer to **research-guide.md** for details.

## External References

Refer to **external-references.md** for GitHub links and documentation.
