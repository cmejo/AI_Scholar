import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, FileText, Clock, AlertTriangle, CheckCircle, Activity } from 'lucide-react';
import { analyticsService } from '../services/analyticsService';

export const EnterpriseAnalyticsDashboard: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | '90d'>('7d');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const endDate = new Date();
      const startDate = new Date();
      
      switch (timeRange) {
        case '24h':
          startDate.setHours(startDate.getHours() - 24);
          break;
        case '7d':
          startDate.setDate(startDate.getDate() - 7);
          break;
        case '30d':
          startDate.setDate(startDate.getDate() - 30);
          break;
        case '90d':
          startDate.setDate(startDate.getDate() - 90);
          break;
      }

      const data = analyticsService.getDashboardData({ start: startDate, end: endDate });
      setAnalyticsData(data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  const queryInsights = analyticsService.getQueryInsights();
  const documentInsights = analyticsService.getDocumentInsights();
  const userInsights = analyticsService.getUserInsights();
  const knowledgeGaps = analyticsService.identifyKnowledgeGaps();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Enterprise Analytics</h2>
          <p className="text-gray-400">Comprehensive insights into your RAG system performance</p>
        </div>
        
        <div className="flex items-center space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Queries"
          value={analyticsData?.queries?.length || 0}
          change={12}
          icon={<Activity className="text-blue-400" size={24} />}
        />
        <MetricCard
          title="Success Rate"
          value={`${(queryInsights.successRate * 100).toFixed(1)}%`}
          change={5}
          icon={<CheckCircle className="text-emerald-400" size={24} />}
        />
        <MetricCard
          title="Avg Response Time"
          value={`${queryInsights.averageResponseTime.toFixed(0)}ms`}
          change={-8}
          icon={<Clock className="text-yellow-400" size={24} />}
        />
        <MetricCard
          title="Active Users"
          value={userInsights.activeUsers}
          change={15}
          icon={<Users className="text-purple-400" size={24} />}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Query Volume Trend */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <TrendingUp className="text-blue-400 mr-2" size={20} />
            Query Volume Trend
          </h3>
          <div className="h-64 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <BarChart3 size={48} className="mx-auto mb-2 opacity-50" />
              <p>Query volume visualization would appear here</p>
              <p className="text-sm">Showing {timeRange} data</p>
            </div>
          </div>
        </div>

        {/* Top Queries */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Most Common Queries</h3>
          <div className="space-y-3">
            {queryInsights.mostCommonQueries.slice(0, 5).map((query, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-gray-300 truncate flex-1">{query.query}</span>
                <span className="text-blue-400 font-medium ml-2">{query.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Document Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Most Referenced Documents */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <FileText className="text-emerald-400 mr-2" size={20} />
            Most Referenced Documents
          </h3>
          <div className="space-y-3">
            {documentInsights.mostReferencedDocuments.slice(0, 5).map((doc, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-gray-300 truncate flex-1">{doc.documentId}</span>
                <span className="text-emerald-400 font-medium ml-2">{doc.references}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Knowledge Gaps */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <AlertTriangle className="text-yellow-400 mr-2" size={20} />
            Knowledge Gaps
          </h3>
          <div className="space-y-3">
            {knowledgeGaps.unansweredQueries.slice(0, 5).map((query, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-gray-300 truncate flex-1">{query.query}</span>
                <span className="text-yellow-400 font-medium ml-2">{query.frequency}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* User Behavior */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Users className="text-purple-400 mr-2" size={20} />
          User Behavior Insights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">{userInsights.activeUsers}</div>
            <div className="text-gray-400">Active Users</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">{userInsights.averageSessionLength.toFixed(1)}m</div>
            <div className="text-gray-400">Avg Session Length</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-400">{(userInsights.userRetention * 100).toFixed(1)}%</div>
            <div className="text-gray-400">User Retention</div>
          </div>
        </div>
      </div>

      {/* Intent Analysis */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Query Intent Distribution</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {queryInsights.topIntents.map((intent, index) => (
            <div key={index} className="text-center">
              <div className="text-xl font-bold text-blue-400">{intent.count}</div>
              <div className="text-gray-400 capitalize text-sm">{intent.intent}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Satisfaction Score */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">User Satisfaction</h3>
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Overall Satisfaction</span>
              <span className="text-white font-medium">{(queryInsights.satisfactionScore * 100).toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-red-500 via-yellow-500 to-emerald-500 h-2 rounded-full"
                style={{ width: `${queryInsights.satisfactionScore * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

interface MetricCardProps {
  title: string;
  value: string | number;
  change: number;
  icon: React.ReactNode;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon }) => {
  const isPositive = change > 0;
  
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          <div className="flex items-center mt-1">
            <span className={`text-sm ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
              {isPositive ? '+' : ''}{change}%
            </span>
            <span className="text-gray-400 text-sm ml-1">vs last period</span>
          </div>
        </div>
        <div className="p-3 bg-gray-700 rounded-lg">
          {icon}
        </div>
      </div>
    </div>
  );
};