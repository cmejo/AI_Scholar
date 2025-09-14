/**
 * Performance Charts Component - Trend analysis and performance visualization
 * Implements part of task 2.3: Create PerformanceCharts component with trend analysis
 */

import React, { useState, useMemo } from 'react';
import { 
  Activity, 
  Cpu, 
  HardDrive, 
  Zap, 
  Clock, 
  TrendingUp, 
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  LineChart,
  Monitor
} from 'lucide-react';
import { PerformanceMetrics, TrendAnalysis } from '../../../types/ui';

interface PerformanceChartsProps {
  performance: PerformanceMetrics;
  trends: TrendAnalysis[];
  loading?: boolean;
  timeRange: string;
}

interface PerformanceIndicatorProps {
  title: string;
  value: number;
  unit: string;
  icon: React.ReactNode;
  threshold: { warning: number; critical: number };
  trend?: { direction: 'up' | 'down' | 'stable'; value: number };
  format?: (value: number) => string;
}

interface MetricHistory {
  timestamp: Date;
  value: number;
}

const PerformanceIndicator: React.FC<PerformanceIndicatorProps> = ({
  title,
  value,
  unit,
  icon,
  threshold,
  trend,
  format
}) => {
  const getStatusColor = () => {
    if (value >= threshold.critical) return 'red';
    if (value >= threshold.warning) return 'yellow';
    return 'green';
  };

  const getStatusIcon = () => {
    const status = getStatusColor();
    switch (status) {
      case 'red':
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case 'yellow':
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      default:
        return <CheckCircle className="w-4 h-4 text-green-400" />;
    }
  };

  const colorClasses = {
    red: 'bg-red-500/20 border-red-500/30',
    yellow: 'bg-yellow-500/20 border-yellow-500/30',
    green: 'bg-green-500/20 border-green-500/30'
  };

  const status = getStatusColor();
  const formattedValue = format ? format(value) : `${value.toFixed(1)}${unit}`;

  return (
    <div className={`bg-gray-800 rounded-lg p-4 border ${colorClasses[status]} transition-all duration-200`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          {icon}
          <span className="text-sm font-medium text-gray-300">{title}</span>
        </div>
        {getStatusIcon()}
      </div>
      
      <div className="mb-2">
        <span className="text-2xl font-bold text-white">{formattedValue}</span>
      </div>
      
      {trend && (
        <div className="flex items-center space-x-2">
          {trend.direction === 'up' ? (
            <TrendingUp className="w-3 h-3 text-red-400" />
          ) : trend.direction === 'down' ? (
            <TrendingDown className="w-3 h-3 text-green-400" />
          ) : (
            <Activity className="w-3 h-3 text-gray-400" />
          )}
          <span className={`text-xs ${
            trend.direction === 'up' ? 'text-red-400' : 
            trend.direction === 'down' ? 'text-green-400' : 'text-gray-400'
          }`}>
            {Math.abs(trend.value).toFixed(1)}%
          </span>
        </div>
      )}
      
      {/* Progress bar */}
      <div className="mt-3 w-full bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${
            status === 'red' ? 'bg-red-500' : 
            status === 'yellow' ? 'bg-yellow-500' : 'bg-green-500'
          }`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  );
};

export const PerformanceCharts: React.FC<PerformanceChartsProps> = ({
  performance,
  trends,
  loading = false,
  timeRange
}) => {
  const [selectedMetric, setSelectedMetric] = useState<'responseTime' | 'throughput' | 'errorRate' | 'system'>('responseTime');
  const [chartType, setChartType] = useState<'line' | 'bar'>('line');

  // Generate mock historical data for demonstration
  const generateHistoricalData = (baseValue: number, points: number = 24): MetricHistory[] => {
    const data: MetricHistory[] = [];
    const now = new Date();
    
    for (let i = points - 1; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000); // Hourly data
      const variation = (Math.random() - 0.5) * 0.3; // ±15% variation
      const value = Math.max(0, baseValue * (1 + variation));
      data.push({ timestamp, value });
    }
    
    return data;
  };

  // Historical data for charts
  const historicalData = useMemo(() => {
    if (loading) return null;
    
    return {
      responseTime: generateHistoricalData(performance.responseTime),
      throughput: generateHistoricalData(performance.throughput),
      errorRate: generateHistoricalData(performance.errorRate * 100),
      cpuUsage: generateHistoricalData(performance.cpuUsage),
      memoryUsage: generateHistoricalData(performance.memoryUsage),
      diskUsage: generateHistoricalData(performance.diskUsage || 0)
    };
  }, [performance, loading]);

  // Simple line chart component
  const SimpleLineChart: React.FC<{ 
    data: MetricHistory[]; 
    color: string; 
    label: string;
    unit: string;
  }> = ({ data, color, label, unit }) => {
    if (!data || data.length === 0) {
      return (
        <div className="flex items-center justify-center h-48 text-gray-500">
          <div className="text-center">
            <LineChart className="w-8 h-8 mx-auto mb-2 text-gray-600" />
            <p className="text-sm">No data available</p>
          </div>
        </div>
      );
    }

    const maxValue = Math.max(...data.map(d => d.value));
    const minValue = Math.min(...data.map(d => d.value));
    const range = maxValue - minValue || 1;

    return (
      <div className="h-48 p-4">
        <div className="flex items-end justify-between h-full">
          {data.map((point, index) => {
            const height = ((point.value - minValue) / range) * 100;
            const isLast = index === data.length - 1;
            
            return (
              <div key={index} className="flex-1 flex flex-col items-center relative group">
                <div className="flex-1 flex items-end">
                  <div
                    className={`w-1 bg-${color}-500 rounded-t transition-all duration-300`}
                    style={{ height: `${Math.max(height, 2)}%` }}
                  />
                  {index < data.length - 1 && (
                    <svg
                      className="absolute top-0 left-0 w-full h-full pointer-events-none"
                      style={{ zIndex: -1 }}
                    >
                      <line
                        x1="50%"
                        y1={`${100 - height}%`}
                        x2="150%"
                        y2={`${100 - ((data[index + 1].value - minValue) / range) * 100}%`}
                        stroke={color === 'blue' ? '#3B82F6' : color === 'green' ? '#10B981' : '#F59E0B'}
                        strokeWidth="2"
                      />
                    </svg>
                  )}
                </div>
                
                {/* Tooltip */}
                <div className="absolute bottom-full mb-2 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
                  {point.value.toFixed(1)}{unit}
                  <br />
                  {point.timestamp.toLocaleTimeString()}
                </div>
                
                {/* Time label for every 4th point */}
                {index % 4 === 0 && (
                  <div className="text-xs text-gray-500 mt-1">
                    {point.timestamp.getHours()}:00
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-700 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        <div>
          <h2 className="text-xl font-semibold text-white">Performance Metrics</h2>
          <p className="text-sm text-gray-400">System performance analysis for {timeRange}</p>
        </div>
        
        {/* Chart controls */}
        <div className="flex items-center space-x-2">
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value as any)}
            className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm text-white"
          >
            <option value="responseTime">Response Time</option>
            <option value="throughput">Throughput</option>
            <option value="errorRate">Error Rate</option>
            <option value="system">System Resources</option>
          </select>
          
          <button
            onClick={() => setChartType(chartType === 'line' ? 'bar' : 'line')}
            className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
          >
            {chartType === 'line' ? <BarChart3 className="w-4 h-4" /> : <LineChart className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Performance Indicators Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <PerformanceIndicator
          title="Response Time"
          value={performance.responseTime}
          unit="ms"
          icon={<Clock className="w-4 h-4 text-blue-400" />}
          threshold={{ warning: 1000, critical: 3000 }}
          format={(value) => `${value.toFixed(0)}ms`}
        />
        
        <PerformanceIndicator
          title="CPU Usage"
          value={performance.cpuUsage}
          unit="%"
          icon={<Cpu className="w-4 h-4 text-green-400" />}
          threshold={{ warning: 70, critical: 90 }}
        />
        
        <PerformanceIndicator
          title="Memory Usage"
          value={performance.memoryUsage}
          unit="%"
          icon={<Activity className="w-4 h-4 text-yellow-400" />}
          threshold={{ warning: 80, critical: 95 }}
        />
        
        <PerformanceIndicator
          title="Disk Usage"
          value={performance.diskUsage || 0}
          unit="%"
          icon={<HardDrive className="w-4 h-4 text-purple-400" />}
          threshold={{ warning: 85, critical: 95 }}
        />
      </div>

      {/* Main Chart */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">
            {selectedMetric === 'responseTime' ? 'Response Time Trend' :
             selectedMetric === 'throughput' ? 'Throughput Trend' :
             selectedMetric === 'errorRate' ? 'Error Rate Trend' :
             'System Resource Usage'}
          </h3>
          <div className="flex items-center space-x-2">
            <Monitor className="w-5 h-5 text-gray-400" />
            <span className="text-sm text-gray-400">Last 24 hours</span>
          </div>
        </div>
        
        {historicalData && (
          <>
            {selectedMetric === 'responseTime' && (
              <SimpleLineChart
                data={historicalData.responseTime}
                color="blue"
                label="Response Time"
                unit="ms"
              />
            )}
            
            {selectedMetric === 'throughput' && (
              <SimpleLineChart
                data={historicalData.throughput}
                color="green"
                label="Throughput"
                unit=" req/s"
              />
            )}
            
            {selectedMetric === 'errorRate' && (
              <SimpleLineChart
                data={historicalData.errorRate}
                color="red"
                label="Error Rate"
                unit="%"
              />
            )}
            
            {selectedMetric === 'system' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-300 mb-2">CPU Usage</h4>
                  <SimpleLineChart
                    data={historicalData.cpuUsage}
                    color="green"
                    label="CPU"
                    unit="%"
                  />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Memory Usage</h4>
                  <SimpleLineChart
                    data={historicalData.memoryUsage}
                    color="yellow"
                    label="Memory"
                    unit="%"
                  />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Disk Usage</h4>
                  <SimpleLineChart
                    data={historicalData.diskUsage}
                    color="purple"
                    label="Disk"
                    unit="%"
                  />
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Performance Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend Analysis */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Trend Analysis</h3>
          <div className="space-y-3">
            {trends.slice(0, 4).map((trend, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  {trend.direction === 'up' ? (
                    <TrendingUp className="w-4 h-4 text-green-400" />
                  ) : trend.direction === 'down' ? (
                    <TrendingDown className="w-4 h-4 text-red-400" />
                  ) : (
                    <Activity className="w-4 h-4 text-gray-400" />
                  )}
                  <span className="text-sm text-white">{trend.metric}</span>
                </div>
                <div className="text-right">
                  <span className={`text-sm font-medium ${
                    trend.direction === 'up' ? 'text-green-400' : 
                    trend.direction === 'down' ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    {trend.change > 0 ? '+' : ''}{trend.change.toFixed(1)}%
                  </span>
                  <p className="text-xs text-gray-400">{trend.period}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Performance Summary */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Performance Summary</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Overall Health</span>
              <div className="flex items-center space-x-2">
                {performance.responseTime < 1000 && performance.cpuUsage < 70 && performance.memoryUsage < 80 ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span className="text-green-400 font-medium">Excellent</span>
                  </>
                ) : performance.responseTime < 3000 && performance.cpuUsage < 90 && performance.memoryUsage < 95 ? (
                  <>
                    <AlertTriangle className="w-4 h-4 text-yellow-400" />
                    <span className="text-yellow-400 font-medium">Good</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                    <span className="text-red-400 font-medium">Needs Attention</span>
                  </>
                )}
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Throughput</span>
              <span className="text-white font-medium">{performance.throughput.toFixed(1)} req/s</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Error Rate</span>
              <span className={`font-medium ${
                performance.errorRate < 0.01 ? 'text-green-400' : 
                performance.errorRate < 0.05 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {(performance.errorRate * 100).toFixed(2)}%
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Uptime</span>
              <span className="text-green-400 font-medium">99.9%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceCharts;