# Template System with Glob Patterns

This directory contains templates that agents can use to generate consistent documentation and files across the project. Each template includes glob patterns that specify which files or folders the generated documentation applies to.

## 📁 Directory Structure

```
.cursor/templates/
├── documents/           # Document templates
│   ├── technical_spec.md.template
│   ├── api_documentation.md.template
│   └── component_documentation.md.template
├── code/               # Code templates (future)
├── rules/              # Rule templates (future)
├── meta/               # Template metadata
│   ├── template_registry.json
│   └── template_schema.json
└── README.md           # This file
```

## 🎯 Glob Patterns in Templates

### What are Glob Patterns?
Glob patterns specify which files or directories a document is relevant to. This helps agents understand:
- **When to reference the document** (when working on matching files)
- **What files the document covers** (scope of documentation)
- **How to organize documentation** (by file type/location)

### Common Glob Patterns

| Pattern | Description | Example Files |
|---------|-------------|---------------|
| `src/api/**/*` | All API-related files | `src/api/users.js`, `src/api/auth/login.js` |
| `src/components/**/*` | All component files | `src/components/Button.tsx`, `src/components/forms/Input.vue` |
| `**/*.test.*` | All test files | `src/utils.test.js`, `tests/integration.test.ts` |
| `*.config.*` | All configuration files | `webpack.config.js`, `jest.config.json` |
| `docs/**/*` | All documentation files | `docs/api.md`, `docs/guides/setup.md` |

### Template-Specific Patterns

#### API Documentation (`api_documentation_v1`)
**Default Globs**: `src/api/**/*,src/routes/**/*,src/controllers/**/*,src/handlers/**/*`
- Covers: REST endpoints, GraphQL resolvers, route handlers, middleware
- Use when: Documenting APIs, endpoints, request/response formats

#### Component Documentation (`component_documentation_v1`)
**Default Globs**: `src/components/**/*,src/ui/**/*,src/views/**/*,src/pages/**/*`
- Covers: React/Vue/Angular components, UI elements, pages, views
- Use when: Documenting frontend components, props, styling

#### Technical Specification (`technical_spec_v1`)
**Default Globs**: `src/**/*,docs/**/*`
- Covers: All source code and existing documentation
- Use when: Creating comprehensive technical specifications

## 🛠️ Using Templates with Glob Patterns

### 1. Agent Workflow Integration

When an agent works on files, it can:
1. **Check which templates apply** to the current file path
2. **Load relevant documentation** automatically
3. **Generate context-aware documentation** using appropriate templates

```python
# Example: Agent working on src/components/Button.tsx
file_path = "src/components/Button.tsx"

# Find applicable templates
applicable_templates = find_templates_for_path(file_path)
# Returns: ["component_documentation_v1", "general_document_v1"]

# Load documentation for context
docs = load_documentation_for_templates(applicable_templates)
# Agent now has component documentation context
```

### 2. Template Selection Logic

```python
def select_template_for_task(task, file_paths):
    """Select the most appropriate template based on task and file paths"""
    
    # Check file patterns
    if any("src/api/" in path for path in file_paths):
        return "api_documentation_v1"
    elif any("src/components/" in path for path in file_paths):
        return "component_documentation_v1"
    elif task.category == "technical":
        return "technical_spec_v1"
    else:
        return "general_document_v1"
```

### 3. Context-Aware Documentation

```python
def generate_documentation(template_id, context):
    """Generate documentation with glob-aware context"""
    
    template = load_template(template_id)
    
    # Add glob-specific context
    context["globs"] = template.default_globs
    context["relevant_files"] = find_files_matching_globs(template.default_globs)
    context["file_analysis"] = analyze_matching_files(context["relevant_files"])
    
    return process_template(template, context)
```

## 📋 Template Variables

### Standard Variables
All templates support these variables:
- `{{title}}` - Document title
- `{{author}}` - Document author (agent name)
- `{{project.name}}` - Project name
- `{{project.id}}` - Project ID
- `{{system.timestamp}}` - Generation timestamp
- `{{system.git_branch}}` - Current git branch

### Glob-Specific Variables
- `{{globs}}` - Glob patterns for the template
- `{{relevant_files}}` - Files matching the glob patterns
- `{{file_analysis}}` - Analysis of matching files

### Task-Specific Variables
- `{{task.id}}` - Task ID
- `{{task.title}}` - Task title
- `{{task.description}}` - Task description
- `{{task.status}}` - Task status
- `{{task.assignee}}` - Assigned agent

## 🎨 Creating Custom Templates

### 1. Template Header
```yaml
---
template_id: "my_custom_template_v1"
template_name: "My Custom Template"
template_version: "1.0.0"
template_type: "document"
template_category: "custom"
created_by: "agent_name"
created_at: "2025-01-27T10:30:00Z"
usage_scenarios: ["Scenario 1", "Scenario 2"]
required_variables: ["title", "author", "project_id"]
optional_variables: ["task_id", "custom_field", "globs"]
output_format: "markdown"
validation_rules: ["title_required", "author_required"]
globs: "{{globs | default: 'custom/**/*'}}"
---
```

### 2. Template Body
```markdown
# {{title}}

**Information:**
- **Author**: {{author}}
- **Created**: {{system.timestamp}}
{{#if globs}}
- **Applies to**: `{{globs}}`
{{/if}}

## Content
{{content | default: "Add your content here"}}

## Related Files
{{#each relevant_files}}
- `{{this}}`
{{/each}}
```

### 3. Register Template
Add to `.cursor/templates/meta/template_registry.json`:
```json
{
  "my_custom_template_v1": {
    "id": "my_custom_template_v1",
    "name": "My Custom Template",
    "path": ".cursor/templates/documents/my_custom.md.template",
    "category": "custom",
    "default_globs": "custom/**/*",
    // ... other metadata
  }
}
```

## 🔍 Glob Pattern Best Practices

### 1. Be Specific but Flexible
```bash
# Good: Specific to API files
src/api/**/*,src/routes/**/*

# Bad: Too broad
src/**/*

# Bad: Too specific
src/api/users/controller.js
```

### 2. Use Multiple Patterns
```bash
# Cover related file types
src/components/**/*,src/ui/**/*,src/views/**/*
```

### 3. Consider File Extensions
```bash
# TypeScript/JavaScript files
**/*.{ts,tsx,js,jsx}

# Test files
**/*.{test,spec}.{ts,js}

# Configuration files
*.{json,yaml,yml,config.js}
```

### 4. Exclude Unnecessary Files
```bash
# Include source, exclude build
src/**/*,!dist/**/*,!node_modules/**/*
```

## 📊 Benefits for Agents

### 1. **Context Awareness**
- Agents know which documentation applies to current work
- Automatic loading of relevant documentation
- Better understanding of file relationships

### 2. **Consistent Documentation**
- Standardized documentation structure
- Automatic file scope indication
- Clear relationship between docs and code

### 3. **Efficient Workflow**
- Reduced time searching for relevant documentation
- Automatic template selection based on file patterns
- Context-aware rule generation

### 4. **Better Collaboration**
- Clear indication of documentation scope
- Easier handoffs between agents
- Consistent documentation patterns

## 🚀 Future Enhancements

### 1. Smart Pattern Detection
- Automatic glob pattern suggestion based on file analysis
- Pattern optimization based on usage statistics
- Dynamic pattern updates

### 2. Integration with IDEs
- Cursor IDE integration for template suggestions
- Real-time template applicability indicators
- Automatic documentation generation triggers

### 3. Advanced Context Analysis
- File dependency analysis for better glob patterns
- Semantic analysis of file content
- Cross-reference detection between documents and code

This template system with glob patterns provides a robust foundation for context-aware documentation generation, helping agents work more efficiently and maintain better project documentation. 