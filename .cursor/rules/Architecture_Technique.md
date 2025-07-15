---
description: Technical Architecture for DhafnckMCP AI Agent Orchestration Platform
globs: 
alwaysApply: false
---
# DhafnckMCP AI Agent Orchestration Platform - Technical Architecture

## SYSTEM_ARCHITECTURE_OVERVIEW
### Architecture_Type
Multi-Tier Enterprise Architecture

### Architecture_Description
Comprehensive enterprise-grade architecture providing advanced agent coordination, real-time monitoring, enterprise compliance, and autonomous workflow management across 70+ specialized AI agents, 12+ MCP tool categories, and a 6-phase Vision System.

### Architecture_Tiers
1. Frontend Layer - React + TypeScript + Tailwind CSS Application
2. Core MCP Server - Python + FastMCP 2.0 + Domain-Driven Design
3. Database Layer - Supabase + PostgreSQL + Real-time Sync

## ARCHITECTURE_COMPONENTS
### Frontend_Layer
- Location: dhafnck-frontend/
- Technology: React + TypeScript + Tailwind CSS
- Components:
  - Task Management Dashboard
  - Agent Coordination Interface  
  - Real-time Analytics & Monitoring
  - Project Health Visualization
  - Context Management UI
  - System Administration Panel

### Core_MCP_Server
- Location: dhafnck_mcp_main/
- Technology: Python + FastMCP 2.0 + Domain-Driven Design
- Components:
  - Agent Orchestration Engine (70+ agents)
  - MCP Tool Ecosystem (12+ categories)
  - Vision System (6 phases)
  - Connection Management
  - Compliance & Audit System
  - Real-time Event Processing

### Database_Layer
- Location: dhafnck-db-server/
- Technology: Supabase + PostgreSQL + Real-time Sync
- Components:
  - Task & Project Storage
  - Agent State Management
  - Context & Analytics Storage
  - Audit Trail & Compliance
  - Real-time Synchronization

## DOMAIN_DRIVEN_DESIGN
### Domain_Layer
- Location: dhafnck_mcp_main/src/fastmcp/task_management/domain/
- Entities:
  - Task - Main task entity with business logic and validation
  - Subtask - Hierarchical task decomposition
  - Project - Project entity with metadata and relationships
  - GitBranch - Branch-based task organization
  - Agent - AI agent entity with capabilities and assignments
  - Context - Rich context preservation and insights
- Value_Objects:
  - TaskId, ProjectId, AgentId - Unique identifiers
  - TaskStatus - Task status with transition rules
  - Priority - Task priority levels
  - ProgressPercentage - Progress tracking and analytics
- Domain_Events:
  - TaskCreated, TaskUpdated, TaskCompleted, TaskDeleted
  - SubtaskCreated, SubtaskUpdated, SubtaskCompleted
  - ProjectCreated, ProjectUpdated, ProjectHealthCheck
  - AgentRegistered, AgentAssigned, AgentUnassigned
  - ContextCreated, ContextUpdated, InsightAdded, ProgressAdded
- Domain_Services:
  - TaskOrchestrationService - Advanced task workflow coordination
  - AgentCoordinationService - Multi-agent workflow orchestration
  - WorkDistributionService - Intelligent task assignment
  - ProgressTrackingService - Multi-dimensional progress analytics
  - ContextEnrichmentService - Context enhancement and knowledge building

### Application_Layer
- Location: dhafnck_mcp_main/src/fastmcp/task_management/application/
- Use_Cases:
  - Task Management: CreateTask, UpdateTask, CompleteTask, DeleteTask, ListTasks, SearchTasks, GetNextTask
  - Subtask Management: CreateSubtask, UpdateSubtask, CompleteSubtask, ListSubtasks
  - Project Management: CreateProject, UpdateProject, GetProjectHealth, CleanupObsolete
  - Agent Management: RegisterAgent, AssignAgent, UnassignAgent, RebalanceAgents
  - Context Management: CreateContext, UpdateContext, AddProgress, AddInsight
- Application_Services:
  - TaskApplicationService - Coordinates task operations with vision enhancement
  - SubtaskApplicationService - Manages hierarchical task decomposition
  - ProjectApplicationService - Project lifecycle and health management
  - AgentApplicationService - Agent registration and coordination
  - ContextApplicationService - Context preservation and enrichment

### Infrastructure_Layer
- Location: dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/
- Repositories:
  - JsonTaskRepository - JSON-based task storage with atomic operations
  - SupabaseTaskRepository - PostgreSQL integration with real-time sync
  - FileSystemRepository - File-based storage for configurations
- External_Services:
  - VisionSystemService - 6-phase AI enhancement platform
  - ComplianceOrchestrator - Audit trails and validation
  - ConnectionHealthMonitor - Real-time health monitoring
  - NotificationService - Real-time status broadcasting

### Interface_Layer
- Location: dhafnck_mcp_main/src/fastmcp/task_management/interface/
- MCP_Controllers:
  - TaskMCPController - Task management MCP tools
  - SubtaskMCPController - Subtask management tools  
  - ContextMCPController - Context management tools
  - ProjectMCPController - Project management tools
  - GitBranchMCPController - Git branch management tools
  - AgentMCPController - Agent management tools
  - CallAgentMCPController - Agent invocation tools
  - ConnectionMCPController - Connection management tools
  - ComplianceMCPController - Compliance and audit tools
  - RuleOrchestrationController - Rule management tools

## TOOL_ECOSYSTEM
### Tool_Categories_Count
12+ categories with 50+ individual tools

### Tool_Categories_List
1. Task Management Tools - Full CRUD with context integration
2. Subtask Management Tools - Hierarchical task decomposition
3. Context Management Tools - Advanced context preservation and insights
4. Project Management Tools - Project lifecycle and health monitoring
5. Git Branch Management Tools - Branch-based task organization
6. Agent Management Tools - Agent registration and coordination
7. Agent Invocation Tools - Dynamic agent loading and execution
8. Connection Management Tools - Health monitoring and diagnostics
9. Compliance Tools - Audit trails and validation
10. Rule Management Tools - Rule orchestration and hierarchy
11. File Resource Tools - File system integration
12. Cursor Rules Tools - IDE integration and rule generation

### Key_Tool_Features
- Advanced workflow guidance and intelligent suggestions
- Real-time monitoring and health diagnostics
- Enterprise compliance and audit capabilities
- AI-powered task recommendations
- Multi-agent coordination support

## AGENT_ECOSYSTEM
### Total_Agent_Count
70+ specialized AI agents

### Agent_Categories
- Development Agents: 15+ agents (coding_agent, debugger_agent, system_architect_agent, tech_spec_agent)
- Design Agents: 8+ agents (ui_designer_agent, design_system_agent, ux_researcher_agent)
- DevOps Agents: 10+ agents (devops_agent, security_auditor_agent, performance_load_tester_agent)
- Analytics Agents: 8+ agents (analytics_setup_agent, market_research_agent, user_feedback_collector_agent)
- Management Agents: 12+ agents (project_initiator_agent, task_planning_agent, uber_orchestrator_agent)
- Marketing Agents: 10+ agents (campaign_manager_agent, content_strategy_agent, seo_sem_agent)
- Specialized Agents: 15+ agents (compliance_scope_agent, ethical_review_agent, incident_learning_agent)

### Agent_Library_Structure
- Location: dhafnck_mcp_main/agent-library/agents/
- Configuration: YAML-based agent definitions
- Capabilities: Dynamic loading and execution
- Coordination: Multi-agent workflow support

## VISION_SYSTEM
### Vision_System_Phases
1. Context Enforcement - Mandatory context validation and completeness
2. Progress Tracking - Multi-dimensional progress analytics and forecasting
3. Workflow Hints - AI-powered workflow optimization and suggestions
4. Multi-Agent Coordination - Structured agent handoffs and collaboration
5. Vision Enrichment - Strategic objective alignment and goal tracking
6. Integration & Testing - Performance benchmarks and system analytics

### Vision_Features
- Intelligent Insights - AI-powered recommendations and guidance
- Progress Analytics - Multi-dimensional tracking and forecasting
- Context Enrichment - Automatic enhancement and knowledge building
- Workflow Optimization - Pattern detection and process improvement
- Performance Metrics - Comprehensive analytics and benchmarking

## DATA_ARCHITECTURE
### Task_Storage_Structure
- Format: JSON with multi-tier synchronization
- Key_Fields:
  - id: task_uuid
  - title: Enterprise feature implementation
  - status: todo, in_progress, blocked, review, testing, done
  - priority: low, medium, high, urgent, critical
  - git_branch_id: branch_uuid
  - context_id: context_uuid
  - vision_data: phase, progress_analytics, workflow_hints, agent_coordination

### Context_Storage_Structure
- Format: JSON with rich metadata
- Key_Components:
  - metadata: task_id, status, priority, assignees, labels, version
  - objective: title, description, estimated_effort, due_date
  - progress: completed_actions, next_steps, completion_percentage, vision_alignment_score
  - vision_data: phase, progress_analytics, workflow_hints, agent_coordination
  - notes: agent_insights, challenges_encountered, solutions_applied, decisions_made

### Database_Schema
- Provider: Supabase + PostgreSQL
- Real_Time_Sync: Enabled across all tiers
- Backup_Strategy: Enterprise-grade backup and recovery
- Performance: Optimized queries with indexing strategy

## SECURITY_ARCHITECTURE
### Security_Layers
1. Authentication & Authorization - Agent-based access control
2. Data Protection - Encryption at rest and in transit
3. Audit & Compliance - Complete operation logging
4. Threat Protection - Input validation and intrusion detection

### Compliance_Framework
- Operation Validation - Real-time policy enforcement
- Audit Trail Management - Comprehensive activity logging
- Governance Controls - Policy configuration management
- Risk Management - Risk assessment automation

## PERFORMANCE_ARCHITECTURE
### Performance_Optimization
- Frontend: Code splitting and lazy loading
- Server: Async/await architecture with connection pooling
- Database: Query optimization with index strategy
- Vision System: AI model caching and batch processing

### Scalability_Strategy
- Horizontal Scaling - Multi-instance deployment support
- Vertical Scaling - Resource optimization
- Auto-scaling - Demand-based scaling
- Performance Monitoring - Real-time metrics and benchmarking

### Performance_Targets
- Task Operations: < 100ms response time
- Agent Coordination: < 500ms orchestration time
- Database Sync: < 200ms synchronization
- Health Monitoring: < 50ms check time
- Vision Analytics: < 1 second generation

## DEPLOYMENT_ARCHITECTURE
### Production_Configuration
- Environment: Production
- Server_Host: 0.0.0.0
- Server_Port: 8000
- Workers: 4
- Max_Connections: 1000
- Database_Pool_Size: 20
- Max_Concurrent_Agents: 100
- Audit_Retention_Days: 2555

### Deployment_Components
- Frontend Deployment - React build with CDN distribution
- MCP Server Deployment - Python application with FastMCP
- Database Deployment - Supabase with PostgreSQL optimization
- Infrastructure - Load balancing and SSL/TLS management

### System_Paths
- Frontend: /home/daihungpham/agentic-project/dhafnck-frontend/
- Core Server: /home/daihungpham/agentic-project/dhafnck_mcp_main/
- Database: /home/daihungpham/agentic-project/dhafnck-db-server/
- Agent Library: /home/daihungpham/agentic-project/dhafnck_mcp_main/agent-library/
- Configuration: /home/daihungpham/agentic-project/.cursor/rules/

## CURRENT_ARCHITECTURE_STATUS
### Implemented_Components
- Multi-Tier Architecture: COMPLETE
- MCP Tool Ecosystem: COMPLETE (12+ categories, 50+ tools)
- Agent Orchestration: COMPLETE (70+ agents)
- Vision System: COMPLETE (6 phases)
- Enterprise Compliance: COMPLETE
- Real-Time Monitoring: COMPLETE
- Database Integration: COMPLETE
- Performance Optimization: COMPLETE
- Security Framework: COMPLETE

### Active_Development
- Advanced Analytics - Enhanced vision system insights
- Performance Scaling - Multi-tier optimization
- Extended Integrations - External system APIs
- Cloud Deployment - Kubernetes configuration
- Advanced Workflows - Sophisticated orchestration patterns

### Technical_Debt
- Microservices Migration - Future architecture evolution
- GraphQL API - Additional API layer
- Mobile Applications - Mobile client development
- ML Integration - Advanced machine learning features
- Federated Architecture - Distributed deployment

## INTEGRATION_POINTS
### External_Integrations
- Cursor IDE - MCP server integration
- Git Systems - Branch-based task management
- Supabase - Real-time database synchronization
- YAML Libraries - Agent configuration management
- FastMCP Framework - Core server infrastructure

### API_Endpoints
- MCP Protocol - Standard MCP tool invocation
- WebSocket - Real-time status updates
- REST API - Future development
- GraphQL - Planned enhancement

### System_Interfaces
- Frontend-Server: HTTP/WebSocket communication
- Server-Database: PostgreSQL protocol with real-time sync
- Agent-Server: YAML configuration and dynamic loading
- Client-Server: MCP protocol standard