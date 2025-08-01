# DhafnckMCP System Architecture

## Overview

DhafnckMCP is a multi-project AI orchestration platform built using Domain-Driven Design (DDD) principles with a 4-tier hierarchical context system. The platform enables autonomous AI agents to manage complex software development workflows across multiple projects and team contexts.

## Core Architecture Principles

### 1. Domain-Driven Design (DDD)
- **Bounded Contexts**: Clear separation between task management, agent orchestration, and context management domains
- **Aggregates**: Task, Project, GitBranch, and Context as primary aggregates
- **Domain Services**: Business logic encapsulated in domain services
- **Application Services**: Orchestrate domain operations and external integrations

### 2. 4-Tier Hierarchical Context System
```
GLOBAL (Organization-wide patterns)
   ↓ inherits to
PROJECT (Business domain context)  
   ↓ inherits to
BRANCH (Feature/work branch context)
   ↓ inherits to
TASK (Specific work unit context)
```

### 3. MCP (Model Context Protocol) Integration
- FastMCP framework for tool definitions
- Type-safe parameter validation
- Async/await support for performance
- Comprehensive error handling

## System Components

### Core Domains

#### Task Management Domain
- **Entities**: Task, Subtask, TaskContext
- **Value Objects**: TaskStatus, Priority, CompletionSummary
- **Services**: TaskCompletionService, TaskWorkflowGuidance
- **Repositories**: TaskRepository, SubtaskRepository

#### Project Management Domain
- **Entities**: Project, GitBranch
- **Value Objects**: ProjectMetadata, BranchConfiguration
- **Services**: ProjectHealthService, BranchStatisticsService
- **Repositories**: ProjectRepository, GitBranchRepository

#### Agent Orchestration Domain
- **Entities**: Agent, AgentAssignment
- **Value Objects**: AgentCapabilities, AssignmentConfiguration
- **Services**: AgentLoadBalancer, AgentSelectionService
- **Repositories**: AgentRepository

#### Context Management Domain
- **Entities**: HierarchicalContext, ContextDelegation
- **Value Objects**: ContextData, DelegationRequest
- **Services**: ContextInheritanceService, ContextDelegationService, ContextCacheService
- **Repositories**: HierarchicalContextRepository

### Application Layer

#### Facades
- **TaskApplicationFacade**: Orchestrates task operations
- **ProjectApplicationFacade**: Manages project lifecycle
- **AgentApplicationFacade**: Handles agent assignments
- **HierarchicalContextFacade**: Manages context hierarchy

#### MCP Controllers
- **TaskMCPController**: Exposes task management tools
- **ProjectMCPController**: Exposes project management tools
- **AgentMCPController**: Exposes agent orchestration tools
- **ContextMCPController**: Exposes context management tools

### Infrastructure Layer

#### Persistence
- **SQLAlchemy ORM**: Object-relational mapping
- **Database Adapters**: PostgreSQL (primary for all environments)
- **Migration Management**: Alembic for schema versioning

#### Caching
- **ContextCacheService**: LRU cache with dependency tracking
- **Cache Invalidation**: Automatic invalidation on context changes
- **Performance Monitoring**: Cache hit/miss metrics

#### External Integrations
- **MCP Protocol**: Tool registration and execution
- **Authentication**: Bearer token validation
- **Compliance**: Operation validation and audit trails

## Data Flow Architecture

### Request Processing Flow
```
AI Agent → MCP Tool → Controller → Facade → Domain Service → Repository → Database
                                      ↓
                              Context Resolution
                                      ↓
                              Business Logic
                                      ↓
                              Response Enrichment
```

### Context Resolution Flow
```
Task Context Request → Branch Context → Project Context → Global Context
                           ↓
                    Inheritance Chain
                           ↓
                    Merged Context Data
                           ↓
                    Cached for Performance
```

## Key Design Patterns

### 1. Facade Pattern
- Simplified interfaces for complex domain operations
- Coordination of multiple domain services
- Transaction boundary management

### 2. Repository Pattern
- Abstraction over data persistence
- Domain-focused query interfaces
- Testability through interface abstractions

### 3. Strategy Pattern
- Agent selection strategies
- Context delegation strategies
- Workflow guidance strategies

### 4. Observer Pattern
- Context change propagation
- Cache invalidation events
- Audit trail generation

### 5. Factory Pattern
- Facade creation with proper dependencies
- Context creation based on hierarchy level
- Agent instantiation with capabilities

## Performance Considerations

### Caching Strategy
- **Context Cache**: LRU cache with dependency tracking
- **Agent Assignment Cache**: Cached agent-branch relationships
- **Workflow Guidance Cache**: Cached decision trees

### Database Optimization
- **Connection Pooling**: PostgreSQL connection pooling with automatic scaling
- **Query Optimization**: Selective loading with SQLAlchemy relationships and PostgreSQL query plans
- **Index Strategy**: B-tree and GIN indexes for JSONB fields and search performance
- **PostgreSQL Features**: JSONB operators, UUID generation, partial indexes, and parallel queries

### Async Processing
- **Non-blocking Operations**: Async/await throughout the stack
- **Background Tasks**: Deferred processing for expensive operations
- **Resource Management**: Proper cleanup of async resources

## Security Architecture

### Authentication & Authorization
- **Bearer Token Authentication**: Stateless token validation
- **Role-based Access Control**: Project and task-level permissions
- **Audit Trails**: Comprehensive operation logging

### Data Protection
- **Input Validation**: Type-safe parameter validation
- **SQL Injection Prevention**: Parameterized queries with SQLAlchemy
- **Secrets Management**: Environment-based configuration

### Compliance
- **Operation Validation**: Pre-execution compliance checks
- **Audit Logging**: Immutable audit trail
- **Data Retention**: Configurable retention policies

## Deployment Architecture

### Container Strategy
- **Docker Containerization**: Consistent deployment environments
- **Multi-stage Builds**: Optimized container images
- **Health Checks**: Container health monitoring

### Database Configuration
- **Primary**: PostgreSQL with JSONB for all environments (development, production)
- **Testing**: Isolated PostgreSQL test databases with automatic cleanup
- **Features**: Advanced indexing, partitioning, and query optimization

### Monitoring & Observability
- **Health Endpoints**: System health monitoring
- **Metrics Collection**: Performance and usage metrics
- **Error Tracking**: Comprehensive error logging

## Scalability Considerations

### Horizontal Scaling
- **Stateless Design**: No server-side session state
- **Database Scaling**: Read replicas and connection pooling
- **Cache Distribution**: Distributed caching strategies

### Vertical Scaling
- **Resource Optimization**: Efficient memory and CPU usage
- **Database Tuning**: Query optimization and indexing
- **Caching Efficiency**: Intelligent cache eviction policies

## Future Architecture Evolution

### Planned Enhancements
- **Event Sourcing**: Complete audit trail with event replay
- **CQRS Pattern**: Separated read/write models for performance
- **Microservices**: Domain-based service decomposition
- **Real-time Updates**: WebSocket-based real-time notifications

### Extension Points
- **Plugin Architecture**: Dynamic tool registration
- **Custom Workflows**: User-defined workflow patterns
- **Third-party Integrations**: External system connectors
- **AI Model Integration**: Direct LLM integration capabilities

## Conclusion

The DhafnckMCP architecture provides a robust, scalable foundation for AI-driven project management. The combination of DDD principles, hierarchical context management, and MCP integration enables sophisticated autonomous workflows while maintaining clean separation of concerns and high testability.

The architecture is designed to evolve with changing requirements while maintaining backward compatibility and system stability.