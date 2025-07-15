import { Project } from '../types/application';
import { AnalyticsInsight, CrossProjectAnalytics as CrossProjectAnalyticsType, MetricTrend } from './ProjectDashboard';
import { Sparkline, TrendChart } from './TrendChart';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card } from './ui/card';

interface CrossProjectAnalyticsProps {
  projects: Project[];
  analytics: CrossProjectAnalyticsType;
  onRefreshAnalytics: () => Promise<void>;
  timeRange: '7d' | '30d' | '90d' | '1y';
  onTimeRangeChange: (range: string) => void;
}

function CrossProjectAnalytics({
  projects,
  analytics,
  onRefreshAnalytics,
  timeRange,
  onTimeRangeChange
}: CrossProjectAnalyticsProps) {
  const getInsightIcon = (type: AnalyticsInsight['type']) => {
    switch (type) {
      case 'recommendation': return '💡';
      case 'warning': return '⚠️';
      case 'success': return '✅';
      default: return 'ℹ️';
    }
  };

  const getInsightBgColor = (type: AnalyticsInsight['type']) => {
    switch (type) {
      case 'recommendation': return 'border-blue-500 bg-blue-50';
      case 'warning': return 'border-yellow-500 bg-yellow-50';
      case 'success': return 'border-green-500 bg-green-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  const calculateTrend = (data: MetricTrend[]) => {
    if (data.length < 2) return 0;
    const recent = data.slice(-7);
    const older = data.slice(-14, -7);
    
    const recentAvg = recent.reduce((sum, item) => sum + item.value, 0) / recent.length;
    const olderAvg = older.reduce((sum, item) => sum + item.value, 0) / older.length;
    
    return ((recentAvg - olderAvg) / olderAvg) * 100;
  };

  const formatTrend = (trend: number) => {
    const isPositive = trend > 0;
    const icon = isPositive ? '📈' : trend < 0 ? '📉' : '➡️';
    const color = isPositive ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-600';
    
    return (
      <span className={`flex items-center gap-1 text-sm ${color}`}>
        <span>{icon}</span>
        <span>{Math.abs(trend).toFixed(1)}%</span>
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Cross-Project Analytics</h3>
        <div className="flex gap-2">
          <select
            value={timeRange}
            onChange={(e) => onTimeRangeChange(e.target.value)}
            className="px-3 py-1 border rounded text-sm"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <Button
            size="sm"
            onClick={onRefreshAnalytics}
            className="text-sm"
          >
            🔄 Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {analytics.summary.total_projects}
              </div>
              <div className="text-sm text-gray-600">Total Projects</div>
              <div className="text-xs text-green-600 mt-1">
                {analytics.summary.active_projects} active
              </div>
            </div>
            <div className="text-3xl">📊</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-green-600">
                {Math.round(analytics.summary.average_health_score)}%
              </div>
              <div className="text-sm text-gray-600">Avg Health Score</div>
              <div className="mt-1">
                {formatTrend(calculateTrend(analytics.trends.health_score_trend))}
              </div>
            </div>
            <div className="text-3xl">💚</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {analytics.summary.completed_tasks}/{analytics.summary.total_tasks}
              </div>
              <div className="text-sm text-gray-600">Task Completion</div>
              <div className="mt-1">
                {formatTrend(calculateTrend(analytics.trends.task_completion_rate))}
              </div>
            </div>
            <div className="text-3xl">✅</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-orange-600">
                {analytics.summary.total_tasks > 0 
                  ? Math.round((analytics.summary.completed_tasks / analytics.summary.total_tasks) * 100)
                  : 0}%
              </div>
              <div className="text-sm text-gray-600">Completion Rate</div>
              <div className="mt-1">
                <Sparkline 
                  data={analytics.trends.task_completion_rate} 
                  color="#F97316"
                />
              </div>
            </div>
            <div className="text-3xl">🎯</div>
          </div>
        </Card>
      </div>

      {/* Trend Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium">Project Creation Trend</h4>
            {formatTrend(calculateTrend(analytics.trends.project_creation_rate))}
          </div>
          <div className="h-48">
            <TrendChart 
              data={analytics.trends.project_creation_rate}
              color="#3B82F6"
              type="area"
            />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium">Health Score Trend</h4>
            {formatTrend(calculateTrend(analytics.trends.health_score_trend))}
          </div>
          <div className="h-48">
            <TrendChart 
              data={analytics.trends.health_score_trend}
              color="#10B981"
              type="line"
            />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium">Task Completion Rate</h4>
            {formatTrend(calculateTrend(analytics.trends.task_completion_rate))}
          </div>
          <div className="h-48">
            <TrendChart 
              data={analytics.trends.task_completion_rate}
              color="#8B5CF6"
              type="bar"
            />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium">Agent Utilization</h4>
            {formatTrend(calculateTrend(analytics.trends.agent_utilization))}
          </div>
          <div className="h-48">
            <TrendChart 
              data={analytics.trends.agent_utilization}
              color="#F59E0B"
              type="area"
            />
          </div>
        </Card>
      </div>

      {/* Project Performance Comparison */}
      <Card className="p-4">
        <h4 className="font-medium mb-3">Project Performance Comparison</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 px-2">Project</th>
                <th className="text-left py-2 px-2">Health Score</th>
                <th className="text-left py-2 px-2">Task Completion</th>
                <th className="text-left py-2 px-2">Agent Utilization</th>
                <th className="text-left py-2 px-2">Days Active</th>
                <th className="text-left py-2 px-2">Performance</th>
              </tr>
            </thead>
            <tbody>
              {analytics.comparisons
                .sort((a, b) => b.health_score - a.health_score)
                .map(comparison => {
                  const overallScore = (
                    comparison.health_score * 0.4 +
                    comparison.task_completion_rate * 0.4 +
                    comparison.agent_utilization * 0.2
                  );
                  
                  const performanceLevel = 
                    overallScore >= 80 ? { label: 'Excellent', color: 'bg-green-100 text-green-800' } :
                    overallScore >= 60 ? { label: 'Good', color: 'bg-blue-100 text-blue-800' } :
                    overallScore >= 40 ? { label: 'Fair', color: 'bg-yellow-100 text-yellow-800' } :
                    { label: 'Needs Attention', color: 'bg-red-100 text-red-800' };

                  return (
                    <tr key={comparison.project_id} className="border-b hover:bg-gray-50">
                      <td className="py-2 px-2 font-medium">{comparison.project_name}</td>
                      <td className="py-2 px-2">
                        <div className="flex items-center gap-2">
                          <div className="w-12 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all" 
                              style={{ width: `${comparison.health_score}%` }}
                            />
                          </div>
                          <span className="text-xs">{comparison.health_score}%</span>
                        </div>
                      </td>
                      <td className="py-2 px-2">
                        <div className="flex items-center gap-2">
                          <div className="w-12 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-green-600 h-2 rounded-full transition-all" 
                              style={{ width: `${comparison.task_completion_rate}%` }}
                            />
                          </div>
                          <span className="text-xs">{comparison.task_completion_rate}%</span>
                        </div>
                      </td>
                      <td className="py-2 px-2">
                        <div className="flex items-center gap-2">
                          <div className="w-12 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-purple-600 h-2 rounded-full transition-all" 
                              style={{ width: `${comparison.agent_utilization}%` }}
                            />
                          </div>
                          <span className="text-xs">{comparison.agent_utilization}%</span>
                        </div>
                      </td>
                      <td className="py-2 px-2">{comparison.days_active}</td>
                      <td className="py-2 px-2">
                        <Badge className={`text-xs ${performanceLevel.color}`}>
                          {performanceLevel.label}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Analytics Insights */}
      {analytics.insights.length > 0 && (
        <Card className="p-4">
          <h4 className="font-medium mb-3">Analytics Insights</h4>
          <div className="space-y-3">
            {analytics.insights.map((insight, idx) => (
              <div 
                key={idx} 
                className={`p-4 rounded-lg border-l-4 ${getInsightBgColor(insight.type)}`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-xl mt-1">{getInsightIcon(insight.type)}</span>
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-medium">{insight.title}</div>
                        <div className="text-sm text-gray-600 mt-1">{insight.description}</div>
                      </div>
                      {insight.action_required && (
                        <Badge variant="destructive" className="ml-2">
                          Action Required
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Quick Actions */}
      <Card className="p-4">
        <h4 className="font-medium mb-3">Quick Actions</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button variant="outline" className="flex items-center gap-2">
            <span>📊</span>
            Export Analytics Report
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <span>⚖️</span>
            Rebalance All Agents
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <span>🔍</span>
            Run Health Checks
          </Button>
        </div>
      </Card>
    </div>
  );
}

export { CrossProjectAnalytics };
export default CrossProjectAnalytics;