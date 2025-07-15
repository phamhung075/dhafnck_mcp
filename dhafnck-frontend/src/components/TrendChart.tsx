import React from 'react';
import { MetricTrend } from './ProjectDashboard';

interface TrendChartProps {
  data: MetricTrend[];
  height?: number;
  color?: string;
  showGrid?: boolean;
  showLabels?: boolean;
  type?: 'line' | 'area' | 'bar';
}

export function TrendChart({ 
  data, 
  height = 200, 
  color = '#3B82F6', 
  showGrid = true,
  showLabels = true,
  type = 'line'
}: TrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div 
        className="flex items-center justify-center text-gray-500 bg-gray-50 rounded"
        style={{ height }}
      >
        No data available
      </div>
    );
  }

  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = Math.min(...data.map(d => d.value));
  const valueRange = maxValue - minValue || 1;

  const width = 100; // Percentage based
  const chartHeight = height - 40; // Leave space for labels
  const chartWidth = width - 10; // Leave space for padding

  // Generate SVG path for line chart
  const generatePath = () => {
    const points = data.map((point, index) => {
      const x = (index / (data.length - 1)) * chartWidth;
      const y = chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
      return `${x},${y}`;
    }).join(' L');
    
    return `M${points}`;
  };

  // Generate area path
  const generateAreaPath = () => {
    const points = data.map((point, index) => {
      const x = (index / (data.length - 1)) * chartWidth;
      const y = chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
      return `${x},${y}`;
    });
    
    const firstPoint = points[0];
    const lastPoint = points[points.length - 1];
    const [lastX] = lastPoint.split(',');
    const [firstX] = firstPoint.split(',');
    
    return `M${firstX},${chartHeight} L${points.join(' L')} L${lastX},${chartHeight} Z`;
  };

  // Generate grid lines
  const generateGridLines = () => {
    const lines = [];
    const numLines = 5;
    
    for (let i = 0; i <= numLines; i++) {
      const y = (i / numLines) * chartHeight;
      lines.push(
        <line
          key={`grid-${i}`}
          x1="0"
          y1={y}
          x2={chartWidth}
          y2={y}
          stroke="#E5E7EB"
          strokeWidth="1"
          strokeDasharray="2,2"
        />
      );
    }
    
    return lines;
  };

  // Format date for labels
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="w-full">
      <div className="relative" style={{ height }}>
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${width} ${height}`}
          className="overflow-visible"
        >
          {/* Grid lines */}
          {showGrid && (
            <g transform={`translate(5, 10)`}>
              {generateGridLines()}
            </g>
          )}
          
          {/* Chart content */}
          <g transform={`translate(5, 10)`}>
            {type === 'area' && (
              <path
                d={generateAreaPath()}
                fill={color}
                fillOpacity="0.2"
                stroke="none"
              />
            )}
            
            {type === 'bar' && data.map((point, index) => {
              const x = (index / (data.length - 1)) * chartWidth;
              const barHeight = ((point.value - minValue) / valueRange) * chartHeight;
              const y = chartHeight - barHeight;
              const barWidth = Math.max(chartWidth / data.length * 0.6, 2);
              
              return (
                <rect
                  key={index}
                  x={x - barWidth / 2}
                  y={y}
                  width={barWidth}
                  height={barHeight}
                  fill={color}
                  fillOpacity="0.8"
                />
              );
            })}
            
            {(type === 'line' || type === 'area') && (
              <path
                d={generatePath()}
                fill="none"
                stroke={color}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}
            
            {/* Data points */}
            {(type === 'line' || type === 'area') && data.map((point, index) => {
              const x = (index / (data.length - 1)) * chartWidth;
              const y = chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
              
              return (
                <circle
                  key={index}
                  cx={x}
                  cy={y}
                  r="3"
                  fill={color}
                  stroke="white"
                  strokeWidth="2"
                  className="hover:r-4 transition-all cursor-pointer"
                >
                  <title>{`${formatDate(point.date)}: ${point.value}`}</title>
                </circle>
              );
            })}
          </g>
          
          {/* Y-axis labels */}
          {showLabels && (
            <g>
              {[0, 0.25, 0.5, 0.75, 1].map((ratio, index) => {
                const value = minValue + (valueRange * ratio);
                const y = 10 + chartHeight - (ratio * chartHeight);
                
                return (
                  <text
                    key={index}
                    x="2"
                    y={y}
                    fontSize="10"
                    fill="#6B7280"
                    textAnchor="start"
                    dominantBaseline="middle"
                  >
                    {Math.round(value)}
                  </text>
                );
              })}
            </g>
          )}
          
          {/* X-axis labels */}
          {showLabels && (
            <g>
              {data.filter((_, index) => index % Math.ceil(data.length / 5) === 0).map((point, index, filteredData) => {
                const originalIndex = data.indexOf(point);
                const x = 5 + (originalIndex / (data.length - 1)) * chartWidth;
                const y = height - 5;
                
                return (
                  <text
                    key={originalIndex}
                    x={x}
                    y={y}
                    fontSize="10"
                    fill="#6B7280"
                    textAnchor="middle"
                  >
                    {formatDate(point.date)}
                  </text>
                );
              })}
            </g>
          )}
        </svg>
      </div>
      
      {/* Legend */}
      <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
        <span>
          Min: {Math.round(minValue)}
        </span>
        <span>
          Latest: {data[data.length - 1]?.value ? Math.round(data[data.length - 1].value) : 'N/A'}
        </span>
        <span>
          Max: {Math.round(maxValue)}
        </span>
      </div>
    </div>
  );
}

// Simple sparkline component for inline use
export function Sparkline({ 
  data, 
  width = 60, 
  height = 20, 
  color = '#3B82F6' 
}: {
  data: MetricTrend[];
  width?: number;
  height?: number;
  color?: string;
}) {
  if (!data || data.length === 0) {
    return <div style={{ width, height }} className="bg-gray-100 rounded" />;
  }

  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = Math.min(...data.map(d => d.value));
  const valueRange = maxValue - minValue || 1;

  const points = data.map((point, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((point.value - minValue) / valueRange) * height;
    return `${x},${y}`;
  }).join(' L');

  return (
    <svg width={width} height={height} className="inline-block">
      <path
        d={`M${points}`}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}