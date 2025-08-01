#!/usr/bin/env python3
"""
Project MCP Setup Script
========================

This script sets up the DhafnckMCP task management system for any project location.
It creates the necessary directory structure and MCP configuration files.

Usage:
    python setup_project_mcp.py [project_path]
    
If no project_path is provided, it uses the current directory.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Optional

def setup_project_structure(project_path: Path) -> bool:
    """
    Set up the required directory structure for a project.
    
    Args:
        project_path: Path to the project root
        
    Returns:
        bool: True if setup was successful
    """
    print(f"Setting up project structure in: {project_path}")
    
    try:
        # Create .cursor/rules directory structure
        cursor_rules_dir = project_path / ".cursor" / "rules"
        directories = [
            cursor_rules_dir,
            cursor_rules_dir / "tasks",
            cursor_rules_dir / "brain",
            cursor_rules_dir / "agents",
            cursor_rules_dir / "02_AI-DOCS",
            cursor_rules_dir / "02_AI-DOCS" / "TaskManagement",
            cursor_rules_dir / "02_AI-DOCS" / "MultiAgentOrchestration"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        
        # File structure to create
        files_to_create = {
            cursor_rules_dir / "tasks" / "tasks.json": {
                "tasks": {},
                "metadata": {
                    "version": "1.0.0",
                    "created": "2025-01-01T00:00:00Z",
                    "project_root": str(project_path)
                }
            },
            # Only create empty projects.json if it doesn't exist or is truly empty
            # This prevents overwriting production data during tests
            cursor_rules_dir / "brain" / "projects.json": None,  # Handle specially below
            cursor_rules_dir / "auto_rule.mdc": "# Auto-generated rules\n\nThis file is automatically generated by the task management system.\n",
            cursor_rules_dir / "main_objectif.mdc": f"""# Project Task Management

This project uses the DhafnckMCP task management system.

## Project Information
- **Location**: {project_path}
- **Task Management**: Enabled
- **Multi-Agent Support**: Enabled

## Quick Start
1. Use MCP tools to manage tasks and projects
2. Tasks are stored in `.cursor/rules/tasks/tasks.json`
3. Project data is stored in `.cursor/rules/brain/projects.json`
4. Auto-generated rules are in `.cursor/rules/auto_rule.mdc`

## MCP Tools Available
- `manage_task` - Create, update, and manage tasks
- `manage_project` - Project lifecycle management
- `manage_agent` - Multi-agent coordination
- `manage_subtask` - Subtask management
- `call_agent` - Agent role switching
"""
        }
        
        # Handle projects.json specially to avoid overwriting production data
        projects_json_path = cursor_rules_dir / "brain" / "projects.json"
        if not projects_json_path.exists():
            # File doesn't exist, create empty one
            projects_json_path.write_text(json.dumps({}, indent=2))
            print(f"✅ Created file: {projects_json_path}")
        else:
            # File exists, check if it's empty or has only whitespace
            try:
                existing_content = projects_json_path.read_text().strip()
                if not existing_content or existing_content == "{}":
                    # Empty or just empty object, safe to initialize
                    projects_json_path.write_text(json.dumps({}, indent=2))
                    print(f"✅ Initialized empty file: {projects_json_path}")
                else:
                    # File has content, don't overwrite
                    print(f"📄 File already exists with content: {projects_json_path}")
            except Exception as e:
                print(f"⚠️ Could not read existing projects.json: {e}")
                print(f"📄 Keeping existing file: {projects_json_path}")
        
        # Create other files
        for file_path, content in files_to_create.items():
            if content is None:  # Skip projects.json as handled above
                continue
                
            if not file_path.exists():
                if isinstance(content, dict):
                    file_path.write_text(json.dumps(content, indent=2))
                else:
                    file_path.write_text(content)
                print(f"✅ Created file: {file_path}")
            else:
                print(f"📄 File already exists: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up project structure: {e}")
        return False

def create_mcp_config(project_path: Path, dhafnck_mcp_path: Optional[Path] = None) -> bool:
    """
    Create MCP configuration file for the project.
    
    Args:
        project_path: Path to the project root
        dhafnck_mcp_path: Path to dhafnck_mcp_main directory (optional)
        
    Returns:
        bool: True if config was created successfully
    """
    print(f"Creating MCP configuration for project: {project_path}")
    
    try:
        # Auto-detect dhafnck_mcp_main if not provided
        if dhafnck_mcp_path is None:
            # Look for dhafnck_mcp_main in the project or parent directories
            search_paths = [
                project_path / "dhafnck_mcp_main",
                project_path.parent / "dhafnck_mcp_main",
                Path.cwd() / "dhafnck_mcp_main"
            ]
            
            for path in search_paths:
                if path.exists() and (path / "src" / "fastmcp").exists():
                    dhafnck_mcp_path = path
                    break
            
            if dhafnck_mcp_path is None:
                print("❌ Could not find dhafnck_mcp_main directory")
                print("   Please ensure dhafnck_mcp_main is in the project or parent directory")
                return False
        
        print(f"Using dhafnck_mcp_main at: {dhafnck_mcp_path}")
        
        # Check if virtual environment exists
        venv_python = dhafnck_mcp_path / ".venv" / "bin" / "python"
        if not venv_python.exists():
            print(f"❌ Virtual environment not found at: {venv_python}")
            print("   Please run: cd dhafnck_mcp_main && python -m venv .venv && source .venv/bin/activate && pip install -e .")
            return False
        
        # Create MCP configuration
        mcp_config = {
            "mcpServers": {
                "dhafnck_mcp": {
                    "command": "wsl.exe",
                    "args": [
                        "--cd", str(project_path),
                        "--exec", str(venv_python),
                        "-m", "fastmcp.server.mcp_entry_point"
                    ],
                    "env": {
                        "PYTHONPATH": str(dhafnck_mcp_path / "src"),
                        "PROJECT_ROOT_PATH": ".",
                        "TASKS_JSON_PATH": ".cursor/rules/tasks/tasks.json",
                        "TASK_JSON_BACKUP_PATH": ".cursor/rules/tasks/backup",
                        "MCP_TOOL_CONFIG": ".cursor/tool_config.json",
                        "AGENTS_OUTPUT_DIR": ".cursor/rules/agents",
                        "AUTO_RULE_PATH": ".cursor/rules/auto_rule.mdc",
                        "BRAIN_DIR_PATH": ".cursor/rules/brain",
                        "PROJECTS_FILE_PATH": ".cursor/rules/brain/projects.json",
                                    "AGENT_LIBRARY_DIR_PATH": str(dhafnck_mcp_path / "agent-library")
                    },
                    "transport": "stdio",
                    "debug": True
                },
                "sequential-thinking": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
                    "env": {}
                }
            }
        }
        
        # Write MCP configuration
        mcp_config_path = project_path / ".cursor" / "mcp.json"
        mcp_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(mcp_config_path, 'w') as f:
            json.dump(mcp_config, f, indent=2)
        
        print(f"✅ Created MCP configuration: {mcp_config_path}")
        
        # Create backup of original config if it exists
        if mcp_config_path.exists():
            backup_path = mcp_config_path.with_suffix('.json.backup')
            if backup_path.exists():
                print(f"📄 Backup already exists: {backup_path}")
            else:
                print(f"💾 Created backup: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating MCP configuration: {e}")
        return False

def create_tool_config(project_path: Path) -> bool:
    """
    Create tool configuration file for the project.
    
    Args:
        project_path: Path to the project root
        
    Returns:
        bool: True if config was created successfully
    """
    try:
        tool_config = {
            "enabled_tools": {
                "manage_project": True,
                "manage_task": True,
                "manage_subtask": True,
                "manage_agent": True,
                "call_agent": True,
                "update_auto_rule": True,
                "validate_rules": True,
                "manage_rule": True,
                "regenerate_auto_rule": True,
                "validate_tasks_json": True
            },
            "debug_mode": False,
            "tool_logging": True,
            "project_root": str(project_path)
        }
        
        tool_config_path = project_path / ".cursor" / "tool_config.json"
        with open(tool_config_path, 'w') as f:
            json.dump(tool_config, f, indent=2)
        
        print(f"✅ Created tool configuration: {tool_config_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tool configuration: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 DhafnckMCP Project Setup")
    print("=" * 50)
    
    # Get project path from command line or use current directory
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1]).resolve()
    else:
        project_path = Path.cwd()
    
    print(f"Project path: {project_path}")
    
    if not project_path.exists():
        print(f"❌ Project path does not exist: {project_path}")
        sys.exit(1)
    
    # Setup project structure
    if not setup_project_structure(project_path):
        print("❌ Failed to set up project structure")
        sys.exit(1)
    
    # Create MCP configuration
    if not create_mcp_config(project_path):
        print("❌ Failed to create MCP configuration")
        sys.exit(1)
    
    # Create tool configuration
    if not create_tool_config(project_path):
        print("❌ Failed to create tool configuration")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Project setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Restart Cursor completely for MCP changes to take effect")
    print("2. Open the project in Cursor")
    print("3. Use MCP tools to manage tasks and projects")
    print("4. Check .cursor/mcp.json for configuration details")
    print("\n🔧 Available MCP tools:")
    print("- manage_task - Create and manage tasks")
    print("- manage_project - Project lifecycle management")
    print("- manage_agent - Multi-agent coordination")
    print("- call_agent - Switch AI agent roles")
    print("\n📁 Project structure created:")
    print(f"- {project_path}/.cursor/rules/tasks/tasks.json")
    print(f"- {project_path}/.cursor/rules/brain/projects.json")
    print(f"- {project_path}/.cursor/rules/auto_rule.mdc")
    print(f"- {project_path}/.cursor/mcp.json")

if __name__ == "__main__":
    main() 