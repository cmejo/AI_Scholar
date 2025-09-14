/**
 * PerformanceAnalyzer - Advanced performance analysis and optimization tools
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  Cpu,
  HardDrive,
  Wifi,
  AlertTriangle,
  CheckCircle,
  Settings,
  RefreshCw,
  Download,
  Calendar,
  Filter,
  Search,
  Zap,
  Target,
  Gauge,
  LineChart,
  PieChart
} from 'lucide-react';

export interface PerformanceAnalyzerProps {
  timeRange?: '1h' | '24h' | '7d' | '30d';
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface PerformanceMetric {
  id: string;
  name: string;
  category: 'response_time' | 'throughput' | 'resource_usage' | 'error_rate';
  value: number;
  unit: string;
  threshold: {
    warning: number;
    critical: number;
  };
  trend: 'up' | 'down' | 'stable';
  trendPercentage: number;
  history: Array<{
    timestamp: Date;
    value: number;
  }>;
}

interface PerformanceAlert {
  id: string;
  metric: string;
  severity: 'warning' | 'critical' | 'info';
  message: string;
  timestamp: Date;
  acknowledged: boolean;
  recommendation?: string;
}

interface PerformanceInsight {
  id: string;
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  category: 'optimization' | 'bottleneck' | 'resource' | 'configuration';
  recommendation: string;
  estimatedImprovement: string;
}

export const PerformanceAnalyzer: React.FC<PerformanceAnalyzerProps> = ({
  timeRange = '24h',
  autoRefresh = true,
  refreshInterval = 60000
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [insights, setInsights] = useState<PerformanceInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showAlerts, setShowAlerts] = useState(true);
  const [showInsights, setShowInsights] = useState(true);

  // Load performance data
  const loadPerformanceData = useCallback(async () => {
    try {
      setLoading(true);
      const [metricsData, alertsData, insightsData] = await Promise.all([
        loadMetrics(),
        loadAlerts(),
        loadInsights()
      ]);
      
      setMetrics(metricsData);
      setAlerts(alertsData);
      setInsights(insightsData);
      setError(null);
    } catch (err) {
      setError('Failed to load performance data');
      console.error('Failed to load performance data:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedTimeRange]);

  // Auto refresh
  useEffect(() => {
    loadPerformanceData();
    
    if (autoRefresh) {
      const interval = setInterval(loadPerformanceData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [loadPerformanceData, autoRefresh, refreshInterval]);

  // Mock data loading
  const loadMetrics = async (): Promise<PerformanceMetric[]> => {
    const now = new Date();
    const generateHistory = (baseValue: number, variance: number) => {
      const history = [];
      for (let i = 23; i >= 0; i--) {
        history.push({
          timestamp: new Date(now.getTime() - i * 3600000),
          value: baseValue + (Math.random() - 0.5) * variance
        });
      }
      return history;
    };

    return [
      {
        id: 'response_time',
        name: 'Average Response Time',
        category: 'response_time',
        value: 245,
        unit: 'ms',
        threshold: { warning: 500, critical: 1000 },
        trend: 'down',
        trendPercentage: 12.5,
        history: generateHistory(245, 100)
      },
      {
        id: 'throughput',
        name: 'Requests per Second',
        category: 'throughput',
        value: 1250,
        unit: 'req/s',
        threshold: { warning: 800, critical: 500 },
        trend: 'up',
        trendPercentage: 8.3,
        history: generateHistory(1250, 200)
      },
      {
        id: 'cpu_usage',
        name: 'CPU Usage',
        category: 'resource_usage',
        value: 68.5,
        unit: '%',
        threshold: { warning: 80, critical: 90 },
        trend: 'stable',
        trendPercentage: 2.1,
        history: generateHistory(68.5, 15)
      },
      {
        id: 'memory_usage',
        name: 'Memory Usage',
        category: 'resource_usage',
        value: 72.3,
        unit: '%',
        threshold: { warning: 85, critical: 95 },
        trend: 'up',
        trendPercentage: 5.7,
        history: generateHistory(72.3, 10)
      },
      {
        id: 'disk_io',
        name: 'Disk I/O',
        category: 'resource_usage',
        value: 45.2,
        unit: 'MB/s',
        threshold: { warning: 80, critical: 100 },
        trend: 'down',
        trendPercentage: 3.4,
        history: generateHistory(45.2, 20)
      },
      {
        id: 'error_rate',
        name: 'Error Rate',
        category: 'error_rate',
        value: 2.1,
        unit: '%',
        threshold: { warning: 5, critical: 10 },
        trend: 'down',
        trendPercentage: 15.2,
        history: generateHistory(2.1, 1.5)
      }
    ];
  };

  const loadAlerts = async (): Promise<PerformanceAlert[]> => {
    return [
      {
        id: 'alert_1',
        metric: 'Memory Usage',
        severity: 'warning',
        message: 'Memory usage approaching threshold (72.3%)',
        timestamp: new Date(Date.now() - 1800000),
        acknowledged: false,
        recommendation: 'Consider scaling up memory or optimizing memory-intensive operations'
      },
      {
        id: 'alert_2',
        metric: 'Response Time',
        severity: 'info',
        message: 'Response time improved by 12.5% in the last hour',
        timestamp: new Date(Date.now() - 3600000),
        acknowledged: true
      },
      {
        id: 'alert_3',
        metric: 'Throughput',
        severity: 'info',
        message: 'Peak throughput reached: 1,450 req/s',
        timestamp: new Date(Date.now() - 7200000),
        acknowledged: true
      }
    ];
  };

  const loadInsights = async (): Promise<PerformanceInsight[]> => {
    return [
      {
        id: 'insight_1',
        title: 'Database Query Optimization',
        description: 'Several slow queries detected in the analytics module',
        impact: 'high',
        category: 'bottleneck',
        recommendation: 'Add indexes to frequently queried columns and optimize JOIN operations',
        estimatedImprovement: '25-40% response time reduction'
      },
      {
        id: 'insight_2',
        title: 'Memory Cache Efficiency',
        description: 'Cache hit rate is below optimal levels (65%)',
        impact: 'medium',
        category: 'optimization',
        recommendation: 'Increase cache size and implement better cache invalidation strategies',
        estimatedImprovement: '15-20% performance improvement'
      },
      {
        id: 'insight_3',
        title: 'Resource Scaling Opportunity',
        description: 'CPU usage patterns suggest auto-scaling could be beneficial',
        impact: 'medium',
        category: 'resource',
        recommendation: 'Configure horizontal auto-scaling based on CPU and memory thresholds',
        estimatedImprovement: '30% cost optimization'
      }
    ];
  };

  // Filter metrics
  const filteredMetrics = metrics.filter(metric => 
    selectedCategory === 'all' || metric.category === selectedCategory
  );

  // Get metric status
  const getMetricStatus = (metric: PerformanceMetric): 'good' | 'warning' | 'critical' => {
    if (metric.value >= metric.threshold.critical) return 'critical';
    if (metric.value >= metric.threshold.warning) return 'warning';
    return 'good';
  };

  // Metric card component
  const MetricCard: React.FC<{ metric: PerformanceMetric }> = ({ metric }) => {
    const status = getMetricStatus(metric);
    const statusColors = {
      good: 'border-green-500 bg-green-500/10',
      warning: 'border-yellow-500 bg-yellow-500/10',
      critical: 'border-red-500 bg-red-500/10'
    };

    const TrendIcon = metric.trend === 'up' ? TrendingUp : 
                     metric.trend === 'down' ? TrendingDown : Activity;
    const trendColor = metric.trend === 'up' ? 'text-green-400' : 
                      metric.trend === 'down' ? 'text-red-400' : 'text-gray-400';

    return (
      <div className={`bg-gray-800 rounded-lg p-6 border-l-4 ${statusColors[status]}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-white">{metric.name}</h3>
          <div className={`flex items-center ${trendColor}`}>
            <TrendIcon className="w-4 h-4 mr-1" />
            <span className="text-sm">{metric.trendPercentage.toFixed(1)}%</span>
          </div>
        </div>
        
        <div className="flex items-end justify-between">
          <div>
            <div className="text-2xl font-bold text-white">
              {metric.value.toFixed(1)}
            </div>
            <div className="text-sm text-gray-400">{metric.unit}</div>
          </div>
          
          <div className="text-right text-sm">
            <div className="text-gray-400">Threshold</div>
            <div className="text-yellow-400">{metric.threshold.warning}{metric.unit}</div>
            <div className="text-red-400">{metric.threshold.critical}{metric.unit}</div>
          </div>
        </div>

        {/* Mini chart */}
        <div className="mt-4 h-16 flex items-end space-x-1">
          {metric.history.slice(-12).map((point, index) => {
            const height = Math.max(4, (point.value / Math.max(...metric.history.map(h => h.value))) * 60);
            return (
              <div
                key={index}
                className="bg-blue-500 rounded-sm flex-1"
                style={{ height: `${height}px` }}
                title={`${point.value.toFixed(1)}${metric.unit} at ${point.timestamp.toLocaleTimeString()}`}
              />
            );
          })}
        </div>
      </div>
    );
  };

  // Alert component
  const AlertCard: React.FC<{ alert: PerformanceAlert }> = ({ alert }) => {
    const severityColors = {
      info: 'border-blue-500 bg-blue-500/10 text-blue-400',
      warning: 'border-yellow-500 bg-yellow-500/10 text-yellow-400',
      critical: 'border-red-500 bg-red-500/10 text-red-400'
    };

    const SeverityIcon = alert.severity === 'critical' ? AlertTriangle :
                        alert.severity === 'warning' ? AlertTriangle : CheckCircle;

    return (
      <div className={`border-l-4 p-4 rounded ${severityColors[alert.severity]}`}>
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <SeverityIcon className="w-5 h-5 mt-0.5" />
            <div>
              <div className="font-medium">{alert.metric}</div>
              <div className="text-sm opacity-90">{alert.message}</div>
              {alert.recommendation && (
                <div className="text-xs mt-2 opacity-75">
                  Recommendation: {alert.recommendation}
                </div>
              )}
            </div>
          </div>
          <div className="text-xs opacity-75">
            {alert.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  // Insight component
  const InsightCard: React.FC<{ insight: PerformanceInsight }> = ({ insight }) => {
    const impactColors = {
      high: 'text-red-400',
      medium: 'text-yellow-400',
      low: 'text-green-400'
    };

    const categoryIcons = {
      optimization: Zap,
      bottleneck: Target,
      resource: Cpu,
      configuration: Settings
    };

    const CategoryIcon = categoryIcons[insight.category];

    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            <CategoryIcon className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold text-white">{insight.title}</h3>
          </div>
          <span className={`px-2 py-1 rounded text-xs font-medium ${impactColors[insight.impact]} bg-current bg-opacity-10`}>
            {insight.impact} impact
          </span>
        </div>
        
        <p className="text-gray-300 text-sm mb-3">{insight.description}</p>
        
        <div className="space-y-2 text-sm">
          <div>
            <span className="text-gray-400">Recommendation:</span>
            <p className="text-gray-300 mt-1">{insight.recommendation}</p>
          </div>
          <div>
            <span className="text-gray-400">Expected Improvement:</span>
            <span className="text-green-400 ml-2">{insight.estimatedImprovement}</span>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">Error</h3>
        <p className="text-gray-400 mb-4">{error}</p>
        <button
          onClick={loadPerformanceData}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-900 text-white">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Performance Analyzer</h2>
            <p className="text-gray-400">Advanced performance analysis and optimization insights</p>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value as any)}
              className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
            <button
              onClick={loadPerformanceData}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4 mb-6">
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
        >
          <option value="all">All Categories</option>
          <option value="response_time">Response Time</option>
          <option value="throughput">Throughput</option>
          <option value="resource_usage">Resource Usage</option>
          <option value="error_rate">Error Rate</option>
        </select>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAlerts(!showAlerts)}
            className={`px-3 py-2 rounded text-sm ${
              showAlerts ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'
            }`}
          >
            Alerts
          </button>
          <button
            onClick={() => setShowInsights(!showInsights)}
            className={`px-3 py-2 rounded text-sm ${
              showInsights ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'
            }`}
          >
            Insights
          </button>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {filteredMetrics.map(metric => (
          <MetricCard key={metric.id} metric={metric} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts */}
        {showAlerts && (
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Performance Alerts</h3>
            <div className="space-y-3">
              {alerts.length === 0 ? (
                <div className="text-center py-8 bg-gray-800 rounded-lg">
                  <CheckCircle className="w-8 h-8 text-green-400 mx-auto mb-2" />
                  <p className="text-gray-400">No active alerts</p>
                </div>
              ) : (
                alerts.map(alert => (
                  <AlertCard key={alert.id} alert={alert} />
                ))
              )}
            </div>
          </div>
        )}

        {/* Insights */}
        {showInsights && (
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Optimization Insights</h3>
            <div className="space-y-4">
              {insights.length === 0 ? (
                <div className="text-center py-8 bg-gray-800 rounded-lg">
                  <Zap className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                  <p className="text-gray-400">No insights available</p>
                </div>
              ) : (
                insights.map(insight => (
                  <InsightCard key={insight.id} insight={insight} />
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};