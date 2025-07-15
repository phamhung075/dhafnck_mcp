---
description: GLOBAL RULE
alwaysApply: true
tags: [GLOBAL-RULE, DEFAULT_USER, CURSOR-TOOLS, FILE-RULE, AGENT-MANAGEMENT, TASK-MANAGEMENT, Development-Methodology, MEMORY, CONTEXT, TOOL-COUNTING, RUNTIME-CONFIGURATION, TOOL-CONFIGURATIONS, OPERATIONAL-WORKFLOW]
---

## 🌍 GLOBAL RULE
#GLOBAL-RULE
-try change document and code to use uuid unique auto generate for task, subtask, context, project, ... (all table) 
  

### User Identification
#DEFAULT_USER
  

- **Default User**: `default_user` (proactively identify if unknown)

- **Environment**: Cursor AI Editor Chat Mode

- **Project ID**: see PROJECT_ID, if PROJECT_ID not available, find on `<PROJECT_ROOT>/<PROJECT_ID> (name folder project), if any folder exist nor not match id demande default_user

- **Project Root**: PROJECT_ROOT

- **Username**: `<whoami command result>`

  

### Available Cursor Tools
#CURSOR-TOOLS
  

- `read_file`: Read codebase file contents

- `list_dir`: Directory structure listing

- `codebase_search`: Semantic codebase searches

- `grep_search`: Exact keyword/pattern searches

- `file_search`: Fuzzy filename matching

- `web_search`: Web search capabilities

- `fetch_rules`: Retrieve specific rules

- `edit_file`: File editing and creation

- `delete_file`: Autonomous file deletion

- `run_terminal_cmd`: Terminal command execution

  

---

  

### 🔧 CORE OPERATIONAL RULES

  

#### File Protection & Editing
#FILE-RULE
  

- **Protection**: When `protect: true`, files are READ-ONLY

- **Edit Strategy**: ALWAYS edit files in small chunks

- **File Creation**: ALWAYS ask default_user before creating new files

- **No Root Creation**: No permission to create files in project root directory

- **Path Usage**: ALWAYS use absolute paths from `/home` for commands for Cursor Tools

- **Project Structure**: Respect existing structure unless changes requested

  

#### Agent & Task Management
#AGENT-MANAGEMENT #TASK-MANAGEMENT 
  

- **Sequential Thinking**: ALWAYS when first step of `sequential-thinking` call_agent() first for thingking complex requests

- **Agent Priority**: Call appropriate specialized agent before processing

- **Task Splitting**: Use task management agent to break down complex demands to tasks and subtasks

- **Agent Combination**: Assigne multiple agents for complex tasks when necessary

- **Context Provision**: Always provide sufficient context for agent understanding, include documents path (if document relative to task exist) on tasks for help agent take context faster

  

#### Development Methodology
#Development-Methodology
  

- **TDD Approach**: Write failing test → Implement code → Pass test → Refactor → Repeat

- **Root Cause Focus**: Fix root causes, not symptoms

- **Detailed Summaries**: Comprehensive summaries without missing important details

- **Error Handling**: Fix everything automatically, continue without asking when CONTINUE_AUTOMATIC is ON, ai must asking himseft what cause of this error, using  `sequential-thinking`

  

#### Memory & Context Management
#MEMORY #CONTEXT #TOOL-COUNTING

  

- **Tool Counting**: Increment tool count with each usage, reset when >20

- **Context Reset**: Call manage_context() when tool count exceeds threshold

- **Token Monitoring**: Monitor for requests exceeding Pro plan limits, terminate if exceeded

  

---

  

### ⚙️ RUNTIME CONFIGURATION
#RUNTIME-CONFIGURATION
  

#### Runtime Constants (Fixed Values) :  See Runtime Constants (Fixed Values) on <PROJECT_ROOT>/.cursor/settings.md

  

#### Runtime Variables (Dynamic Values): Runtime Variables (Dynamic Values) on <PROJECT_ROOT>/.cursor/settings.md

  
---

  

### 🛠️ TOOL CONFIGURATIONS
#TOOL-CONFIGURATIONS

  

#### Custom Tools (Specialized MCP Tools)
| Tool                   | 🛠️ Purpose                               | ⏳ Display Before                         | ✅ Display After             | ⚙️ Action                                                                                                                                                  |
| ---------------------- | ----------------------------------------- | ---------------------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🤖 `call_agent`        | Call specialized agent for specific tasks | "🔄 Loading Agents Information..."       | "🔁 Switch to agent"        | **AI Role Switch**: The assistant adopts the agent’s expertise, knowledge base, behavioral patterns, and tools. Ready to operate as the designated expert. |
| 📋 `manage_task`       | Manage project tasks                      | "🔄 Loading Task Information..."         | "✅ Tasks loaded"            | Task list initialized: ready for viewing, updating, or tracking, next task.                                                                                |
| 🧩 `manage_subtask`    | Manage project subtasks                   | "🔄 Loading Subtask Information..."      | "✅ Subtasks ready"          | Subtasks are linked and ready for hierarchical assignment under parent tasks.                                                                              |
| 🧠 `manage_context`    | Manage session context                    | "🔄 Loading Context Information..."      | "✅ Context loaded"          | Session memory and flow context restored. Ensures continuity in the assistant's understanding.                                                             |
| 🗂️ `manage_project`   | Manage project information                | "🔄 Loading Project Information..."      | "📁 Project details loaded" | Project metadata (e.g. ID, name, owner, etc.) fetched and available for interaction.                                                                       |
| 🧾 `manage_rule`       | Manage rule information                   | "🔄 Loading Rule Information..."         | "📜 Rules available"        | Validation, business, or behavioral rules are now accessible for enforcement or modification.                                                              |
| 🩺 `manage_connection` | Perform system health checks              | "🔄 Loading Health Check Information..." | "📡 System status updated"  | Health diagnostics completed. Reports on backend, APIs, services, or runtime environment integrity.                                                        |

---

## 🔄 OPERATIONAL WORKFLOW
#OPERATIONAL-WORKFLOW
  

use MASTER WORKFLOW SEQUENCE adaptif

  

---

  

## 🚨 CRITICAL REMINDERS

  
- **Always Apply**: This configuration is mandatory for all sessions, must run first before reponse to user

- **User-First**: Proactively identify and serve default_user needs

- **Quality Focus**: Detailed, accurate responses without missing information

- **Automatic Operation**: Continue tasks automatically when configured

- **Protection Respect**: Never modify protected files when protect=true







---
description: AI Assistant Core Operating Rules - Runtime variables, session management, tool usage, agent interactions, and orchestration guidelines.
globs: 
alwaysApply: true
task: AI Assistant Core Operating Rules
step: Core
task_id: CORE-001
title: AI Assistant Core Operating Rules
previous_task: N/A
next_task: N/A
version: 0.0.1
agent: "@uber_orchestrator_agent"
orchestrator: "@uber_orchestrator_agent"
---
This document outlines the core operating rules for the AI Assistant, designed for clear and efficient processing by AI agents. These rules govern runtime variables, session management, tool usage, agent interactions, file access, and overall AI assistant orchestration.


> **📋 For Detailed MCP System Rules**: See [MCP Task Management: Best Practices Guide.mdc](00_RULES/02_AI-DOCS/TaskManagement/best_practices.mdc) for comprehensive MCP system architecture, workflows, task management, agent coordination, and context management guidelines.

### 🧠 **AI Assistant Core Operating Rules**

#### 1. **Runtime Variables Management**
*   **Variables**: Runtime variables are defined in `.cursor/settings.json` and managed automatically by the system.
*   **Path Reference**: Refer to `@need-update-this-file-if-change-project-tree.mdc` for path information.

#### 2. **Session Initialization**
At the beginning of each new session, perform the following steps:
1.  **Load MCP context** using `MCP tools`.
2.  **Read the core rule file**: `MCP Task Management: Best Practices Guide.mdc`.


#### 3. **During Chat Session**

##### A. **Tool Usage**
*   **Tool Call Tracking**: **Tool usage is automatically tracked** according to settings configuration.
*   **Context Sync**: **Automatic context synchronization** occurs based on configured thresholds via `manage_context()`.

##### B. **Terminal Commands**
*   **Timeout Protection**: All terminal commands **must be run with timeout protection wrapper**.
*   **Force Quit**: If no result is obtained after `20` seconds, **force quit the command**.
*   **Result Display**: **Always show the result if any**.

##### C. **MCP Agent Tool Calls**
**Use the following sequence for each agent interaction**:
*   `"Call Agent..."` → **`call_agent()`**.
*   `"Retrieve Knowledge..."` → (gather all relevant information).
*   `"Switch Agent Capacity..."` → (end call).
*   `"Using dhafnck Tool..."` → (for calls to tools that are not `call_agent()`).

#### 4. **General Context Management Principles**
*   **Context Updates**: **Always check and update context** from `.cursor/rules/auto_rule.mdc`.
*   **Context Sync**: **Use `manage_context()` for context updates relative to tasks**.
*   **Role Alignment**: **Align the AI's role and context automatically with the current task or subtask**.
*   **Progress Logging**: **Regularly log progress and insights during implementation**.
*   **Session Continuity**: **Update next steps to maintain session continuity** and guide subsequent actions.

#### 5. **File Access Rules**
*   **Restricted Access**: **NEVER directly access files within `.cursor/rules/tasks/**/*`**.
*   **MCP Server Usage**: **Use the `dhafnck_mcp` MCP server to manage all tasks and data**.
*   **Manual Access Exception**: Only access these files manually if the **user explicitly requests it**.
*   **Rule File Behavior**: The file `.cursor/rules/auto_rule.mdc` **CAN be READ by the AI (✅)** but **CANNOT be EDITED by the AI (❌)**.

#### 6. **Agent Switching Triggers**
*   **Trigger Events**: Automatic role switching is **triggered by**:
    1.  `manage_task` with `action="get"` (retrieving task details).
    2.  `manage_task` with `action="next"` (getting the next recommended task).
    3.  **Directly using the `call_agent` tool** (manual or system-invoked).
*   **Immediate Switching**: When `call_agent` is used, the **AI immediately switches its role and context** to the specified agent.
*   **Role Adaptation**: The AI adopts the specialized agent's expertise, knowledge base, and behavioral patterns.

> **⚠️ For Complete MCP System Details**: Refer to [MCP Task Management: Best Practices Guide.mdc](mdc:.cursor/rules/MCP Task Management: Best Practices Guide.mdc) for detailed information on:
> - Task ID formats and management rules
> - Agent assignment and coordination specifics  
> - Context management workflows and dot notation
> - Project structure and deployment architecture
> - Complete MCP tool usage guidelines
> - YAML configuration requirements

These rules provide the foundational operating principles for AI Assistant behavior, with detailed MCP system operations covered in the comprehensive MCP Task Management guide.



---
description: Core Task Management System
globs: 
alwaysApply: true
tags: []

---
The MCP (Multi-Agent Coordination Platform) Task Management System is engineered as a **structured, scalable, and maintainable framework** for orchestrating tasks, projects, and AI agents in multi-agent environments. Its core purpose is to **ensure data integrity and automation**, mandating that **all operations are exclusively performed via dedicated MCP tools**.

## 🏗️ **PROJECT STRUCTURE & DEPLOYMENT MODEL**

**IMPORTANT**: The `.cursor/rules/` directory structure described in this guide exists **ONLY in the dhafnck_mcp development project** (this repository). Other projects using the MCP server will **NOT have these directories**.

### @task_planning_agent need review all task then split task to subtask if no subtask is exist, last subtask is "call manage_context() for complete context data before complete task"

### **Deployment Architecture**
- **dhafnck_mcp**: The **ROOT/SOURCE** project containing the MCP server implementation
  - Contains `.cursor/rules/` with full directory structure
  - Will be built into Docker containers for distribution
- **Client Projects**: Projects using the dockerized MCP server
  - **NO `.cursor/rules/` directories** in client projects
  - Data is stored **remotely** in the Docker container or cloud infrastructure
  - Client projects only need MCP client configuration (e.g., `.cursor/mcp.json`)

### **Data Storage Locations**
- **Development (dhafnck_mcp)**: Local `.cursor/rules/` directories
- **Production/Docker**: Data stored within container or cloud storage
- **Client Projects**: No local data storage - all managed remotely via MCP protocol

### Key Features and Core Components

1.  **Tasks**: These are the **atomic units of work**.
    *   They are hierarchically stored in `/.cursor/rules/tasks/{user_id}/{project_id}/{git_branch_name}/tasks.json` **(in dhafnck_mcp development only)**. A legacy `tasks.json` format is supported but deprecated.
    *   **Required fields** for every task include `id`, `title`, `description`, `project_id`, `status`, `priority`, `created_at`, and `updated_at`.
    *   **Task IDs** follow a **date-based format**: `YYYYMMDDXXX` for main tasks (e.g., `20250617001`) and `YYYYMMDDXXX.XXX` for subtasks (e.g., `20250617001.001`). These IDs are **auto-generated by MCP tools**. **Always quote IDs** when using them in tool calls (e.g., `"20250617001"`).
    *   **Valid Status values** for tasks include: `todo`, `in_progress`, `review`, `done`, `cancelled`, `blocked`, `deferred`.

2.  **Projects**: These serve as **logical containers for related work**, each capable of holding one or more task trees.
    *   Each project can have multiple **task trees** (Execute: `echo "Branch: $(git rev-parse --abbrev-ref HEAD)"), which organize tasks by branches, features, or workflows.

3.  **Agents**: These represent **specialized AI or human roles** that are assigned to projects, task trees, or individual tasks.
    *   Agent data is managed by MCP tools can check by call manage_projet() MCP tool.
    *   Agent registration is **streamlined**, requiring only three essential fields: `id`, `name`, and `call_agent`. **Agent details (capabilities, behaviors) are automatically loaded from YAML configurations** in `yaml-lib/` when an agent is called.
    *   Agents are assigned to task trees via the `agent_assignments` mapping in the project object.
    *   **Agent configurations (YAML files)** must be kept up to date in `/yaml-lib/[agent_name]/`. Each agent needs a `job_desc.yaml` and at least one `rules/context` file.

4.  **Contexts**: This is a **JSON-based system for managing task contexts**.
    *   Contexts are stored hierarchically **(storage location varies by deployment)**
    *   Contexts can be **manually created** using `manage_context("create", ...)` tool - **MUST created and updated when complete task**
    *   A context contains crucial information such as `task_id`, `project_id`, `git_branch_name`, `status`, `assignees`, `title`, `description`, `next_steps`, and `notes` (for insights).
    *   **Agent insights** in notes should use specific categories: `insight`, `challenge`, `solution`, `decision`.

### Workflow for AI Reading

Here's a simplified workflow demonstrating interactions within the MCP Task Management System:

**I. System Initialization & Setup**
→ **Create Project & Task Trees**
    ├── Use `manage_project("create", project_id="...", name="...")`.
    └── Create task trees (branches/features) using `manage_project("create_tree", project_id="...", git_branch_name="...")`.
→ **Register & Assign Agents**
    ├── **Simplified Agent Registration**: Use `manage_agent("register", name="...", call_agent="@...")` with only `id`, `name`, `call_agent` fields required.
    └── **Agent Details Auto-loaded**: When an agent is called, its full capabilities and behaviors are automatically loaded. Agents are assigned to specific task trees via `manage_agent("assign", agent_id="...", project_id="...", git_branch_name="...")`.

**II. Task Lifecycle & Management**
→ **Create Task (in Specific Project/Tree, ai no have permission to use it if no have demande of user, use next instead)**
    ├── Use `manage_task("create", project_id="...", git_branch_name="...", title="...", description="...")`.
    └── **Assign Agent(s)**: In task assignees, **always use the `@` prefix** (e.g., `["@coding_agent"]`). The system automatically normalizes names by adding "@" if missing.
→ **Retrieve Task / Get Next Recommended Task**
    ├── User calls `manage_task("get", task_id="...", project_id="...", git_branch_name="...")` or `manage_task("next", ...)`.
    ├── System loads task data and metadata.
    └── **Manual Context Management**: Use `manage_context("update_property", ...)` to update contexts property.

**III. Agent Role Switching Process**
→ **Manual Trigger**: Agent role switching is triggered by **explicitly using the `call_agent` tool** (e.g., `call_agent(name_agent="coding_agent")`).
    ├── **Specify Agent Name**: Use the agent name directly in `call_agent()`.
    ├── **Normalize Agent Name**: The "@" prefix is stripped to get a clean agent name (e.g., "@coding_agent" → "coding_agent").
    ├── **Execute Agent Call**: The system calls `call_agent(name_agent="...")`.
    └── **AI Role Switch**: The AI assistant then adopts the specialized agent's expertise, knowledge base, behavioral patterns, problem-solving approaches, quality standards, and tool preferences. The AI is now ready to work with appropriate expertise.

**IV. Context-Driven Work & Progress Tracking**
→ **Manual Context Creation**: Use `manage_context("create", task_id="...", project_id="...", git_branch_name="...")` to create task contexts when needed.
→ **Check Context Before Starting Work**: Use `manage_context("get", task_id="...", project_id="...", git_branch_name="...")` to retrieve the current task context.
    ├── **During Implementation**: Log progress with `add_progress` and `add_insight` actions.
    │   └── **Agent Insights Categories**: When adding insights, use specific categories: `insight` (general observations), `challenge` (problems encountered), `solution` (how challenges were resolved), and `decision` (important choices made).
    ├── **When Completing Steps**: Update `next_steps` in the context to maintain session continuity and guide subsequent actions.
    └── **Update Context Properties**: For efficient and specific updates, use **dot notation** (e.g., `metadata.status` to update task status, `progress.next_steps.0` for the first next step).

### Important Rules & Best Practices for AI Agents

*   **DO NOT EDIT DATA JSON FILES DIRECTLY**: This is a **critical rule**. All data (tasks, projects, agents, contexts) must be managed **exclusively through MCP tools** (e.g., `manage_project`, `manage_agent`, `manage_task`, `manage_subtask`, `manage_context`) to ensure data integrity and system automation.
*   **Project Structure Awareness**:
    *   **dhafnck_mcp (ROOT)**: Contains full `.cursor/rules/` structure for development
    *   **Client Projects**: NO `.cursor/rules/` directories - data managed remotely via MCP
    *   **Docker/Cloud**: Data stored in container or cloud infrastructure
*   **Task ID Usage**:
    *   **Use the full date-based format** for all new tasks and subtasks.
    *   **Let the system auto-generate IDs**; do not create them manually.
    *   **Always quote IDs** when using them in tool calls (e.g., `"20250617001"`).
*   **Agent Assignment**:
    *   **Always use the `@` prefix** for agent assignees in tasks (e.g., `["@coding_agent"]`).
    *   **Assign only one primary agent per task** for clarity and predictable behavior. Multi-agent collaboration is handled through task decomposition.
    *   Register and assign agents using MCP tools, not by editing JSON.
*   **Context Management**:
    *   **Manually create contexts** using `manage_context("create", ...)` when context of task actual is not created.
    *   **Always check the task context before starting work** using `manage_context("get", ...)`.
    *   **Regularly log progress** using `add_progress` and `add_insight` actions.
    *   **Update `next_steps`** to maintain session continuity.
    *   When encountering issues, add `challenge` and `solution` insights. Document important `decision`s made.
    *   Use **dot notation** (e.g., `metadata.status`, `progress.next_steps.0`) for efficient and specific updates to context properties.
*   **YAML Configuration**: Keep agent YAML configs in `/yaml-lib/[agent_name]/` up to date. Ensure `job_desc.yaml` and at least one `rules/context` file exist **(in dhafnck_mcp development only)**.
*   **Specify Full Context**: Always include `project_id` and `git_branch_name` in all task and context operations to ensure correct hierarchical access.

### Index for Easy Content Check

*   **System Overview**: Purpose, architecture, key features, deployment model.
*   **Core Components**:
    *   **Tasks**: Definition, storage, required fields, ID format, statuses, auto-generation.
    *   **Projects**: Definition, storage, task trees.
    *   **Agents**: Definition, registration, assignment, YAML config, simplified format.
    *   **Contexts**: Definition, manual creation, storage, schema, insight categories, properties, dot notation.
*   **Key Rules for AI**:
    *   **Never Edit JSON Directly**: Always use MCP tools.
    *   **Project Structure**: dhafnck_mcp vs client projects.
    *   **Task ID Usage**: Auto-generate, date-based format, quoting IDs.
    *   **Agent Assignment**: `@` prefix, single primary agent.
    *   **Context Usage**: Check before work, log progress, update next steps, use dot notation, insight categories.
    *   **YAML Configs**: Keep up to date.
    *   **Specify Context**: Use `project_id` and `git_branch_name`.
*   **MCP Tool Integration**: Examples of `manage_project`, `manage_agent`, `manage_task`, `manage_context`, `call_agent`.
*   **Deployment Architecture**: ROOT project vs client projects, Docker/cloud storage.
*   **Troubleshooting**: Common issues, e.g., agent not switching, task not found, ID format errors, missing config, project structure confusion.



---
description: Agents Information
globs: **/*
alwaysApply: true
tags: [AGENT-MANAGEMENT, uber_orchestrator_agent, nlu_processor_agent, elicitation_agent, compliance_scope_agent, idea_refinement_agent, core-concept-agent, market_research_agent, mcp_researcher_agent, technology_advisor_agent, system_architect_agent, branding_agent, design_system_agent, ui_designer_agent, prototyping_agent, design_qa_analyst, ux_researcher_agent, tech_spec_agent, task_planning_agent, prd_architect_agent, mcp_configuration_agent, algorithmic_problem_solver_agent, coding_agent, code_reviewer_agent, documentation_agent, development_orchestrator_agent, test_case_generator_agent, test_orchestrator_agent, functional_tester_agent, exploratory_tester_agent, performance_load_tester_agent, visual_regression_testing_agent, uat_coordinator_agent, lead_testing_agent, compliance_testing_agent, security_penetration_tester_agent, usability_heuristic_agent, adaptive_deployment_strategist_agent, devops_agent, user_feedback_collector_agent, efficiency_optimization_agent, knowledge_evolution_agent, security_auditor_agent, swarm_scaler_agent, root_cause_analysis_agent, remediation_agent, health_monitor_agent, incident_learning_agent, marketing_strategy_orchestrator, campaign_manager_agent, content_strategy_agent, graphic_design_agent, growth_hacking_idea_agent, video_production_agent, analytics_setup_agent, seo_sem_agent, social_media_setup_agent, community_strategy_agent, project_initiator_agent, task_deep_manager_agent, debugger_agent, task_sync_agent, ethical_review_agent, workflow_architect_agent, scribe_agent, brainjs_ml_agent, deep_research_agent, core_concept_agent, ui_designer_expert_shadcn_agent]
---
## Specialized AI Agents
#AGENT-MANAGEMENT

This file contains specialized AI agents converted from the DafnckMachine agent system.

Each agent has specific expertise and can be invoked using @agent_name syntax.


### Usage

- MUST switch to a role agent if no role is specified; otherwise, the default agent @uber_orchestrator_agent will be used.
- Use @agent-name to invoke a specific agent
- Agents can collaborate with each other as specified in their connectivity
- Each agent has specialized knowledge and capabilities
- All documents created by agents need save on format `.md`, inside folder `.cursor/rules/docs`, after create document, AI need be update document information to `.cursor/rules/docs/index.json`
- Agent relative can update these document if needed

{
    document-(str): {
        name: str
        category: str
        description: str
        usecase: str
        globs: str (path/to/concerned/files/**)
        useby: [str] (list agent AI)
        created_at: ISOdate(format str),
        created_by: ISOdate(format str),
    }
}


## Available Agents

### @uber_orchestrator_agent
#uber_orchestrator_agent
**🎩 Uber Orchestrator Agent (Talk with me)**
#### Collaborates with:
- @development_orchestrator_agent
- @marketing_strategy_orchestrator
- @test_orchestrator_agent
- @swarm_scaler_agent
- @health_monitor_agent
- @devops_agent
- @system_architect_agent
- @security_auditor_agent
- @task_deep_manager_agent

---

### @nlu_processor_agent
#nlu_processor_agent
**🗣️ NLU Processor Agent**
#### Collaborates with:
- @elicitation_agent
- @uber_orchestrator_agent
- @idea_generation_agent

---

### @elicitation_agent
#elicitation_agent
**💬 Requirements Elicitation Agent**
#### Collaborates with:
- @nlu_processor_agent
- @compliance_scope_agent
- @idea_generation_agent

---

### @compliance_scope_agent
#compliance_scope_agent
**📜 Compliance Scope Agent**
#### Collaborates with:
- @elicitation_agent
- @compliance_testing_agent
- @security_auditor_agent

---

### @idea_generation_agent
**💡 Idea Generation Agent**
#### Collaborates with:
- @coding_agent

---

### @idea_refinement_agent
#idea_refinement_agent
**✨ Idea Refinement Agent**
#### Collaborates with:
- @coding_agent

---

### @core_concept_agent
#core_concept_agent
**🎯 Core Concept Agent**
#### Collaborates with:
- @coding_agent

---

### @market_research_agent
#market_research_agent
**📈 Market Research Agent**
#### Collaborates with:
- @idea_generation_agent
- @technology_advisor_agent
- @marketing_strategy_orchestrator

---

### @mcp_researcher_agent
#mcp_researcher_agent
**🔌 MCP Researcher Agent**
#### Collaborates with:
- @technology_advisor_agent
- @mcp_configuration_agent
- @coding_agent

---

### @technology_advisor_agent
#technology_advisor_agent
**🛠️ Technology Advisor Agent**
#### Collaborates with:
- @system_architect_agent
- @security_auditor_agent
- @devops_agent
- @compliance_scope_agent
- @development_orchestrator_agent
- @task_planning_agent

---

### @system_architect_agent
#system_architect_agent
**🏛️ System Architect Agent**
#### Collaborates with:
- @prd_architect_agent
- @tech_spec_agent
- @coding_agent

---

### @branding_agent
#branding_agent
**🎭 Branding Agent**
#### Collaborates with:
- @coding_agent

---

### @design_system_agent
#design_system_agent
**🎨 Design System Agent**
#### Collaborates with:
- @ui_designer_agent
- @branding_agent
- @prototyping_agent

---

### @ui_designer_agent
#ui_designer_agent
**🖼️ UI Designer Agent**
#### Collaborates with:
- @design_system_agent
- @ux_researcher_agent
- @prototyping_agent

---
### @ui_designer_expert_shadcn_agent
#ui_designer_expert_shadcn_agent
**🎨 UI Designer Expert ShadCN Agent**
#### Collaborates with:
- @ui_designer_agent
- @design_system_agent
- @prototyping_agent
- @coding_agent
- @branding_agent
#### Use tool : 
    "shadcn-ui-server": {
        "command": "npx",
        "args": ["@heilgar/shadcn-ui-mcp-server"]
    }   


---

### @prototyping_agent
#prototyping_agent
**🕹️ Prototyping Agent**
#### Collaborates with:
- @coding_agent

---

### @design_qa_analyst
#design_qa_analyst
**🔍 Design QA Analyst**
#### Collaborates with:
- @ui_designer_agent
- @ux_researcher_agent
- @compliance_testing_agent

---

### @ux_researcher_agent
#ux_researcher_agent
**🧐 UX Researcher Agent**
#### Collaborates with:
- @ui_designer_agent
- @design_system_agent
- @usability_heuristic_agent

---

### @tech_spec_agent
#tech_spec_agent
**⚙️ Technical Specification Agent**
#### Collaborates with:
- @coding_agent

---

### @task_planning_agent
#task_planning_agent
**📅 Task Planning Agent**
#### Collaborates with:
- @uber_orchestrator_agent
- @prd_architect_agent
- @development_orchestrator_agent

---

### @prd_architect_agent
#prd_architect_agent
**📝 PRD Architect Agent**
#### Collaborates with:
- @task_planning_agent
- @system_architect_agent
- @tech_spec_agent

---

### @mcp_configuration_agent
#mcp_configuration_agent
**🔧 MCP Configuration Agent**
#### Collaborates with:
- @coding_agent

---

### @algorithmic_problem_solver_agent
#algorithmic_problem_solver_agent
**🧠 Algorithmic Problem Solver Agent**
#### Collaborates with:
- @coding_agent

---

### @coding_agent

#coding_agent
**💻 Coding Agent (Feature Implementation)**
#### Collaborates with:
- @development_orchestrator_agent
- @code_reviewer_agent
- @tech_spec_agent

---

### @code_reviewer_agent
#code_reviewer_agent
**🧐 Code Reviewer Agent**
#### Collaborates with:
- @coding_agent
- @test_orchestrator_agent

---

### @documentation_agent
#documentation_agent
**📄 Documentation Agent**
#### Collaborates with:
- @coding_agent
- @tech_spec_agent
- @knowledge_evolution_agent

---

### @development_orchestrator_agent
#development_orchestrator_agent
**🛠️ Development Orchestrator Agent**
#### Collaborates with:
- @coding_agent
- @code_reviewer_agent
- @test_orchestrator_agent

---

### @test_case_generator_agent
#test_case_generator_agent
**📝 Test Case Generator Agent**
#### Collaborates with:
- @test_orchestrator_agent
- @functional_tester_agent
- @coding_agent

---

### @test_orchestrator_agent
#test_orchestrator_agent
**🚦 Test Orchestrator Agent**
#### Collaborates with:
- @development_orchestrator_agent
- @functional_tester_agent
- @test_case_generator_agent

---

### @functional_tester_agent
#functional_tester_agent
**⚙️ Functional Tester Agent**
#### Collaborates with:
- @test_orchestrator_agent
- @coding_agent

---

### @exploratory_tester_agent
#exploratory_tester_agent
**🧭 Exploratory Tester Agent**
#### Collaborates with:
- @coding_agent

---

### @performance_load_tester_agent
#performance_load_tester_agent
**⏱️ Performance & Load Tester Agent**
#### Collaborates with:
- @coding_agent

---

### @visual_regression_testing_agent
#visual_regression_testing_agent
**🖼️ Visual Regression Testing Agent**
#### Collaborates with:
- @coding_agent

---

### @uat_coordinator_agent
#uat_coordinator_agent
**🤝 UAT Coordinator Agent**
#### Collaborates with:
- @coding_agent

---

### @lead_testing_agent
#lead_testing_agent
**🧪 Lead Testing Agent**
#### Collaborates with:
- @coding_agent

---

### @compliance_testing_agent
#compliance_testing_agent
**🛡️ Compliance Testing Agent**
#### Collaborates with:
- @security_auditor_agent
- @test_orchestrator_agent
- @compliance_scope_agent

---

### @security_penetration_tester_agent
#security_penetration_tester_agent
**🔐 Security & Penetration Tester Agent**
#### Collaborates with:
- @security_auditor_agent
- @coding_agent

---

### @usability_heuristic_agent
#usability_heuristic_agent
**🧐 Usability & Heuristic Evaluation Agent**
#### Collaborates with:
- @user_feedback_collector_agent
- @ux_researcher_agent
- @design_qa_analyst

---

### @adaptive_deployment_strategist_agent
#adaptive_deployment_strategist_agent
**🚀 Adaptive Deployment Strategist Agent**
#### Collaborates with:
- @devops_agent
- @health_monitor_agent
- @efficiency_optimization_agent

---

### @devops_agent
#devops_agent
**⚙️ DevOps Agent**
#### Collaborates with:
- @adaptive_deployment_strategist_agent
- @development_orchestrator_agent
- @security_auditor_agent

---

### @user_feedback_collector_agent
#user_feedback_collector_agent
**🗣️ User Feedback Collector Agent**
#### Collaborates with:
- @ux_researcher_agent
- @usability_heuristic_agent
- @analytics_setup_agent

---

### @efficiency_optimization_agent
#efficiency_optimization_agent
**⏱️ Efficiency Optimization Agent**
#### Collaborates with:
- @analytics_setup_agent
- @health_monitor_agent
- @knowledge_evolution_agent

---

### @knowledge_evolution_agent
#knowledge_evolution_agent
**🧠 Knowledge Evolution Agent**
#### Collaborates with:
- @documentation_agent
- @incident_learning_agent
- @efficiency_optimization_agent

---

### @security_auditor_agent
#security_auditor_agent
**🛡️ Security Auditor Agent**
#### Collaborates with:
- @security_penetration_tester_agent
- @compliance_testing_agent
- @system_architect_agent

---

### @swarm_scaler_agent
#swarm_scaler_agent
**🦾 Swarm Scaler Agent**
#### Collaborates with:
- @coding_agent

---

### @root_cause_analysis_agent
#root_cause_analysis_agent
**🕵️ Root Cause Analysis Agent**
#### Collaborates with:
- @coding_agent

---

### @remediation_agent
#remediation_agent
**🛠️ Remediation Agent**
#### Collaborates with:
- @coding_agent

---

### @health_monitor_agent
#health_monitor_agent
**🩺 Health Monitor Agent**
#### Collaborates with:
- @remediation_agent
- @root_cause_analysis_agent
- @incident_learning_agent
- @swarm_scaler_agent
- @devops_agent
- @performance_load_tester_agent
- @security_auditor_agent

---

### @incident_learning_agent
#incident_learning_agent
**📚 Incident Learning Agent**
#### Collaborates with:
- @coding_agent

---

### @marketing_strategy_orchestrator
#marketing_strategy_orchestrator
**📈 Marketing Strategy Orchestrator**
#### Collaborates with:
- @campaign_manager_agent
- @content_strategy_agent
- @growth_hacking_idea_agent

---

### @campaign_manager_agent
#campaign_manager_agent
**📣 Campaign Manager Agent**
#### Collaborates with:
- @marketing_strategy_orchestrator
- @content_strategy_agent
- @social_media_setup_agent

---

### @content_strategy_agent
#content_strategy_agent
**📝 Content Strategy Agent**
#### Collaborates with:
- @campaign_manager_agent
- @graphic_design_agent
- @seo_sem_agent

---

### @graphic_design_agent
#graphic_design_agent
**🎨 Graphic Design Agent**
#### Collaborates with:
- @coding_agent

---

### @growth_hacking_idea_agent
#growth_hacking_idea_agent
**💡 Growth Hacking Idea Agent**
#### Collaborates with:
- @marketing_strategy_orchestrator
- @coding_agent
- @analytics_setup_agent

---

### @video_production_agent
#video_production_agent
**🎬 Video Production Agent**
#### Collaborates with:
- @coding_agent

---

### @analytics_setup_agent
#analytics_setup_agent
**📊 Analytics Setup Agent**
#### Collaborates with:
- @user_feedback_collector_agent
- @seo_sem_agent
- @efficiency_optimization_agent

---

### @seo_sem_agent
#seo_sem_agent
**🔍 SEO/SEM Agent**
#### Collaborates with:
- @coding_agent

---

### @social_media_setup_agent
#social_media_setup_agent
**📱 Social Media Setup Agent**
#### Collaborates with:
- @coding_agent

---

### @community_strategy_agent
#community_strategy_agent
**🤝 Community Strategy Agent**
#### Collaborates with:
- @coding_agent

---

### @project_initiator_agent
#project_initiator_agent
**🚀 Project Initiator Agent**
#### Collaborates with:
- @coding_agent

---

### @task_deep_manager_agent
#task_deep_manager_agent
**🧠 Task Deep Manager Agent (Full Automation)**
#### Collaborates with:
- @task_planning_agent
- @uber_orchestrator_agent
- @development_orchestrator_agent

---

### @debugger_agent
#debugger_agent
**🐞 Debugger Agent**
#### Collaborates with:
- @coding_agent

---

### @task_sync_agent
#task_sync_agent
**🔄 Task Sync Agent**
#### Collaborates with:
- @task_planning_agent
- @uber_orchestrator_agent
- @task_deep_manager_agent

---

### @ethical_review_agent
#ethical_review_agent
**⚖️ Ethical Review Agent**
#### Collaborates with:
- @coding_agent

---

### @workflow_architect_agent
#workflow_architect_agent
**🗺️ Workflow Architect Agent**
#### Collaborates with:
- @coding_agent

---

### @scribe_agent
#scribe_agent
**✍️ Scribe Agent**
#### Collaborates with:
- @coding_agent

---

### @brainjs_ml_agent
#brainjs_ml_agent
**🧠 Brain.js ML Agent**
#### Collaborates with:
- @coding_agent

---

### @deep_research_agent
#deep_research_agent
**🔍 Deep Research Agent**
#### Collaborates with:
- @coding_agent

---