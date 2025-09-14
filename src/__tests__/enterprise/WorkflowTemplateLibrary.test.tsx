import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { WorkflowTemplateLibrary } from '../../components/enterprise/workflow/WorkflowTemplateLibrary';
import type { WorkflowTemplate } from '../../types/workflow';

// Mock the workflow service
vi.mock('../../services/workflowManagementService', () => ({
  WorkflowManagementService: vi.fn().mockImplementation(() => ({
    getWorkflowTemplates: vi.fn().mockResolvedValue([
      {
        id: 'template-1',
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
          createdBy: 'system',
          triggers: [{
            id: 'trigger-1',
            type: 'document_upload',
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
          tags: ['template'],
          version: 1,
          isTemplate: true
        }
      },
      {
        id: 'template-2',
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
          createdBy: 'system',
          triggers: [{
            id: 'trigger-2',
            type: 'schedule',
            config: { cron: '0 9 * * 1' },
            enabled: true
          }],
          conditions: [],
          actions: [{
            id: 'action-2',
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
      },
      {
        id: 'template-3',
        name: 'Community Template',
        description: 'A community-contributed template',
        category: 'Integration',
        tags: ['community', 'integration'],
        popularity: 45,
        isOfficial: false,
        definition: {
          name: 'Community Template',
          description: 'A community-contributed template',
          status: 'active',
          createdBy: 'community',
          triggers: [],
          conditions: [],
          actions: [],
          tags: ['template'],
          version: 1,
          isTemplate: true
        }
      }
    ])
  }))
}));

describe('WorkflowTemplateLibrary', () => {
  const mockOnSelectTemplate = vi.fn();
  const mockOnPreviewTemplate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders template library interface', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Workflow Templates')).toBeInTheDocument();
      expect(screen.getByText('Choose from pre-built workflow templates to get started quickly')).toBeInTheDocument();
    });
  });

  it('displays templates after loading', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
      expect(screen.getByText('Scheduled Reporting')).toBeInTheDocument();
      expect(screen.getByText('Community Template')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    expect(screen.getByText('Loading templates...')).toBeInTheDocument();
  });

  it('handles search functionality', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search templates...');
    fireEvent.change(searchInput, { target: { value: 'document' } });

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
      expect(screen.queryByText('Scheduled Reporting')).not.toBeInTheDocument();
    });
  });

  it('handles view mode toggle', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    const listViewButton = screen.getByTitle('List View');
    fireEvent.click(listViewButton);

    const gridViewButton = screen.getByTitle('Grid View');
    fireEvent.click(gridViewButton);
  });

  it('handles filter toggle', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    const filtersButton = screen.getByText('Filters');
    fireEvent.click(filtersButton);

    expect(screen.getByText('Category')).toBeInTheDocument();
    expect(screen.getByText('Popularity')).toBeInTheDocument();
    expect(screen.getByText('Source')).toBeInTheDocument();
  });

  it('handles category filtering', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    // Open filters
    const filtersButton = screen.getByText('Filters');
    fireEvent.click(filtersButton);

    // Select category filter
    const categorySelect = screen.getByDisplayValue('All Categories');
    fireEvent.change(categorySelect, { target: { value: 'Document Management' } });

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
      expect(screen.queryByText('Scheduled Reporting')).not.toBeInTheDocument();
    });
  });

  it('handles popularity filtering', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    // Open filters
    const filtersButton = screen.getByText('Filters');
    fireEvent.click(filtersButton);

    // Select popularity filter
    const popularitySelect = screen.getByDisplayValue('All');
    fireEvent.change(popularitySelect, { target: { value: 'high' } });

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
      expect(screen.getByText('Scheduled Reporting')).toBeInTheDocument();
      expect(screen.queryByText('Community Template')).not.toBeInTheDocument();
    });
  });

  it('handles official/community filtering', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    // Open filters
    const filtersButton = screen.getByText('Filters');
    fireEvent.click(filtersButton);

    // Select official filter
    const sourceSelect = screen.getByDisplayValue('All Sources');
    fireEvent.change(sourceSelect, { target: { value: 'false' } });

    await waitFor(() => {
      expect(screen.queryByText('Document Processing Pipeline')).not.toBeInTheDocument();
      expect(screen.queryByText('Scheduled Reporting')).not.toBeInTheDocument();
      expect(screen.getByText('Community Template')).toBeInTheDocument();
    });
  });

  it('handles tag filtering', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    // Open filters
    const filtersButton = screen.getByText('Filters');
    fireEvent.click(filtersButton);

    // Click on a tag
    const documentTag = screen.getByText('document');
    fireEvent.click(documentTag);

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
      expect(screen.queryByText('Scheduled Reporting')).not.toBeInTheDocument();
    });
  });

  it('handles clear filters', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    // Open filters and apply some
    const filtersButton = screen.getByText('Filters');
    fireEvent.click(filtersButton);

    const categorySelect = screen.getByDisplayValue('All Categories');
    fireEvent.change(categorySelect, { target: { value: 'Document Management' } });

    // Clear filters
    const clearButton = screen.getByText('Clear Filters');
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
      expect(screen.getByText('Scheduled Reporting')).toBeInTheDocument();
      expect(screen.getByText('Community Template')).toBeInTheDocument();
    });
  });

  it('handles sorting', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    const sortSelect = screen.getByDisplayValue('Most Popular');
    fireEvent.change(sortSelect, { target: { value: 'name-asc' } });
  });

  it('handles template selection', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    const templateCard = screen.getByText('Document Processing Pipeline').closest('div');
    fireEvent.click(templateCard!);

    expect(mockOnSelectTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Document Processing Pipeline'
      })
    );
  });

  it('handles template preview', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    const previewButtons = screen.getAllByTitle('Preview');
    fireEvent.click(previewButtons[0]);

    expect(mockOnPreviewTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Document Processing Pipeline'
      })
    );
  });

  it('handles bookmark toggle', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    const bookmarkButtons = screen.getAllByRole('button');
    const bookmarkButton = bookmarkButtons.find(button => 
      button.querySelector('svg')?.getAttribute('class')?.includes('w-4 h-4 text-gray-400')
    );
    
    if (bookmarkButton) {
      fireEvent.click(bookmarkButton);
    }
  });

  it('shows no templates message when filtered results are empty', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Processing Pipeline')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search templates...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

    await waitFor(() => {
      expect(screen.getByText('No templates found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search or filters')).toBeInTheDocument();
    });
  });

  it('displays template popularity badges correctly', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Popular')).toBeInTheDocument(); // 85% popularity
      expect(screen.getByText('Trending')).toBeInTheDocument(); // 72% popularity
      expect(screen.getByText('New')).toBeInTheDocument(); // 45% popularity
    });
  });

  it('displays official badges correctly', async () => {
    render(
      <WorkflowTemplateLibrary
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      const officialBadges = screen.getAllByText('Official');
      expect(officialBadges).toHaveLength(2); // Two official templates
    });
  });

  it('handles selected template highlighting', async () => {
    render(
      <WorkflowTemplateLibrary
        selectedTemplateId="template-1"
        onSelectTemplate={mockOnSelectTemplate}
        onPreviewTemplate={mockOnPreviewTemplate}
      />
    );

    await waitFor(() => {
      const selectedTemplate = screen.getByText('Document Processing Pipeline').closest('div');
      expect(selectedTemplate).toHaveClass('border-blue-500');
    });
  });
});