/**
 * WorkflowMonitor - Component for monitoring workflow executions
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Pause,
  Play,
  RefreshCw,
  Filter,
  Search,
  Eye,
  Download,
  Calendar,
  User,
  Zap,
  BarChart3,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import type { WorkflowExecution, WorkflowExecutionLog } from '../../../types/workflow';
import { WorkflowManagementService } from '../../../services/workflowManagementService';

export interface WorkflowMonitorProps {
  workflowId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface ExecutionStats {
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  averageExecutionTime: number;
  executionsToday: number;
  successRate: number;
}

const workflowService = new WorkflowManagementService();

export const WorkflowMonitor: React.FC<WorkflowMonitorProps> = ({
  workflowId,
  autoRefresh = true,
  refreshInterval = 30000
}) => {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [stats, setStats] = useState<ExecutionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [showExecutionDetails, setShowExecutionDetails] = useState(false);

  // Load executions
  const loadExecutions = useCallback(async () => {
    try {
      setLoading(true);
      const [executionsData, statsData] = await Promise.all([
        workflowService.getWorkflowExecutions(workflowId),
        workflowService.getExecutionStats(workflowId)
      ]);
      
      setExecutions(executionsData.data);
      setStats(statsData);
      setError(null);
    } catch (err) {
      setError('Failed to load workflow executions');
      console.error('Failed to load executions:', err);
    } finally {
      setLoading(false);
    }
  }, [workflowId]);

  // Auto refresh
  useEffect(() => {
    loadExecutions();
    
    if (autoRefresh) {
      const interval = setInterval(loadExecutions, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [loadExecutions, autoRefresh, refreshInterval]);

  // Filter executions
  const filteredExecutions = executions.filter(execution => {
    const matchesSearch = execution.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         execution.triggeredBy.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || execution.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Handle view execution details
  const handleViewExecution = (execution: WorkflowExecution) => {
    setSelectedExecution(execution);
    setShowExecutionDetails(true);
  };

  // Handle retry failed execution
  const handleRetryExecution = async (execution: WorkflowExecution) => {
    try {
      await workflowService.executeWorkflow(execution.workflowId, execution.context);
      await loadExecutions();
    } catch (err) {
      console.error('Failed to retry execution:', err);
      setError('Failed to retry workflow execution');
    }
  };

  // Handle cancel running execution
  const handleCancelExecution = async (executionId: string) => {
    try {
      await workflowService.cancelExecution(executionId);
      await loadExecutions();
    } catch (err) {
      console.error('Failed to cancel execution:', err);
      setError('Failed to cancel workflow execution');
    }
  };

  // Handle download execution logs
  const handleDownloadLogs = (execution: WorkflowExecution) => {
    const logs = execution.logs.map(log => 
      `[${log.timestamp.toISOString()}] ${log.level.toUpperCase()}: ${log.message}`
    ).join('\n');
    
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow-execution-${execution.id}-logs.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Status badge component
  const StatusBadge: React.FC<{ status: WorkflowExecution['status'] }> = ({ status }) => {
    const statusConfig = {
      pending: { icon: Clock, color: 'text-yellow-400 bg-yellow-400/10', label: 'Pending' },
      running: { icon: Activity, color: 'text-blue-400 bg-blue-400/10', label: 'Running' },
      completed: { icon: CheckCircle, color: 'text-green-400 bg-green-400/10', label: 'Completed' },
      failed: { icon: XCircle, color: 'text-red-400 bg-red-400/10', label: 'Failed' },
      cancelled: { icon: Pause, color: 'text-gray-400 bg-gray-400/10', label: 'Cancelled' }
    };

    const config = statusConfig[status];
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {config.label}
      </span>
    );
  };

  // Execution details modal
  const ExecutionDetailsModal: React.FC = () => {
    if (!showExecutionDetails || !selectedExecution) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              Execution Details: {selectedExecution.id}
            </h3>
            <button
              onClick={() => setShowExecutionDetails(false)}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
                <StatusBadge status={selectedExecution.status} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Triggered By</label>
                <p className="text-white">{selectedExecution.triggeredBy}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Trigger Type</label>
                <p className="text-white">{selectedExecution.triggerType}</p>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Start Time</label>
                <p className="text-white">{selectedExecution.startTime.toLocaleString()}</p>
              </div>
              {selectedExecution.endTime && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">End Time</label>
                  <p className="text-white">{selectedExecution.endTime.toLocaleString()}</p>
                </div>
              )}
              {selectedExecution.duration && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Duration</label>
                  <p className="text-white">{selectedExecution.duration}ms</p>
                </div>
              )}
            </div>
          </div>

          {selectedExecution.error && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">Error Details</label>
              <div className="bg-red-900/20 border border-red-500/30 rounded p-4">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-red-400 text-sm font-medium mb-2">Error Message:</p>
                    <p className="text-red-300 text-sm mb-3">{selectedExecution.error}</p>
                    
                    {/* Recovery suggestions */}
                    <div className="bg-red-800/30 rounded p-3">
                      <p className="text-red-200 text-sm font-medium mb-2">Recovery Suggestions:</p>
                      <ul className="text-red-200 text-sm space-y-1">
                        <li>• Check workflow configuration and dependencies</li>
                        <li>• Verify external service availability</li>
                        <li>• Review input data format and validation</li>
                        <li>• Check system resources and permissions</li>
                        <li>• Retry execution after resolving issues</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Execution Results */}
          {selectedExecution.results.length > 0 && (
            <div className="mb-6">
              <h4 className="text-md font-semibold text-white mb-3">Execution Results</h4>
              <div className="space-y-2">
                {selectedExecution.results.map((result, index) => (
                  <div key={index} className="bg-gray-700 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-white">{result.actionName}</span>
                      <StatusBadge status={result.status as any} />
                    </div>
                    <p className="text-sm text-gray-400">Duration: {result.duration}ms</p>
                    {result.error && (
                      <p className="text-sm text-red-400 mt-1">Error: {result.error}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Execution Logs */}
          {selectedExecution.logs.length > 0 && (
            <div>
              <h4 className="text-md font-semibold text-white mb-3">Execution Logs</h4>
              <div className="bg-gray-900 rounded p-4 max-h-64 overflow-y-auto">
                {selectedExecution.logs.map((log, index) => (
                  <div key={index} className="flex items-start space-x-3 mb-2 text-sm">
                    <span className="text-gray-400 whitespace-nowrap">
                      {log.timestamp.toLocaleTimeString()}
                    </span>
                    <span className={`font-medium ${
                      log.level === 'error' ? 'text-red-400' :
                      log.level === 'warn' ? 'text-yellow-400' :
                      log.level === 'info' ? 'text-blue-400' :
                      'text-gray-400'
                    }`}>
                      [{log.level.toUpperCase()}]
                    </span>
                    <span className="text-gray-300 flex-1">{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-between mt-6">
            <div className="flex space-x-3">
              {/* Action buttons based on execution status */}
              {selectedExecution.status === 'failed' && (
                <button
                  onClick={() => {
                    handleRetryExecution(selectedExecution);
                    setShowExecutionDetails(false);
                  }}
                  className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 flex items-center"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retry Execution
                </button>
              )}
              
              {selectedExecution.status === 'running' && (
                <button
                  onClick={() => {
                    handleCancelExecution(selectedExecution.id);
                    setShowExecutionDetails(false);
                  }}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 flex items-center"
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  Cancel Execution
                </button>
              )}

              <button
                onClick={() => handleDownloadLogs(selectedExecution)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
              >
                <Download className="w-4 h-4 mr-2" />
                Download Logs
              </button>
            </div>
            
            <button
              onClick={() => setShowExecutionDetails(false)}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Close
            </button>
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
          onClick={loadExecutions}
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
        <h2 className="text-2xl font-bold mb-2">Workflow Monitor</h2>
        <p className="text-gray-400">Monitor workflow executions and performance</p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total</p>
                <p className="text-xl font-bold">{stats.totalExecutions}</p>
              </div>
              <Activity className="w-6 h-6 text-blue-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Success</p>
                <p className="text-xl font-bold">{stats.successfulExecutions}</p>
              </div>
              <CheckCircle className="w-6 h-6 text-green-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Failed</p>
                <p className="text-xl font-bold">{stats.failedExecutions}</p>
              </div>
              <XCircle className="w-6 h-6 text-red-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Success Rate</p>
                <p className="text-xl font-bold">{stats.successRate.toFixed(1)}%</p>
              </div>
              <BarChart3 className="w-6 h-6 text-purple-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Avg Time</p>
                <p className="text-xl font-bold">{stats.averageExecutionTime}ms</p>
              </div>
              <Clock className="w-6 h-6 text-yellow-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Today</p>
                <p className="text-xl font-bold">{stats.executionsToday}</p>
              </div>
              <Calendar className="w-6 h-6 text-indigo-500" />
            </div>
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search executions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        <button
          onClick={loadExecutions}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Executions List */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        {filteredExecutions.length === 0 ? (
          <div className="text-center py-8">
            <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Executions Found</h3>
            <p className="text-gray-400">No executions match your current filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Execution ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Triggered By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Start Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {filteredExecutions.map(execution => (
                  <tr key={execution.id} className="hover:bg-gray-700/50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Zap className="w-4 h-4 text-blue-400 mr-2" />
                        <span className="text-sm font-medium text-white">
                          {execution.id.slice(0, 8)}...
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={execution.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <User className="w-4 h-4 text-gray-400 mr-1" />
                        <span className="text-sm text-gray-300">{execution.triggeredBy}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {execution.startTime.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {execution.duration ? `${execution.duration}ms` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleViewExecution(execution)}
                          className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        
                        {/* Download logs button */}
                        <button
                          onClick={() => handleDownloadLogs(execution)}
                          className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded"
                          title="Download Logs"
                        >
                          <Download className="w-4 h-4" />
                        </button>

                        {/* Retry button for failed executions */}
                        {execution.status === 'failed' && (
                          <button
                            onClick={() => handleRetryExecution(execution)}
                            className="p-2 text-orange-400 hover:text-white hover:bg-orange-400/10 rounded"
                            title="Retry Execution"
                          >
                            <RefreshCw className="w-4 h-4" />
                          </button>
                        )}

                        {/* Cancel button for running executions */}
                        {execution.status === 'running' && (
                          <button
                            onClick={() => handleCancelExecution(execution.id)}
                            className="p-2 text-red-400 hover:text-white hover:bg-red-400/10 rounded"
                            title="Cancel Execution"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ExecutionDetailsModal />
    </div>
  );
};