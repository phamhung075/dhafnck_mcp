#!/bin/bash

# Function to properly escape strings for JSON
json_escape() {
    local string="$1"
    # Escape backslashes first
    string="${string//\\/\\\\}"
    # Escape quotes
    string="${string//\"/\\\"}"
    # Escape newlines
    string="${string//$'\n'/\\n}"
    # Escape carriage returns
    string="${string//$'\r'/\\r}"
    # Escape tabs
    string="${string//$'\t'/\\t}"
    # Remove any control characters
    string=$(echo "$string" | tr -d '\000-\037')
    echo "$string"
}

# Test the function
test_string='This is a "test" string
with newlines and	tabs
and special chars like @uber_orchestrator_agent'

echo "Original: $test_string"
echo "Escaped: $(json_escape "$test_string")"