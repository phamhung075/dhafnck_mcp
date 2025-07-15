import React, { useState } from 'react';
import { CreateProjectData, ProjectTemplate, TaskTemplate } from './ProjectDashboard';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Badge } from './ui/badge';

interface ProjectCreationWizardProps {
  onCreateProject: (projectData: CreateProjectData) => Promise<void>;
  onCancel: () => void;
  templates: ProjectTemplate[];
}

interface StepProps {
  data: CreateProjectData;
  onChange: (data: CreateProjectData) => void;
  templates?: ProjectTemplate[];
}

export function ProjectCreationWizard({
  onCreateProject,
  onCancel,
  templates
}: ProjectCreationWizardProps) {
  const [step, setStep] = useState(1);
  const [projectData, setProjectData] = useState<CreateProjectData>({
    name: '',
    description: '',
    initial_branches: ['main'],
    assigned_agents: [],
    estimated_duration: '',
    priority: 'medium',
    tags: []
  });

  const steps = [
    { id: 1, title: 'Basic Information', component: BasicInfoStep },
    { id: 2, title: 'Template Selection', component: TemplateSelectionStep },
    { id: 3, title: 'Configuration', component: ConfigurationStep },
    { id: 4, title: 'Review & Create', component: ReviewStep }
  ];

  const isStepValid = (currentStep: number, data: CreateProjectData): boolean => {
    switch (currentStep) {
      case 1:
        return data.name.trim().length > 0;
      case 2:
        return true; // Template selection is optional
      case 3:
        return data.initial_branches.length > 0;
      case 4:
        return true; // Review step is always valid
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (step < 4) {
      setStep(step + 1);
    }
  };

  const handlePrevious = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleCreate = async () => {
    try {
      await onCreateProject(projectData);
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  const CurrentStepComponent = steps[step - 1].component;

  return (
    <div className="w-full">
      {/* Progress Indicator */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          {steps.map((s, idx) => (
            <div key={s.id} className="flex items-center flex-1">
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= s.id 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {step > s.id ? '✓' : s.id}
                </div>
                <div className="ml-2 hidden sm:block">
                  <div className={`text-sm font-medium ${
                    step >= s.id ? 'text-blue-600' : 'text-gray-500'
                  }`}>
                    {s.title}
                  </div>
                </div>
              </div>
              {idx < steps.length - 1 && (
                <div className={`flex-1 h-1 mx-4 ${
                  step > s.id ? 'bg-blue-600' : 'bg-gray-200'
                }`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="min-h-[400px]">
        <CurrentStepComponent 
          data={projectData} 
          onChange={setProjectData}
          templates={templates}
        />
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-6 border-t mt-6">
        <Button
          variant="outline"
          onClick={step === 1 ? onCancel : handlePrevious}
        >
          {step === 1 ? 'Cancel' : 'Previous'}
        </Button>
        
        {step < 4 ? (
          <Button
            onClick={handleNext}
            disabled={!isStepValid(step, projectData)}
          >
            Next
          </Button>
        ) : (
          <Button
            onClick={handleCreate}
            className="bg-green-600 hover:bg-green-700"
          >
            Create Project
          </Button>
        )}
      </div>
    </div>
  );
}

// Step 1: Basic Information
function BasicInfoStep({ data, onChange }: StepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Project Basic Information</h3>
        <p className="text-gray-600 mb-6">
          Let's start with the basic details of your project.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            Project Name <span className="text-red-500">*</span>
          </label>
          <Input
            value={data.name}
            onChange={(e) => onChange({ ...data, name: e.target.value })}
            placeholder="Enter project name"
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Description
          </label>
          <textarea
            value={data.description}
            onChange={(e) => onChange({ ...data, description: e.target.value })}
            placeholder="Describe your project..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md resize-none"
            rows={4}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Priority</label>
          <select
            value={data.priority}
            onChange={(e) => onChange({ ...data, priority: e.target.value as any })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Estimated Duration
          </label>
          <Input
            value={data.estimated_duration}
            onChange={(e) => onChange({ ...data, estimated_duration: e.target.value })}
            placeholder="e.g., 2 weeks, 1 month"
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
}

// Step 2: Template Selection
function TemplateSelectionStep({ data, onChange, templates = [] }: StepProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<ProjectTemplate | null>(null);

  const handleTemplateSelect = (template: ProjectTemplate) => {
    setSelectedTemplate(template);
    onChange({
      ...data,
      template_id: template.id,
      initial_branches: [...template.default_branches],
      assigned_agents: [...template.recommended_agents]
    });
  };

  const handleSkipTemplate = () => {
    setSelectedTemplate(null);
    onChange({
      ...data,
      template_id: undefined,
      initial_branches: ['main'],
      assigned_agents: []
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Choose a Project Template</h3>
        <p className="text-gray-600 mb-6">
          Select a template to get started quickly, or skip to configure manually.
        </p>
      </div>

      <div className="grid gap-4">
        {templates.map((template) => (
          <Card 
            key={template.id}
            className={`p-4 cursor-pointer transition-all border-2 ${
              selectedTemplate?.id === template.id 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => handleTemplateSelect(template)}
          >
            <div className="flex justify-between items-start mb-3">
              <div>
                <h4 className="font-semibold">{template.name}</h4>
                <p className="text-sm text-gray-600">{template.description}</p>
              </div>
              {selectedTemplate?.id === template.id && (
                <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm">✓</span>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <div>
                <div className="text-xs font-medium text-gray-700 mb-1">Default Branches:</div>
                <div className="flex flex-wrap gap-1">
                  {template.default_branches.map((branch, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs">
                      {branch}
                    </Badge>
                  ))}
                </div>
              </div>
              
              <div>
                <div className="text-xs font-medium text-gray-700 mb-1">Recommended Agents:</div>
                <div className="flex flex-wrap gap-1">
                  {template.recommended_agents.map((agent, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {agent}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <div className="text-xs font-medium text-gray-700 mb-1">Initial Tasks:</div>
                <ul className="text-xs text-gray-600 space-y-1">
                  {template.initial_tasks.slice(0, 3).map((task, idx) => (
                    <li key={idx} className="flex items-start gap-1">
                      <span className="text-gray-400">•</span>
                      <span>{task.title}</span>
                    </li>
                  ))}
                  {template.initial_tasks.length > 3 && (
                    <li className="text-gray-500">+{template.initial_tasks.length - 3} more tasks</li>
                  )}
                </ul>
              </div>
            </div>
          </Card>
        ))}

        <Card 
          className={`p-4 cursor-pointer transition-all border-2 border-dashed ${
            !selectedTemplate 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-200 hover:border-gray-300'
          }`}
          onClick={handleSkipTemplate}
        >
          <div className="text-center py-4">
            <div className="text-lg mb-2">🛠️</div>
            <h4 className="font-semibold">Start from Scratch</h4>
            <p className="text-sm text-gray-600">Configure everything manually</p>
          </div>
        </Card>
      </div>
    </div>
  );
}

// Step 3: Configuration
function ConfigurationStep({ data, onChange }: StepProps) {
  const [newBranch, setNewBranch] = useState('');
  const [newAgent, setNewAgent] = useState('');
  const [newTag, setNewTag] = useState('');

  const availableAgents = [
    '@coding_agent',
    '@ui_designer_agent',
    '@test_orchestrator_agent',
    '@debugger_agent',
    '@devops_agent',
    '@security_auditor_agent',
    '@documentation_agent',
    '@deep_research_agent',
    '@uber_orchestrator_agent'
  ];

  const addBranch = () => {
    if (newBranch.trim() && !data.initial_branches.includes(newBranch.trim())) {
      onChange({
        ...data,
        initial_branches: [...data.initial_branches, newBranch.trim()]
      });
      setNewBranch('');
    }
  };

  const removeBranch = (branch: string) => {
    if (data.initial_branches.length > 1) { // Keep at least one branch
      onChange({
        ...data,
        initial_branches: data.initial_branches.filter(b => b !== branch)
      });
    }
  };

  const addAgent = (agent: string) => {
    if (!data.assigned_agents.includes(agent)) {
      onChange({
        ...data,
        assigned_agents: [...data.assigned_agents, agent]
      });
    }
  };

  const removeAgent = (agent: string) => {
    onChange({
      ...data,
      assigned_agents: data.assigned_agents.filter(a => a !== agent)
    });
  };

  const addTag = () => {
    if (newTag.trim() && !data.tags.includes(newTag.trim())) {
      onChange({
        ...data,
        tags: [...data.tags, newTag.trim()]
      });
      setNewTag('');
    }
  };

  const removeTag = (tag: string) => {
    onChange({
      ...data,
      tags: data.tags.filter(t => t !== tag)
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Project Configuration</h3>
        <p className="text-gray-600 mb-6">
          Configure branches, agents, and other project settings.
        </p>
      </div>

      <div className="space-y-6">
        {/* Initial Branches */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Initial Branches <span className="text-red-500">*</span>
          </label>
          <div className="flex gap-2 mb-2">
            <Input
              value={newBranch}
              onChange={(e) => setNewBranch(e.target.value)}
              placeholder="Branch name (e.g., feature/auth)"
              className="flex-1"
              onKeyPress={(e) => e.key === 'Enter' && addBranch()}
            />
            <Button onClick={addBranch} disabled={!newBranch.trim()}>
              Add
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.initial_branches.map((branch, idx) => (
              <Badge 
                key={idx} 
                variant="secondary" 
                className="flex items-center gap-1"
              >
                {branch}
                {data.initial_branches.length > 1 && (
                  <button
                    onClick={() => removeBranch(branch)}
                    className="ml-1 text-red-500 hover:text-red-700"
                  >
                    ×
                  </button>
                )}
              </Badge>
            ))}
          </div>
        </div>

        {/* Assigned Agents */}
        <div>
          <label className="block text-sm font-medium mb-2">Assigned Agents</label>
          <div className="mb-2">
            <select
              value=""
              onChange={(e) => {
                if (e.target.value) {
                  addAgent(e.target.value);
                  e.target.value = '';
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">Select an agent to add...</option>
              {availableAgents
                .filter(agent => !data.assigned_agents.includes(agent))
                .map(agent => (
                  <option key={agent} value={agent}>{agent}</option>
                ))}
            </select>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.assigned_agents.map((agent, idx) => (
              <Badge 
                key={idx} 
                variant="outline" 
                className="flex items-center gap-1"
              >
                {agent}
                <button
                  onClick={() => removeAgent(agent)}
                  className="ml-1 text-red-500 hover:text-red-700"
                >
                  ×
                </button>
              </Badge>
            ))}
          </div>
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium mb-2">Project Tags</label>
          <div className="flex gap-2 mb-2">
            <Input
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              placeholder="Add a tag..."
              className="flex-1"
              onKeyPress={(e) => e.key === 'Enter' && addTag()}
            />
            <Button onClick={addTag} disabled={!newTag.trim()}>
              Add
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.tags.map((tag, idx) => (
              <Badge 
                key={idx} 
                className="flex items-center gap-1"
              >
                {tag}
                <button
                  onClick={() => removeTag(tag)}
                  className="ml-1 text-white hover:text-gray-200"
                >
                  ×
                </button>
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Step 4: Review
function ReviewStep({ data }: StepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Review Project Details</h3>
        <p className="text-gray-600 mb-6">
          Review your project configuration before creating.
        </p>
      </div>

      <Card className="p-4">
        <div className="space-y-4">
          <div>
            <h4 className="font-semibold text-lg">{data.name}</h4>
            <p className="text-gray-600">{data.description}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-700">Priority</div>
              <Badge variant={data.priority === 'urgent' ? 'destructive' : 'secondary'}>
                {data.priority}
              </Badge>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-700">Estimated Duration</div>
              <div className="text-sm">{data.estimated_duration || 'Not specified'}</div>
            </div>
          </div>

          <div>
            <div className="text-sm font-medium text-gray-700 mb-2">Initial Branches</div>
            <div className="flex flex-wrap gap-1">
              {data.initial_branches.map((branch, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  {branch}
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <div className="text-sm font-medium text-gray-700 mb-2">Assigned Agents</div>
            <div className="flex flex-wrap gap-1">
              {data.assigned_agents.map((agent, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {agent}
                </Badge>
              ))}
              {data.assigned_agents.length === 0 && (
                <div className="text-sm text-gray-500">No agents assigned</div>
              )}
            </div>
          </div>

          {data.tags.length > 0 && (
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">Tags</div>
              <div className="flex flex-wrap gap-1">
                {data.tags.map((tag, idx) => (
                  <Badge key={idx} className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}