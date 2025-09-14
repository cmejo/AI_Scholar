/**
 * Enterprise Authentication Guard
 * Implements task 4.1: Role-based feature visibility and permissions
 * 
 * Features:
 * - Route protection based on permissions
 * - Feature-level access control
 * - Graceful fallback for unauthorized access
 * - Loading states during auth checks
 */

import React from 'react';
import { Shield, Lock, AlertTriangle, RefreshCw } from 'lucide-react';
import { useEnterpriseAuth } from '../../hooks/useEnterpriseAuth';
import { EnterprisePermissions } from '../../services/enterpriseAuthService';

export interface EnterpriseAuthGuardProps {
  children: React.ReactNode;
  
  // Permission requirements
  requiredFeature?: 'analytics' | 'security' | 'workflows' | 'integrations' | 'performance';
  requiredPermission?: {
    category: keyof EnterprisePermissions;
    action: string;
  };
  requiredRole?: 'admin' | 'researcher' | 'user' | 'student';
  
  // Fallback options
  fallback?: React.ReactNode;
  showLoginPrompt?: boolean;
  redirectToLogin?: boolean;
  
  // Display options
  showLoadingSpinner?: boolean;
  loadingMessage?: string;
  unauthorizedMessage?: string;
}

export const EnterpriseAuthGuard: React.FC<EnterpriseAuthGuardProps> = ({
  children,
  requiredFeature,
  requiredPermission,
  requiredRole,
  fallback,
  showLoginPrompt = true,
  redirectToLogin = false,
  showLoadingSpinner = true,
  loadingMessage = 'Checking permissions...',
  unauthorizedMessage = 'You do not have permission to access this feature.'
}) => {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    canAccessFeature,
    hasPermission,
    login
  } = useEnterpriseAuth();

  // Show loading state
  if (isLoading && showLoadingSpinner) {
    return (
      <div className="flex items-center justify-center min-h-[200px] bg-gray-900 text-white">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-purple-500" />
          <p className="text-gray-300">{loadingMessage}</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[200px] bg-gray-900 text-white">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-red-400" />
          <h3 className="text-lg font-semibold text-red-300 mb-2">Authentication Error</h3>
          <p className="text-gray-400 text-sm mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Check if user is authenticated
  if (!isAuthenticated) {
    if (redirectToLogin) {
      window.location.href = '/login';
      return null;
    }

    if (showLoginPrompt) {
      return (
        <div className="flex items-center justify-center min-h-[400px] bg-gray-900 text-white">
          <div className="text-center max-w-md">
            <Lock className="w-16 h-16 mx-auto mb-6 text-purple-400" />
            <h2 className="text-2xl font-bold text-white mb-4">Authentication Required</h2>
            <p className="text-gray-400 mb-6">
              Please log in to access enterprise features.
            </p>
            <button
              onClick={() => window.location.href = '/login'}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-medium"
            >
              Go to Login
            </button>
          </div>
        </div>
      );
    }

    return fallback || null;
  }

  // Check role requirement
  if (requiredRole && user?.role !== requiredRole) {
    // Allow admin to access all roles
    if (user?.role !== 'admin') {
      return (
        <UnauthorizedAccess 
          message={`This feature requires ${requiredRole} role.`}
          fallback={fallback}
        />
      );
    }
  }

  // Check feature access requirement
  if (requiredFeature && !canAccessFeature(requiredFeature)) {
    return (
      <UnauthorizedAccess 
        message={`You do not have permission to access ${requiredFeature} features.`}
        fallback={fallback}
      />
    );
  }

  // Check specific permission requirement
  if (requiredPermission && !hasPermission(requiredPermission.category, requiredPermission.action)) {
    return (
      <UnauthorizedAccess 
        message={`You do not have permission to ${requiredPermission.action} in ${requiredPermission.category}.`}
        fallback={fallback}
      />
    );
  }

  // All checks passed, render children
  return <>{children}</>;
};

/**
 * Unauthorized Access Component
 */
interface UnauthorizedAccessProps {
  message: string;
  fallback?: React.ReactNode;
}

const UnauthorizedAccess: React.FC<UnauthorizedAccessProps> = ({ message, fallback }) => {
  if (fallback) {
    return <>{fallback}</>;
  }

  return (
    <div className="flex items-center justify-center min-h-[300px] bg-gray-900 text-white">
      <div className="text-center max-w-md">
        <Shield className="w-16 h-16 mx-auto mb-6 text-yellow-400" />
        <h3 className="text-xl font-semibold text-white mb-4">Access Restricted</h3>
        <p className="text-gray-400 mb-6">{message}</p>
        <div className="text-sm text-gray-500">
          Contact your administrator if you believe you should have access to this feature.
        </div>
      </div>
    </div>
  );
};

/**
 * Higher-order component for protecting components with authentication
 */
export function withEnterpriseAuth<P extends object>(
  Component: React.ComponentType<P>,
  guardProps?: Omit<EnterpriseAuthGuardProps, 'children'>
) {
  return function ProtectedComponent(props: P) {
    return (
      <EnterpriseAuthGuard {...guardProps}>
        <Component {...props} />
      </EnterpriseAuthGuard>
    );
  };
}

/**
 * Hook for conditional rendering based on permissions
 */
export const usePermissionGate = () => {
  const { hasPermission, canAccessFeature, user } = useEnterpriseAuth();

  const gate = {
    /**
     * Render children only if user has required permission
     */
    hasPermission: (
      category: keyof EnterprisePermissions,
      action: string,
      children: React.ReactNode,
      fallback?: React.ReactNode
    ) => {
      return hasPermission(category, action) ? children : (fallback || null);
    },

    /**
     * Render children only if user can access feature
     */
    canAccessFeature: (
      feature: 'analytics' | 'security' | 'workflows' | 'integrations' | 'performance',
      children: React.ReactNode,
      fallback?: React.ReactNode
    ) => {
      return canAccessFeature(feature) ? children : (fallback || null);
    },

    /**
     * Render children only if user has required role
     */
    hasRole: (
      role: 'admin' | 'researcher' | 'user' | 'student',
      children: React.ReactNode,
      fallback?: React.ReactNode
    ) => {
      const userRole = user?.role;
      const hasRole = userRole === role || userRole === 'admin'; // Admin can access all roles
      return hasRole ? children : (fallback || null);
    }
  };

  return gate;
};

export default EnterpriseAuthGuard;