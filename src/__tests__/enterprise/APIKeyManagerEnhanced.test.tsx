/**
 * Enhanced APIKeyManager Component Tests
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import { APIKeyManager } from '../../components/enterprise/integration/APIKeyManager';

// Mock the lucide-react icons
vi.mock('lucide-react', () => ({
  Key: () => <div data-testid="key-icon" />,
  Plus: () => <div data-testid="plus-icon" />,
  Edit: () => <div data-testid="edit-icon" />,
  Trash2: () => <div data-testid="trash-icon" />,
  Eye: () => <div data-testid="eye-icon" />,
  EyeOff: () => <div data-testid="eye-off-icon" />,
  Copy: () => <div data-testid="copy-icon" />,
  RefreshCw: () => <div data-testid="refresh-icon" />,
  Shield: () => <div data-testid="shield-icon" />,
  AlertTriangle: () => <div data-testid="alert-triangle-icon" />,
  CheckCircle: () => <div data-testid="check-circle-icon" />,
  Clock: () => <div data-testid="clock-icon" />,
  Search: () => <div data-testid="search-icon" />,
  Filter: () => <div data-testid="filter-icon" />,
  Download: () => <div data-testid="download-icon" />,
  Upload: () => <div data-testid="upload-icon" />,
  Settings: () => <div data-testid="settings-icon" />,
  Calendar: () => <div data-testid="calendar-icon" />,
  User: () => <div data-testid="user-icon" />,
  TestTube: () => <div data-testid="test-tube-icon" />
}));

describe('APIKeyManager', () => {
  const mockOnKeyUpdate = vi.fn();
  const mockOnKeyDelete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined)
      }
    });
  });

  it('renders API key manager interface', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('API Key Manager')).toBeInTheDocument();
      expect(screen.getByText('Securely manage API keys and credentials')).toBeInTheDocument();
    });
  });

  it('displays loading state initially', () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    expect(screen.getByTestId('refresh-icon')).toBeInTheDocument();
  });

  it('shows API keys after loading', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('OpenAI API Key')).toBeInTheDocument();
      expect(screen.getByText('AWS Access Key')).toBeInTheDocument();
      expect(screen.getByText('Slack Webhook')).toBeInTheDocument();
    });
  });

  it('displays search and filter controls', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search API keys...')).toBeInTheDocument();
      expect(screen.getByDisplayValue('All Services')).toBeInTheDocument();
      expect(screen.getByDisplayValue('All Status')).toBeInTheDocument();
    });
  });

  it('filters keys by search term', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search API keys...');
      fireEvent.change(searchInput, { target: { value: 'OpenAI' } });
      
      expect(screen.getByText('OpenAI API Key')).toBeInTheDocument();
      expect(screen.queryByText('AWS Access Key')).not.toBeInTheDocument();
    });
  });

  it('filters keys by service', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const serviceFilter = screen.getByDisplayValue('All Services');
      fireEvent.change(serviceFilter, { target: { value: 'AWS' } });
      
      expect(screen.getByText('AWS Access Key')).toBeInTheDocument();
      expect(screen.queryByText('OpenAI API Key')).not.toBeInTheDocument();
    });
  });

  it('filters keys by status', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const statusFilter = screen.getByDisplayValue('All Status');
      fireEvent.change(statusFilter, { target: { value: 'expired' } });
      
      expect(screen.getByText('Test API Key')).toBeInTheDocument();
      expect(screen.queryByText('OpenAI API Key')).not.toBeInTheDocument();
    });
  });

  it('displays status badges correctly', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      expect(screen.getAllByText('Active')).toHaveLength(3);
      expect(screen.getByText('Expired')).toBeInTheDocument();
    });
  });

  it('displays environment badges', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      expect(screen.getAllByText('production')).toHaveLength(3);
      expect(screen.getByText('development')).toBeInTheDocument();
    });
  });

  it('opens add key modal', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);
      
      expect(screen.getByText('Add New API Key')).toBeInTheDocument();
    });
  });

  it('validates all keys', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const validateButton = screen.getByText('Validate All');
      fireEvent.click(validateButton);
      
      expect(validateButton).toBeDisabled();
    });
  });

  it('refreshes key list', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
      
      expect(refreshButton).toBeDisabled();
    });
  });

  it('shows no keys message when filtered results are empty', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search API keys...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
      
      expect(screen.getByText('No API Keys Found')).toBeInTheDocument();
      expect(screen.getByText('No API keys match your current filters.')).toBeInTheDocument();
    });
  });

  it('handles key modal form submission', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);
      
      // Fill form
      const nameInput = screen.getByLabelText(/key name/i);
      const serviceInput = screen.getByLabelText(/service/i);
      
      fireEvent.change(nameInput, { target: { value: 'Test Key' } });
      fireEvent.change(serviceInput, { target: { value: 'Test Service' } });
      
      const createButton = screen.getByText('Create Key');
      fireEvent.click(createButton);
      
      expect(mockOnKeyUpdate).toHaveBeenCalled();
    });
  });

  it('generates new key value', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);
      
      const generateButton = screen.getByText('Generate');
      fireEvent.click(generateButton);
      
      const valueInput = screen.getByLabelText(/key value/i);
      expect(valueInput).toHaveValue(expect.any(String));
      expect((valueInput as HTMLInputElement).value.length).toBeGreaterThan(0);
    });
  });

  it('handles key rotation schedule configuration', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);
      
      const rotationCheckbox = screen.getByLabelText(/enable automatic key rotation/i);
      fireEvent.click(rotationCheckbox);
      
      expect(screen.getByLabelText(/rotation interval/i)).toBeInTheDocument();
    });
  });

  it('closes modal when cancel is clicked', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);
      
      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);
      
      expect(screen.queryByText('Add New API Key')).not.toBeInTheDocument();
    });
  });

  it('handles permissions input as comma-separated values', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);
      
      const permissionsInput = screen.getByLabelText(/permissions/i);
      fireEvent.change(permissionsInput, { target: { value: 'read, write, admin' } });
      
      expect(permissionsInput).toHaveValue('read, write, admin');
    });
  });

  it('handles expiration date input', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);
      
      const expirationInput = screen.getByLabelText(/expiration date/i);
      fireEvent.change(expirationInput, { target: { value: '2024-12-31' } });
      
      expect(expirationInput).toHaveValue('2024-12-31');
    });
  });

  it('validates rotation interval input', async () => {
    render(
      <APIKeyManager 
        onKeyUpdate={mockOnKeyUpdate}
        onKeyDelete={mockOnKeyDelete}
      />
    );
    
    await waitFor(() => {
      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);
      
      const rotationCheckbox = screen.getByLabelText(/enable automatic key rotation/i);
      fireEvent.click(rotationCheckbox);
      
      const intervalInput = screen.getByLabelText(/rotation interval/i);
      fireEvent.change(intervalInput, { target: { value: '30' } });
      
      expect(intervalInput).toHaveValue(30);
    });
  });
});