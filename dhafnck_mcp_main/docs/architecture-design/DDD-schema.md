# DDD Architecture Schema - Detailed Flow Documentation

## 🏗️ System Architecture Overview

### Complete System Flow Diagram
```
┌──────────────────────────────────────────────────────┐
│                  MCP Client Request                   │
│         (Claude, VS Code, Other MCP Clients)         │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│              MCP Protocol Transport Layer             │
│  • WebSocket Connection Establishment                │
│  • HTTP/2 Request Handling                          │
│  • Connection Keep-Alive Management                 │
│  • Request ID Generation & Tracking                 │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│              FastMCP Server Entry Point              │
│  • Server Instance Creation                         │
│  • Environment Configuration Loading                │
│  • Tool Registration Process                        │
│  • Middleware Stack Initialization                  │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│            Authentication & Authorization             │
│  • JWT Token Extraction from Headers                │
│  • Token Signature Verification                     │
│  • User ID & Permissions Extraction                 │
│  • Request Context Enrichment                       │
│  • Rate Limiting Check                             │
│  • API Key Validation (if configured)              │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│         INTERFACE LAYER (MCP Controllers)            │
│                                                      │
│  Request Reception & Initial Processing:            │
│  ├─ Parse MCP Tool Name & Action                    │
│  ├─ Extract Raw Parameters from Request             │
│  ├─ Identify Target Controller                      │
│  └─ Route to Appropriate Handler                    │
│                                                      │
│  Parameter Validation & Transformation:             │
│  ├─ Type Coercion (string → bool/int/list)         │
│  ├─ Required Parameter Validation                   │
│  ├─ Format Validation (UUID, dates, enums)         │
│  ├─ Default Value Application                       │
│  └─ Parameter Sanitization                          │
│                                                      │
│  Request DTO Construction:                          │
│  ├─ Map MCP Parameters to DTO Fields               │
│  ├─ Apply Business Context (user_id, project_id)   │
│  ├─ Add Metadata & Timestamps                      │
│  └─ Create Immutable Request Object                │
│                                                      │
│  Error Handling Setup:                              │
│  ├─ Exception Handler Registration                  │
│  ├─ Timeout Configuration                           │
│  └─ Transaction Boundary Setup                      │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│      APPLICATION LAYER (Facades & Use Cases)         │
│                                                      │
│  Facade Entry & Orchestration:                      │
│  ├─ Receive Request DTO from Interface              │
│  ├─ Begin Database Transaction                      │
│  ├─ Initialize Audit Trail                          │
│  └─ Setup Event Collection                          │
│                                                      │
│  Use Case Selection & Execution:                    │
│  ├─ Identify Required Use Cases                     │
│  ├─ Resolve Dependencies Between Use Cases          │
│  ├─ Execute Use Cases in Correct Order              │
│  └─ Collect Intermediate Results                    │
│                                                      │
│  Cross-Cutting Concerns:                            │
│  ├─ Logging & Monitoring                           │
│  ├─ Performance Metrics Collection                  │
│  ├─ Security Context Validation                     │
│  └─ Business Rule Pre-validation                    │
│                                                      │
│  Domain Service Coordination:                       │
│  ├─ Instantiate Required Domain Services            │
│  ├─ Prepare Domain Entity Collections               │
│  ├─ Configure Service Dependencies                  │
│  └─ Execute Domain Operations                       │
│                                                      │
│  Infrastructure Service Usage:                      │
│  ├─ Repository Factory Selection                    │
│  ├─ Cache Strategy Determination                    │
│  ├─ External Service Integration                    │
│  └─ Event Bus Configuration                         │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│         DOMAIN LAYER (Business Logic Core)           │
│                                                      │
│  Entity Lifecycle Management:                       │
│  ├─ Entity Creation with Validation                 │
│  ├─ Identity Generation (UUID)                      │
│  ├─ State Initialization                           │
│  └─ Invariant Enforcement                          │
│                                                      │
│  Business Rule Execution:                          │
│  ├─ Pre-condition Validation                       │
│  ├─ Business Logic Application                     │
│  ├─ State Transition Management                    │
│  └─ Post-condition Verification                    │
│                                                      │
│  Domain Service Operations:                        │
│  ├─ Complex Business Calculations                  │
│  ├─ Multi-Entity Coordination                      │
│  ├─ Business Process Orchestration                 │
│  └─ Domain Event Generation                        │
│                                                      │
│  Value Object Processing:                          │
│  ├─ Immutable Object Creation                      │
│  ├─ Value Validation & Constraints                 │
│  ├─ Business Meaning Enforcement                   │
│  └─ Type Safety Guarantees                         │
│                                                      │
│  Specification Pattern Application:                 │
│  ├─ Business Rule Composition                      │
│  ├─ Complex Condition Evaluation                   │
│  ├─ Reusable Logic Encapsulation                  │
│  └─ Query Criteria Building                        │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│     INFRASTRUCTURE LAYER (Technical Services)        │
│                                                      │
│  Repository Pattern Implementation:                 │
│  ├─ Environment Detection                          │
│  │   ├─ Check DATABASE_TYPE Variable               │
│  │   ├─ Verify Redis Availability                  │
│  │   └─ Select Repository Strategy                 │
│  │                                                  │
│  ├─ Repository Factory Selection                    │
│  │   ├─ Test: MockRepository                       │
│  │   ├─ Local: SQLiteRepository                    │
│  │   ├─ Cloud: SupabaseRepository                  │
│  │   └─ Cached: RedisDecoratedRepository           │
│  │                                                  │
│  ├─ Database Operations                            │
│  │   ├─ Connection Pool Management                 │
│  │   ├─ Query Optimization                         │
│  │   ├─ Transaction Handling                       │
│  │   └─ Lazy Loading Strategy                      │
│  │                                                  │
│  └─ ORM Mapping                                    │
│      ├─ Entity to Model Conversion                 │
│      ├─ Model to Entity Conversion                 │
│      ├─ Relationship Management                    │
│      └─ Data Type Mapping                          │
│                                                      │
│  Caching Layer:                                     │
│  ├─ Cache Key Generation                           │
│  ├─ TTL Management                                 │
│  ├─ Cache Invalidation Strategy                    │
│  ├─ Multi-Level Cache Coordination                 │
│  └─ Cache Warming & Preloading                     │
│                                                      │
│  External Service Integration:                      │
│  ├─ API Client Configuration                       │
│  ├─ Authentication & Authorization                 │
│  ├─ Request/Response Transformation                │
│  ├─ Error Handling & Retry Logic                   │
│  └─ Circuit Breaker Pattern                        │
│                                                      │
│  Event Infrastructure:                              │
│  ├─ Event Bus Implementation                       │
│  ├─ Event Persistence                              │
│  ├─ Event Replay Capability                        │
│  └─ Event Subscription Management                  │
└──────────────────────────────────────────────────────┘
```

## 📊 Detailed Request Flow Sequence

### 1. MCP Tool Request Flow (manage_task example)
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ MCP Client  │     │   FastMCP   │     │ Application │     │   Domain    │
│             │     │   Server    │     │    Layer    │     │    Layer    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                    │                    │                    │
       │ 1. Tool Request    │                    │                    │
       │ manage_task(       │                    │                    │
       │   action="create", │                    │                    │
       │   title="Task",    │                    │                    │
       │   branch_id="xyz") │                    │                    │
       ├───────────────────>│                    │                    │
       │                    │                    │                    │
       │                    │ 2. Auth Check      │                    │
       │                    ├──────────┐         │                    │
       │                    │          │         │                    │
       │                    │<─────────┘         │                    │
       │                    │                    │                    │
       │                    │ 3. Route to        │                    │
       │                    │    Controller      │                    │
       │                    ├──────────┐         │                    │
       │                    │          │         │                    │
       │                    │<─────────┘         │                    │
       │                    │                    │                    │
       │                    │ 4. Create DTO      │                    │
       │                    │    & Validate      │                    │
       │                    ├───────────────────>│                    │
       │                    │                    │                    │
       │                    │                    │ 5. Execute         │
       │                    │                    │    Use Case       │
       │                    │                    ├──────────┐         │
       │                    │                    │          │         │
       │                    │                    │<─────────┘         │
       │                    │                    │                    │
       │                    │                    │ 6. Domain Logic    │
       │                    │                    ├───────────────────>│
       │                    │                    │                    │
       │                    │                    │                    ├──┐
       │                    │                    │                    │  │ 7. Business
       │                    │                    │                    │  │    Rules
       │                    │                    │                    │<─┘
       │                    │                    │                    │
       │                    │                    │ 8. Entity Created  │
       │                    │                    │<───────────────────┤
       │                    │                    │                    │
       │                    │                    │ 9. Persist         │
       │                    │                    │    to Repository   │
       │                    │                    ├──────────┐         │
       │                    │                    │          │         │
       │                    │                    │          ↓         │
       │                    │                    │    Infrastructure  │
       │                    │                    │        Layer       │
       │                    │                    │          │         │
       │                    │                    │<─────────┘         │
       │                    │                    │                    │
       │                    │ 10. Response DTO   │                    │
       │                    │<───────────────────┤                    │
       │                    │                    │                    │
       │ 11. MCP Response   │                    │                    │
       │<───────────────────┤                    │                    │
       │                    │                    │                    │
```

## 🔄 Layer Interaction Flows

### Interface → Application Flow
```
Interface Layer (Controller)
│
├─ 1. Receive MCP Request
│    └─ Extract tool name, action, parameters
│
├─ 2. Parameter Processing Pipeline
│    ├─ Raw Parameter Extraction
│    ├─ Type Detection & Coercion
│    │   ├─ String → Boolean ("true", "1", "yes" → true)
│    │   ├─ String → Integer ("123" → 123)
│    │   ├─ String → List ("[1,2,3]" or "1,2,3" → [1,2,3])
│    │   └─ JSON String → Object ('{"key":"value"}' → {key: "value"})
│    │
│    ├─ Validation Pipeline
│    │   ├─ Required Field Check
│    │   ├─ Format Validation (UUID, Email, URL)
│    │   ├─ Range Validation (0-100 for percentages)
│    │   ├─ Enum Validation (status in allowed values)
│    │   └─ Business Context Validation
│    │
│    └─ Default Value Application
│
├─ 3. Request DTO Construction
│    ├─ Map Parameters to DTO Fields
│    ├─ Add System Context (user_id, timestamp)
│    ├─ Apply Security Context
│    └─ Create Immutable Request Object
│
├─ 4. Facade Selection
│    ├─ Determine Target Facade
│    ├─ Resolve Facade Dependencies
│    └─ Get Facade Instance
│
└─ 5. Delegate to Application Layer
     ├─ Pass Request DTO
     ├─ Handle Response
     └─ Format MCP Response
```

### Application → Domain Flow
```
Application Layer (Facade/Use Case)
│
├─ 1. Receive Request DTO
│    └─ Validate Application-Level Rules
│
├─ 2. Transaction Management
│    ├─ Begin Transaction
│    ├─ Setup Rollback Handlers
│    └─ Configure Isolation Level
│
├─ 3. Use Case Orchestration
│    ├─ Identify Required Use Cases
│    ├─ Resolve Dependencies
│    ├─ Execute in Order
│    │   ├─ CreateTaskUseCase
│    │   ├─ AssignAgentUseCase
│    │   └─ UpdateContextUseCase
│    └─ Aggregate Results
│
├─ 4. Domain Service Invocation
│    ├─ Get Domain Services
│    ├─ Prepare Domain Entities
│    ├─ Execute Domain Logic
│    │   ├─ Entity Creation
│    │   ├─ Business Rule Validation
│    │   ├─ State Transitions
│    │   └─ Event Generation
│    └─ Collect Domain Events
│
├─ 5. Repository Interaction
│    ├─ Get Repository Instance
│    ├─ Execute Persistence
│    └─ Handle Persistence Errors
│
└─ 6. Response Preparation
     ├─ Convert Entities to DTOs
     ├─ Add Metadata
     └─ Return Response
```

### Domain → Infrastructure Flow
```
Domain Layer
│
├─ 1. Repository Interface Usage
│    ├─ Define Repository Contract
│    ├─ Request Data Operation
│    └─ Receive Domain Entities
│
├─ 2. Domain Service Requirements
│    ├─ Specify Service Interface
│    ├─ Define Expected Behavior
│    └─ Handle Service Results
│
└─ 3. Event Publishing
     ├─ Generate Domain Events
     ├─ Pass to Event Bus Interface
     └─ No Knowledge of Subscribers

Infrastructure Layer (Implementing Domain Interfaces)
│
├─ 1. Repository Implementation
│    ├─ Environment Detection
│    │   ├─ Test Environment → MockRepository
│    │   ├─ Local Development → SQLiteRepository
│    │   └─ Production → SupabaseRepository
│    │
│    ├─ Database Operations
│    │   ├─ Connection Management
│    │   ├─ Query Execution
│    │   ├─ Transaction Handling
│    │   └─ Error Recovery
│    │
│    └─ Caching Layer
│         ├─ Check Cache First
│         ├─ Database Fallback
│         └─ Cache Update
│
├─ 2. External Service Integration
│    ├─ API Configuration
│    ├─ Request Transformation
│    ├─ Response Mapping
│    └─ Error Handling
│
└─ 3. Event Infrastructure
     ├─ Event Bus Implementation
     ├─ Event Storage
     └─ Event Distribution
```

## 🔀 Complete Request/Response Flow

### Detailed Step-by-Step Flow
```
1. CLIENT INITIATES REQUEST
   ↓
2. MCP PROTOCOL TRANSPORT
   ├─ WebSocket: Persistent connection, bi-directional
   └─ HTTP/2: Request-response pattern
   ↓
3. FASTMCP SERVER RECEIVES
   ├─ Connection validation
   ├─ Protocol version check
   └─ Request queue management
   ↓
4. AUTHENTICATION MIDDLEWARE
   ├─ Extract auth token
   ├─ Validate signature
   ├─ Load user context
   └─ Check permissions
   ↓
5. RATE LIMITING
   ├─ Check request count
   ├─ Validate time window
   └─ Apply throttling if needed
   ↓
6. REQUEST ROUTING
   ├─ Parse tool name
   ├─ Extract action
   └─ Route to controller
   ↓
7. CONTROLLER PROCESSING
   ├─ Parameter extraction
   ├─ Type coercion
   ├─ Validation
   └─ DTO creation
   ↓
8. FACADE ORCHESTRATION
   ├─ Transaction start
   ├─ Use case selection
   ├─ Service coordination
   └─ Event collection
   ↓
9. DOMAIN LOGIC EXECUTION
   ├─ Entity operations
   ├─ Business rules
   ├─ State management
   └─ Event generation
   ↓
10. INFRASTRUCTURE OPERATIONS
    ├─ Database queries
    ├─ Cache management
    ├─ External services
    └─ Event publishing
    ↓
11. RESPONSE CONSTRUCTION
    ├─ Entity to DTO mapping
    ├─ Success/error formatting
    ├─ Metadata addition
    └─ Response validation
    ↓
12. TRANSACTION COMPLETION
    ├─ Commit/rollback
    ├─ Event dispatch
    └─ Cache invalidation
    ↓
13. RESPONSE TRANSFORMATION
    ├─ DTO to MCP format
    ├─ Add protocol headers
    └─ Serialize response
    ↓
14. SEND TO CLIENT
    ├─ Protocol transport
    ├─ Connection management
    └─ Acknowledgment
```

## 🔄 Error Flow Sequence

### Error Handling Pipeline
```
ERROR OCCURRENCE
│
├─ DOMAIN LAYER ERRORS
│   ├─ Business Rule Violation
│   │   ├─ Capture violation details
│   │   ├─ Generate domain error event
│   │   └─ Throw domain exception
│   │
│   ├─ Entity Validation Failure
│   │   ├─ Collect validation errors
│   │   ├─ Create validation result
│   │   └─ Return to application layer
│   │
│   └─ State Transition Error
│       ├─ Log invalid transition
│       ├─ Preserve current state
│       └─ Raise state exception
│
├─ APPLICATION LAYER ERRORS
│   ├─ Use Case Failure
│   │   ├─ Rollback transaction
│   │   ├─ Log failure context
│   │   └─ Create error response
│   │
│   ├─ Service Coordination Error
│   │   ├─ Compensate completed operations
│   │   ├─ Release resources
│   │   └─ Build error details
│   │
│   └─ Authorization Failure
│       ├─ Log security event
│       ├─ Clear sensitive data
│       └─ Return forbidden response
│
├─ INFRASTRUCTURE LAYER ERRORS
│   ├─ Database Connection Error
│   │   ├─ Attempt reconnection
│   │   ├─ Switch to fallback
│   │   └─ Queue for retry
│   │
│   ├─ External Service Error
│   │   ├─ Apply circuit breaker
│   │   ├─ Use cached data
│   │   └─ Return degraded response
│   │
│   └─ Cache Failure
│       ├─ Bypass cache
│       ├─ Direct database query
│       └─ Log cache issue
│
└─ INTERFACE LAYER ERRORS
    ├─ Validation Error
    │   ├─ Format error details
    │   ├─ Include field information
    │   └─ Return 400 response
    │
    ├─ Authentication Error
    │   ├─ Clear auth context
    │   ├─ Log attempt
    │   └─ Return 401 response
    │
    └─ Protocol Error
        ├─ Log protocol violation
        ├─ Send error frame
        └─ Close connection
```

## 🎯 Event Flow Architecture

### Domain Event Flow
```
DOMAIN EVENT GENERATION
│
├─ 1. Event Creation
│    ├─ Entity State Change
│    ├─ Business Process Completion
│    └─ Domain Rule Trigger
│
├─ 2. Event Properties
│    ├─ Event ID (UUID)
│    ├─ Event Type
│    ├─ Aggregate ID
│    ├─ Timestamp
│    ├─ User Context
│    └─ Event Payload
│
├─ 3. Event Collection
│    ├─ In-Memory Queue
│    ├─ Transaction Scope
│    └─ Order Preservation
│
├─ 4. Event Publishing (Post-Transaction)
│    ├─ Transaction Commit
│    ├─ Event Bus Dispatch
│    └─ Async Processing
│
├─ 5. Event Subscription
│    ├─ Handler Registration
│    ├─ Filter Application
│    └─ Priority Ordering
│
├─ 6. Event Processing
│    ├─ Handler Invocation
│    ├─ Error Isolation
│    └─ Retry Logic
│
└─ 7. Event Storage
     ├─ Event Store Write
     ├─ Event Replay Support
     └─ Audit Trail
```

## 📊 Data Flow Through Layers

### Request Data Transformation
```
RAW MCP REQUEST
│
├─ Interface Layer Transform
│   Raw Parameters → Validated Parameters → Request DTO
│
├─ Application Layer Transform
│   Request DTO → Domain Commands → Use Case Input
│
├─ Domain Layer Transform
│   Commands → Entities → Value Objects → Events
│
└─ Infrastructure Layer Transform
    Entities → ORM Models → Database Records

RESPONSE PATH (Reverse)
│
├─ Infrastructure Layer Transform
│   Database Records → ORM Models → Entities
│
├─ Domain Layer Transform
│   Entities → Domain Results → Events
│
├─ Application Layer Transform
│   Domain Results → Response DTOs → Service Results
│
└─ Interface Layer Transform
    Response DTOs → MCP Response → JSON Output
```

## 🔐 Security Flow

### Authentication & Authorization Pipeline
```
REQUEST SECURITY CHECK
│
├─ 1. Transport Security
│    ├─ TLS/SSL Verification
│    ├─ Certificate Validation
│    └─ Encryption Check
│
├─ 2. Authentication
│    ├─ Token Extraction
│    │   ├─ Bearer Token (Header)
│    │   ├─ API Key (Header/Query)
│    │   └─ Session Cookie
│    │
│    ├─ Token Validation
│    │   ├─ Signature Verification
│    │   ├─ Expiry Check
│    │   └─ Revocation Check
│    │
│    └─ Identity Resolution
│        ├─ User ID Extraction
│        ├─ User Profile Load
│        └─ Context Enrichment
│
├─ 3. Authorization
│    ├─ Permission Check
│    │   ├─ Resource Access
│    │   ├─ Action Permission
│    │   └─ Data Scope
│    │
│    ├─ Role Validation
│    │   ├─ Role Assignment
│    │   ├─ Role Hierarchy
│    │   └─ Role Constraints
│    │
│    └─ Policy Enforcement
│        ├─ Business Rules
│        ├─ Compliance Requirements
│        └─ Audit Requirements
│
└─ 4. Security Context
     ├─ User Context Creation
     ├─ Permission Matrix
     ├─ Audit Trail Start
     └─ Security Token Generation
```

## 🚀 Performance Optimization Flows

### Caching Strategy Flow
```
REQUEST WITH CACHING
│
├─ 1. Cache Check Pipeline
│    ├─ Generate Cache Key
│    ├─ Check L1 Cache (In-Memory)
│    ├─ Check L2 Cache (Redis)
│    └─ Check L3 Cache (CDN)
│
├─ 2. Cache Hit Path
│    ├─ Validate Cache Entry
│    ├─ Check TTL
│    ├─ Return Cached Data
│    └─ Update Access Metrics
│
├─ 3. Cache Miss Path
│    ├─ Execute Full Request
│    ├─ Generate Response
│    ├─ Update All Cache Levels
│    └─ Set Appropriate TTL
│
├─ 4. Cache Invalidation
│    ├─ Entity Update Trigger
│    ├─ Cascade Invalidation
│    ├─ Related Cache Clear
│    └─ Cache Rebuild Queue
│
└─ 5. Cache Warming
     ├─ Predictive Loading
     ├─ Batch Processing
     ├─ Off-Peak Scheduling
     └─ Priority Queuing
```

### Database Query Optimization Flow
```
DATABASE OPERATION
│
├─ 1. Query Planning
│    ├─ Parse Request
│    ├─ Analyze Indexes
│    ├─ Choose Execution Plan
│    └─ Estimate Cost
│
├─ 2. Connection Management
│    ├─ Get from Pool
│    ├─ Health Check
│    ├─ Transaction Start
│    └─ Isolation Level
│
├─ 3. Query Execution
│    ├─ Prepared Statement
│    ├─ Parameter Binding
│    ├─ Batch Processing
│    └─ Result Streaming
│
├─ 4. Lazy Loading
│    ├─ Initial Entity Load
│    ├─ Relationship Proxies
│    ├─ On-Demand Fetch
│    └─ N+1 Prevention
│
└─ 5. Result Processing
     ├─ Row Mapping
     ├─ Entity Hydration
     ├─ Collection Building
     └─ Memory Management
```

## 🔄 Transaction Management Flow

### Distributed Transaction Coordination
```
TRANSACTION LIFECYCLE
│
├─ 1. Transaction Initiation
│    ├─ Begin Transaction
│    ├─ Set Isolation Level
│    ├─ Create Save Points
│    └─ Register Participants
│
├─ 2. Operation Execution
│    ├─ Domain Operations
│    │   ├─ Entity Updates
│    │   ├─ State Changes
│    │   └─ Event Generation
│    │
│    ├─ Infrastructure Operations
│    │   ├─ Database Writes
│    │   ├─ Cache Updates
│    │   └─ External Calls
│    │
│    └─ Compensation Tracking
│        ├─ Rollback Actions
│        ├─ Undo Operations
│        └─ State Restoration
│
├─ 3. Commit Phase
│    ├─ Pre-Commit Validation
│    ├─ Two-Phase Commit
│    │   ├─ Prepare Phase
│    │   └─ Commit Phase
│    ├─ Event Publishing
│    └─ Cache Invalidation
│
└─ 4. Rollback Handling
     ├─ Error Detection
     ├─ Rollback Execution
     ├─ Compensation Actions
     ├─ State Cleanup
     └─ Error Reporting
```

## 📈 Monitoring & Observability Flow

### Request Tracing Pipeline
```
REQUEST MONITORING
│
├─ 1. Trace Initiation
│    ├─ Generate Trace ID
│    ├─ Create Root Span
│    ├─ Set Context
│    └─ Start Timer
│
├─ 2. Layer Instrumentation
│    ├─ Interface Layer
│    │   ├─ Request Receipt
│    │   ├─ Validation Time
│    │   └─ DTO Creation
│    │
│    ├─ Application Layer
│    │   ├─ Use Case Duration
│    │   ├─ Service Calls
│    │   └─ Transaction Time
│    │
│    ├─ Domain Layer
│    │   ├─ Business Logic
│    │   ├─ Rule Evaluation
│    │   └─ Event Generation
│    │
│    └─ Infrastructure Layer
│        ├─ Database Queries
│        ├─ Cache Operations
│        └─ External APIs
│
├─ 3. Metrics Collection
│    ├─ Performance Metrics
│    │   ├─ Response Time
│    │   ├─ Throughput
│    │   └─ Error Rate
│    │
│    ├─ Business Metrics
│    │   ├─ Task Creation Rate
│    │   ├─ Completion Rate
│    │   └─ User Activity
│    │
│    └─ System Metrics
│        ├─ CPU Usage
│        ├─ Memory Usage
│        └─ Connection Pool
│
└─ 4. Log Aggregation
     ├─ Structured Logging
     ├─ Context Propagation
     ├─ Error Tracking
     └─ Audit Trail
```

## 🔧 Dependency Resolution Flow

### Module Dependency Rules
```
DEPENDENCY DIRECTION RULES

Interface Layer
    ↓ (depends on)
Application Layer
    ↓ (depends on)
Domain Layer
    ↑ (implemented by)
Infrastructure Layer

FORBIDDEN DEPENDENCIES:
- Domain → Application (❌)
- Domain → Interface (❌)
- Domain → Infrastructure (❌)
- Application → Interface (❌)

ALLOWED DEPENDENCIES:
- Interface → Application (✅)
- Application → Domain (✅)
- Infrastructure → Domain (✅)
- Infrastructure → Infrastructure (✅)
```

### Dependency Injection Flow
```
DEPENDENCY INJECTION CONTAINER
│
├─ 1. Registration Phase
│    ├─ Interface Registration
│    ├─ Implementation Binding
│    ├─ Lifetime Management
│    └─ Factory Registration
│
├─ 2. Resolution Phase
│    ├─ Dependency Graph Build
│    ├─ Circular Check
│    ├─ Instance Creation
│    └─ Property Injection
│
├─ 3. Scope Management
│    ├─ Singleton Scope
│    ├─ Request Scope
│    ├─ Transient Scope
│    └─ Custom Scopes
│
└─ 4. Disposal Phase
     ├─ Reverse Order Disposal
     ├─ Resource Cleanup
     ├─ Connection Close
     └─ Memory Release
```