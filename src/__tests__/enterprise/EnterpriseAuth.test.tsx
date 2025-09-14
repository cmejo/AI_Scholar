/**
 * Enterprise Authentication Tests
 * Tests for task 4.2: User authentication flow with error handling
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EnterpriseAuthProvider } from '../../contexts/EnterpriseAuthContext';
import { useEnterpriseAuth } from '../../hooks/useEnterpriseAuth';
import UserManagement from '../../components/enterprise/UserManagement';
import EnterpriseAuthGuard from '../../components/enterprise/EnterpriseAuthGuard';
import { enterpriseAuthService } from '../../services/enterpriseAuthService';

import { vi } from 'vitest';

// Mock the enterprise auth service
vi.mock('../../services/enterpriseAuthService', () => ({
  enterpriseAuthService: {
    getCurrentUser: vi.fn(),
    getCurrentSession: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    hasPermission: vi.fn(),
    canAccessFeature: vi.fn(),
    subscribe: vi.fn(() => () => {}),
    destroy: vi.fn()
  }
}));

// Mock the base auth service
vi.mock('../../services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn()
  }
}));

const mockEnterpriseAuthService = enterpriseAuthService as any;

// Test component that uses the auth hook
const TestComponent: React.FC = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    hasPermission,
    canAccessFeature
  } = useEnterpriseAuth();

  return (
    <div>
      <div data-testid="auth-status">
        {isLoading ? 'Loading' : isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
      </div>
      {user && <div data-testid="user-name">{user.name}</div>}
      {error && <div data-testid="auth-error">{error}</div>}
      
      <button
        data-testid="login-btn"
        onClick={() => login({ email: 'test@example.com', password: 'password' })}
      >
        Login
      </button>
      
      <button data-testid="logout-btn" onClick={logout}>
        Logout
      </button>
      
      <div data-testid="analytics-permission">
        {hasPermission('analytics', 'view') ? 'Can View Analytics' : 'Cannot View Analytics'}
      </div>
      
      <div data-testid="security-feature">
        {canAccessFeature('security') ? 'Can Access Security' : 'Cannot Access Security'}
      </div>
    </div>
  );
};

// Wrapper component with auth provider
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <EnterpriseAuthProvider>
    {children}
  </EnterpriseAuthProvider>
);

describe('Enterprise Authentication System', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock implementations
    mockEnterpriseAuthService.getCurrentUser.mockResolvedValue(null);
    mockEnterpriseAuthService.getCurrentSession.mockReturnValue(null);
    mockEnterpriseAuthService.hasPermission.mockReturnValue(false);
    mockEnterpriseAuthService.canAccessFeature.mockReturnValue(false);
  });

  describe('Authentication Context', () => {
    it('should initialize with unauthenticated state', async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
      });
    });

    it('should handle successful login', async () => {
      const mockUser = {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'user' as const,
        enterprisePermissions: {
          analytics: { view: true, export: false, admin: false },
          security: { view: false, manage_sessions: false, view_audit_logs: false, manage_threats: false },
          workflows: { view: true, create: false, edit: false, delete: false, execute: true },
          integrations: { view: false, configure: false, manage_keys: false, sync_data: false },
          performance: { view: false, configure: false, admin: false },
          admin: { user_management: false, system_settings: false, enterprise_config: false }
        },
        sessionTimeout: 30,
        lastActivity: new Date(),
        securityLevel: 'standard' as const,
        mfaEnabled: false,
        loginAttempts: 0,
        accountLocked: false
      };

      const mockSession = {
        id: 'session-1',
        userId: '1',
        startTime: new Date(),
        lastActivity: new Date(),
        expiresAt: new Date(Date.now() + 30 * 60 * 1000),
        ipAddress: '127.0.0.1',
        userAgent: 'Test Agent',
        isActive: true,
        securityLevel: 'standard'
      };

      mockEnterpriseAuthService.login.mockResolvedValue({
        user: mockUser,
        session: mockSession
      });

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const loginBtn = screen.getByTestId('login-btn');
      
      await act(async () => {
        fireEvent.click(loginBtn);
      });

      await waitFor(() => {
        expect(mockEnterpriseAuthService.login).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password'
        });
      });
    });

    it('should handle login error', async () => {
      const loginError = new Error('Invalid credentials');
      mockEnterpriseAuthService.login.mockRejectedValue(loginError);

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const loginBtn = screen.getByTestId('login-btn');
      
      await act(async () => {
        fireEvent.click(loginBtn);
      });

      await waitFor(() => {
        expect(screen.getByTestId('auth-error')).toHaveTextContent('Invalid credentials');
      });
    });

    it('should handle logout', async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const logoutBtn = screen.getByTestId('logout-btn');
      
      await act(async () => {
        fireEvent.click(logoutBtn);
      });

      expect(mockEnterpriseAuthService.logout).toHaveBeenCalled();
    });
  });

  describe('Permission System', () => {
    it('should check permissions correctly', async () => {
      mockEnterpriseAuthService.hasPermission.mockReturnValue(true);
      mockEnterpriseAuthService.canAccessFeature.mockReturnValue(true);

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId('analytics-permission')).toHaveTextContent('Can View Analytics');
        expect(screen.getByTestId('security-feature')).toHaveTextContent('Can Access Security');
      });
    });

    it('should deny permissions correctly', async () => {
      mockEnterpriseAuthService.hasPermission.mockReturnValue(false);
      mockEnterpriseAuthService.canAccessFeature.mockReturnValue(false);

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId('analytics-permission')).toHaveTextContent('Cannot View Analytics');
        expect(screen.getByTestId('security-feature')).toHaveTextContent('Cannot Access Security');
      });
    });
  });

  describe('EnterpriseAuthGuard', () => {
    const ProtectedComponent = () => <div data-testid="protected-content">Protected Content</div>;

    it('should show loading state', () => {
      render(
        <TestWrapper>
          <EnterpriseAuthGuard requiredFeature="analytics">
            <ProtectedComponent />
          </EnterpriseAuthGuard>
        </TestWrapper>
      );

      expect(screen.getByText('Checking permissions...')).toBeInTheDocument();
    });

    it('should show login prompt when not authenticated', async () => {
      mockEnterpriseAuthService.getCurrentUser.mockResolvedValue(null);

      render(
        <TestWrapper>
          <EnterpriseAuthGuard requiredFeature="analytics">
            <ProtectedComponent />
          </EnterpriseAuthGuard>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Authentication Required')).toBeInTheDocument();
      });
    });

    it('should show unauthorized message when user lacks permissions', async () => {
      const mockUser = {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'user' as const,
        enterprisePermissions: {
          analytics: { view: false, export: false, admin: false },
          security: { view: false, manage_sessions: false, view_audit_logs: false, manage_threats: false },
          workflows: { view: false, create: false, edit: false, delete: false, execute: false },
          integrations: { view: false, configure: false, manage_keys: false, sync_data: false },
          performance: { view: false, configure: false, admin: false },
          admin: { user_management: false, system_settings: false, enterprise_config: false }
        },
        sessionTimeout: 30,
        lastActivity: new Date(),
        securityLevel: 'standard' as const,
        mfaEnabled: false,
        loginAttempts: 0,
        accountLocked: false
      };

      mockEnterpriseAuthService.getCurrentUser.mockResolvedValue(mockUser);
      mockEnterpriseAuthService.canAccessFeature.mockReturnValue(false);

      render(
        <TestWrapper>
          <EnterpriseAuthGuard requiredFeature="analytics">
            <ProtectedComponent />
          </EnterpriseAuthGuard>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Access Restricted')).toBeInTheDocument();
      });
    });

    it('should render protected content when user has permissions', async () => {
      const mockUser = {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'admin' as const,
        enterprisePermissions: {
          analytics: { view: true, export: true, admin: true },
          security: { view: true, manage_sessions: true, view_audit_logs: true, manage_threats: true },
          workflows: { view: true, create: true, edit: true, delete: true, execute: true },
          integrations: { view: true, configure: true, manage_keys: true, sync_data: true },
          performance: { view: true, configure: true, admin: true },
          admin: { user_management: true, system_settings: true, enterprise_config: true }
        },
        sessionTimeout: 60,
        lastActivity: new Date(),
        securityLevel: 'admin' as const,
        mfaEnabled: true,
        loginAttempts: 0,
        accountLocked: false
      };

      mockEnterpriseAuthService.getCurrentUser.mockResolvedValue(mockUser);
      mockEnterpriseAuthService.canAccessFeature.mockReturnValue(true);

      render(
        <TestWrapper>
          <EnterpriseAuthGuard requiredFeature="analytics">
            <ProtectedComponent />
          </EnterpriseAuthGuard>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      });
    });
  });

  describe('UserManagement Component', () => {
    it('should render login form when not authenticated', async () => {
      render(
        <TestWrapper>
          <UserManagement showLoginForm={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Enterprise Login')).toBeInTheDocument();
        expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
        expect(screen.getByLabelText('Password')).toBeInTheDocument();
      });
    });

    it('should handle login form submission', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <UserManagement showLoginForm={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
      });

      const emailInput = screen.getByLabelText('Email Address');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      expect(mockEnterpriseAuthService.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        rememberMe: false
      });
    });

    it('should show user profile when authenticated', async () => {
      const mockUser = {
        id: '1',
        name: 'John Doe',
        email: 'john@example.com',
        role: 'researcher' as const,
        enterprisePermissions: {
          analytics: { view: true, export: true, admin: false },
          security: { view: true, manage_sessions: false, view_audit_logs: false, manage_threats: false },
          workflows: { view: true, create: true, edit: true, delete: false, execute: true },
          integrations: { view: true, configure: false, manage_keys: false, sync_data: true },
          performance: { view: true, configure: false, admin: false },
          admin: { user_management: false, system_settings: false, enterprise_config: false }
        },
        sessionTimeout: 45,
        lastActivity: new Date(),
        securityLevel: 'elevated' as const,
        mfaEnabled: false,
        loginAttempts: 0,
        accountLocked: false
      };

      mockEnterpriseAuthService.getCurrentUser.mockResolvedValue(mockUser);

      render(
        <TestWrapper>
          <UserManagement />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('User Profile')).toBeInTheDocument();
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('john@example.com')).toBeInTheDocument();
      });
    });
  });
});