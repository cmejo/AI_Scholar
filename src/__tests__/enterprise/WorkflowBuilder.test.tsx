import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { WorkflowBuilder } from '../../components/enterprise/workflow/WorkflowBuilder';
import type { WorkflowTemplate } from '../../types/workflow';

// Mock the workflow service
vi.mock('../../services/workflowManagementService', () => ({
  WorkflowManagementService: vi.fn().mockImplementation(() => ({
    getWorkflow: vi.fn().mockResolvedValue({
      id: 'test-workflow',
      name: 'Test Workflow',
      description: 'Test Description',
      status: 'draft',
      triggers: [],
      conditions: [],
      actions: [],
      tags: [],
      version: 1,
      isTemplate: false,
      createdBy: 'test-user',
      createdAt: new Date(),
      updatedAt: new Date()
    }),
    createWorkflow: vi.fn().mockResolvedValue({
      id: 'new-workflow',
      name: 'New Workflow',
      description: 'New Description',
      status: 'draft',
      triggers: [],
      conditions: [],
      actions: [],
      tags: [],
      version: 1,
      isTemplate: false,
      createdBy: 'test-user',
      createdAt: new Date(),
      updatedAt: new Date()
    }),
    updateWorkflow: vi.fn().mockResolvedValue({
      id: 'test-workflow',
      name: 'Updated Workflow',
      description: 'Updated Description',
      status: 'draft',
      triggers: [],
      conditions: [],
      actions: [],
      tags: [],
      version: 2,
      isTemplate: false,
      createdBy: 'test-user',
      createdAt: new Date(),
      updatedAt: new Date()
    }),
    executeWorkflow: vi.fn().mockResolvedValue({
      id: 'exec-1',
      workflowId: 'test-workflow',
      status: 'running',
      startTime: new Date(),
      triggeredBy: 'test-user',
      triggerType: 'manual',
      logs: [],
      results: [],
      context: {}
    })
  }))
}));

const mockTemplate: WorkflowTemplate = {
  id: 'template-1',
  name: 'Test Template',
  description: 'Test template description',
  category: 'Document Management',
  tags: ['test', 'template'],
  popularity: 85,
  isOfficial: true,
  definition: {
    name: 'Test Template',
    description: 'Test template description',
    status: 'active',
    createdBy: 'system',
    triggers: [{
      id: 'trigger-1',
      type: 'manual',
      config: {},
      enabled: true
    }],
    conditions: [],
    actions: [{
      id: 'action-1',
      type: 'auto_tag',
      name: 'Auto Tag',
      config: {},
      enabled: true,
      order: 1
    }],
    tags: ['test'],
    version: 1,
    isTemplate: true
  }
};

describe('WorkflowBuilder', () => {
  const mockOnSave = vi.fn();
  const mockOnCancel = vi.fn();
  const mockOnTest = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders workflow builder interface', () => {
    render(
      <WorkflowBuilder
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    expect(screen.getByText('New Workflow')).toBeInTheDocument();
    expect(screen.getByText('Draft')).toBeInTheDocument();
    expect(screen.getByTitle('Save Workflow')).toBeInTheDocument();
    expect(screen.getByTitle('Test Workflow')).toBeInTheDocument();
  });

  it('renders with template data', () => {
    render(
      <WorkflowBuilder
        template={mockTemplate}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    expect(screen.getByDisplayValue('Test Template')).toBeInTheDocument();
  });

  it('handles workflow name changes', () => {
    render(
      <WorkflowBuilder
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    const nameInput = screen.getByDisplayValue('New Workflow');
    fireEvent.change(nameInput, { target: { value: 'Updated Workflow Name' } });

    expect(screen.getByDisplayValue('Updated Workflow Name')).toBeInTheDocument();
  });

  it('handles zoom controls', () => {
    render(
      <WorkflowBuilder
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    const zoomInButton = screen.getByTitle('Zoom In');
    const zoomOutButton = screen.getByTitle('Zoom Out');

    expect(zoomInButton).toBeInTheDocument();
    expect(zoomOutButton).toBeInTheDocument();

    fireEvent.click(zoomInButton);
    fireEvent.click(zoomOutButton);
  });

  it('handles tool selection', () => {
    render(
      <WorkflowBuilder
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    const selectTool = screen.getByTitle('Select Tool');
    const panTool = screen.getByTitle('Pan Tool');

    expect(selectTool).toBeInTheDocument();
    expect(panTool).toBeInTheDocument();

    fireEvent.click(panTool);
    fireEvent.click(selectTool);
  });

  it('handles grid toggle', () => {
    render(
      <WorkflowBuilder
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    const gridToggle = screen.getByTitle('Toggle Grid');
    fireEvent.click(gridToggle);
  });

  it('handles undo/redo', () => {
    render(
      <WorkflowBuilder
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    const undoButton = screen.getByTitle('Undo');
    const redoButton = screen.getByTitle('Redo');

    expect(undoButton).toBeDisabled();
    expect(redoButton).toBeDisabled();
  });

  it('handles save workflow', async () => {
    render(
      <WorkflowBuilder
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    const saveButton = screen.getByTitle('Save Workflow');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalled();
    });
  });

  it('handles test workflow', async () => {
    render(
      <WorkflowBuilder
        workflowId="test-workflow"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    const testButton = screen.getByTitle('Test Workflow');
    fireEvent.click(testButton);

    await waitFor(() => {
      expect(mockOnTest).toHaveBeenCalled();
    });
  });

  it('handles cancel', () => {
    render(
      <WorkflowBuilder
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('renders in read-only mode', () => {
    render(
      <WorkflowBuilder
        readOnly={true}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    expect(screen.queryByTitle('Save Workflow')).not.toBeInTheDocument();
    expect(screen.queryByTitle('Test Workflow')).not.toBeInTheDocument();
  });

  it('handles drag and drop from palette', () => {
    render(
      <WorkflowBuilder
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    // Check that component palette is rendered
    expect(screen.getByText('Components')).toBeInTheDocument();
    expect(screen.getByText('Triggers')).toBeInTheDocument();
    expect(screen.getByText('Conditions')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();
  });

  it('loads existing workflow', async () => {
    render(
      <WorkflowBuilder
        workflowId="test-workflow"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Workflow')).toBeInTheDocument();
    });
  });

  it('shows loading state', () => {
    render(
      <WorkflowBuilder
        workflowId="test-workflow"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    expect(screen.getByText('Loading workflow...')).toBeInTheDocument();
  });

  it('handles canvas interactions', () => {
    render(
      <WorkflowBuilder
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        onTest={mockOnTest}
      />
    );

    // Test canvas drag and drop
    const canvas = document.querySelector('.cursor-crosshair');
    
    // Simulate drag over
    fireEvent.dragOver(canvas, {
      preventDefault: vi.fn()
    });

    // Simulate drop with node data
    const dropData = JSON.stringify({
      nodeType: 'trigger',
      subType: 'manual',
      label: 'Manual Trigger'
    });

    fireEvent.drop(canvas, {
      preventDefault: vi.fn(),
      dataTransfer: {
        getData: vi.fn().mockReturnValue(dropData)
      }
    });
  });
});