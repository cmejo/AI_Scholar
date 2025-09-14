/**
 * Integration Hub Tests
 * Comprehensive tests for integration management functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { IntegrationHub } from '../../components/enterprise/IntegrationHub';
import { integrationManagementService } from '../../services/integrationManagementService';

// Mock the integration management service
vi.mock('../../services/integrationManagementService', () => ({
  integrationManagementService: {
    getIntegrations: vi.fn(),
    getIntegrationCatalog: vi.fn(),
    getIntegrationStats: vi.fn(),
    testConnection: vi.fn(),
    deleteIntegration: vi.fn(),
    createIntegration: vi.fn(),
  }
}));

const mockIntegrations = [
  {
    id: 'slack_1',
    name: 'Slack Notifications',
    description: 'Send notifications to Slack channels',
    category: 'Communication',
    status: 'connected' as const,
    type: 'webhook' as const,
    lastSync: new Date('2024-01-25T10:30:00'),
    nextSync: new Date('2024-01-25T11:30:00'),
    syncStatus: 'success' as const,
    config: { 
      endpoint: 'https://hooks.slack.com/services/...',
      settings: { channel: '#alerts' }
    },
    credentials: { type: 'api_key' as const, masked: true },
    metrics: {
      totalRequests: 1250,
      successRate: 98.5,
      averageResponseTime: 150,
      lastRequest: new Date('2024-01-25T10:25:00')
    }
  },
  {
    id: 'aws_s3_1',
    name: 'AWS S3 Storage',
    description: 'Document storage and backup',
    category: 'Storage',
    status: 'error' as const,
    type: 'cloud' as const,
    lastSync: new Date('2024-01-25T09:00:00'),
    syncStatus: 'failed' as const,
    errorMessage: 'Authentication failed',
    config: { 
      settings: { bucket: 'my-documents', region: 'us-east-1' }
    },
    credentials: { type: 'api_key' as const, masked: true },
    metrics: {
      totalRequests: 5600,
      successRate: 95.2,
      averageResponseTime: 250,
      lastRequest: new Date('2024-01-25T08:55:00')
    }
  }
];

const mockStats = {
  totalIntegrations: 2,
  connectedIntegrations: 1,
  failedIntegrations: 1,
  pendingIntegrations: 0,
  totalSyncs: 1250,
  successfulSyncs: 1205,
  failedSyncs: 45
};

const mockCatalog = [
  {
    id: 'slack',
    name: 'Slack',
    description: 'Team communication and notifications',
    category: 'Communication',
    provider: 'Slack Technologies',
    icon: 'slack',
    type: 'webhook' as const,
    features: ['Real-time notifications', 'Channel integration', 'Bot commands'],
    pricing: 'free' as const,
    documentation: 'https://api.slack.com/docs',
    setupComplexity: 'easy' as const,
    popularity: 95,
    rating: 4.8,
    reviews: 1250,
    tags: ['communication', 'notifications', 'team']
  }
];

describe('IntegrationHub', () => {
  beforeEach(() => {
    vi.mocked(integrationManagementService.getIntegrations).mockResolvedValue(mockIntegrations);
    vi.mocked(integrationManagementService.getIntegrationCatalog).mockResolvedValue(mockCatalog);
    vi.mocked(integrationManagementService.getIntegrationStats).mockResolvedValue(mockStats);
    vi.mocked(integrationManagementService.testConnection).mockResolvedValue({
      status: 'healthy',
      timestamp: new Date(),
      responseTime: 150,
      details: {
        connectivity: true,
        authentication: true,
        permissions: true,
        dataAccess: true
      }
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders integration hub with overview tab by default', async () => {
    render(<IntegrationHub />);
    
    // Wait for data to load first
    await waitFor(() => {
      expect(screen.getByText('Integration Hub')).toBeInTheDocument();
      expect(screen.getByText('Configure and manage third-party integrations and API connections')).toBeInTheDocument();
    });
    
    // Wait for integration data to load
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
      expect(screen.getByText('AWS S3 Storage')).toBeInTheDocument();
    });
  });

  it('displays integration statistics correctly', async () => {
    render(<IntegrationHub />);
    
    await waitFor(() => {
      // Check for specific stats in the stats cards
      expect(screen.getByText('Total Integrations')).toBeInTheDocument();
      expect(screen.getByText('Issues')).toBeInTheDocument();
      
      // Check that the stats values are displayed
      const allConnectedTexts = screen.getAllByText('Connected');
      const allPendingTexts = screen.getAllByText('Pending');
      expect(allConnectedTexts.length).toBeGreaterThan(0);
      expect(allPendingTexts.length).toBeGreaterThan(0);
    });
  });

  it('shows integration status badges correctly', async () => {
    render(<IntegrationHub />);
    
    await waitFor(() => {
      // Look for status badges in the integration cards
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
      expect(screen.getByText('AWS S3 Storage')).toBeInTheDocument();
      
      // Check that status badges exist (there might be multiple "Connected" texts)
      const connectedElements = screen.getAllByText('Connected');
      const errorElements = screen.getAllByText('Error');
      expect(connectedElements.length).toBeGreaterThan(0);
      expect(errorElements.length).toBeGreaterThan(0);
    });
  });

  it('filters integrations by search term', async () => {
    render(<IntegrationHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
      expect(screen.getByText('AWS S3 Storage')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search integrations...');
    fireEvent.change(searchInput, { target: { value: 'Slack' } });

    expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    expect(screen.queryByText('AWS S3 Storage')).not.toBeInTheDocument();
  });

  it('filters integrations by category', async () => {
    render(<IntegrationHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
      expect(screen.getByText('AWS S3 Storage')).toBeInTheDocument();
    });

    const categorySelect = screen.getByDisplayValue('All Categories');
    fireEvent.change(categorySelect, { target: { value: 'Communication' } });

    expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    expect(screen.queryByText('AWS S3 Storage')).not.toBeInTheDocument();
  });

  it('filters integrations by status', async () => {
    render(<IntegrationHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
      expect(screen.getByText('AWS S3 Storage')).toBeInTheDocument();
    });

    const statusSelect = screen.getByDisplayValue('All Status');
    fireEvent.change(statusSelect, { target: { value: 'connected' } });

    expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    expect(screen.queryByText('AWS S3 Storage')).not.toBeInTheDocument();
  });

  it('tests integration connection', async () => {
    render(<IntegrationHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    const testButtons = screen.getAllByTitle('Test Connection');
    fireEvent.click(testButtons[0]);

    await waitFor(() => {
      expect(integrationManagementService.testConnection).toHaveBeenCalled();
    });
  });

  it('deletes integration with confirmation', async () => {
    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => true);

    render(<IntegrationHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByTitle('Delete');
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(integrationManagementService.deleteIntegration).toHaveBeenCalledWith('slack_1');
    });

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('switches between tabs correctly', async () => {
    render(<IntegrationHub />);
    
    // Initially on overview tab
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    // Switch to catalog tab
    const catalogTab = screen.getByText('Catalog');
    fireEvent.click(catalogTab);

    expect(screen.getByText('Integration Catalog')).toBeInTheDocument();

    // Switch to connections tab
    const connectionsTab = screen.getByText('Connections');
    fireEvent.click(connectionsTab);

    // The ConnectionManager component should be rendered
    await waitFor(() => {
      expect(screen.getByText('Connection Manager')).toBeInTheDocument();
    });

    // Switch to API keys tab
    const keysTab = screen.getByText('API Keys');
    fireEvent.click(keysTab);

    // The APIKeyManager component should be rendered
    await waitFor(() => {
      expect(screen.getByText('API Key Manager')).toBeInTheDocument();
    });
  });

  it('opens configuration modal', async () => {
    render(<IntegrationHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    const configButtons = screen.getAllByTitle('Configure');
    fireEvent.click(configButtons[0]);

    expect(screen.getByText('Configure Slack Notifications')).toBeInTheDocument();
  });

  it('refreshes data when refresh button is clicked', async () => {
    render(<IntegrationHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    expect(integrationManagementService.getIntegrations).toHaveBeenCalledTimes(2);
    expect(integrationManagementService.getIntegrationStats).toHaveBeenCalledTimes(2);
  });

  it('handles loading state', () => {
    vi.mocked(integrationManagementService.getIntegrations).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 1000))
    );

    render(<IntegrationHub />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    vi.mocked(integrationManagementService.getIntegrations).mockRejectedValue(
      new Error('Failed to load integrations')
    );

    render(<IntegrationHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Failed to load integration data')).toBeInTheDocument();
    });
  });

  it('shows empty state when no integrations match filters', async () => {
    render(<IntegrationHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search integrations...');
    fireEvent.change(searchInput, { target: { value: 'NonExistentIntegration' } });

    expect(screen.getByText('No Integrations Found')).toBeInTheDocument();
    expect(screen.getByText('No integrations match your current filters.')).toBeInTheDocument();
  });

  it('calls onIntegrationUpdate when integration is updated', async () => {
    const mockOnUpdate = vi.fn();
    render(<IntegrationHub onIntegrationUpdate={mockOnUpdate} />);
    
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    // Mock window.confirm for delete
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => true);

    const deleteButtons = screen.getAllByTitle('Delete');
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalled();
    });

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('switches to catalog tab and displays catalog items', async () => {
    render(<IntegrationHub />);
    
    // Wait for initial data to load
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    // Switch to catalog tab
    const catalogTab = screen.getByText('Catalog');
    fireEvent.click(catalogTab);

    // Wait for catalog content to appear
    await waitFor(() => {
      expect(screen.getByText('Integration Catalog')).toBeInTheDocument();
      expect(screen.getByText('Browse and add integrations from our comprehensive catalog of supported services.')).toBeInTheDocument();
    });
    
    await waitFor(() => {
      expect(screen.getByText('Slack')).toBeInTheDocument();
      expect(screen.getByText('Team communication and notifications')).toBeInTheDocument();
    });
  });

  it('opens catalog modal when Add Integration is clicked', async () => {
    render(<IntegrationHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    const addButton = screen.getByText('Add Integration');
    fireEvent.click(addButton);

    expect(screen.getByText('Integration Catalog')).toBeInTheDocument();
    expect(screen.getByText('Browse and install integrations from our catalog of supported services.')).toBeInTheDocument();
  });

  it('installs integration from catalog', async () => {
    const mockCreateIntegration = vi.mocked(integrationManagementService.createIntegration);
    mockCreateIntegration.mockResolvedValue({
      id: 'new_integration_1',
      name: 'Slack',
      description: 'Team communication and notifications',
      category: 'Communication',
      status: 'pending',
      type: 'webhook',
      syncStatus: 'never',
      config: { settings: {} },
      credentials: { type: 'api_key', masked: true },
      metrics: {
        totalRequests: 0,
        successRate: 0,
        averageResponseTime: 0
      }
    });

    // Use a different catalog item that won't conflict with existing integrations
    const mockCatalogWithNewItem = [
      {
        id: 'github',
        name: 'GitHub',
        description: 'Code repository integration',
        category: 'Development',
        provider: 'GitHub Inc.',
        icon: 'github',
        type: 'api' as const,
        features: ['Repository access', 'Issue tracking', 'Pull requests'],
        pricing: 'free' as const,
        documentation: 'https://docs.github.com/api',
        setupComplexity: 'medium' as const,
        popularity: 90,
        rating: 4.7,
        reviews: 850,
        tags: ['development', 'git', 'repository']
      }
    ];

    vi.mocked(integrationManagementService.getIntegrationCatalog).mockResolvedValue(mockCatalogWithNewItem);

    render(<IntegrationHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    // Switch to catalog tab
    const catalogTab = screen.getByText('Catalog');
    fireEvent.click(catalogTab);

    await waitFor(() => {
      expect(screen.getByText('GitHub')).toBeInTheDocument();
    });

    const installButton = screen.getByText('Install');
    fireEvent.click(installButton);

    await waitFor(() => {
      expect(mockCreateIntegration).toHaveBeenCalledWith({
        name: 'GitHub',
        description: 'Code repository integration',
        category: 'Development',
        status: 'pending',
        type: 'api',
        syncStatus: 'never',
        config: { settings: {} },
        credentials: { type: 'api_key', masked: true }
      });
    });
  });

  it('filters catalog items by search term', async () => {
    render(<IntegrationHub />);
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    // Switch to catalog tab
    const catalogTab = screen.getByText('Catalog');
    fireEvent.click(catalogTab);

    await waitFor(() => {
      expect(screen.getByText('Slack')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search catalog...');
    fireEvent.change(searchInput, { target: { value: 'NonExistent' } });

    expect(screen.queryByText('Slack')).not.toBeInTheDocument();
  });

  it('shows installed status for existing integrations in catalog', async () => {
    render(<IntegrationHub />);
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Slack Notifications')).toBeInTheDocument();
    });

    // Switch to catalog tab
    const catalogTab = screen.getByText('Catalog');
    fireEvent.click(catalogTab);

    await waitFor(() => {
      expect(screen.getByText('Slack')).toBeInTheDocument();
    });

    // Since we have a Slack integration in mockIntegrations, it should show as installed
    const installButton = screen.getByText('Installed');
    expect(installButton).toBeDisabled();
  });
});