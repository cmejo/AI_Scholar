import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { 
  Play, Pause, Square, Settings, Plus, Edit, Trash2,
  Clock, CheckCircle, XCircle, AlertCircle, BarChart3,
  Workflow, Zap, Calendar, Users, ArrowRight, Copy
} from 'lucide-react';

interface WorkflowStep {
  id: string;
  name: string;
  type: 'trigger' | 'action' | 'condition' | 'delay';
  config: Record<string, any>;
  status: 'pending' | 'running' | 'completed' | 'failed';
  duration?: number;
}

interface WorkflowExecution {
  id: string;
  workflowId: string;
  status: 'running' | 'completed' | 'failed' | 'paused';
  startTime: Date;
  endTime?: Date;
  currentStep: number;
  totalSteps: number;
  logs: string[];
}

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: 'data_processing' | 'user_management' | 'security' | 'analytics' | 'integration';
  steps: WorkflowStep[];
  isActive: boolean;
  lastRun?: Date;
  totalRuns: number;
  successRate: number;
  avgDuration: number;
}

export const WorkflowManager: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowTemplate[]>([]);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [activeTab, setActiveTab] = useState<'workflows' | 'executions' | 'templates' | 'analytics'>('workflows');
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowTemplate | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // Mock data generation
  useEffect(() => {
    const mockWorkflows: WorkflowTemplate[] = [
      {
        id: 'wf_1',
        name: 'User Onboarding Automation',
        description: 'Automated user registration, email verification, and initial setup',
        category: 'user_management',
        steps: [
          { id: 'step_1', name: 'User Registration', type: 'trigger', config: {}, status: 'completed' },
          { id: 'step_2', name: 'Send Welcome Email', type: 'action', config: {}, status: 'completed' },
          { id: 'step_3', name: 'Create User Profile', type: 'action', config: {}, status: 'running' },
          { id: 'step_4', name: 'Assign Default Permissions', type: 'action', config: {}, status: 'pending' }
        ],
        isActive: true,
        lastRun: new Date(Date.now() - 2 * 60 * 60 * 1000),
        totalRuns: 156,
        successRate: 94.2,
        avgDuration: 45
      },
      {
        id: 'wf_2',
        name: 'Document Processing Pipeline',
        description: 'Automated document upload, processing, indexing, and notification',
        category: 'data_processing',
        steps: [
          { id: 'step_1', name: 'Document Upload', type: 'trigger', config: {}, status: 'completed' },
          { id: 'step_2', name: 'Virus Scan', type: 'action', config: {}, status: 'completed' },
          { id: 'step_3', name: 'Extract Text', type: 'action', config: {}, status: 'completed' },
          { id: 'step_4', name: 'Generate Embeddings', type: 'action', config: {}, status: 'completed' },
          { id: 'step_5', name: 'Index Document', type: 'action', config: {}, status: 'completed' }
        ],
        isActive: true,
        lastRun: new Date(Date.now() - 30 * 60 * 1000),
        totalRuns: 89,
        successRate: 98.9,
        avgDuration: 120
      },
      {
        id: 'wf_3',
        name: 'Security Monitoring Alert',
        description: 'Real-time security event detection and notification system',
        category: 'security',
        steps: [
          { id: 'step_1', name: 'Security Event Detected', type: 'trigger', config: {}, status: 'completed' },
          { id: 'step_2', name: 'Analyze Threat Level', type: 'condition', config: {}, status: 'completed' },
          { id: 'step_3', name: 'Send Alert', type: 'action', config: {}, status: 'failed' },
          { id: 'step_4', name: 'Log Incident', type: 'action', config: {}, status: 'pending' }
        ],
        isActive: true,
        lastRun: new Date(Date.now() - 10 * 60 * 1000),
        totalRuns: 234,
        successRate: 87.6,
        avgDuration: 15
      }
    ];

    const mockExecutions: WorkflowExecution[] = [
      {
        id: 'exec_1',
        workflowId: 'wf_1',
        status: 'running',
        startTime: new Date(Date.now() - 5 * 60 * 1000),
        currentStep: 2,
        totalSteps: 4,
        logs: [
          'Started workflow execution',
          'User registration completed',
          'Welcome email sent',
          'Creating user profile...'
        ]
      },
      {
        id: 'exec_2',
        workflowId: 'wf_2',
        status: 'completed',
        startTime: new Date(Date.now() - 30 * 60 * 1000),
        endTime: new Date(Date.now() - 28 * 60 * 1000),
        currentStep: 5,
        totalSteps: 5,
        logs: [
          'Document uploaded successfully',
          'Virus scan passed',
          'Text extraction completed',
          'Embeddings generated',
          'Document indexed successfully'
        ]
      }
    ];

    setWorkflows(mockWorkflows);
    setExecutions(mockExecutions);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Play className="w-4 h-4 text-blue-500" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'paused': return <Pause className="w-4 h-4 text-yellow-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getCategoryColor = (category: WorkflowTemplate['category']) => {
    switch (category) {
      case 'data_processing': return 'bg-blue-100 text-blue-800';
      case 'user_management': return 'bg-green-100 text-green-800';
      case 'security': return 'bg-red-100 text-red-800';
      case 'analytics': return 'bg-purple-100 text-purple-800';
      case 'integration': return 'bg-orange-100 text-orange-800';
    }
  };

  const executeWorkflow = (workflowId: string) => {
    const workflow = workflows.find(w => w.id === workflowId);
    if (!workflow) return;

    const newExecution: WorkflowExecution = {
      id: `exec_${Date.now()}`,
      workflowId,
      status: 'running',
      startTime: new Date(),
      currentStep: 1,
      totalSteps: workflow.steps.length,
      logs: ['Workflow execution started']
    };

    setExecutions(prev => [newExecution, ...prev]);
  };

  const pauseExecution = (executionId: string) => {
    setExecutions(prev =>
      prev.map(exec =>
        exec.id === executionId ? { ...exec, status: 'paused' as const } : exec
      )
    );
  };

  const stopExecution = (executionId: string) => {
    setExecutions(prev =>
      prev.map(exec =>
        exec.id === executionId 
          ? { ...exec, status: 'failed' as const, endTime: new Date() } 
          : exec
      )
    );
  };

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Workflow className="w-8 h-8 text-purple-600" />
            Workflow Manager
          </h1>
          <p className="text-gray-600 mt-1">Intelligent process automation and workflow orchestration</p>
        </div>
        
        <div className="flex gap-3">
          <Button variant="outline" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Analytics
          </Button>
          <Button 
            className="bg-purple-600 hover:bg-purple-700 flex items-center gap-2"
            onClick={() => setIsCreating(true)}
          >
            <Plus className="w-4 h-4" />
            Create Workflow
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100">Active Workflows</p>
                <p className="text-3xl font-bold">{workflows.filter(w => w.isActive).length}</p>
              </div>
              <Workflow className="w-8 h-8 text-purple-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100">Running Executions</p>
                <p className="text-3xl font-bold">{executions.filter(e => e.status === 'running').length}</p>
              </div>
              <Play className="w-8 h-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100">Success Rate</p>
                <p className="text-3xl font-bold">
                  {Math.round(workflows.reduce((acc, w) => acc + w.successRate, 0) / workflows.length)}%
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-orange-500 to-orange-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100">Total Executions</p>
                <p className="text-3xl font-bold">{workflows.reduce((acc, w) => acc + w.totalRuns, 0)}</p>
              </div>
              <Zap className="w-8 h-8 text-orange-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-1 bg-gray-200 p-1 rounded-lg">
        {[
          { id: 'workflows', label: 'Workflows', icon: Workflow },
          { id: 'executions', label: 'Executions', icon: Play },
          { id: 'templates', label: 'Templates', icon: Copy },
          { id: 'analytics', label: 'Analytics', icon: BarChart3 }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-purple-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'workflows' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {workflows.map(workflow => (
            <Card key={workflow.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{workflow.name}</CardTitle>
                    <p className="text-sm text-gray-600 mt-1">{workflow.description}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getCategoryColor(workflow.category)}`}>
                    {workflow.category.replace('_', ' ')}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Workflow Steps Preview */}
                  <div className="flex items-center gap-2 overflow-x-auto pb-2">
                    {workflow.steps.map((step, index) => (
                      <React.Fragment key={step.id}>
                        <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs whitespace-nowrap ${
                          step.status === 'completed' ? 'bg-green-100 text-green-800' :
                          step.status === 'running' ? 'bg-blue-100 text-blue-800' :
                          step.status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {getStatusIcon(step.status)}
                          {step.name}
                        </div>
                        {index < workflow.steps.length - 1 && (
                          <ArrowRight className="w-3 h-3 text-gray-400 flex-shrink-0" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>

                  {/* Workflow Stats */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Success Rate:</span>
                      <span className="font-semibold ml-1">{workflow.successRate}%</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Avg Duration:</span>
                      <span className="font-semibold ml-1">{workflow.avgDuration}s</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Total Runs:</span>
                      <span className="font-semibold ml-1">{workflow.totalRuns}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Last Run:</span>
                      <span className="font-semibold ml-1">
                        {workflow.lastRun ? workflow.lastRun.toLocaleTimeString() : 'Never'}
                      </span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-2">
                    <Button
                      size="sm"
                      className="flex-1"
                      onClick={() => executeWorkflow(workflow.id)}
                      disabled={!workflow.isActive}
                    >
                      <Play className="w-3 h-3 mr-1" />
                      Execute
                    </Button>
                    <Button size="sm" variant="outline">
                      <Edit className="w-3 h-3" />
                    </Button>
                    <Button size="sm" variant="outline">
                      <Settings className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'executions' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Play className="w-5 h-5" />
              Recent Executions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {executions.map(execution => {
                const workflow = workflows.find(w => w.id === execution.workflowId);
                return (
                  <div key={execution.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-medium">{workflow?.name || 'Unknown Workflow'}</h4>
                        <p className="text-sm text-gray-600">
                          Started: {execution.startTime.toLocaleString()}
                          {execution.endTime && ` • Ended: ${execution.endTime.toLocaleString()}`}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(execution.status)}
                        <span className="text-sm font-medium capitalize">{execution.status}</span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-3">
                      <div className="flex justify-between text-sm text-gray-600 mb-1">
                        <span>Progress</span>
                        <span>{execution.currentStep}/{execution.totalSteps} steps</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${(execution.currentStep / execution.totalSteps) * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* Execution Logs */}
                    <div className="bg-gray-50 rounded p-3 mb-3">
                      <h5 className="text-sm font-medium mb-2">Execution Log:</h5>
                      <div className="space-y-1 max-h-32 overflow-y-auto">
                        {execution.logs.map((log, index) => (
                          <div key={index} className="text-xs text-gray-600 font-mono">
                            {log}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    {execution.status === 'running' && (
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => pauseExecution(execution.id)}>
                          <Pause className="w-3 h-3 mr-1" />
                          Pause
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => stopExecution(execution.id)}>
                          <Square className="w-3 h-3 mr-1" />
                          Stop
                        </Button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'templates' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { name: 'Data Backup Automation', category: 'data_processing', description: 'Automated daily data backup and verification' },
            { name: 'User Deactivation Process', category: 'user_management', description: 'Secure user account deactivation workflow' },
            { name: 'Incident Response', category: 'security', description: 'Automated security incident response and escalation' },
            { name: 'Report Generation', category: 'analytics', description: 'Scheduled report generation and distribution' },
            { name: 'API Integration Sync', category: 'integration', description: 'Third-party API data synchronization' },
            { name: 'Content Moderation', category: 'data_processing', description: 'Automated content review and moderation' }
          ].map((template, index) => (
            <Card key={index} className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-medium">{template.name}</h3>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getCategoryColor(template.category as any)}`}>
                    {template.category.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-4">{template.description}</p>
                <Button size="sm" className="w-full">
                  <Plus className="w-3 h-3 mr-1" />
                  Use Template
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Workflow Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {workflows.map(workflow => (
                  <div key={workflow.id} className="flex justify-between items-center">
                    <div>
                      <div className="font-medium">{workflow.name}</div>
                      <div className="text-sm text-gray-600">{workflow.totalRuns} executions</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">{workflow.successRate}%</div>
                      <div className="text-sm text-gray-600">{workflow.avgDuration}s avg</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Execution Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>Daily Executions</span>
                  <span className="font-semibold">47</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Weekly Success Rate</span>
                  <span className="font-semibold text-green-600">94.2%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Average Duration</span>
                  <span className="font-semibold">68s</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Failed Executions</span>
                  <span className="font-semibold text-red-600">3</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};