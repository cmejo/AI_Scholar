/**
 * Analytics Overview Component - Key metrics display
 * Implements part of task 2.3: Build AnalyticsOverview component with key metrics display
 */

import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  Users, 
  FileText, 
  Clock, 
  CheckCircle,
  AlertTriangle,
  Activity
} from 'lucide-react';
import { OverviewMetrics } from '../../../types/ui';

interface AnalyticsOverviewProps {
  metrics: OverviewMetrics;
  loading?: boolean;
  timeRange: string;
  previousMetrics?: OverviewMetrics;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  color: 'blue' | 'green' | 'yellow' | 'purple' | 'red' | 'gray';
  loading?: boolean;
  subtitle?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon,
  trend,
  trendValue,
  color,
  loading,
  subtitle
}) => {
  const colorClasses = {
    blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    green: 'bg-green-500/20 text-green-400 border-green-500/30',
    yellow: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    purple: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    red: 'bg-red-500/20 text-red-400 border-red-500/30',
    gray: 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-3 h-3 text-green-400" />;
      case 'down':
        return <TrendingDown className="w-3 h-3 text-red-400" />;
      default:
        return <Minus className="w-3 h-3 text-gray-400" />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-400';
      case 'down':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-all duration-200 hover:shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          <p className="text-gray-400 text-sm font-medium mb-1">{title}</p>
          {loading ? (
            <div className="animate-pulse">
              <div className="h-8 bg-gray-700 rounded w-20"></div>
            </div>
          ) : (
            <p className="text-2xl font-bold text-white">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
          )}
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>

      {/* Trend indicator */}
      {trend && trendValue !== undefined && !loading && (
        <div className="flex items-center space-x-2">
          {getTrendIcon()}
          <span className={`text-xs font-medium ${getTrendColor()}`}>
            {Math.abs(trendValue).toFixed(1)}%
          </span>
          <span className="text-xs text-gray-500">vs previous period</span>
        </div>
      )}
    </div>
  );
};

export const AnalyticsOverview: React.FC<AnalyticsOverviewProps> = ({
  metrics,
  loading = false,
  timeRange,
  previousMetrics
}) => {
  // Calculate trends if previous metrics are available
  const calculateTrend = (current: number, previous: number): { trend: 'up' | 'down' | 'stable'; value: number } => {
    if (!previous || previous === 0) return { trend: 'stable', value: 0 };
    
    const change = ((current - previous) / previous) * 100;
    
    if (Math.abs(change) < 1) return { trend: 'stable', value: change };
    return { trend: change > 0 ? 'up' : 'down', value: change };
  };

  const queryTrend = previousMetrics ? calculateTrend(metrics.totalQueries, previousMetrics.totalQueries) : undefined;
  const userTrend = previousMetrics ? calculateTrend(metrics.totalUsers, previousMetrics.totalUsers) : undefined;
  const responseTrend = previousMetrics ? calculateTrend(metrics.averageResponseTime, previousMetrics.averageResponseTime) : undefined;
  const successTrend = previousMetrics ? calculateTrend(metrics.successRate, previousMetrics.successRate) : undefined;
  const satisfactionTrend = previousMetrics ? calculateTrend(metrics.satisfactionScore, previousMetrics.satisfactionScore) : undefined;

  // Format response time
  const formatResponseTime = (time: number): string => {
    if (time < 1000) return `${Math.round(time)}ms`;
    return `${(time / 1000).toFixed(1)}s`;
  };

  // Get success rate color
  const getSuccessRateColor = (rate: number): 'green' | 'yellow' | 'red' => {
    if (rate >= 0.95) return 'green';
    if (rate >= 0.85) return 'yellow';
    return 'red';
  };

  // Get satisfaction color
  const getSatisfactionColor = (score: number): 'green' | 'yellow' | 'red' => {
    if (score >= 0.8) return 'green';
    if (score >= 0.6) return 'yellow';
    return 'red';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Overview</h2>
          <p className="text-sm text-gray-400">Key metrics for {timeRange}</p>
        </div>
        
        {/* Health indicator */}
        <div className="flex items-center space-x-2">
          {loading ? (
            <div className="animate-pulse flex items-center space-x-2">
              <div className="w-2 h-2 bg-gray-600 rounded-full"></div>
              <span className="text-sm text-gray-500">Loading...</span>
            </div>
          ) : (
            <>
              {metrics.successRate >= 0.95 && metrics.satisfactionScore >= 0.8 ? (
                <>
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-sm text-green-400">Healthy</span>
                </>
              ) : metrics.successRate >= 0.85 && metrics.satisfactionScore >= 0.6 ? (
                <>
                  <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
                  <span className="text-sm text-yellow-400">Warning</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
                  <span className="text-sm text-red-400">Critical</span>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {/* Total Queries */}
        <MetricCard
          title="Total Queries"
          value={metrics.totalQueries}
          icon={<TrendingUp className="w-6 h-6" />}
          color="blue"
          trend={queryTrend?.trend}
          trendValue={queryTrend?.value}
          loading={loading}
          subtitle={`${timeRange} period`}
        />

        {/* Active Users */}
        <MetricCard
          title="Active Users"
          value={metrics.totalUsers}
          icon={<Users className="w-6 h-6" />}
          color="green"
          trend={userTrend?.trend}
          trendValue={userTrend?.value}
          loading={loading}
          subtitle="Unique users"
        />

        {/* Documents */}
        <MetricCard
          title="Documents"
          value={metrics.totalDocuments}
          icon={<FileText className="w-6 h-6" />}
          color="purple"
          loading={loading}
          subtitle="Available documents"
        />

        {/* Response Time */}
        <MetricCard
          title="Avg Response Time"
          value={formatResponseTime(metrics.averageResponseTime)}
          icon={<Clock className="w-6 h-6" />}
          color="yellow"
          trend={responseTrend?.trend === 'down' ? 'up' : responseTrend?.trend === 'up' ? 'down' : 'stable'} // Invert trend for response time
          trendValue={responseTrend?.value}
          loading={loading}
          subtitle="System performance"
        />

        {/* Success Rate */}
        <MetricCard
          title="Success Rate"
          value={`${(metrics.successRate * 100).toFixed(1)}%`}
          icon={metrics.successRate >= 0.95 ? <CheckCircle className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
          color={getSuccessRateColor(metrics.successRate)}
          trend={successTrend?.trend}
          trendValue={successTrend?.value}
          loading={loading}
          subtitle="Query success rate"
        />
      </div>

      {/* Additional Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Satisfaction Score */}
        <MetricCard
          title="User Satisfaction"
          value={`${(metrics.satisfactionScore * 100).toFixed(1)}%`}
          icon={<Activity className="w-6 h-6" />}
          color={getSatisfactionColor(metrics.satisfactionScore)}
          trend={satisfactionTrend?.trend}
          trendValue={satisfactionTrend?.value}
          loading={loading}
          subtitle="Average user satisfaction"
        />

        {/* System Health Summary */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">System Health</h3>
            <Activity className="w-5 h-5 text-gray-400" />
          </div>
          
          {loading ? (
            <div className="space-y-2">
              <div className="animate-pulse h-4 bg-gray-700 rounded w-3/4"></div>
              <div className="animate-pulse h-4 bg-gray-700 rounded w-1/2"></div>
              <div className="animate-pulse h-4 bg-gray-700 rounded w-2/3"></div>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Performance Status */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Performance</span>
                <div className="flex items-center space-x-2">
                  {metrics.averageResponseTime < 1000 ? (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  ) : metrics.averageResponseTime < 3000 ? (
                    <AlertTriangle className="w-4 h-4 text-yellow-400" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                  )}
                  <span className="text-sm text-white">
                    {metrics.averageResponseTime < 1000 ? 'Excellent' : 
                     metrics.averageResponseTime < 3000 ? 'Good' : 'Poor'}
                  </span>
                </div>
              </div>

              {/* Reliability Status */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Reliability</span>
                <div className="flex items-center space-x-2">
                  {metrics.successRate >= 0.95 ? (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  ) : metrics.successRate >= 0.85 ? (
                    <AlertTriangle className="w-4 h-4 text-yellow-400" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                  )}
                  <span className="text-sm text-white">
                    {metrics.successRate >= 0.95 ? 'Excellent' : 
                     metrics.successRate >= 0.85 ? 'Good' : 'Poor'}
                  </span>
                </div>
              </div>

              {/* User Experience Status */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">User Experience</span>
                <div className="flex items-center space-x-2">
                  {metrics.satisfactionScore >= 0.8 ? (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  ) : metrics.satisfactionScore >= 0.6 ? (
                    <AlertTriangle className="w-4 h-4 text-yellow-400" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                  )}
                  <span className="text-sm text-white">
                    {metrics.satisfactionScore >= 0.8 ? 'Excellent' : 
                     metrics.satisfactionScore >= 0.6 ? 'Good' : 'Poor'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsOverview;