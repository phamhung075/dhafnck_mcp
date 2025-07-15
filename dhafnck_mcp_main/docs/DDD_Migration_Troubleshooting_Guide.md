# DDD Migration Troubleshooting Guide - Strict Clean Architecture

## 🏗️ **New Architecture Overview (2025-07-02)**

The codebase has been migrated to a **strict clean DDD architecture** with **NO backward compatibility**. All test compatibility layers have been removed to enforce proper architectural boundaries.

### **Layer Structure:**
- **Domain:** Business logic, value objects, validation
- **Application:** Use cases, facades, factories, orchestration, services  
- **Infrastructure:** Data access, repositories, file/database operations, utilities, configuration
- **Interface:** Controllers, MCP tools, adapters, orchestrators, request/response handling

### **Recent MCP Tools Refactoring (2025-07-02):**
The `interface/mcp_tools/` folder has been **REMOVED** and files relocated to proper DDD layers:

**Removed Files:**
- ❌ `mcp_tools/tool_config.py` → ✅ `infrastructure/configuration/tool_config.py`
- ❌ `mcp_tools/path_resolver.py` → ✅ `infrastructure/utilities/path_resolver.py`
- ❌ `mcp_tools/project_manager.py` → ✅ `application/services/project_management_service.py`
- ❌ `mcp_tools/task_operation_handler.py` → ✅ `application/services/task_operation_service.py`
- ❌ `mcp_tools/simple_multi_agent_tools.py` → ✅ `interface/adapters/simple_multi_agent_adapter.py`
- ❌ `mcp_tools/tool_registration_orchestrator.py` → ✅ `interface/orchestrators/tool_registration_orchestrator.py`

**New Architecture Patterns:**
- ✅ Factory pattern for service creation (`application/factories/project_service_factory.py`)
- ✅ Adapter pattern for backward compatibility (`interface/adapters/`)
- ✅ Proper dependency injection and inversion of control
- ✅ Clean separation of infrastructure, application, and interface concerns

---

## 🚨 **BREAKING CHANGES - Test Migration Required** 
More detail on [BREAKING_CHANGES_SUMMARY.md](dhafnck_mcp_main/docs/BREAKING_CHANGES_SUMMARY.md)

### **Import Path Changes (2025-07-02):**
**❌ Old Imports (Broken):**
```python
from fastmcp.task_management.interface.mcp_tools.tool_config import ToolConfig
from fastmcp.task_management.interface.mcp_tools.path_resolver import PathResolver
from fastmcp.task_management.interface.mcp_tools.project_manager import ProjectManager
```

**✅ New Imports (Correct):**
```python
from fastmcp.task_management.infrastructure.configuration.tool_config import ToolConfig
from fastmcp.task_management.infrastructure.utilities.path_resolver import PathResolver
from fastmcp.task_management.application.services.project_management_service import ProjectManagementService
```

### **Backward Compatibility:**
The main `DDDCompliantMCPTools` class maintains backward compatibility through:
- `tools.project_manager` → Returns `ProjectManagementService` instance
- All existing controller access patterns remain unchanged
- Factory patterns provide proper dependency injection while maintaining test compatibility

### **Removed Components:**
- ❌ `TestCompatibilityAdapter` - No longer exists
- ❌ `manage_subtask()` method in `DDDCompliantMCPTools`
- ❌ `_handle_*` test methods in main class
- ❌ `ensure_brain_dir()` utility in interface layer

### **New Strict Architecture:**
```
📁 application/
├── factories/
│   └── task_facade_factory.py      # 🆕 Facade construction
├── facades/
│   └── task_application_facade.py  # ✅ Business orchestration

📁 infrastructure/
├── utilities/
│   └── directory_utils.py          # 🆕 File system utilities  

📁 interface/
├── controllers/                    # ✅ ALL tool registrations
│   ├── task_mcp_controller.py
│   ├── context_mcp_controller.py  
│   ├── project_mcp_controller.py   # 🆕
│   ├── agent_mcp_controller.py     # 🆕
│   └── call_agent_mcp_controller.py # 🆕
└── ddd_compliant_mcp_tools.py      # ✅ Clean orchestration only
```

---

## 🔧 **How to Fix Broken Tests**

### **1. Update Test Imports**

**❌ Old (Broken):**
```python
from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools

tools = DDDCompliantMCPTools()
result = tools.manage_subtask("list", "task_id")  # ❌ Method removed
result = tools._handle_list_tasks()  # ❌ Method removed
```

**✅ New (Correct):**
```python
from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools

tools = DDDCompliantMCPTools()
# Use controller directly
result = tools.task_controller.manage_subtask("list", "task_id")
# Or use specific controller methods
result = tools.task_controller.handle_list_search_next("list")
```

### **2. Controller-Based Testing**

**✅ Direct Controller Access:**
```python
def test_task_operations():
    tools = DDDCompliantMCPTools()
    
    # Access controllers directly
    task_controller = tools.task_controller
    context_controller = tools.context_controller
    project_controller = tools.project_controller
    agent_controller = tools.agent_controller
    
    # Use controller methods
    result = task_controller.manage_task("create", title="Test", description="Test task")
    subtask_result = task_controller.manage_subtask("add", "task_id", {"title": "Subtask"})
```

### **3. Facade-Based Testing**

**✅ Application Layer Testing:**
```python
def test_business_logic():
    tools = DDDCompliantMCPTools()
    
    # Access application facade
    facade = tools.task_facade
    
    # Use facade methods directly
    from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
    
    request = CreateTaskRequest(title="Test", description="Test task")
    result = facade.create_task(request)
```

### **4. Utility Function Migration**

**❌ Old (Broken):**
```python
from fastmcp.task_management.interface.ddd_compliant_mcp_tools import ensure_brain_dir
```

**✅ New (Correct):**
```python
from fastmcp.task_management.infrastructure.utilities.directory_utils import ensure_brain_dir
```

---

## 📋 **Test Migration Checklist**

### **For Integration Tests:**
- [ ] Replace `tools.manage_subtask()` → `tools.task_controller.manage_subtask()`
- [ ] Replace `tools._handle_*()` → `tools.task_controller.handle_*()`
- [ ] Update utility imports to infrastructure layer
- [ ] Use controller-specific methods for tool operations

### **For Unit Tests:**
- [ ] Test controllers individually via `tools.{controller_name}`
- [ ] Test facades directly via `tools.task_facade`
- [ ] Mock at appropriate layer boundaries
- [ ] Use proper DTOs for application layer testing

### **For MCP Tool Tests:**
- [ ] Test tool registration via `controller.register_tools(mock_mcp)`
- [ ] Test individual tools through controller methods
- [ ] Verify proper parameter passing and validation

---

## 🎯 **Recommended Test Patterns**

### **1. Controller Layer Testing**
```python
def test_controller_delegation():
    """Test that controllers properly delegate to application layer"""
    tools = DDDCompliantMCPTools()
    controller = tools.task_controller
    
    # Test delegation to facade
    result = controller.manage_task("create", title="Test", description="Test")
    assert result["success"] is True
```

### **2. Application Layer Testing**
```python
def test_facade_business_logic():
    """Test business logic in application facade"""
    from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
    from fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
    from fastmcp.task_management.infrastructure.services.file_auto_rule_generator import FileAutoRuleGenerator
    
    # Create facade directly
    repo_factory = TaskRepositoryFactory()
    auto_rule_gen = FileAutoRuleGenerator()
    facade_factory = TaskFacadeFactory(repo_factory, auto_rule_gen)
    facade = facade_factory.create_task_facade()
    
    # Test business logic
    request = CreateTaskRequest(title="Test", description="Test")
    result = facade.create_task(request)
```

### **3. Infrastructure Layer Testing**
```python
def test_infrastructure_utilities():
    """Test infrastructure utilities"""
    from fastmcp.task_management.infrastructure.utilities.directory_utils import ensure_brain_dir
    from pathlib import Path
    
    # Test utility functions
    brain_dir = ensure_brain_dir("/tmp/test_brain")
    assert isinstance(brain_dir, Path)
    assert brain_dir.exists()
```

---

## 🔍 **Common Migration Errors**

| **Error** | **Cause** | **Fix** |
|-----------|-----------|---------|
| `AttributeError: 'DDDCompliantMCPTools' has no attribute 'manage_subtask'` | Method removed | Use `tools.task_controller.manage_subtask()` |
| `AttributeError: 'DDDCompliantMCPTools' has no attribute '_handle_list_tasks'` | Method removed | Use `tools.task_controller.handle_list_search_next()` |
| `ImportError: cannot import name 'ensure_brain_dir'` | Moved to infrastructure | Import from `infrastructure.utilities.directory_utils` |
| `AttributeError: 'DDDCompliantMCPTools' has no attribute 'test_adapter'` | Adapter removed | Use controllers directly |

---

## 🚀 **Benefits of Strict Architecture**

1. **Clear Boundaries**: No mixing of concerns between layers
2. **Testability**: Each layer can be tested independently  
3. **Maintainability**: Changes isolated to appropriate layers
4. **Consistency**: Enforced architectural patterns
5. **Performance**: No compatibility overhead

---

## 📞 **Quick Reference**

**Main Class Access Points:**
- `tools.task_controller` → Task operations
- `tools.context_controller` → Context operations  
- `tools.project_controller` → Project operations
- `tools.agent_controller` → Agent operations
- `tools.call_agent_controller` → Call agent operations
- `tools.task_facade` → Direct business logic access
- `tools.project_manager` → Project management

**No longer available (removed for strict DDD):**
- ❌ `tools.manage_subtask()`
- ❌ `tools._handle_*()`  
- ❌ `tools.test_adapter`
- ❌ Backward compatibility methods

---

Current Problem
The application layer (rule_application_facade.py) imports from the interface layer (rule_orchestration_controller.py), creating a circular dependency and violating DDD boundaries.
DDD Principle
Controllers (interface layer) should depend on facades (application layer), not the other way around.
Application layer should only depend on domain and infrastructure.
Refactor Plan
1. Remove All Interface Layer Imports from Application Layer
Eliminate any import of RuleOrchestrationController (or any controller) from rule_application_facade.py.
2. Move Orchestration Logic to Application Layer
If the application layer needs orchestration logic, define it as a service or use case in the application layer.
The controller should instantiate and use the facade/service, not the other way around.
3. Controllers Delegate to Facades
The controller (rule_orchestration_controller.py) should import and use the facade (RuleApplicationFacade), not vice versa.
4. Update All Usages
Update any code or tests that expected the old (incorrect) dependency direction.

---

**Migration Strategy:** Update tests to use the appropriate controller or facade for the operation being tested. Follow the new layer boundaries strictly.

**Rule STRICT**: 
- need follow DDD architect, move code is note on good position, good layer, refactor code. 
- when debug, code, refactore need continue update information on this file for other agent can work easier