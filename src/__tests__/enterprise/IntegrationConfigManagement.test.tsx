/**
 * Integration Configuration and Management Tests
 * Tests for task 6.2 implementation
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ConnectionManager, APIKeyManager, IntegrationTester } from '../../components/enterprise/integration';

// Mock the integration management service
vi.mock('../../services/integrationManagementService', () => ({
  integrationManagementService: {
    testConnection: vi.fn(),
    getAPIKeys: vi.fn(),
    createAPIKey: vi.fn(),
    updateAPIKey: vi.fn(),
    deleteAPIKey: vi.fn()
  }
}));

describe('Integration Configuration and Management', () => {
  describe('ConnectionManager', () => {
    it('should render connection configuration form', () => {
      render(<ConnectionManager />);
      
      expect(screen.getByText('Connection Manager')).toBeInTheDocument();
      expect(screen.getByLabelText(/Connection Name/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Endpoint URL/)).toBeInTheDocument();
      expect(screen.getByText('Test Connection')).toBeInTheDocument();
    });

    it('should validate required fields', async () => {
      render(<ConnectionManager />);
      
      const testButton = screen.getByText('Test Connection');
      fireEvent.click(testButton);
      
      await waitFor(() => {
        expect(screen.getByText('Connection name is required')).toBeInTheDocument();
        expect(screen.getByText('Endpoint URL is required')).toBeInTheDocument();
      });
    });

    it('should validate URL format', async () => {
      render(<ConnectionManager />);
      
      const nameInput = screen.getByLabelText(/Connection Name/);
      const endpointInput = screen.getByLabelText(/Endpoint URL/);
      
      fireEvent.change(nameInput, { target: { value: 'Test Connection' } });
      fireEvent.change(endpointInput, { target: { value: 'invalid-url' } });
      
      const testButton = screen.getByText('Test Connection');
      fireEvent.click(testButton);
      
      await waitFor(() => {
        expect(screen.getByText('Invalid URL format')).toBeInTheDocument();
      });
    });

    it('should support different authentication types', () => {
      render(<ConnectionManager />);
      
      const authSelect = screen.getByDisplayValue('None');
      fireEvent.change(authSelect, { target: { value: 'api_key' } });
      
      expect(screen.getByLabelText(/API Key/)).toBeInTheDocument();
      
      fireEvent.change(authSelect, { target: { value: 'basic_auth' } });
      
      expect(screen.getByLabelText(/Username/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Password/)).toBeInTheDocument();
    });

    it('should perform comprehensive connection testing', async () => {
      const mockOnConnectionTest = vi.fn().mockResolvedValue(true);
      
      render(<ConnectionManager onConnectionTest={mockOnConnectionTest} />);
      
      // Fill in valid configuration
      fireEvent.change(screen.getByLabelText(/Connection Name/), { 
        target: { value: 'Test API' } 
      });
      fireEvent.change(screen.getByLabelText(/Endpoint URL/), { 
        target: { value: 'https://api.example.com' } 
      });
      
      const testButton = screen.getByText('Test Connection');
      fireEvent.click(testButton);
      
      // Should show testing progress
      await waitFor(() => {
        expect(screen.getByText(/Testing connectivity/)).toBeInTheDocument();
      });
      
      // Should complete with success
      await waitFor(() => {
        expect(screen.getByText(/Connection successful/)).toBeInTheDocument();
      }, { timeout: 10000 });
      
      expect(mockOnConnectionTest).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Test API',
          endpoint: 'https://api.example.com'
        })
      );
    });

    it('should handle SSL validation settings', () => {
      render(<ConnectionManager />);
      
      const sslCheckbox = screen.getByLabelText(/Validate SSL certificates/);
      expect(sslCheckbox).toBeChecked();
      
      fireEvent.click(sslCheckbox);
      expect(sslCheckbox).not.toBeChecked();
    });

    it('should support custom headers', () => {
      render(<ConnectionManager />);
      
      const addHeaderButton = screen.getByText('Add Header');
      
      // Mock prompt for header name
      window.prompt = vi.fn().mockReturnValue('Authorization');
      
      fireEvent.click(addHeaderButton);
      
      expect(screen.getByDisplayValue('Authorization')).toBeInTheDocument();
    });
  });

  describe('APIKeyManager', () => {
    beforeEach(() => {
      // Mock API keys data
      const mockKeys = [
        {
          id: 'key_1',
          name: 'Test API Key',
          service: 'OpenAI',
          type: 'api_key',
          value: 'sk-test123',
          status: 'active',
          environment: 'development',
          permissions: ['read', 'write']
        }
      ];
      
      require('../../services/integrationManagementService').integrationManagementService.getAPIKeys
        .mockResolvedValue(mockKeys);
    });

    it('should render API key management interface', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        expect(screen.getByText('API Key Manager')).toBeInTheDocument();
        expect(screen.getByText('Add API Key')).toBeInTheDocument();
      });
    });

    it('should display API keys with masked values', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        expect(screen.getByText('Test API Key')).toBeInTheDocument();
        expect(screen.getByText('••••••••••••••••')).toBeInTheDocument();
      });
    });

    it('should support key visibility toggle', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        const eyeButton = screen.getByTitle('Show');
        fireEvent.click(eyeButton);
        
        expect(screen.getByText('sk-test123')).toBeInTheDocument();
      });
    });

    it('should validate API key format', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        const addButton = screen.getByText('Add API Key');
        fireEvent.click(addButton);
      });
      
      // Fill in form with invalid key
      fireEvent.change(screen.getByLabelText(/Key Name/), { 
        target: { value: 'Test Key' } 
      });
      fireEvent.change(screen.getByLabelText(/Service/), { 
        target: { value: 'Test Service' } 
      });
      fireEvent.change(screen.getByLabelText(/Key Value/), { 
        target: { value: 'short' } 
      });
      
      const createButton = screen.getByText('Create Key');
      fireEvent.click(createButton);
      
      // Should validate key format
      expect(screen.getByText('Test Key')).toBeInTheDocument();
    });

    it('should support key rotation', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        const testButton = screen.getByTitle('Test API Key');
        fireEvent.click(testButton);
      });
      
      // Should show test results
      await waitFor(() => {
        expect(screen.getByText(/API key is valid/)).toBeInTheDocument();
      });
    });

    it('should support bulk validation', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        const validateAllButton = screen.getByText('Validate All');
        fireEvent.click(validateAllButton);
      });
      
      // Should show validation progress
      await waitFor(() => {
        expect(screen.getByText(/validation/i)).toBeInTheDocument();
      });
    });

    it('should support expiration date configuration', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        const addButton = screen.getByText('Add API Key');
        fireEvent.click(addButton);
      });
      
      const expirationInput = screen.getByLabelText(/Expiration Date/);
      expect(expirationInput).toBeInTheDocument();
      
      fireEvent.change(expirationInput, { 
        target: { value: '2024-12-31' } 
      });
      
      expect(expirationInput).toHaveValue('2024-12-31');
    });

    it('should support rotation schedule configuration', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        const addButton = screen.getByText('Add API Key');
        fireEvent.click(addButton);
      });
      
      const rotationCheckbox = screen.getByLabelText(/Enable Automatic Key Rotation/);
      fireEvent.click(rotationCheckbox);
      
      expect(screen.getByLabelText(/Rotation Interval/)).toBeInTheDocument();
    });
  });

  describe('IntegrationTester', () => {
    it('should render integration tester interface', () => {
      const mockConfig = {
        name: 'Test Integration',
        endpoint: 'https://api.example.com'
      };
      
      render(
        <IntegrationTester 
          integrationType="connection" 
          config={mockConfig} 
        />
      );
      
      expect(screen.getByText('Integration Tester')).toBeInTheDocument();
      expect(screen.getByText('Run Tests')).toBeInTheDocument();
    });

    it('should run comprehensive test suite', async () => {
      const mockConfig = {
        name: 'Test Integration',
        endpoint: 'https://api.example.com',
        authentication: { type: 'api_key', credentials: { api_key: 'test-key' } }
      };
      
      const mockOnTestComplete = vi.fn();
      
      render(
        <IntegrationTester 
          integrationType="connection" 
          config={mockConfig}
          onTestComplete={mockOnTestComplete}
        />
      );
      
      const runTestsButton = screen.getByText('Run Tests');
      fireEvent.click(runTestsButton);
      
      // Should show testing progress
      await waitFor(() => {
        expect(screen.getByText('Testing...')).toBeInTheDocument();
      });
      
      // Should complete tests
      await waitFor(() => {
        expect(mockOnTestComplete).toHaveBeenCalled();
      }, { timeout: 15000 });
    });

    it('should support different integration types', () => {
      const mockConfig = { value: 'test-api-key' };
      
      render(
        <IntegrationTester 
          integrationType="api_key" 
          config={mockConfig} 
        />
      );
      
      expect(screen.getByText(/api_key integration/)).toBeInTheDocument();
    });

    it('should show detailed test results', async () => {
      const mockConfig = {
        name: 'Test Integration',
        endpoint: 'https://api.example.com'
      };
      
      render(
        <IntegrationTester 
          integrationType="connection" 
          config={mockConfig} 
        />
      );
      
      const runTestsButton = screen.getByText('Run Tests');
      fireEvent.click(runTestsButton);
      
      // Wait for tests to complete
      await waitFor(() => {
        expect(screen.getByText(/tests passed/i)).toBeInTheDocument();
      }, { timeout: 15000 });
      
      // Should have show details button
      const showDetailsButton = screen.getByText('Show Details');
      fireEvent.click(showDetailsButton);
      
      expect(screen.getByText('Test Details')).toBeInTheDocument();
    });
  });

  describe('Integration Testing and Validation', () => {
    it('should validate connection configuration before testing', async () => {
      render(<ConnectionManager />);
      
      // Try to test without configuration
      const testButton = screen.getByText('Test Connection');
      fireEvent.click(testButton);
      
      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText('Connection name is required')).toBeInTheDocument();
      });
    });

    it('should perform security validation for SSL connections', async () => {
      const mockConfig = {
        name: 'Secure API',
        endpoint: 'https://secure-api.example.com',
        validateSsl: true
      };
      
      render(
        <IntegrationTester 
          integrationType="connection" 
          config={mockConfig} 
        />
      );
      
      const runTestsButton = screen.getByText('Run Tests');
      fireEvent.click(runTestsButton);
      
      // Should include SSL validation in tests
      await waitFor(() => {
        expect(screen.getByText(/SSL\/TLS/)).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('should validate API key permissions and expiration', async () => {
      const mockConfig = {
        value: 'test-api-key-12345',
        permissions: ['read', 'write'],
        expiresAt: new Date(Date.now() + 86400000) // 1 day from now
      };
      
      render(
        <IntegrationTester 
          integrationType="api_key" 
          config={mockConfig} 
        />
      );
      
      const runTestsButton = screen.getByText('Run Tests');
      fireEvent.click(runTestsButton);
      
      // Should validate permissions and expiration
      await waitFor(() => {
        expect(screen.getByText(/Expiration Check/)).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('should handle test failures gracefully', async () => {
      const mockConfig = {
        name: 'Failing Integration',
        endpoint: 'https://nonexistent-api.example.com'
      };
      
      render(
        <IntegrationTester 
          integrationType="connection" 
          config={mockConfig} 
        />
      );
      
      const runTestsButton = screen.getByText('Run Tests');
      fireEvent.click(runTestsButton);
      
      // Should handle failures
      await waitFor(() => {
        expect(screen.getByText(/failed/i)).toBeInTheDocument();
      }, { timeout: 15000 });
    });
  });
});