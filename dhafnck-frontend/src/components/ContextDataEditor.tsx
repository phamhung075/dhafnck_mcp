/**
 * ContextDataEditor Component
 * JSON editor with syntax highlighting, validation, and auto-save capability
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Alert } from './ui/alert';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import {
  ContextDataEditorProps,
  ContextData,
  ValidationError
} from '../types/context-delegation';

export function ContextDataEditor({
  contextData,
  onChange,
  onSave,
  readOnly = false,
  showHistory = false,
  validationErrors = []
}: ContextDataEditorProps) {
  const [editMode, setEditMode] = useState<'form' | 'json'>('form');
  const [jsonData, setJsonData] = useState(() => JSON.stringify(contextData, null, 2));
  const [localData, setLocalData] = useState<ContextData>(contextData);
  const [isDirty, setIsDirty] = useState(false);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  const [changeHistory, setChangeHistory] = useState<Array<{
    timestamp: string;
    field: keyof ContextData | string;
    oldValue: any;
    newValue: any;
  }>>([]);

  const autoSaveTimeoutRef = useRef<number | undefined>(undefined);

  // Auto-save logic
  useEffect(() => {
    if (autoSaveEnabled && isDirty && !readOnly) {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
      
      autoSaveTimeoutRef.current = window.setTimeout(() => {
        handleSave();
      }, 2000); // Auto-save after 2 seconds of inactivity
    }

    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, [isDirty, autoSaveEnabled, readOnly]);

  // Update local state when external data changes
  useEffect(() => {
    setLocalData(contextData);
    setJsonData(JSON.stringify(contextData, null, 2));
    setIsDirty(false);
  }, [contextData]);

  // Handle form field changes
  const handleFieldChange = useCallback((field: keyof ContextData, value: any) => {
    if (readOnly) return;

    const oldValue = localData[field];
    const newData = { ...localData, [field]: value };
    
    setLocalData(newData);
    setIsDirty(true);
    
    // Update change history
    if (showHistory && oldValue !== value) {
      setChangeHistory(prev => [
        ...prev,
        {
          timestamp: new Date().toISOString(),
          field,
          oldValue,
          newValue: value
        }
      ].slice(-50)); // Keep last 50 changes
    }

    onChange(newData);
  }, [localData, onChange, readOnly, showHistory]);

  // Handle JSON changes
  const handleJsonChange = useCallback((newJson: string) => {
    if (readOnly) return;

    setJsonData(newJson);
    setJsonError(null);

    try {
      const parsed = JSON.parse(newJson);
      setLocalData(parsed);
      setIsDirty(true);
      onChange(parsed);
    } catch (error) {
      setJsonError('Invalid JSON: ' + (error as Error).message);
    }
  }, [onChange, readOnly]);

  // Handle save
  const handleSave = useCallback(async () => {
    if (readOnly || jsonError) return;

    try {
      await onSave();
      setIsDirty(false);
    } catch (error) {
      console.error('Failed to save context data:', error);
    }
  }, [onSave, readOnly, jsonError]);

  // Validate field value
  const getFieldValidationError = (field: string): ValidationError | undefined => {
    return validationErrors.find(error => error.field === field);
  };

  // Render form mode
  const renderFormMode = () => {
    const fields = [
      { key: 'title', label: 'Title', type: 'text', placeholder: 'Enter context title' },
      { key: 'description', label: 'Description', type: 'textarea', placeholder: 'Enter context description' },
      { key: 'status', label: 'Status', type: 'select', options: ['todo', 'in_progress', 'blocked', 'review', 'testing', 'done', 'cancelled'] },
      { key: 'priority', label: 'Priority', type: 'select', options: ['low', 'medium', 'high', 'urgent', 'critical'] },
      { key: 'estimated_effort', label: 'Estimated Effort', type: 'text', placeholder: 'e.g., 2 hours, 3 days' },
      { key: 'due_date', label: 'Due Date', type: 'date' },
      { key: 'assignees', label: 'Assignees', type: 'array', placeholder: 'Enter assignee names' },
      { key: 'labels', label: 'Labels', type: 'array', placeholder: 'Enter labels' }
    ];

    return (
      <div className="space-y-4">
        {fields.map(field => {
          const error = getFieldValidationError(field.key);
          const value = localData[field.key as keyof ContextData];

          return (
            <div key={field.key} className="space-y-1">
              <label className="text-sm font-medium text-gray-700">
                {field.label}
              </label>
              
              {field.type === 'text' && (
                <Input
                  value={value || ''}
                  onChange={(e) => handleFieldChange(field.key as keyof ContextData, e.target.value)}
                  placeholder={field.placeholder}
                  disabled={readOnly}
                  className={error ? 'border-red-300' : ''}
                />
              )}

              {field.type === 'textarea' && (
                <textarea
                  value={value || ''}
                  onChange={(e) => handleFieldChange(field.key as keyof ContextData, e.target.value)}
                  placeholder={field.placeholder}
                  disabled={readOnly}
                  rows={3}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    error ? 'border-red-300' : 'border-gray-300'
                  } ${readOnly ? 'bg-gray-50' : ''}`}
                />
              )}

              {field.type === 'select' && (
                <select
                  value={value || ''}
                  onChange={(e) => handleFieldChange(field.key as keyof ContextData, e.target.value)}
                  disabled={readOnly}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    error ? 'border-red-300' : 'border-gray-300'
                  } ${readOnly ? 'bg-gray-50' : ''}`}
                >
                  <option value="">Select {field.label}</option>
                  {field.options?.map(option => (
                    <option key={option} value={option}>
                      {option.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              )}

              {field.type === 'date' && (
                <Input
                  type="date"
                  value={value ? new Date(value).toISOString().split('T')[0] : ''}
                  onChange={(e) => handleFieldChange(field.key as keyof ContextData, e.target.value)}
                  disabled={readOnly}
                  className={error ? 'border-red-300' : ''}
                />
              )}

              {field.type === 'array' && (
                <ArrayEditor
                  values={Array.isArray(value) ? value : []}
                  onChange={(newValues) => handleFieldChange(field.key as keyof ContextData, newValues)}
                  placeholder={field.placeholder}
                  readOnly={readOnly}
                  hasError={!!error}
                />
              )}

              {error && (
                <p className="text-sm text-red-600">{error.message}</p>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  // Render JSON mode
  const renderJsonMode = () => {
    return (
      <div className="space-y-4">
        <div className="relative">
          <textarea
            value={jsonData}
            onChange={(e) => handleJsonChange(e.target.value)}
            disabled={readOnly}
            rows={20}
            className={`w-full px-3 py-2 border rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              jsonError ? 'border-red-300' : 'border-gray-300'
            } ${readOnly ? 'bg-gray-50' : ''}`}
            placeholder="Enter JSON data..."
          />
          
          {jsonError && (
            <Alert className="mt-2 bg-red-50 border-red-200">
              <span className="text-red-600 text-sm">{jsonError}</span>
            </Alert>
          )}
        </div>

        {validationErrors.length > 0 && (
          <Alert className="bg-red-50 border-red-200">
            <div className="text-red-600 text-sm">
              <p className="font-medium mb-1">Validation Errors:</p>
              <ul className="list-disc list-inside space-y-1">
                {validationErrors.map((error, index) => (
                  <li key={index}>{error.field ? `${error.field}: ` : ''}{error.message}</li>
                ))}
              </ul>
            </div>
          </Alert>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="flex rounded-md border border-gray-300 overflow-hidden">
            <button
              className={`px-3 py-1 text-sm ${
                editMode === 'form' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
              onClick={() => setEditMode('form')}
            >
              📝 Form
            </button>
            <button
              className={`px-3 py-1 text-sm ${
                editMode === 'json' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
              onClick={() => setEditMode('json')}
            >
              🔧 JSON
            </button>
          </div>

          {!readOnly && (
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={autoSaveEnabled}
                onChange={(e) => setAutoSaveEnabled(e.target.checked)}
                className="rounded"
              />
              <span>Auto-save</span>
            </label>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {isDirty && <Badge variant="outline">Unsaved changes</Badge>}
          {readOnly && <Badge variant="secondary">Read-only</Badge>}
          
          {!readOnly && (
            <Button
              size="sm"
              onClick={handleSave}
              disabled={!!jsonError || !isDirty}
            >
              💾 Save
            </Button>
          )}
        </div>
      </div>

      {/* Content */}
      <Card className="p-4">
        {editMode === 'form' ? renderFormMode() : renderJsonMode()}
      </Card>

      {/* Change History */}
      {showHistory && changeHistory.length > 0 && (
        <Card className="p-4">
          <h3 className="font-medium mb-3">Change History</h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {changeHistory.slice().reverse().map((change, index) => (
              <div key={index} className="text-sm p-2 bg-gray-50 rounded">
                <div className="flex justify-between items-start">
                  <span className="font-medium">{change.field}</span>
                  <span className="text-gray-500">
                    {new Date(change.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="mt-1">
                  <span className="text-red-600">- {JSON.stringify(change.oldValue)}</span>
                  <br />
                  <span className="text-green-600">+ {JSON.stringify(change.newValue)}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

// Array Editor Component
function ArrayEditor({
  values,
  onChange,
  placeholder,
  readOnly,
  hasError
}: {
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  readOnly: boolean;
  hasError: boolean;
}) {
  const [inputValue, setInputValue] = useState('');

  const handleAdd = () => {
    if (inputValue.trim() && !values.includes(inputValue.trim())) {
      onChange([...values, inputValue.trim()]);
      setInputValue('');
    }
  };

  const handleRemove = (index: number) => {
    onChange(values.filter((_, i) => i !== index));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="space-y-2">
      {!readOnly && (
        <div className="flex space-x-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            className={hasError ? 'border-red-300' : ''}
          />
          <Button
            type="button"
            size="sm"
            onClick={handleAdd}
            disabled={!inputValue.trim()}
          >
            Add
          </Button>
        </div>
      )}
      
      {values.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {values.map((value, index) => (
            <div
              key={index}
              className="flex items-center space-x-1 px-2 py-1 bg-gray-100 rounded text-sm"
            >
              <span>{value}</span>
              {!readOnly && (
                <button
                  type="button"
                  onClick={() => handleRemove(index)}
                  className="text-red-500 hover:text-red-700 text-xs"
                >
                  ×
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}