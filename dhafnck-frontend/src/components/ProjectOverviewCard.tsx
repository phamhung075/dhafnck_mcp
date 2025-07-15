import React from 'react';
import type { Project } from '../types/application';
import { ProjectHealthStatus, ProjectStatistics, ProjectIssue } from './ProjectDashboard';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

interface ProjectOverviewCardProps {
  project: Project;
  healthStatus: ProjectHealthStatus;
  statistics: ProjectStatistics;
  onSelect: () => void;
  onEdit: () => void;
  onRunHealthCheck: () => Promise<void>;
  onViewDetails: () => void;
  isSelected: boolean;
}

export function ProjectOverviewCard({
  project,
  healthStatus,
  statistics,
  onSelect,
  onEdit,
  onRunHealthCheck,
  onViewDetails,
  isSelected
}: ProjectOverviewCardProps) {
  const healthColor = healthStatus.overall_score >= 80 ? 'border-green-500' :
                     healthStatus.overall_score >= 60 ? 'border-yellow-500' :
                     'border-red-500';

  const trendIcon = healthStatus.health_trend === 'improving' ? '📈' :
                   healthStatus.health_trend === 'stable' ? '➡️' : '📉';

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSeverityColor = (severity: ProjectIssue['severity']) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const completionPercentage = statistics.total_tasks > 0 
    ? Math.round((statistics.completed_tasks / statistics.total_tasks) * 100)
    : 0;

  return (
    <Card 
      className={`border-2 rounded-lg p-4 cursor-pointer transition-all hover:shadow-lg ${
        isSelected ? 'border-blue-500 bg-blue-50 shadow-md' : `${healthColor} bg-white hover:border-gray-300`
      }`}
      onClick={onSelect}
    >
      {/* Header Section */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold truncate">{project.name}</h3>
          <p className="text-sm text-gray-600 line-clamp-2">{project.description || 'No description available'}</p>
        </div>
        <div className="flex items-center gap-2 ml-3">
          <span className="text-lg">{trendIcon}</span>
          <div className="text-right">
            <div className={`text-xl font-bold ${getHealthScoreColor(healthStatus.overall_score)}`}>
              {healthStatus.overall_score}%
            </div>
            <div className="text-xs text-gray-500">Health Score</div>
          </div>
        </div>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="text-lg font-semibold">
            {statistics.completed_tasks}/{statistics.total_tasks}
          </div>
          <div className="text-xs text-gray-600">Tasks Complete</div>
          <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
            <div 
              className="bg-blue-600 h-1 rounded-full transition-all" 
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="text-lg font-semibold">{statistics.active_branches}</div>
          <div className="text-xs text-gray-600">Active Branches</div>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="text-lg font-semibold">{statistics.assigned_agents}</div>
          <div className="text-xs text-gray-600">Agents</div>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className={`text-lg font-semibold ${healthStatus.blocker_count > 0 ? 'text-red-600' : 'text-green-600'}`}>
            {healthStatus.blocker_count}
          </div>
          <div className="text-xs text-gray-600">Blockers</div>
        </div>
      </div>

      {/* Health Metrics */}
      <div className="mb-3 space-y-2">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600">Task Completion Rate</span>
          <span className="font-medium">{healthStatus.task_completion_rate}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-1">
          <div 
            className="bg-green-500 h-1 rounded-full transition-all" 
            style={{ width: `${healthStatus.task_completion_rate}%` }}
          />
        </div>
        
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600">Agent Utilization</span>
          <span className="font-medium">{healthStatus.agent_utilization}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-1">
          <div 
            className="bg-purple-500 h-1 rounded-full transition-all" 
            style={{ width: `${healthStatus.agent_utilization}%` }}
          />
        </div>
      </div>

      {/* Issues Section */}
      {healthStatus.issues.length > 0 && (
        <div className="mb-3">
          <div className="text-xs font-medium text-gray-700 mb-1">Active Issues:</div>
          <div className="space-y-1">
            {healthStatus.issues.slice(0, 2).map((issue, idx) => (
              <div 
                key={idx} 
                className={`text-xs px-2 py-1 rounded border ${getSeverityColor(issue.severity)}`}
                title={issue.description}
              >
                <div className="flex items-center justify-between">
                  <span className="truncate flex-1">{issue.title}</span>
                  <Badge variant="outline" className="ml-1 text-xs">
                    {issue.severity}
                  </Badge>
                </div>
              </div>
            ))}
            {healthStatus.issues.length > 2 && (
              <div className="text-xs text-gray-500 text-center">
                +{healthStatus.issues.length - 2} more issues
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer Section */}
      <div className="space-y-2">
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>Last activity: {new Date(healthStatus.last_activity).toLocaleDateString()}</span>
          <span>Created: {statistics.days_since_creation} days ago</span>
        </div>
        
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>Est. completion: {statistics.estimated_completion}</span>
          <div className="flex items-center gap-1">
            <div className={`w-2 h-2 rounded-full ${
              healthStatus.overall_score >= 80 ? 'bg-green-500' :
              healthStatus.overall_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
            }`} />
            <span>{healthStatus.health_trend}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-2 border-t">
          <div className="flex gap-1">
            <Button
              size="sm"
              variant="outline"
              onClick={(e) => {
                e.stopPropagation();
                onRunHealthCheck();
              }}
              className="text-xs px-2 py-1 h-auto"
            >
              🔍 Check Health
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={(e) => {
                e.stopPropagation();
                onEdit();
              }}
              className="text-xs px-2 py-1 h-auto"
            >
              ✏️ Edit
            </Button>
          </div>
          <Button
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onViewDetails();
            }}
            className="text-xs px-3 py-1 h-auto"
          >
            View Details →
          </Button>
        </div>
      </div>
    </Card>
  );
}