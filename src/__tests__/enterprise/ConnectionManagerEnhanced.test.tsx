/**
 * Enhanced ConnectionManager Component Tests
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import { ConnectionManager } from '../../components/enterprise/integration/ConnectionManager';

// Mock the lucide-react icons
vi.mock('lucide-react', () => ({
  Plus: () => <div data-testid="plus-icon" />,
  TestTube: () => <div data-testid="test-tube-icon" />,
  CheckCircle: () => <div data-testid="check-circle-icon" />,
  XCircle: () => <div data-testid="x-circle-icon" />,
  Eye: () => <div data-testid="eye-icon" />,
  EyeOff: () => <div data-testid="eye-off-icon" />,
  RefreshCw: () => <div data-testid="refresh-icon" />,
  Save: () => <div data-testid="save-icon" />,
  Trash2: () => <div data-testid="trash-icon" />
}));

// Mock the IntegrationTester component
vi.mock('../../components/enterprise/integration/IntegrationTester', () => ({
  IntegrationTester: ({ onTestComplete }: any) => (
    <div data-testid="integration-tester">
      <button 
        onClick={() => onTestComplete?.({ success: true, message: 'Test passed' })}
        data-testid="mock-test-button"
      >
        Mock Test
      </button>
    </div>
  )
}));

describe('ConnectionManager', () => {
  const mockOnConnectionSave = vi.fn();
  const mockOnConnectionTest = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders connection manager interface', () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    expect(screen.getByText('Connection Manager')).toBeInTheDocument();
    expect(screen.getByText('Test Connection')).toBeInTheDocument();
    expect(screen.getByText('Save')).toBeInTheDocument();
  });

  it('displays basic configuration fields', () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    expect(screen.getByLabelText(/connection name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/connection type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/endpoint url/i)).toBeInTheDocument();
  });

  it('shows validation errors for required fields', async () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    const testButton = screen.getByText('Test Connection');
    fireEvent.click(testButton);
    
    await waitFor(() => {
      expect(screen.getByText('Connection name is required')).toBeInTheDocument();
      expect(screen.getByText('Endpoint URL is required')).toBeInTheDocument();
    });
  });

  it('validates URL format', async () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    const nameInput = screen.getByLabelText(/connection name/i);
    const endpointInput = screen.getByLabelText(/endpoint url/i);
    
    fireEvent.change(nameInput, { target: { value: 'Test Connection' } });
    fireEvent.change(endpointInput, { target: { value: 'invalid-url' } });
    
    const testButton = screen.getByText('Test Connection');
    fireEvent.click(testButton);
    
    await waitFor(() => {
      expect(screen.getByText('Invalid URL format')).toBeInTheDocument();
    });
  });

  it('shows authentication fields based on type selection', () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    const authTypeSelect = screen.getByDisplayValue('None');
    
    // Change to API Key authentication
    fireEvent.change(authTypeSelect, { target: { value: 'api_key' } });
    expect(screen.getByLabelText(/api key/i)).toBeInTheDocument();
    
    // Change to Basic Auth
    fireEvent.change(authTypeSelect, { target: { value: 'basic_auth' } });
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('toggles credential visibility', () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    const authTypeSelect = screen.getByDisplayValue('None');
    fireEvent.change(authTypeSelect, { target: { value: 'api_key' } });
    
    const apiKeyInput = screen.getByLabelText(/api key/i);
    expect(apiKeyInput).toHaveAttribute('type', 'password');
    
    const toggleButton = screen.getByTestId('eye-icon').parentElement;
    fireEvent.click(toggleButton!);
    
    expect(apiKeyInput).toHaveAttribute('type', 'text');
  });

  it('runs comprehensive connection test', async () => {
    mockOnConnectionTest.mockResolvedValue(true);
    
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    // Fill in valid configuration
    const nameInput = screen.getByLabelText(/connection name/i);
    const endpointInput = screen.getByLabelText(/endpoint url/i);
    
    fireEvent.change(nameInput, { target: { value: 'Test Connection' } });
    fireEvent.change(endpointInput, { target: { value: 'https://api.example.com' } });
    
    const testButton = screen.getByText('Test Connection');
    fireEvent.click(testButton);
    
    expect(testButton).toBeDisabled();
    expect(screen.getByText('Testing...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText(/connection successful/i)).toBeInTheDocument();
    }, { timeout: 10000 });
    
    expect(mockOnConnectionTest).toHaveBeenCalled();
  });

  it('displays test failure results', async () => {
    mockOnConnectionTest.mockResolvedValue(false);
    
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    // Fill in valid configuration
    const nameInput = screen.getByLabelText(/connection name/i);
    const endpointInput = screen.getByLabelText(/endpoint url/i);
    
    fireEvent.change(nameInput, { target: { value: 'Test Connection' } });
    fireEvent.change(endpointInput, { target: { value: 'https://api.example.com' } });
    
    const testButton = screen.getByText('Test Connection');
    fireEvent.click(testButton);
    
    await waitFor(() => {
      expect(screen.getByText(/connection validation failed/i)).toBeInTheDocument();
    }, { timeout: 10000 });
  });

  it('saves connection configuration', () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    // Fill in valid configuration
    const nameInput = screen.getByLabelText(/connection name/i);
    const endpointInput = screen.getByLabelText(/endpoint url/i);
    
    fireEvent.change(nameInput, { target: { value: 'Test Connection' } });
    fireEvent.change(endpointInput, { target: { value: 'https://api.example.com' } });
    
    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);
    
    expect(mockOnConnectionSave).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Test Connection',
        endpoint: 'https://api.example.com'
      })
    );
  });

  it('adds and removes custom headers', () => {
    // Mock prompt to return a header name
    global.prompt = vi.fn().mockReturnValue('Authorization');
    
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    const addHeaderButton = screen.getByText('Add Header');
    fireEvent.click(addHeaderButton);
    
    expect(global.prompt).toHaveBeenCalledWith('Header name:');
    expect(screen.getByDisplayValue('Authorization')).toBeInTheDocument();
    
    // Remove header
    const removeButton = screen.getByTestId('trash-icon').parentElement;
    fireEvent.click(removeButton!);
    
    expect(screen.queryByDisplayValue('Authorization')).not.toBeInTheDocument();
  });

  it('updates timeout and retry settings', () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    const timeoutInput = screen.getByDisplayValue('30000');
    const retriesInput = screen.getByDisplayValue('3');
    
    fireEvent.change(timeoutInput, { target: { value: '60000' } });
    fireEvent.change(retriesInput, { target: { value: '5' } });
    
    expect(timeoutInput).toHaveValue(60000);
    expect(retriesInput).toHaveValue(5);
  });

  it('toggles SSL validation setting', () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    const sslCheckbox = screen.getByLabelText(/validate ssl certificates/i);
    expect(sslCheckbox).toBeChecked();
    
    fireEvent.click(sslCheckbox);
    expect(sslCheckbox).not.toBeChecked();
  });

  it('includes IntegrationTester component', () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    expect(screen.getByTestId('integration-tester')).toBeInTheDocument();
  });

  it('handles IntegrationTester test completion', () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    const mockTestButton = screen.getByTestId('mock-test-button');
    fireEvent.click(mockTestButton);
    
    expect(screen.getByText('Test passed')).toBeInTheDocument();
  });

  it('prevents save with invalid configuration', () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    // Try to save without filling required fields
    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);
    
    expect(mockOnConnectionSave).not.toHaveBeenCalled();
  });

  it('shows HTTP method selection for API connections', () => {
    render(
      <ConnectionManager 
        onConnectionSave={mockOnConnectionSave}
        onConnectionTest={mockOnConnectionTest}
      />
    );
    
    const typeSelect = screen.getByDisplayValue('REST API');
    expect(typeSelect).toBeInTheDocument();
    
    expect(screen.getByDisplayValue('GET')).toBeInTheDocument();
    
    const methodSelect = screen.getByDisplayValue('GET');
    fireEvent.change(methodSelect, { target: { value: 'POST' } });
    expect(methodSelect).toHaveValue('POST');
  });
});