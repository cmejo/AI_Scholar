/**
 * WorkflowExecutionTracker - Real-time workflow execution tracking component
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
  Zap,
  BarChart3,
  TrendingUp,
  AlertCircle,
  Info
} from 'lucide-react';
import type { WorkflowExecution } from '../../../types/workflow';
import { WorkflowManagementService } from '../../../services/workflowManagementService';

export interface WorkflowExecutionTrackerProps {
  executionId: string;
  onExecutionComplete?: (execution: WorkflowExecution) => void;
  onExecutionFailed?: (execution: WorkflowExecution, error: string) => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface ExecutionProgress {
  currentStep: string;
  completedSteps: number;
  totalSteps: number;
  progress: number;
  estimatedTimeRemaining?: number;
}

const workflowService = new WorkflowManagementService();

export const WorkflowExecutionTracker: React.FC<WorkflowExecutionTrackerProps> = ({
  executionId,
  onExecutionComplete,
  onExecutionFailed,
  autoRefresh = true,
  refreshInterval = 2000
}) => {
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [progress, setProgress] = useState<ExecutionProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load execution details and status
  const loadExecution = useCallback(async () => {
    try {
      const [executionData, statusData] = await Promise.all([
        workflowService.getExecution(executionId),
        workflowService.getExecutionStatus(executionId)
      ]);
      
      setExecution(executionData);
      
      // Calculate progress if execution is running
      if (executionData.status === 'running' && statusData.progress !== undefined) {
        const completedSteps = Math.floor((statusData.progress / 100) * executionData.results.length);
        setProgress({
          currentStep: statusData.currentStep || 'Processing...',
          completedSteps,
          totalSteps: executionData.results.length || 1,
          progress: statusData.progress,
          estimatedTimeRemaining: calculateEstimatedTime(executionData, statusData.progress)
        });
      } else {
        setProgress(null);
      }

      // Handle execution completion
      if (executionData.status === 'completed' && onExecutionComplete) {
        onExecutionComplete(executionData);
      } else if (executionData.status === 'failed' && onExecutionFailed) {
        onExecutionFailed(executionData, executionData.error || 'Unknown error');
      }

      setError(null);
    } catch (err) {
      setError('Failed to load execution details');
      console.error('Failed to load execution:', err);
    } finally {
      setLoading(false);
    }
  }, [executionId, onExecutionComplete, onExecutionFailed]);

  // Calculate estimated time remaining
  const calculateEstimatedTime = (execution: WorkflowExecution, progress: number): number | undefined => {
    if (!execution.startTime || progress <= 0) return undefined;
    
    const elapsed = Date.now() - execution.startTime.getTime();
    const totalEstimated = (elapsed / progress) * 100;
    return Math.max(0, totalEstimated - elapsed);
  };

  // Auto refresh
  useEffect(() => {
    loadExecution();
    
    if (autoRefresh && execution?.status === 'running') {
      const interval = setInterval(loadExecution, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [loadExecution, autoRefresh, refreshInterval, execution?.status]);

  // Handle cancel execution
  const handleCancel = async () => {
    if (!execution) return;
    
    try {
      await workflowService.cancelExecution(execution.id);
      await loadExecution();
    } catch (err) {
      console.error('Failed to cancel execution:', err);
      setError('Failed to cancel execution');
    }
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
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.color}`}>
        <Icon className="w-4 h-4 mr-2" />
        {config.label}
      </span>
    );
  };

  // Progress bar component
  const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => (
    <div className="w-full bg-gray-700 rounded-full h-2">
      <div
        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
        style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
      />
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    );
  }

  if (error || !execution) {
    return (
      <div className="text-center p-8">
        <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">Error</h3>
        <p className="text-gray-400 mb-4">{error || 'Execution not found'}</p>
        <button
          onClick={loadExecution}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 text-white">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold mb-2">Execution Tracking</h3>
          <p className="text-gray-400 text-sm">ID: {execution.id}</p>
        </div>
        <StatusBadge status={execution.status} />
      </div>

      {/* Execution Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-700 rounded p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Started</p>
              <p className="font-medium">{execution.startTime.toLocaleString()}</p>
            </div>
            <Clock className="w-5 h-5 text-blue-400" />
          </div>
        </div>

        <div className="bg-gray-700 rounded p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Duration</p>
              <p className="font-medium">
                {execution.duration 
                  ? `${(execution.duration / 1000).toFixed(1)}s`
                  : execution.status === 'running'
                  ? `${Math.floor((Date.now() - execution.startTime.getTime()) / 1000)}s`
                  : '-'
                }
              </p>
            </div>
            <BarChart3 className="w-5 h-5 text-purple-400" />
          </div>
        </div>

        <div className="bg-gray-700 rounded p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Triggered By</p>
              <p className="font-medium">{execution.triggeredBy}</p>
            </div>
            <Zap className="w-5 h-5 text-yellow-400" />
          </div>
        </div>
      </div>

      {/* Progress Section */}
      {progress && execution.status === 'running' && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium">Execution Progress</h4>
            <span className="text-sm text-gray-400">{progress.progress.toFixed(1)}%</span>
          </div>
          
          <ProgressBar progress={progress.progress} />
          
          <div className="flex items-center justify-between mt-3 text-sm text-gray-400">
            <span>Current: {progress.currentStep}</span>
            <span>
              {progress.completedSteps} / {progress.totalSteps} steps
            </span>
          </div>

          {progress.estimatedTimeRemaining && (
            <div className="mt-2 text-sm text-gray-400">
              <TrendingUp className="w-4 h-4 inline mr-1" />
              Est. {Math.ceil(progress.estimatedTimeRemaining / 1000)}s remaining
            </div>
          )}
        </div>
      )}

      {/* Error Information */}
      {execution.status === 'failed' && execution.error && (
        <div className="mb-6">
          <div className="bg-red-900/20 border border-red-500/30 rounded p-4">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-red-400 mb-2">Execution Failed</h4>
                <p className="text-red-300 text-sm">{execution.error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Results */}
      {execution.results.length > 0 && (
        <div className="mb-6">
          <h4 className="font-medium mb-3">Action Results</h4>
          <div className="space-y-2">
            {execution.results.map((result, index) => (
              <div key={index} className="bg-gray-700 rounded p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{result.actionName}</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    result.status === 'success' 
                      ? 'bg-green-400/10 text-green-400'
                      : result.status === 'failed'
                      ? 'bg-red-400/10 text-red-400'
                      : 'bg-gray-400/10 text-gray-400'
                  }`}>
                    {result.status}
                  </span>
                </div>
                <p className="text-sm text-gray-400 mt-1">
                  Duration: {(result.duration / 1000).toFixed(2)}s
                </p>
                {result.error && (
                  <p className="text-sm text-red-400 mt-1">Error: {result.error}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Logs */}
      {execution.logs.length > 0 && (
        <div className="mb-6">
          <h4 className="font-medium mb-3">Recent Logs</h4>
          <div className="bg-gray-900 rounded p-4 max-h-32 overflow-y-auto">
            {execution.logs.slice(-5).map((log, index) => (
              <div key={index} className="flex items-start space-x-3 mb-1 text-sm">
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

      {/* Actions */}
      <div className="flex justify-between">
        <div className="flex space-x-3">
          {execution.status === 'running' && (
            <button
              onClick={handleCancel}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 flex items-center"
            >
              <XCircle className="w-4 h-4 mr-2" />
              Cancel
            </button>
          )}
        </div>
        
        <button
          onClick={loadExecution}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 flex items-center"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>
    </div>
  );
};