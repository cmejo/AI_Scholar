/**
 * Enterprise Authentication Hook
 * Implements task 4.1: Integrate authentication service with enterprise features
 * Implements task 4.2: User authentication flow with error handling
 * 
 * Features:
 * - Role-based access control
 * - Session management
 * - Permission checking
 * - Real-time auth state updates
 * - Context-based state management
 */

import { useMemo } from 'react';
import { 
  EnterpriseUser, 
  EnterprisePermissions
} from '../services/enterpriseAuthService';
import { LoginCredentials } from '../types/auth';
import { useEnterpriseAuthContext } from '../contexts/EnterpriseAuthContext';

export interface UseEnterpriseAuthReturn {
  // Auth state
  user: EnterpriseUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  isInitialized: boolean;
  
  // Session info
  session: any;
  sessionTimeRemaining: number; // in minutes
  
  // Auth actions
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  clearError: () => void;
  
  // Permission helpers
  hasPermission: (category: keyof EnterprisePermissions, permission: string) => boolean;
  canAccessFeature: (feature: 'analytics' | 'security' | 'workflows' | 'integrations' | 'performance') => boolean;
  canPerformAction: (category: keyof EnterprisePermissions, action: string) => boolean;
  
  // Feature access helpers
  canViewAnalytics: boolean;
  canExportAnalytics: boolean;
  canManageSecurity: boolean;
  canCreateWorkflows: boolean;
  canConfigureIntegrations: boolean;
  canViewPerformance: boolean;
  canAdministerSystem: boolean;
  
  // Utility functions
  isTokenExpired: () => boolean;
  getTimeUntilExpiry: () => number;
}

export const useEnterpriseAuth = (): UseEnterpriseAuthReturn => {
  // Get auth state from context
  const authContext = useEnterpriseAuthContext();

  // Permission helpers that work with the context
  const hasPermission = (category: keyof EnterprisePermissions, permission: string): boolean => {
    return authContext.hasPermission(category, permission);
  };

  const canAccessFeature = (feature: 'analytics' | 'security' | 'workflows' | 'integrations' | 'performance'): boolean => {
    return authContext.canAccessFeature(feature);
  };

  const canPerformAction = (category: keyof EnterprisePermissions, action: string): boolean => {
    return hasPermission(category, action);
  };

  // Memoized feature access flags
  const featureAccess = useMemo(() => {
    return {
      canViewAnalytics: canAccessFeature('analytics'),
      canExportAnalytics: hasPermission('analytics', 'export'),
      canManageSecurity: hasPermission('security', 'manage_sessions') || hasPermission('security', 'manage_threats'),
      canCreateWorkflows: hasPermission('workflows', 'create'),
      canConfigureIntegrations: hasPermission('integrations', 'configure'),
      canViewPerformance: canAccessFeature('performance'),
      canAdministerSystem: hasPermission('admin', 'system_settings') || hasPermission('admin', 'user_management')
    };
  }, [authContext.user]);

  return {
    // Auth state from context
    user: authContext.user,
    isAuthenticated: authContext.isAuthenticated,
    isLoading: authContext.isLoading,
    error: authContext.error,
    isInitialized: authContext.isInitialized,
    
    // Session info
    session: authContext.session,
    sessionTimeRemaining: authContext.sessionTimeRemaining,
    
    // Auth actions
    login: authContext.login,
    logout: authContext.logout,
    refreshUser: authContext.refreshUser,
    clearError: authContext.clearError,
    
    // Permission helpers
    hasPermission,
    canAccessFeature,
    canPerformAction,
    
    // Feature access helpers
    ...featureAccess,
    
    // Utility functions
    isTokenExpired: authContext.isTokenExpired,
    getTimeUntilExpiry: authContext.getTimeUntilExpiry
  };
};