import React, { useState } from 'react';
import { Zap, Clock, AlertTriangle, CheckCircle, Server, Database } from 'lucide-react';

interface PerformanceData {
  uptime: number;
  errorRate: number;
  avgLoadTime: number;
}

interface PerformanceMetricsProps {
  data: PerformanceData;
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ data }) => {
  const [selectedMetric, setSelectedMetric] = useState<'uptime' | 'response' | 'errors'>('uptime');

  // Mock detailed performance data
  const detailedMetrics = {
    uptime: {
      current: data.uptime,
      target: 99.9,
      history: [99.8, 99.9, 99.7, 99.9, 99.8, 99.9, 100],
    },
    response: {
      current: data.avgLoadTime,
      target: 200,
      history: [180, 220, 195, 210, 185, 175, data.avgLoadTime],
    },
    errors: {
      current: data.errorRate,
      target: 0.1,
      history: [0.2, 0.1, 0.3, 0.1, 0.2, 0.1, data.errorRate],
    },
  };

  const getStatusColor = (metric: string, value: number) => {
    switch (metric) {
      case 'uptime':
        if (value >= 99.9) return 'text-green-400';
        if (value >= 99.5) return 'text-yellow-400';
        return 'text-red-400';
      case 'response':
        if (value <= 200) return 'text-green-400';
        if (value <= 500) return 'text-yellow-400';
        return 'text-red-400';
      case 'errors':
        if (value <= 0.1) return 'text-green-400';
        if (value <= 0.5) return 'text-yellow-400';
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusIcon = (metric: string, value: number) => {
    const isGood = 
      (metric === 'uptime' && value >= 99.9) ||
      (metric === 'response' && value <= 200) ||
      (metric === 'errors' && value <= 0.1);

    return isGood ? (
      <CheckCircle className="w-5 h-5 text-green-400" />
    ) : (
      <AlertTriangle className="w-5 h-5 text-yellow-400" />
    );
  };

  const formatValue = (metric: string, value: number) => {
    switch (metric) {
      case 'uptime':
        return `${value.toFixed(2)}%`;
      case 'response':
        return `${value}ms`;
      case 'errors':
        return `${value.toFixed(2)}%`;
      default:
        return value.toString();
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-white flex items-center">
          <Zap className="w-5 h-5 mr-2 text-purple-500" />
          Performance Metrics
        </h3>
        
        <div className="flex space-x-1 bg-gray-700 rounded p-1">
          <button
            onClick={() => setSelectedMetric('uptime')}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              selectedMetric === 'uptime'
                ? 'bg-purple-600 text-white'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            Uptime
          </button>
          <button
            onClick={() => setSelectedMetric('response')}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              selectedMetric === 'response'
                ? 'bg-purple-600 text-white'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            Response
          </button>
          <button
            onClick={() => setSelectedMetric('errors')}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              selectedMetric === 'errors'
                ? 'bg-purple-600 text-white'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            Errors
          </button>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-300 text-sm">System Uptime</span>
            {getStatusIcon('uptime', data.uptime)}
          </div>
          <div className="flex items-baseline space-x-2">
            <span className={`text-2xl font-bold ${getStatusColor('uptime', data.uptime)}`}>
              {formatValue('uptime', data.uptime)}
            </span>
            <span className="text-xs text-gray-400">Target: 99.9%</span>
          </div>
        </div>

        <div className="bg-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-300 text-sm">Avg Response Time</span>
            {getStatusIcon('response', data.avgLoadTime)}
          </div>
          <div className="flex items-baseline space-x-2">
            <span className={`text-2xl font-bold ${getStatusColor('response', data.avgLoadTime)}`}>
              {formatValue('response', data.avgLoadTime)}
            </span>
            <span className="text-xs text-gray-400">Target: &lt;200ms</span>
          </div>
        </div>

        <div className="bg-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-300 text-sm">Error Rate</span>
            {getStatusIcon('errors', data.errorRate)}
          </div>
          <div className="flex items-baseline space-x-2">
            <span className={`text-2xl font-bold ${getStatusColor('errors', data.errorRate)}`}>
              {formatValue('errors', data.errorRate)}
            </span>
            <span className="text-xs text-gray-400">Target: &lt;0.1%</span>
          </div>
        </div>
      </div>

      {/* Detailed Chart */}
      <div className="mb-6">
        <h4 className="text-lg font-medium text-white mb-3 capitalize">
          {selectedMetric} Trend (Last 7 Days)
        </h4>
        
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-end justify-between h-32 space-x-2">
            {detailedMetrics[selectedMetric].history.map((value, index) => {
              const maxValue = Math.max(...detailedMetrics[selectedMetric].history);
              const minValue = Math.min(...detailedMetrics[selectedMetric].history);
              const range = maxValue - minValue || 1;
              const height = ((value - minValue) / range) * 100;
              
              return (
                <div
                  key={index}
                  className="flex-1 flex flex-col items-center group cursor-pointer"
                >
                  <div
                    className={`w-full rounded-t transition-all duration-300 ${
                      selectedMetric === 'uptime' ? 'bg-green-500' :
                      selectedMetric === 'response' ? 'bg-blue-500' : 'bg-red-500'
                    } opacity-70 hover:opacity-100`}
                    style={{ height: `${Math.max(height, 5)}%` }}
                  />
                  <span className="text-xs text-gray-400 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    {formatValue(selectedMetric, value)}
                  </span>
                </div>
              );
            })}
          </div>
          
          <div className="flex justify-between mt-2 text-xs text-gray-400">
            <span>6 days ago</span>
            <span>3 days ago</span>
            <span>Today</span>
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="border-t border-gray-700 pt-4">
        <h4 className="text-lg font-medium text-white mb-3 flex items-center">
          <Server className="w-4 h-4 mr-2 text-gray-400" />
          System Health
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-300 text-sm">API Server</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-green-400 text-sm">Healthy</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-300 text-sm">Database</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-green-400 text-sm">Healthy</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-300 text-sm">Cache Layer</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                <span className="text-yellow-400 text-sm">Warning</span>
              </div>
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-300 text-sm">Memory Usage</span>
              <span className="text-white text-sm">68%</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-300 text-sm">CPU Usage</span>
              <span className="text-white text-sm">42%</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-300 text-sm">Disk Usage</span>
              <span className="text-white text-sm">23%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Incidents */}
      <div className="border-t border-gray-700 pt-4 mt-4">
        <h4 className="text-lg font-medium text-white mb-3">Recent Incidents</h4>
        
        <div className="space-y-2">
          <div className="bg-gray-700 rounded-lg p-3 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
              <div>
                <p className="text-white text-sm">Cache performance degradation</p>
                <p className="text-gray-400 text-xs">2 hours ago</p>
              </div>
            </div>
            <span className="text-yellow-400 text-xs">Investigating</span>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-3 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <div>
                <p className="text-white text-sm">Database connection timeout</p>
                <p className="text-gray-400 text-xs">1 day ago</p>
              </div>
            </div>
            <span className="text-green-400 text-xs">Resolved</span>
          </div>
        </div>
      </div>
    </div>
  );
};