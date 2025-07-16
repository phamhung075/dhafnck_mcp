#!/usr/bin/env python3
"""
Script to update task_mcp_controller.py to use StandardResponseFormatter consistently.
This script helps identify and fix response inconsistencies.
"""

import re
from pathlib import Path

def find_simple_responses(file_path):
    """Find all simple response patterns that need updating."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find simple error responses
    pattern = r'return\s*\{\s*["\']success["\']\s*:\s*False[^}]*\}'
    
    matches = []
    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        start = match.start()
        end = match.end()
        
        # Get line numbers
        lines_before = content[:start].count('\n')
        line_start = lines_before + 1
        
        # Get context
        context_start = max(0, content.rfind('\n', 0, start - 100))
        context_end = content.find('\n', end + 100)
        if context_end == -1:
            context_end = len(content)
        
        context = content[context_start:context_end]
        
        matches.append({
            'line': line_start,
            'match': match.group(),
            'context': context,
            'start': start,
            'end': end
        })
    
    return matches

def analyze_response(response_str):
    """Analyze a response string to extract key components."""
    components = {}
    
    # Extract error message
    error_match = re.search(r'["\']error["\']\s*:\s*["\']([^"\']+)["\']', response_str)
    if error_match:
        components['error'] = error_match.group(1)
    
    # Extract error code
    code_match = re.search(r'["\']error_code["\']\s*:\s*["\']([^"\']+)["\']', response_str)
    if code_match:
        components['error_code'] = code_match.group(1)
    
    # Extract field
    field_match = re.search(r'["\']field["\']\s*:\s*["\']([^"\']+)["\']', response_str)
    if field_match:
        components['field'] = field_match.group(1)
    
    # Extract hint
    hint_match = re.search(r'["\']hint["\']\s*:\s*["\']([^"\']+)["\']', response_str)
    if hint_match:
        components['hint'] = hint_match.group(1)
    
    # Extract expected
    expected_match = re.search(r'["\']expected["\']\s*:\s*["\']([^"\']+)["\']', response_str)
    if expected_match:
        components['expected'] = expected_match.group(1)
    
    return components

def generate_fix(components, operation_name):
    """Generate StandardResponseFormatter call based on components."""
    if 'field' in components and ('expected' in components or 'error_code' == 'MISSING_FIELD'):
        # Validation error
        return f"""StandardResponseFormatter.create_validation_error_response(
                            operation="{operation_name}",
                            field="{components.get('field', 'unknown')}",
                            expected="{components.get('expected', 'valid value')}",
                            hint="{components.get('hint', '')}"
                        )"""
    else:
        # General error
        error_code = components.get('error_code', 'OPERATION_FAILED')
        if error_code == 'OPERATION_FAILED':
            error_code = 'ErrorCodes.OPERATION_FAILED'
        else:
            error_code = f'ErrorCodes.{error_code}'
        
        return f"""StandardResponseFormatter.create_error_response(
                            operation="{operation_name}",
                            error="{components.get('error', 'Operation failed')}",
                            error_code={error_code}
                        )"""

def main():
    file_path = Path("/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/task_mcp_controller.py")
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    print(f"Analyzing {file_path}...")
    matches = find_simple_responses(file_path)
    
    print(f"\nFound {len(matches)} simple response patterns to fix:\n")
    
    for i, match in enumerate(matches):
        print(f"{i+1}. Line {match['line']}:")
        print("   Current:")
        print("   " + match['match'].replace('\n', '\n   '))
        
        components = analyze_response(match['match'])
        print("\n   Components found:")
        for key, value in components.items():
            print(f"     - {key}: {value}")
        
        # Try to determine operation from context
        operation = "unknown_operation"
        if 'create' in match['context'].lower():
            operation = "create_task"
        elif 'update' in match['context'].lower():
            operation = "update_task"
        elif 'delete' in match['context'].lower():
            operation = "delete_task"
        elif 'complete' in match['context'].lower():
            operation = "complete_task"
        elif 'search' in match['context'].lower():
            operation = "search_tasks"
        elif 'list' in match['context'].lower():
            operation = "list_tasks"
        
        fix = generate_fix(components, operation)
        print(f"\n   Suggested fix:")
        print("   return " + fix)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()