/**
 * Enterprise Authentication Context
 * Implements task 4.2: User authentication flow with error handling
 * 
 * Features:
 * - Global authentication state management
 * - Automatic token refresh
 * - Session persistence
 * - Error handling and recovery
 * - Permission-based routing
 */

import React, { createContext, useContext, useEffect, useReducer, useCallback } from 'react';
import { 
  EnterpriseUser, 
  SessionInfo, 
  enterpriseAuthService 
} from '../services/enterpriseAuthService';
import { AuthState, LoginCredentials } from '../types/auth';

// Auth Context State
interface EnterpriseAuthContextState extends AuthState {
  user: EnterpriseUser | null;
  session: SessionInfo | null;
  sessionTimeRemaining: number;
  isInitialized: boolean;
}

// Auth Context Actions
type AuthAction =
  | { type: 'INIT_START' }
  | { type: 'INIT_SUCCESS'; payload: { user: EnterpriseUser | null; session: SessionInfo | null } }
  | { type: 'INIT_ERROR'; payload: string }
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: EnterpriseUser; session: SessionInfo } }
  | { type: 'LOGIN_ERROR'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'REFRESH_USER_START' }
  | { type: 'REFRESH_USER_SUCCESS'; payload: EnterpriseUser }
  | { type: 'REFRESH_USER_ERROR'; payload: string }
  | { type: 'UPDATE_SESSION_TIME'; payload: number }
  | { type: 'CLEAR_ERROR' };

// Auth Context Value
interface EnterpriseAuthContextValue extends EnterpriseAuthContextState {
  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  clearError: () => void;
  
  // Permission helpers
  hasPermission: (category: string, permission: string) => boolean;
  canAccessFeature: (feature: string) => boolean;
  
  // Utility functions
  isTokenExpired: () => boolean;
  getTimeUntilExpiry: () => number;
}

// Initial state
const initialState: EnterpriseAuthContextState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  session: null,
  sessionTimeRemaining: 0,
  isInitialized: false
};

// Auth reducer
const authReducer = (state: EnterpriseAuthContextState, action: AuthAction): EnterpriseAuthContextState => {
  switch (action.type) {
    case 'INIT_START':
      return {
        ...state,
        isLoading: true,
        error: null
      };

    case 'INIT_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        session: action.payload.session,
        isAuthenticated: !!action.payload.user,
        isLoading: false,
        error: null,
        isInitialized: true
      };

    case 'INIT_ERROR':
      return {
        ...state,
        user: null,
        session: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
        isInitialized: true
      };

    case 'LOGIN_START':
      return {
        ...state,
        isLoading: true,
        error: null
      };

    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        session: action.payload.session,
        isAuthenticated: true,
        isLoading: false,
        error: null
      };

    case 'LOGIN_ERROR':
      return {
        ...state,
        user: null,
        session: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload
      };

    case 'LOGOUT':
      return {
        ...state,
        user: null,
        session: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        sessionTimeRemaining: 0
      };

    case 'REFRESH_USER_START':
      return {
        ...state,
        isLoading: true,
        error: null
      };

    case 'REFRESH_USER_SUCCESS':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
        error: null
      };

    case 'REFRESH_USER_ERROR':
      return {
        ...state,
        isLoading: false,
        error: action.payload
      };

    case 'UPDATE_SESSION_TIME':
      return {
        ...state,
        sessionTimeRemaining: action.payload
      };

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null
      };

    default:
      return state;
  }
};

// Create context
const EnterpriseAuthContext = createContext<EnterpriseAuthContextValue | null>(null);

// Auth Provider Props
interface EnterpriseAuthProviderProps {
  children: React.ReactNode;
  autoRefresh?: boolean;
  sessionWarningThreshold?: number; // minutes before expiry to show warning
}

// Auth Provider Component
export const EnterpriseAuthProvider: React.FC<EnterpriseAuthProviderProps> = ({
  children,
  autoRefresh = true,
  sessionWarningThreshold = 5
}) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize authentication state
  const initializeAuth = useCallback(async () => {
    dispatch({ type: 'INIT_START' });

    try {
      const user = await enterpriseAuthService.getCurrentUser();
      const session = enterpriseAuthService.getCurrentSession();

      dispatch({ 
        type: 'INIT_SUCCESS', 
        payload: { user, session } 
      });
    } catch (error) {
      dispatch({ 
        type: 'INIT_ERROR', 
        payload: error instanceof Error ? error.message : 'Initialization failed' 
      });
    }
  }, []);

  // Login function
  const login = useCallback(async (credentials: LoginCredentials) => {
    dispatch({ type: 'LOGIN_START' });

    try {
      const { user, session } = await enterpriseAuthService.login(credentials);
      
      dispatch({ 
        type: 'LOGIN_SUCCESS', 
        payload: { user, session } 
      });
    } catch (error) {
      dispatch({ 
        type: 'LOGIN_ERROR', 
        payload: error instanceof Error ? error.message : 'Login failed' 
      });
      throw error;
    }
  }, []);

  // Logout function
  const logout = useCallback(() => {
    enterpriseAuthService.logout();
    dispatch({ type: 'LOGOUT' });
  }, []);

  // Refresh user function
  const refreshUser = useCallback(async () => {
    dispatch({ type: 'REFRESH_USER_START' });

    try {
      const user = await enterpriseAuthService.getCurrentUser();
      
      if (user) {
        dispatch({ 
          type: 'REFRESH_USER_SUCCESS', 
          payload: user 
        });
      } else {
        throw new Error('User not found');
      }
    } catch (error) {
      dispatch({ 
        type: 'REFRESH_USER_ERROR', 
        payload: error instanceof Error ? error.message : 'Refresh failed' 
      });
      throw error;
    }
  }, []);

  // Clear error function
  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  // Permission helpers
  const hasPermission = useCallback((category: string, permission: string): boolean => {
    return enterpriseAuthService.hasPermission(state.user, category as any, permission);
  }, [state.user]);

  const canAccessFeature = useCallback((feature: string): boolean => {
    return enterpriseAuthService.canAccessFeature(state.user, feature as any);
  }, [state.user]);

  // Utility functions
  const isTokenExpired = useCallback((): boolean => {
    if (!state.session) return true;
    return new Date() >= new Date(state.session.expiresAt);
  }, [state.session]);

  const getTimeUntilExpiry = useCallback((): number => {
    if (!state.session) return 0;
    const now = new Date();
    const expiresAt = new Date(state.session.expiresAt);
    return Math.max(0, Math.floor((expiresAt.getTime() - now.getTime()) / (1000 * 60)));
  }, [state.session]);

  // Update session time remaining
  useEffect(() => {
    if (!state.session) return;

    const updateSessionTime = () => {
      const timeRemaining = getTimeUntilExpiry();
      dispatch({ type: 'UPDATE_SESSION_TIME', payload: timeRemaining });

      // Auto-logout if session expired
      if (timeRemaining <= 0) {
        logout();
      }
    };

    // Update immediately
    updateSessionTime();

    // Update every minute
    const interval = setInterval(updateSessionTime, 60000);

    return () => clearInterval(interval);
  }, [state.session, getTimeUntilExpiry, logout]);

  // Auto-refresh token
  useEffect(() => {
    if (!autoRefresh || !state.isAuthenticated) return;

    const refreshInterval = setInterval(async () => {
      try {
        const timeUntilExpiry = getTimeUntilExpiry();
        
        // Refresh token if less than 10 minutes remaining
        if (timeUntilExpiry <= 10 && timeUntilExpiry > 0) {
          await refreshUser();
        }
      } catch (error) {
        console.error('Auto-refresh failed:', error);
      }
    }, 5 * 60 * 1000); // Check every 5 minutes

    return () => clearInterval(refreshInterval);
  }, [autoRefresh, state.isAuthenticated, getTimeUntilExpiry, refreshUser]);

  // Subscribe to auth service events
  useEffect(() => {
    const unsubscribe = enterpriseAuthService.subscribe((authState) => {
      // Handle auth state changes from the service
      if (!authState.isAuthenticated && state.isAuthenticated) {
        dispatch({ type: 'LOGOUT' });
      }
    });

    return unsubscribe;
  }, [state.isAuthenticated]);

  // Initialize on mount
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  // Session warning effect
  useEffect(() => {
    if (state.sessionTimeRemaining <= sessionWarningThreshold && state.sessionTimeRemaining > 0) {
      // Could dispatch a custom event or show a notification
      const event = new CustomEvent('sessionWarning', {
        detail: { timeRemaining: state.sessionTimeRemaining }
      });
      window.dispatchEvent(event);
    }
  }, [state.sessionTimeRemaining, sessionWarningThreshold]);

  // Context value
  const contextValue: EnterpriseAuthContextValue = {
    ...state,
    login,
    logout,
    refreshUser,
    clearError,
    hasPermission,
    canAccessFeature,
    isTokenExpired,
    getTimeUntilExpiry
  };

  return (
    <EnterpriseAuthContext.Provider value={contextValue}>
      {children}
    </EnterpriseAuthContext.Provider>
  );
};

// Hook to use auth context
export const useEnterpriseAuthContext = (): EnterpriseAuthContextValue => {
  const context = useContext(EnterpriseAuthContext);
  
  if (!context) {
    throw new Error('useEnterpriseAuthContext must be used within an EnterpriseAuthProvider');
  }
  
  return context;
};

// HOC for components that need authentication
export function withEnterpriseAuthContext<P extends object>(
  Component: React.ComponentType<P>
) {
  return function AuthenticatedComponent(props: P) {
    return (
      <EnterpriseAuthProvider>
        <Component {...props} />
      </EnterpriseAuthProvider>
    );
  };
}

export default EnterpriseAuthContext;