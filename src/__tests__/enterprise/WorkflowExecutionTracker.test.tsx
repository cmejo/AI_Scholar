import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { WorkflowExecutionTracker } from '../../components/enterprise/workflow/WorkflowExecutionTracker';
import { WorkflowManagementService } from '../../services/workflowManagementService';
import type { WorkflowExecution } from '../../types/workflow';

// Mock the workflow service
vi.mock('../../services/workflowManagementService');
const mockWorkflowService = WorkflowManagementService as any;

describe('WorkflowExecutionTracker', () => {
  const mockExecution: WorkflowExecution = {
    id: 'exec_123',
    workflowId: 'wf_456',
    status: 'running',
    startTime: new Date('2024-01-25T10:00:00Z'),
    triggeredBy: 'user1',
    triggerType: 'manual',
    logs: [
      {
        id: 'log_1',
        timestamp: new Date('2024-01-25T10:00:00Z'),
        level: 'info',
        message: 'Execution started'
      },
      {
        id: 'log_2',
        timestamp: new Date('2024-01-25T10:01:00Z'),
        level: 'info',
        message: 'Processing step 1'
      }
    ],
    results: [
      {
        actionId: 'action_1',
        actionName: 'Process Data',
        status: 'success',
        duration: 30000
      }
    ],
    context: { documentId: 'doc_123' }
  };

  const mockExecutionStatus = {
    status: 'running',
    progress: 65,
    currentStep: 'Processing documents'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockWorkflowService.prototype.getExecution = vi.fn().mockResolvedValue(mockExecution);
    mockWorkflowService.prototype.getExecutionStatus = vi.fn().mockResolvedValue(mockExecutionStatus);
    mockWorkflowService.prototype.cancelExecution = vi.fn().mockResolvedValue(undefined);
  });

  it('renders execution tracker with basic information', async () => {
    render(<WorkflowExecutionTracker executionId="exec_123" />);

    await waitFor(() => {
      expect(screen.getByText('Execution Tracking')).toBeInTheDocument();
      expect(screen.getByText('ID: exec_123')).toBeInTheDocument();
      expect(screen.getByText('Running')).toBeInTheDocument();
    });
  });

  it('displays execution progress for running workflows', async () => {
    render(<WorkflowExecutionTracker executionId="exec_123" />);

    await waitFor(() => {
      expect(screen.getByText('Execution Progress')).toBeInTheDocument();
      expect(screen.getByText('65.0%')).toBeInTheDocument();
      expect(screen.getByText('Current: Processing documents')).toBeInTheDocument();
    });
  });

  it('shows execution details and metrics', async () => {
    render(<WorkflowExecutionTracker executionId="exec_123" />);

    await waitFor(() => {
      expect(screen.getByText('Started')).toBeInTheDocument();
      expect(screen.getByText('Duration')).toBeInTheDocument();
      expect(screen.getByText('Triggered By')).toBeInTheDocument();
      expect(screen.getByText('user1')).toBeInTheDocument();
    });
  });

  it('displays action results', async () => {
    render(<WorkflowExecutionTracker executionId="exec_123" />);

    await waitFor(() => {
      expect(screen.getByText('Action Results')).toBeInTheDocument();
      expect(screen.getByText('Process Data')).toBeInTheDocument();
      expect(screen.getByText('success')).toBeInTheDocument();
      expect(screen.getByText('Duration: 30.00s')).toBeInTheDocument();
    });
  });

  it('shows recent logs', async () => {
    render(<WorkflowExecutionTracker executionId="exec_123" />);

    await waitFor(() => {
      expect(screen.getByText('Recent Logs')).toBeInTheDocument();
      expect(screen.getByText('Execution started')).toBeInTheDocument();
      expect(screen.getByText('Processing step 1')).toBeInTheDocument();
    });
  });

  it('handles cancel execution', async () => {
    render(<WorkflowExecutionTracker executionId="exec_123" />);

    await waitFor(() => {
      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);
    });

    expect(mockWorkflowService.prototype.cancelExecution).toHaveBeenCalledWith('exec_123');
  });

  it('displays error information for failed executions', async () => {
    const failedExecution = {
      ...mockExecution,
      status: 'failed' as const,
      error: 'API timeout occurred'
    };

    mockWorkflowService.prototype.getExecution = vi.fn().mockResolvedValue(failedExecution);

    render(<WorkflowExecutionTracker executionId="exec_123" />);

    await waitFor(() => {
      expect(screen.getByText('Execution Failed')).toBeInTheDocument();
      expect(screen.getByText('API timeout occurred')).toBeInTheDocument();
    });
  });

  it('calls completion callback when execution completes', async () => {
    const completedExecution = {
      ...mockExecution,
      status: 'completed' as const,
      endTime: new Date('2024-01-25T10:05:00Z'),
      duration: 300000
    };

    mockWorkflowService.prototype.getExecution = vi.fn().mockResolvedValue(completedExecution);
    const onComplete = vi.fn();

    render(
      <WorkflowExecutionTracker 
        executionId="exec_123" 
        onExecutionComplete={onComplete}
      />
    );

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith(completedExecution);
    });
  });

  it('calls failure callback when execution fails', async () => {
    const failedExecution = {
      ...mockExecution,
      status: 'failed' as const,
      error: 'Processing failed'
    };

    mockWorkflowService.prototype.getExecution = vi.fn().mockResolvedValue(failedExecution);
    const onFailed = vi.fn();

    render(
      <WorkflowExecutionTracker 
        executionId="exec_123" 
        onExecutionFailed={onFailed}
      />
    );

    await waitFor(() => {
      expect(onFailed).toHaveBeenCalledWith(failedExecution, 'Processing failed');
    });
  });

  it('handles loading state', () => {
    mockWorkflowService.prototype.getExecution = vi.fn().mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<WorkflowExecutionTracker executionId="exec_123" />);

    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('handles error state', async () => {
    mockWorkflowService.prototype.getExecution = vi.fn().mockRejectedValue(
      new Error('Failed to load execution')
    );

    render(<WorkflowExecutionTracker executionId="exec_123" />);

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Failed to load execution details')).toBeInTheDocument();
    });
  });

  it('refreshes execution data when refresh button is clicked', async () => {
    render(<WorkflowExecutionTracker executionId="exec_123" />);

    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
    });

    expect(mockWorkflowService.prototype.getExecution).toHaveBeenCalledTimes(2);
    expect(mockWorkflowService.prototype.getExecutionStatus).toHaveBeenCalledTimes(2);
  });

  it('auto-refreshes for running executions', async () => {
    vi.useFakeTimers();
    
    render(
      <WorkflowExecutionTracker 
        executionId="exec_123" 
        autoRefresh={true}
        refreshInterval={1000}
      />
    );

    await waitFor(() => {
      expect(mockWorkflowService.prototype.getExecution).toHaveBeenCalledTimes(1);
    });

    // Fast-forward time
    vi.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(mockWorkflowService.prototype.getExecution).toHaveBeenCalledTimes(2);
    });

    vi.useRealTimers();
  });

  it('calculates estimated time remaining correctly', async () => {
    // Mock Date.now to return a specific time
    const mockNow = new Date('2024-01-25T10:02:00Z').getTime();
    vi.spyOn(Date, 'now').mockReturnValue(mockNow);

    render(<WorkflowExecutionTracker executionId="exec_123" />);

    await waitFor(() => {
      // Should show estimated time based on progress and elapsed time
      expect(screen.getByText(/Est\. \d+s remaining/)).toBeInTheDocument();
    });

    vi.restoreAllMocks();
  });

  it('does not show progress for completed executions', async () => {
    const completedExecution = {
      ...mockExecution,
      status: 'completed' as const,
      endTime: new Date('2024-01-25T10:05:00Z'),
      duration: 300000
    };

    mockWorkflowService.prototype.getExecution = vi.fn().mockResolvedValue(completedExecution);

    render(<WorkflowExecutionTracker executionId="exec_123" />);

    await waitFor(() => {
      expect(screen.queryByText('Execution Progress')).not.toBeInTheDocument();
      expect(screen.getByText('Completed')).toBeInTheDocument();
    });
  });
});