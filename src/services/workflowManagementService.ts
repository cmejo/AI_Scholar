// Workflow Management Service
import type {
  WorkflowDefinition,
  WorkflowExecution,
  WorkflowTemplate,
  WorkflowStats,
  WorkflowFilter,
  WorkflowSort
} from '../types/workflow';
import type { PaginatedResponse } from '../types/api';

export class WorkflowManagementService {
  private baseUrl = '/api/workflows';

  /**
   * Get workflow statistics
   */
  async getWorkflowStats(): Promise<WorkflowStats> {
    try {
      const response = await fetch(`${this.baseUrl}/stats`);
      if (!response.ok) {
        throw new Error(`Failed to fetch workflow stats: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data || this.getMockStats();
    } catch (error) {
      console.warn('Using mock workflow stats:', error);
      return this.getMockStats();
    }
  }

  /**
   * Get paginated list of workflows
   */
  async getWorkflows(
    page = 1,
    limit = 10,
    filter?: WorkflowFilter,
    sort?: WorkflowSort
  ): Promise<PaginatedResponse<WorkflowDefinition>> {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        ...(filter?.status && { status: filter.status.join(',') }),
        ...(filter?.search && { search: filter.search }),
        ...(sort && { sort: sort.field, order: sort.direction })
      });

      const response = await fetch(`${this.baseUrl}?${params}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch workflows: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data || this.getMockWorkflows(page, limit, filter);
    } catch (error) {
      console.warn('Using mock workflows:', error);
      return this.getMockWorkflows(page, limit, filter);
    }
  }

  /**
   * Get workflow by ID
   */
  async getWorkflow(id: string): Promise<WorkflowDefinition> {
    try {
      const response = await fetch(`${this.baseUrl}/${id}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch workflow: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data || this.getMockWorkflow(id);
    } catch (error) {
      console.warn('Using mock workflow:', error);
      return this.getMockWorkflow(id);
    }
  }

  /**
   * Create new workflow
   */
  async createWorkflow(workflow: Omit<WorkflowDefinition, 'id' | 'createdAt' | 'updatedAt' | 'createdBy'>): Promise<WorkflowDefinition> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflow)
      });
      if (!response.ok) {
        throw new Error(`Failed to create workflow: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.warn('Mock workflow creation:', error);
      return {
        ...workflow,
        id: `workflow_${Date.now()}`,
        createdBy: 'user',
        createdAt: new Date(),
        updatedAt: new Date()
      } as WorkflowDefinition;
    }
  }

  /**
   * Update workflow
   */
  async updateWorkflow(id: string, updates: Partial<WorkflowDefinition>): Promise<WorkflowDefinition> {
    try {
      const response = await fetch(`${this.baseUrl}/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (!response.ok) {
        throw new Error(`Failed to update workflow: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.warn('Mock workflow update:', error);
      const existing = await this.getWorkflow(id);
      return { ...existing, ...updates, updatedAt: new Date() };
    }
  }

  /**
   * Delete workflow
   */
  async deleteWorkflow(id: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/${id}`, {
        method: 'DELETE'
      });
      if (!response.ok) {
        throw new Error(`Failed to delete workflow: ${response.statusText}`);
      }
    } catch (error) {
      console.warn('Mock workflow deletion:', error);
    }
  }

  /**
   * Execute workflow manually
   */
  async executeWorkflow(id: string, context?: Record<string, unknown>): Promise<WorkflowExecution> {
    try {
      const response = await fetch(`${this.baseUrl}/${id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context })
      });
      if (!response.ok) {
        throw new Error(`Failed to execute workflow: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.warn('Mock workflow execution:', error);
      return this.getMockExecution(id);
    }
  }

  /**
   * Get workflow executions
   */
  async getWorkflowExecutions(
    workflowId: string,
    page = 1,
    limit = 10
  ): Promise<PaginatedResponse<WorkflowExecution>> {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString()
      });

      const response = await fetch(`${this.baseUrl}/${workflowId}/executions?${params}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch executions: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data || this.getMockExecutions(workflowId, page, limit);
    } catch (error) {
      console.warn('Using mock executions:', error);
      return this.getMockExecutions(workflowId, page, limit);
    }
  }

  /**
   * Get workflow templates
   */
  async getWorkflowTemplates(): Promise<WorkflowTemplate[]> {
    try {
      const response = await fetch(`${this.baseUrl}/templates`);
      if (!response.ok) {
        throw new Error(`Failed to fetch templates: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data || this.getMockTemplates();
    } catch (error) {
      console.warn('Using mock templates:', error);
      return this.getMockTemplates();
    }
  }

  /**
   * Toggle workflow status
   */
  async toggleWorkflowStatus(id: string): Promise<WorkflowDefinition> {
    const workflow = await this.getWorkflow(id);
    const newStatus = workflow.status === 'active' ? 'inactive' : 'active';
    return this.updateWorkflow(id, { status: newStatus });
  }

  /**
   * Get scheduled workflows
   */
  async getScheduledWorkflows(): Promise<any[]> {
    try {
      const response = await fetch(`${this.baseUrl}/scheduled`);
      if (!response.ok) {
        throw new Error(`Failed to fetch scheduled workflows: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data || this.getMockScheduledWorkflows();
    } catch (error) {
      console.warn('Using mock scheduled workflows:', error);
      return this.getMockScheduledWorkflows();
    }
  }

  /**
   * Update workflow status
   */
  async updateWorkflowStatus(workflowId: string, status: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/${workflowId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (!response.ok) {
        throw new Error(`Failed to update workflow status: ${response.statusText}`);
      }
    } catch (error) {
      console.warn('Mock workflow status update:', error);
    }
  }

  /**
   * Update workflow schedule
   */
  async updateWorkflowSchedule(workflowId: string, schedule: any): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/${workflowId}/schedule`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(schedule)
      });
      if (!response.ok) {
        throw new Error(`Failed to update workflow schedule: ${response.statusText}`);
      }
    } catch (error) {
      console.warn('Mock workflow schedule update:', error);
    }
  }

  /**
   * Get execution statistics
   */
  async getExecutionStats(workflowId?: string): Promise<any> {
    try {
      const params = workflowId ? `?workflowId=${workflowId}` : '';
      const response = await fetch(`${this.baseUrl}/execution-stats${params}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch execution stats: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data || this.getMockExecutionStats();
    } catch (error) {
      console.warn('Using mock execution stats:', error);
      return this.getMockExecutionStats();
    }
  }

  /**
   * Cancel workflow execution
   */
  async cancelExecution(executionId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/executions/${executionId}/cancel`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error(`Failed to cancel execution: ${response.statusText}`);
      }
    } catch (error) {
      console.warn('Mock execution cancellation:', error);
    }
  }

  /**
   * Retry failed workflow execution
   */
  async retryExecution(executionId: string): Promise<WorkflowExecution> {
    try {
      const response = await fetch(`${this.baseUrl}/executions/${executionId}/retry`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error(`Failed to retry execution: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.warn('Mock execution retry:', error);
      return this.getMockExecution('retry_' + executionId);
    }
  }

  /**
   * Get workflow execution by ID
   */
  async getExecution(executionId: string): Promise<WorkflowExecution> {
    try {
      const response = await fetch(`${this.baseUrl}/executions/${executionId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch execution: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.warn('Using mock execution:', error);
      return this.getMockExecution(executionId);
    }
  }

  /**
   * Get real-time execution status
   */
  async getExecutionStatus(executionId: string): Promise<{ status: string; progress?: number; currentStep?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/executions/${executionId}/status`);
      if (!response.ok) {
        throw new Error(`Failed to fetch execution status: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data || { status: 'unknown' };
    } catch (error) {
      console.warn('Using mock execution status:', error);
      return { status: 'unknown' };
    }
  }

  // Mock data methods
  private getMockStats(): WorkflowStats {
    return {
      totalWorkflows: 12,
      activeWorkflows: 8,
      pausedWorkflows: 3,
      errorWorkflows: 1,
      totalExecutions: 156,
      successfulExecutions: 142,
      failedExecutions: 14,
      averageExecutionTime: 2.3,
      executionsToday: 23,
      scheduledExecutions: 5
    };
  }

  private getMockWorkflows(page: number, limit: number, filter?: WorkflowFilter): PaginatedResponse<WorkflowDefinition> {
    const mockWorkflows: WorkflowDefinition[] = [
      {
        id: 'wf_1',
        name: 'Auto-tag Documents',
        description: 'Automatically tag documents based on content analysis',
        status: 'active',
        createdBy: 'admin',
        createdAt: new Date('2024-01-15'),
        updatedAt: new Date('2024-01-20'),
        lastRun: new Date('2024-01-25T10:30:00'),
        nextRun: new Date('2024-01-26T10:30:00'),
        triggers: [{
          id: 'trigger_1',
          type: 'document_upload',
          config: { fileTypes: ['pdf', 'docx'] },
          enabled: true
        }],
        conditions: [{
          id: 'cond_1',
          type: 'document_size',
          operator: 'greater_than',
          value: 1024
        }],
        actions: [{
          id: 'action_1',
          type: 'auto_tag',
          name: 'Tag Document',
          config: { aiModel: 'gpt-4' },
          enabled: true,
          order: 1
        }],
        tags: ['automation', 'tagging'],
        version: 1,
        isTemplate: false
      },
      {
        id: 'wf_2',
        name: 'Daily Analytics Report',
        description: 'Generate and send daily analytics reports',
        status: 'active',
        createdBy: 'admin',
        createdAt: new Date('2024-01-10'),
        updatedAt: new Date('2024-01-15'),
        lastRun: new Date('2024-01-25T09:00:00'),
        nextRun: new Date('2024-01-26T09:00:00'),
        triggers: [{
          id: 'trigger_2',
          type: 'schedule',
          config: { cron: '0 9 * * *' },
          enabled: true
        }],
        conditions: [],
        actions: [{
          id: 'action_2',
          type: 'generate_summary',
          name: 'Generate Report',
          config: { reportType: 'daily' },
          enabled: true,
          order: 1
        }],
        schedule: {
          type: 'recurring',
          startDate: new Date('2024-01-10'),
          cron: '0 9 * * *',
          timezone: 'UTC',
          enabled: true
        },
        tags: ['reporting', 'analytics'],
        version: 2,
        isTemplate: false
      },
      {
        id: 'wf_3',
        name: 'Document Backup',
        description: 'Create backups of important documents',
        status: 'inactive',
        createdBy: 'user1',
        createdAt: new Date('2024-01-05'),
        updatedAt: new Date('2024-01-10'),
        triggers: [{
          id: 'trigger_3',
          type: 'manual',
          config: {},
          enabled: true
        }],
        conditions: [{
          id: 'cond_2',
          type: 'document_type',
          operator: 'equals',
          value: 'important'
        }],
        actions: [{
          id: 'action_3',
          type: 'create_backup',
          name: 'Backup Document',
          config: { location: 's3://backups' },
          enabled: true,
          order: 1
        }],
        tags: ['backup', 'storage'],
        version: 1,
        isTemplate: false
      }
    ];

    // Apply filters
    let filteredWorkflows = mockWorkflows;
    if (filter?.status) {
      filteredWorkflows = filteredWorkflows.filter(w => filter.status!.includes(w.status));
    }
    if (filter?.search) {
      const search = filter.search.toLowerCase();
      filteredWorkflows = filteredWorkflows.filter(w => 
        w.name.toLowerCase().includes(search) || 
        w.description.toLowerCase().includes(search)
      );
    }

    const total = filteredWorkflows.length;
    const start = (page - 1) * limit;
    const end = start + limit;
    const data = filteredWorkflows.slice(start, end);

    return {
      data,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
        hasNext: end < total,
        hasPrev: page > 1
      }
    };
  }

  private getMockWorkflow(id: string): WorkflowDefinition {
    const workflows = this.getMockWorkflows(1, 10).data;
    const found = workflows.find(w => w.id === id);
    if (!found) {
      throw new Error(`Workflow with id ${id} not found`);
    }
    return found;
  }

  private getMockExecution(workflowId: string): WorkflowExecution {
    return {
      id: `exec_${Date.now()}`,
      workflowId,
      status: 'running',
      startTime: new Date(),
      triggeredBy: 'user',
      triggerType: 'manual',
      logs: [{
        id: 'log_1',
        timestamp: new Date(),
        level: 'info',
        message: 'Workflow execution started'
      }],
      results: [],
      context: {}
    };
  }

  private getMockExecutions(workflowId: string, page: number, limit: number): PaginatedResponse<WorkflowExecution> {
    const mockExecutions: WorkflowExecution[] = [
      {
        id: 'exec_1',
        workflowId,
        status: 'completed',
        startTime: new Date('2024-01-25T10:30:00'),
        endTime: new Date('2024-01-25T10:32:15'),
        duration: 135000,
        triggeredBy: 'system',
        triggerType: 'schedule',
        logs: [
          {
            id: 'log_1',
            timestamp: new Date('2024-01-25T10:30:00'),
            level: 'info',
            message: 'Workflow execution started'
          },
          {
            id: 'log_2',
            timestamp: new Date('2024-01-25T10:32:15'),
            level: 'info',
            message: 'Workflow execution completed successfully'
          }
        ],
        results: [{
          actionId: 'action_1',
          actionName: 'Tag Document',
          status: 'success',
          result: { tags: ['research', 'ai'] },
          duration: 120000
        }],
        context: { documentId: 'doc_123' }
      },
      {
        id: 'exec_2',
        workflowId,
        status: 'failed',
        startTime: new Date('2024-01-24T10:30:00'),
        endTime: new Date('2024-01-24T10:31:30'),
        duration: 90000,
        triggeredBy: 'user1',
        triggerType: 'manual',
        logs: [
          {
            id: 'log_3',
            timestamp: new Date('2024-01-24T10:30:00'),
            level: 'info',
            message: 'Workflow execution started'
          },
          {
            id: 'log_4',
            timestamp: new Date('2024-01-24T10:31:30'),
            level: 'error',
            message: 'Action failed: API timeout'
          }
        ],
        results: [{
          actionId: 'action_1',
          actionName: 'Tag Document',
          status: 'failed',
          error: 'API timeout after 30 seconds',
          duration: 30000
        }],
        error: 'Workflow failed due to API timeout',
        context: { documentId: 'doc_456' }
      }
    ];

    const total = mockExecutions.length;
    const start = (page - 1) * limit;
    const end = start + limit;
    const data = mockExecutions.slice(start, end);

    return {
      data,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
        hasNext: end < total,
        hasPrev: page > 1
      }
    };
  }

  private getMockTemplates(): WorkflowTemplate[] {
    return [
      {
        id: 'template_1',
        name: 'Document Processing Pipeline',
        description: 'Complete document processing with OCR, tagging, and storage',
        category: 'Document Management',
        tags: ['document', 'ocr', 'automation'],
        popularity: 85,
        isOfficial: true,
        definition: {
          name: 'Document Processing Pipeline',
          description: 'Complete document processing with OCR, tagging, and storage',
          status: 'active',
          triggers: [{
            id: 'trigger_template_1',
            type: 'document_upload',
            config: {},
            enabled: true
          }],
          conditions: [],
          actions: [
            {
              id: 'action_template_1',
              type: 'auto_tag',
              name: 'Auto Tag',
              config: {},
              enabled: true,
              order: 1
            },
            {
              id: 'action_template_2',
              type: 'create_backup',
              name: 'Create Backup',
              config: {},
              enabled: true,
              order: 2
            }
          ],
          tags: ['template'],
          version: 1,
          isTemplate: true
        }
      },
      {
        id: 'template_2',
        name: 'Scheduled Reporting',
        description: 'Automated report generation and distribution',
        category: 'Analytics',
        tags: ['reporting', 'analytics', 'schedule'],
        popularity: 72,
        isOfficial: true,
        definition: {
          name: 'Scheduled Reporting',
          description: 'Automated report generation and distribution',
          status: 'active',
          triggers: [{
            id: 'trigger_template_2',
            type: 'schedule',
            config: { cron: '0 9 * * 1' },
            enabled: true
          }],
          conditions: [],
          actions: [{
            id: 'action_template_3',
            type: 'generate_summary',
            name: 'Generate Report',
            config: { reportType: 'weekly' },
            enabled: true,
            order: 1
          }],
          tags: ['template'],
          version: 1,
          isTemplate: true
        }
      }
    ];
  }

  private getMockScheduledWorkflows(): any[] {
    return [
      {
        id: 'wf_1',
        name: 'Auto-tag Documents',
        description: 'Automatically tag documents based on content analysis',
        status: 'active',
        nextExecution: new Date(Date.now() + 3600000), // 1 hour from now
        lastExecution: new Date(Date.now() - 3600000), // 1 hour ago
        executionCount: 45,
        averageExecutionTime: 2300
      },
      {
        id: 'wf_2',
        name: 'Daily Analytics Report',
        description: 'Generate and send daily analytics reports',
        status: 'active',
        nextExecution: new Date(Date.now() + 86400000), // 24 hours from now
        lastExecution: new Date(Date.now() - 86400000), // 24 hours ago
        executionCount: 30,
        averageExecutionTime: 5600
      }
    ];
  }

  private getMockExecutionStats(): any {
    return {
      totalExecutions: 156,
      successfulExecutions: 142,
      failedExecutions: 14,
      averageExecutionTime: 2300,
      executionsToday: 23,
      successRate: 91.0
    };
  }
}

export const workflowManagementService = new WorkflowManagementService();