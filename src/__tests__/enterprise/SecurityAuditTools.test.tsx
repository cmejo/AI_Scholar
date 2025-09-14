/**
 * Security Audit Tools Test - Testing enhanced audit and monitoring functionality
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { AuditLogViewer } from '../../components/enterprise/security/AuditLogViewer';
import { ThreatMonitor } from '../../components/enterprise/security/ThreatMonitor';
import { SecurityAction } from '../../types/security';

// Mock the security service
vi.mock('../../services/securityDashboardService', () => ({
  securityDashboardService: {
    getAuditLogs: vi.fn().mockResolvedValue({
      logs: [
        {
          id: 'audit_1',
          userId: 'user_123',
          action: 'login_success',
          resource: 'system',
          success: true,
          timestamp: new Date('2024-01-01T10:00:00Z'),
          ipAddress: '192.168.1.100',
          userAgent: 'Mozilla/5.0',
          details: { source: 'test' }
        },
        {
          id: 'audit_2',
          userId: 'user_456',
          action: 'login_failed',
          resource: 'system',
          success: false,
          timestamp: new Date('2024-01-01T10:05:00Z'),
          ipAddress: '192.168.1.101',
          userAgent: 'Mozilla/5.0',
          details: { reason: 'invalid_password' }
        }
      ],
      total: 2
    }),
    getSecurityAlerts: vi.fn().mockResolvedValue([
      {
        id: 'alert_1',
        type: 'login_anomaly',
        severity: 'high',
        message: 'Suspicious login activity detected',
        timestamp: new Date('2024-01-01T10:00:00Z'),
        resolved: false,
        userId: 'user_123'
      }
    ]),
    getSecurityMetrics: vi.fn().mockResolvedValue({
      overview: {
        activeSessions: 5,
        securityAlerts: 1,
        lastSecurityScan: new Date('2024-01-01T09:55:00Z'),
        threatLevel: 'medium'
      }
    }),
    performSecurityAction: vi.fn().mockResolvedValue(true)
  }
}));

describe('Security Audit Tools', () => {
  const mockOnSecurityAction = vi.fn();
  const mockOnExport = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('AuditLogViewer', () => {
    it('renders audit log viewer with logs', async () => {
      render(
        <AuditLogViewer 
          onExport={mockOnExport}
          onSecurityAction={mockOnSecurityAction}
          showAdminControls={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Audit Logs')).toBeInTheDocument();
      });

      // Check if logs are displayed
      expect(screen.getByText('user_123')).toBeInTheDocument();
      expect(screen.getByText('user_456')).toBeInTheDocument();
      expect(screen.getByText('Login Success')).toBeInTheDocument();
      expect(screen.getByText('Login Failed')).toBeInTheDocument();
    });

    it('shows administrative controls when enabled', async () => {
      render(
        <AuditLogViewer 
          onExport={mockOnExport}
          onSecurityAction={mockOnSecurityAction}
          showAdminControls={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Audit Logs')).toBeInTheDocument();
      });

      // Click admin controls button - find by SVG content
      const buttons = screen.getAllByRole('button');
      const adminButton = buttons.find(button => 
        button.querySelector('svg.lucide-settings')
      );
      expect(adminButton).toBeTruthy();
      
      fireEvent.click(adminButton!);

      // Check if admin panel is shown
      expect(screen.getByText('Administrative Controls')).toBeInTheDocument();
      expect(screen.getByText('Bulk Actions')).toBeInTheDocument();
    });

    it('handles log selection and bulk actions', async () => {
      render(
        <AuditLogViewer 
          onExport={mockOnExport}
          onSecurityAction={mockOnSecurityAction}
          showAdminControls={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Audit Logs')).toBeInTheDocument();
      });

      // Open admin controls - find by SVG content
      const buttons = screen.getAllByRole('button');
      const adminButton = buttons.find(button => 
        button.querySelector('svg.lucide-settings')
      );
      expect(adminButton).toBeTruthy();
      
      fireEvent.click(adminButton!);

      // Select all logs
      const selectAllButton = screen.getByText('Select All');
      fireEvent.click(selectAllButton);

      // Perform archive action
      const archiveButton = screen.getByText('Archive');
      fireEvent.click(archiveButton);

      expect(mockOnSecurityAction).toHaveBeenCalledWith({
        type: 'admin_action',
        payload: expect.objectContaining({
          action: 'archive',
          logIds: expect.any(Array)
        })
      });
    });

    it('handles export functionality', async () => {
      render(
        <AuditLogViewer 
          onExport={mockOnExport}
          onSecurityAction={mockOnSecurityAction}
          showAdminControls={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Audit Logs')).toBeInTheDocument();
      });

      const exportButton = screen.getByText('Export');
      fireEvent.click(exportButton);

      expect(mockOnExport).toHaveBeenCalledWith(expect.any(Array));
    });
  });

  describe('ThreatMonitor', () => {
    it('renders threat monitor with statistics', async () => {
      render(
        <ThreatMonitor 
          onSecurityAction={mockOnSecurityAction}
          onAlertAction={vi.fn()}
          showAdminControls={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Threat Monitor')).toBeInTheDocument();
      });

      // Check threat statistics
      expect(screen.getByText('Active Threats')).toBeInTheDocument();
      expect(screen.getByText('Critical Alerts')).toBeInTheDocument();
      expect(screen.getByText('Mitigated')).toBeInTheDocument();
      expect(screen.getByText('Resolved')).toBeInTheDocument();
    });

    it('shows administrative controls when enabled', async () => {
      render(
        <ThreatMonitor 
          onSecurityAction={mockOnSecurityAction}
          onAlertAction={vi.fn()}
          showAdminControls={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Threat Monitor')).toBeInTheDocument();
      });

      // Check for response mode selector
      expect(screen.getByText('Response:')).toBeInTheDocument();
      expect(screen.getByDisplayValue('manual')).toBeInTheDocument();

      // Check for auto-mitigation toggle
      const autoMitigationButton = screen.getByRole('button', { name: /toggle automatic threat mitigation/i });
      expect(autoMitigationButton).toBeInTheDocument();
    });

    it('handles threat response mode changes', async () => {
      render(
        <ThreatMonitor 
          onSecurityAction={mockOnSecurityAction}
          onAlertAction={vi.fn()}
          showAdminControls={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Threat Monitor')).toBeInTheDocument();
      });

      const responseSelect = screen.getByDisplayValue('manual');
      fireEvent.change(responseSelect, { target: { value: 'automatic' } });

      expect(responseSelect).toHaveValue('automatic');
    });

    it('handles real-time monitoring toggle', async () => {
      render(
        <ThreatMonitor 
          onSecurityAction={mockOnSecurityAction}
          onAlertAction={vi.fn()}
          showAdminControls={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Threat Monitor')).toBeInTheDocument();
      });

      // Check initial state shows "Live"
      expect(screen.getByText('Live')).toBeInTheDocument();

      // Toggle real-time monitoring - find button by its SVG content
      const buttons = screen.getAllByRole('button');
      const realtimeButton = buttons.find(button => 
        button.querySelector('svg.lucide-bell')
      );
      expect(realtimeButton).toBeTruthy();
      
      fireEvent.click(realtimeButton!);

      // Should show "Paused" after toggle
      expect(screen.getByText('Paused')).toBeInTheDocument();
    });
  });

  describe('Security Action Integration', () => {
    it('handles security actions with proper logging', async () => {
      const mockOnAlertAction = vi.fn();
      
      render(
        <ThreatMonitor 
          onSecurityAction={mockOnSecurityAction}
          onAlertAction={mockOnAlertAction}
          showAdminControls={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Threat Monitor')).toBeInTheDocument();
      });

      // Test refresh action - find button by its SVG content
      const buttons = screen.getAllByRole('button');
      const refreshButton = buttons.find(button => 
        button.querySelector('svg.lucide-refresh-cw')
      );
      expect(refreshButton).toBeTruthy();
      
      fireEvent.click(refreshButton!);

      // Should call the security service
      expect(mockOnSecurityAction).toHaveBeenCalled();
    });

    it('integrates administrative controls with security logging', async () => {
      render(
        <AuditLogViewer 
          onExport={mockOnExport}
          onSecurityAction={mockOnSecurityAction}
          showAdminControls={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Audit Logs')).toBeInTheDocument();
      });

      // Open admin controls - find button by its SVG content
      const buttons = screen.getAllByRole('button');
      const adminButton = buttons.find(button => 
        button.querySelector('svg.lucide-settings')
      );
      expect(adminButton).toBeTruthy();
      
      fireEvent.click(adminButton!);

      // All administrative actions should be properly logged
      expect(screen.getByText('Administrative Controls')).toBeInTheDocument();
      expect(screen.getByText(/Administrative actions will be logged/)).toBeInTheDocument();
    });
  });
});