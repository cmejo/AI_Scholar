import React, { useState, useEffect } from 'react';
import { Play, Pause, Settings, Plus, Trash2, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { workflowService } from '../services/workflowService';
import { WorkflowDefinition } from '../types';

export const WorkflowManager: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowDefinition | null>(null);
  const [newWorkflow, setNewWorkflow] = useState({
    name: '',
    description: '',
    triggers: [],
    actions: [],
    conditions: []
  });

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = () => {
    // Mock loading workflows
    const mockWorkflows: WorkflowDefinition[] = [
      {
        id: 'workflow_1',
        name: 'Auto-tag Documents',
        description: 'Automatically tag documents based on content',
        triggers: [{ type: 'document_upload', config: {} }],
        actions: [{ type: 'auto_tag', config: {} }],
        conditions: [],
        status: 'active'
      },
      {
        id: 'workflow_2',
        name: 'Daily Report Generation',
        description: 'Generate daily analytics report',
        triggers: [{ type: 'schedule', config: { cron: '0 9 * * *' } }],
        actions: [{ type: 'generate_report', config: { type: 'daily' } }],
        conditions: [],
        status: 'active'
      },
      {
        id: 'workflow_3',
        name: 'Document Freshness Check',
        description: 'Check for outdated documents',
        triggers: [{ type: 'schedule', config: { cron: '0 0 * * 0' } }],
        actions: [{ type: 'check_freshness', config: {} }],
        conditions: [],
        status: 'inactive'
      }
    ];
    setWorkflows(mockWorkflows);
  };

  const toggleWorkflowStatus = async (workflowId: string) => {
    setWorkflows(prev => prev.map(workflow => 
      workflow.id === workflowId 
        ? { ...workflow, status: workflow.status === 'active' ? 'inactive' : 'active' }
        : workflow
    ));
  };

  const executeWorkflow = async (workflowId: string) => {
    try {
      await workflowService.executeWorkflow(workflowId, { manual: true });
      // Show success notification
    } catch (error) {
      console.error('Failed to execute workflow:', error);
    }
  };

  const createWorkflow = () => {
    const workflow = workflowService.createWorkflow(newWorkflow as any);
    setWorkflows(prev => [...prev, workflow]);
    setShowCreateModal(false);
    setNewWorkflow({ name: '', description: '', triggers: [], actions: [], conditions: [] });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Workflow Manager</h2>
          <p className="text-gray-400">Automate document processing and system tasks</p>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
        >
          <Plus size={16} />
          <span>Create Workflow</span>
        </button>
      </div>

      {/* Workflow Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {workflows.map((workflow) => (
          <WorkflowCard
            key={workflow.id}
            workflow={workflow}
            onToggleStatus={() => toggleWorkflowStatus(workflow.id)}
            onExecute={() => executeWorkflow(workflow.id)}
            onEdit={() => setSelectedWorkflow(workflow)}
          />
        ))}
      </div>

      {/* Workflow Statistics */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Workflow Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">{workflows.length}</div>
            <div className="text-gray-400">Total Workflows</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-400">
              {workflows.filter(w => w.status === 'active').length}
            </div>
            <div className="text-gray-400">Active</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">
              {workflows.filter(w => w.status === 'inactive').length}
            </div>
            <div className="text-gray-400">Inactive</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">156</div>
            <div className="text-gray-400">Executions Today</div>
          </div>
        </div>
      </div>

      {/* Recent Executions */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Executions</h3>
        <div className="space-y-3">
          {[
            { workflow: 'Auto-tag Documents', status: 'success', time: '2 minutes ago', duration: '1.2s' },
            { workflow: 'Daily Report Generation', status: 'success', time: '1 hour ago', duration: '45s' },
            { workflow: 'Document Freshness Check', status: 'failed', time: '3 hours ago', duration: '2.1s' },
            { workflow: 'Auto-tag Documents', status: 'success', time: '5 hours ago', duration: '0.8s' }
          ].map((execution, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
              <div className="flex items-center space-x-3">
                {execution.status === 'success' ? (
                  <CheckCircle className="text-emerald-400" size={16} />
                ) : (
                  <AlertCircle className="text-red-400" size={16} />
                )}
                <div>
                  <div className="text-white font-medium">{execution.workflow}</div>
                  <div className="text-gray-400 text-sm">{execution.time}</div>
                </div>
              </div>
              <div className="text-gray-400 text-sm">
                {execution.duration}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Create Workflow Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-white mb-4">Create New Workflow</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Name</label>
                <input
                  type="text"
                  value={newWorkflow.name}
                  onChange={(e) => setNewWorkflow({ ...newWorkflow, name: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                  placeholder="Workflow name..."
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Description</label>
                <textarea
                  value={newWorkflow.description}
                  onChange={(e) => setNewWorkflow({ ...newWorkflow, description: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                  rows={3}
                  placeholder="Describe what this workflow does..."
                />
              </div>
            </div>
            
            <div className="flex items-center justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={createWorkflow}
                disabled={!newWorkflow.name.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

interface WorkflowCardProps {
  workflow: WorkflowDefinition;
  onToggleStatus: () => void;
  onExecute: () => void;
  onEdit: () => void;
}

const WorkflowCard: React.FC<WorkflowCardProps> = ({
  workflow,
  onToggleStatus,
  onExecute,
  onEdit
}) => {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-1">{workflow.name}</h3>
          <p className="text-gray-400 text-sm">{workflow.description}</p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={onToggleStatus}
            className={`p-2 rounded-lg transition-colors ${
              workflow.status === 'active'
                ? 'bg-emerald-600 hover:bg-emerald-700'
                : 'bg-gray-600 hover:bg-gray-700'
            }`}
          >
            {workflow.status === 'active' ? <Pause size={16} /> : <Play size={16} />}
          </button>
          
          <button
            onClick={onEdit}
            className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
          >
            <Settings size={16} />
          </button>
        </div>
      </div>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Status:</span>
          <span className={`px-2 py-1 rounded-full text-xs ${
            workflow.status === 'active'
              ? 'bg-emerald-600/20 text-emerald-400'
              : 'bg-gray-600/20 text-gray-400'
          }`}>
            {workflow.status}
          </span>
        </div>
        
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Triggers:</span>
          <span className="text-white">{workflow.triggers.length}</span>
        </div>
        
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Actions:</span>
          <span className="text-white">{workflow.actions.length}</span>
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-700">
        <button
          onClick={onExecute}
          disabled={workflow.status !== 'active'}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
        >
          <Play size={16} />
          <span>Execute Now</span>
        </button>
      </div>
    </div>
  );
};