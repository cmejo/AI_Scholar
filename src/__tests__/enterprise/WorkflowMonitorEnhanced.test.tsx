/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkflowMonitor } from '../../components/enterprise/workflow/WorkflowMonitor';
import { WorkflowManagementService } from '../../services/workflowManagementService';
import type { WorkflowExecution } from '../../types/workflow';

// Mock the workflow service
jest.mock('../../services/workflowManagementService');
const mockWorkflowService = WorkflowManagementService as jest.MockedClass<typeof WorkflowManagementService>;

// Mock URL.createObjectURL for download functionality
global.URL.createObjectURL = jest.fn(() => 'mock-url');
global.URL.revokeObjectURL = jest.fn();

describe('WorkflowMonitor - Enhanced Error Handling and Recovery', () => {
  const mockExecutions: WorkflowExecution[] = [
    {
      id: 'exec_1',
      workflowId: 'wf_1',
      status: 'completed',
      startTime: new Date('2024-01-25T10:30:00Z'),
      endTime: new Date('2024-01-25T10:32:15Z'),
      duration: 135000,
      triggeredBy: 'system',
      triggerType: 'schedule',
      logs: [
        {
          id: 'log_1',
          timestamp: new Date('2024-01-25T10:30:00Z'),
          level: 'info',
          message: 'Workflow execution started'
        },
        {
          id: 'log_2',
          timestamp: new Date('2024-01-25T10:32:15Z'),
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
      workflowId: 'wf_1',
      status: 'failed',
      startTime: new Date('2024-01-24T10:30:00Z'),
      endTime: new Date('2024-01-24T10:31:30Z'),
      duration: 90000,
      triggeredBy: 'user1',
      triggerType: 'manual',
      logs: [
        {
          id: 'log_3',
          timestamp: new Date('2024-01-24T10:30:00Z'),
          level: 'info',
          message: 'Workflow execution started'
        },
        {
          id: 'log_4',
          timestamp: new Date('2024-01-24T10:31:30Z'),
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
    },
    {
      id: 'exec_3',
      workflowId: 'wf_1',
      status: 'running',
      startTime: new Date('2024-01-25T11:00:00Z'),
      triggeredBy: 'user2',
      triggerType: 'manual',
      logs: [
        {
          id: 'log_5',
          timestamp: new Date('2024-01-25T11:00:00Z'),
          level: 'info',
          message: 'Workflow execution started'
        }
      ],
      results: [],
      context: { documentId: 'doc_789' }
    }
  ];

  const mockStats = {
    totalExecutions: 156,
    successfulExecutions: 142,
    failedExecutions: 14,
    averageExecutionTime: 2300,
    executionsToday: 23,
    successRate: 91.0
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockWorkflowService.prototype.getWorkflowExecutions = jest.fn().mockResolvedValue({
      data: mockExecutions,
      pagination: {
        page: 1,
        limit: 10,
        total: mockExecutions.length,
        totalPages: 1,
        hasNext: false,
        hasPrev: false
      }
    });
    mockWorkflowService.prototype.getExecutionStats = jest.fn().mockResolvedValue(mockStats);
    mockWorkflowService.prototype.executeWorkflow = jest.fn().mockResolvedValue({
      id: 'exec_retry',
      workflowId: 'wf_1',
      status: 'running'
    });
    mockWorkflowService.prototype.cancelExecution = jest.fn().mockResolvedValue(undefined);
  });

  it('renders execution monitor with statistics', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      expect(screen.getByText('Workflow Monitor')).toBeInTheDocument();
      expect(screen.getByText('156')).toBeInTheDocument(); // Total executions
      expect(screen.getByText('142')).toBeInTheDocument(); // Successful
      expect(screen.getByText('14')).toBeInTheDocument(); // Failed
      expect(screen.getByText('91.0%')).toBeInTheDocument(); // Success rate
    });
  });

  it('displays executions with different statuses', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();
      expect(screen.getByText('Running')).toBeInTheDocument();
    });
  });

  it('shows retry button for failed executions', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const retryButtons = screen.getAllByTitle('Retry Execution');
      expect(retryButtons).toHaveLength(1); // Only for failed execution
    });
  });

  it('handles retry execution', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const retryButton = screen.getByTitle('Retry Execution');
      fireEvent.click(retryButton);
    });

    expect(mockWorkflowService.prototype.executeWorkflow).toHaveBeenCalledWith(
      'wf_1',
      { documentId: 'doc_456' }
    );
  });

  it('shows cancel button for running executions', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const cancelButtons = screen.getAllByTitle('Cancel Execution');
      expect(cancelButtons).toHaveLength(1); // Only for running execution
    });
  });

  it('handles cancel execution', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const cancelButton = screen.getByTitle('Cancel Execution');
      fireEvent.click(cancelButton);
    });

    expect(mockWorkflowService.prototype.cancelExecution).toHaveBeenCalledWith('exec_3');
  });

  it('shows download logs button for all executions', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const downloadButtons = screen.getAllByTitle('Download Logs');
      expect(downloadButtons).toHaveLength(3); // One for each execution
    });
  });

  it('handles log download', async () => {
    // Mock document methods
    const mockAppendChild = jest.fn();
    const mockRemoveChild = jest.fn();
    const mockClick = jest.fn();
    
    Object.defineProperty(document, 'createElement', {
      value: jest.fn(() => ({
        href: '',
        download: '',
        click: mockClick
      }))
    });
    
    Object.defineProperty(document.body, 'appendChild', {
      value: mockAppendChild
    });
    
    Object.defineProperty(document.body, 'removeChild', {
      value: mockRemoveChild
    });

    render(<WorkflowMonitor />);

    await waitFor(() => {
      const downloadButton = screen.getAllByTitle('Download Logs')[0];
      fireEvent.click(downloadButton);
    });

    expect(global.URL.createObjectURL).toHaveBeenCalled();
    expect(mockClick).toHaveBeenCalled();
  });

  it('opens execution details modal', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const viewButton = screen.getAllByTitle('View Details')[0];
      fireEvent.click(viewButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Execution Details: exec_1')).toBeInTheDocument();
    });
  });

  it('shows error details and recovery suggestions in modal', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const viewButtons = screen.getAllByTitle('View Details');
      fireEvent.click(viewButtons[1]); // Click on failed execution
    });

    await waitFor(() => {
      expect(screen.getByText('Error Details')).toBeInTheDocument();
      expect(screen.getByText('Workflow failed due to API timeout')).toBeInTheDocument();
      expect(screen.getByText('Recovery Suggestions:')).toBeInTheDocument();
      expect(screen.getByText(/Check workflow configuration/)).toBeInTheDocument();
    });
  });

  it('shows retry button in execution details modal for failed executions', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const viewButtons = screen.getAllByTitle('View Details');
      fireEvent.click(viewButtons[1]); // Click on failed execution
    });

    await waitFor(() => {
      expect(screen.getByText('Retry Execution')).toBeInTheDocument();
    });
  });

  it('shows cancel button in execution details modal for running executions', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const viewButtons = screen.getAllByTitle('View Details');
      fireEvent.click(viewButtons[2]); // Click on running execution
    });

    await waitFor(() => {
      expect(screen.getByText('Cancel Execution')).toBeInTheDocument();
    });
  });

  it('handles retry from execution details modal', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const viewButtons = screen.getAllByTitle('View Details');
      fireEvent.click(viewButtons[1]); // Click on failed execution
    });

    await waitFor(() => {
      const retryButton = screen.getByText('Retry Execution');
      fireEvent.click(retryButton);
    });

    expect(mockWorkflowService.prototype.executeWorkflow).toHaveBeenCalledWith(
      'wf_1',
      { documentId: 'doc_456' }
    );
  });

  it('handles cancel from execution details modal', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const viewButtons = screen.getAllByTitle('View Details');
      fireEvent.click(viewButtons[2]); // Click on running execution
    });

    await waitFor(() => {
      const cancelButton = screen.getByText('Cancel Execution');
      fireEvent.click(cancelButton);
    });

    expect(mockWorkflowService.prototype.cancelExecution).toHaveBeenCalledWith('exec_3');
  });

  it('filters executions by status', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const statusFilter = screen.getByDisplayValue('All Status');
      fireEvent.change(statusFilter, { target: { value: 'failed' } });
    });

    // Should show only failed executions
    await waitFor(() => {
      expect(screen.getByText('exec_2')).toBeInTheDocument();
      expect(screen.queryByText('exec_1')).not.toBeInTheDocument();
      expect(screen.queryByText('exec_3')).not.toBeInTheDocument();
    });
  });

  it('searches executions by ID and triggered by', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search executions...');
      fireEvent.change(searchInput, { target: { value: 'user1' } });
    });

    // Should show only executions triggered by user1
    await waitFor(() => {
      expect(screen.getByText('exec_2')).toBeInTheDocument();
      expect(screen.queryByText('exec_1')).not.toBeInTheDocument();
      expect(screen.queryByText('exec_3')).not.toBeInTheDocument();
    });
  });

  it('handles retry errors gracefully', async () => {
    mockWorkflowService.prototype.executeWorkflow = jest.fn().mockRejectedValue(
      new Error('Retry failed')
    );

    render(<WorkflowMonitor />);

    await waitFor(() => {
      const retryButton = screen.getByTitle('Retry Execution');
      fireEvent.click(retryButton);
    });

    // Should handle error without crashing
    expect(mockWorkflowService.prototype.executeWorkflow).toHaveBeenCalled();
  });

  it('handles cancel errors gracefully', async () => {
    mockWorkflowService.prototype.cancelExecution = jest.fn().mockRejectedValue(
      new Error('Cancel failed')
    );

    render(<WorkflowMonitor />);

    await waitFor(() => {
      const cancelButton = screen.getByTitle('Cancel Execution');
      fireEvent.click(cancelButton);
    });

    // Should handle error without crashing
    expect(mockWorkflowService.prototype.cancelExecution).toHaveBeenCalled();
  });

  it('auto-refreshes execution data', async () => {
    jest.useFakeTimers();
    
    render(<WorkflowMonitor autoRefresh={true} refreshInterval={5000} />);

    await waitFor(() => {
      expect(mockWorkflowService.prototype.getWorkflowExecutions).toHaveBeenCalledTimes(1);
    });

    // Fast-forward time
    jest.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(mockWorkflowService.prototype.getWorkflowExecutions).toHaveBeenCalledTimes(2);
    });

    jest.useRealTimers();
  });

  it('displays execution results with error details', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const viewButtons = screen.getAllByTitle('View Details');
      fireEvent.click(viewButtons[1]); // Click on failed execution
    });

    await waitFor(() => {
      expect(screen.getByText('Execution Results')).toBeInTheDocument();
      expect(screen.getByText('Tag Document')).toBeInTheDocument();
      expect(screen.getByText('failed')).toBeInTheDocument();
      expect(screen.getByText('Error: API timeout after 30 seconds')).toBeInTheDocument();
    });
  });

  it('shows execution logs in modal', async () => {
    render(<WorkflowMonitor />);

    await waitFor(() => {
      const viewButton = screen.getAllByTitle('View Details')[0];
      fireEvent.click(viewButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Execution Logs')).toBeInTheDocument();
      expect(screen.getByText('Workflow execution started')).toBeInTheDocument();
      expect(screen.getByText('Workflow execution completed successfully')).toBeInTheDocument();
    });
  });

  it('handles loading state', () => {
    mockWorkflowService.prototype.getWorkflowExecutions = jest.fn().mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<WorkflowMonitor />);

    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('handles error state', async () => {
    mockWorkflowService.prototype.getWorkflowExecutions = jest.fn().mockRejectedValue(
      new Error('Failed to load executions')
    );

    render(<WorkflowMonitor />);

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Failed to load workflow executions')).toBeInTheDocument();
    });
  });
});