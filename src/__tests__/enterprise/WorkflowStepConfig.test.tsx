import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { WorkflowStepConfig } from '../../components/enterprise/workflow/WorkflowStepConfig';
import type { WorkflowTrigger, WorkflowCondition, WorkflowAction } from '../../types/workflow';

const mockTrigger: WorkflowTrigger = {
  id: 'trigger-1',
  type: 'manual',
  config: {},
  enabled: true
};

const mockCondition: WorkflowCondition = {
  id: 'condition-1',
  type: 'document_size',
  operator: 'greater_than',
  value: 1024
};

const mockAction: WorkflowAction = {
  id: 'action-1',
  type: 'auto_tag',
  name: 'Auto Tag Documents',
  config: { aiModel: 'gpt-4' },
  enabled: true,
  order: 1
};

describe('WorkflowStepConfig', () => {
  const mockOnSave = vi.fn();
  const mockOnCancel = vi.fn();
  const mockOnDelete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Trigger Configuration', () => {
    it('renders trigger configuration interface', () => {
      render(
        <WorkflowStepConfig
          step={mockTrigger}
          stepType="trigger"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Edit Trigger')).toBeInTheDocument();
      expect(screen.getByText('Trigger Configuration')).toBeInTheDocument();
      expect(screen.getByText('Trigger Type')).toBeInTheDocument();
    });

    it('handles trigger type changes', () => {
      render(
        <WorkflowStepConfig
          step={mockTrigger}
          stepType="trigger"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const typeSelect = screen.getByDisplayValue('Manual Trigger');
      fireEvent.change(typeSelect, { target: { value: 'schedule' } });

      expect(screen.getByText('Cron Expression')).toBeInTheDocument();
      expect(screen.getByText('Timezone')).toBeInTheDocument();
    });

    it('shows schedule-specific fields for scheduled triggers', () => {
      const scheduledTrigger: WorkflowTrigger = {
        ...mockTrigger,
        type: 'schedule',
        config: { cron: '0 9 * * *', timezone: 'UTC' }
      };

      render(
        <WorkflowStepConfig
          step={scheduledTrigger}
          stepType="trigger"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Cron Expression')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('0 9 * * * (daily at 9 AM)')).toBeInTheDocument();
      expect(screen.getByDisplayValue('UTC')).toBeInTheDocument();
    });

    it('shows document upload fields for document upload triggers', () => {
      const documentTrigger: WorkflowTrigger = {
        ...mockTrigger,
        type: 'document_upload',
        config: { fileTypes: ['pdf', 'docx'], maxSize: 10 }
      };

      render(
        <WorkflowStepConfig
          step={documentTrigger}
          stepType="trigger"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('File Types')).toBeInTheDocument();
      expect(screen.getByText('Maximum File Size (MB)')).toBeInTheDocument();
    });

    it('shows webhook fields for webhook triggers', () => {
      const webhookTrigger: WorkflowTrigger = {
        ...mockTrigger,
        type: 'webhook',
        config: { url: 'https://example.com/webhook', secret: 'secret123' }
      };

      render(
        <WorkflowStepConfig
          step={webhookTrigger}
          stepType="trigger"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Webhook URL')).toBeInTheDocument();
      expect(screen.getByText('Secret Token')).toBeInTheDocument();
    });

    it('handles enabled toggle for triggers', () => {
      render(
        <WorkflowStepConfig
          step={mockTrigger}
          stepType="trigger"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const enabledCheckbox = screen.getByLabelText('Enable this trigger');
      expect(enabledCheckbox).toBeChecked();

      fireEvent.click(enabledCheckbox);
      expect(enabledCheckbox).not.toBeChecked();
    });
  });

  describe('Condition Configuration', () => {
    it('renders condition configuration interface', () => {
      render(
        <WorkflowStepConfig
          step={mockCondition}
          stepType="condition"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Edit Condition')).toBeInTheDocument();
      expect(screen.getByText('Condition Configuration')).toBeInTheDocument();
      expect(screen.getByText('Condition Type')).toBeInTheDocument();
    });

    it('handles condition type changes', () => {
      render(
        <WorkflowStepConfig
          step={mockCondition}
          stepType="condition"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const typeSelect = screen.getByDisplayValue('Document Size');
      fireEvent.change(typeSelect, { target: { value: 'custom' } });

      expect(screen.getByText('Field Name')).toBeInTheDocument();
    });

    it('shows custom field for custom conditions', () => {
      const customCondition: WorkflowCondition = {
        ...mockCondition,
        type: 'custom',
        field: 'metadata.category'
      };

      render(
        <WorkflowStepConfig
          step={customCondition}
          stepType="condition"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Field Name')).toBeInTheDocument();
      expect(screen.getByDisplayValue('metadata.category')).toBeInTheDocument();
    });

    it('handles operator changes', () => {
      render(
        <WorkflowStepConfig
          step={mockCondition}
          stepType="condition"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const operatorSelect = screen.getByDisplayValue('Greater Than');
      fireEvent.change(operatorSelect, { target: { value: 'equals' } });
    });

    it('handles value changes', () => {
      render(
        <WorkflowStepConfig
          step={mockCondition}
          stepType="condition"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const valueInput = screen.getByDisplayValue('1024');
      fireEvent.change(valueInput, { target: { value: '2048' } });
    });

    it('shows time input for time_of_day conditions', () => {
      const timeCondition: WorkflowCondition = {
        ...mockCondition,
        type: 'time_of_day',
        value: '09:00'
      };

      render(
        <WorkflowStepConfig
          step={timeCondition}
          stepType="condition"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const timeInput = screen.getByDisplayValue('09:00');
      expect(timeInput).toHaveAttribute('type', 'time');
    });
  });

  describe('Action Configuration', () => {
    it('renders action configuration interface', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Edit Action')).toBeInTheDocument();
      expect(screen.getByText('Action Configuration')).toBeInTheDocument();
      expect(screen.getByText('Action Type')).toBeInTheDocument();
      expect(screen.getByText('Action Name')).toBeInTheDocument();
    });

    it('handles action type changes', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const typeSelect = screen.getByDisplayValue('Auto Tag');
      fireEvent.change(typeSelect, { target: { value: 'send_notification' } });

      expect(screen.getByText('Recipients')).toBeInTheDocument();
    });

    it('shows auto tag fields for auto tag actions', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('AI Model')).toBeInTheDocument();
      expect(screen.getByText('Tag Categories')).toBeInTheDocument();
    });

    it('shows notification fields for notification actions', () => {
      const notificationAction: WorkflowAction = {
        ...mockAction,
        type: 'send_notification',
        config: {
          recipients: ['user@example.com'],
          subject: 'Test Subject',
          message: 'Test Message'
        }
      };

      render(
        <WorkflowStepConfig
          step={notificationAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Recipients')).toBeInTheDocument();
      expect(screen.getByText('Subject Template')).toBeInTheDocument();
      expect(screen.getByText('Message Template')).toBeInTheDocument();
    });

    it('shows API call fields for API call actions', () => {
      const apiAction: WorkflowAction = {
        ...mockAction,
        type: 'api_call',
        config: {
          url: 'https://api.example.com/endpoint',
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        }
      };

      render(
        <WorkflowStepConfig
          step={apiAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('API URL')).toBeInTheDocument();
      expect(screen.getByText('HTTP Method')).toBeInTheDocument();
      expect(screen.getByText('Request Headers (JSON)')).toBeInTheDocument();
    });

    it('handles action name changes', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const nameInput = screen.getByDisplayValue('Auto Tag Documents');
      fireEvent.change(nameInput, { target: { value: 'Updated Action Name' } });
    });

    it('handles execution order changes', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const orderInput = screen.getByDisplayValue('1');
      fireEvent.change(orderInput, { target: { value: '2' } });
    });

    it('handles enabled toggle for actions', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const enabledCheckbox = screen.getByLabelText('Enable this action');
      expect(enabledCheckbox).toBeChecked();

      fireEvent.click(enabledCheckbox);
      expect(enabledCheckbox).not.toBeChecked();
    });
  });

  describe('Common Functionality', () => {
    it('handles save action', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      expect(mockOnSave).toHaveBeenCalledWith(mockAction);
    });

    it('handles cancel action', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });

    it('handles delete action when provided', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
          onDelete={mockOnDelete}
        />
      );

      const deleteButton = screen.getByText('Delete');
      fireEvent.click(deleteButton);

      expect(mockOnDelete).toHaveBeenCalled();
    });

    it('does not show delete button for new steps', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
          onDelete={mockOnDelete}
          isNew={true}
        />
      );

      expect(screen.queryByText('Delete')).not.toBeInTheDocument();
    });

    it('handles test functionality', async () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const testButton = screen.getByText('Test');
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(screen.getByText('Configuration test passed')).toBeInTheDocument();
      });
    });

    it('shows validation errors', () => {
      const invalidAction: WorkflowAction = {
        ...mockAction,
        name: '', // Invalid: empty name
        type: 'send_notification',
        config: {} // Invalid: missing recipients
      };

      render(
        <WorkflowStepConfig
          step={invalidAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      expect(screen.getByText('Please fix the following errors:')).toBeInTheDocument();
      expect(mockOnSave).not.toHaveBeenCalled();
    });

    it('shows create mode for new steps', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
          isNew={true}
        />
      );

      expect(screen.getByText('Create Action')).toBeInTheDocument();
    });

    it('handles close button', () => {
      render(
        <WorkflowStepConfig
          step={mockAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const closeButton = screen.getByRole('button', { name: '' }); // X button
      fireEvent.click(closeButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });
  });

  describe('Validation', () => {
    it('validates required trigger fields', () => {
      const invalidTrigger: WorkflowTrigger = {
        ...mockTrigger,
        type: 'schedule',
        config: {} // Missing cron
      };

      render(
        <WorkflowStepConfig
          step={invalidTrigger}
          stepType="trigger"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      expect(screen.getByText('Please fix the following errors:')).toBeInTheDocument();
    });

    it('validates required condition fields', () => {
      const invalidCondition: WorkflowCondition = {
        ...mockCondition,
        value: undefined // Missing value
      };

      render(
        <WorkflowStepConfig
          step={invalidCondition}
          stepType="condition"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      expect(screen.getByText('Please fix the following errors:')).toBeInTheDocument();
    });

    it('validates required action fields', () => {
      const invalidAction: WorkflowAction = {
        ...mockAction,
        name: '', // Missing name
        type: 'api_call',
        config: {} // Missing URL
      };

      render(
        <WorkflowStepConfig
          step={invalidAction}
          stepType="action"
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      expect(screen.getByText('Please fix the following errors:')).toBeInTheDocument();
    });
  });
});