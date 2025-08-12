/**
 * Bundle Performance Dashboard Component
 * Displays bundle analysis results and performance metrics
 */

import {
    AlertTriangle,
    BarChart3,
    CheckCircle,
    Info,
    Package,
    TrendingDown,
    TrendingUp,
    Zap
} from 'lucide-react';
import React, { useEffect, useState } from 'react';

interface BundleMetrics {
  totalSize: number;
  gzippedSize: number;
  chunkCount: number;
  assetCount: number;
  compressionRatio: number;
  timestamp: string;
}

interface PerformanceRegression {
  metric: string;
  current: string;
  previous: string;
  change: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
}

interface OptimizationRecommendation {
  type: string;
  priority: 'high' | 'medium' | 'low';
  message: string;
  action?: string;
  estimatedSavings?: number;
}

interface BundleAnalysisData {
  summary: {
    totalSize: string;
    gzippedSize: string;
    compressionRatio: string;
    jsChunks: number;
    assets: number;
    recommendations: number;
    regressions: number;
  };
  regressions?: PerformanceRegression[];
  recommendations: OptimizationRecommendation[];
  performance?: {
    buildTime: number;
    analysisTime: string;
    baseline?: {
      totalSize: string;
      gzippedSize: string;
      timestamp: string;
    };
  };
}

export const BundlePerformanceDashboard: React.FC = () => {
  const [analysisData, setAnalysisData] = useState<BundleAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBundleAnalysis();
  }, []);

  const loadBundleAnalysis = async () => {
    try {
      setLoading(true);
      // In a real implementation, this would fetch from an API or load from a file
      // For now, we'll simulate loading bundle analysis data
      const mockData: BundleAnalysisData = {
        summary: {
          totalSize: '2.1 MB',
          gzippedSize: '680 KB',
          compressionRatio: '67.6%',
          jsChunks: 3,
          assets: 5,
          recommendations: 4,
          regressions: 1,
        },
        regressions: [
          {
            metric: 'Total Size',
            current: '2.1 MB',
            previous: '1.9 MB',
            change: '+10.5%',
            severity: 'warning',
            message: 'Bundle size increased by 10.5%',
          },
        ],
        recommendations: [
          {
            type: 'tree-shaking',
            priority: 'high',
            message: 'Optimize lucide-react imports to reduce bundle size',
            action: 'Use specific icon imports instead of barrel imports',
            estimatedSavings: 180000,
          },
          {
            type: 'code-splitting',
            priority: 'medium',
            message: 'Implement route-based code splitting for better performance',
            action: 'Use React.lazy() and dynamic imports for route components',
            estimatedSavings: 300000,
          },
          {
            type: 'dependency-optimization',
            priority: 'high',
            message: 'Vendor bundle is 1.2 MB. Analyze dependencies for unused code',
            action: 'npm run deps:analyze && npm run optimize:deps',
            estimatedSavings: 400000,
          },
          {
            type: 'asset-optimization',
            priority: 'low',
            message: 'Optimize images using tools like imagemin or squoosh',
            estimatedSavings: 50000,
          },
        ],
        performance: {
          buildTime: 12500,
          analysisTime: new Date().toISOString(),
          baseline: {
            totalSize: '1.9 MB',
            gzippedSize: '620 KB',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
          },
        },
      };

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      setAnalysisData(mockData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bundle analysis');
    } finally {
      setLoading(false);
    }
  };

  const formatSize = (bytes: number): string => {
    const KB = 1024;
    const MB = KB * 1024;

    if (bytes >= MB) {
      return `${(bytes / MB).toFixed(2)} MB`;
    } else if (bytes >= KB) {
      return `${(bytes / KB).toFixed(2)} KB`;
    } else {
      return `${bytes} B`;
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <Zap className="w-5 h-5 text-red-500" />;
      case 'medium':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  if (loading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm border">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm border">
        <div className="text-center text-red-600">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Error Loading Bundle Analysis</h3>
          <p className="text-sm">{error}</p>
          <button
            onClick={loadBundleAnalysis}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!analysisData) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Package className="w-6 h-6 mr-2" />
            Bundle Performance Dashboard
          </h2>
          <button
            onClick={loadBundleAnalysis}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
          >
            Refresh Analysis
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">Total Size</p>
                <p className="text-2xl font-bold text-blue-900">{analysisData.summary.totalSize}</p>
              </div>
              <Package className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Gzipped</p>
                <p className="text-2xl font-bold text-green-900">{analysisData.summary.gzippedSize}</p>
                <p className="text-xs text-green-600">{analysisData.summary.compressionRatio} compression</p>
              </div>
              <Zap className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">Chunks</p>
                <p className="text-2xl font-bold text-purple-900">{analysisData.summary.jsChunks}</p>
                <p className="text-xs text-purple-600">{analysisData.summary.assets} assets</p>
              </div>
              <BarChart3 className="w-8 h-8 text-purple-500" />
            </div>
          </div>

          <div className="bg-yellow-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-600">Issues</p>
                <p className="text-2xl font-bold text-yellow-900">
                  {analysisData.summary.recommendations + (analysisData.summary.regressions || 0)}
                </p>
                <p className="text-xs text-yellow-600">
                  {analysisData.summary.regressions || 0} regressions
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Performance Regressions */}
      {analysisData.regressions && analysisData.regressions.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-red-500" />
            Performance Regressions
          </h3>
          <div className="space-y-3">
            {analysisData.regressions.map((regression, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border-l-4 ${
                  regression.severity === 'critical'
                    ? 'bg-red-50 border-red-500'
                    : regression.severity === 'warning'
                    ? 'bg-yellow-50 border-yellow-500'
                    : 'bg-blue-50 border-blue-500'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start">
                    {getSeverityIcon(regression.severity)}
                    <div className="ml-3">
                      <p className="font-medium text-gray-900">{regression.message}</p>
                      <p className="text-sm text-gray-600 mt-1">
                        {regression.previous} → {regression.current} ({regression.change})
                      </p>
                    </div>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded ${
                      regression.severity === 'critical'
                        ? 'bg-red-100 text-red-800'
                        : regression.severity === 'warning'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}
                  >
                    {regression.severity.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Optimization Recommendations */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <CheckCircle className="w-5 h-5 mr-2 text-green-500" />
          Optimization Recommendations
        </h3>
        <div className="space-y-4">
          {analysisData.recommendations.map((recommendation, index) => (
            <div
              key={index}
              className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start">
                  {getPriorityIcon(recommendation.priority)}
                  <div className="ml-3 flex-1">
                    <p className="font-medium text-gray-900">{recommendation.message}</p>
                    {recommendation.action && (
                      <p className="text-sm text-gray-600 mt-1">
                        <strong>Action:</strong> {recommendation.action}
                      </p>
                    )}
                    {recommendation.estimatedSavings && (
                      <p className="text-sm text-green-600 mt-1">
                        <strong>Potential Savings:</strong> {formatSize(recommendation.estimatedSavings)}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded ${
                      recommendation.priority === 'high'
                        ? 'bg-red-100 text-red-800'
                        : recommendation.priority === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}
                  >
                    {recommendation.priority.toUpperCase()}
                  </span>
                  <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                    {recommendation.type}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance History */}
      {analysisData.performance?.baseline && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingDown className="w-5 h-5 mr-2 text-blue-500" />
            Performance History
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Current Build</h4>
              <p className="text-sm text-gray-600">Size: {analysisData.summary.totalSize}</p>
              <p className="text-sm text-gray-600">Gzipped: {analysisData.summary.gzippedSize}</p>
              <p className="text-sm text-gray-600">
                Analyzed: {new Date(analysisData.performance.analysisTime).toLocaleString()}
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Previous Baseline</h4>
              <p className="text-sm text-gray-600">Size: {analysisData.performance.baseline.totalSize}</p>
              <p className="text-sm text-gray-600">Gzipped: {analysisData.performance.baseline.gzippedSize}</p>
              <p className="text-sm text-gray-600">
                Baseline: {new Date(analysisData.performance.baseline.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BundlePerformanceDashboard;