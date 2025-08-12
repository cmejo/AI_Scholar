/**
 * Performance monitoring dashboard component
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Activity } from 'lucide-react/dist/esm/icons/activity';
import { Clock } from 'lucide-react/dist/esm/icons/clock';
import { Zap } from 'lucide-react/dist/esm/icons/zap';
import { AlertTriangle } from 'lucide-react/dist/esm/icons/alert-triangle';
import { TrendingUp } from 'lucide-react/dist/esm/icons/trending-up';
import { TrendingDown } from 'lucide-react/dist/esm/icons/trending-down';
import { performanceMonitor, type PerformanceMetrics } from '../utils/performanceMonitor';
import { useRenderPerformance } from '../hooks/usePerformanceOptimization';

interface PerformanceStats {
  averageRenderTime: number;
  totalRenders: number;
  slowRenders: number;
  fastRenders: number;
  trend: 'up' | 'down' | 'stable';
}

const PerformanceCard: React.FC<{
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'stable';
  color: string;
}> = React.memo(({ title, value, subtitle, icon, trend, color }) => (
  <div className={`bg-gray-800 rounded-lg p-4 border-l-4 ${color}`}>
    <div className="flex items-center justify-between">
      <div>
        <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        <div className="flex items-center space-x-2 mt-1">
          <span className="text-2xl font-bold text-white">{value}</span>
          {trend && (
            <div className="flex items-center">
              {trend === 'up' && <TrendingUp size={16} className="text-red-400" />}
              {trend === 'down' && <TrendingDown size={16} className="text-green-400" />}
              {trend === 'stable' && <div className="w-4 h-0.5 bg-gray-400" />}
            </div>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
      </div>
      <div className="text-gray-400">
        {icon}
      </div>
    </div>
  </div>
));

PerformanceCard.displayName = 'PerformanceCard';

const ComponentMetricsTable: React.FC<{
  metrics: Record<string, PerformanceStats>;
}> = React.memo(({ metrics }) => (
  <div className="bg-gray-800 rounded-lg overflow-hidden">
    <div className="px-4 py-3 border-b border-gray-700">
      <h3 className="text-lg font-medium text-white">Component Performance</h3>
    </div>
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-700">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
              Component
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
              Avg Render Time
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
              Total Renders
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
              Slow Renders
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700">
          {Object.entries(metrics).map(([componentName, stats]) => (
            <tr key={componentName} className="hover:bg-gray-700/50">
              <td className="px-4 py-3 text-sm font-medium text-white">
                {componentName}
              </td>
              <td className="px-4 py-3 text-sm text-gray-300">
                {stats.averageRenderTime.toFixed(2)}ms
              </td>
              <td className="px-4 py-3 text-sm text-gray-300">
                {stats.totalRenders}
              </td>
              <td className="px-4 py-3 text-sm">
                <span className={`${
                  stats.slowRenders > 0 ? 'text-red-400' : 'text-green-400'
                }`}>
                  {stats.slowRenders}
                </span>
              </td>
              <td className="px-4 py-3 text-sm">
                {stats.averageRenderTime > 16 ? (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-red-900 text-red-200">
                    <AlertTriangle size={12} className="mr-1" />
                    Needs Optimization
                  </span>
                ) : stats.averageRenderTime > 8 ? (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-900 text-yellow-200">
                    <Clock size={12} className="mr-1" />
                    Monitor
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-900 text-green-200">
                    <Zap size={12} className="mr-1" />
                    Optimized
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
));

ComponentMetricsTable.displayName = 'ComponentMetricsTable';

const RecommendationsList: React.FC<{
  recommendations: string[];
}> = React.memo(({ recommendations }) => (
  <div className="bg-gray-800 rounded-lg p-4">
    <h3 className="text-lg font-medium text-white mb-4">Optimization Recommendations</h3>
    {recommendations.length === 0 ? (
      <div className="text-center py-8">
        <Zap className="mx-auto h-12 w-12 text-green-400 mb-4" />
        <p className="text-gray-400">All components are performing well!</p>
      </div>
    ) : (
      <ul className="space-y-3">
        {recommendations.map((recommendation, index) => (
          <li key={index} className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-yellow-400 mt-0.5 flex-shrink-0" />
            <span className="text-gray-300 text-sm">{recommendation}</span>
          </li>
        ))}
      </ul>
    )}
  </div>
));

RecommendationsList.displayName = 'RecommendationsList';

export const PerformanceDashboard: React.FC = () => {
  useRenderPerformance('PerformanceDashboard');
  
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      const allMetrics = performanceMonitor.getAllMetrics();
      setMetrics(allMetrics);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const performanceStats = useMemo(() => {
    const componentStats: Record<string, PerformanceStats> = {};
    
    // Group metrics by component
    const componentGroups = metrics.reduce((groups, metric) => {
      if (!groups[metric.componentName]) {
        groups[metric.componentName] = [];
      }
      groups[metric.componentName].push(metric);
      return groups;
    }, {} as Record<string, PerformanceMetrics[]>);

    // Calculate stats for each component
    Object.entries(componentGroups).forEach(([componentName, componentMetrics]) => {
      const renderTimes = componentMetrics.map(m => m.renderTime);
      const averageRenderTime = renderTimes.reduce((sum, time) => sum + time, 0) / renderTimes.length;
      const slowRenders = renderTimes.filter(time => time > 16).length;
      const fastRenders = renderTimes.filter(time => time <= 8).length;

      // Calculate trend (simplified)
      const recentMetrics = componentMetrics.slice(-10);
      const olderMetrics = componentMetrics.slice(-20, -10);
      const recentAvg = recentMetrics.reduce((sum, m) => sum + m.renderTime, 0) / recentMetrics.length;
      const olderAvg = olderMetrics.reduce((sum, m) => sum + m.renderTime, 0) / olderMetrics.length;
      
      let trend: 'up' | 'down' | 'stable' = 'stable';
      if (recentAvg > olderAvg * 1.1) trend = 'up';
      else if (recentAvg < olderAvg * 0.9) trend = 'down';

      componentStats[componentName] = {
        averageRenderTime,
        totalRenders: componentMetrics.length,
        slowRenders,
        fastRenders,
        trend,
      };
    });

    return componentStats;
  }, [metrics]);

  const overallStats = useMemo(() => {
    const allRenderTimes = metrics.map(m => m.renderTime);
    const totalRenders = metrics.length;
    const averageRenderTime = totalRenders > 0 
      ? allRenderTimes.reduce((sum, time) => sum + time, 0) / totalRenders 
      : 0;
    const slowRenders = allRenderTimes.filter(time => time > 16).length;
    const fastRenders = allRenderTimes.filter(time => time <= 8).length;

    return {
      totalRenders,
      averageRenderTime,
      slowRenders,
      fastRenders,
    };
  }, [metrics]);

  const report = useMemo(() => {
    return performanceMonitor.generateReport();
  }, [metrics]);

  const handleStartRecording = () => {
    setIsRecording(true);
    performanceMonitor.clearMetrics();
  };

  const handleStopRecording = () => {
    setIsRecording(false);
  };

  const handleClearMetrics = () => {
    performanceMonitor.clearMetrics();
    setMetrics([]);
  };

  return (
    <div className="p-6 bg-gray-900 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Performance Dashboard</h1>
            <p className="text-gray-400 mt-2">
              Monitor React component performance and identify optimization opportunities
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={isRecording ? handleStopRecording : handleStartRecording}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                isRecording
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
            
            <button
              onClick={handleClearMetrics}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
            >
              Clear Data
            </button>
          </div>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <PerformanceCard
            title="Total Renders"
            value={overallStats.totalRenders.toString()}
            subtitle="Component renders tracked"
            icon={<Activity size={24} />}
            color="border-blue-500"
          />
          
          <PerformanceCard
            title="Average Render Time"
            value={`${overallStats.averageRenderTime.toFixed(2)}ms`}
            subtitle="Across all components"
            icon={<Clock size={24} />}
            color="border-purple-500"
          />
          
          <PerformanceCard
            title="Fast Renders"
            value={overallStats.fastRenders.toString()}
            subtitle="≤8ms render time"
            icon={<Zap size={24} />}
            color="border-green-500"
          />
          
          <PerformanceCard
            title="Slow Renders"
            value={overallStats.slowRenders.toString()}
            subtitle=">16ms render time"
            icon={<AlertTriangle size={24} />}
            color="border-red-500"
          />
        </div>

        {/* Component Metrics Table */}
        <div className="mb-8">
          <ComponentMetricsTable metrics={performanceStats} />
        </div>

        {/* Recommendations */}
        <RecommendationsList recommendations={report.recommendations} />

        {/* Debug Info (Development Only) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-8 bg-gray-800 rounded-lg p-4">
            <h3 className="text-lg font-medium text-white mb-4">Debug Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-medium text-gray-300 mb-2">Recording Status</h4>
                <p className="text-gray-400">
                  Status: {isRecording ? 'Recording' : 'Stopped'}
                </p>
                <p className="text-gray-400">
                  Metrics Count: {metrics.length}
                </p>
              </div>
              <div>
                <h4 className="font-medium text-gray-300 mb-2">Performance Thresholds</h4>
                <p className="text-gray-400">Fast: ≤8ms</p>
                <p className="text-gray-400">Normal: 8-16ms</p>
                <p className="text-gray-400">Slow: >16ms</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};