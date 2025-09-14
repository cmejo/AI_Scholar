/**
 * Enterprise Performance Monitor - Real-time monitoring for enterprise components
 */
import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Activity, AlertTriangle, CheckCircle, Clock, TrendingDown, TrendingUp, Target, Gauge } from 'lucide-react';
import { EnterprisePerformanceTracker } from '../../utils/enterpriseCodeSplitting';
import { PerformanceAnalyzer } from './performance/PerformanceAnalyzer';

interface PerformanceMetrics {
  componentName: string;
  loadTime: number;
  retryCount: number;
  errorCount: number;
  lastAccessed: Date;
  averageLoadTime: number;
  successRate: number;
  performance: string;
  recommendations: string[];
}

interface EnterprisePerformanceMonitorProps {
  enabled?: boolean;
  updateInterval?: number;
  showDetails?: boolean;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  onAlert?: (alert: PerformanceAlert) => void;
}

interface PerformanceAlert {
  type: 'warning' | 'error' | 'info';
  message: string;
  componentName: string;
  timestamp: Date;
}

export const EnterprisePerformanceMonitor: React.FC<EnterprisePerformanceMonitorProps> = ({
  enabled = true,
  updateInterval = 5000,
  showDetails = false,
  position = 'top-right',
  onAlert
}) => {
  const [metrics, setMetrics] = useState<Record<string, PerformanceMetrics>>({});
  const [isExpanded, setIsExpanded] = useState(false);
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [viewMode, setViewMode] = useState<'monitor' | 'analyzer'>('monitor');
  const intervalRef = useRef<NodeJS.Timeout>();
  const previousMetricsRef = useRef<Record<string, PerformanceMetrics>>({});

  const updateMetrics = useCallback(() => {
    const currentMetrics = EnterprisePerformanceTracker.getPerformanceReport();
    setMetrics(currentMetrics);

    // Check for performance alerts
    Object.entries(currentMetrics).forEach(([componentName, metric]) => {
      const previousMetric = previousMetricsRef.current[componentName];
      
      // Check for new errors
      if (previousMetric && metric.errorCount > previousMetric.errorCount) {
        const alert: PerformanceAlert = {
          type: 'error',
          message: `New error detected in ${componentName}`,
          componentName,
          timestamp: new Date()
        };
        setAlerts(prev => [...prev.slice(-9), alert]); // Keep last 10 alerts
        onAlert?.(alert);
      }

      // Check for performance degradation
      if (previousMetric && metric.averageLoadTime > previousMetric.averageLoadTime * 1.5) {
        const alert: PerformanceAlert = {
          type: 'warning',
          message: `Performance degradation in ${componentName}`,
          componentName,
          timestamp: new Date()
        };
        setAlerts(prev => [...prev.slice(-9), alert]);
        onAlert?.(alert);
      }

      // Check for low success rate
      if (metric.successRate < 0.8) {
        const alert: PerformanceAlert = {
          type: 'warning',
          message: `Low success rate (${(metric.successRate * 100).toFixed(1)}%) in ${componentName}`,
          componentName,
          timestamp: new Date()
        };
        setAlerts(prev => [...prev.slice(-9), alert]);
        onAlert?.(alert);
      }
    });

    previousMetricsRef.current = currentMetrics;
  }, [onAlert]);

  useEffect(() => {
    if (!enabled) return;

    // Initial update
    updateMetrics();

    // Set up interval
    intervalRef.current = setInterval(updateMetrics, updateInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, updateInterval, updateMetrics]);

  const getPositionClasses = () => {
    switch (position) {
      case 'top-left':
        return 'top-4 left-4';
      case 'bottom-left':
        return 'bottom-4 left-4';
      case 'bottom-right':
        return 'bottom-4 right-4';
      default:
        return 'top-4 right-4';
    }
  };

  const getPerformanceIcon = (performance: string) => {
    switch (performance) {
      case 'excellent':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'good':
        return <TrendingUp className="w-4 h-4 text-blue-500" />;
      case 'fair':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'poor':
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Activity className="w-4 h-4 text-blue-500" />;
    }
  };

  const getOverallHealth = () => {
    const componentCount = Object.keys(metrics).length;
    if (componentCount === 0) return { status: 'unknown', color: 'gray' };

    const excellentCount = Object.values(metrics).filter(m => m.performance === 'excellent').length;
    const goodCount = Object.values(metrics).filter(m => m.performance === 'good').length;
    const fairCount = Object.values(metrics).filter(m => m.performance === 'fair').length;
    const poorCount = Object.values(metrics).filter(m => m.performance === 'poor').length;

    if (poorCount > 0) return { status: 'poor', color: 'red' };
    if (fairCount > componentCount * 0.3) return { status: 'fair', color: 'yellow' };
    if (goodCount + excellentCount > componentCount * 0.8) return { status: 'good', color: 'green' };
    return { status: 'fair', color: 'yellow' };
  };

  if (!enabled) return null;

  // Show full analyzer view
  if (viewMode === 'analyzer') {
    return <PerformanceAnalyzer />;
  }

  const overallHealth = getOverallHealth();
  const hasAlerts = alerts.length > 0;

  return (
    <div className={`fixed ${getPositionClasses()} z-50`}>
      <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-lg">
        {/* Header */}
        <div 
          className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-750 transition-colors"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center space-x-2">
            <Activity className={`w-5 h-5 text-${overallHealth.color}-500`} />
            <span className="text-sm font-medium text-white">Enterprise Monitor</span>
            {hasAlerts && (
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            )}
          </div>
          <div className={`text-xs px-2 py-1 rounded bg-${overallHealth.color}-500 bg-opacity-20 text-${overallHealth.color}-400`}>
            {overallHealth.status.toUpperCase()}
          </div>
        </div>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="border-t border-gray-700">
            {/* Component Metrics */}
            {Object.keys(metrics).length > 0 && (
              <div className="p-3 border-b border-gray-700">
                <h4 className="text-xs font-semibold text-gray-400 mb-2">Component Performance</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {Object.entries(metrics).map(([componentName, metric]) => (
                    <div key={componentName} className="flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2">
                        {getPerformanceIcon(metric.performance)}
                        <span className="text-white truncate max-w-32" title={componentName}>
                          {componentName}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 text-gray-400">
                        <span>{metric.averageLoadTime.toFixed(0)}ms</span>
                        <span>{(metric.successRate * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Alerts */}
            {alerts.length > 0 && (
              <div className="p-3 border-b border-gray-700">
                <h4 className="text-xs font-semibold text-gray-400 mb-2">Recent Alerts</h4>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {alerts.slice(-5).reverse().map((alert, index) => (
                    <div key={index} className="flex items-start space-x-2 text-xs">
                      {getAlertIcon(alert.type)}
                      <div className="flex-1">
                        <div className="text-white">{alert.message}</div>
                        <div className="text-gray-500">
                          {alert.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Detailed Metrics */}
            {showDetails && Object.keys(metrics).length > 0 && (
              <div className="p-3">
                <h4 className="text-xs font-semibold text-gray-400 mb-2">Detailed Metrics</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {Object.entries(metrics).map(([componentName, metric]) => (
                    <div key={componentName} className="bg-gray-900 rounded p-2">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-white">{componentName}</span>
                        {getPerformanceIcon(metric.performance)}
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
                        <div>Load: {metric.averageLoadTime.toFixed(0)}ms</div>
                        <div>Success: {(metric.successRate * 100).toFixed(1)}%</div>
                        <div>Errors: {metric.errorCount}</div>
                        <div>Retries: {metric.retryCount}</div>
                      </div>
                      {metric.recommendations.length > 0 && (
                        <div className="mt-1 text-xs text-yellow-400">
                          💡 {metric.recommendations[0]}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="p-3 space-y-2">
              <div className="flex space-x-2">
                <button
                  onClick={() => setViewMode(viewMode === 'monitor' ? 'analyzer' : 'monitor')}
                  className="flex-1 text-xs px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors flex items-center justify-center"
                >
                  {viewMode === 'monitor' ? (
                    <>
                      <Target className="w-3 h-3 mr-1" />
                      Analyzer
                    </>
                  ) : (
                    <>
                      <Gauge className="w-3 h-3 mr-1" />
                      Monitor
                    </>
                  )}
                </button>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setAlerts([])}
                  className="flex-1 text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
                >
                  Clear Alerts
                </button>
                <button
                  onClick={() => {
                    EnterprisePerformanceTracker.clearMetrics();
                    setMetrics({});
                    setAlerts([]);
                  }}
                  className="flex-1 text-xs px-2 py-1 bg-red-600 hover:bg-red-700 text-white rounded transition-colors"
                >
                  Reset Metrics
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnterprisePerformanceMonitor;