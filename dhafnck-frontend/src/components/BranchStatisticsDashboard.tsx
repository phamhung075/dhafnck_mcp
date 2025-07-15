/**
 * Branch Statistics Dashboard Component
 * Provides comprehensive analytics and metrics for git branches
 */

import React, { useState, useEffect } from 'react';
import { GitBranch, DetailedBranchStatistics, DataPoint, AgentPerformance, HealthFactor } from './GitBranchManager';

interface BranchStatisticsDashboardProps {
  branch: GitBranch;
  statistics: DetailedBranchStatistics;
  onRefreshStatistics: () => Promise<void>;
  onClose?: () => void;
}

interface ProgressChartProps {
  data: DataPoint[];
  title: string;
  color: string;
}

function ProgressChart({ data, title, color }: ProgressChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-32 flex items-center justify-center text-gray-500 text-sm">
        No data available
      </div>
    );
  }

  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = Math.min(...data.map(d => d.value));
  const range = maxValue - minValue || 1;

  return (
    <div className="space-y-2">
      <h5 className="text-sm font-medium text-gray-700">{title}</h5>
      <div className="h-24 flex items-end justify-between gap-1">
        {data.slice(-7).map((point, index) => {
          const height = ((point.value - minValue) / range) * 80 + 10;
          return (
            <div key={index} className="flex flex-col items-center flex-1">
              <div
                className={`w-full ${color} rounded-t transition-all hover:opacity-80`}
                style={{ height: `${height}px` }}
                title={`${new Date(point.date).toLocaleDateString()}: ${point.value}%`}
              />
              <div className="text-xs text-gray-500 mt-1 text-center">
                {new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </div>
            </div>
          );
        })}
      </div>
      <div className="text-xs text-gray-500 text-center">
        Last 7 data points
      </div>
    </div>
  );
}

interface HealthFactorProps {
  factor: HealthFactor;
}

function HealthFactorItem({ factor }: HealthFactorProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBarColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <div className="font-medium text-sm">{factor.name}</div>
        <div className={`font-semibold ${getScoreColor(factor.score)}`}>
          {factor.score}%
        </div>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${getScoreBarColor(factor.score)}`}
          style={{ width: `${factor.score}%` }}
        />
      </div>
      <div className="text-xs text-gray-600">{factor.description}</div>
      <div className="text-xs text-gray-500">Weight: {factor.weight}%</div>
    </div>
  );
}

export function BranchStatisticsDashboard({
  branch,
  statistics,
  onRefreshStatistics,
  onClose
}: BranchStatisticsDashboardProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'tasks' | 'agents' | 'health' | 'timeline'>('overview');
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await onRefreshStatistics();
    } catch (error) {
      console.error('Failed to refresh statistics:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'tasks', label: 'Tasks', icon: '📋' },
    { id: 'agents', label: 'Agents', icon: '🤖' },
    { id: 'health', label: 'Health', icon: '💚' },
    { id: 'timeline', label: 'Timeline', icon: '📅' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-lg font-semibold">
              Statistics for {branch.git_branch_name}
            </h3>
            <p className="text-gray-600 text-sm">{branch.git_branch_description}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {refreshing ? '🔄' : '↻'} Refresh
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                ✕ Close
              </button>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 mb-6 border-b">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg ${
                activeTab === tab.id
                  ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-500'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <span className="mr-1">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Overview Cards */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-white p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {statistics.basic.progress_percentage}%
                  </div>
                  <div className="text-sm text-gray-600">Progress</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Overall completion rate
                  </div>
                </div>
                <div className="bg-white p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {statistics.basic.completed_tasks}/{statistics.basic.total_tasks}
                  </div>
                  <div className="text-sm text-gray-600">Tasks</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Completed vs Total
                  </div>
                </div>
                <div className="bg-white p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {statistics.basic.assigned_agents.length}
                  </div>
                  <div className="text-sm text-gray-600">Agents</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Currently assigned
                  </div>
                </div>
                <div className="bg-white p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {statistics.health.score}%
                  </div>
                  <div className="text-sm text-gray-600">Health Score</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Overall branch health
                  </div>
                </div>
              </div>

              {/* Progress Chart */}
              {statistics.tasks.completion_trend && (
                <div className="bg-white p-4 border rounded-lg">
                  <ProgressChart
                    data={statistics.tasks.completion_trend}
                    title="Completion Trend"
                    color="bg-blue-500"
                  />
                </div>
              )}
            </div>
          )}

          {activeTab === 'tasks' && (
            <div className="space-y-6">
              {/* Task Breakdown */}
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-white p-4 border rounded-lg">
                  <h4 className="font-medium mb-3">Tasks by Status</h4>
                  <div className="space-y-2">
                    {Object.entries(statistics.tasks.by_status).map(([status, count]) => (
                      <div key={status} className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full ${
                            status === 'done' ? 'bg-green-500' :
                            status === 'in_progress' ? 'bg-blue-500' :
                            status === 'blocked' ? 'bg-red-500' :
                            'bg-gray-400'
                          }`} />
                          <span className="capitalize text-sm">{status.replace('_', ' ')}</span>
                        </div>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white p-4 border rounded-lg">
                  <h4 className="font-medium mb-3">Tasks by Priority</h4>
                  <div className="space-y-2">
                    {Object.entries(statistics.tasks.by_priority).map(([priority, count]) => (
                      <div key={priority} className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full ${
                            priority === 'critical' ? 'bg-red-600' :
                            priority === 'high' ? 'bg-orange-500' :
                            priority === 'medium' ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`} />
                          <span className="capitalize text-sm">{priority}</span>
                        </div>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Task Assignment */}
              {Object.keys(statistics.tasks.by_assignee).length > 0 && (
                <div className="bg-white p-4 border rounded-lg">
                  <h4 className="font-medium mb-3">Tasks by Assignee</h4>
                  <div className="space-y-2">
                    {Object.entries(statistics.tasks.by_assignee).map(([assignee, count]) => (
                      <div key={assignee} className="flex justify-between items-center">
                        <span className="text-sm">{assignee}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'agents' && (
            <div className="space-y-6">
              {/* Agent Performance */}
              <div className="bg-white p-4 border rounded-lg">
                <h4 className="font-medium mb-3">Agent Performance</h4>
                <div className="space-y-4">
                  {Object.entries(statistics.agents.performance).map(([agentId, performance]) => (
                    <div key={agentId} className="border rounded p-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium">{agentId}</div>
                          <div className="text-sm text-gray-600">
                            Utilization: {statistics.agents.utilization[agentId] || 0}%
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium">
                            {performance.completed_tasks} tasks completed
                          </div>
                          <div className="text-xs text-gray-500">
                            {performance.success_rate}% success rate
                          </div>
                          <div className="text-xs text-gray-500">
                            Avg: {Math.round(performance.average_completion_time)}h
                          </div>
                        </div>
                      </div>
                      
                      {/* Performance Bar */}
                      <div className="mt-2">
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                          <span>Performance</span>
                          <span>{performance.success_rate}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              performance.success_rate >= 90 ? 'bg-green-500' :
                              performance.success_rate >= 70 ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${performance.success_rate}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Agent Utilization Summary */}
              <div className="bg-white p-4 border rounded-lg">
                <h4 className="font-medium mb-3">Utilization Summary</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">Average Utilization</div>
                    <div className="text-lg font-semibold">
                      {Object.values(statistics.agents.utilization).length > 0
                        ? Math.round(Object.values(statistics.agents.utilization).reduce((a, b) => a + b, 0) / Object.values(statistics.agents.utilization).length)
                        : 0}%
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600">Total Completed Tasks</div>
                    <div className="text-lg font-semibold">
                      {Object.values(statistics.agents.performance).reduce((sum, perf) => sum + perf.completed_tasks, 0)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'health' && (
            <div className="space-y-6">
              {/* Overall Health Score */}
              <div className="bg-white p-4 border rounded-lg text-center">
                <div className={`text-4xl font-bold mb-2 ${
                  statistics.health.score >= 80 ? 'text-green-600' :
                  statistics.health.score >= 60 ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {statistics.health.score}%
                </div>
                <div className="text-gray-600">Overall Health Score</div>
                <div className={`text-sm mt-2 ${
                  statistics.health.score >= 80 ? 'text-green-600' :
                  statistics.health.score >= 60 ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {statistics.health.score >= 80 ? 'Excellent' :
                   statistics.health.score >= 60 ? 'Good' :
                   'Needs Attention'}
                </div>
              </div>

              {/* Health Factors */}
              <div className="bg-white p-4 border rounded-lg">
                <h4 className="font-medium mb-4">Health Factors</h4>
                <div className="space-y-4">
                  {statistics.health.factors.map((factor, index) => (
                    <HealthFactorItem key={index} factor={factor} />
                  ))}
                </div>
              </div>

              {/* Recommendations */}
              {statistics.health.recommendations.length > 0 && (
                <div className="bg-white p-4 border rounded-lg">
                  <h4 className="font-medium mb-3">Recommendations</h4>
                  <div className="space-y-3">
                    {statistics.health.recommendations.map((recommendation, idx) => (
                      <div key={idx} className="p-3 bg-blue-50 border-l-4 border-blue-500 rounded">
                        <div className="text-sm">{recommendation}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'timeline' && (
            <div className="space-y-6">
              {/* Timeline Information */}
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-white p-4 border rounded-lg">
                  <h4 className="font-medium mb-3">Branch Timeline</h4>
                  <div className="space-y-3">
                    <div>
                      <div className="text-sm text-gray-600">Created</div>
                      <div className="font-medium">
                        {new Date(statistics.timeline.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">First Task</div>
                      <div className="font-medium">
                        {statistics.timeline.first_task_at 
                          ? new Date(statistics.timeline.first_task_at).toLocaleDateString()
                          : 'No tasks yet'
                        }
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Last Activity</div>
                      <div className="font-medium">
                        {new Date(statistics.timeline.last_activity_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-4 border rounded-lg">
                  <h4 className="font-medium mb-3">Projections</h4>
                  <div className="space-y-3">
                    <div>
                      <div className="text-sm text-gray-600">Estimated Completion</div>
                      <div className="font-medium">
                        {statistics.timeline.estimated_completion 
                          ? new Date(statistics.timeline.estimated_completion).toLocaleDateString()
                          : 'Not available'
                        }
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Days Active</div>
                      <div className="font-medium">
                        {Math.ceil((new Date(statistics.timeline.last_activity_at).getTime() - new Date(statistics.timeline.created_at).getTime()) / (1000 * 60 * 60 * 24))}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Progress Rate</div>
                      <div className="font-medium">
                        {statistics.basic.total_tasks > 0 
                          ? Math.round((statistics.basic.completed_tasks / statistics.basic.total_tasks) * 100)
                          : 0
                        }% completion
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Activity Summary */}
              <div className="bg-white p-4 border rounded-lg">
                <h4 className="font-medium mb-3">Activity Summary</h4>
                <div className="text-sm text-gray-600 space-y-2">
                  <p>
                    This branch has been active for{' '}
                    <span className="font-medium">
                      {Math.ceil((new Date(statistics.timeline.last_activity_at).getTime() - new Date(statistics.timeline.created_at).getTime()) / (1000 * 60 * 60 * 24))}
                    </span>{' '}
                    days with{' '}
                    <span className="font-medium">{statistics.basic.total_tasks}</span>{' '}
                    total tasks.
                  </p>
                  <p>
                    Current completion rate is{' '}
                    <span className="font-medium">{statistics.basic.progress_percentage}%</span>{' '}
                    with{' '}
                    <span className="font-medium">{statistics.basic.assigned_agents.length}</span>{' '}
                    assigned agents.
                  </p>
                  {statistics.timeline.estimated_completion && (
                    <p>
                      Estimated completion date is{' '}
                      <span className="font-medium">
                        {new Date(statistics.timeline.estimated_completion).toLocaleDateString()}
                      </span>.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default BranchStatisticsDashboard;