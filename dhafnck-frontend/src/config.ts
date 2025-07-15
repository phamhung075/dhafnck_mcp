/**
 * Application configuration
 */

export const config = {
  // MCP Server Configuration
  mcp: {
    baseUrl: process.env.REACT_APP_MCP_URL || 'http://localhost:8000/mcp',
    timeout: 30000, // Default timeout in milliseconds
    retries: 3, // Default number of retries
  },
  
  // Polling intervals (in milliseconds)
  polling: {
    healthCheck: 300000, // 5 minutes
    statusUpdate: 120000, // 2 minutes
    compliance: 300000, // 5 minutes
  },
  
  // Cache configuration
  cache: {
    timeout: 60000, // 1 minute
  },
  
  // UI Configuration
  ui: {
    notificationDuration: 5000, // 5 seconds
    loadingTimeout: 10000, // 10 seconds for initial load
  }
};