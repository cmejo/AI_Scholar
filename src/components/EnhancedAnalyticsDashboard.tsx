import {
    Activity,
    AlertTriangle,
    BarChart3,
    Brain,
    CheckCircle,
    Clock,
    Database,
    Download,
    Eye,
    FileText,
    MessageSquare,
    Network,
    RefreshCw,
    Search,
    Target,
    TrendingUp, Users,
    Zap
} from 'lucide-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { analyticsService } from '../services/analyticsService';
import {
    ExportData
} from '../types/ui';

interface AnalyticsDashboardProps {
  userId?: string;
  timeRange?: { start: Date; end: Date };
  onExport?: (data: ExportData) => void;
}

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string;
    borderWidth?: number;
  }[];
}

export const EnhancedAnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  userId,
  timeRange: _initialTimeRange,
  onExport
}) => {
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d' | '90d'>('7d');
  const [loading, setLoading] = useState(true);
  const [realTimeMetrics, setRealTimeMetrics] = useState<any>({});
  const [selectedMetric, setSelectedMetric] = useState<string>('overview');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval] = useState(30000); // 30 seconds
  const intervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    loadAnalytics();
    if (autoRefresh) {
      startAutoRefresh();
    }
    return () => stopAutoRefresh();
  }, [timeRange, userId, autoRefresh, loadAnalytics, startAutoRefresh, stopAutoRefresh]);

  const loadRealTimeMetrics = useCallback(async () => {
    try {
      // Simulate real-time metrics API call
      const metrics = {
        activeUsers: Math.floor(Math.random() * 50) + 10,
        queriesPerMinute: Math.floor(Math.random() * 20) + 5,
        avgResponseTime: Math.random() * 2000 + 500,
        systemLoad: Math.random() * 100,
        errorRate: Math.random() * 5,
        cacheHitRate: Math.random() * 30 + 70
      };
      setRealTimeMetrics(metrics);
    } catch (error) {
      console.error('Failed to load real-time metrics:', error);
    }
  }, []);

  const stopAutoRefresh = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  }, []);

  const startAutoRefresh = useCallback(() => {
    stopAutoRefresh();
    intervalRef.current = setInterval(() => {
      loadRealTimeMetrics();
    }, refreshInterval);
  }, [refreshInterval, loadRealTimeMetrics, stopAutoRefresh]);

  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const endDate = new Date();
      const startDate = new Date();
      
      switch (timeRange) {
        case '1h':
          startDate.setHours(startDate.getHours() - 1);
          break;
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
      
      await loadRealTimeMetrics();
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange, loadRealTimeMetrics]);



  const exportData = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      timeRange,
      userId,
      analytics: analyticsData,
      realTimeMetrics
    };
    
    if (onExport) {
      onExport(exportData);
    } else {
      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `analytics_${timeRange}_${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);
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
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Enhanced Analytics Dashboard</h2>
          <p className="text-gray-400">Comprehensive insights and real-time monitoring</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
              autoRefresh ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-600 hover:bg-gray-700'
            }`}
          >
            <RefreshCw size={16} className={autoRefresh ? 'animate-spin' : ''} />
            <span className="text-sm">Auto Refresh</span>
          </button>
          
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
          
          <button
            onClick={exportData}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Download size={16} />
            <span className="text-sm">Export</span>
          </button>
        </div>
      </div>

      {/* Real-time Metrics Bar */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
          <Zap className="text-yellow-400 mr-2" size={20} />
          Real-time Metrics
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <RealTimeMetric
            label="Active Users"
            value={realTimeMetrics.activeUsers || 0}
            icon={<Users size={16} />}
            color="text-blue-400"
          />
          <RealTimeMetric
            label="Queries/Min"
            value={realTimeMetrics.queriesPerMinute || 0}
            icon={<MessageSquare size={16} />}
            color="text-green-400"
          />
          <RealTimeMetric
            label="Avg Response"
            value={`${Math.round(realTimeMetrics.avgResponseTime || 0)}ms`}
            icon={<Clock size={16} />}
            color="text-yellow-400"
          />
          <RealTimeMetric
            label="System Load"
            value={`${Math.round(realTimeMetrics.systemLoad || 0)}%`}
            icon={<Activity size={16} />}
            color="text-purple-400"
          />
          <RealTimeMetric
            label="Error Rate"
            value={`${(realTimeMetrics.errorRate || 0).toFixed(1)}%`}
            icon={<AlertTriangle size={16} />}
            color="text-red-400"
          />
          <RealTimeMetric
            label="Cache Hit"
            value={`${Math.round(realTimeMetrics.cacheHitRate || 0)}%`}
            icon={<Database size={16} />}
            color="text-emerald-400"
          />
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-1 bg-gray-800 rounded-lg p-1">
        {[
          { id: 'overview', label: 'Overview', icon: <BarChart3 size={16} /> },
          { id: 'queries', label: 'Queries', icon: <Search size={16} /> },
          { id: 'documents', label: 'Documents', icon: <FileText size={16} /> },
          { id: 'users', label: 'Users', icon: <Users size={16} /> },
          { id: 'knowledge', label: 'Knowledge Graph', icon: <Network size={16} /> },
          { id: 'performance', label: 'Performance', icon: <Target size={16} /> }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedMetric(tab.id)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
              selectedMetric === tab.id
                ? 'bg-purple-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            {tab.icon}
            <span className="text-sm">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Content based on selected metric */}
      {selectedMetric === 'overview' && (
        <OverviewDashboard 
          analyticsData={analyticsData}
          queryInsights={queryInsights}
          documentInsights={documentInsights}
          userInsights={userInsights}
          knowledgeGaps={knowledgeGaps}
        />
      )}

      {selectedMetric === 'queries' && (
        <QueryAnalyticsDashboard 
          queryInsights={queryInsights}
          analyticsData={analyticsData}
        />
      )}

      {selectedMetric === 'documents' && (
        <DocumentAnalyticsDashboard 
          documentInsights={documentInsights}
          analyticsData={analyticsData}
        />
      )}

      {selectedMetric === 'users' && (
        <UserAnalyticsDashboard 
          userInsights={userInsights}
          analyticsData={analyticsData}
        />
      )}

      {selectedMetric === 'knowledge' && (
        <KnowledgeGraphDashboard 
          analyticsData={analyticsData}
        />
      )}

      {selectedMetric === 'performance' && (
        <PerformanceDashboard 
          analyticsData={analyticsData}
          realTimeMetrics={realTimeMetrics}
        />
      )}
    </div>
  );
};

// Real-time Metric Component
interface RealTimeMetricProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

const RealTimeMetric: React.FC<RealTimeMetricProps> = ({ label, value, icon, color }) => (
  <div className="text-center">
    <div className={`flex items-center justify-center mb-1 ${color}`}>
      {icon}
    </div>
    <div className="text-lg font-bold text-white">{value}</div>
    <div className="text-xs text-gray-400">{label}</div>
  </div>
);

// Overview Dashboard Component
interface OverviewDashboardProps {
  analyticsData: AnalyticsDashboardData;
  queryInsights: {
    mostCommonQueries: QueryAnalytics[];
    averageResponseTime: number;
    totalQueries: number;
  };
  documentInsights: {
    mostReferencedDocuments: DocumentAnalytics[];
    totalDocuments: number;
  };
  userInsights: {
    activeUsers: UserAnalytics[];
    totalUsers: number;
  };
  knowledgeGaps: {
    unansweredQueries: { query: string; frequency: number }[];
    lowConfidenceAreas: string[];
  };
}

const OverviewDashboard: React.FC<OverviewDashboardProps> = ({
  analyticsData,
  queryInsights,
  documentInsights,
  userInsights,
  knowledgeGaps
}) => (
  <div className="space-y-6">
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
        value={`${((queryInsights?.successRate || 0) * 100).toFixed(1)}%`}
        change={5}
        icon={<CheckCircle className="text-emerald-400" size={24} />}
      />
      <MetricCard
        title="Avg Response Time"
        value={`${(queryInsights?.averageResponseTime || 0).toFixed(0)}ms`}
        change={-8}
        icon={<Clock className="text-yellow-400" size={24} />}
      />
      <MetricCard
        title="Active Users"
        value={userInsights?.activeUsers || 0}
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
        <InteractiveChart
          type="line"
          data={generateQueryVolumeData()}
          height={250}
        />
      </div>

      {/* Response Time Distribution */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <BarChart3 className="text-emerald-400 mr-2" size={20} />
          Response Time Distribution
        </h3>
        <InteractiveChart
          type="bar"
          data={generateResponseTimeData()}
          height={250}
        />
      </div>
    </div>

    {/* Document and User Insights */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Most Referenced Documents */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <FileText className="text-emerald-400 mr-2" size={20} />
          Most Referenced Documents
        </h3>
        <div className="space-y-3">
          {(documentInsights?.mostReferencedDocuments || []).slice(0, 5).map((doc: DocumentAnalytics, index: number) => (
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
          {(knowledgeGaps?.unansweredQueries || []).slice(0, 5).map((query: { query: string; frequency: number }, index: number) => (
            <div key={index} className="flex items-center justify-between">
              <span className="text-gray-300 truncate flex-1">{query.query}</span>
              <span className="text-yellow-400 font-medium ml-2">{query.frequency}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

// Query Analytics Dashboard
interface QueryAnalyticsDashboardProps {
  queryInsights: {
    mostCommonQueries: QueryAnalytics[];
    averageResponseTime: number;
    totalQueries: number;
    successRate: number;
  };
  analyticsData: AnalyticsDashboardData;
}

const QueryAnalyticsDashboard: React.FC<QueryAnalyticsDashboardProps> = ({
  queryInsights,
  analyticsData
}) => (
  <div className="space-y-6">
    {/* Query Metrics */}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <MetricCard
        title="Total Queries"
        value={analyticsData?.queries?.length || 0}
        change={8}
        icon={<MessageSquare className="text-blue-400" size={24} />}
      />
      <MetricCard
        title="Success Rate"
        value={`${(queryInsights.successRate * 100).toFixed(1)}%`}
        change={3}
        icon={<CheckCircle className="text-emerald-400" size={24} />}
      />
      <MetricCard
        title="Avg Response Time"
        value={`${queryInsights.averageResponseTime.toFixed(0)}ms`}
        change={-12}
        icon={<Clock className="text-yellow-400" size={24} />}
      />
    </div>

    {/* Query Analysis Charts */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Query Intent Distribution */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Query Intent Distribution</h3>
        <InteractiveChart
          type="doughnut"
          data={generateIntentDistributionData(queryInsights.topIntents)}
          height={300}
        />
      </div>

      {/* Query Complexity Over Time */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Query Complexity Trends</h3>
        <InteractiveChart
          type="line"
          data={generateComplexityTrendData()}
          height={300}
        />
      </div>
    </div>

    {/* Top Queries Table */}
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Most Common Queries</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="pb-3 text-gray-400">Query</th>
              <th className="pb-3 text-gray-400">Count</th>
              <th className="pb-3 text-gray-400">Success Rate</th>
              <th className="pb-3 text-gray-400">Avg Response Time</th>
            </tr>
          </thead>
          <tbody>
            {queryInsights.mostCommonQueries.slice(0, 10).map((query: QueryAnalytics, index: number) => (
              <tr key={index} className="border-b border-gray-700">
                <td className="py-3 text-gray-300 max-w-xs truncate">{query.query}</td>
                <td className="py-3 text-blue-400">{query.count}</td>
                <td className="py-3 text-emerald-400">95%</td>
                <td className="py-3 text-yellow-400">1.2s</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

// Document Analytics Dashboard
interface DocumentAnalyticsDashboardProps {
  documentInsights: {
    mostReferencedDocuments: DocumentAnalytics[];
    totalDocuments: number;
    averageRelevance: number;
  };
  analyticsData: AnalyticsDashboardData;
}

const DocumentAnalyticsDashboard: React.FC<DocumentAnalyticsDashboardProps> = ({
  documentInsights,
  analyticsData
}) => (
  <div className="space-y-6">
    {/* Document Metrics */}
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <MetricCard
        title="Total Documents"
        value={analyticsData?.documents?.length || 0}
        change={5}
        icon={<FileText className="text-blue-400" size={24} />}
      />
      <MetricCard
        title="Most Referenced"
        value={documentInsights.mostReferencedDocuments[0]?.references || 0}
        change={15}
        icon={<Eye className="text-emerald-400" size={24} />}
      />
      <MetricCard
        title="Avg Effectiveness"
        value="87%"
        change={3}
        icon={<Target className="text-yellow-400" size={24} />}
      />
      <MetricCard
        title="Upload Rate"
        value="12/day"
        change={8}
        icon={<TrendingUp className="text-purple-400" size={24} />}
      />
    </div>

    {/* Document Analysis Charts */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Document Usage Heatmap */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Document Usage Heatmap</h3>
        <DocumentHeatmap documents={documentInsights.mostReferencedDocuments} />
      </div>

      {/* Document Type Distribution */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Document Type Distribution</h3>
        <InteractiveChart
          type="pie"
          data={generateDocumentTypeData()}
          height={300}
        />
      </div>
    </div>

    {/* Document Relationship Map */}
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
        <Network className="text-purple-400 mr-2" size={20} />
        Document Relationship Map
      </h3>
      <DocumentRelationshipMap documents={analyticsData?.documents || []} />
    </div>
  </div>
);

// User Analytics Dashboard
interface UserAnalyticsDashboardProps {
  userInsights: {
    activeUsers: UserAnalytics[];
    totalUsers: number;
    averageSessionTime: number;
  };
  analyticsData: AnalyticsDashboardData;
}

const UserAnalyticsDashboard: React.FC<UserAnalyticsDashboardProps> = ({
  userInsights,
  analyticsData: _analyticsData
}) => (
  <div className="space-y-6">
    {/* User Metrics */}
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <MetricCard
        title="Active Users"
        value={userInsights.activeUsers}
        change={12}
        icon={<Users className="text-blue-400" size={24} />}
      />
      <MetricCard
        title="Avg Session"
        value={`${userInsights.averageSessionLength.toFixed(1)}m`}
        change={-5}
        icon={<Clock className="text-emerald-400" size={24} />}
      />
      <MetricCard
        title="Retention Rate"
        value={`${(userInsights.userRetention * 100).toFixed(1)}%`}
        change={8}
        icon={<TrendingUp className="text-yellow-400" size={24} />}
      />
      <MetricCard
        title="Satisfaction"
        value="4.2/5"
        change={3}
        icon={<CheckCircle className="text-purple-400" size={24} />}
      />
    </div>

    {/* User Behavior Charts */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* User Activity Timeline */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">User Activity Timeline</h3>
        <InteractiveChart
          type="line"
          data={generateUserActivityData()}
          height={300}
        />
      </div>

      {/* Feature Usage */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Feature Usage</h3>
        <InteractiveChart
          type="bar"
          data={generateFeatureUsageData()}
          height={300}
        />
      </div>
    </div>

    {/* User Engagement Metrics */}
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">User Engagement Metrics</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="text-center">
          <div className="text-3xl font-bold text-blue-400 mb-2">{userInsights.activeUsers}</div>
          <div className="text-gray-400">Daily Active Users</div>
          <div className="text-sm text-emerald-400 mt-1">+12% from last week</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-emerald-400 mb-2">{userInsights.averageSessionLength.toFixed(1)}m</div>
          <div className="text-gray-400">Avg Session Length</div>
          <div className="text-sm text-red-400 mt-1">-5% from last week</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-yellow-400 mb-2">{(userInsights.userRetention * 100).toFixed(1)}%</div>
          <div className="text-gray-400">User Retention</div>
          <div className="text-sm text-emerald-400 mt-1">+8% from last week</div>
        </div>
      </div>
    </div>
  </div>
);

// Knowledge Graph Dashboard
interface KnowledgeGraphDashboardProps {
  analyticsData: AnalyticsDashboardData;
}

const KnowledgeGraphDashboard: React.FC<KnowledgeGraphDashboardProps> = ({
  analyticsData: _analyticsData
}) => (
  <div className="space-y-6">
    {/* Knowledge Graph Metrics */}
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <MetricCard
        title="Total Entities"
        value="1,247"
        change={18}
        icon={<Network className="text-blue-400" size={24} />}
      />
      <MetricCard
        title="Relationships"
        value="3,891"
        change={25}
        icon={<Brain className="text-emerald-400" size={24} />}
      />
      <MetricCard
        title="Graph Density"
        value="0.73"
        change={5}
        icon={<Activity className="text-yellow-400" size={24} />}
      />
      <MetricCard
        title="Query Coverage"
        value="89%"
        change={12}
        icon={<Target className="text-purple-400" size={24} />}
      />
    </div>

    {/* Knowledge Graph Visualization */}
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
        <Network className="text-purple-400 mr-2" size={20} />
        Knowledge Graph Overview
      </h3>
      <KnowledgeGraphVisualization />
    </div>

    {/* Entity and Relationship Analytics */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Top Entities */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Most Connected Entities</h3>
        <div className="space-y-3">
          {generateTopEntities().map((entity, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${entity.color}`}></div>
                <span className="text-gray-300">{entity.name}</span>
              </div>
              <span className="text-blue-400 font-medium">{entity.connections}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Relationship Types */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Relationship Distribution</h3>
        <InteractiveChart
          type="doughnut"
          data={generateRelationshipTypeData()}
          height={250}
        />
      </div>
    </div>
  </div>
);

// Performance Dashboard
interface PerformanceDashboardProps {
  analyticsData: AnalyticsDashboardData;
  realTimeMetrics: {
    currentUsers: number;
    queriesPerMinute: number;
    averageResponseTime: number;
    errorRate: number;
    systemLoad: number;
  };
}

const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  analyticsData: _analyticsData,
  realTimeMetrics
}) => (
  <div className="space-y-6">
    {/* Performance Metrics */}
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <MetricCard
        title="Avg Response Time"
        value={`${Math.round(realTimeMetrics.avgResponseTime || 0)}ms`}
        change={-8}
        icon={<Clock className="text-blue-400" size={24} />}
      />
      <MetricCard
        title="Throughput"
        value="156 req/min"
        change={12}
        icon={<Activity className="text-emerald-400" size={24} />}
      />
      <MetricCard
        title="Error Rate"
        value={`${(realTimeMetrics.errorRate || 0).toFixed(1)}%`}
        change={-15}
        icon={<AlertTriangle className="text-yellow-400" size={24} />}
      />
      <MetricCard
        title="Cache Hit Rate"
        value={`${Math.round(realTimeMetrics.cacheHitRate || 0)}%`}
        change={5}
        icon={<Database className="text-purple-400" size={24} />}
      />
    </div>

    {/* Performance Charts */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Response Time Trend */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Response Time Trend</h3>
        <InteractiveChart
          type="line"
          data={generateResponseTimeTrendData()}
          height={300}
        />
      </div>

      {/* System Resource Usage */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">System Resources</h3>
        <SystemResourceMonitor realTimeMetrics={realTimeMetrics} />
      </div>
    </div>

    {/* Performance Alerts */}
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
        <AlertTriangle className="text-yellow-400 mr-2" size={20} />
        Performance Alerts
      </h3>
      <PerformanceAlerts />
    </div>
  </div>
);

// Supporting Components

// Metric Card Component
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

// Interactive Chart Component
interface InteractiveChartProps {
  type: 'line' | 'bar' | 'pie' | 'doughnut';
  data: ChartData;
  height: number;
}

const InteractiveChart: React.FC<InteractiveChartProps> = ({ type, data, height }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) {
        // Clear canvas
        ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
        
        // Simple chart rendering (placeholder)
        renderSimpleChart(ctx, type, data, canvasRef.current.width, height);
      }
    }
  }, [type, data, height]);

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={400}
        height={height}
        className="w-full"
        style={{ height: `${height}px` }}
      />
    </div>
  );
};

// Simple chart rendering function
const renderSimpleChart = (
  ctx: CanvasRenderingContext2D,
  type: string,
  data: ChartData,
  width: number,
  height: number
) => {
  const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];
  
  if (type === 'line') {
    // Simple line chart
    const dataset = data.datasets[0];
    const values = dataset.data;
    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min || 1;
    
    ctx.strokeStyle = dataset.borderColor || colors[0];
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    values.forEach((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    ctx.stroke();
  } else if (type === 'bar') {
    // Simple bar chart
    const dataset = data.datasets[0];
    const values = dataset.data;
    const max = Math.max(...values);
    const barWidth = width / values.length * 0.8;
    const barSpacing = width / values.length * 0.2;
    
    values.forEach((value, index) => {
      const barHeight = (value / max) * height;
      const x = index * (barWidth + barSpacing) + barSpacing / 2;
      const y = height - barHeight;
      
      ctx.fillStyle = Array.isArray(dataset.backgroundColor) 
        ? dataset.backgroundColor[index] || colors[index % colors.length]
        : dataset.backgroundColor || colors[0];
      
      ctx.fillRect(x, y, barWidth, barHeight);
    });
  } else if (type === 'pie' || type === 'doughnut') {
    // Simple pie/doughnut chart
    const dataset = data.datasets[0];
    const values = dataset.data;
    const total = values.reduce((sum, value) => sum + value, 0);
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 20;
    const innerRadius = type === 'doughnut' ? radius * 0.5 : 0;
    
    let currentAngle = -Math.PI / 2;
    
    values.forEach((value, index) => {
      const sliceAngle = (value / total) * 2 * Math.PI;
      
      ctx.fillStyle = Array.isArray(dataset.backgroundColor)
        ? dataset.backgroundColor[index] || colors[index % colors.length]
        : colors[index % colors.length];
      
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
      if (innerRadius > 0) {
        ctx.arc(centerX, centerY, innerRadius, currentAngle + sliceAngle, currentAngle, true);
      } else {
        ctx.lineTo(centerX, centerY);
      }
      ctx.closePath();
      ctx.fill();
      
      currentAngle += sliceAngle;
    });
  }
};

// Document Heatmap Component
interface DocumentHeatmapProps {
  documents: DocumentAnalytics[];
}

const DocumentHeatmap: React.FC<DocumentHeatmapProps> = ({ documents }) => {
  const maxReferences = Math.max(...documents.map(doc => doc.references));
  
  return (
    <div className="grid grid-cols-8 gap-1">
      {documents.slice(0, 64).map((doc, index) => {
        const intensity = doc.references / maxReferences;
        const opacity = Math.max(0.1, intensity);
        
        return (
          <div
            key={index}
            className="aspect-square rounded-sm bg-blue-500 hover:bg-blue-400 transition-colors cursor-pointer"
            style={{ opacity }}
            title={`${doc.documentId}: ${doc.references} references`}
          />
        );
      })}
    </div>
  );
};

// Document Relationship Map Component
interface DocumentRelationshipMapProps {
  documents: KnowledgeGraphDocument[];
}

const DocumentRelationshipMap: React.FC<DocumentRelationshipMapProps> = ({ documents }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  
  const renderRelationshipMap = useCallback(() => {
    // Simple network visualization
    const svg = svgRef.current;
    if (!svg) return;
    
    svg.innerHTML = '';
    const width = 600;
    const height = 300;
    
    // Generate positions for documents
    const positions = documents.slice(0, 20).map(() => ({
      x: Math.random() * (width - 40) + 20,
      y: Math.random() * (height - 40) + 20
    }));
    
    // Draw connections
    for (let i = 0; i < positions.length; i++) {
      for (let j = i + 1; j < positions.length; j++) {
        if (Math.random() > 0.7) { // 30% chance of connection
          const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
          line.setAttribute('x1', positions[i].x.toString());
          line.setAttribute('y1', positions[i].y.toString());
          line.setAttribute('x2', positions[j].x.toString());
          line.setAttribute('y2', positions[j].y.toString());
          line.setAttribute('stroke', '#6B7280');
          line.setAttribute('stroke-width', '1');
          line.setAttribute('opacity', '0.5');
          svg.appendChild(line);
        }
      }
    }
    
    // Draw nodes
    positions.forEach((pos) => {
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', pos.x.toString());
      circle.setAttribute('cy', pos.y.toString());
      circle.setAttribute('r', '6');
      circle.setAttribute('fill', '#3B82F6');
      circle.setAttribute('stroke', '#1E40AF');
      circle.setAttribute('stroke-width', '2');
      svg.appendChild(circle);
    });
  }, [documents]);

  useEffect(() => {
    if (svgRef.current && documents.length > 0) {
      renderRelationshipMap();
    }
  }, [documents, renderRelationshipMap]);
  
  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <svg ref={svgRef} width="100%" height="300" viewBox="0 0 600 300" />
    </div>
  );
};

// Knowledge Graph Visualization Component
const KnowledgeGraphVisualization: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null);
  
  useEffect(() => {
    renderKnowledgeGraph();
  }, []);
  
  const renderKnowledgeGraph = () => {
    const svg = svgRef.current;
    if (!svg) return;
    
    svg.innerHTML = '';
    const _width = 800;
    const _height = 400;
    
    // Generate sample nodes and edges
    const nodes = [
      { id: 'ai', x: 400, y: 200, type: 'concept', label: 'Artificial Intelligence' },
      { id: 'ml', x: 300, y: 150, type: 'concept', label: 'Machine Learning' },
      { id: 'dl', x: 500, y: 150, type: 'concept', label: 'Deep Learning' },
      { id: 'nlp', x: 250, y: 250, type: 'concept', label: 'NLP' },
      { id: 'cv', x: 550, y: 250, type: 'concept', label: 'Computer Vision' },
      { id: 'doc1', x: 200, y: 100, type: 'document', label: 'AI Research Paper' },
      { id: 'doc2', x: 600, y: 100, type: 'document', label: 'ML Tutorial' }
    ];
    
    const edges = [
      { source: 'ai', target: 'ml' },
      { source: 'ai', target: 'dl' },
      { source: 'ml', target: 'nlp' },
      { source: 'dl', target: 'cv' },
      { source: 'doc1', target: 'ai' },
      { source: 'doc2', target: 'ml' }
    ];
    
    // Draw edges
    edges.forEach(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);
      
      if (sourceNode && targetNode) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', sourceNode.x.toString());
        line.setAttribute('y1', sourceNode.y.toString());
        line.setAttribute('x2', targetNode.x.toString());
        line.setAttribute('y2', targetNode.y.toString());
        line.setAttribute('stroke', '#6B7280');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('opacity', '0.6');
        svg.appendChild(line);
      }
    });
    
    // Draw nodes
    nodes.forEach(node => {
      const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', node.x.toString());
      circle.setAttribute('cy', node.y.toString());
      circle.setAttribute('r', node.type === 'document' ? '12' : '16');
      circle.setAttribute('fill', node.type === 'document' ? '#3B82F6' : '#10B981');
      circle.setAttribute('stroke', '#FFFFFF');
      circle.setAttribute('stroke-width', '2');
      
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', node.x.toString());
      text.setAttribute('y', (node.y + 30).toString());
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('fill', '#FFFFFF');
      text.setAttribute('font-size', '12');
      text.textContent = node.label;
      
      group.appendChild(circle);
      group.appendChild(text);
      svg.appendChild(group);
    });
  };
  
  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <svg ref={svgRef} width="100%" height="400" viewBox="0 0 800 400" />
    </div>
  );
};

// System Resource Monitor Component
interface SystemResourceMonitorProps {
  realTimeMetrics: {
    currentUsers: number;
    queriesPerMinute: number;
    averageResponseTime: number;
    errorRate: number;
    systemLoad: number;
    memoryUsage: number;
    cpuUsage: number;
  };
}

const SystemResourceMonitor: React.FC<SystemResourceMonitorProps> = ({ realTimeMetrics }) => {
  const resources = [
    { name: 'CPU Usage', value: realTimeMetrics.systemLoad || 0, max: 100, color: 'bg-blue-500' },
    { name: 'Memory Usage', value: 65, max: 100, color: 'bg-emerald-500' },
    { name: 'Disk I/O', value: 23, max: 100, color: 'bg-yellow-500' },
    { name: 'Network', value: 45, max: 100, color: 'bg-purple-500' }
  ];
  
  return (
    <div className="space-y-4">
      {resources.map((resource, index) => (
        <div key={index}>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-400">{resource.name}</span>
            <span className="text-white">{Math.round(resource.value)}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className={`${resource.color} h-2 rounded-full transition-all duration-300`}
              style={{ width: `${(resource.value / resource.max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

// Performance Alerts Component
const PerformanceAlerts: React.FC = () => {
  const alerts = [
    { type: 'warning', message: 'Response time increased by 15% in the last hour', time: '5 min ago' },
    { type: 'info', message: 'Cache hit rate improved to 85%', time: '12 min ago' },
    { type: 'error', message: 'High error rate detected in query processing', time: '25 min ago' }
  ];
  
  return (
    <div className="space-y-3">
      {alerts.map((alert, index) => (
        <div key={index} className={`flex items-start space-x-3 p-3 rounded-lg ${
          alert.type === 'error' ? 'bg-red-900/20 border border-red-500/30' :
          alert.type === 'warning' ? 'bg-yellow-900/20 border border-yellow-500/30' :
          'bg-blue-900/20 border border-blue-500/30'
        }`}>
          <div className={`mt-0.5 ${
            alert.type === 'error' ? 'text-red-400' :
            alert.type === 'warning' ? 'text-yellow-400' :
            'text-blue-400'
          }`}>
            <AlertTriangle size={16} />
          </div>
          <div className="flex-1">
            <p className="text-white text-sm">{alert.message}</p>
            <p className="text-gray-400 text-xs mt-1">{alert.time}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

// Data generation functions
const generateQueryVolumeData = (): ChartData => ({
  labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  datasets: [{
    label: 'Queries',
    data: [120, 190, 300, 500, 200, 300, 450],
    borderColor: '#3B82F6',
    backgroundColor: 'rgba(59, 130, 246, 0.1)'
  }]
});

const generateResponseTimeData = (): ChartData => ({
  labels: ['<500ms', '500-1s', '1-2s', '2-5s', '>5s'],
  datasets: [{
    label: 'Queries',
    data: [450, 320, 180, 90, 20],
    backgroundColor: ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6']
  }]
});

const generateIntentDistributionData = (intents: { intent: string; count: number }[]): ChartData => ({
  labels: intents.map(i => i.intent),
  datasets: [{
    label: 'Intent Distribution',
    data: intents.map(i => i.count),
    backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
  }]
});

const generateComplexityTrendData = (): ChartData => ({
  labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
  datasets: [
    {
      label: 'Simple',
      data: [40, 35, 30, 25],
      borderColor: '#10B981'
    },
    {
      label: 'Medium',
      data: [45, 50, 55, 60],
      borderColor: '#F59E0B'
    },
    {
      label: 'Complex',
      data: [15, 15, 15, 15],
      borderColor: '#EF4444'
    }
  ]
});

const generateDocumentTypeData = (): ChartData => ({
  labels: ['PDF', 'Word', 'Text', 'Code', 'Other'],
  datasets: [{
    label: 'Document Types',
    data: [45, 25, 15, 10, 5],
    backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
  }]
});

const generateUserActivityData = (): ChartData => ({
  labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
  datasets: [{
    label: 'Active Users',
    data: [5, 2, 15, 25, 30, 20],
    borderColor: '#3B82F6',
    backgroundColor: 'rgba(59, 130, 246, 0.1)'
  }]
});

const generateFeatureUsageData = (): ChartData => ({
  labels: ['Search', 'Chat', 'Upload', 'Analytics', 'Settings'],
  datasets: [{
    label: 'Usage Count',
    data: [850, 650, 200, 150, 80],
    backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
  }]
});

const generateResponseTimeTrendData = (): ChartData => ({
  labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
  datasets: [{
    label: 'Response Time (ms)',
    data: [800, 600, 1200, 1500, 1800, 1000],
    borderColor: '#F59E0B',
    backgroundColor: 'rgba(245, 158, 11, 0.1)'
  }]
});

const generateTopEntities = () => [
  { name: 'Machine Learning', connections: 45, color: 'bg-blue-500' },
  { name: 'Neural Networks', connections: 38, color: 'bg-emerald-500' },
  { name: 'Deep Learning', connections: 32, color: 'bg-yellow-500' },
  { name: 'AI Ethics', connections: 28, color: 'bg-purple-500' },
  { name: 'Computer Vision', connections: 25, color: 'bg-red-500' }
];

const generateRelationshipTypeData = (): ChartData => ({
  labels: ['Related To', 'Part Of', 'Mentions', 'Similar To', 'Depends On'],
  datasets: [{
    label: 'Relationship Types',
    data: [35, 25, 20, 15, 5],
    backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
  }]
});