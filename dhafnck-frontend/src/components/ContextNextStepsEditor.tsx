/**
 * ContextNextStepsEditor Component
 * Edit and manage next steps for context planning
 */

import React, { useState, useCallback } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Alert } from './ui/alert';

interface ContextNextStepsEditorProps {
  contextId: string;
  nextSteps: string[];
  onUpdateNextSteps: (steps: string[]) => void;
  readOnly?: boolean;
}

export function ContextNextStepsEditor({
  contextId,
  nextSteps,
  onUpdateNextSteps,
  readOnly = false
}: ContextNextStepsEditorProps) {
  const [steps, setSteps] = useState<string[]>(nextSteps);
  const [newStep, setNewStep] = useState('');
  const [isDirty, setIsDirty] = useState(false);

  // Handle adding new step
  const handleAddStep = useCallback(() => {
    if (!newStep.trim()) return;

    const updatedSteps = [...steps, newStep.trim()];
    setSteps(updatedSteps);
    setNewStep('');
    setIsDirty(true);
  }, [steps, newStep]);

  // Handle removing step
  const handleRemoveStep = useCallback((index: number) => {
    const updatedSteps = steps.filter((_, i) => i !== index);
    setSteps(updatedSteps);
    setIsDirty(true);
  }, [steps]);

  // Handle editing step
  const handleEditStep = useCallback((index: number, newValue: string) => {
    const updatedSteps = [...steps];
    updatedSteps[index] = newValue;
    setSteps(updatedSteps);
    setIsDirty(true);
  }, [steps]);

  // Handle reordering steps
  const handleMoveStep = useCallback((fromIndex: number, toIndex: number) => {
    const updatedSteps = [...steps];
    const [movedStep] = updatedSteps.splice(fromIndex, 1);
    updatedSteps.splice(toIndex, 0, movedStep);
    setSteps(updatedSteps);
    setIsDirty(true);
  }, [steps]);

  // Handle saving changes
  const handleSave = useCallback(async () => {
    try {
      await onUpdateNextSteps(steps);
      setIsDirty(false);
    } catch (error) {
      console.error('Failed to update next steps:', error);
    }
  }, [steps, onUpdateNextSteps]);

  // Handle key press for adding steps
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddStep();
    }
  }, [handleAddStep]);

  // Reset to original state
  const handleReset = useCallback(() => {
    setSteps(nextSteps);
    setNewStep('');
    setIsDirty(false);
  }, [nextSteps]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Next Steps</h2>
          <p className="text-sm text-gray-600">
            Plan and organize upcoming actions
          </p>
        </div>
        {isDirty && !readOnly && (
          <div className="flex space-x-2">
            <Button size="sm" variant="outline" onClick={handleReset}>
              Reset
            </Button>
            <Button size="sm" onClick={handleSave}>
              Save Changes
            </Button>
          </div>
        )}
      </div>

      {/* Add New Step */}
      {!readOnly && (
        <Card className="p-4">
          <div className="flex space-x-2">
            <Input
              value={newStep}
              onChange={(e) => setNewStep(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Add a new next step..."
              className="flex-1"
            />
            <Button onClick={handleAddStep} disabled={!newStep.trim()}>
              Add Step
            </Button>
          </div>
        </Card>
      )}

      {/* Steps List */}
      <div className="space-y-2">
        {steps.length === 0 ? (
          <Alert>
            <span>No next steps defined. Add steps to plan upcoming work.</span>
          </Alert>
        ) : (
          steps.map((step, index) => (
            <StepItem
              key={index}
              step={step}
              index={index}
              totalSteps={steps.length}
              onEdit={(newValue) => handleEditStep(index, newValue)}
              onRemove={() => handleRemoveStep(index)}
              onMoveUp={() => handleMoveStep(index, index - 1)}
              onMoveDown={() => handleMoveStep(index, index + 1)}
              readOnly={readOnly}
            />
          ))
        )}
      </div>

      {/* Quick Actions */}
      {!readOnly && steps.length > 0 && (
        <Card className="p-4">
          <h3 className="font-medium mb-3">Quick Actions</h3>
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                const commonSteps = [
                  'Review and test implementation',
                  'Update documentation',
                  'Get stakeholder feedback',
                  'Plan next iteration'
                ];
                const newSteps = [...steps, ...commonSteps.filter(s => !steps.includes(s))];
                setSteps(newSteps);
                setIsDirty(true);
              }}
            >
              + Add Common Steps
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                const sortedSteps = [...steps].sort();
                setSteps(sortedSteps);
                setIsDirty(true);
              }}
            >
              Sort Alphabetically
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSteps([]);
                setIsDirty(true);
              }}
            >
              Clear All
            </Button>
          </div>
        </Card>
      )}

      {/* Step Templates */}
      {!readOnly && (
        <Card className="p-4">
          <h3 className="font-medium mb-3">Step Templates</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {stepTemplates.map(template => (
              <div
                key={template.name}
                className="p-3 border border-gray-200 rounded-md cursor-pointer hover:border-gray-300"
                onClick={() => {
                  const newSteps = [...steps, ...template.steps.filter(s => !steps.includes(s))];
                  setSteps(newSteps);
                  setIsDirty(true);
                }}
              >
                <h4 className="font-medium text-sm">{template.name}</h4>
                <p className="text-xs text-gray-600 mt-1">{template.description}</p>
                <div className="text-xs text-gray-500 mt-2">
                  {template.steps.length} steps
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

// Individual Step Item Component
function StepItem({
  step,
  index,
  totalSteps,
  onEdit,
  onRemove,
  onMoveUp,
  onMoveDown,
  readOnly
}: {
  step: string;
  index: number;
  totalSteps: number;
  onEdit: (newValue: string) => void;
  onRemove: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  readOnly: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(step);

  const handleSave = () => {
    if (editValue.trim()) {
      onEdit(editValue.trim());
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(step);
    setIsEditing(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  return (
    <Card className="p-3">
      <div className="flex items-center space-x-3">
        {/* Step Number */}
        <div className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full text-sm font-medium">
          {index + 1}
        </div>

        {/* Step Content */}
        <div className="flex-1">
          {isEditing && !readOnly ? (
            <Input
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyPress={handleKeyPress}
              onBlur={handleSave}
              className="w-full"
              autoFocus
            />
          ) : (
            <span
              className={`${!readOnly ? 'cursor-pointer hover:text-blue-600' : ''}`}
              onClick={() => !readOnly && setIsEditing(true)}
            >
              {step}
            </span>
          )}
        </div>

        {/* Controls */}
        {!readOnly && (
          <div className="flex items-center space-x-1">
            {isEditing ? (
              <>
                <Button size="sm" onClick={handleSave}>
                  ✓
                </Button>
                <Button size="sm" variant="outline" onClick={handleCancel}>
                  ✕
                </Button>
              </>
            ) : (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onMoveUp}
                  disabled={index === 0}
                  title="Move up"
                >
                  ↑
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onMoveDown}
                  disabled={index === totalSteps - 1}
                  title="Move down"
                >
                  ↓
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setIsEditing(true)}
                  title="Edit"
                >
                  ✏️
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onRemove}
                  title="Remove"
                >
                  🗑️
                </Button>
              </>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

// Predefined step templates
const stepTemplates = [
  {
    name: 'Development Workflow',
    description: 'Standard development process steps',
    steps: [
      'Design system architecture',
      'Implement core functionality',
      'Write unit tests',
      'Perform integration testing',
      'Code review and optimization',
      'Deploy to staging environment',
      'User acceptance testing',
      'Production deployment'
    ]
  },
  {
    name: 'Feature Planning',
    description: 'Steps for planning new features',
    steps: [
      'Gather requirements from stakeholders',
      'Create user stories and acceptance criteria',
      'Design mockups and wireframes',
      'Estimate development effort',
      'Plan sprint iterations',
      'Set up tracking and metrics'
    ]
  },
  {
    name: 'Bug Investigation',
    description: 'Systematic bug resolution process',
    steps: [
      'Reproduce the issue',
      'Analyze logs and error messages',
      'Identify root cause',
      'Develop and test fix',
      'Verify fix in different environments',
      'Update documentation if needed'
    ]
  },
  {
    name: 'Project Handoff',
    description: 'Steps for project completion and handoff',
    steps: [
      'Complete final testing',
      'Update all documentation',
      'Prepare deployment guide',
      'Train end users',
      'Set up monitoring and alerts',
      'Schedule follow-up reviews'
    ]
  }
];