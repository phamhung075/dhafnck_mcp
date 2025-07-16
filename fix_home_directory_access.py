#!/usr/bin/env python3
"""
Fix for Home Directory Permission Errors

Problem: Hardcoded paths to /home/daihungpham/agentic-project cause permission errors
Solution: Use environment variables and proper data paths
"""

import os
import re

# Files that need fixing based on grep results
FILES_TO_FIX = [
    "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/services/agent_doc_generator.py",
    "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/database/database_initializer.py",
    "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/utilities/directory_utils.py",
    "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/repositories/task_repository_factory.py",
    "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/repositories/subtask_repository_factory.py",
    "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/repositories/sqlite/git_branch_repository.py",
    "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/repositories/sqlite/template_repository.py",
    "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/repositories/template_repository_factory.py",
    "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/repositories/hierarchical_context_repository_factory.py",
    "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/application/use_cases/call_agent.py",
    "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/cursor_rules_tools_ddd.py"
]

def backup_file(filepath):
    """Create a backup of the file"""
    backup_path = filepath + ".backup"
    if not os.path.exists(backup_path):
        with open(filepath, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"✓ Backed up: {os.path.basename(filepath)}")

def fix_hardcoded_paths(filepath):
    """Replace hardcoded paths with environment-aware code"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to match the hardcoded path
    patterns = [
        (r'return Path\("/home/daihungpham/agentic-project"\)', 
         '''# Use environment variable or default data path
    data_path = os.environ.get('DHAFNCK_DATA_PATH', '/data')
    # If running in development, try to find project root
    if not os.path.exists(data_path):
        # Try current working directory
        cwd = Path.cwd()
        if (cwd / "dhafnck_mcp_main").exists():
            return cwd
        # Try parent directories
        current = Path(__file__).resolve()
        while current.parent != current:
            if (current / "dhafnck_mcp_main").exists():
                return current
            current = current.parent
        # Fall back to temp directory for safety
        return Path("/tmp/dhafnck_project")
    return Path(data_path)'''),
        
        (r'return "/home/daihungpham/agentic-project"',
         '''# Use environment variable or default data path
    data_path = os.environ.get('DHAFNCK_DATA_PATH', '/data')
    # If running in development, try to find project root
    if not os.path.exists(data_path):
        # Try current working directory
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "dhafnck_mcp_main")):
            return cwd
        # Fall back to temp directory for safety
        return "/tmp/dhafnck_project"
    return data_path''')
    ]
    
    modified = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True
    
    # Also add os import if needed and not present
    if modified and 'import os' not in content:
        # Add import after other imports
        lines = content.split('\n')
        import_added = False
        for i, line in enumerate(lines):
            if line.startswith('from pathlib import Path') or line.startswith('import'):
                # Add os import after this line
                lines.insert(i + 1, 'import os')
                import_added = True
                break
        if not import_added:
            # Add at the beginning after docstring
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith('"""') and not line.startswith('#'):
                    lines.insert(i, 'import os\n')
                    break
        content = '\n'.join(lines)
    
    if modified:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✓ Fixed: {os.path.basename(filepath)}")
        return True
    else:
        print(f"⚠️  No changes needed: {os.path.basename(filepath)}")
        return False

def add_environment_config():
    """Add environment variable to docker-compose.yml"""
    docker_compose_path = "/home/daihungpham/agentic-project/dhafnck_mcp_main/docker/docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        content = f.read()
    
    # Check if the environment variable is already there
    if 'DHAFNCK_DATA_PATH' not in content:
        # Add it to the environment section
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'environment:' in line and 'dhafnck-mcp:' in content[:content.index(line)]:
                # Find the right indentation
                indent = len(line) - len(line.lstrip())
                # Insert after the environment: line
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith('-') or lines[j].strip().startswith('PYTHONPATH'):
                    j += 1
                lines.insert(j, ' ' * (indent + 2) + 'DHAFNCK_DATA_PATH: /data')
                break
        
        content = '\n'.join(lines)
        with open(docker_compose_path, 'w') as f:
            f.write(content)
        print("✓ Added DHAFNCK_DATA_PATH to docker-compose.yml")

def main():
    print("Home Directory Permission Fix")
    print("=" * 50)
    
    # Backup all files first
    print("\nBacking up files...")
    for filepath in FILES_TO_FIX:
        if os.path.exists(filepath):
            backup_file(filepath)
    
    # Fix the files
    print("\nFixing hardcoded paths...")
    fixed_count = 0
    for filepath in FILES_TO_FIX:
        if os.path.exists(filepath):
            if fix_hardcoded_paths(filepath):
                fixed_count += 1
        else:
            print(f"✗ File not found: {os.path.basename(filepath)}")
    
    # Update docker-compose.yml
    print("\nUpdating Docker configuration...")
    add_environment_config()
    
    print(f"\n✅ Fixed {fixed_count} files!")
    print("\nNext steps:")
    print("1. Restart the Docker container:")
    print("   cd /home/daihungpham/agentic-project/dhafnck_mcp_main/docker")
    print("   docker-compose restart dhafnck-mcp")
    print("2. Test the next task feature to verify the fix")

if __name__ == "__main__":
    main()