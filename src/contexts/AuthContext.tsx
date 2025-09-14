import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { AuthState, User, LoginCredentials, RegisterData, AuthResponse } from '../types/auth';
import { authService } from '../services/authService';
import { AuthStorage, TokenRefreshManager } from '../utils/authStorage';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
  updateProfile: (updates: Partial<User>) => Promise<void>;

}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; token: string; refreshToken: string } }
  | { type: 'AUTH_ERROR'; payload: string }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'UPDATE_USER'; payload: User };

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_START':
      return { ...state, isLoading: true, error: null };
    case 'AUTH_SUCCESS':
      return {
        ...state,
        isLoading: false,
        isAuthenticated: true,
        user: action.payload.user,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken,
        error: null,
      };
    case 'AUTH_ERROR':
      return {
        ...state,
        isLoading: false,
        isAuthenticated: false,
        user: null,
        error: action.payload,
      };
    case 'AUTH_LOGOUT':
      return {
        ...initialState,
      };
    case 'UPDATE_USER':
      return {
        ...state,
        user: action.payload,
      };
    default:
      return state;
  }
}

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check for existing auth on mount
  useEffect(() => {
    const initAuth = async () => {
      const tokens = AuthStorage.getTokens();
      const rememberMe = AuthStorage.getRememberMe();
      
      if (tokens && AuthStorage.hasValidAuth()) {
        try {
          dispatch({ type: 'AUTH_START' });
          const user = await authService.validateToken(tokens.token);
          dispatch({
            type: 'AUTH_SUCCESS',
            payload: { user, token: tokens.token, refreshToken: tokens.refreshToken }
          });
          
          // Set up automatic token refresh
          TokenRefreshManager.setupAutoRefresh(refreshAuth);
          
          console.log('AuthContext: Authentication restored from storage', {
            rememberMe,
            storageType: AuthStorage.getStorageType(),
            isExpired: AuthStorage.isTokenExpired()
          });
        } catch (error) {
          console.log('Token validation failed, clearing storage:', error);
          AuthStorage.clearTokens();
          dispatch({ type: 'AUTH_LOGOUT' });
        }
      } else {
        // Clear any invalid tokens
        AuthStorage.clearTokens();
        dispatch({ type: 'AUTH_LOGOUT' });
      }
    };

    initAuth();

    // Cleanup on unmount
    return () => {
      TokenRefreshManager.clearAutoRefresh();
    };
  }, []);



  const login = async (credentials: LoginCredentials) => {
    try {
      console.log('AuthContext: Starting login process');
      dispatch({ type: 'AUTH_START' });
      
      console.log('AuthContext: Calling authService.login');
      const response = await authService.login(credentials);
      console.log('AuthContext: Login response received:', { 
        hasToken: !!response.token, 
        hasRefreshToken: !!response.refreshToken,
        hasUser: !!response.user,
        rememberMe: credentials.rememberMe
      });
      
      // Store tokens using AuthStorage utility
      AuthStorage.storeTokens({
        token: response.token,
        refreshToken: response.refreshToken,
        expiresAt: response.expiresAt.toISOString()
      }, credentials.rememberMe || false);
      
      // Set up automatic token refresh
      TokenRefreshManager.setupAutoRefresh(refreshAuth);
      
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: response.user,
          token: response.token,
          refreshToken: response.refreshToken
        }
      });
      console.log('AuthContext: Login successful, state updated');
    } catch (error) {
      console.error('AuthContext: Login error:', error);
      const message = error instanceof Error ? error.message : 'Login failed';
      dispatch({ type: 'AUTH_ERROR', payload: message });
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    try {
      dispatch({ type: 'AUTH_START' });
      const response = await authService.register(data);
      
      // Store tokens
      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('refresh_token', response.refreshToken);
      
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: response.user,
          token: response.token,
          refreshToken: response.refreshToken
        }
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Registration failed';
      dispatch({ type: 'AUTH_ERROR', payload: message });
      throw error;
    }
  };

  const logout = () => {
    // Clear automatic token refresh
    TokenRefreshManager.clearAutoRefresh();
    
    // Clear all auth storage
    AuthStorage.clearTokens();
    
    dispatch({ type: 'AUTH_LOGOUT' });
  };

  const refreshAuth = async () => {
    try {
      const currentRefreshToken = state.refreshToken || AuthStorage.getRefreshToken();
      if (!currentRefreshToken) throw new Error('No refresh token available');
      
      const response = await authService.refreshToken(currentRefreshToken);
      const rememberMe = AuthStorage.getRememberMe();
      
      // Store refreshed tokens using the same storage preference
      AuthStorage.storeTokens({
        token: response.token,
        refreshToken: response.refreshToken,
        expiresAt: response.expiresAt.toISOString()
      }, rememberMe);
      
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: response.user,
          token: response.token,
          refreshToken: response.refreshToken
        }
      });
      
      console.log('AuthContext: Token refreshed successfully');
    } catch (error) {
      console.error('AuthContext: Token refresh failed:', error);
      logout();
      throw error;
    }
  };

  const updateProfile = async (updates: Partial<User>) => {
    try {
      if (!state.user) throw new Error('No user logged in');
      
      const updatedUser = await authService.updateProfile(state.user.id, updates);
      dispatch({ type: 'UPDATE_USER', payload: updatedUser });
    } catch (error) {
      throw error;
    }
  };

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshAuth,
    updateProfile,

  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};