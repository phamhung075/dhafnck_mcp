import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Separator } from './ui/separator';
import { cn } from '../lib/utils';
import { mcpApi, Agent } from '../api/enhanced';

// --- Core Interfaces ---
export interface WorkType {
  category: 'debug' | 'implement' | 'test' | 'design' | 'research' | 'security' | 'deploy' | 'document' | 'plan' | 'complex';
  keywords: string[];
  confidence: number;
}

export interface AgentSwitcherProps {
  currentAgent: Agent | null;
  availableAgents: Agent[];
  workType?: WorkType;
  onAgentSwitch: (agent: Agent) => Promise<void>;
  onRefreshAgents: () => Promise<void>;
  className?: string;
}

export interface AgentRecommendation {
  primary: string;
  alternatives: string[];
  confidence: number;
  reasoning: string;
}

export interface AgentStatus {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'busy' | 'error';
  last_active: string;
  current_task?: string;
  performance_metrics: {
    success_rate: number;
    avg_response_time: number;
    tasks_completed: number;
  };
}

// --- Agent Selection Logic ---
export class AgentSelector {
  private workTypeToAgent: Record<string, string[]> = {
    debug: ["@debugger_agent", "@root_cause_analysis_agent"],
    implement: ["@coding_agent", "@development_orchestrator_agent"],
    test: ["@test_orchestrator_agent", "@functional_tester_agent", "@exploratory_tester_agent"],
    design: ["@ui_designer_agent", "@design_system_agent", "@ux_researcher_agent"],
    research: ["@deep_research_agent", "@market_research_agent", "@mcp_researcher_agent"],
    security: ["@security_auditor_agent", "@security_penetration_tester_agent", "@compliance_testing_agent"],
    deploy: ["@devops_agent", "@adaptive_deployment_strategist_agent"],
    document: ["@documentation_agent", "@tech_spec_agent", "@scribe_agent"],
    plan: ["@task_planning_agent", "@system_architect_agent", "@workflow_architect_agent"],
    complex: ["@uber_orchestrator_agent", "@workflow_architect_agent", "@system_architect_agent"]
  };

  selectAgent(workType: WorkType): AgentRecommendation {
    const { category, confidence } = workType;
    const agents = this.workTypeToAgent[category] || ["@uber_orchestrator_agent"];
    
    return {
      primary: agents[0],
      alternatives: agents.slice(1),
      confidence: confidence * 0.9, // Slight confidence reduction for agent selection
      reasoning: `Selected ${agents[0]} based on work type "${category}" with ${Math.round(confidence * 100)}% confidence`
    };
  }

  getQuickSwitchAgents(): Array<{ name: string; category: string; icon: string }> {
    return [
      { name: "@debugger_agent", category: "Debug", icon: "🐛" },
      { name: "@coding_agent", category: "Code", icon: "💻" },
      { name: "@test_orchestrator_agent", category: "Test", icon: "🧪" },
      { name: "@ui_designer_agent", category: "Design", icon: "🎨" }
    ];
  }
}

// --- Work Type Detection Hook ---
export function useWorkTypeDetection(
  taskDescription?: string,
  userInput?: string
): WorkType | null {
  const workTypePatterns = {
    debug: /debug|fix|error|bug|troubleshoot|issue|broken|failing|crash|exception/i,
    implement: /implement|code|build|develop|create|write|program|feature|function|class|method/i,
    test: /test|verify|validate|qa|check|coverage|spec|e2e|unit|integration/i,
    design: /design|ui|interface|ux|frontend|component|layout|wireframe|mockup|style/i,
    research: /research|investigate|explore|study|analyze|benchmark|compare|evaluate/i,
    security: /security|audit|vulnerability|penetration|auth|permission|encrypt|secure/i,
    deploy: /deploy|infrastructure|devops|ci\/cd|server|cloud|container|docker|kubernetes/i,
    document: /document|guide|manual|readme|explain|instruction|tutorial|wiki/i,
    plan: /plan|analyze|breakdown|organize|strategy|architecture|workflow|roadmap/i,
    complex: /complex|orchestrate|coordinate|multi-step|integration|workflow|pipeline/i
  };

  return useMemo(() => {
    const input = `${taskDescription || ''} ${userInput || ''}`.toLowerCase();
    if (!input.trim()) return null;

    const matches: Array<{ category: keyof typeof workTypePatterns; score: number }> = [];
    
    for (const [category, pattern] of Object.entries(workTypePatterns)) {
      const match = input.match(pattern);
      if (match) {
        // Calculate confidence based on match length and position
        const score = match[0].length / input.length + (input.indexOf(match[0]) === 0 ? 0.2 : 0);
        matches.push({ category: category as keyof typeof workTypePatterns, score });
      }
    }

    if (matches.length === 0) return null;

    // Sort by score and take the highest
    matches.sort((a, b) => b.score - a.score);
    const best = matches[0];
    const keywords = input.match(workTypePatterns[best.category])?.map(m => m.toLowerCase()) || [];

    return {
      category: best.category,
      keywords,
      confidence: Math.min(best.score * 2, 1) // Cap at 100%
    };
  }, [taskDescription, userInput]);
}

// --- Agent Status Indicator Component ---
function AgentStatusIndicator({ agent, className }: { agent: Agent | AgentStatus; className?: string }) {
  const statusConfig = {
    active: { color: "bg-green-500", label: "Active", pulse: false },
    idle: { color: "bg-yellow-500", label: "Idle", pulse: false },
    busy: { color: "bg-blue-500", label: "Busy", pulse: true },
    error: { color: "bg-red-500", label: "Error", pulse: false }
  };

  const config = statusConfig[agent.status];

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div 
        className={cn(
          "w-2 h-2 rounded-full", 
          config.color,
          config.pulse && "animate-pulse"
        )} 
      />
      <span className="text-xs text-muted-foreground">{config.label}</span>
    </div>
  );
}

// --- Agent Browser Modal ---
function AgentBrowserModal({ 
  isOpen, 
  onClose, 
  agents, 
  onSelectAgent,
  currentAgent 
}: {
  isOpen: boolean;
  onClose: () => void;
  agents: Agent[];
  onSelectAgent: (agent: Agent) => void;
  currentAgent: Agent | null;
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const filteredAgents = useMemo(() => {
    return agents.filter(agent => {
      const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || 
        agent.name.toLowerCase().includes(selectedCategory.toLowerCase());
      return matchesSearch && matchesCategory;
    });
  }, [agents, searchTerm, selectedCategory]);

  const categories = ['all', 'debug', 'coding', 'test', 'design', 'research', 'security', 'devops', 'document'];

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Agent Browser</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Search and Filter */}
          <div className="flex gap-4">
            <Input
              placeholder="Search agents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1"
            />
            <select 
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border rounded-md"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Agent Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
            {filteredAgents.map(agent => (
              <Card 
                key={agent.id} 
                className={cn(
                  "cursor-pointer transition-colors hover:bg-accent",
                  currentAgent?.id === agent.id && "ring-2 ring-primary"
                )}
                onClick={() => {
                  onSelectAgent(agent);
                  onClose();
                }}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">{agent.name}</CardTitle>
                    <AgentStatusIndicator agent={agent} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <CardDescription className="text-xs">
                      Project: {agent.project_id}
                    </CardDescription>
                    {(() => {
                      if ('performance_metrics' in agent && agent.performance_metrics && typeof agent.performance_metrics === 'object') {
                        return (
                          <div className="text-xs space-y-1">
                            <div>Success Rate: {Math.round((agent.performance_metrics as any).success_rate * 100)}%</div>
                            <div>Avg Response: {(agent.performance_metrics as any).avg_response_time}ms</div>
                            <div>Tasks: {(agent.performance_metrics as any).tasks_completed}</div>
                          </div>
                        );
                      }
                      return null;
                    })()}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// --- Main Agent Switcher Component ---
export function AgentSwitcher({
  currentAgent,
  availableAgents,
  workType,
  onAgentSwitch,
  onRefreshAgents,
  className
}: AgentSwitcherProps) {
  const [switchInProgress, setSwitchInProgress] = useState(false);
  const [showBrowser, setShowBrowser] = useState(false);
  const [recommendation, setRecommendation] = useState<AgentRecommendation | null>(null);

  const selector = useMemo(() => new AgentSelector(), []);

  // Update recommendation when work type changes
  useEffect(() => {
    if (workType) {
      const rec = selector.selectAgent(workType);
      setRecommendation(rec);
    } else {
      setRecommendation(null);
    }
  }, [workType, selector]);

  const handleAgentSwitch = useCallback(async (agent: Agent) => {
    if (switchInProgress || agent.id === currentAgent?.id) return;
    
    setSwitchInProgress(true);
    try {
      await onAgentSwitch(agent);
    } catch (error) {
      console.error('Agent switch failed:', error);
    } finally {
      setSwitchInProgress(false);
    }
  }, [switchInProgress, currentAgent?.id, onAgentSwitch]);

  const quickSwitchAgents = selector.getQuickSwitchAgents();
  
  const recommendedAgent = recommendation 
    ? availableAgents.find(a => a.name === recommendation.primary)
    : null;

  return (
    <div className={cn("bg-background border rounded-lg shadow-lg p-4 space-y-4", className)}>
      {/* Current Agent Display */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <span className="font-semibold text-sm">
              {currentAgent?.name || 'No Agent Selected'}
            </span>
            {currentAgent && (
              <AgentStatusIndicator agent={currentAgent} className="mt-1" />
            )}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onRefreshAgents}
          disabled={switchInProgress}
        >
          Refresh
        </Button>
      </div>

      <Separator />

      {/* Work Type Recommendation */}
      {recommendation && recommendedAgent && (
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">Recommended for {workType?.category}:</div>
          <Card className="p-3 bg-blue-50 border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-sm">{recommendedAgent.name}</div>
                <div className="text-xs text-muted-foreground">
                  {Math.round(recommendation.confidence * 100)}% confidence
                </div>
              </div>
              <Button
                size="sm"
                onClick={() => handleAgentSwitch(recommendedAgent)}
                disabled={switchInProgress || recommendedAgent.id === currentAgent?.id}
              >
                Switch
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Quick Switch Buttons */}
      <div className="space-y-2">
        <div className="text-xs text-muted-foreground">Quick Switch:</div>
        <div className="grid grid-cols-2 gap-2">
          {quickSwitchAgents.map(({ name, category, icon }) => {
            const agent = availableAgents.find(a => a.name === name);
            const isActive = agent?.id === currentAgent?.id;
            
            return (
              <Button
                key={name}
                variant={isActive ? "default" : "outline"}
                size="sm"
                className="text-xs p-2 h-auto flex flex-col"
                onClick={() => agent && handleAgentSwitch(agent)}
                disabled={switchInProgress || !agent || isActive}
              >
                <span className="text-lg">{icon}</span>
                <span>{category}</span>
              </Button>
            );
          })}
        </div>
      </div>

      <Separator />

      {/* Advanced Controls */}
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          className="flex-1"
          onClick={() => setShowBrowser(true)}
        >
          Browse All Agents
        </Button>
        {currentAgent && (
          <Badge variant="outline" className="self-center">
            {availableAgents.length} Available
          </Badge>
        )}
      </div>

      {/* Context Preservation Warning */}
      {switchInProgress && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-2">
          <div className="text-xs text-yellow-800">
            ⚠️ Switching agent... Context will be preserved.
          </div>
        </div>
      )}

      {/* Agent Browser Modal */}
      <AgentBrowserModal
        isOpen={showBrowser}
        onClose={() => setShowBrowser(false)}
        agents={availableAgents}
        onSelectAgent={handleAgentSwitch}
        currentAgent={currentAgent}
      />
    </div>
  );
}

// --- State Management Hook ---
export interface AgentState {
  currentAgent: Agent | null;
  availableAgents: Agent[];
  agentHistory: Agent[];
  switchInProgress: boolean;
  lastSwitch: Date | null;
}

export function useAgentSwitcher(projectId: string = "default_project") {
  const [state, setState] = useState<AgentState>({
    currentAgent: null,
    availableAgents: [],
    agentHistory: [],
    switchInProgress: false,
    lastSwitch: null,
  });

  const refreshAgents = useCallback(async () => {
    try {
      const response = await mcpApi.manageAgent('list', { project_id: projectId });
      if (response.success && response.data) {
        const data = response.data as any;
        setState(prev => ({
          ...prev,
          availableAgents: data.agents || []
        }));
      }
    } catch (error) {
      console.error('Failed to refresh agents:', error);
    }
  }, [projectId]);

  const switchAgent = useCallback(async (agent: Agent, preserveContext = true) => {
    setState(prev => ({ ...prev, switchInProgress: true }));
    
    try {
      // Call the agent through the API
      const response = await mcpApi.callAgent(agent.name);
      
      if (response.success) {
        const data = response.data as any;
        setState(prev => ({
          ...prev,
          currentAgent: agent,
          agentHistory: prev.currentAgent 
            ? [prev.currentAgent, ...prev.agentHistory.slice(0, 9)] // Keep last 10
            : prev.agentHistory,
          lastSwitch: new Date(),
          switchInProgress: false
        }));
      } else {
        throw new Error('Agent switch failed');
      }
    } catch (error) {
      console.error('Agent switch error:', error);
      setState(prev => ({ ...prev, switchInProgress: false }));
      throw error;
    }
  }, []);

  // Initialize agents on mount
  useEffect(() => {
    refreshAgents();
  }, [refreshAgents]);

  return { 
    state, 
    switchAgent, 
    refreshAgents,
    actions: {
      setState
    }
  };
}

export default AgentSwitcher;