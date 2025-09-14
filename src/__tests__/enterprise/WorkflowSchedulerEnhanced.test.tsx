/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkflowScheduler } from '../../components/enterprise/workflow/WorkflowScheduler';
import { WorkflowManagementService } from '../../services/workflowManagementService';

// Mock the workflow service
jest.mock('../../services/workflowManagementService');
const mockWorkflowService = WorkflowManagementService as jest.MockedClass<typeof WorkflowManagementService>;

describe('WorkflowScheduler - Enhanced Execution and Monitoring', () => {
  const mockScheduledWorkflows = [
    {
      id: 'wf_1',
      name: 'Auto-tag Documents',
      description: 'Automatically tag documents based on content analysis',
      status: 'active',
      nextExecution: new Date('2024-01-26T10:30:00Z'),
      lastExecution: new Date('2024-01-25T10:30:00Z'),
      executionCount: 45,
      averageExecutionTime: 2300
    },
    {
      id: 'wf_2',
      name: 'Failed Workflow',
      description: 'A workflow in error state',
      status: 'error',
      nextExecution: null,
      lastExecution: new Date('2024-01-25T09:00:00Z'),
      executionCount: 12,
      averageExecutionTime: 5600
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockWorkflowService.prototype.getScheduledWorkflows = jest.fn().mockResolvedValue(mockScheduledWorkflows);
    mockWorkflowService.prototype.updateWorkflowStatus = jest.fn().mockResolvedValue(undefined);
    mockWorkflowService.prototype.executeWorkflow = jest.fn().mockResolvedValue({
      id: 'exec_123',
      workflowId: 'wf_1',
      status: 'running'
    });
    mockWorkflowService.prototype.updateWorkflowSchedule = jest.fn().mockResolvedValue(undefined);
  });

  it('renders scheduled workflows with execution controls', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      expect(screen.getByText('Auto-tag Documents')).toBeInTheDocument();
      expect(screen.getByText('Failed Workflow')).toBeInTheDocument();
      expect(screen.getByText('Executions: 45')).toBeInTheDocument();
      expect(screen.getByText('Avg Time: 2300ms')).toBeInTheDocument();
    });
  });

  it('shows manual execution button for active workflows', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const executeButtons = screen.getAllByTitle('Execute Now');
      expect(executeButtons).toHaveLength(1); // Only for active workflow
    });
  });

  it('handles manual workflow execution', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const executeButton = screen.getByTitle('Execute Now');
      fireEvent.click(executeButton);
    });

    expect(mockWorkflowService.prototype.executeWorkflow).toHaveBeenCalledWith('wf_1');
  });

  it('shows recovery button for workflows in error state', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      expect(screen.getByTitle('Recover from Error')).toBeInTheDocument();
    });
  });

  it('handles workflow error recovery', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const recoveryButton = screen.getByTitle('Recover from Error');
      fireEvent.click(recoveryButton);
    });

    expect(mockWorkflowService.prototype.updateWorkflowStatus).toHaveBeenCalledWith('wf_2', 'active');
  });

  it('disables toggle button for workflows in error state', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const toggleButtons = screen.getAllByRole('button');
      const errorWorkflowToggle = toggleButtons.find(button => 
        button.getAttribute('title') === 'Cannot toggle - in error state'
      );
      expect(errorWorkflowToggle).toBeDisabled();
    });
  });

  it('shows different status indicators for workflow states', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      expect(screen.getByText('active')).toBeInTheDocument();
      expect(screen.getByText('error')).toBeInTheDocument();
    });
  });

  it('handles workflow scheduling with different schedule types', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const scheduleButton = screen.getAllByTitle('Edit Schedule')[0];
      fireEvent.click(scheduleButton);
    });

    // Should open schedule modal
    await waitFor(() => {
      expect(screen.getByText('Schedule Workflow: Auto-tag Documents')).toBeInTheDocument();
    });

    // Test recurring schedule
    const scheduleTypeSelect = screen.getByDisplayValue('recurring');
    fireEvent.change(scheduleTypeSelect, { target: { value: 'once' } });

    expect(scheduleTypeSelect.value).toBe('once');
  });

  it('validates cron expression for recurring schedules', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const scheduleButton = screen.getAllByTitle('Edit Schedule')[0];
      fireEvent.click(scheduleButton);
    });

    await waitFor(() => {
      const cronInput = screen.getByPlaceholderText('0 0 * * *');
      fireEvent.change(cronInput, { target: { value: '0 9 * * 1' } });
      
      expect(cronInput.value).toBe('0 9 * * 1');
    });
  });

  it('saves schedule configuration', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const scheduleButton = screen.getAllByTitle('Edit Schedule')[0];
      fireEvent.click(scheduleButton);
    });

    await waitFor(() => {
      const saveButton = screen.getByText('Save Schedule');
      fireEvent.click(saveButton);
    });

    expect(mockWorkflowService.prototype.updateWorkflowSchedule).toHaveBeenCalled();
  });

  it('filters workflows by status', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const statusFilter = screen.getByDisplayValue('All Status');
      fireEvent.change(statusFilter, { target: { value: 'active' } });
    });

    // Should filter to show only active workflows
    await waitFor(() => {
      expect(screen.getByText('Auto-tag Documents')).toBeInTheDocument();
      expect(screen.queryByText('Failed Workflow')).not.toBeInTheDocument();
    });
  });

  it('searches workflows by name and description', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search workflows...');
      fireEvent.change(searchInput, { target: { value: 'auto-tag' } });
    });

    // Should filter to show only matching workflows
    await waitFor(() => {
      expect(screen.getByText('Auto-tag Documents')).toBeInTheDocument();
      expect(screen.queryByText('Failed Workflow')).not.toBeInTheDocument();
    });
  });

  it('handles execution errors gracefully', async () => {
    mockWorkflowService.prototype.executeWorkflow = jest.fn().mockRejectedValue(
      new Error('Execution failed')
    );

    render(<WorkflowScheduler />);

    await waitFor(() => {
      const executeButton = screen.getByTitle('Execute Now');
      fireEvent.click(executeButton);
    });

    // Should handle error without crashing
    expect(mockWorkflowService.prototype.executeWorkflow).toHaveBeenCalled();
  });

  it('handles recovery errors gracefully', async () => {
    mockWorkflowService.prototype.updateWorkflowStatus = jest.fn().mockRejectedValue(
      new Error('Recovery failed')
    );

    render(<WorkflowScheduler />);

    await waitFor(() => {
      const recoveryButton = screen.getByTitle('Recover from Error');
      fireEvent.click(recoveryButton);
    });

    // Should handle error without crashing
    expect(mockWorkflowService.prototype.updateWorkflowStatus).toHaveBeenCalled();
  });

  it('refreshes workflow list after actions', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
    });

    expect(mockWorkflowService.prototype.getScheduledWorkflows).toHaveBeenCalledTimes(2);
  });

  it('shows execution statistics for each workflow', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      expect(screen.getByText('Executions: 45')).toBeInTheDocument();
      expect(screen.getByText('Avg Time: 2300ms')).toBeInTheDocument();
      expect(screen.getByText('Executions: 12')).toBeInTheDocument();
      expect(screen.getByText('Avg Time: 5600ms')).toBeInTheDocument();
    });
  });

  it('displays next and last execution times', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      expect(screen.getByText(/Next:/)).toBeInTheDocument();
      expect(screen.getByText(/Last:/)).toBeInTheDocument();
    });
  });

  it('handles timezone selection in schedule modal', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const scheduleButton = screen.getAllByTitle('Edit Schedule')[0];
      fireEvent.click(scheduleButton);
    });

    await waitFor(() => {
      const timezoneSelect = screen.getByDisplayValue('UTC');
      fireEvent.change(timezoneSelect, { target: { value: 'America/New_York' } });
      
      expect(timezoneSelect.value).toBe('America/New_York');
    });
  });

  it('toggles schedule enabled state', async () => {
    render(<WorkflowScheduler />);

    await waitFor(() => {
      const scheduleButton = screen.getAllByTitle('Edit Schedule')[0];
      fireEvent.click(scheduleButton);
    });

    await waitFor(() => {
      const enabledCheckbox = screen.getByLabelText('Enable schedule');
      fireEvent.click(enabledCheckbox);
      
      expect(enabledCheckbox).not.toBeChecked();
    });
  });
});