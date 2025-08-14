# DhafnckMCP Documentation

Welcome to the DhafnckMCP Multi-Project AI Orchestration Platform documentation.

## 📚 Documentation Hub

### 🚀 Getting Started
- [README](../README.md) - Project overview and quick start
- [Database Setup](../DATABASE_SETUP.md) - Database configuration guide
- [Environment Setup](../ENV_SETUP_README.md) - Environment setup instructions
- [Docker Quick Start](../docker/README_DOCKER.md) - Docker deployment guide
- [Configuration Guide](configuration.md) - Environment variables and settings

### 🏗️ Architecture & Design
Foundational design principles, architectural patterns, and technical decisions for the DhafnckMCP platform.

- [**Architecture & Design Overview**](architecture-design/README.md) - Complete architectural documentation hub
- [System Architecture](architecture-design/architecture.md) - Overall system architecture and components
- [Technical Architecture](architecture-design/Architecture_Technique.md) - Detailed technical architecture with DDD
- [Domain-Driven Design](architecture-design/domain-driven-design.md) - DDD implementation patterns
- [AI Context Realistic Approach](architecture-design/AI-CONTEXT-REALISTIC-APPROACH.md) - Practical AI context strategies

### 🔄 Migration & Updates
System migration guides for upgrading and transitioning between versions and configurations.

- [**Migration Guides Overview**](migration-guides/README.md) - Complete migration documentation hub
- [Hierarchical Context Migration](migration-guides/HIERARCHICAL_CONTEXT_MIGRATION.md) - Basic to hierarchical context migration
- [Unified Context Migration Guide](migration-guides/unified_context_migration_guide.md) - Unified context system migration
- [Context Auto-Detection Fix](migration-guides/CONTEXT_AUTO_DETECTION_FIX.md) - Enhanced auto-detection with error handling

### 📖 API & Integration
Comprehensive API documentation, integration guides, and configuration references.

- [**API & Integration Overview**](api-integration/README.md) - Complete API documentation hub
- [API Reference](api-integration/api-reference.md) - Complete MCP tools and HTTP API documentation
- [Configuration Guide](api-integration/configuration.md) - Environment variables and settings
- [Parameter Type Validation](api-behavior/parameter-type-validation.md) - Strict type validation for MCP tool parameters
- [Parameter Type Conversion](api-behavior/parameter-type-conversion-verification.md) - Automatic parameter type conversion
- [JSON Parameter Parsing](api-behavior/json-parameter-parsing.md) - JSON string parameter handling

### 📄 Claude Document Management System
A comprehensive documentation management system with analysis tools, quality metrics, and automated maintenance capabilities.

- [**System Overview**](claude-document-management-system/index.md) - Complete documentation management guide
- [**CLI Tools Documentation**](claude-document-management-system/cli-commands/manage-documentation-tools.md) - Command-line tools for doc management
- [Architecture](claude-document-management-system/architecture/claude-document-management-architecture.md) - Database schema and system design
- [Implementation Guide](claude-document-management-system/implementation/claude-document-management-implementation.md) - Setup and deployment
- [Multi-Phase Roadmap](claude-document-management-system/phases/claude-document-management-phases.md) - 5-phase evolution plan
- [Phase 2: pgvector](claude-document-management-system/phases/phase2-pgvector-implementation.md) - Semantic search integration
- [Phase 3: Advanced Search](claude-document-management-system/phases/phase3-advanced-search-implementation.md) - Analytics and recommendations
- [File Specifications](claude-document-management-system/file-specifications/complete-file-structure-and-tests.md) - Complete file listings and tests
- [CLI Commands](claude-document-management-system/cli-commands/) - Executable scripts and tools

### 🔗 Context System
Comprehensive documentation for the DhafnckMCP hierarchical context management system.

- [**Context System Overview**](context-system/README.md) - Complete context system documentation hub
- [Hierarchical Context System](context-system/hierarchical-context.md) - 4-tier context hierarchy (Global→Project→Branch→Task)
- [Context Response Format](context-system/context-response-format.md) - Context API response structures
- [Context System Audit](context-system/context_system_audit.md) - System validation and health checks
- [Unified Context System Final](context-system/unified_context_system_final.md) - Final implementation specifications

### 🧪 Testing & Quality
Comprehensive testing documentation, QA procedures, and test results.

- [**Testing & QA Overview**](testing-qa/README.md) - Complete testing documentation hub
- [Testing Guide](testing-qa/testing.md) - Unit and integration testing strategies with TDD patterns
- [Test Results and Issues](testing-qa/test-results-and-issues.md) - Comprehensive test execution results
- [MCP Tools Test Issues](testing-qa/mcp-tools-test-issues.md) - Known MCP tool integration test issues
- [MCP Testing Report](testing-qa/MCP_TESTING_REPORT.md) - Detailed MCP tools testing results
- [PostgreSQL TDD Fixes](testing-qa/POSTGRESQL_TDD_FIXES_SUMMARY.md) - Test-driven development fixes
- [PostgreSQL Test Migration](testing-qa/POSTGRESQL_TEST_MIGRATION_SUMMARY.md) - Database test migration results
- [End-to-End Testing Guidelines](testing-qa/e2e/End_to_End_Testing_Guidelines.md) - E2E testing best practices
- [Context Resolution Tests Summary](testing-qa/context_resolution_tests_summary.md) - Context resolution test results
- [Context Resolution TDD Tests](testing-qa/context_resolution_tdd_tests.md) - TDD approach for context tests

### 🛠️ Development Guides
Technical development guides, implementation patterns, and best practices.

- [**Development Guides Overview**](development-guides/README.md) - Complete development documentation hub
- [Error Handling and Logging](development-guides/error-handling-and-logging.md) - Error handling patterns and logging strategies
- [ORM Agent Repository](development-guides/orm-agent-repository-implementation.md) - ORM-based repository patterns
- [Docker Deployment](development-guides/docker-deployment.md) - Production-ready Docker configurations

### 📋 Product Requirements
Product requirements, specifications, and strategic planning documents.

- [**Product Requirements Overview**](product-requirements/README.md) - Complete product requirements hub
- [Product Requirements Document (PRD)](product-requirements/PRD.md) - Complete product requirements and strategic objectives

### 🎯 Vision System Documentation
The Vision System is a CRITICAL component that transforms DhafnckMCP into a strategic execution platform.

#### Core Vision Docs
- [Vision System Overview](vision/README.md) - **START HERE** - Complete Vision System guide
- [System Integration Guide](vision/SYSTEM_INTEGRATION_GUIDE.md) - **AUTHORITATIVE** - Resolves all conflicts
- [Phase 6 Implementation Summary](vision/PHASE6_IMPLEMENTATION_SUMMARY.md) - Implementation completion status
- [AI Phase Guide](vision/AI_PHASE_GUIDE.md) - Quick reference for AI implementation

#### Vision Implementation
- [Implementation Roadmap](vision/IMPLEMENTATION_ROADMAP.md) - Step-by-step implementation phases
- [Consolidated MCP Vision Implementation](vision/consolidated-mcp-vision-implementation.md) - Main implementation guide
- [Vision Hierarchy](vision/01-vision-hierarchy.md) - Hierarchical vision structure
- [Vision Components](vision/02-vision-components.md) - Vision components framework
- [Domain Models](vision/04-domain-models.md) - Domain model specifications

#### Workflow & Guidance
- [Workflow Guidance Detailed Spec](vision/WORKFLOW_GUIDANCE_DETAILED_SPEC.md) - Complete workflow guidance specification
- [Workflow Guidance Quick Reference](vision/WORKFLOW_GUIDANCE_QUICK_REFERENCE.md) - Quick workflow reference
- [Workflow Hints and Rules](vision/workflow-hints-and-rules.md) - Workflow guidance system
- [Server-Side Context Tracking](vision/server-side-context-tracking.md) - Context tracking via MCP parameters
- [Manual Context Updates with Vision](vision/manual-context-vision-updates.md) - Enforce context updates through parameters
- [Implementation Guide Server Enrichment](vision/implementation-guide-server-enrichment.md) - Auto-enrich responses
- [Subtask Manual Progress Tracking](vision/subtask-manual-progress-tracking.md) - Manual progress updates with enriched responses

### 🚨 Troubleshooting & Issues
Comprehensive troubleshooting documentation for diagnosing and resolving issues.

- [**Troubleshooting Overview**](troubleshooting-guides/README.md) - Complete troubleshooting documentation hub
- [Comprehensive Troubleshooting Guide](troubleshooting-guides/COMPREHENSIVE_TROUBLESHOOTING_GUIDE.md) - Systematic problem diagnosis and solutions
- [Quick Troubleshooting Reference](troubleshooting-guides/TROUBLESHOOTING.md) - Common issues and quick fixes
- [**Issue Documentation**](issues/index.md) - Detailed documentation of significant issues and resolutions
  - [Database Schema Mismatch (2025-01-13)](issues/2025-01-13-database-schema-mismatch.md) - Critical context table schema fix

### 📊 Reports & Status
System status reports, documentation health checks, and implementation status updates.

- [**Reports & Status Overview**](reports-status/README.md) - Complete reports and status documentation hub
- [Documentation Status Report](reports-status/DOCUMENTATION_STATUS_REPORT.md) - Latest documentation health check and coverage
- [Insights Found Parameter Fix](reports-status/INSIGHTS_FOUND_PARAMETER_FIX_SOLUTION.md) - Parameter validation solution implementation

### 🐳 Deployment & Operations
- **[Operations Overview](operations/index.md)** - Complete operations documentation hub
- [PostgreSQL Configuration Guide](operations/postgresql-configuration-guide.md) - Database setup and configuration
- [Docker Deployment](development-guides/docker-deployment.md) - Production Docker deployment
- [Docker Configuration](docker/config/README.md) - Docker configuration details
- [Scripts Documentation](operations/scripts-documentation.md) - Utility scripts guide

### 📂 Examples & Templates
- [Smart Home Example](../examples/smart_home/README.md) - Smart home integration example

## 🔗 Quick Links

- **🚨 Error Handling**: See [Error Handling and Logging](development-guides/error-handling-and-logging.md) for comprehensive error management
- **💾 Database Setup**: See [Database Setup Guide](../DATABASE_SETUP.md) for PostgreSQL configuration
- **📡 API Documentation**: See [API Reference](api-integration/api-reference.md) for MCP tools documentation
- **👁️ Vision System**: See [Vision System Overview](vision/README.md) for strategic AI orchestration
- **📄 Document Management**: See [Claude Document Management System](claude-document-management-system/README.md) for document management solution
- **🐛 Troubleshooting**: See [Comprehensive Troubleshooting Guide](troubleshooting-guides/COMPREHENSIVE_TROUBLESHOOTING_GUIDE.md)

## 📅 Recent Updates

### 2025-01-31
- **Major Documentation Reorganization**: Complete restructuring of documentation into logical categories
  - Created 9 new categorized subfolders: architecture-design, context-system, troubleshooting-guides, migration-guides, testing-qa, reports-status, development-guides, api-integration, product-requirements
  - Moved 28 loose markdown files into appropriate categories with dedicated README files
  - Updated all cross-references and maintained proper documentation hierarchy
- **Claude Document Management System**: Organized all system files into dedicated subfolder with structured organization
- **Enhanced Navigation**: Added comprehensive README files for each category with clear descriptions
- **Vision System Priority**: Highlighted Vision System as critical component with dedicated section
- **Better Discoverability**: Organized docs into logical categories with consistent formatting and icons

### 2025-01-20
- **Boolean Parameter Fix**: Resolved validation issues for boolean string parameters
- **Auto-Context Creation**: Implemented automatic context creation for all entities
- **Context Synchronization**: Manual context updates sync to cloud automatically

### 2025-01-19
- **Task Completion Fix**: Tasks can now be completed without manual context creation
- **Unified Context Fix**: Resolved async/sync architecture issues in context system
- **Parameter Flexibility**: Added JSON string support for context data parameters

### 2025-01-18
- **4-Tier Context System**: Global→Project→Branch→Task hierarchy implemented
- **Database Enforcement**: Strict Docker DB usage for consistency
- **Documentation Cleanup**: Removed 45% of obsolete docs while improving coverage

### Previous Updates
- Enhanced hierarchical context system with custom data fields
- PostgreSQL support with JSONB for better performance
- ORM-based agent repository implementation with comprehensive test suite
- Complete migration to 4-tier hierarchical context system
- Enhanced context auto-detection with comprehensive error handling
- Comprehensive testing guide with TDD patterns and performance testing
- Docker deployment guide with production-ready configurations

## 🤝 Contributing

Please see the project repository for guidelines on contributing to this project. Contact the maintainers for contribution guidelines.

## 📝 Documentation Standards

When adding new documentation:
1. Place files in appropriate category directories
2. Update this index with proper categorization
3. Follow existing naming conventions
4. Include clear descriptions and examples
5. Cross-reference related documentation
6. Test all code examples before inclusion

---
*Last Updated: 2025-01-31 - Major Documentation Reorganization & Category Structure Implementation*