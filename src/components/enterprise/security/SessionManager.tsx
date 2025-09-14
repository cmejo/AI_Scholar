/**
 * Session Manager - Active session display and management
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Users,
  Search,
  Filter,
  Clock,
  MapPin,
  Monitor,
  AlertTriangle,
  RefreshCw,
  Calendar,
  Shield
} from 'lucide-react';
import { ActiveSession, SecurityAction } from '../../../types/security';
import { securityDashboardService } from '../../../services/securityDashboardService';

export interface SessionManagerProps {
  onSecurityAction?: (action: SecurityAction) => void;
}

interface SessionFilters {
  userId?: string;
  ipAddress?: string;
  timeRange?: { start: Date; end: Date };
  location?: string;
  status?: 'active' | 'inactive' | 'suspicious';
  sortBy?: 'loginTime' | 'lastActivity' | 'userEmail' | 'location';
  sortOrder?: 'asc' | 'desc';
}

export const SessionManager: React.FC<SessionManagerProps> = ({
  onSecurityAction
}) => {
  const [sessions, setSessions] = useState<ActiveSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SessionFilters>({
    sortBy: 'lastActivity',
    sortOrder: 'desc'
  });
  const [selectedSessions, setSelectedSessions] = useState<Set<string>>(new Set());
  const [showConfirmDialog, setShowConfirmDialog] = useState<{
    type: 'single' | 'multiple';
    sessionIds: string[];
  } | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);
  const [expandedSession, setExpandedSession] = useState<string | null>(null);

  // Load sessions
  const loadSessions = useCallback(async () => {
    try {
      setError(null);
      const sessionData = await securityDashboardService.getActiveSessions(filters);
      setSessions(sessionData);
    } catch (err) {
      setError('Failed to load session data');
      console.error('Session loading error:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Handle session termination
  const handleTerminateSession = async (sessionId: string) => {
    try {
      const success = await securityDashboardService.performSecurityAction({
        type: 'terminate_session',
        payload: { sessionId }
      });
      
      if (success) {
        onSecurityAction?.({ type: 'terminate_session', payload: { sessionId } });
        await loadSessions(); // Refresh the list
        setSelectedSessions(prev => {
          const newSet = new Set(prev);
          newSet.delete(sessionId);
          return newSet;
        });
      } else {
        setError('Failed to terminate session');
      }
    } catch (err) {
      setError('Error terminating session');
      console.error('Session termination error:', err);
    }
  };

  // Handle multiple session termination
  const handleTerminateMultipleSessions = async (sessionIds: string[]) => {
    try {
      const promises = sessionIds.map(id => 
        securityDashboardService.performSecurityAction({
          type: 'terminate_session',
          payload: { sessionId: id }
        })
      );
      
      await Promise.all(promises);
      
      sessionIds.forEach(id => {
        onSecurityAction?.({ type: 'terminate_session', payload: { sessionId: id } });
      });
      
      await loadSessions();
      setSelectedSessions(new Set());
    } catch (err) {
      setError('Error terminating sessions');
      console.error('Multiple session termination error:', err);
    }
  };

  // Filter and sort sessions
  const filteredSessions = sessions
    .filter(session => {
      // Search term filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch = (
          session.userEmail.toLowerCase().includes(searchLower) ||
          session.userId.toLowerCase().includes(searchLower) ||
          session.ipAddress.includes(searchTerm) ||
          (session.location && session.location.toLowerCase().includes(searchLower))
        );
        if (!matchesSearch) return false;
      }

      // Location filter
      if (filters.location && session.location) {
        if (!session.location.toLowerCase().includes(filters.location.toLowerCase())) {
          return false;
        }
      }

      // Status filter
      if (filters.status) {
        const suspicious = isSuspiciousSession(session);
        switch (filters.status) {
          case 'active':
            return session.isActive && !suspicious;
          case 'inactive':
            return !session.isActive;
          case 'suspicious':
            return suspicious;
        }
      }

      return true;
    })
    .sort((a, b) => {
      const { sortBy = 'lastActivity', sortOrder = 'desc' } = filters;
      let comparison = 0;

      switch (sortBy) {
        case 'loginTime':
          comparison = a.loginTime.getTime() - b.loginTime.getTime();
          break;
        case 'lastActivity':
          comparison = a.lastActivity.getTime() - b.lastActivity.getTime();
          break;
        case 'userEmail':
          comparison = a.userEmail.localeCompare(b.userEmail);
          break;
        case 'location':
          comparison = (a.location || '').localeCompare(b.location || '');
          break;
        default:
          comparison = 0;
      }

      return sortOrder === 'desc' ? -comparison : comparison;
    });

  // Handle session selection
  const handleSessionSelect = (sessionId: string, selected: boolean) => {
    setSelectedSessions(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(sessionId);
      } else {
        newSet.delete(sessionId);
      }
      return newSet;
    });
  };

  // Handle select all
  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedSessions(new Set(filteredSessions.map(s => s.id)));
    } else {
      setSelectedSessions(new Set());
    }
  };

  // Get session duration
  const getSessionDuration = (loginTime: Date): string => {
    const now = new Date();
    const duration = now.getTime() - loginTime.getTime();
    const hours = Math.floor(duration / (1000 * 60 * 60));
    const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  // Get time since last activity
  const getTimeSinceActivity = (lastActivity: Date): string => {
    const now = new Date();
    const duration = now.getTime() - lastActivity.getTime();
    const minutes = Math.floor(duration / (1000 * 60));
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  // Check if session is suspicious
  const isSuspiciousSession = (session: ActiveSession): boolean => {
    const now = new Date();
    const inactiveTime = now.getTime() - session.lastActivity.getTime();
    const sessionDuration = now.getTime() - session.loginTime.getTime();
    
    // Flag as suspicious if inactive for more than 2 hours or session longer than 12 hours
    return inactiveTime > 2 * 60 * 60 * 1000 || sessionDuration > 12 * 60 * 60 * 1000;
  };

  // Get session statistics
  const getSessionStats = () => {
    const activeSessions = sessions.filter(s => s.isActive);
    const suspiciousSessions = activeSessions.filter(isSuspiciousSession);
    const inactiveSessions = sessions.filter(s => !s.isActive);
    
    return {
      total: sessions.length,
      active: activeSessions.length,
      inactive: inactiveSessions.length,
      suspicious: suspiciousSessions.length,
      filtered: filteredSessions.length
    };
  };

  // Export session data
  const exportSessionData = () => {
    const dataToExport = filteredSessions.map(session => ({
      id: session.id,
      userId: session.userId,
      userEmail: session.userEmail,
      loginTime: session.loginTime.toISOString(),
      lastActivity: session.lastActivity.toISOString(),
      ipAddress: session.ipAddress,
      location: session.location || 'Unknown',
      isActive: session.isActive,
      suspicious: isSuspiciousSession(session),
      sessionDuration: getSessionDuration(session.loginTime),
      timeSinceActivity: getTimeSinceActivity(session.lastActivity)
    }));

    const csvContent = [
      'ID,User ID,Email,Login Time,Last Activity,IP Address,Location,Active,Suspicious,Duration,Time Since Activity',
      ...dataToExport.map(session => 
        `"${session.id}","${session.userId}","${session.userEmail}","${session.loginTime}","${session.lastActivity}","${session.ipAddress}","${session.location}","${session.isActive}","${session.suspicious}","${session.sessionDuration}","${session.timeSinceActivity}"`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `session-data-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const sessionStats = getSessionStats();

  // Initialize data loading
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadSessions();
      }, 30000); // Refresh every 30 seconds
      setRefreshInterval(interval);
      return () => clearInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh, loadSessions]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [refreshInterval]);

  // Confirmation dialog component
  const ConfirmDialog = ({ onConfirm, onCancel, sessionCount }: {
    onConfirm: () => void;
    onCancel: () => void;
    sessionCount: number;
  }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center space-x-3 mb-4">
          <AlertTriangle className="w-6 h-6 text-orange-400" />
          <h3 className="text-lg font-semibold text-white">Confirm Session Termination</h3>
        </div>
        <p className="text-gray-300 mb-6">
          Are you sure you want to terminate {sessionCount === 1 ? 'this session' : `${sessionCount} sessions`}? 
          This action cannot be undone and will immediately log out the affected user{sessionCount > 1 ? 's' : ''}.
        </p>
        <div className="flex space-x-3">
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            Terminate {sessionCount === 1 ? 'Session' : 'Sessions'}
          </button>
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-center h-32">
          <div className="flex items-center space-x-3">
            <RefreshCw className="w-5 h-5 animate-spin text-blue-400" />
            <span className="text-gray-300">Loading sessions...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Users className="w-6 h-6 text-blue-400" />
          <h2 className="text-xl font-semibold text-white">Session Management</h2>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-1 bg-blue-900 text-blue-200 rounded text-sm">
              {sessionStats.filtered} shown
            </span>
            <span className="px-2 py-1 bg-green-900 text-green-200 rounded text-sm">
              {sessionStats.active} active
            </span>
            {sessionStats.suspicious > 0 && (
              <span className="px-2 py-1 bg-orange-900 text-orange-200 rounded text-sm">
                {sessionStats.suspicious} suspicious
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="auto-refresh"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="auto-refresh" className="text-sm text-gray-300">
              Auto-refresh
            </label>
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-lg transition-colors ${
              showFilters ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            title="Toggle filters"
          >
            <Filter className="w-4 h-4" />
          </button>
          <button
            onClick={loadSessions}
            className="p-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
            title="Refresh now"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={exportSessionData}
            className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-colors"
            title="Export session data as CSV"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by user, email, IP address, or location..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Advanced Filters */}
        {showFilters && (
          <div className="bg-gray-700 rounded-lg p-4 space-y-4">
            <h3 className="text-sm font-medium text-gray-300">Advanced Filters & Sorting</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">User ID</label>
                <input
                  type="text"
                  placeholder="Filter by user ID"
                  value={filters.userId || ''}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    userId: e.target.value.trim() === '' ? undefined : e.target.value 
                  }))}
                  className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">IP Address</label>
                <input
                  type="text"
                  placeholder="Filter by IP address"
                  value={filters.ipAddress || ''}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    ipAddress: e.target.value.trim() === '' ? undefined : e.target.value 
                  }))}
                  className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Location</label>
                <input
                  type="text"
                  placeholder="Filter by location"
                  value={filters.location || ''}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    location: e.target.value.trim() === '' ? undefined : e.target.value 
                  }))}
                  className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Status</label>
                <select
                  value={filters.status || ''}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    status: e.target.value === '' ? undefined : e.target.value as 'active' | 'inactive' | 'suspicious'
                  }))}
                  className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Sessions</option>
                  <option value="active">Active Only</option>
                  <option value="inactive">Inactive Only</option>
                  <option value="suspicious">Suspicious Only</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Sort By</label>
                <select
                  value={filters.sortBy || 'lastActivity'}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    sortBy: e.target.value as 'loginTime' | 'lastActivity' | 'userEmail' | 'location'
                  }))}
                  className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="lastActivity">Last Activity</option>
                  <option value="loginTime">Login Time</option>
                  <option value="userEmail">User Email</option>
                  <option value="location">Location</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Sort Order</label>
                <select
                  value={filters.sortOrder || 'desc'}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    sortOrder: e.target.value as 'asc' | 'desc'
                  }))}
                  className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="desc">Newest First</option>
                  <option value="asc">Oldest First</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={() => setFilters({ sortBy: 'lastActivity', sortOrder: 'desc' })}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors"
                >
                  Clear Filters
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bulk Actions */}
      {selectedSessions.size > 0 && (
        <div className="mb-4 p-3 bg-blue-900 bg-opacity-50 border border-blue-700 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-blue-200">
                {selectedSessions.size} session{selectedSessions.size > 1 ? 's' : ''} selected
              </span>
              <div className="text-xs text-blue-300">
                {Array.from(selectedSessions).map(id => {
                  const session = sessions.find(s => s.id === id);
                  return session ? session.userEmail : id;
                }).join(', ')}
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setSelectedSessions(new Set())}
                className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded transition-colors"
              >
                Clear Selection
              </button>
              <button
                onClick={() => setShowConfirmDialog({
                  type: 'multiple',
                  sessionIds: Array.from(selectedSessions)
                })}
                className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
              >
                Terminate Selected
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-700 rounded-lg">
          <p className="text-red-200">{error}</p>
        </div>
      )}

      {/* Sessions Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left py-3 px-4">
                <input
                  type="checkbox"
                  checked={selectedSessions.size === filteredSessions.length && filteredSessions.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th className="text-left py-3 px-4 text-gray-300">User</th>
              <th className="text-left py-3 px-4 text-gray-300">Session Info</th>
              <th className="text-left py-3 px-4 text-gray-300">Location & IP</th>
              <th className="text-left py-3 px-4 text-gray-300">Activity</th>
              <th className="text-left py-3 px-4 text-gray-300">Status</th>
              <th className="text-left py-3 px-4 text-gray-300">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredSessions.map((session) => {
              const suspicious = isSuspiciousSession(session);
              return (
                <React.Fragment key={session.id}>
                  <tr className={`border-b border-gray-700 hover:bg-gray-700 ${suspicious ? 'bg-orange-900 bg-opacity-20' : ''}`}>
                  <td className="py-3 px-4">
                    <input
                      type="checkbox"
                      checked={selectedSessions.has(session.id)}
                      onChange={(e) => handleSessionSelect(session.id, e.target.checked)}
                      className="rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className="py-3 px-4">
                    <div>
                      <p className="font-medium text-white">{session.userEmail}</p>
                      <p className="text-sm text-gray-400">{session.userId}</p>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-300">
                          Started {getSessionDuration(session.loginTime)} ago
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-400">
                          {session.loginTime.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <MapPin className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-300">{session.location || 'Unknown'}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Monitor className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-400 font-mono">{session.ipAddress}</span>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div>
                      <p className="text-sm text-gray-300">
                        {getTimeSinceActivity(session.lastActivity)}
                      </p>
                      <p className="text-xs text-gray-400">
                        {session.lastActivity.toLocaleString()}
                      </p>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      {session.isActive ? (
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                          <span className="text-sm text-green-400">Active</span>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                          <span className="text-sm text-gray-400">Inactive</span>
                        </div>
                      )}
                      {suspicious && (
                        <div className="flex items-center space-x-1">
                          <Shield className="w-4 h-4 text-orange-400" />
                          <span className="text-xs text-orange-400">Suspicious</span>
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setExpandedSession(expandedSession === session.id ? null : session.id)}
                        className="px-2 py-1 bg-gray-600 hover:bg-gray-500 text-white text-xs rounded transition-colors"
                        title="View details"
                      >
                        {expandedSession === session.id ? 'Hide' : 'Details'}
                      </button>
                      <button
                        onClick={() => setShowConfirmDialog({
                          type: 'single',
                          sessionIds: [session.id]
                        })}
                        className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
                        title="Terminate session"
                      >
                        Terminate
                      </button>
                    </div>
                  </td>
                </tr>
                {/* Expanded session details */}
                {expandedSession === session.id && (
                  <tr className="bg-gray-750">
                    <td colSpan={7} className="px-4 py-3">
                      <div className="bg-gray-600 rounded-lg p-4 space-y-3">
                        <h4 className="text-sm font-medium text-white mb-3">Session Details</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-400">Session ID:</span>
                            <span className="ml-2 text-white font-mono">{session.id}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">User Agent:</span>
                            <span className="ml-2 text-white break-all">{session.userAgent}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Login Time:</span>
                            <span className="ml-2 text-white">{session.loginTime.toLocaleString()}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Last Activity:</span>
                            <span className="ml-2 text-white">{session.lastActivity.toLocaleString()}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Session Duration:</span>
                            <span className="ml-2 text-white">{getSessionDuration(session.loginTime)}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Time Since Activity:</span>
                            <span className="ml-2 text-white">{getTimeSinceActivity(session.lastActivity)}</span>
                          </div>
                        </div>
                        {isSuspiciousSession(session) && (
                          <div className="mt-3 p-3 bg-orange-900 bg-opacity-50 border border-orange-700 rounded">
                            <div className="flex items-center space-x-2">
                              <Shield className="w-4 h-4 text-orange-400" />
                              <span className="text-orange-200 font-medium">Suspicious Activity Detected</span>
                            </div>
                            <p className="text-orange-300 text-sm mt-1">
                              This session has been flagged as suspicious due to extended inactivity or unusual duration.
                            </p>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>

        {filteredSessions.length === 0 && (
          <div className="text-center py-8">
            <Users className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">
              {searchTerm ? 'No sessions match your search criteria' : 'No active sessions found'}
            </p>
          </div>
        )}
      </div>

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <ConfirmDialog
          sessionCount={showConfirmDialog.sessionIds.length}
          onConfirm={async () => {
            if (showConfirmDialog.type === 'single' && showConfirmDialog.sessionIds[0]) {
              await handleTerminateSession(showConfirmDialog.sessionIds[0]);
            } else {
              await handleTerminateMultipleSessions(showConfirmDialog.sessionIds);
            }
            setShowConfirmDialog(null);
          }}
          onCancel={() => setShowConfirmDialog(null)}
        />
      )}
    </div>
  );
};

export default SessionManager;