/**
 * @deprecated Use ./api/index instead
 * 
 * This file is kept for import compatibility.
 * All new development should use the enhanced API from ./api/
 */

// Re-export everything from the enhanced API directly
export * from './api/enhanced';
export { mcpApi as default } from './api/enhanced';
