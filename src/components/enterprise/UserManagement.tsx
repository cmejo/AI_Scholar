/**
 * User Management Component
 * Implements task 4.2: Create user management and permission controls
 * 
 * Features:
 * - User authentication flow with error handling
 * - Permission-based UI adaptation and feature access
 * - Secure logout functionality with session cleanup
 * - User profile management
 * - Session monitoring and management
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  User,
  Shield,
  Clock,
  LogOut,
  Settings,
  Eye,
  EyeOff,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Lock,
  Unlock,
  UserCheck,
  UserX,
  Activity
} from 'lucide-react';
import { useEnterpriseAuth } from '../../hooks/useEnterpriseAuth';
import { EnterpriseAuthGuard, usePermissionGate } from './EnterpriseAuthGuard';
import { LoginCredentials } from '../../types/auth';

export interface UserManagementProps {
  showLoginForm?: boolean;
  onLoginSuccess?: () => void;
  onLogoutSuccess?: () => void;
}

export const UserManagement: React.FC<UserManagementProps> = ({
  showLoginForm = false,
  onLoginSuccess,
  onLogoutSuccess
}) => {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    session,
    sessionTimeRemaining,
    login,
    logout,
    refreshUser,
    hasPermission
  } = useEnterpriseAuth();

  const gate = usePermissionGate();

  // Login form state
  const [loginForm, setLoginForm] = useState<LoginCredentials>({
    email: '',
    password: '',
    rememberMe: false
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // User profile state
  const [showUserDetails, setShowUserDetails] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Handle login form submission
  const handleLogin = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoggingIn(true);
    setLoginError(null);

    try {
      await login(loginForm);
      setLoginForm({ email: '', password: '', rememberMe: false });
      onLoginSuccess?.();
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoggingIn(false);
    }
  }, [login, loginForm, onLoginSuccess]);

  // Handle logout
  const handleLogout = useCallback(() => {
    logout();
    onLogoutSuccess?.();
  }, [logout, onLogoutSuccess]);

  // Handle user refresh
  const handleRefreshUser = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await refreshUser();
    } catch (err) {
      console.error('Failed to refresh user:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, [refreshUser]);

  // Format session time remaining
  const formatTimeRemaining = (minutes: number): string => {
    if (minutes <= 0) return 'Expired';
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  // Get security level color
  const getSecurityLevelColor = (level: string): string => {
    switch (level) {
      case 'admin': return 'text-red-400';
      case 'elevated': return 'text-yellow-400';
      case 'standard': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  // Get role badge color
  const getRoleBadgeColor = (role: string): string => {
    switch (role) {
      case 'admin': return 'bg-red-600 text-red-100';
      case 'researcher': return 'bg-blue-600 text-blue-100';
      case 'user': return 'bg-green-600 text-green-100';
      case 'student': return 'bg-purple-600 text-purple-100';
      default: return 'bg-gray-600 text-gray-100';
    }
  };

  // Login Form Component
  const LoginForm = () => (
    <div className="max-w-md mx-auto bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="text-center mb-6">
        <Shield className="w-12 h-12 mx-auto mb-4 text-purple-400" />
        <h2 className="text-2xl font-bold text-white">Enterprise Login</h2>
        <p className="text-gray-400 mt-2">Access your enterprise features</p>
      </div>

      <form onSubmit={handleLogin} className="space-y-4">
        {/* Email Field */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
            Email Address
          </label>
          <input
            id="email"
            type="email"
            value={loginForm.email}
            onChange={(e) => setLoginForm(prev => ({ ...prev, email: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            placeholder="Enter your email"
            required
            disabled={isLoggingIn}
          />
        </div>

        {/* Password Field */}
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
            Password
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              value={loginForm.password}
              onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
              className="w-full px-3 py-2 pr-10 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter your password"
              required
              disabled={isLoggingIn}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300"
              disabled={isLoggingIn}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Remember Me */}
        <div className="flex items-center">
          <input
            id="rememberMe"
            type="checkbox"
            checked={loginForm.rememberMe}
            onChange={(e) => setLoginForm(prev => ({ ...prev, rememberMe: e.target.checked }))}
            className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
            disabled={isLoggingIn}
          />
          <label htmlFor="rememberMe" className="ml-2 text-sm text-gray-300">
            Remember me
          </label>
        </div>

        {/* Error Message */}
        {(loginError || error) && (
          <div className="flex items-center space-x-2 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
            <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span className="text-red-300 text-sm">{loginError || error}</span>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoggingIn || !loginForm.email || !loginForm.password}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
        >
          {isLoggingIn ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Signing In...</span>
            </>
          ) : (
            <>
              <Lock className="w-4 h-4" />
              <span>Sign In</span>
            </>
          )}
        </button>
      </form>
    </div>
  );

  // User Profile Component
  const UserProfile = () => (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-white">User Profile</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRefreshUser}
            disabled={isRefreshing}
            className="p-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-gray-300 rounded-lg transition-colors"
            title="Refresh user data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowUserDetails(!showUserDetails)}
            className="p-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
            title="Toggle details"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {user && (
        <div className="space-y-4">
          {/* Basic Info */}
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center">
              <User className="w-6 h-6 text-white" />
            </div>
            <div>
              <h4 className="text-lg font-medium text-white">{user.name}</h4>
              <p className="text-gray-400">{user.email}</p>
            </div>
          </div>

          {/* Role and Security Level */}
          <div className="flex items-center space-x-4">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getRoleBadgeColor(user.role || 'user')}`}>
              {user.role?.toUpperCase() || 'USER'}
            </div>
            <div className="flex items-center space-x-2">
              <Shield className={`w-4 h-4 ${getSecurityLevelColor(user.securityLevel)}`} />
              <span className={`text-sm ${getSecurityLevelColor(user.securityLevel)}`}>
                {user.securityLevel?.toUpperCase() || 'STANDARD'} Security
              </span>
            </div>
          </div>

          {/* Session Info */}
          {session && (
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-300">Session Status</span>
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-green-400" />
                  <span className="text-sm text-green-400">Active</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Time Remaining:</span>
                  <div className="text-white font-medium">{formatTimeRemaining(sessionTimeRemaining)}</div>
                </div>
                <div>
                  <span className="text-gray-400">Started:</span>
                  <div className="text-white font-medium">
                    {new Date(session.startTime).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Detailed Info (Expandable) */}
          {showUserDetails && (
            <div className="space-y-4 pt-4 border-t border-gray-700">
              {/* Permissions Summary */}
              <div>
                <h5 className="text-sm font-medium text-gray-300 mb-2">Feature Access</h5>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center space-x-2">
                    {hasPermission('analytics', 'view') ? (
                      <CheckCircle className="w-3 h-3 text-green-400" />
                    ) : (
                      <UserX className="w-3 h-3 text-red-400" />
                    )}
                    <span className="text-gray-400">Analytics</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {hasPermission('security', 'view') ? (
                      <CheckCircle className="w-3 h-3 text-green-400" />
                    ) : (
                      <UserX className="w-3 h-3 text-red-400" />
                    )}
                    <span className="text-gray-400">Security</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {hasPermission('workflows', 'view') ? (
                      <CheckCircle className="w-3 h-3 text-green-400" />
                    ) : (
                      <UserX className="w-3 h-3 text-red-400" />
                    )}
                    <span className="text-gray-400">Workflows</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {hasPermission('integrations', 'view') ? (
                      <CheckCircle className="w-3 h-3 text-green-400" />
                    ) : (
                      <UserX className="w-3 h-3 text-red-400" />
                    )}
                    <span className="text-gray-400">Integrations</span>
                  </div>
                </div>
              </div>

              {/* Account Info */}
              <div>
                <h5 className="text-sm font-medium text-gray-300 mb-2">Account Information</h5>
                <div className="space-y-1 text-xs text-gray-400">
                  <div>User ID: {user.id}</div>
                  {user.createdAt && (
                    <div>Member since: {new Date(user.createdAt).toLocaleDateString()}</div>
                  )}
                  {user.lastLoginAt && (
                    <div>Last login: {new Date(user.lastLoginAt).toLocaleString()}</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Logout Button */}
          <div className="pt-4 border-t border-gray-700">
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );

  // Loading State
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[300px] bg-gray-900 text-white">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-purple-500" />
          <p className="text-gray-300">Loading user information...</p>
        </div>
      </div>
    );
  }

  // Main Render
  return (
    <div className="p-6 bg-gray-900 text-white min-h-screen">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">User Management</h1>
          <p className="text-gray-400">
            Manage your account, permissions, and session settings
          </p>
        </div>

        {/* Show login form if not authenticated or explicitly requested */}
        {(!isAuthenticated || showLoginForm) && <LoginForm />}

        {/* Show user profile if authenticated */}
        {isAuthenticated && user && (
          <div className="space-y-6">
            <UserProfile />

            {/* Admin-only user management features */}
            {gate.hasPermission('admin', 'user_management', (
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-xl font-semibold text-white mb-4">Administrative Controls</h3>
                <div className="text-sm text-gray-400">
                  Advanced user management features would be implemented here for administrators.
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UserManagement;