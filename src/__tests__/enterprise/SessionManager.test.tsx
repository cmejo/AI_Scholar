/**
 * Session Manager Component Tests
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SessionManager } from '../../components/enterprise/security/SessionManager';
import { vi } from 'vitest';

// Mock the security dashboard service
vi.mock('../../services/securityDashboardService', () => ({
  securityDashboardService: {
    getActiveSessions: vi.fn().mockResolvedValue([
      {
        id: 'session_1',
        userId: 'user_1',
        userEmail: 'user1@example.com',
        loginTime: new Date('2024-01-01T10:00:00Z'),
        lastActivity: new Date('2024-01-01T11:00:00Z'),
        ipAddress: '192.168.1.100',
        userAgent: 'Mozilla/5.0 Test Browser',
        location: 'New York',
        isActive: true
      },
      {
        id: 'session_2',
        userId: 'user_2',
        userEmail: 'user2@example.com',
        loginTime: new Date('2024-01-01T09:00:00Z'),
        lastActivity: new Date('2024-01-01T09:30:00Z'),
        ipAddress: '192.168.1.101',
        userAgent: 'Mozilla/5.0 Test Browser',
        location: 'London',
        isActive: false
      }
    ]),
    performSecurityAction: vi.fn().mockResolvedValue(true)
  }
}));

describe('SessionManager', () => {
  const mockOnSecurityAction = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders session manager with sessions', async () => {
    render(<SessionManager onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Session Management')).toBeInTheDocument();
    });

    expect(screen.getByText('user1@example.com')).toBeInTheDocument();
    expect(screen.getByText('user2@example.com')).toBeInTheDocument();
  });

  it('displays session statistics correctly', async () => {
    render(<SessionManager onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('2 shown')).toBeInTheDocument();
    });

    expect(screen.getByText('1 active')).toBeInTheDocument();
  });

  it('filters sessions by search term', async () => {
    render(<SessionManager onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Session Management')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search by user, email, IP address, or location...');
    fireEvent.change(searchInput, { target: { value: 'user1' } });

    await waitFor(() => {
      expect(screen.getByText('user1@example.com')).toBeInTheDocument();
      expect(screen.queryByText('user2@example.com')).not.toBeInTheDocument();
    });
  });

  it('shows and hides advanced filters', async () => {
    render(<SessionManager onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Session Management')).toBeInTheDocument();
    });

    const filterButton = screen.getByTitle('Toggle filters');
    fireEvent.click(filterButton);

    expect(screen.getByText('Advanced Filters & Sorting')).toBeInTheDocument();
    expect(screen.getByLabelText('User ID')).toBeInTheDocument();
  });

  it('handles session termination with confirmation', async () => {
    render(<SessionManager onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Session Management')).toBeInTheDocument();
    });

    // Click terminate button for first session
    const terminateButtons = screen.getAllByText('Terminate');
    fireEvent.click(terminateButtons[0]);

    // Confirmation dialog should appear
    expect(screen.getByText('Confirm Session Termination')).toBeInTheDocument();
    expect(screen.getByText(/Are you sure you want to terminate this session/)).toBeInTheDocument();

    // Confirm termination
    const confirmButton = screen.getByText('Terminate Session');
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockOnSecurityAction).toHaveBeenCalledWith({
        type: 'terminate_session',
        payload: { sessionId: 'session_1' }
      });
    });
  });

  it('handles bulk session selection and termination', async () => {
    render(<SessionManager onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Session Management')).toBeInTheDocument();
    });

    // Select all sessions
    const selectAllCheckbox = screen.getAllByRole('checkbox')[0];
    fireEvent.click(selectAllCheckbox);

    // Bulk actions should appear
    expect(screen.getByText('2 sessions selected')).toBeInTheDocument();
    expect(screen.getByText('Terminate Selected')).toBeInTheDocument();

    // Click terminate selected
    fireEvent.click(screen.getByText('Terminate Selected'));

    // Confirmation dialog should appear
    expect(screen.getByText('Confirm Session Termination')).toBeInTheDocument();
    expect(screen.getByText(/Are you sure you want to terminate 2 sessions/)).toBeInTheDocument();

    // Confirm termination
    const confirmButton = screen.getByText('Terminate Sessions');
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockOnSecurityAction).toHaveBeenCalledTimes(2);
    });
  });

  it('exports session data as CSV', async () => {
    // Mock URL.createObjectURL and related methods
    const mockCreateObjectURL = vi.fn(() => 'mock-url');
    const mockRevokeObjectURL = vi.fn();
    const mockClick = vi.fn();
    const mockAppendChild = vi.fn();
    const mockRemoveChild = vi.fn();

    Object.defineProperty(window, 'URL', {
      value: {
        createObjectURL: mockCreateObjectURL,
        revokeObjectURL: mockRevokeObjectURL
      }
    });

    Object.defineProperty(document, 'createElement', {
      value: vi.fn(() => ({
        href: '',
        download: '',
        click: mockClick
      }))
    });

    Object.defineProperty(document.body, 'appendChild', { value: mockAppendChild });
    Object.defineProperty(document.body, 'removeChild', { value: mockRemoveChild });

    render(<SessionManager onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Session Management')).toBeInTheDocument();
    });

    const exportButton = screen.getByText('Export CSV');
    fireEvent.click(exportButton);

    expect(mockCreateObjectURL).toHaveBeenCalled();
    expect(mockClick).toHaveBeenCalled();
  });

  it('toggles auto-refresh functionality', async () => {
    render(<SessionManager onSecurityAction={mockOnSecurityAction} />);
    
    await waitFor(() => {
      expect(screen.getByText('Session Management')).toBeInTheDocument();
    });

    const autoRefreshCheckbox = screen.getByLabelText('Auto-refresh');
    expect(autoRefreshCheckbox).toBeChecked();

    fireEvent.click(autoRefreshCheckbox);
    expect(autoRefreshCheckbox).not.toBeChecked();
  });
});