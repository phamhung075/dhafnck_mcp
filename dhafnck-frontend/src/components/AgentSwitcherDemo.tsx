import React, { useState } from 'react';
import { AgentSwitcher, useAgentSwitcher, useWorkTypeDetection, WorkType } from './AgentSwitcher';
import { Agent } from '../api/enhanced';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

export function AgentSwitcherDemo() {
  const [taskDescription, setTaskDescription] = useState('');
  const [userInput, setUserInput] = useState('');
  
  // Mock project ID for demo
  const projectId = "default_project";
  
  // Use the agent switcher hook
  const { state, switchAgent, refreshAgents } = useAgentSwitcher(projectId);
  
  // Detect work type from inputs
  const workType = useWorkTypeDetection(taskDescription, userInput);

  // Mock agents if none are loaded
  const mockAgents: Agent[] = [
    {
      id: "1",
      name: "@uber_orchestrator_agent",
      project_id: projectId,
      status: "active"
    },
    {
      id: "2", 
      name: "@debugger_agent",
      project_id: projectId,
      status: "idle"
    },
    {
      id: "3",
      name: "@coding_agent", 
      project_id: projectId,
      status: "busy"
    },
    {
      id: "4",
      name: "@test_orchestrator_agent",
      project_id: projectId,
      status: "idle"
    },
    {
      id: "5",
      name: "@ui_designer_agent",
      project_id: projectId,
      status: "error"
    }
  ];

  const availableAgents = state.availableAgents.length > 0 ? state.availableAgents : mockAgents;

  const handleAgentSwitch = async (agent: Agent) => {
    console.log('Switching to agent:', agent.name);
    await switchAgent(agent);
  };

  const handleRefreshAgents = async () => {
    console.log('Refreshing agents...');
    await refreshAgents();
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Agent Switcher Demo</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          
          {/* Input Section */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Task Description:</label>
              <Input
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                placeholder="Describe what you want to work on..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">User Input:</label>
              <Input
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="Additional context or commands..."
              />
            </div>
          </div>

          {/* Work Type Detection Display */}
          {workType && (
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-4">
                <div className="text-sm">
                  <strong>Detected Work Type:</strong> {workType.category}
                  <br />
                  <strong>Confidence:</strong> {Math.round(workType.confidence * 100)}%
                  <br />
                  <strong>Keywords:</strong> {workType.keywords.join(', ')}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Current State Display */}
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm space-y-2">
                <div><strong>Current Agent:</strong> {state.currentAgent?.name || 'None'}</div>
                <div><strong>Available Agents:</strong> {availableAgents.length}</div>
                <div><strong>Switch in Progress:</strong> {state.switchInProgress ? 'Yes' : 'No'}</div>
                <div><strong>Last Switch:</strong> {state.lastSwitch?.toLocaleTimeString() || 'Never'}</div>
              </div>
            </CardContent>
          </Card>
        </CardContent>
      </Card>

      {/* Agent Switcher Component */}
      <div className="flex justify-center">
        <AgentSwitcher
          currentAgent={state.currentAgent}
          availableAgents={availableAgents}
          workType={workType || undefined}
          onAgentSwitch={handleAgentSwitch}
          onRefreshAgents={handleRefreshAgents}
          className="w-80"
        />
      </div>

      {/* Agent History */}
      {state.agentHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Agent History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {state.agentHistory.map((agent, index) => (
                <div key={`${agent.id}-${index}`} className="flex items-center justify-between">
                  <span className="text-sm">{agent.name}</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAgentSwitch(agent)}
                  >
                    Switch Back
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Test Scenarios */}
      <Card>
        <CardHeader>
          <CardTitle>Test Scenarios</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setTaskDescription('Fix the login bug that crashes the app');
                setUserInput('debug the authentication error');
              }}
            >
              Test Debug Scenario
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setTaskDescription('Implement new user registration feature');
                setUserInput('code the signup form with validation');
              }}
            >
              Test Implementation Scenario
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setTaskDescription('Create unit tests for the API endpoints');
                setUserInput('test coverage for authentication endpoints');
              }}
            >
              Test Testing Scenario
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setTaskDescription('Design a new dashboard interface');
                setUserInput('UI mockup for analytics dashboard');
              }}
            >
              Test Design Scenario
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default AgentSwitcherDemo;