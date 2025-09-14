/**
 * WorkflowScheduler - Component for managing workflow scheduling
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Clock,
  Play,
  Pause,
  Settings,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Plus,
  Edit,
  Trash2,
  Filter,
  Search
} from 'lucide-react';
import type { WorkflowDefinition, WorkflowSchedule } from '../../../types/workflow';
import { WorkflowManagementService } from '../../../services/workflowManagementService';

export interface WorkflowSchedulerProps {
  workflowId?: string;
  onScheduleUpdate?: (schedule: WorkflowSchedule) => void;
}

interface ScheduledWorkflow extends WorkflowDefinition {
  nextExecution?: Date;
  lastExecution?: Date;
  executionCount: number;
  averageExecutionTime: number;
}

const workflowService = new WorkflowManagementService();

export const WorkflowScheduler: React.FC<WorkflowSchedulerProps> = ({
  workflowId,
  onScheduleUpdate
}) => {
  const [scheduledWorkflows, setScheduledWorkflows] = useState<ScheduledWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<ScheduledWorkflow | null>(null);

  // Load scheduled workflows
  const loadScheduledWorkflows = useCallback(async () => {
    try {
      setLoading(true);
      const workflows = await workflowService.getScheduledWorkflows();
      setScheduledWorkflows(workflows);
      setError(null);
    } catch (err) {
      setError('Failed to load scheduled workflows');
      console.error('Failed to load scheduled workflows:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadScheduledWorkflows();
  }, [loadScheduledWorkflows]);

  // Filter workflows
  const filteredWorkflows = scheduledWorkflows.filter(workflow => {
    const matchesSearch = workflow.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         workflow.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || workflow.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Handle schedule workflow
  const handleScheduleWorkflow = (workflow: ScheduledWorkflow) => {
    setSelectedWorkflow(workflow);
    setShowScheduleModal(true);
  };

  // Handle pause/resume workflow
  const handleToggleWorkflow = async (workflowId: string, currentStatus: string) => {
    try {
      const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
      await workflowService.updateWorkflowStatus(workflowId, newStatus);
      await loadScheduledWorkflows();
    } catch (err) {
      console.error('Failed to toggle workflow:', err);
      setError(`Failed to ${currentStatus === 'active' ? 'pause' : 'resume'} workflow`);
    }
  };

  // Handle manual workflow execution
  const handleExecuteWorkflow = async (workflowId: string) => {
    try {
      await workflowService.executeWorkflow(workflowId);
      await loadScheduledWorkflows();
    } catch (err) {
      console.error('Failed to execute workflow:', err);
      setError('Failed to execute workflow manually');
    }
  };

  // Handle workflow error recovery
  const handleRecoverWorkflow = async (workflowId: string) => {
    try {
      await workflowService.updateWorkflowStatus(workflowId, 'active');
      await loadScheduledWorkflows();
    } catch (err) {
      console.error('Failed to recover workflow:', err);
      setError('Failed to recover workflow from error state');
    }
  };

  // Schedule modal component
  const ScheduleModal: React.FC = () => {
    const [schedule, setSchedule] = useState<Partial<WorkflowSchedule>>({
      type: 'recurring',
      startDate: new Date(),
      timezone: 'UTC',
      enabled: true
    });

    const handleSave = async () => {
      if (!selectedWorkflow) return;
      
      try {
        await workflowService.updateWorkflowSchedule(selectedWorkflow.id, schedule as WorkflowSchedule);
        onScheduleUpdate?.(schedule as WorkflowSchedule);
        setShowScheduleModal(false);
        await loadScheduledWorkflows();
      } catch (err) {
        console.error('Failed to update schedule:', err);
      }
    };

    if (!showScheduleModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
          <h3 className="text-lg font-semibold text-white mb-4">
            Schedule Workflow: {selectedWorkflow?.name}
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Schedule Type
              </label>
              <select
                value={schedule.type}
                onChange={(e) => setSchedule({ ...schedule, type: e.target.value as 'once' | 'recurring' })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="once">Run Once</option>
                <option value="recurring">Recurring</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Start Date
              </label>
              <input
                type="datetime-local"
                value={schedule.startDate?.toISOString().slice(0, 16)}
                onChange={(e) => setSchedule({ ...schedule, startDate: new Date(e.target.value) })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>

            {schedule.type === 'recurring' && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Cron Expression
                </label>
                <input
                  type="text"
                  placeholder="0 0 * * *"
                  value={schedule.cron || ''}
                  onChange={(e) => setSchedule({ ...schedule, cron: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Example: "0 0 * * *" for daily at midnight
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Timezone
              </label>
              <select
                value={schedule.timezone}
                onChange={(e) => setSchedule({ ...schedule, timezone: e.target.value })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="UTC">UTC</option>
                <option value="America/New_York">Eastern Time</option>
                <option value="America/Chicago">Central Time</option>
                <option value="America/Denver">Mountain Time</option>
                <option value="America/Los_Angeles">Pacific Time</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="enabled"
                checked={schedule.enabled}
                onChange={(e) => setSchedule({ ...schedule, enabled: e.target.checked })}
                className="mr-2"
              />
              <label htmlFor="enabled" className="text-sm text-gray-300">
                Enable schedule
              </label>
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={() => setShowScheduleModal(false)}
              className="px-4 py-2 text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Save Schedule
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
          onClick={loadScheduledWorkflows}
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
        <h2 className="text-2xl font-bold mb-2">Workflow Scheduler</h2>
        <p className="text-gray-400">Manage and monitor scheduled workflow executions</p>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search workflows..."
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
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="error">Error</option>
          </select>
        </div>
        <button
          onClick={loadScheduledWorkflows}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Workflows List */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        {filteredWorkflows.length === 0 ? (
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Scheduled Workflows</h3>
            <p className="text-gray-400">No workflows match your current filters.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {filteredWorkflows.map(workflow => (
              <div key={workflow.id} className="p-4 hover:bg-gray-700/50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="font-medium text-white">{workflow.name}</h3>
                      <span className={`px-2 py-1 rounded text-xs ${
                        workflow.status === 'active' 
                          ? 'bg-green-400/10 text-green-400'
                          : workflow.status === 'error'
                          ? 'bg-red-400/10 text-red-400'
                          : 'bg-gray-400/10 text-gray-400'
                      }`}>
                        {workflow.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mt-1">{workflow.description}</p>
                    
                    <div className="flex items-center space-x-6 mt-2 text-sm text-gray-400">
                      {workflow.nextExecution && (
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          Next: {workflow.nextExecution.toLocaleString()}
                        </div>
                      )}
                      {workflow.lastExecution && (
                        <div className="flex items-center">
                          <Calendar className="w-4 h-4 mr-1" />
                          Last: {workflow.lastExecution.toLocaleString()}
                        </div>
                      )}
                      <div>Executions: {workflow.executionCount}</div>
                      <div>Avg Time: {workflow.averageExecutionTime}ms</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleScheduleWorkflow(workflow)}
                      className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded"
                      title="Edit Schedule"
                    >
                      <Settings className="w-4 h-4" />
                    </button>
                    
                    {/* Manual execution button */}
                    <button
                      onClick={() => handleExecuteWorkflow(workflow.id)}
                      className="p-2 text-blue-400 hover:text-white hover:bg-blue-400/10 rounded"
                      title="Execute Now"
                      disabled={workflow.status === 'error'}
                    >
                      <Play className="w-4 h-4" />
                    </button>

                    {/* Error recovery button */}
                    {workflow.status === 'error' && (
                      <button
                        onClick={() => handleRecoverWorkflow(workflow.id)}
                        className="p-2 text-orange-400 hover:text-white hover:bg-orange-400/10 rounded"
                        title="Recover from Error"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    )}
                    
                    <button
                      onClick={() => handleToggleWorkflow(workflow.id, workflow.status)}
                      className={`p-2 rounded ${
                        workflow.status === 'active'
                          ? 'text-yellow-400 hover:bg-yellow-400/10'
                          : workflow.status === 'error'
                          ? 'text-red-400 hover:bg-red-400/10'
                          : 'text-green-400 hover:bg-green-400/10'
                      }`}
                      title={
                        workflow.status === 'active' ? 'Pause' : 
                        workflow.status === 'error' ? 'Cannot toggle - in error state' : 'Resume'
                      }
                      disabled={workflow.status === 'error'}
                    >
                      {workflow.status === 'active' ? (
                        <Pause className="w-4 h-4" />
                      ) : workflow.status === 'error' ? (
                        <XCircle className="w-4 h-4" />
                      ) : (
                        <Play className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <ScheduleModal />
    </div>
  );
};