/**
 * Enterprise Authentication Service
 * Implements task 4.1: Integrate authentication service with enterprise features
 * 
 * Features:
 * - Role-based access control for enterprise features
 * - Session management and timeout handling
 * - Permission-based feature visibility
 * - Enhanced security monitoring
 */

import { User, AuthResponse, LoginCredentials, AuthState } from '../types/auth';
import { authService } from './authService';

export interface EnterprisePermissions {
  analytics: {
    view: boolean;
    export: boolean;
    admin: boolean;
  };
  security: {
    view: boolean;
    manage_sessions: boolean;
    view_audit_logs: boolean;
    manage_threats: boolean;
  };
  workflows: {
    view: boolean;
    create: boolean;
    edit: boolean;
    delete: boolean;
    execute: boolean;
  };
  integrations: {
    view: boolean;
    configure: boolean;
    manage_keys: boolean;
    sync_data: boolean;
  };
  performance: {
    view: boolean;
    configure: boolean;
    admin: boolean;
  };
  admin: {
    user_management: boolean;
    system_settings: boolean;
    enterprise_config: boolean;
  };
}

export interface EnterpriseUser extends User {
  enterprisePermissions: EnterprisePermissions;
  sessionTimeout: number; // in minutes
  lastActivity: Date;
  securityLevel: 'standard' | 'elevated' | 'admin';
  mfaEnabled: boolean;
  loginAttempts: number;
  accountLocked: boolean;
}

export interface SessionInfo {
  id: string;
  userId: string;
  startTime: Date;
  lastActivity: Date;
  expiresAt: Date;
  ipAddress: string;
  userAgent: string;
  isActive: boolean;
  securityLevel: string;
}

class EnterpriseAuthService {
  private sessionCheckInterval: NodeJS.Timeout | null = null;
  private sessionTimeout: number = 30; // Default 30 minutes
  private authStateListeners: ((state: AuthState) => void)[] = [];
  private currentSession: SessionInfo | null = null;

  constructor() {
    this.initializeSessionMonitoring();
  }

  /**
   * Initialize session monitoring and timeout handling
   */
  private initializeSessionMonitoring(): void {
    // Check session every minute
    this.sessionCheckInterval = setInterval(() => {
      this.checkSessionTimeout();
    }, 60000);

    // Listen for user activity to update last activity time
    this.setupActivityListeners();
  }

  /**
   * Setup activity listeners to track user interaction
   */
  private setupActivityListeners(): void {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    
    const updateActivity = () => {
      this.updateLastActivity();
    };

    events.forEach(event => {
      document.addEventListener(event, updateActivity, { passive: true });
    });
  }

  /**
   * Update last activity timestamp
   */
  private updateLastActivity(): void {
    if (this.currentSession) {
      this.currentSession.lastActivity = new Date();
      localStorage.setItem('lastActivity', this.currentSession.lastActivity.toISOString());
    }
  }

  /**
   * Check if session has timed out
   */
  private checkSessionTimeout(): void {
    const lastActivity = localStorage.getItem('lastActivity');
    if (!lastActivity) return;

    const lastActivityTime = new Date(lastActivity);
    const now = new Date();
    const timeDiff = (now.getTime() - lastActivityTime.getTime()) / (1000 * 60); // minutes

    if (timeDiff > this.sessionTimeout) {
      this.handleSessionTimeout();
    }
  }

  /**
   * Handle session timeout
   */
  private handleSessionTimeout(): void {
    console.warn('Session timed out due to inactivity');
    this.logout(true); // Force logout with timeout flag
  }

  /**
   * Get current user with enterprise permissions
   */
  async getCurrentUser(): Promise<EnterpriseUser | null> {
    try {
      const user = await authService.getCurrentUser();
      if (!user) return null;

      // Enhance user with enterprise permissions
      const enterpriseUser = await this.enhanceUserWithPermissions(user);
      return enterpriseUser;
    } catch (error) {
      console.error('Error getting current enterprise user:', error);
      return null;
    }
  }

  /**
   * Enhance user with enterprise permissions based on role
   */
  private async enhanceUserWithPermissions(user: User): Promise<EnterpriseUser> {
    const basePermissions = this.getBasePermissions(user.role || 'user');
    
    try {
      // Fetch additional permissions from backend if available
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/auth/permissions`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        }
      });

      let enterprisePermissions = basePermissions;
      if (response.ok) {
        const serverPermissions = await response.json();
        enterprisePermissions = { ...basePermissions, ...serverPermissions };
      }

      return {
        ...user,
        enterprisePermissions,
        sessionTimeout: this.getSessionTimeout(user.role || 'user'),
        lastActivity: new Date(),
        securityLevel: this.getSecurityLevel(user.role || 'user'),
        mfaEnabled: user.permissions?.includes('mfa_enabled') || false,
        loginAttempts: 0,
        accountLocked: false
      };
    } catch (error) {
      console.warn('Could not fetch server permissions, using base permissions:', error);
      return {
        ...user,
        enterprisePermissions: basePermissions,
        sessionTimeout: this.getSessionTimeout(user.role || 'user'),
        lastActivity: new Date(),
        securityLevel: this.getSecurityLevel(user.role || 'user'),
        mfaEnabled: false,
        loginAttempts: 0,
        accountLocked: false
      };
    }
  }

  /**
   * Get base permissions based on user role
   */
  private getBasePermissions(role: string): EnterprisePermissions {
    const permissions: Record<string, EnterprisePermissions> = {
      admin: {
        analytics: { view: true, export: true, admin: true },
        security: { view: true, manage_sessions: true, view_audit_logs: true, manage_threats: true },
        workflows: { view: true, create: true, edit: true, delete: true, execute: true },
        integrations: { view: true, configure: true, manage_keys: true, sync_data: true },
        performance: { view: true, configure: true, admin: true },
        admin: { user_management: true, system_settings: true, enterprise_config: true }
      },
      researcher: {
        analytics: { view: true, export: true, admin: false },
        security: { view: true, manage_sessions: false, view_audit_logs: false, manage_threats: false },
        workflows: { view: true, create: true, edit: true, delete: false, execute: true },
        integrations: { view: true, configure: false, manage_keys: false, sync_data: true },
        performance: { view: true, configure: false, admin: false },
        admin: { user_management: false, system_settings: false, enterprise_config: false }
      },
      user: {
        analytics: { view: true, export: false, admin: false },
        security: { view: false, manage_sessions: false, view_audit_logs: false, manage_threats: false },
        workflows: { view: true, create: false, edit: false, delete: false, execute: true },
        integrations: { view: false, configure: false, manage_keys: false, sync_data: false },
        performance: { view: false, configure: false, admin: false },
        admin: { user_management: false, system_settings: false, enterprise_config: false }
      },
      student: {
        analytics: { view: false, export: false, admin: false },
        security: { view: false, manage_sessions: false, view_audit_logs: false, manage_threats: false },
        workflows: { view: false, create: false, edit: false, delete: false, execute: false },
        integrations: { view: false, configure: false, manage_keys: false, sync_data: false },
        performance: { view: false, configure: false, admin: false },
        admin: { user_management: false, system_settings: false, enterprise_config: false }
      }
    };

    return permissions[role] || permissions.user;
  }

  /**
   * Get session timeout based on user role
   */
  private getSessionTimeout(role: string): number {
    const timeouts: Record<string, number> = {
      admin: 60,      // 1 hour
      researcher: 45, // 45 minutes
      user: 30,       // 30 minutes
      student: 20     // 20 minutes
    };

    return timeouts[role] || 30;
  }

  /**
   * Get security level based on user role
   */
  private getSecurityLevel(role: string): 'standard' | 'elevated' | 'admin' {
    const levels: Record<string, 'standard' | 'elevated' | 'admin'> = {
      admin: 'admin',
      researcher: 'elevated',
      user: 'standard',
      student: 'standard'
    };

    return levels[role] || 'standard';
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(user: EnterpriseUser | null, category: keyof EnterprisePermissions, permission: string): boolean {
    if (!user || !user.enterprisePermissions) return false;
    
    const categoryPermissions = user.enterprisePermissions[category] as Record<string, boolean>;
    return categoryPermissions[permission] || false;
  }

  /**
   * Check if user can access enterprise feature
   */
  canAccessFeature(user: EnterpriseUser | null, feature: 'analytics' | 'security' | 'workflows' | 'integrations' | 'performance'): boolean {
    if (!user) return false;
    
    switch (feature) {
      case 'analytics':
        return this.hasPermission(user, 'analytics', 'view');
      case 'security':
        return this.hasPermission(user, 'security', 'view');
      case 'workflows':
        return this.hasPermission(user, 'workflows', 'view');
      case 'integrations':
        return this.hasPermission(user, 'integrations', 'view');
      case 'performance':
        return this.hasPermission(user, 'performance', 'view');
      default:
        return false;
    }
  }

  /**
   * Enhanced login with enterprise features
   */
  async login(credentials: LoginCredentials): Promise<{ user: EnterpriseUser; session: SessionInfo }> {
    try {
      // Use base auth service for authentication
      const authResponse = await authService.login(credentials);
      
      // Enhance user with enterprise permissions
      const enterpriseUser = await this.enhanceUserWithPermissions(authResponse.user);
      
      // Create session info
      const session: SessionInfo = {
        id: this.generateSessionId(),
        userId: enterpriseUser.id,
        startTime: new Date(),
        lastActivity: new Date(),
        expiresAt: new Date(Date.now() + enterpriseUser.sessionTimeout * 60 * 1000),
        ipAddress: await this.getClientIP(),
        userAgent: navigator.userAgent,
        isActive: true,
        securityLevel: enterpriseUser.securityLevel
      };

      this.currentSession = session;
      this.sessionTimeout = enterpriseUser.sessionTimeout;
      
      // Store session info
      localStorage.setItem('enterpriseSession', JSON.stringify(session));
      localStorage.setItem('lastActivity', new Date().toISOString());

      // Notify listeners
      this.notifyAuthStateChange({
        user: enterpriseUser,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        token: authResponse.token,
        refreshToken: authResponse.refreshToken
      });

      return { user: enterpriseUser, session };
    } catch (error) {
      console.error('Enterprise login failed:', error);
      throw error;
    }
  }

  /**
   * Enhanced logout with session cleanup
   */
  logout(isTimeout: boolean = false): void {
    try {
      // Clear session data
      localStorage.removeItem('enterpriseSession');
      localStorage.removeItem('lastActivity');
      
      // Clear current session
      this.currentSession = null;
      
      // Use base auth service logout
      authService.logout();
      
      // Notify listeners
      this.notifyAuthStateChange({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: isTimeout ? 'Session timed out due to inactivity' : null
      });

      // Log security event
      this.logSecurityEvent('logout', { 
        reason: isTimeout ? 'timeout' : 'manual',
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  /**
   * Get current session info
   */
  getCurrentSession(): SessionInfo | null {
    if (this.currentSession) {
      return this.currentSession;
    }

    // Try to restore from localStorage
    const storedSession = localStorage.getItem('enterpriseSession');
    if (storedSession) {
      try {
        this.currentSession = JSON.parse(storedSession);
        return this.currentSession;
      } catch (error) {
        console.error('Error parsing stored session:', error);
        localStorage.removeItem('enterpriseSession');
      }
    }

    return null;
  }

  /**
   * Subscribe to auth state changes
   */
  subscribe(listener: (state: AuthState) => void): () => void {
    this.authStateListeners.push(listener);
    
    return () => {
      const index = this.authStateListeners.indexOf(listener);
      if (index > -1) {
        this.authStateListeners.splice(index, 1);
      }
    };
  }

  /**
   * Notify auth state change listeners
   */
  private notifyAuthStateChange(state: AuthState): void {
    this.authStateListeners.forEach(listener => {
      try {
        listener(state);
      } catch (error) {
        console.error('Error in auth state listener:', error);
      }
    });
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get client IP address (best effort)
   */
  private async getClientIP(): Promise<string> {
    try {
      // This is a simplified implementation
      // In production, you might want to use a service or get this from the server
      return 'unknown';
    } catch (error) {
      return 'unknown';
    }
  }

  /**
   * Log security events
   */
  private logSecurityEvent(event: string, details: Record<string, any>): void {
    try {
      const logEntry = {
        event,
        details,
        timestamp: new Date().toISOString(),
        sessionId: this.currentSession?.id,
        userId: this.currentSession?.userId
      };

      // Store locally for now, could be sent to backend
      const logs = JSON.parse(localStorage.getItem('securityLogs') || '[]');
      logs.push(logEntry);
      
      // Keep only last 100 entries
      if (logs.length > 100) {
        logs.splice(0, logs.length - 100);
      }
      
      localStorage.setItem('securityLogs', JSON.stringify(logs));
    } catch (error) {
      console.error('Error logging security event:', error);
    }
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    if (this.sessionCheckInterval) {
      clearInterval(this.sessionCheckInterval);
      this.sessionCheckInterval = null;
    }
    
    this.authStateListeners = [];
    this.currentSession = null;
  }
}

export const enterpriseAuthService = new EnterpriseAuthService();
export default enterpriseAuthService;