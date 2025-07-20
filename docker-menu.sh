#!/bin/bash
# Wrapper script for docker-menu

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to docker-system directory and execute menu
cd "${SCRIPT_DIR}/docker-system" && exec ./docker-menu.py "$@"