---
inclusion: manual
---

# VRED Design Workflow Guide

This guide walks through creating a comprehensive design document for a new VRED feature.

## Step 1: Understand the Feature Request

Before starting the design:
1. Clarify the user's goal and expected outcome
2. Identify which VRED components are affected (submitter UI, render script, job template)
3. Determine if this is a new feature or modification to existing behavior
4. Ask clarifying questions if the scope is unclear

## Step 2: Research Phase

### 2.1 Check Existing VRED Implementation

Review the current codebase:
- `src/deadline/vred_submitter/` - Submitter code
- `src/deadline/vred_submitter/ui/components/` - UI components
- `src/deadline/vred_submitter/data_classes.py` - Data structures
- `src/deadline/vred_submitter/vred_utils.py` - VRED API wrappers
- `src/deadline/vred_submitter/VRED_RenderScript_DeadlineCloud.py` - Render script
- `src/deadline/vred_submitter/default_vred_job_template.yaml` - Job template

### 2.2 Internet Research

Search for:
- VRED Python API documentation
- Community solutions and workarounds
- Known issues and limitations

## Step 3: Design the Data Structures

Data structures anchor the design - **always include full definitions** for new types:

```python
from typing import Optional
from dataclasses import dataclass

@dataclass
class FeatureSettings:
    """Settings for Feature X workflow."""
    
    enabled: bool = False
    output_path: Optional[str] = None
```

Consider:
- What data flows from submitter to render script?
- What fields need to be added to RenderSubmitterUISettings?
- What types should be used?

## Step 4: Design the UX

Sketch out the submitter dialog changes:

1. **Control Type**: Dropdown, checkbox, text field, etc.
2. **Placement**: Which group/section does it belong to?
3. **Default Value**: What's the sensible default?
4. **Validation**: What values are valid?
5. **Dependencies**: Does it depend on other settings?

Example:
```
Group: Render Options
├── [Checkbox] Enable Feature X (default: unchecked)
│   └── [Dropdown] Feature X Mode (visible when enabled)
│       ├── Option A
│       └── Option B
└── [Text Field] Custom Path (optional)
```

## Step 5: Design Job Template Changes

Define the job bundle modifications:

```yaml
parameterDefinitions:
  - name: FeatureXEnabled
    type: STRING
    default: "false"
    allowedValues: ["true", "false"]
    
  - name: FeatureXMode
    type: STRING
    default: "option_a"
    allowedValues: ["option_a", "option_b"]
    userInterface:
      control: DROPDOWN
      label: "Feature X Mode"
```

## Step 6: Design Render Script Changes

Plan the render script implementation using concise inline snippets:

```python
# In VRED_RenderScript_DeadlineCloud.py
def configure_feature_x(params):
    """Configure Feature X before rendering."""
    if params.get("FeatureXEnabled") == "true":
        # VRED API calls here
        ...
```

## Step 7: Plan Testing

Define tests:

```python
def test_feature_x_job_bundle():
    """Test Feature X parameters appear in job bundle."""
    # Setup submitter with feature X enabled
    # Export bundle
    # Verify parameters in template.yaml and parameter_values.yaml

def test_feature_x_rendering():
    """Test Feature X produces correct output."""
    # Load job bundle with feature X parameters
    # Execute render script
    # Compare output against expected
```

## Step 8: Document Files to Modify

Create a summary table:

| File | Changes |
|------|---------|
| `src/deadline/vred_submitter/ui/components/...` | Add UI controls |
| `src/deadline/vred_submitter/data_classes.py` | Add settings fields |
| `src/deadline/vred_submitter/default_vred_job_template.yaml` | Add parameters |
| `src/deadline/vred_submitter/VRED_RenderScript_DeadlineCloud.py` | Add render logic |
| `src/deadline/vred_submitter/vred_utils.py` | Add VRED API wrappers |
| `test/unit/...` | Add unit tests |

## Common Pitfalls

1. **Forgetting standalone submitter**: Changes may need to work in both VRED-embedded and standalone modes
2. **Missing type annotations**: All code needs proper types
3. **No error handling**: VRED API operations can fail
4. **Untested edge cases**: Test with missing/invalid data
5. **Tiling interactions**: New features may interact with region rendering
6. **Animation interactions**: Consider how the feature behaves with animation clips vs timeline

## Step 9: Create the Appendix

Put all full code implementations in a clearly marked appendix at the end of the design document.

### Appendix Format

```markdown
---

## Appendix: Full Code Implementations

<!-- REVIEW: Brief description of what's new -->

### A.1 ClassName.method_name (Full Implementation)

**File:** `src/deadline/vred_submitter/...`

\`\`\`python
def method_name(self, data: dict) -> None:
    """Full docstring here."""
    # Complete implementation
    ...
\`\`\`
```
