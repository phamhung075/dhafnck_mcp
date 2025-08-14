import React from "react";
import SimpleTaskManager from "./components/SimpleTaskManager";

function SimpleApp() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">MCP Task Manager</h1>
          <p className="text-gray-600">Manage your tasks with create, read, update, and delete operations</p>
        </div>
        
        <SimpleTaskManager projectId="demo_project" taskTreeId="main" />
      </div>
    </div>
  );
}

export default SimpleApp;