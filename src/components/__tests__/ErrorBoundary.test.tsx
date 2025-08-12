import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { errorTrackingService } from '../../services/errorTrackingService';
import { ErrorBoundary, useErrorHandler, withErrorBoundary } from '../ErrorBoundary';

// Mock the error tracking service
vi.mock('../../services/errorTrackingService', () => ({
  errorTrackingService: {
    reportError: vi.fn(),
  },
}));

// Mock console methods to avoid noise in tests
const consoleSpy = {
  error: vi.spyOn(console, 'error').mockImplementation(() => {}),
  warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
  group: vi.spyOn(console, 'group').mockImplementation(() => {}),
  groupEnd: vi.spyOn(console, 'groupEnd').mockImplementation(() => {}),
};

// Component that throws an error for testing
const ThrowError: React.FC<{ shouldThrow?: boolean; errorMessage?: string }> = ({ 
  shouldThrow = true, 
  errorMessage = 'Test error' 
}) => {
  if (shouldThrow) {
    throw new Error(errorMessage);
  }
  return <div>No error</div>;
};

// Component that uses the error handler hook
const ComponentWithErrorHandler: React.FC<{ triggerError?: boolean }> = ({ triggerError }) => {
  const handleError = useErrorHandler();

  const triggerTestError = () => {
    const error = new Error('Hook error test');
    handleError(error, { customInfo: 'test data' });
  };

  return (
    <div>
      <span>Component with error handler</span>
      {triggerError && (
        <button onClick={triggerTestError}>Trigger Error</button>
      )}
    </div>
  );
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    consoleSpy.error.mockClear();
    consoleSpy.warn.mockClear();
    consoleSpy.group.mockClear();
    consoleSpy.groupEnd.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Basic Error Handling', () => {
    it('should render children when there is no error', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByText('No error')).toBeInTheDocument();
    });

    it('should catch and display error when child component throws', () => {
      render(
        <ErrorBoundary>
          <ThrowError errorMessage="Component crashed" />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByText(/We're sorry, but something unexpected happened/)).toBeInTheDocument();
    });

    it('should report error to error tracking service', () => {
      render(
        <ErrorBoundary>
          <ThrowError errorMessage="Tracking test error" />
        </ErrorBoundary>
      );

      expect(errorTrackingService.reportError).toHaveBeenCalledWith(
        expect.objectContaining({
          error_type: 'ComponentError',
          error_message: 'Tracking test error',
          severity: 'high',
          category: 'application',
          feature_name: 'react_component',
          operation: 'component_render',
        })
      );
    });

    it('should call onError prop when provided', () => {
      const onError = vi.fn();
      
      render(
        <ErrorBoundary onError={onError}>
          <ThrowError errorMessage="Callback test error" />
        </ErrorBoundary>
      );

      expect(onError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String),
        })
      );
    });
  });

  describe('Custom Fallback UI', () => {
    it('should render custom fallback component when provided', () => {
      const CustomFallback = () => <div>Custom error message</div>;

      render(
        <ErrorBoundary fallback={<CustomFallback />}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Custom error message')).toBeInTheDocument();
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
    });

    it('should render custom fallback function when provided', () => {
      const fallbackFunction = (error: Error, errorInfo: React.ErrorInfo, retry: () => void) => (
        <div>
          <span>Function fallback: {error.message}</span>
          <button onClick={retry}>Custom Retry</button>
        </div>
      );

      render(
        <ErrorBoundary fallback={fallbackFunction}>
          <ThrowError errorMessage="Function fallback test" />
        </ErrorBoundary>
      );

      expect(screen.getByText('Function fallback: Function fallback test')).toBeInTheDocument();
      expect(screen.getByText('Custom Retry')).toBeInTheDocument();
    });
  });

  describe('Retry Functionality', () => {
    it('should show retry button for retryable errors', () => {
      render(
        <ErrorBoundary maxRetries={3}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText(/Try Again \(1\/3\)/)).toBeInTheDocument();
    });

    it('should retry rendering when retry button is clicked', async () => {
      let shouldThrow = true;
      const RetryableComponent = () => {
        if (shouldThrow) {
          shouldThrow = false; // Only throw once
          throw new Error('Retryable error');
        }
        return <div>Retry successful</div>;
      };

      render(
        <ErrorBoundary maxRetries={3}>
          <RetryableComponent />
        </ErrorBoundary>
      );

      // Should show error initially
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // Click retry button
      const retryButton = screen.getByText(/Try Again/);
      fireEvent.click(retryButton);

      // Should show successful render after retry
      await waitFor(() => {
        expect(screen.getByText('Retry successful')).toBeInTheDocument();
      });
    });

    it('should increment retry count on each retry attempt', () => {
      render(
        <ErrorBoundary maxRetries={3}>
          <ThrowError />
        </ErrorBoundary>
      );

      // First attempt
      expect(screen.getByText(/Try Again \(1\/3\)/)).toBeInTheDocument();

      // Click retry
      fireEvent.click(screen.getByText(/Try Again/));

      // Second attempt
      expect(screen.getByText(/Try Again \(2\/3\)/)).toBeInTheDocument();
    });

    it('should hide retry button after max retries reached', () => {
      render(
        <ErrorBoundary maxRetries={1}>
          <ThrowError />
        </ErrorBoundary>
      );

      // Click retry to reach max retries
      fireEvent.click(screen.getByText(/Try Again/));

      // Retry button should not be visible anymore
      expect(screen.queryByText(/Try Again/)).not.toBeInTheDocument();
    });
  });

  describe('Reset Functionality', () => {
    it('should reset error state when resetKeys change', () => {
      let resetKey = 'initial';
      const { rerender } = render(
        <ErrorBoundary resetKeys={[resetKey]}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      // Initially no error
      expect(screen.getByText('No error')).toBeInTheDocument();

      // Cause error
      rerender(
        <ErrorBoundary resetKeys={[resetKey]}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // Change reset key to trigger reset
      resetKey = 'changed';
      rerender(
        <ErrorBoundary resetKeys={[resetKey]}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByText('No error')).toBeInTheDocument();
    });

    it('should reset error state when resetOnPropsChange is true', () => {
      let propValue = 'initial';
      const { rerender } = render(
        <ErrorBoundary resetOnPropsChange={true} customProp={propValue}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      // Initially no error
      expect(screen.getByText('No error')).toBeInTheDocument();

      // Cause error
      rerender(
        <ErrorBoundary resetOnPropsChange={true} customProp={propValue}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // Change prop to trigger reset
      propValue = 'changed';
      rerender(
        <ErrorBoundary resetOnPropsChange={true} customProp={propValue}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByText('No error')).toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('should show Go Home button', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Go Home')).toBeInTheDocument();
    });

    it('should show Report Bug button', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Report Bug')).toBeInTheDocument();
    });

    it('should navigate to home when Go Home is clicked', () => {
      // Mock window.location
      const originalLocation = window.location;
      delete (window as any).location;
      window.location = { ...originalLocation, href: '' };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      fireEvent.click(screen.getByText('Go Home'));

      expect(window.location.href).toBe('/');

      // Restore original location
      window.location = originalLocation;
    });

    it('should open bug report when Report Bug is clicked', () => {
      // Mock window.open
      const mockOpen = vi.fn();
      window.open = mockOpen;

      render(
        <ErrorBoundary>
          <ThrowError errorMessage="Bug report test" />
        </ErrorBoundary>
      );

      fireEvent.click(screen.getByText('Report Bug'));

      expect(mockOpen).toHaveBeenCalledWith(
        expect.stringContaining('mailto:support@example.com')
      );
      expect(mockOpen).toHaveBeenCalledWith(
        expect.stringContaining('Bug report test')
      );
    });
  });

  describe('Development Mode Features', () => {
    it('should show error details in development mode', () => {
      // Mock development environment
      const originalEnv = import.meta.env;
      (import.meta as any).env = { ...originalEnv, DEV: true };

      render(
        <ErrorBoundary>
          <ThrowError errorMessage="Dev mode test error" />
        </ErrorBoundary>
      );

      expect(screen.getByText('Error Details (Development)')).toBeInTheDocument();

      // Restore original environment
      (import.meta as any).env = originalEnv;
    });

    it('should log error details to console in development mode', () => {
      // Mock development environment
      const originalEnv = import.meta.env;
      (import.meta as any).env = { ...originalEnv, DEV: true };

      render(
        <ErrorBoundary>
          <ThrowError errorMessage="Console log test" />
        </ErrorBoundary>
      );

      expect(consoleSpy.group).toHaveBeenCalledWith('🚨 Error Boundary');
      expect(consoleSpy.error).toHaveBeenCalledWith('Error:', expect.any(Error));

      // Restore original environment
      (import.meta as any).env = originalEnv;
    });
  });

  describe('Error ID Generation', () => {
    it('should generate and display unique error ID', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const errorIdElement = screen.getByText(/error_\d+_[a-z0-9]+/);
      expect(errorIdElement).toBeInTheDocument();
    });

    it('should generate different error IDs for different errors', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError errorMessage="First error" />
        </ErrorBoundary>
      );

      const firstErrorId = screen.getByText(/error_\d+_[a-z0-9]+/).textContent;

      // Reset and cause different error
      rerender(
        <ErrorBoundary resetKeys={['reset']}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      rerender(
        <ErrorBoundary resetKeys={['reset2']}>
          <ThrowError errorMessage="Second error" />
        </ErrorBoundary>
      );

      const secondErrorId = screen.getByText(/error_\d+_[a-z0-9]+/).textContent;

      expect(firstErrorId).not.toBe(secondErrorId);
    });
  });

  describe('withErrorBoundary HOC', () => {
    it('should wrap component with error boundary', () => {
      const TestComponent = () => <div>Test component</div>;
      const WrappedComponent = withErrorBoundary(TestComponent);

      render(<WrappedComponent />);

      expect(screen.getByText('Test component')).toBeInTheDocument();
    });

    it('should catch errors in wrapped component', () => {
      const WrappedThrowError = withErrorBoundary(ThrowError);

      render(<WrappedThrowError />);

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('should pass error boundary props to wrapper', () => {
      const onError = vi.fn();
      const WrappedThrowError = withErrorBoundary(ThrowError, { onError });

      render(<WrappedThrowError />);

      expect(onError).toHaveBeenCalled();
    });

    it('should set correct display name', () => {
      const TestComponent = () => <div>Test</div>;
      TestComponent.displayName = 'TestComponent';
      
      const WrappedComponent = withErrorBoundary(TestComponent);

      expect(WrappedComponent.displayName).toBe('withErrorBoundary(TestComponent)');
    });
  });

  describe('useErrorHandler Hook', () => {
    it('should report errors to tracking service', () => {
      render(<ComponentWithErrorHandler triggerError={true} />);

      fireEvent.click(screen.getByText('Trigger Error'));

      expect(errorTrackingService.reportError).toHaveBeenCalledWith(
        expect.objectContaining({
          error_type: 'Error',
          error_message: 'Hook error test',
          severity: 'medium',
          category: 'application',
          feature_name: 'react_hook',
          operation: 'error_handler',
          context_data: expect.objectContaining({
            customInfo: 'test data',
          }),
        })
      );
    });

    it('should log errors in development mode', () => {
      // Mock development environment
      const originalEnv = import.meta.env;
      (import.meta as any).env = { ...originalEnv, DEV: true };

      render(<ComponentWithErrorHandler triggerError={true} />);

      fireEvent.click(screen.getByText('Trigger Error'));

      expect(consoleSpy.error).toHaveBeenCalledWith(
        'Error reported via useErrorHandler:',
        expect.any(Error)
      );

      // Restore original environment
      (import.meta as any).env = originalEnv;
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveAccessibleName();
      });
    });

    it('should be keyboard navigable', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toBeFocusable();
      });
    });
  });

  describe('Error State Management', () => {
    it('should maintain error state across re-renders', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // Re-render with same props
      rerender(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('should clean up timeouts on unmount', () => {
      const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');
      
      const { unmount } = render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      unmount();

      // clearTimeout should be called during cleanup
      expect(clearTimeoutSpy).toHaveBeenCalled();
    });
  });
});