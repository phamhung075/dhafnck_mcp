/**
 * ContextDelegationWorkflow Component
 * Step-by-step wizard for delegating context patterns to higher levels
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Alert } from './ui/alert';
import {
  ContextDelegationWorkflowProps,
  DelegationRequest,
  DelegationStep,
  DelegationPattern,
  DelegationTarget,
  DelegationPreview
} from '../types/context-delegation';

export function ContextDelegationWorkflow({
  sourceContext,
  availableTargets,
  onDelegate,
  onPreviewDelegation,
  delegationHistory,
  availablePatterns
}: ContextDelegationWorkflowProps) {
  const [currentStep, setCurrentStep] = useState<DelegationStep>('pattern-selection');
  const [selectedPattern, setSelectedPattern] = useState<DelegationPattern | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<DelegationTarget | null>(null);
  const [delegationRequest, setDelegationRequest] = useState<Partial<DelegationRequest>>({});
  const [preview, setPreview] = useState<DelegationPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Workflow steps configuration
  const steps: Array<{
    id: DelegationStep;
    title: string;
    description: string;
    icon: string;
  }> = [
    {
      id: 'pattern-selection',
      title: 'Select Pattern',
      description: 'Choose what to delegate',
      icon: '🎯'
    },
    {
      id: 'target-selection',
      title: 'Select Target',
      description: 'Choose delegation target',
      icon: '📍'
    },
    {
      id: 'configuration',
      title: 'Configure',
      description: 'Configure pattern details',
      icon: '⚙️'
    },
    {
      id: 'preview',
      title: 'Preview',
      description: 'Review before submission',
      icon: '👁️'
    },
    {
      id: 'submission',
      title: 'Submit',
      description: 'Submit for approval',
      icon: '✅'
    }
  ];

  // Navigation functions
  const nextStep = useCallback(() => {
    const currentIndex = steps.findIndex(s => s.id === currentStep);
    if (currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1].id);
      setError(null);
    }
  }, [currentStep, steps]);

  const prevStep = useCallback(() => {
    const currentIndex = steps.findIndex(s => s.id === currentStep);
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1].id);
      setError(null);
    }
  }, [currentStep, steps]);

  // Reset workflow
  const resetWorkflow = useCallback(() => {
    setCurrentStep('pattern-selection');
    setSelectedPattern(null);
    setSelectedTarget(null);
    setDelegationRequest({});
    setPreview(null);
    setError(null);
  }, []);

  // Pattern auto-detection
  const detectPatterns = useCallback(() => {
    const detectedPatterns: DelegationPattern[] = [];
    
    // Analyze source context for common patterns
    if (sourceContext.data.title?.includes('component') || sourceContext.data.title?.includes('UI')) {
      detectedPatterns.push({
        type: 'reusable_component',
        name: 'UI Component Pattern',
        description: 'Reusable UI component with props and styling',
        required_fields: ['implementation', 'usage_guide'],
        optional_fields: ['tags', 'category']
      });
    }

    if (sourceContext.data.description?.includes('auth') || sourceContext.data.description?.includes('security')) {
      detectedPatterns.push({
        type: 'best_practice',
        name: 'Security Best Practice',
        description: 'Security implementation or methodology',
        required_fields: ['implementation', 'usage_guide'],
        optional_fields: ['tags', 'category']
      });
    }

    if (sourceContext.data.labels?.includes('config') || sourceContext.data.labels?.includes('setup')) {
      detectedPatterns.push({
        type: 'configuration',
        name: 'Configuration Pattern',
        description: 'Reusable configuration or settings',
        required_fields: ['implementation', 'usage_guide'],
        optional_fields: ['tags', 'category']
      });
    }

    return detectedPatterns;
  }, [sourceContext]);

  // Generate preview
  const generatePreview = useCallback(async () => {
    if (!selectedPattern || !selectedTarget || !delegationRequest.delegation_data) {
      return;
    }

    setLoading(true);
    try {
      const request: DelegationRequest = {
        source_context_id: sourceContext.context_id,
        source_level: sourceContext.level as 'task' | 'project',
        target_level: selectedTarget.level,
        delegation_data: delegationRequest.delegation_data,
        delegation_reason: delegationRequest.delegation_reason || ''
      };

      const previewResult = await onPreviewDelegation(request);
      setPreview(previewResult);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to generate preview');
    } finally {
      setLoading(false);
    }
  }, [selectedPattern, selectedTarget, delegationRequest, sourceContext, onPreviewDelegation]);

  // Submit delegation
  const submitDelegation = useCallback(async () => {
    if (!selectedPattern || !selectedTarget || !delegationRequest.delegation_data) {
      setError('Missing required information');
      return;
    }

    setLoading(true);
    try {
      const request: DelegationRequest = {
        source_context_id: sourceContext.context_id,
        source_level: sourceContext.level as 'task' | 'project',
        target_level: selectedTarget.level,
        delegation_data: delegationRequest.delegation_data,
        delegation_reason: delegationRequest.delegation_reason || ''
      };

      await onDelegate(request);
      resetWorkflow();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to submit delegation');
    } finally {
      setLoading(false);
    }
  }, [selectedPattern, selectedTarget, delegationRequest, sourceContext, onDelegate, resetWorkflow]);

  // Auto-generate preview when configuration changes
  useEffect(() => {
    if (currentStep === 'preview' && selectedPattern && selectedTarget && delegationRequest.delegation_data) {
      generatePreview();
    }
  }, [currentStep, generatePreview]);

  // Render step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 'pattern-selection':
        return <PatternSelectionStep 
          patterns={[...availablePatterns, ...detectPatterns()]}
          selectedPattern={selectedPattern}
          onSelectPattern={setSelectedPattern}
          sourceContext={sourceContext}
        />;
      
      case 'target-selection':
        return <TargetSelectionStep
          targets={availableTargets}
          selectedTarget={selectedTarget}
          onSelectTarget={setSelectedTarget}
          sourceLevel={sourceContext.level}
        />;
      
      case 'configuration':
        return <ConfigurationStep
          pattern={selectedPattern}
          sourceContext={sourceContext}
          delegationData={delegationRequest.delegation_data}
          delegationReason={delegationRequest.delegation_reason}
          onUpdateData={(data) => setDelegationRequest(prev => ({ ...prev, delegation_data: data }))}
          onUpdateReason={(reason) => setDelegationRequest(prev => ({ ...prev, delegation_reason: reason }))}
        />;
      
      case 'preview':
        return <PreviewStep
          delegationRequest={delegationRequest as DelegationRequest}
          selectedPattern={selectedPattern}
          selectedTarget={selectedTarget}
          preview={preview}
          loading={loading}
        />;
      
      case 'submission':
        return <SubmissionStep
          onSubmit={submitDelegation}
          loading={loading}
          onReset={resetWorkflow}
        />;
      
      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Progress Steps */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className={`
                flex items-center justify-center w-10 h-10 rounded-full text-sm font-medium
                ${currentStep === step.id 
                  ? 'bg-blue-500 text-white' 
                  : steps.findIndex(s => s.id === currentStep) > index
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-600'
                }
              `}>
                {steps.findIndex(s => s.id === currentStep) > index ? '✓' : step.icon}
              </div>
              <div className="ml-2 hidden md:block">
                <p className="text-sm font-medium">{step.title}</p>
                <p className="text-xs text-gray-500">{step.description}</p>
              </div>
              {index < steps.length - 1 && (
                <div className={`
                  w-8 h-px mx-4
                  ${steps.findIndex(s => s.id === currentStep) > index ? 'bg-green-500' : 'bg-gray-300'}
                `} />
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert className="bg-red-50 border-red-200">
          <span className="text-red-600">{error}</span>
        </Alert>
      )}

      {/* Step Content */}
      <Card className="p-6">
        {renderStepContent()}
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={prevStep}
          disabled={currentStep === 'pattern-selection' || loading}
        >
          ← Previous
        </Button>
        
        <div className="flex space-x-2">
          <Button
            variant="outline"
            onClick={resetWorkflow}
            disabled={loading}
          >
            Reset
          </Button>
          
          {currentStep !== 'submission' && (
            <Button
              onClick={nextStep}
              disabled={
                loading ||
                (currentStep === 'pattern-selection' && !selectedPattern) ||
                (currentStep === 'target-selection' && !selectedTarget) ||
                (currentStep === 'configuration' && (!delegationRequest.delegation_data || !delegationRequest.delegation_reason))
              }
            >
              Next →
            </Button>
          )}
        </div>
      </div>

      {/* Delegation History */}
      {delegationHistory.length > 0 && (
        <Card className="p-4">
          <h3 className="font-medium mb-3">Recent Delegations</h3>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {delegationHistory.slice(0, 5).map((item, index) => (
              <div key={index} className="text-sm p-2 bg-gray-50 rounded">
                <div className="flex justify-between">
                  <span>{item.action}</span>
                  <span className="text-gray-500">
                    {new Date(item.timestamp).toLocaleString()}
                  </span>
                </div>
                <p className="text-gray-600 mt-1">{item.details}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

// Pattern Selection Step
function PatternSelectionStep({
  patterns,
  selectedPattern,
  onSelectPattern,
  sourceContext
}: {
  patterns: DelegationPattern[];
  selectedPattern: DelegationPattern | null;
  onSelectPattern: (pattern: DelegationPattern) => void;
  sourceContext: any;
}) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold mb-2">Select Pattern Type</h2>
        <p className="text-gray-600">Choose what type of pattern you want to delegate from this context.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {patterns.map((pattern, index) => (
          <div
            key={index}
            className={`
              border rounded-lg p-4 cursor-pointer transition-colors
              ${selectedPattern?.type === pattern.type 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300'
              }
            `}
            onClick={() => onSelectPattern(pattern)}
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-medium">{pattern.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{pattern.description}</p>
                <Badge variant="outline" className="mt-2">
                  {pattern.type.replace('_', ' ')}
                </Badge>
              </div>
              {selectedPattern?.type === pattern.type && (
                <div className="text-blue-500">✓</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {patterns.length === 0 && (
        <Alert>
          <span>No patterns available for delegation from this context.</span>
        </Alert>
      )}
    </div>
  );
}

// Target Selection Step
function TargetSelectionStep({
  targets,
  selectedTarget,
  onSelectTarget,
  sourceLevel
}: {
  targets: DelegationTarget[];
  selectedTarget: DelegationTarget | null;
  onSelectTarget: (target: DelegationTarget) => void;
  sourceLevel: string;
}) {
  const validTargets = targets.filter(target => {
    if (sourceLevel === 'task') return ['project', 'global'].includes(target.level);
    if (sourceLevel === 'project') return target.level === 'global';
    return false;
  });

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold mb-2">Select Delegation Target</h2>
        <p className="text-gray-600">Choose where to delegate this pattern.</p>
      </div>

      <div className="space-y-3">
        {validTargets.map((target, index) => (
          <div
            key={index}
            className={`
              border rounded-lg p-4 cursor-pointer transition-colors
              ${selectedTarget?.context_id === target.context_id 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300'
              }
            `}
            onClick={() => onSelectTarget(target)}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium">{target.display_name}</h3>
                {target.description && (
                  <p className="text-sm text-gray-600 mt-1">{target.description}</p>
                )}
                <div className="flex items-center space-x-2 mt-2">
                  <Badge variant={target.level === 'global' ? 'default' : 'secondary'}>
                    {target.level}
                  </Badge>
                  <span className="text-xs text-gray-500">{target.context_id}</span>
                </div>
              </div>
              {selectedTarget?.context_id === target.context_id && (
                <div className="text-blue-500">✓</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {validTargets.length === 0 && (
        <Alert>
          <span>No valid delegation targets available for this context level.</span>
        </Alert>
      )}
    </div>
  );
}

// Configuration Step
function ConfigurationStep({
  pattern,
  sourceContext,
  delegationData,
  delegationReason,
  onUpdateData,
  onUpdateReason
}: {
  pattern: DelegationPattern | null;
  sourceContext: any;
  delegationData: any;
  delegationReason: string | undefined;
  onUpdateData: (data: any) => void;
  onUpdateReason: (reason: string) => void;
}) {
  const [data, setData] = useState<any>(delegationData || {
    pattern_name: '',
    pattern_type: pattern?.type || 'reusable_component',
    implementation: {},
    usage_guide: '',
    tags: []
  });

  useEffect(() => {
    onUpdateData(data);
  }, [data, onUpdateData]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-2">Configure Pattern</h2>
        <p className="text-gray-600">Provide details about the pattern to be delegated.</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Pattern Name</label>
          <Input
            value={data.pattern_name}
            onChange={(e) => setData((prev: any) => ({ ...prev, pattern_name: e.target.value }))}
            placeholder="Enter a descriptive name for this pattern"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Usage Guide</label>
          <textarea
            value={data.usage_guide}
            onChange={(e) => setData((prev: any) => ({ ...prev, usage_guide: e.target.value }))}
            placeholder="Describe how and when to use this pattern"
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Implementation</label>
          <textarea
            value={JSON.stringify(data.implementation, null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                setData((prev: any) => ({ ...prev, implementation: parsed }));
              } catch {
                // Invalid JSON, keep typing
              }
            }}
            placeholder="Enter implementation details as JSON"
            rows={8}
            className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Delegation Reason</label>
          <textarea
            value={delegationReason || ''}
            onChange={(e) => onUpdateReason(e.target.value)}
            placeholder="Explain why this pattern should be delegated"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>
  );
}

// Preview Step
function PreviewStep({
  delegationRequest,
  selectedPattern,
  selectedTarget,
  preview,
  loading
}: {
  delegationRequest: DelegationRequest;
  selectedPattern: DelegationPattern | null;
  selectedTarget: DelegationTarget | null;
  preview: DelegationPreview | null;
  loading: boolean;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-2">Preview Delegation</h2>
        <p className="text-gray-600">Review the delegation details before submission.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-4">
          <h3 className="font-medium mb-3">Delegation Details</h3>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-gray-500">Pattern:</span>
              <span className="ml-2">{selectedPattern?.name}</span>
            </div>
            <div>
              <span className="text-gray-500">Target:</span>
              <span className="ml-2">{selectedTarget?.display_name}</span>
            </div>
            <div>
              <span className="text-gray-500">Level:</span>
              <span className="ml-2">{selectedTarget?.level}</span>
            </div>
            <div>
              <span className="text-gray-500">Pattern Name:</span>
              <span className="ml-2">{delegationRequest.delegation_data?.pattern_name}</span>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <h3 className="font-medium mb-3">Impact Analysis</h3>
          {loading ? (
            <div className="flex items-center justify-center h-20">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            </div>
          ) : preview ? (
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-500">Estimated Impact:</span>
                <Badge variant={
                  preview.estimated_impact === 'high' ? 'destructive' :
                  preview.estimated_impact === 'medium' ? 'default' : 'secondary'
                } className="ml-2">
                  {preview.estimated_impact}
                </Badge>
              </div>
              <div>
                <span className="text-gray-500">Affected Contexts:</span>
                <span className="ml-2">{preview.affected_contexts.length}</span>
              </div>
              <div>
                <span className="text-gray-500">Potential Conflicts:</span>
                <span className="ml-2">{preview.potential_conflicts.length}</span>
              </div>
              <div>
                <span className="text-gray-500">Approval Likelihood:</span>
                <span className="ml-2">{Math.round(preview.approval_likelihood * 100)}%</span>
              </div>
            </div>
          ) : (
            <p className="text-gray-500">No preview available</p>
          )}
        </Card>
      </div>

      {preview?.recommendations && preview.recommendations.length > 0 && (
        <Card className="p-4">
          <h3 className="font-medium mb-3">Recommendations</h3>
          <ul className="space-y-1 text-sm">
            {preview.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}

// Submission Step
function SubmissionStep({
  onSubmit,
  loading,
  onReset
}: {
  onSubmit: () => void;
  loading: boolean;
  onReset: () => void;
}) {
  return (
    <div className="text-center space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-2">Submit Delegation</h2>
        <p className="text-gray-600">
          Your delegation request will be submitted to the approval queue for review.
        </p>
      </div>

      <div className="flex justify-center space-x-4">
        <Button
          variant="outline"
          onClick={onReset}
          disabled={loading}
        >
          Start Over
        </Button>
        <Button
          onClick={onSubmit}
          disabled={loading}
          className="px-8"
        >
          {loading ? 'Submitting...' : 'Submit Delegation'}
        </Button>
      </div>

      {loading && (
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-gray-600">Processing delegation...</span>
        </div>
      )}
    </div>
  );
}