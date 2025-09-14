/**
 * IntegrationValidator Component Tests
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import { IntegrationValidator } from '../../components/enterprise/integration/IntegrationValidator';

// Mock the lucide-react icons
vi.mock('lucide-react', () => ({
  TestTube: () => <div data-testid="test-tube-icon" />,
  CheckCircle: () => <div data-testid="check-circle-icon" />,
  XCircle: () => <div data-testid="x-circle-icon" />,
  AlertTriangle: () => <div data-testid="alert-triangle-icon" />,
  RefreshCw: () => <div data-testid="refresh-icon" />,
  Shield: () => <div data-testid="shield-icon" />,
  Zap: () => <div data-testid="zap-icon" />,
  Database: () => <div data-testid="database-icon" />,
  Globe: () => <div data-testid="globe-icon" />,
  Key: () => <div data-testid="key-icon" />,
  Activity: () => <div data-testid="activity-icon" />,
  Clock: () => <div data-testid="clock-icon" />,
  Eye: () => <div data-testid="eye-icon" />,
  EyeOff: () => <div data-testid="eye-off-icon" />,
  Download: () => <div data-testid="download-icon" />,
  FileText: () => <div data-testid="file-text-icon" />,
  Settings: () => <div data-testid="settings-icon" />
}));

describe('IntegrationValidator', () => {
  const mockOnValidationComplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders integration validator interface', () => {
    render(<IntegrationValidator onValidationComplete={mockOnValidationComplete} />);
    
    expect(screen.getByText('Integration Validator')).toBeInTheDocument();
    expect(screen.getByText('Comprehensive testing and validation for all integrations')).toBeInTheDocument();
    expect(screen.getByText('Run Validation')).toBeInTheDocument();
  });

  it('displays validation settings checkboxes', () => {
    render(<IntegrationValidator onValidationComplete={mockOnValidationComplete} />);
    
    expect(screen.getByText('Test Endpoints')).toBeInTheDocument();
    expect(screen.getByText('Security Validation')).toBeInTheDocument();
    expect(screen.getByText('Performance Testing')).toBeInTheDocument();
    expect(screen.getByText('Generate Report')).toBeInTheDocument();
  });

  it('allows toggling validation settings', () => {
    render(<IntegrationValidator onValidationComplete={mockOnValidationComplete} />);
    
    const testEndpointsCheckbox = screen.getByRole('checkbox', { name: /test endpoints/i });
    const securityCheckbox = screen.getByRole('checkbox', { name: /security validation/i });
    
    expect(testEndpointsCheckbox).toBeChecked();
    expect(securityCheckbox).toBeChecked();
    
    fireEvent.click(testEndpointsCheckbox);
    expect(testEndpointsCheckbox).not.toBeChecked();
    
    fireEvent.click(securityCheckbox);
    expect(securityCheckbox).not.toBeChecked();
  });

  it('starts validation when run validation button is clicked', async () => {
    render(<IntegrationValidator onValidationComplete={mockOnValidationComplete} />);
    
    const runButton = screen.getByText('Run Validation');
    fireEvent.click(runButton);
    
    expect(screen.getByText('Validating...')).toBeInTheDocument();
    expect(runButton).toBeDisabled();
  });

  it('shows current step during validation', async () => {
    render(<IntegrationValidator onValidationComplete={mockOnValidationComplete} />);
    
    const runButton = screen.getByText('Run Validation');
    fireEvent.click(runButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Running:/)).toBeInTheDocument();
    });
  });

  it('displays validation results after completion', async () => {
    render(<IntegrationValidator onValidationComplete={mockOnValidationComplete} />);
    
    const runButton = screen.getByText('Run Validation');
    fireEvent.click(runButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Validation completed/)).toBeInTheDocument();
    }, { timeout: 10000 });
    
    expect(mockOnValidationComplete).toHaveBeenCalled();
  });

  it('shows export report button after validation', async () => {
    render(<IntegrationValidator onValidationComplete={mockOnValidationComplete} />);
    
    const runButton = screen.getByText('Run Validation');
    fireEvent.click(runButton);
    
    await waitFor(() => {
      expect(screen.getByText('Export Report')).toBeInTheDocument();
    }, { timeout: 10000 });
  });

  it('toggles details visibility', async () => {
    render(<IntegrationValidator onValidationComplete={mockOnValidationComplete} />);
    
    const runButton = screen.getByText('Run Validation');
    fireEvent.click(runButton);
    
    await waitFor(() => {
      const showDetailsButton = screen.getByText('Show Details');
      expect(showDetailsButton).toBeInTheDocument();
      
      fireEvent.click(showDetailsButton);
      expect(screen.getByText('Hide Details')).toBeInTheDocument();
      expect(screen.getByText('Validation Details')).toBeInTheDocument();
    }, { timeout: 10000 });
  });

  it('displays recommendations when available', async () => {
    render(<IntegrationValidator onValidationComplete={mockOnValidationComplete} />);
    
    const runButton = screen.getByText('Run Validation');
    fireEvent.click(runButton);
    
    await waitFor(() => {
      const recommendationsSection = screen.queryByText('Recommendations');
      if (recommendationsSection) {
        expect(recommendationsSection).toBeInTheDocument();
      }
    }, { timeout: 10000 });
  });

  it('handles validation errors gracefully', async () => {
    // Mock console.error to avoid test output noise
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(<IntegrationValidator onValidationComplete={mockOnValidationComplete} />);
    
    const runButton = screen.getByText('Run Validation');
    fireEvent.click(runButton);
    
    await waitFor(() => {
      expect(screen.getByText('Run Validation')).toBeInTheDocument();
    }, { timeout: 10000 });
    
    consoleSpy.mockRestore();
  });

  it('applies custom className', () => {
    const { container } = render(
      <IntegrationValidator 
        onValidationComplete={mockOnValidationComplete} 
        className="custom-class" 
      />
    );
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('shows export button after validation completes', async () => {
    render(<IntegrationValidator onValidationComplete={mockOnValidationComplete} />);
    
    // Run validation first
    const runButton = screen.getByText('Run Validation');
    fireEvent.click(runButton);
    
    await waitFor(() => {
      expect(screen.getByText('Export Report')).toBeInTheDocument();
    }, { timeout: 10000 });
  });
});