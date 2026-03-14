# Workflows

This directory contains markdown SOPs that define your agentic workflows.

## What Goes Here

Each workflow is a markdown file that describes:
- **Objective:** What you're trying to accomplish
- **Required Inputs:** What information/data is needed
- **Tools Used:** Which scripts from `tools/` to execute
- **Process Steps:** The sequence of operations
- **Expected Outputs:** Where results should go
- **Edge Cases:** How to handle failures and exceptions

## Workflow Template

```markdown
# [Workflow Name]

## Objective
What does this workflow accomplish?

## Required Inputs
- Input 1: Description
- Input 2: Description

## Tools Used
- `tool_name.py` - What it does

## Process
1. Step one
2. Step two
3. Step three

## Expected Outputs
Where do results go? (Google Sheets, files, etc.)

## Edge Cases
- Rate limits: How to handle
- Missing data: Fallback strategy
- API failures: Retry logic

## Learnings
Document improvements and discoveries here as you go.
```

## Best Practices

- Keep workflows focused on a single objective
- Update workflows when you discover better approaches
- Document rate limits and API quirks
- Include examples of inputs/outputs
- Note timing considerations (batch vs real-time)
