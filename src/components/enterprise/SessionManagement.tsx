/**
 * Session Management Component
 * Implements task 4.2: Session management and timeout handling
 * 
 * Features:
 * - Real-time session monitoring
 * - Session timeout warnings
 * - Multiple session management
 * - Security alerts for suspicious sessions
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Clock,
  Shield,
  AlertTriangle,
  RefreshCw,
  LogOut,
  Monitor,
  Smartphone,
  Globe,
  CheckCircle,
  XCircle,
  Eye,
  Trash2
} from 'lucide-react';
import { useEnterpriseAuth } from '../../hooks/useEnterpriseAuth';
import { EnterpriseAuthGuard } from './EnterpriseAuthGuard';
import { SessionInfo } from '../../services/enterpriseAuthService';

export interface SessionManagementProps {
  showCurrentSessionOnly?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number; // in seconds
}

interface SessionWarning {
  type: 'timeout' | 'suspicious' | 'multiple';
  message: string;
  severity: 'low' | 'medium' | 'high';
  timestamp: Date;
}

export const SessionManagement: React.FC<SessionManagementProps> = ({
  showCurrentSessionOnly = false,
  autoRefresh = true,
  refreshInterval = 30
}) => {
  const {
    user,
    session,
    sessionTimeRemaining,
    logout,
    hasPermission
  } = useEnterpriseAuth();

  // State management
  const [allSessions, setAllSessions] = useState<SessionInfo[]>([]);
  const [warnings, setWarnings] = useState<SessionWarning[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showWarningDialog, setShowWarningDialog] = useState(false);

  // Fetch all user sessions (if user has permission)
  const fetchSessions = useCallback(async () => {
    if (!hasPermission('security', 'manage_sessions')) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      // This would typically fetch from the backend
      // For now, we'll simulate with current session data
      const sessions: SessionInfo[] = session ? [session] : [];
      
      setAllSessions(sessions);
      
      // Check for warnings
      checkSessionWarnings(sessions);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sessions');
    } finally {
      setIsLoading(false);
    }
  }, [hasPermission, session]);

  // Check for session warnings
  const checkSessionWarnings = useCallback((sessions: SessionInfo[]) => {
    const newWarnings: SessionWarning[] = [];

    // Check for session timeout warning (less than 5 minutes remaining)
    if (sessionTimeRemaining > 0 && sessionTimeRemaining <= 5) {
      newWarnings.push({
        type: 'timeout',
        message: `Your session will expire in ${sessionTimeRemaining} minutes`,
        severity: sessionTimeRemaining <= 2 ? 'high' : 'medium',
        timestamp: new Date()
      });
    }

    // Check for multiple active sessions
    if (sessions.length > 1) {
      newWarnings.push({
        type: 'multiple',
        message: `You have ${sessions.length} active sessions`,
        severity: sessions.length > 3 ? 'high' : 'medium',
        timestamp: new Date()
      });
    }

    // Check for suspicious sessions (different locations, unusual times, etc.)
    sessions.forEach(sessionInfo => {
      // This is a simplified check - in production, you'd have more sophisticated detection
      const sessionAge = Date.now() - new Date(sessionInfo.startTime).getTime();
      const hoursActive = sessionAge / (1000 * 60 * 60);
      
      if (hoursActive > 12) {
        newWarnings.push({
          type: 'suspicious',
          message: `Long-running session detected (${Math.round(hoursActive)} hours)`,
          severity: 'medium',
          timestamp: new Date()
        });
      }
    });

    setWarnings(newWarnings);
    
    // Show warning dialog if there are high-severity warnings
    if (newWarnings.some(w => w.severity === 'high')) {
      setShowWarningDialog(true);
    }
  }, [sessionTimeRemaining]);

  // Terminate a specific session
  const terminateSession = useCallback(async (sessionId: string) => {
    try {
      // If terminating current session, use logout
      if (session?.id === sessionId) {
        logout();
        return;
      }

      // For other sessions, would call backend API
      console.log('Terminating session:', sessionId);
      
      // Remove from local state
      setAllSessions(prev => prev.filter(s => s.id !== sessionId));
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to terminate session');
    }
  }, [session?.id, logout]);

  // Extend current session
  const extendSession = useCallback(async () => {
    try {
      // This would typically call a backend API to extend the session
      console.log('Extending session');
      
      // For now, just dismiss warnings
      setWarnings(prev => prev.filter(w => w.type !== 'timeout'));
      setShowWarningDialog(false);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to extend session');
    }
  }, []);

  // Auto-refresh sessions
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchSessions, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchSessions]);

  // Initial fetch
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Format session duration
  const formatDuration = (startTime: Date): string => {
    const duration = Date.now() - new Date(startTime).getTime();
    const hours = Math.floor(duration / (1000 * 60 * 60));
    const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  // Get device icon based on user agent
  const getDeviceIcon = (userAgent: string) => {
    if (userAgent.includes('Mobile') || userAgent.includes('Android') || userAgent.includes('iPhone')) {
      return <Smartphone className="w-4 h-4" />;
    }
    return <Monitor className="w-4 h-4" />;
  };

  // Get warning color
  const getWarningColor = (severity: string): string => {
    switch (severity) {
      case 'high': return 'text-red-400 bg-red-900/20 border-red-500/30';
      case 'medium': return 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30';
      case 'low': return 'text-blue-400 bg-blue-900/20 border-blue-500/30';
      default: return 'text-gray-400 bg-gray-900/20 border-gray-500/30';
    }
  };

  // Warning Dialog Component
  const WarningDialog = () => (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-700">
        <div className="flex items-center space-x-3 mb-4">
          <AlertTriangle className="w-6 h-6 text-red-400" />
          <h3 className="text-lg font-semibold text-white">Session Warning</h3>
        </div>
        
        <div className="space-y-2 mb-6">
          {warnings.filter(w => w.severity === 'high').map((warning, index) => (
            <div key={index} className="text-sm text-gray-300">
              {warning.message}
            </div>
          ))}
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={extendSession}
            className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
          >
            Extend Session
          </button>
          <button
            onClick={() => setShowWarningDialog(false)}
            className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );

  // Current Session Component
  const CurrentSession = () => (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Current Session</h3>
        <div className="flex items-center space-x-2">
          <CheckCircle className="w-5 h-5 text-green-400" />
          <span className="text-sm text-green-400">Active</span>
        </div>
      </div>

      {session && (
        <div className="space-y-4">
          {/* Session Info Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm text-gray-400">Time Remaining</span>
              <div className="flex items-center space-x-2 mt-1">
                <Clock className="w-4 h-4 text-purple-400" />
                <span className={`font-medium ${sessionTimeRemaining <= 5 ? 'text-red-400' : 'text-white'}`}>
                  {sessionTimeRemaining > 0 ? `${sessionTimeRemaining}m` : 'Expired'}
                </span>
              </div>
            </div>
            
            <div>
              <span className="text-sm text-gray-400">Duration</span>
              <div className="flex items-center space-x-2 mt-1">
                <Activity className="w-4 h-4 text-blue-400" />
                <span className="text-white font-medium">
                  {formatDuration(session.startTime)}
                </span>
              </div>
            </div>
            
            <div>
              <span className="text-sm text-gray-400">Device</span>
              <div className="flex items-center space-x-2 mt-1">
                {getDeviceIcon(session.userAgent)}
                <span className="text-white font-medium text-sm">
                  {session.userAgent.includes('Mobile') ? 'Mobile' : 'Desktop'}
                </span>
              </div>
            </div>
            
            <div>
              <span className="text-sm text-gray-400">Security Level</span>
              <div className="flex items-center space-x-2 mt-1">
                <Shield className="w-4 h-4 text-purple-400" />
                <span className="text-white font-medium capitalize">
                  {session.securityLevel}
                </span>
              </div>
            </div>
          </div>

          {/* Session Actions */}
          <div className="flex space-x-3 pt-4 border-t border-gray-700">
            <button
              onClick={extendSession}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Extend</span>
            </button>
            
            <button
              onClick={() => terminateSession(session.id)}
              className="flex items-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>End Session</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );

  // All Sessions Component
  const AllSessions = () => (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">All Sessions</h3>
        <button
          onClick={fetchSessions}
          disabled={isLoading}
          className="flex items-center space-x-2 px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-600 text-gray-300 rounded-lg transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span className="text-sm">Refresh</span>
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span className="text-red-300 text-sm">{error}</span>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {allSessions.map((sessionInfo) => (
          <div
            key={sessionInfo.id}
            className={`p-4 rounded-lg border ${
              sessionInfo.id === session?.id 
                ? 'bg-purple-900/20 border-purple-500/30' 
                : 'bg-gray-700 border-gray-600'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {getDeviceIcon(sessionInfo.userAgent)}
                <div>
                  <div className="text-sm font-medium text-white">
                    {sessionInfo.id === session?.id ? 'Current Session' : 'Session'}
                  </div>
                  <div className="text-xs text-gray-400">
                    Started {formatDuration(sessionInfo.startTime)} ago
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                {sessionInfo.isActive ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400" />
                )}
                
                <button
                  onClick={() => terminateSession(sessionInfo.id)}
                  className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                  title="Terminate session"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
        
        {allSessions.length === 0 && !isLoading && (
          <div className="text-center text-gray-500 py-8">
            No active sessions found
          </div>
        )}
      </div>
    </div>
  );

  // Warnings Component
  const WarningsPanel = () => (
    warnings.length > 0 && (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Security Alerts</h3>
        
        <div className="space-y-3">
          {warnings.map((warning, index) => (
            <div
              key={index}
              className={`p-3 rounded-lg border ${getWarningColor(warning.severity)}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm font-medium">{warning.message}</span>
                </div>
                <span className="text-xs opacity-75">
                  {warning.timestamp.toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  );

  return (
    <EnterpriseAuthGuard
      requiredPermission={{ category: 'security', action: 'view' }}
      loadingMessage="Loading session management..."
    >
      <div className="p-6 bg-gray-900 text-white min-h-screen">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Session Management</h1>
            <p className="text-gray-400">
              Monitor and manage your active sessions and security settings
            </p>
          </div>

          <div className="space-y-6">
            {/* Warnings Panel */}
            <WarningsPanel />

            {/* Current Session */}
            <CurrentSession />

            {/* All Sessions (if user has permission) */}
            {!showCurrentSessionOnly && hasPermission('security', 'manage_sessions') && (
              <AllSessions />
            )}
          </div>

          {/* Warning Dialog */}
          {showWarningDialog && <WarningDialog />}
        </div>
      </div>
    </EnterpriseAuthGuard>
  );
};

export default SessionManagement;