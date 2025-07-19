# DhafnckMCP Issues Fix Prompts

## Issue 1: Subtask insights_found Parameter Format

### Context
When completing a subtask using the manage_subtask tool with action="complete", the insights_found parameter causes a validation error when passed as an array.

### Error Details
```
Input validation error: '["RS256 is more secure than HS256 for distributed systems", "Token rotation prevents long-term token theft", "httpOnly cookies prevent XSS attacks on refresh tokens"]' is not valid under any of the given schemas
```

### Fix Request Prompt
```
I need help fixing the insights_found parameter validation in the manage_subtask tool. Currently, when I try to complete a subtask with:

mcp__dhafnck_mcp_http__manage_subtask(
    action="complete",
    task_id="eb8f43ab-ff63-49b8-9078-9d2c1b660308",
    subtask_id="d2102186-373f-469c-bc71-28c668005f16",
    completion_summary="Successfully researched JWT best practices...",
    insights_found=["RS256 is more secure than HS256 for distributed systems", "Token rotation prevents long-term token theft", "httpOnly cookies prevent XSS attacks on refresh tokens"]
)

I get a validation error. The parameter appears to not accept arrays as expected. 

Please investigate and fix the following:
1. Check the parameter definition for insights_found in manage_subtask_description.py
2. Verify if it should accept arrays/lists or if it expects a different format
3. Update either the parameter definition or the validation to properly handle arrays of insights
4. Ensure the documentation reflects the correct format

The insights_found parameter should logically accept multiple insights as an array since subtasks can generate multiple learnings.
```

---

## Issue 2: Task Dependencies Display Consistency

### Context
After adding dependencies between tasks using add_dependency action, the dependency information is not consistently displayed in task responses.

### Observation
- Dependencies are successfully added (confirmed by response)
- However, the dependency_relationships field shows as empty in some responses
- The system appears to track dependencies but display is inconsistent

### Fix Request Prompt
```
I need help fixing the dependency display consistency in task responses. When I add dependencies using:

mcp__dhafnck_mcp_http__manage_task(
    action="add_dependency",
    task_id="eb8f43ab-ff63-49b8-9078-9d2c1b660308",
    dependency_id="ca8725c4-0e20-4675-a158-af62e22edfbe"
)

The dependency is added successfully, but when I later retrieve the task with action="get" or "list", the dependency_relationships field sometimes shows as empty or null.

Please investigate and fix:
1. Check if dependencies are being properly loaded in the task retrieval logic
2. Ensure the dependency_relationships field is populated in all task responses (get, list, search, next)
3. Verify the TaskDependencyService is being called correctly in all use cases
4. Add consistent dependency information to the task entity responses

Expected behavior: All task responses should include populated dependency_relationships showing depends_on, blocks, and dependency_chains information.
```

---

## Issue 3: Documentation Enhancement for Parameter Formats

### Context
The workflow guidance is excellent but could be clearer about exact parameter formats, especially for complex parameters that might accept multiple formats.

### Enhancement Request Prompt
```
I'd like to enhance the parameter documentation in the workflow guidance responses. Currently, some parameters like insights_found, assignees, and labels are ambiguous about their expected formats.

Please enhance the parameter_guidance sections to include:
1. Exact type expectations (string, array, comma-separated string, etc.)
2. Multiple format examples if the parameter accepts various formats
3. Clear indication of which formats are preferred
4. Validation rules and constraints

For example, enhance documentation for:
- insights_found: Should clarify if it accepts arrays, comma-separated strings, or other formats
- assignees: Should show examples of single string, array of strings, or comma-separated format
- labels: Similar clarification needed
- dependencies: When creating tasks, what formats are accepted?

This will help users understand exactly how to format their parameters without trial and error.
```

---

## Minor Enhancement: Progress Bar Visualization

### Context
The system tracks progress well but could benefit from visual progress indicators in responses.

### Enhancement Request Prompt
```
As a minor enhancement, it would be helpful to add visual progress bars to task and subtask responses. For example:

Instead of just showing:
- completion_percentage: 75

Also include:
- progress_bar: "████████████████░░░░  75%"

This would make it easier to quickly visualize progress at a glance in the terminal output.
```