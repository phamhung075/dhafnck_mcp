# Documentation Management Commands

This directory contains comprehensive documentation management tools for the DhafnckMCP AI Agent Orchestration Platform. These commands provide intelligent documentation analysis, indexing, and lifecycle management with optional PostgreSQL backend integration.

## Overview

The documentation management system offers three complementary tools:

1. **manage_document_md** - Full-featured documentation management with JSON indexing
2. **manage_document_md_simple** - Lightweight version without external dependencies  
3. **manage_document_md_postgresql** - Enterprise-grade PostgreSQL-based document management

## Core Features

### Document Health Analysis
- **Age Detection**: Identifies documents not updated in >30 days (stale) or >90 days (very old)
- **Status Markers**: Detects DEPRECATED, OUTDATED, TODO, FIXME markers
- **Technology Currency**: Flags outdated technology references (e.g., SQLite when using PostgreSQL)
- **Broken Links**: Validates internal document references and links
- **Orphan Detection**: Finds documents not linked from index.md or README files

### Document Organization
- **Intelligent Categorization**: Automatically categorizes documents by type:
  - API Reference (files matching `*api*` or `*API*`)
  - Testing Documentation (`*test*` or `*Test*`)
  - Bug Fixes & Solutions (`*fix*` or `*Fix*`)
  - Vision System (files in `vision/` directory)
  - Architecture & Design (`*architecture*` or `*design*`)
  - Troubleshooting Guides (`*troubleshoot*`)
  - Configuration & Setup (`*config*` or `*setup*`)
  - Migration Guides (`*migration*`)
  - Change Logs (`*CHANGELOG*` or `*changelog*`)

### Code-Documentation Dependency Tracking
- Tracks Python imports and file references
- Identifies MCP tool references (`manage_*`)
- Maps class/function references
- Detects undocumented major components
- Cross-references code changes with documentation updates

## Command Details

### manage_document_md

The primary documentation management tool with comprehensive features.

**Features:**
- Document health analysis with detailed metrics
- JSON-based document indexing with metadata extraction
- Code-documentation dependency tracking
- Broken link detection and validation
- Orphaned document identification
- Automatic report generation in markdown format
- Main index.md generation and updates
- Git integration for version history

**Usage:**
```bash
# Interactive mode - presents menu-driven interface
manage_document_md

# Command line options
manage_document_md --analyze      # Analyze documentation health
manage_document_md --index        # Generate document index (JSON)
manage_document_md --outdated     # Find outdated documents
manage_document_md --orphaned     # Find orphaned documents
manage_document_md --deps         # Check code-documentation dependencies
manage_document_md --report       # Generate documentation report
manage_document_md --update-index # Update main index.md
manage_document_md --full         # Run full analysis
```

**Output Files:**
- **JSON Index**: `$PROJECT_ROOT/.claude/doc_index.json`
  - Contains document metadata, age, status, and references
- **Status Report**: `$DOCS_ROOT/DOCUMENTATION_STATUS.md`
  - Comprehensive health report with recommendations
- **Main Index**: `$DOCS_ROOT/index.md`
  - Auto-generated navigation structure

**Requirements:**
- `jq` for JSON processing
- `git` for version history
- `tree` (optional) for directory visualization

### manage_document_md_simple

A lightweight alternative without external dependencies.

**Features:**
- Document scanning and categorization
- Age-based outdated detection
- Orphaned document detection
- Broken link checking
- Status report generation
- Individual document analysis
- No external dependencies required

**Usage:**
```bash
# Interactive mode
manage_document_md_simple

# Command line options
manage_document_md_simple --scan          # Scan all documentation
manage_document_md_simple --outdated      # Find outdated documents
manage_document_md_simple --orphaned      # Find orphaned documents
manage_document_md_simple --broken-links  # Check for broken links
manage_document_md_simple --report        # Generate status report
manage_document_md_simple --analyze PATH  # Analyze specific document
manage_document_md_simple --full          # Run full analysis
```

### manage_document_md_postgresql

Enterprise-grade document management with PostgreSQL backend integration.

**Features:**
- Full document lifecycle management
- Version control with automatic versioning
- Full-text search capabilities with pgvector
- Document relationships and dependencies
- Tag-based categorization
- Access control and audit trails
- MCP tool integration
- Real-time synchronization with file system

**Database Schema:**
- Documents table with metadata and content
- Versions table for version history
- Tags and categories for organization
- Dependencies table for relationships
- Audit logs for compliance

**Usage:**
```bash
# Interactive mode
manage_document_md_postgresql

# Command line options
manage_document_md_postgresql --init          # Initialize database schema
manage_document_md_postgresql --sync          # Sync files with database
manage_document_md_postgresql --index         # Rebuild search indexes
manage_document_md_postgresql --search QUERY  # Full-text search
manage_document_md_postgresql --version FILE  # Show version history
manage_document_md_postgresql --audit         # Generate audit report
```

**Environment Variables:**
```bash
CLAUDE_DOC_DB_HOST=localhost     # Database host
CLAUDE_DOC_DB_PORT=5432         # Database port
CLAUDE_DOC_DB_NAME=claude_docs  # Database name
CLAUDE_DOC_DB_USER=claude       # Database user
CLAUDE_DOC_DB_PASSWORD=         # Database password
```

## Integration with MCP Tools

The documentation management system integrates seamlessly with DhafnckMCP tools:

### Task Management Integration
```bash
# Create documentation task
mcp__dhafnck_mcp_http__manage_task(
    action="create",
    title="Update API documentation",
    description="Review and update outdated API docs identified by manage_document_md"
)

# Link documentation to tasks
manage_document_md --deps | grep "undocumented" | \
    xargs -I {} create_documentation_task {}
```

### Context Management Integration
```bash
# Store documentation analysis in context
DOC_REPORT=$(manage_document_md --report)
mcp__dhafnck_mcp_http__manage_context(
    action="update",
    level="project",
    data={"documentation_health": "$DOC_REPORT"}
)
```

### Automated Workflows
```bash
# Daily documentation health check
0 9 * * * /path/to/manage_document_md --full --report

# Pre-commit hook for documentation validation
#!/bin/bash
manage_document_md --deps | grep -q "missing" && exit 1
```

## Detection Criteria

### Outdated Documents
- **Very Old**: Not modified in >90 days
- **Stale**: Not modified in >30 days
- Contains markers: `DEPRECATED`, `OUTDATED`, `TODO`, `FIXME`
- References outdated technology or deprecated APIs
- Missing required sections or metadata

### Orphaned Documents
- Not linked from `index.md` or `README.md` files
- Not referenced by other documents
- No incoming code references
- Excludes index files themselves

### Code-Documentation Dependencies
- Tracks Python imports: `from X import Y`, `import X`
- File path references: `/src/`, `/tests/`, `/fastmcp/`
- Class/function references: `class X`, `def Y`, `function Z`
- MCP tool references: `manage_task`, `manage_context`, etc.

## Best Practices

### Regular Maintenance
1. **Weekly Scans**: Run `--full` analysis weekly
   ```bash
   manage_document_md --full --report
   ```

2. **Update Stale Docs**: Review documents >30 days old
   ```bash
   manage_document_md --outdated | grep "stale"
   ```

3. **Fix Broken Links**: Run after moving/renaming files
   ```bash
   manage_document_md_simple --broken-links
   ```

4. **Remove Orphans**: Either link or archive orphaned documents
   ```bash
   manage_document_md --orphaned
   ```

5. **Maintain Index**: Keep main index.md updated
   ```bash
   manage_document_md --update-index
   ```

### Integration with Development Workflow

1. **Before Release**: 
   ```bash
   # Full documentation audit
   manage_document_md --full
   # Generate compliance report
   manage_document_md_postgresql --audit
   ```

2. **After Major Changes**:
   ```bash
   # Check code-doc dependencies
   manage_document_md --deps
   # Update affected documentation
   ```

3. **During Code Review**:
   ```bash
   # Validate documentation updates
   git diff --name-only | grep ".md$" | \
       xargs -I {} manage_document_md_simple --analyze {}
   ```

4. **Sprint Planning**:
   ```bash
   # Review outdated docs for update tasks
   manage_document_md --outdated --report outdated_docs.md
   ```

## Advanced Features

### Custom Categories
Add custom document categories by modifying the `DOC_CATEGORIES` array:
```bash
declare -A DOC_CATEGORIES=(
    ["api"]="API Reference"
    ["custom"]="Custom Category"
)
```

### Automated Report Generation
Generate different report formats:
```bash
# Markdown report
manage_document_md --report report.md

# JSON data for processing
manage_document_md --index | jq '.documents[] | select(.status=="outdated")'

# CSV export
manage_document_md --index | jq -r '.documents[] | [.path, .title, .age] | @csv'
```

### Integration with CI/CD
```yaml
# GitHub Actions example
- name: Documentation Health Check
  run: |
    ./manage_document_md --full
    if [ -f "DOCUMENTATION_STATUS.md" ]; then
      cat DOCUMENTATION_STATUS.md >> $GITHUB_STEP_SUMMARY
    fi
```

## Troubleshooting

### Command Hangs
- Large repositories may take time to process
- Check git repository status: `git status`
- Ensure proper permissions: `ls -la docs/`

### JSON Parse Errors
- Use `manage_document_md_simple` if jq issues occur
- Check for special characters in document titles
- Validate JSON output: `manage_document_md --index | jq .`

### Missing Documents
- Ensure documents are in tracked directories
- Check `.gitignore` for excluded patterns
- Verify file extensions are `.md`

### Database Connection Issues (PostgreSQL)
- Verify database credentials
- Check network connectivity
- Ensure database exists: `psql -d claude_docs -c '\dt'`

## Performance Optimization

### Large Repositories
```bash
# Limit search depth
find docs -maxdepth 3 -name "*.md" | \
    xargs manage_document_md_simple --analyze

# Parallel processing
find docs -name "*.md" | \
    parallel -j 4 manage_document_md_simple --analyze {}
```

### Caching Results
```bash
# Cache expensive operations
manage_document_md --index > doc_index_cache.json
jq '.documents[] | select(.age > 30)' doc_index_cache.json
```

## Future Enhancements

### Planned Features
1. **AI-Powered Analysis**: Integration with LLMs for content quality assessment
2. **Auto-Update Suggestions**: Generate documentation updates based on code changes
3. **Multi-Language Support**: Extend beyond markdown to other documentation formats
4. **Real-time Monitoring**: Watch mode for continuous documentation health tracking
5. **Collaborative Features**: Multi-user editing and review workflows

### PostgreSQL Advanced Features
1. **Vector Search**: Semantic search using pgvector embeddings
2. **Change Notifications**: Real-time updates via PostgreSQL NOTIFY
3. **Document Templates**: Reusable templates with variable substitution
4. **Workflow Automation**: Trigger-based documentation workflows
5. **Analytics Dashboard**: Web-based documentation metrics visualization

## Contributing

To contribute to the documentation management system:

1. **Report Issues**: Use the issue tracker for bugs or feature requests
2. **Submit PRs**: Follow the coding standards and include tests
3. **Documentation**: Update this README when adding new features
4. **Testing**: Ensure all commands work in both interactive and CLI modes

## Support

For support and questions:
- Check the troubleshooting section above
- Review command help: `manage_document_md --help`
- Consult project documentation in `/docs`
- Use MCP tools for automated assistance

---

**Version**: 2.0.0  
**Last Updated**: 2025-01-31  
**Maintained By**: DhafnckMCP Documentation Team  
**License**: Same as parent project