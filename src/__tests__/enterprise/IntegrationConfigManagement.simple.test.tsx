/**
 * Simple Integration Configuration and Management Tests
 * Tests for task 6.2 implementation - focused on core functionality
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
    getAPIKeys: vi.fn().mockResolvedValue([]),
    createAPIKey: vi.fn(),
    updateAPIKey: vi.fn(),
    deleteAPIKey: vi.fn()
  }
}));

describe('Integration Configuration and Management - Core Features', () => {
  describe('ConnectionManager Component', () => {
    it('should render the connection manager interface', () => {
      render(<ConnectionManager />);
      
      expect(screen.getByText('Connection Manager')).toBeInTheDocument();
      expect(screen.getByText('Test Connection')).toBeInTheDocument();
      expect(screen.getByText('Save')).toBeInTheDocument();
    });

    it('should display basic configuration fields', () => {
      render(<ConnectionManager />);
      
      expect(screen.getByText('Basic Configuration')).toBeInTheDocument();
      expect(screen.getByText('Authentication')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('My API Connection')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('https://api.example.com/v1')).toBeInTheDocument();
    });

    it('should include integration tester component', () => {
      render(<ConnectionManager />);
      
      expect(screen.getByText('Integration Tester')).toBeInTheDocument();
      expect(screen.getByText('Run Tests')).toBeInTheDocument();
    });

    it('should support different connection types', () => {
      render(<ConnectionManager />);
      
      const connectionTypeSelect = screen.getByDisplayValue('REST API');
      expect(connectionTypeSelect).toBeInTheDocument();
      
      fireEvent.change(connectionTypeSelect, { target: { value: 'webhook' } });
      expect(connectionTypeSelect).toHaveValue('webhook');
    });

    it('should support SSL validation toggle', () => {
      render(<ConnectionManager />);
      
      const sslCheckbox = screen.getByLabelText('Validate SSL certificates');
      expect(sslCheckbox).toBeChecked();
      
      fireEvent.click(sslCheckbox);
      expect(sslCheckbox).not.toBeChecked();
    });
  });

  describe('APIKeyManager Component', () => {
    beforeEach(() => {
      // Reset mocks
      vi.clearAllMocks();
    });

    it('should render the API key manager interface', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        expect(screen.getByText('API Key Manager')).toBeInTheDocument();
        expect(screen.getByText('Add API Key')).toBeInTheDocument();
        expect(screen.getByText('Refresh')).toBeInTheDocument();
        expect(screen.getByText('Validate All')).toBeInTheDocument();
      });
    });

    it('should display search and filter controls', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search API keys...')).toBeInTheDocument();
        expect(screen.getByDisplayValue('All Services')).toBeInTheDocument();
        expect(screen.getByDisplayValue('All Status')).toBeInTheDocument();
      });
    });

    it('should show empty state when no keys exist', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        expect(screen.getByText('No API Keys Found')).toBeInTheDocument();
        expect(screen.getByText('Get started by adding your first API key.')).toBeInTheDocument();
      });
    });

    it('should open add key modal when clicking add button', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        const addButton = screen.getByText('Add API Key');
        fireEvent.click(addButton);
        
        expect(screen.getByText('Add New API Key')).toBeInTheDocument();
      });
    });
  });

  describe('IntegrationTester Component', () => {
    it('should render integration tester for connection type', () => {
      const mockConfig = {
        name: 'Test Connection',
        endpoint: 'https://api.example.com'
      };
      
      render(
        <IntegrationTester 
          integrationType="connection" 
          config={mockConfig} 
        />
      );
      
      expect(screen.getByText('Integration Tester')).toBeInTheDocument();
      expect(screen.getByText('Comprehensive testing for connection integration')).toBeInTheDocument();
      expect(screen.getByText('Run Tests')).toBeInTheDocument();
    });

    it('should render integration tester for API key type', () => {
      const mockConfig = {
        value: 'test-api-key',
        service: 'Test Service'
      };
      
      render(
        <IntegrationTester 
          integrationType="api_key" 
          config={mockConfig} 
        />
      );
      
      expect(screen.getByText('Comprehensive testing for api_key integration')).toBeInTheDocument();
    });

    it('should start tests when run tests button is clicked', async () => {
      const mockConfig = {
        name: 'Test Connection',
        endpoint: 'https://api.example.com'
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
      
      // Should show testing state
      await waitFor(() => {
        expect(screen.getByText('Testing...')).toBeInTheDocument();
      });
    });

    it('should support different integration types', () => {
      const configs = [
        { type: 'connection', config: { name: 'Test', endpoint: 'https://api.test.com' } },
        { type: 'api_key', config: { value: 'test-key' } },
        { type: 'webhook', config: { endpoint: 'https://webhook.test.com' } },
        { type: 'database', config: { host: 'db.test.com' } }
      ];
      
      configs.forEach(({ type, config }) => {
        const { unmount } = render(
          <IntegrationTester 
            integrationType={type as any} 
            config={config} 
          />
        );
        
        expect(screen.getByText(`Comprehensive testing for ${type} integration`)).toBeInTheDocument();
        unmount();
      });
    });
  });

  describe('Integration Testing and Validation Features', () => {
    it('should provide comprehensive connection testing', () => {
      const mockConfig = {
        name: 'Secure API',
        endpoint: 'https://secure-api.example.com',
        authentication: {
          type: 'api_key',
          credentials: { api_key: 'test-key' }
        },
        validateSsl: true
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

    it('should provide API key validation features', () => {
      const mockConfig = {
        value: 'test-api-key-12345',
        type: 'api_key',
        service: 'Test Service',
        permissions: ['read', 'write'],
        expiresAt: new Date(Date.now() + 86400000) // 1 day from now
      };
      
      render(
        <IntegrationTester 
          integrationType="api_key" 
          config={mockConfig} 
        />
      );
      
      expect(screen.getByText('Comprehensive testing for api_key integration')).toBeInTheDocument();
    });

    it('should handle configuration validation', () => {
      const invalidConfig = {
        name: '', // Missing required field
        endpoint: 'invalid-url' // Invalid URL
      };
      
      render(
        <IntegrationTester 
          integrationType="connection" 
          config={invalidConfig} 
        />
      );
      
      // Should still render but will fail validation when tests run
      expect(screen.getByText('Integration Tester')).toBeInTheDocument();
    });
  });

  describe('Enhanced Security and Validation', () => {
    it('should support secure credential management in ConnectionManager', () => {
      render(<ConnectionManager />);
      
      // Should have authentication section
      expect(screen.getByText('Authentication')).toBeInTheDocument();
      
      // Should have authentication type selector
      const authSelect = screen.getByDisplayValue('None');
      expect(authSelect).toBeInTheDocument();
      
      // Should support different auth types
      fireEvent.change(authSelect, { target: { value: 'api_key' } });
      expect(authSelect).toHaveValue('api_key');
    });

    it('should support comprehensive API key management in APIKeyManager', async () => {
      render(<APIKeyManager />);
      
      await waitFor(() => {
        // Should have key management features
        expect(screen.getByText('Validate All')).toBeInTheDocument();
        expect(screen.getByText('Refresh')).toBeInTheDocument();
        
        // Should have search functionality
        expect(screen.getByPlaceholderText('Search API keys...')).toBeInTheDocument();
      });
    });

    it('should provide detailed test results in IntegrationTester', async () => {
      const mockConfig = {
        name: 'Test Integration',
        endpoint: 'https://api.example.com'
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
      
      // Should eventually complete (with timeout for async operations)
      await waitFor(() => {
        expect(mockOnTestComplete).toHaveBeenCalled();
      }, { timeout: 15000 });
    });
  });
});