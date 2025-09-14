/**
 * Security Dashboard Component Tests
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SecurityDashboard } from '../../components/enterprise/SecurityDashboard';
import { User } from '../../types/auth';

import { vi } from 'vitest';

// Mock the security dashboard service
vi.mock('../../services/securityDashboardService', () => ({
  securityDashboardService: {
    subscribe: vi.fn((callback) => {
      // Simulate initial data
      setTimeout(() => {
        callback({
          overview: {
            activeSessions: 5,
            securityAlerts: 2,
            lastSecurityScan: new Date(),
            threatLevel: 'low' as const
          },
          sessions: [],
          auditLogs: [],
          alerts: [],
          recentActivity: {
            totalEvents: 10,
            failedLogins: 1,
            rateLimitViolations: 0,
            suspiciousActivities: 0
          }
        });
      }, 100);
      return () => {}; // Unsubscribe function
    }),
    performSecurityAction: vi.fn().mockResolvedValue(true),
    getActiveSessions: vi.fn().mockResolvedValue([]),
    getSecurityAlerts: vi.fn().mockResolvedValue([]),
    getAuditLogs: vi.fn().mockResolvedValue({ logs: [], total: 0 })
  }
}));

// Mock the security components
vi.mock('../../components/enterprise/security', () => ({
  SessionManager: ({ onSecurityAction }: any) => (
    <div data-testid="session-manager">
      Session Manager Component
      <button onClick={() => onSecurityAction({ type: 'terminate_session', payload: { sessionId: 'test' } })}>
        Test Action
      </button>
    </div>
  ),
  AuditLogViewer: ({ onExport }: any) => (
    <div data-testid="audit-log-viewer">
      Audit Log Viewer Component
      <button onClick={() => onExport([])}>Test Export</button>
    </div>
  ),
  ThreatMonitor: ({ onSecurityAction, onAlertAction }: any) => (
    <div data-testid="threat-monitor">
      Threat Monitor Component
      <button onClick={() => onSecurityAction({ type: 'resolve_alert', payload: { alertId: 'test' } })}>
        Test Resolve
      </button>
      <button onClick={() => onAlertAction('test', 'resolve')}>Test Alert Action</button>
    </div>
  )
}));

describe('SecurityDashboard', () => {
  const mockUser: User = {
    id: 'test-user',
    name: 'Test User',
    email: 'test@example.com',
    role: 'admin'
  };

  const mockOnSecurityAction = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders security dashboard with loading state initially', () => {
    render(<SecurityDashboard currentUser={mockUser} onSecurityAction={mockOnSecurityAction} />);
    
    expect(screen.getByText('Loading security dashboard...')).toBeInTheDocument();
  });

  it('renders security dashboard with data after loading', async () => {
    render(<SecurityDashboard currentUser={mockUser} onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Security Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText('Real-time security monitoring and threat detection')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument(); // Active sessions
    expect(screen.getByText('2')).toBeInTheDocument(); // Security alerts
  });

  it('displays current user information', async () => {
    render(<SecurityDashboard currentUser={mockUser} onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    expect(screen.getByText('admin')).toBeInTheDocument();
  });

  it('switches between tabs correctly', async () => {
    render(<SecurityDashboard currentUser={mockUser} onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Security Dashboard')).toBeInTheDocument();
    });

    // Switch to Session Manager tab
    fireEvent.click(screen.getByText('Session Manager'));
    expect(screen.getByTestId('session-manager')).toBeInTheDocument();

    // Switch to Threat Monitor tab
    fireEvent.click(screen.getByText('Threat Monitor'));
    expect(screen.getByTestId('threat-monitor')).toBeInTheDocument();

    // Switch to Audit Logs tab
    fireEvent.click(screen.getByText('Audit Logs'));
    expect(screen.getByTestId('audit-log-viewer')).toBeInTheDocument();
  });

  it('handles security actions correctly', async () => {
    render(<SecurityDashboard currentUser={mockUser} onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Security Dashboard')).toBeInTheDocument();
    });

    // Switch to Session Manager and test action
    fireEvent.click(screen.getByText('Session Manager'));
    fireEvent.click(screen.getByText('Test Action'));

    expect(mockOnSecurityAction).toHaveBeenCalledWith({
      type: 'terminate_session',
      payload: { sessionId: 'test' }
    });
  });

  it('handles refresh action', async () => {
    render(<SecurityDashboard currentUser={mockUser} onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Security Dashboard')).toBeInTheDocument();
    });

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);

    expect(mockOnSecurityAction).toHaveBeenCalledWith({
      type: 'refresh_data'
    });
  });

  it('displays threat level with appropriate styling', async () => {
    render(<SecurityDashboard currentUser={mockUser} onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Low')).toBeInTheDocument();
    });

    const threatLevelElement = screen.getByText('Low');
    expect(threatLevelElement).toHaveClass('text-green-400');
  });

  it('handles component integration correctly', async () => {
    render(<SecurityDashboard currentUser={mockUser} onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Security Dashboard')).toBeInTheDocument();
    });

    // Test Threat Monitor integration
    fireEvent.click(screen.getByText('Threat Monitor'));
    fireEvent.click(screen.getByText('Test Alert Action'));

    // Should trigger security action through the integrated handler
    expect(mockOnSecurityAction).toHaveBeenCalledWith({
      type: 'resolve_alert',
      payload: { alertId: 'test' }
    });
  });
});