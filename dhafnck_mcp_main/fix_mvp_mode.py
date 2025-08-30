#!/usr/bin/env python3
"""Fix MVP mode issues in tests by ensuring correct environment variable settings."""

import os
import sys

# Force the environment variable to be false
os.environ['DHAFNCK_MVP_MODE'] = 'false'

# Add the path to allow imports
sys.path.insert(0, 'src')

# Now import and check
from fastmcp.task_management.domain.constants import MVP_MODE_ENABLED

print(f"MVP_MODE_ENABLED in constants: {MVP_MODE_ENABLED}")
print(f"Environment variable: {os.environ.get('DHAFNCK_MVP_MODE', 'not set')}")

# The issue is that the constant is evaluated at import time
# So we need to ensure the env var is set BEFORE any imports happen

if MVP_MODE_ENABLED:
    print("\n⚠️  WARNING: MVP_MODE_ENABLED is still True!")
    print("This means the constant was evaluated before we could set the environment variable.")
    print("The issue is likely that something is importing the module during Python startup.")
    print("\nSolution: Ensure DHAFNCK_MVP_MODE=false is set in the .env file")
    print("and that no imports happen before dotenv loads.")
else:
    print("\n✅ SUCCESS: MVP_MODE_ENABLED is False")
    print("The environment variable is correctly set.")