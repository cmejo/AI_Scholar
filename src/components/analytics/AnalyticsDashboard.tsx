import React, { useState, useEffect } from 'react';
import { BarChart3, Users, MessageSquare, TrendingUp, Activity, Calendar, Filter, Download } from 'lucide-react';
import { UsageMetrics } from './UsageMetrics';
import { UserActivityChart } from './UserActivityChart';
import { ContentAnalytics } from './ContentAnalytics';
import { PerformanceMetrics } from './PerformanceMetrics';
import { analyticsService } from '../../services/analyticsService';

interface AnalyticsData {
  totalUsers: number;
  activeUsers: number;
  totalMessages: number;
  avgResponseTime: number;
  userGrowth: number;
  messageGrowth: number;
  dailyActivity: Array<{ date: string; users: number; messages: number }>;
  topContent: Array<{ title: string; views: number; engagement: number }>;
  performanceMetrics: {
    uptime: number;
    errorRate: number;
    avgLoadTime: number;
  };
}

export const AnalyticsDashboard: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [selectedMetric, setSelectedMetric] = useState<'users' | 'messages' | 'performance'>('users');

  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange]);

  const loadAnalyticsData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const analyticsData = await analyticsService.getAnalytics(timeRange);
      setData(analyticsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setIsLoading(false);
    }
  };

  const exportData = async () => {
    try {
      await analyticsService.exportAnalytics(timeRange);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-2 border-purple-500 border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/50 border border-red-500 rounded-lg p-6 text-center">
        <p className="text-red-300">{error}</p>
        <button
          onClick={loadAnalyticsData}
          className="mt-4 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center">
            <BarChart3 className="w-8 h-8 mr-3 text-purple-500" />
            Analytics Dashboard
          </h1>
          <p className="text-gray-400 mt-1">Monitor your Reddit AEO performance and usage</p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as '7d' | '30d' | '90d')}
              className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>

          <button
            onClick={exportData}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center text-sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Users</p>
              <p className="text-2xl font-bold text-white">{data.totalUsers.toLocaleString()}</p>
              <p className="text-green-400 text-sm flex items-center mt-1">
                <TrendingUp className="w-3 h-3 mr-1" />
                +{data.userGrowth}% from last period
              </p>
            </div>
            <Users className="w-8 h-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Active Users</p>
              <p className="text-2xl font-bold text-white">{data.activeUsers.toLocaleString()}</p>
              <p className="text-gray-400 text-sm mt-1">
                {((data.activeUsers / data.totalUsers) * 100).toFixed(1)}% of total
              </p>
            </div>
            <Activity className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Messages</p>
              <p className="text-2xl font-bold text-white">{data.totalMessages.toLocaleString()}</p>
              <p className="text-blue-400 text-sm flex items-center mt-1">
                <TrendingUp className="w-3 h-3 mr-1" />
                +{data.messageGrowth}% from last period
              </p>
            </div>
            <MessageSquare className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Avg Response Time</p>
              <p className="text-2xl font-bold text-white">{data.avgResponseTime}ms</p>
              <p className="text-yellow-400 text-sm mt-1">
                System performance
              </p>
            </div>
            <Calendar className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
      </div>

      {/* Metric Selector */}
      <div className="flex space-x-2 bg-gray-800 rounded-lg p-2 border border-gray-700 w-fit">
        <button
          onClick={() => setSelectedMetric('users')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selectedMetric === 'users'
              ? 'bg-purple-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-700'
          }`}
        >
          User Analytics
        </button>
        <button
          onClick={() => setSelectedMetric('messages')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selectedMetric === 'messages'
              ? 'bg-purple-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-700'
          }`}
        >
          Content Analytics
        </button>
        <button
          onClick={() => setSelectedMetric('performance')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selectedMetric === 'performance'
              ? 'bg-purple-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-700'
          }`}
        >
          Performance
        </button>
      </div>

      {/* Charts and Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {selectedMetric === 'users' && (
          <>
            <UsageMetrics data={data.dailyActivity} timeRange={timeRange} />
            <UserActivityChart data={data.dailyActivity} />
          </>
        )}
        
        {selectedMetric === 'messages' && (
          <>
            <ContentAnalytics data={data.topContent} />
            <UserActivityChart data={data.dailyActivity} />
          </>
        )}
        
        {selectedMetric === 'performance' && (
          <>
            <PerformanceMetrics data={data.performanceMetrics} />
            <UserActivityChart data={data.dailyActivity} />
          </>
        )}
      </div>

      {/* Additional Insights */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-xl font-semibold text-white mb-4">Key Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-700 rounded-lg p-4">
            <h4 className="font-medium text-white mb-2">Peak Usage Hours</h4>
            <p className="text-gray-300 text-sm">
              Most active between 2-4 PM and 8-10 PM
            </p>
          </div>
          <div className="bg-gray-700 rounded-lg p-4">
            <h4 className="font-medium text-white mb-2">Popular Features</h4>
            <p className="text-gray-300 text-sm">
              Voice chat and document analysis are trending
            </p>
          </div>
          <div className="bg-gray-700 rounded-lg p-4">
            <h4 className="font-medium text-white mb-2">User Retention</h4>
            <p className="text-gray-300 text-sm">
              85% of users return within 7 days
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};