#!/usr/bin/env python3
"""Simple test of MCP bridge functionality"""
import json
import sys

# Test request
request = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "clientInfo": {
            "name": "simple-test",
            "version": "1.0.0"
        }
    },
    "id": 1
}

# Send to stdout
print(json.dumps(request))
sys.stdout.flush()