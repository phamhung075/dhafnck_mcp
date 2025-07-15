---
description: Core Task Management System
alwaysApply: true
globs:
Loading core: saved, no reload needed
---

## 🌍 GLOBAL RULE
#GLOBAL-RULE

  

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

- `list_dir`: List directory structure

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

- **Error Handling**: Fix everything automatically, continue without asking when CONTINUE_AUTOMATIC is ON, ai must asking himseft what cause of this error, using  `sequential-thinking`

  

#### Memory & Context Management
#MEMORY #CONTEXT #TOOL-COUNTING

  

- **Tool Counting**: Increment tool count with each usage, reset when >20

- **Context Reset**: Call manage_context() when tool count exceeds threshold

- **Token Monitoring**: Monitor for requests exceeding Pro plan limits, terminate if exceeded

  

---

  

### ⚙️ RUNTIME CONFIGURATION
#RUNTIME-CONFIGURATION

  

#### Runtime Constants (Fixed Values) :  See Runtime Constants (Fixed Values) on <PROJECT_ROOT>/.cursor/settings.md

  

#### Runtime Variables (Dynamic Values): Runtime Variables (Dynamic Values) on <PROJECT_ROOT>/.cursor/settings.md

  

---

  

### 🛠️ TOOL CONFIGURATIONS
#TOOL-CONFIGURATIONS

  

#### Custom Tools (Specialized MCP Tools)
| Tool                   | 🛠️ Purpose                               | ⏰ Display Before                         | ✅ Display After             | ⚙️ Action                                                                                                                                                  |
| ---------------------- | ----------------------------------------- | ---------------------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🤖 `call_agent`        | Call specialized agent for specific tasks | "🔄 Loading Agents Information..."       | "🔁 Switch to agent"        | **AI Role Switch**: The assistant adopts the agent's expertise, knowledge base, behavioral patterns, and tools. Ready to operate as the designated expert. |
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

[Additional core content continues with MCP system architecture, task management rules, and agent information...] 