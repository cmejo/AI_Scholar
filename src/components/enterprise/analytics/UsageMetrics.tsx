/**
 * Usage Metrics Component - Interactive charts for usage analytics
 * Implements part of task 2.3: Implement UsageMetrics component with interactive charts
 */

import React, { useState, useMemo } from 'react';
import { 
  BarChart3, 
  LineChart, 
  PieChart, 
  TrendingUp, 
  Users, 
  Clock, 
  Filter,
  Calendar,
  Activity
} from 'lucide-react';
import { QueryAnalytics, UserAnalytics, TrendAnalysis } from '../../../types/ui';

interface UsageMetricsProps {
  queries: QueryAnalytics[];
  users: UserAnalytics[];
  trends: TrendAnalysis[];
  loading?: boolean;
  timeRange: string;
}

interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    color: string;
    borderColor?: string;
    backgroundColor?: string;
  }>;
}

interface FilterOptions {
  chartType: 'line' | 'bar' | 'pie';
  metric: 'queries' | 'users' | 'responseTime' | 'satisfaction';
  groupBy: 'hour' | 'day' | 'week';
}

export const UsageMetrics: React.FC<UsageMetricsProps> = ({
  queries,
  users,
  trends,
  loading = false,
  timeRange
}) => {
  const [filters, setFilters] = useState<FilterOptions>({
    chartType: 'line',
    metric: 'queries',
    groupBy: 'day'
  });

  const [selectedChart, setSelectedChart] = useState<'overview' | 'queries' | 'users' | 'trends'>('overview');

  // Process data for charts
  const chartData = useMemo(() => {
    if (loading || !queries.length) return null;

    const processedData: ChartData = {
      labels: [],
      datasets: []
    };

    switch (filters.metric) {
      case 'queries':
        // Group queries by time period
        const queryGroups = groupDataByTime(queries, filters.groupBy);
        processedData.labels = Object.keys(queryGroups);
        processedData.datasets = [{
          label: 'Query Count',
          data: Object.values(queryGroups).map(group => group.length),
          color: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderColor: '#3B82F6'
        }];
        break;

      case 'users':
        // Group users by activity
        const userGroups = groupUsersByActivity(users, filters.groupBy);
        processedData.labels = Object.keys(userGroups);
        processedData.datasets = [{
          label: 'Active Users',
          data: Object.values(userGroups),
          color: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderColor: '#10B981'
        }];
        break;

      case 'responseTime':
        // Average response time over time
        const responseGroups = groupDataByTime(queries, filters.groupBy);
        processedData.labels = Object.keys(responseGroups);
        processedData.datasets = [{
          label: 'Avg Response Time (ms)',
          data: Object.entries(responseGroups).map(([_, group]) => 
            group.reduce((sum, q) => sum + q.averageResponseTime, 0) / group.length
          ),
          color: '#F59E0B',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          borderColor: '#F59E0B'
        }];
        break;

      case 'satisfaction':
        // User satisfaction over time
        const satisfactionGroups = groupUsersByTime(users, filters.groupBy);
        processedData.labels = Object.keys(satisfactionGroups);
        processedData.datasets = [{
          label: 'Avg Satisfaction Score',
          data: Object.entries(satisfactionGroups).map(([_, group]) => 
            group.reduce((sum, u) => sum + u.satisfactionScore, 0) / group.length
          ),
          color: '#8B5CF6',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          borderColor: '#8B5CF6'
        }];
        break;
    }

    return processedData;
  }, [queries, users, filters, loading]);

  // Group data by time period
  const groupDataByTime = (data: QueryAnalytics[], groupBy: string) => {
    const groups: { [key: string]: QueryAnalytics[] } = {};
    
    data.forEach(item => {
      let key: string;
      const date = new Date(item.timestamp);
      
      switch (groupBy) {
        case 'hour':
          key = `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:00`;
          break;
        case 'day':
          key = `${date.getMonth() + 1}/${date.getDate()}`;
          break;
        case 'week':
          const weekStart = new Date(date);
          weekStart.setDate(date.getDate() - date.getDay());
          key = `Week of ${weekStart.getMonth() + 1}/${weekStart.getDate()}`;
          break;
        default:
          key = date.toDateString();
      }
      
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    });
    
    return groups;
  };

  // Group users by time period
  const groupUsersByTime = (data: UserAnalytics[], groupBy: string) => {
    const groups: { [key: string]: UserAnalytics[] } = {};
    
    data.forEach(user => {
      let key: string;
      const date = new Date(user.lastActive);
      
      switch (groupBy) {
        case 'hour':
          key = `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:00`;
          break;
        case 'day':
          key = `${date.getMonth() + 1}/${date.getDate()}`;
          break;
        case 'week':
          const weekStart = new Date(date);
          weekStart.setDate(date.getDate() - date.getDay());
          key = `Week of ${weekStart.getMonth() + 1}/${weekStart.getDate()}`;
          break;
        default:
          key = date.toDateString();
      }
      
      if (!groups[key]) groups[key] = [];
      groups[key].push(user);
    });
    
    return groups;
  };

  // Group users by activity level
  const groupUsersByActivity = (data: UserAnalytics[], groupBy: string) => {
    const groups: { [key: string]: number } = {};
    
    // Create time-based groups and count active users in each
    const timeGroups = groupUsersByTime(data, groupBy);
    
    Object.entries(timeGroups).forEach(([key, users]) => {
      groups[key] = users.length;
    });
    
    return groups;
  };

  // Simple chart component (since we don't have a chart library)
  const SimpleChart: React.FC<{ data: ChartData; type: 'line' | 'bar' | 'pie' }> = ({ data, type }) => {
    if (!data || !data.datasets.length) {
      return (
        <div className="flex items-center justify-center h-64 text-gray-500">
          <div className="text-center">
            <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-600" />
            <p>No data available</p>
          </div>
        </div>
      );
    }

    const maxValue = Math.max(...data.datasets[0].data);
    
    return (
      <div className="h-64 p-4">
        <div className="flex items-end justify-between h-full space-x-2">
          {data.labels.map((label, index) => {
            const value = data.datasets[0].data[index];
            const height = (value / maxValue) * 100;
            
            return (
              <div key={label} className="flex-1 flex flex-col items-center">
                <div className="flex-1 flex items-end">
                  {type === 'bar' ? (
                    <div
                      className="w-full bg-blue-500 rounded-t transition-all duration-300 hover:bg-blue-400"
                      style={{ height: `${height}%`, minHeight: '4px' }}
                      title={`${label}: ${value}`}
                    />
                  ) : (
                    <div
                      className="w-2 h-2 bg-blue-500 rounded-full"
                      style={{ marginBottom: `${height}%` }}
                      title={`${label}: ${value}`}
                    />
                  )}
                </div>
                <div className="text-xs text-gray-400 mt-2 text-center truncate w-full">
                  {label}
                </div>
                <div className="text-xs text-white font-medium">
                  {value.toLocaleString()}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Top queries component
  const TopQueries: React.FC = () => {
    const topQueries = queries
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    return (
      <div className="space-y-3">
        {topQueries.map((query, index) => (
          <div key={query.id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-xs font-bold">
                {index + 1}
              </div>
              <div>
                <p className="text-sm font-medium text-white truncate max-w-xs">
                  {query.query}
                </p>
                <p className="text-xs text-gray-400">
                  {query.count} queries • {(query.successRate * 100).toFixed(1)}% success
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-white">
                {query.averageResponseTime.toFixed(0)}ms
              </p>
              <p className="text-xs text-gray-400">avg response</p>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Top users component
  const TopUsers: React.FC = () => {
    const topUsers = users
      .sort((a, b) => b.queryCount - a.queryCount)
      .slice(0, 5);

    return (
      <div className="space-y-3">
        {topUsers.map((user, index) => (
          <div key={user.id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-xs font-bold">
                {index + 1}
              </div>
              <div>
                <p className="text-sm font-medium text-white">
                  {user.name}
                </p>
                <p className="text-xs text-gray-400">
                  Last active: {new Date(user.lastActive).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-white">
                {user.queryCount}
              </p>
              <p className="text-xs text-gray-400">queries</p>
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with filters */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        <div>
          <h2 className="text-xl font-semibold text-white">Usage Metrics</h2>
          <p className="text-sm text-gray-400">Interactive analytics for {timeRange}</p>
        </div>
        
        {/* Chart type selector */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setSelectedChart('overview')}
            className={`px-3 py-2 rounded-lg text-sm transition-colors ${
              selectedChart === 'overview' 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setSelectedChart('queries')}
            className={`px-3 py-2 rounded-lg text-sm transition-colors ${
              selectedChart === 'queries' 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Queries
          </button>
          <button
            onClick={() => setSelectedChart('users')}
            className={`px-3 py-2 rounded-lg text-sm transition-colors ${
              selectedChart === 'users' 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Users
          </button>
          <button
            onClick={() => setSelectedChart('trends')}
            className={`px-3 py-2 rounded-lg text-sm transition-colors ${
              selectedChart === 'trends' 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Trends
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-400">Filters:</span>
        </div>
        
        <select
          value={filters.metric}
          onChange={(e) => setFilters(prev => ({ ...prev, metric: e.target.value as any }))}
          className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
        >
          <option value="queries">Queries</option>
          <option value="users">Users</option>
          <option value="responseTime">Response Time</option>
          <option value="satisfaction">Satisfaction</option>
        </select>
        
        <select
          value={filters.groupBy}
          onChange={(e) => setFilters(prev => ({ ...prev, groupBy: e.target.value as any }))}
          className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
        >
          <option value="hour">By Hour</option>
          <option value="day">By Day</option>
          <option value="week">By Week</option>
        </select>
        
        <select
          value={filters.chartType}
          onChange={(e) => setFilters(prev => ({ ...prev, chartType: e.target.value as any }))}
          className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
        >
          <option value="line">Line Chart</option>
          <option value="bar">Bar Chart</option>
          <option value="pie">Pie Chart</option>
        </select>
      </div>

      {/* Main content based on selected chart */}
      {selectedChart === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Main chart */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">
                {filters.metric.charAt(0).toUpperCase() + filters.metric.slice(1)} Trend
              </h3>
              {filters.chartType === 'line' ? (
                <LineChart className="w-5 h-5 text-gray-400" />
              ) : filters.chartType === 'bar' ? (
                <BarChart3 className="w-5 h-5 text-gray-400" />
              ) : (
                <PieChart className="w-5 h-5 text-gray-400" />
              )}
            </div>
            {chartData && <SimpleChart data={chartData} type={filters.chartType} />}
          </div>

          {/* Summary stats */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Summary Statistics</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Total Queries</span>
                <span className="text-white font-medium">{queries.length.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Active Users</span>
                <span className="text-white font-medium">{users.length.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Avg Response Time</span>
                <span className="text-white font-medium">
                  {queries.length > 0 
                    ? (queries.reduce((sum, q) => sum + q.averageResponseTime, 0) / queries.length).toFixed(0)
                    : 0}ms
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Success Rate</span>
                <span className="text-white font-medium">
                  {queries.length > 0 
                    ? (queries.reduce((sum, q) => sum + q.successRate, 0) / queries.length * 100).toFixed(1)
                    : 0}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedChart === 'queries' && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Top Queries</h3>
          <TopQueries />
        </div>
      )}

      {selectedChart === 'users' && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Most Active Users</h3>
          <TopUsers />
        </div>
      )}

      {selectedChart === 'trends' && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Trend Analysis</h3>
          <div className="space-y-4">
            {trends.map((trend, index) => (
              <div key={index} className="p-4 bg-gray-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-medium">{trend.metric}</span>
                  <div className="flex items-center space-x-2">
                    {trend.direction === 'up' ? (
                      <TrendingUp className="w-4 h-4 text-green-400" />
                    ) : trend.direction === 'down' ? (
                      <TrendingUp className="w-4 h-4 text-red-400 rotate-180" />
                    ) : (
                      <Activity className="w-4 h-4 text-gray-400" />
                    )}
                    <span className={`text-sm ${
                      trend.direction === 'up' ? 'text-green-400' : 
                      trend.direction === 'down' ? 'text-red-400' : 'text-gray-400'
                    }`}>
                      {trend.change > 0 ? '+' : ''}{trend.change.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-400">
                  {trend.period} analysis • Current value: {trend.value.toFixed(2)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default UsageMetrics;