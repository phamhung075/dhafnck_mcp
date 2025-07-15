#!/usr/bin/env node

/**
 * Simple script to test MCP server connection
 */

const fetch = require('node-fetch');

const MCP_URL = process.env.REACT_APP_MCP_URL || 'http://localhost:8000/mcp';

async function testConnection() {
  console.log(`Testing MCP server connection at: ${MCP_URL}`);
  console.log('-------------------------------------------');
  
  const testRequest = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_connection",
      arguments: {
        action: "health_check",
        include_details: true
      }
    },
    id: 1
  };
  
  try {
    console.log('Sending health check request...');
    const response = await fetch(MCP_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'MCP-Protocol-Version': '2025-06-18'
      },
      body: JSON.stringify(testRequest),
      timeout: 5000
    });
    
    console.log(`Response status: ${response.status} ${response.statusText}`);
    
    if (!response.ok) {
      console.error(`HTTP Error: ${response.status} ${response.statusText}`);
      const text = await response.text();
      console.error('Response body:', text);
      return;
    }
    
    const data = await response.json();
    console.log('Response received:');
    console.log(JSON.stringify(data, null, 2));
    
    if (data.error) {
      console.error('MCP Error:', data.error);
    } else if (data.result) {
      console.log('\n✅ MCP Server is accessible and responding!');
      if (data.result.content && data.result.content[0]) {
        try {
          const healthData = JSON.parse(data.result.content[0].text);
          console.log('\nHealth Status:', healthData);
        } catch (e) {
          console.log('Raw result:', data.result.content[0].text);
        }
      }
    }
  } catch (error) {
    console.error('\n❌ Failed to connect to MCP server:');
    console.error(error.message);
    console.error('\nPossible causes:');
    console.error('1. MCP server is not running');
    console.error('2. Server is running on a different port');
    console.error('3. Network/firewall issues');
    console.error('\nPlease check that the MCP server is running and accessible.');
  }
}

// Run the test
testConnection();