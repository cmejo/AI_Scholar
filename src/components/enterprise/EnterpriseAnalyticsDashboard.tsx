/**
 * Enterprise Analytics Dashboard - Main dashboard component with layout and navigation
 * Implements task 2.1: Create EnterpriseAnalyticsDashboard component with layout and navigation
 * Implements task 4.1: Integrate authentication service with enterprise features
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  TrendingUp, 
  Users, 
  Clock, 
  Activity, 
  RefreshCw, 
  Calendar,
  AlertCircle,
  CheckCircle,
  Download,
  Shield,
  User
} from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { enterpriseAnalyticsService } from '../../services/enterpriseAnalyticsService';
import { AnalyticsDashboardData, OverviewMetrics } from '../../types/ui';
import { 
  AnalyticsOverview, 
  UsageMetrics, 
  PerformanceCharts, 
  UserBehaviorAnalytics 
} from './analytics';
import { useEnterpriseAuth } from '../../hooks/useEnterpriseAuth';
import { EnterpriseAuthGuard, usePermissionGate } from './EnterpriseAuthGuard';

export interface EnterpriseAnalyticsDashboardProps {
  userId?: string;
  timeRange?: '24h' | '7d' | '30d' | '90d';
  onTimeRangeChange?: (range: string) => void;
}

interface LoadingState {
  overview: boolean;
  charts: boolean;
  data: boolean;
}

interface ErrorState {
  overview: string | null;
  charts: string | null;
  data: string | null;
}

export const EnterpriseAnalyticsDashboard: React.FC<EnterpriseAnalyticsDashboardProps> = ({
  userId,
  timeRange = '24h',
  onTimeRangeChange
}) => {
  // Authentication and permissions
  const {
    user,
    isAuthenticated,
    canViewAnalytics,
    canExportAnalytics,
    hasPermission,
    session,
    sessionTimeRemaining
  } = useEnterpriseAuth();

  const gate = usePermissionGate();

  // State management
  const [dashboardData, setDashboardData] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState<LoadingState>({
    overview: true,
    charts: true,
    data: true
  });
  const [error, setError] = useState<ErrorState>({
    overview: null,
    charts: null,
    data: null
  });
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  // Time range options
  const timeRangeOptions = [
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' }
  ];

  // Calculate date range based on selected time range
  const dateRange = useMemo(() => {
    const end = new Date();
    const start = new Date();
    
    switch (timeRange) {
      case '24h':
        start.setHours(start.getHours() - 24);
        break;
      case '7d':
        start.setDate(start.getDate() - 7);
        break;
      case '30d':
        start.setDate(start.getDate() - 30);
        break;
      case '90d':
        start.setDate(start.getDate() - 90);
        break;
    }
    
    return { start, end };
  }, [timeRange]);

  // Fetch analytics data with enhanced enterprise service
  const fetchAnalyticsData = useCallback(async () => {
    // Check permissions before fetching data
    if (!canViewAnalytics) {
      setError(prev => ({ 
        ...prev, 
        overview: 'Insufficient permissions to view analytics data',
        data: 'Insufficient permissions to view analytics data'
      }));
      setLoading(prev => ({ ...prev, overview: false, data: false }));
      return;
    }

    try {
      setLoading(prev => ({ ...prev, overview: true, data: true }));
      setError(prev => ({ ...prev, overview: null, data: null }));

      // Fetch data from enterprise analytics service with caching and real-time updates
      const options = {
        includeRealTimeMetrics: hasPermission('analytics', 'admin'),
        aggregateUserData: hasPermission('analytics', 'admin'),
        calculateTrends: true,
        userId: user?.id, // Use authenticated user's ID
        ...(userId && hasPermission('analytics', 'admin') && { filterByUserId: userId })
      };
      const data = await enterpriseAnalyticsService.getDashboardData(dateRange, options);
      
      setDashboardData(data);
      setLastRefresh(new Date());
      
      setLoading(prev => ({ ...prev, overview: false, data: false }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch analytics data';
      setError(prev => ({ 
        ...prev, 
        overview: errorMessage, 
        data: errorMessage 
      }));
      setLoading(prev => ({ ...prev, overview: false, data: false }));
      
      // Try fallback to basic analytics service
      try {
        console.warn('Falling back to basic analytics service');
        const fallbackData = analyticsService.getDashboardData(dateRange);
        setDashboardData(fallbackData);
        setError(prev => ({ ...prev, overview: null, data: null }));
        setLoading(prev => ({ ...prev, overview: false, data: false }));
      } catch (fallbackErr) {
        console.error('Fallback also failed:', fallbackErr);
      }
    }
  }, [dateRange, userId, canViewAnalytics, hasPermission, user?.id]);

  // Handle time range change
  const handleTimeRangeChange = useCallback((newRange: string) => {
    onTimeRangeChange?.(newRange);
  }, [onTimeRangeChange]);

  // Handle manual refresh
  const handleRefresh = useCallback(() => {
    fetchAnalyticsData();
  }, [fetchAnalyticsData]);

  // Handle data export
  const handleExport = useCallback(async (format: 'json' | 'csv' | 'pdf' = 'json') => {
    // Check export permissions
    if (!canExportAnalytics) {
      setError(prev => ({ 
        ...prev, 
        data: 'You do not have permission to export analytics data' 
      }));
      return;
    }

    try {
      const exportOptions = {
        includeRealTimeMetrics: hasPermission('analytics', 'admin'),
        aggregateUserData: hasPermission('analytics', 'admin'),
        calculateTrends: true,
        userId: user?.id,
        ...(userId && hasPermission('analytics', 'admin') && { filterByUserId: userId })
      };
      const blob = await enterpriseAnalyticsService.exportData(dateRange, format, exportOptions);

      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `analytics-report-${timeRange}-${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      setError(prev => ({ 
        ...prev, 
        data: `Export failed: ${error instanceof Error ? error.message : 'Unknown error'}` 
      }));
    }
  }, [dateRange, timeRange, userId, canExportAnalytics, hasPermission, user?.id]);

  // Real-time subscription and auto-refresh functionality
  useEffect(() => {
    let unsubscribe: (() => void) | undefined;
    let backgroundRefreshStop: (() => void) | undefined;

    if (autoRefresh) {
      // Initialize WebSocket connection for real-time updates (if available)
      if (typeof enterpriseAnalyticsService.initializeWebSocket === 'function') {
        enterpriseAnalyticsService.initializeWebSocket();
      }
      
      // Configure refresh intervals based on time range
      const refreshInterval = timeRange === '24h' ? 30000 : // 30 seconds for 24h
                             timeRange === '7d' ? 60000 :  // 1 minute for 7d
                             timeRange === '30d' ? 300000 : // 5 minutes for 30d
                             600000; // 10 minutes for 90d
      
      // Configure refresh intervals if method is available
      if (typeof enterpriseAnalyticsService.configureRefreshIntervals === 'function') {
        enterpriseAnalyticsService.configureRefreshIntervals({
          dashboard: refreshInterval,
          overview: refreshInterval / 2,
          performance: refreshInterval / 3,
          realTime: 10000 // 10 seconds for real-time metrics
        });
      }

      // Subscribe to real-time updates using enterprise analytics service
      unsubscribe = enterpriseAnalyticsService.subscribe<AnalyticsDashboardData>(
        'dashboard',
        (updatedData) => {
          setDashboardData(updatedData);
          setLastRefresh(new Date());
        },
        {
          enabled: true,
          interval: refreshInterval,
          onError: (error) => {
            console.error('Real-time update error:', error);
            setError(prev => ({ 
              ...prev, 
              data: `Real-time update failed: ${error.message}` 
            }));
          },
          onSuccess: (data) => {
            setError(prev => ({ ...prev, data: null }));
            console.log('Real-time update successful');
          }
        }
      );

      // Start background refresh for cached data (if available)
      if (typeof enterpriseAnalyticsService.startBackgroundRefresh === 'function') {
        backgroundRefreshStop = enterpriseAnalyticsService.startBackgroundRefresh(refreshInterval * 2);
      }
    }

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
      if (backgroundRefreshStop) {
        backgroundRefreshStop();
      }
    };
  }, [autoRefresh, timeRange]);

  // Initial data fetch
  useEffect(() => {
    fetchAnalyticsData();
  }, [fetchAnalyticsData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Clear cache and subscriptions when component unmounts
      enterpriseAnalyticsService.clearCache();
    };
  }, []);

  // Calculate overview metrics with fallback values
  const overviewMetrics: OverviewMetrics = useMemo(() => {
    if (!dashboardData) {
      return {
        totalQueries: 0,
        totalUsers: 0,
        totalDocuments: 0,
        averageResponseTime: 0,
        successRate: 0,
        satisfactionScore: 0
      };
    }

    return {
      totalQueries: dashboardData.queries.length,
      totalUsers: dashboardData.users.length,
      totalDocuments: dashboardData.documents.length,
      averageResponseTime: dashboardData.performance.responseTime,
      successRate: 1 - dashboardData.performance.errorRate,
      satisfactionScore: dashboardData.users.reduce((sum, user) => sum + user.satisfactionScore, 0) / dashboardData.users.length || 0
    };
  }, [dashboardData]);

  // Loading component
  const LoadingSpinner = ({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) => (
    <div className={`animate-spin ${size === 'sm' ? 'w-4 h-4' : size === 'md' ? 'w-6 h-6' : 'w-8 h-8'}`}>
      <RefreshCw className="w-full h-full text-purple-500" />
    </div>
  );

  // Error component
  const ErrorMessage = ({ message, onRetry }: { message: string; onRetry: () => void }) => (
    <div className="flex items-center justify-between bg-red-900/20 border border-red-500/30 rounded-lg p-4">
      <div className="flex items-center space-x-2">
        <AlertCircle className="w-5 h-5 text-red-400" />
        <span className="text-red-300 text-sm">{message}</span>
      </div>
      <button
        onClick={onRetry}
        className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
      >
        Retry
      </button>
    </div>
  );

  return (
    <EnterpriseAuthGuard 
      requiredFeature="analytics"
      loadingMessage="Checking analytics permissions..."
      unauthorizedMessage="You need analytics permissions to view this dashboard."
    >
      <div className="p-6 bg-gray-900 text-white min-h-screen">
        <div className="max-w-7xl mx-auto">
        {/* Header with navigation */}
        <div className="mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-4">
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
                {user && (
                  <div className="flex items-center space-x-2 px-3 py-1 bg-gray-800 rounded-lg">
                    <User className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-300">{user.name}</span>
                    <Shield className="w-4 h-4 text-purple-400" />
                    <span className="text-xs text-purple-300 capitalize">{user.role}</span>
                  </div>
                )}
              </div>
              <p className="text-gray-400">
                Comprehensive analytics and insights for your enterprise system
              </p>
              {session && sessionTimeRemaining > 0 && (
                <div className="mt-2 text-xs text-gray-500">
                  Session expires in {sessionTimeRemaining} minutes
                </div>
              )}
            </div>
            
            {/* Controls */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4 mt-4 lg:mt-0">
              {/* Time Range Selector */}
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-gray-400" />
                <select
                  value={timeRange}
                  onChange={(e) => handleTimeRangeChange(e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {timeRangeOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Auto-refresh toggle */}
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4 text-purple-600 bg-gray-800 border-gray-600 rounded focus:ring-purple-500"
                />
                <span className="text-sm text-gray-300">Auto-refresh</span>
              </label>

              {/* Manual refresh button */}
              <button
                onClick={handleRefresh}
                disabled={loading.overview || loading.data}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                {loading.overview || loading.data ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                <span className="text-sm">Refresh</span>
              </button>

              {/* Export button with dropdown - only show if user has export permissions */}
              {gate.hasPermission('analytics', 'export', (
                <div className="relative group">
                  <button
                    onClick={() => handleExport('json')}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    <span className="text-sm">Export</span>
                  </button>
                  
                  {/* Export format dropdown */}
                  <div className="absolute right-0 mt-2 w-32 bg-gray-800 border border-gray-700 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                    <button
                      onClick={() => handleExport('json')}
                      className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 rounded-t-lg"
                    >
                      JSON
                    </button>
                    <button
                      onClick={() => handleExport('csv')}
                      className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700"
                    >
                      CSV
                    </button>
                    <button
                      onClick={() => handleExport('pdf')}
                      className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 rounded-b-lg"
                    >
                      PDF
                    </button>
                  </div>
                </div>
              ))}
              
              {/* Show restricted message if no export permission */}
              {gate.hasPermission('analytics', 'export', null, (
                <div className="px-4 py-2 bg-gray-800 text-gray-500 rounded-lg text-sm">
                  Export Restricted
                </div>
              ))}
            </div>
          </div>

          {/* Last refresh indicator and cache status */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 space-y-1 sm:space-y-0 text-xs text-gray-500">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-3 h-3" />
              <span>Last updated: {lastRefresh.toLocaleTimeString()}</span>
              {userId && <span>• User: {userId}</span>}
            </div>
            
            {/* Cache status */}
            <div className="flex items-center space-x-2">
              <Activity className="w-3 h-3" />
              <span>
                Cache: {enterpriseAnalyticsService.getCacheStats().size} entries
              </span>
              <span>
                • Auto-refresh: {autoRefresh ? 'On' : 'Off'}
              </span>
            </div>
          </div>
        </div>

        {/* Error handling for overview */}
        {error.overview && (
          <div className="mb-6">
            <ErrorMessage 
              message={error.overview} 
              onRetry={() => fetchAnalyticsData()} 
            />
          </div>
        )}

        {/* Overview Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Queries */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm font-medium">Total Queries</p>
                {loading.overview ? (
                  <div className="mt-2">
                    <LoadingSpinner size="md" />
                  </div>
                ) : (
                  <p className="text-2xl font-bold mt-1">
                    {overviewMetrics.totalQueries.toLocaleString()}
                  </p>
                )}
              </div>
              <div className="p-3 bg-blue-500/20 rounded-lg">
                <TrendingUp className="w-6 h-6 text-blue-400" />
              </div>
            </div>
            {!loading.overview && (
              <div className="mt-4 text-xs text-gray-500">
                {timeRange} period
              </div>
            )}
          </div>

          {/* Active Users */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm font-medium">Active Users</p>
                {loading.overview ? (
                  <div className="mt-2">
                    <LoadingSpinner size="md" />
                  </div>
                ) : (
                  <p className="text-2xl font-bold mt-1">
                    {overviewMetrics.totalUsers.toLocaleString()}
                  </p>
                )}
              </div>
              <div className="p-3 bg-green-500/20 rounded-lg">
                <Users className="w-6 h-6 text-green-400" />
              </div>
            </div>
            {!loading.overview && (
              <div className="mt-4 text-xs text-gray-500">
                Unique users in {timeRange}
              </div>
            )}
          </div>

          {/* Average Response Time */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm font-medium">Avg Response Time</p>
                {loading.overview ? (
                  <div className="mt-2">
                    <LoadingSpinner size="md" />
                  </div>
                ) : (
                  <p className="text-2xl font-bold mt-1">
                    {Math.round(overviewMetrics.averageResponseTime)}ms
                  </p>
                )}
              </div>
              <div className="p-3 bg-yellow-500/20 rounded-lg">
                <Clock className="w-6 h-6 text-yellow-400" />
              </div>
            </div>
            {!loading.overview && (
              <div className="mt-4 text-xs text-gray-500">
                System performance
              </div>
            )}
          </div>

          {/* Success Rate */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm font-medium">Success Rate</p>
                {loading.overview ? (
                  <div className="mt-2">
                    <LoadingSpinner size="md" />
                  </div>
                ) : (
                  <p className="text-2xl font-bold mt-1">
                    {(overviewMetrics.successRate * 100).toFixed(1)}%
                  </p>
                )}
              </div>
              <div className="p-3 bg-purple-500/20 rounded-lg">
                <Activity className="w-6 h-6 text-purple-400" />
              </div>
            </div>
            {!loading.overview && (
              <div className="mt-4 text-xs text-gray-500">
                Query success rate
              </div>
            )}
          </div>
        </div>

        {/* Analytics Visualization Components */}
        {dashboardData && !loading.data && !error.data && (
          <div className="space-y-8">
            {/* Analytics Overview */}
            <AnalyticsOverview
              metrics={overviewMetrics}
              loading={loading.overview}
              timeRange={timeRange}
            />

            {/* Usage Metrics */}
            <UsageMetrics
              queries={dashboardData.queries}
              users={dashboardData.users}
              trends={dashboardData.trends}
              loading={loading.charts}
              timeRange={timeRange}
            />

            {/* Performance Charts */}
            <PerformanceCharts
              performance={dashboardData.performance}
              trends={dashboardData.trends}
              loading={loading.charts}
              timeRange={timeRange}
            />

            {/* User Behavior Analytics */}
            <UserBehaviorAnalytics
              users={dashboardData.users}
              queries={dashboardData.queries}
              loading={loading.data}
              timeRange={timeRange}
            />
          </div>
        )}

        {/* Loading State */}
        {loading.data && (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {/* Error State */}
        {error.data && (
          <ErrorMessage 
            message={error.data} 
            onRetry={() => fetchAnalyticsData()} 
          />
        )}

        {/* Empty State */}
        {!dashboardData && !loading.data && !error.data && (
          <div className="text-center text-gray-500 py-16">
            <Activity className="w-16 h-16 mx-auto mb-4 text-gray-600" />
            <h3 className="text-lg font-medium text-gray-400 mb-2">No Analytics Data</h3>
            <p className="text-sm">
              No analytics data available for the selected time range.
            </p>
            <button
              onClick={fetchAnalyticsData}
              className="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              Refresh Data
            </button>
          </div>
        )}
        </div>
      </div>
    </EnterpriseAuthGuard>
  );
};

export default EnterpriseAnalyticsDashboard;