/**
 * Audit Log Viewer - Security audit log display with filtering and pagination
 * Enhanced with administrative controls and security action logging
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Search,
  Filter,
  Calendar,
  User,
  Activity,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Download,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Eye,
  Clock,
  Shield,
  Settings,
  Archive,
  Trash2,
  Lock,
  Unlock
} from 'lucide-react';
import { SecurityAuditLog, SecurityAction } from '../../../types/security';
import { securityDashboardService } from '../../../services/securityDashboardService';

export interface AuditLogViewerProps {
  onExport?: (logs: SecurityAuditLog[]) => void;
  onSecurityAction?: (action: SecurityAction) => void;
  showAdminControls?: boolean;
}

interface AuditFilters {
  userId?: string;
  action?: string;
  success?: boolean;
  timeRange?: { start: Date; end: Date };
  page: number;
  limit: number;
}

export const AuditLogViewer: React.FC<AuditLogViewerProps> = ({
  onExport,
  onSecurityAction,
  showAdminControls = true
}) => {
  const [logs, setLogs] = useState<SecurityAuditLog[]>([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedLog, setSelectedLog] = useState<SecurityAuditLog | null>(null);
  const [selectedLogs, setSelectedLogs] = useState<Set<string>>(new Set());
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [archiveMode, setArchiveMode] = useState(false);
  const [filters, setFilters] = useState<AuditFilters>({
    page: 1,
    limit: 50
  });

  // Load audit logs
  const loadAuditLogs = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const { logs: auditLogs, total } = await securityDashboardService.getAuditLogs(filters);
      setLogs(auditLogs);
      setTotalLogs(total);
    } catch (err) {
      setError('Failed to load audit logs');
      console.error('Audit log loading error:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Handle filter changes
  const updateFilters = (newFilters: Partial<AuditFilters>) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters,
      page: newFilters.page !== undefined ? newFilters.page : 1 // Reset to page 1 unless explicitly setting page
    }));
  };

  // Handle pagination
  const handlePageChange = (newPage: number) => {
    setFilters(prev => ({ ...prev, page: newPage }));
  };

  // Handle log selection
  const handleLogSelection = (logId: string, selected: boolean) => {
    const newSelection = new Set(selectedLogs);
    if (selected) {
      newSelection.add(logId);
    } else {
      newSelection.delete(logId);
    }
    setSelectedLogs(newSelection);
  };

  // Handle select all logs
  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedLogs(new Set(logs.map(log => log.id)));
    } else {
      setSelectedLogs(new Set());
    }
  };

  // Handle administrative actions
  const handleAdminAction = async (action: 'archive' | 'delete' | 'flag') => {
    if (selectedLogs.size === 0) return;

    try {
      const logIds = Array.from(selectedLogs);
      const securityAction: SecurityAction = {
        type: 'admin_action',
        payload: { 
          action, 
          logIds,
          reason: `Bulk ${action} operation on ${logIds.length} audit logs`
        }
      };

      onSecurityAction?.(securityAction);
      
      // Clear selection after action
      setSelectedLogs(new Set());
      
      // Refresh data
      await loadAuditLogs();
    } catch (err) {
      setError(`Failed to ${action} selected logs`);
      console.error(`Admin action ${action} error:`, err);
    }
  };

  // Handle security investigation
  const handleInvestigate = async (log: SecurityAuditLog) => {
    try {
      const securityAction: SecurityAction = {
        type: 'investigate_log',
        payload: { 
          logId: log.id,
          userId: log.userId,
          action: log.action,
          timestamp: log.timestamp
        }
      };

      onSecurityAction?.(securityAction);
    } catch (err) {
      setError('Failed to initiate investigation');
      console.error('Investigation error:', err);
    }
  };

  // Handle user blocking
  const handleBlockUser = async (userId: string) => {
    try {
      const securityAction: SecurityAction = {
        type: 'block_user',
        payload: { userId, reason: 'Suspicious activity detected in audit logs' }
      };

      onSecurityAction?.(securityAction);
    } catch (err) {
      setError('Failed to block user');
      console.error('User blocking error:', err);
    }
  };

  // Get action icon
  const getActionIcon = (action: string, success: boolean) => {
    if (!success) {
      return <XCircle className="w-4 h-4 text-red-400" />;
    }

    switch (action) {
      case 'login_success':
      case 'login_failed':
        return <User className="w-4 h-4 text-blue-400" />;
      case 'document_access':
      case 'document_read':
      case 'document_write':
        return <FileText className="w-4 h-4 text-green-400" />;
      case 'api_call':
        return <Activity className="w-4 h-4 text-purple-400" />;
      case 'session_terminated':
      case 'logout':
        return <XCircle className="w-4 h-4 text-orange-400" />;
      case 'permission_change':
      case 'user_blocked':
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      default:
        return <CheckCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  // Get action color class
  const getActionColorClass = (action: string, success: boolean) => {
    if (!success) {
      return 'text-red-400 bg-red-900 bg-opacity-20';
    }

    switch (action) {
      case 'login_success':
        return 'text-green-400 bg-green-900 bg-opacity-20';
      case 'login_failed':
        return 'text-red-400 bg-red-900 bg-opacity-20';
      case 'document_access':
      case 'document_read':
        return 'text-blue-400 bg-blue-900 bg-opacity-20';
      case 'document_write':
        return 'text-green-400 bg-green-900 bg-opacity-20';
      case 'api_call':
        return 'text-purple-400 bg-purple-900 bg-opacity-20';
      case 'session_terminated':
      case 'logout':
        return 'text-orange-400 bg-orange-900 bg-opacity-20';
      case 'permission_change':
      case 'user_blocked':
        return 'text-yellow-400 bg-yellow-900 bg-opacity-20';
      default:
        return 'text-gray-400 bg-gray-900 bg-opacity-20';
    }
  };

  // Format action name
  const formatActionName = (action: string) => {
    return action
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Export logs
  const handleExport = () => {
    if (onExport) {
      onExport(logs);
    } else {
      // Default CSV export
      const csvContent = [
        ['Timestamp', 'User ID', 'Action', 'Resource', 'Success', 'IP Address', 'User Agent', 'Details'].join(','),
        ...logs.map(log => [
          log.timestamp.toISOString(),
          log.userId,
          log.action,
          log.resource,
          log.success.toString(),
          log.ipAddress,
          `"${log.userAgent}"`,
          JSON.stringify(log.details || {})
        ].join(','))
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  // Calculate pagination info
  const totalPages = Math.ceil(totalLogs / filters.limit);
  const startIndex = (filters.page - 1) * filters.limit + 1;
  const endIndex = Math.min(filters.page * filters.limit, totalLogs);

  // Initialize data loading
  useEffect(() => {
    loadAuditLogs();
  }, [loadAuditLogs]);

  // Log detail modal
  const LogDetailModal = ({ log, onClose }: { log: SecurityAuditLog; onClose: () => void }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Audit Log Details</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Log ID</label>
              <p className="text-white font-mono text-sm">{log.id}</p>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Timestamp</label>
              <p className="text-white">{log.timestamp.toLocaleString()}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">User ID</label>
              <p className="text-white">{log.userId}</p>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Action</label>
              <div className="flex items-center space-x-2">
                {getActionIcon(log.action, log.success)}
                <span className="text-white">{formatActionName(log.action)}</span>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Resource</label>
              <p className="text-white">{log.resource}</p>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Success</label>
              <div className="flex items-center space-x-2">
                {log.success ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400" />
                )}
                <span className={log.success ? 'text-green-400' : 'text-red-400'}>
                  {log.success ? 'Success' : 'Failed'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">IP Address</label>
              <p className="text-white font-mono">{log.ipAddress}</p>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">User Agent</label>
              <p className="text-white text-sm break-all">{log.userAgent}</p>
            </div>
          </div>
          
          {log.details && Object.keys(log.details).length > 0 && (
            <div>
              <label className="block text-sm text-gray-400 mb-1">Additional Details</label>
              <pre className="bg-gray-900 p-3 rounded text-sm text-gray-300 overflow-x-auto">
                {JSON.stringify(log.details, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <FileText className="w-6 h-6 text-green-400" />
          <h2 className="text-xl font-semibold text-white">Audit Logs</h2>
          <span className="px-2 py-1 bg-green-900 text-green-200 rounded text-sm">
            {totalLogs} total
          </span>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-lg transition-colors ${
              showFilters ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <Filter className="w-4 h-4" />
          </button>
          {showAdminControls && (
            <button
              onClick={() => setShowAdminPanel(!showAdminPanel)}
              className={`p-2 rounded-lg transition-colors ${
                showAdminPanel ? 'bg-orange-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <Settings className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={handleExport}
            disabled={logs.length === 0}
            className="flex items-center space-x-2 px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
          <button
            onClick={loadAuditLogs}
            className="p-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="mb-6 bg-gray-700 rounded-lg p-4 space-y-4">
          <h3 className="text-sm font-medium text-gray-300">Filter Audit Logs</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">User ID</label>
              <input
                type="text"
                placeholder="Filter by user ID"
                value={filters.userId || ''}
                onChange={(e) => updateFilters({ userId: e.target.value || undefined })}
                className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Action</label>
              <select
                value={filters.action || ''}
                onChange={(e) => updateFilters({ action: e.target.value || undefined })}
                className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">All actions</option>
                <option value="login_success">Login Success</option>
                <option value="login_failed">Login Failed</option>
                <option value="document_access">Document Access</option>
                <option value="api_call">API Call</option>
                <option value="logout">Logout</option>
                <option value="session_terminated">Session Terminated</option>
                <option value="permission_change">Permission Change</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Status</label>
              <select
                value={filters.success === undefined ? '' : filters.success.toString()}
                onChange={(e) => updateFilters({ 
                  success: e.target.value === '' ? undefined : e.target.value === 'true' 
                })}
                className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">All statuses</option>
                <option value="true">Success</option>
                <option value="false">Failed</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => setFilters({ page: 1, limit: filters.limit })}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Administrative Controls Panel */}
      {showAdminControls && showAdminPanel && (
        <div className="mb-6 bg-orange-900 bg-opacity-20 border border-orange-700 rounded-lg p-4 space-y-4">
          <div className="flex items-center space-x-3">
            <Shield className="w-5 h-5 text-orange-400" />
            <h3 className="text-sm font-medium text-orange-300">Administrative Controls</h3>
            <span className="px-2 py-1 bg-orange-800 text-orange-200 rounded text-xs">
              {selectedLogs.size} selected
            </span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="block text-sm text-orange-300">Bulk Actions</label>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleAdminAction('archive')}
                  disabled={selectedLogs.size === 0}
                  className="flex items-center space-x-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded text-sm transition-colors"
                >
                  <Archive className="w-4 h-4" />
                  <span>Archive</span>
                </button>
                <button
                  onClick={() => handleAdminAction('delete')}
                  disabled={selectedLogs.size === 0}
                  className="flex items-center space-x-1 px-3 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded text-sm transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Delete</span>
                </button>
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="block text-sm text-orange-300">Archive Mode</label>
              <button
                onClick={() => setArchiveMode(!archiveMode)}
                className={`flex items-center space-x-2 px-3 py-2 rounded text-sm transition-colors ${
                  archiveMode 
                    ? 'bg-yellow-600 hover:bg-yellow-700 text-white' 
                    : 'bg-gray-600 hover:bg-gray-700 text-gray-300'
                }`}
              >
                {archiveMode ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                <span>{archiveMode ? 'View Archived' : 'View Active'}</span>
              </button>
            </div>
            
            <div className="space-y-2">
              <label className="block text-sm text-orange-300">Selection</label>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleSelectAll(true)}
                  className="px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors"
                >
                  Select All
                </button>
                <button
                  onClick={() => handleSelectAll(false)}
                  className="px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="block text-sm text-orange-300">Security Actions</label>
              <div className="text-xs text-orange-400">
                Use individual log actions for investigations and user management
              </div>
            </div>
          </div>
          
          {selectedLogs.size > 0 && (
            <div className="bg-orange-800 bg-opacity-30 rounded p-3">
              <p className="text-sm text-orange-200">
                <strong>Warning:</strong> Administrative actions on audit logs are permanent and will be logged for compliance.
                Selected logs: {selectedLogs.size}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-700 rounded-lg">
          <p className="text-red-200">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center h-32">
          <div className="flex items-center space-x-3">
            <RefreshCw className="w-5 h-5 animate-spin text-blue-400" />
            <span className="text-gray-300">Loading audit logs...</span>
          </div>
        </div>
      )}

      {/* Logs Table */}
      {!loading && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  {showAdminControls && (
                    <th className="text-left py-3 px-4 text-gray-300 w-12">
                      <input
                        type="checkbox"
                        checked={logs.length > 0 && logs.every(log => selectedLogs.has(log.id))}
                        onChange={(e) => handleSelectAll(e.target.checked)}
                        className="rounded bg-gray-600 border-gray-500 text-blue-600 focus:ring-blue-500"
                      />
                    </th>
                  )}
                  <th className="text-left py-3 px-4 text-gray-300">Timestamp</th>
                  <th className="text-left py-3 px-4 text-gray-300">User</th>
                  <th className="text-left py-3 px-4 text-gray-300">Action</th>
                  <th className="text-left py-3 px-4 text-gray-300">Resource</th>
                  <th className="text-left py-3 px-4 text-gray-300">Status</th>
                  <th className="text-left py-3 px-4 text-gray-300">IP Address</th>
                  <th className="text-left py-3 px-4 text-gray-300">Actions</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className={`border-b border-gray-700 hover:bg-gray-700 ${selectedLogs.has(log.id) ? 'bg-blue-900 bg-opacity-20' : ''}`}>
                    {showAdminControls && (
                      <td className="py-3 px-4">
                        <input
                          type="checkbox"
                          checked={selectedLogs.has(log.id)}
                          onChange={(e) => handleLogSelection(log.id, e.target.checked)}
                          className="rounded bg-gray-600 border-gray-500 text-blue-600 focus:ring-blue-500"
                        />
                      </td>
                    )}
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-sm text-white">{log.timestamp.toLocaleString()}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        <p className="text-sm text-white">{log.userId}</p>
                        {showAdminControls && !log.success && (
                          <button
                            onClick={() => handleBlockUser(log.userId)}
                            className="p-1 hover:bg-red-600 rounded text-red-400 hover:text-white transition-colors"
                            title="Block user due to suspicious activity"
                          >
                            <Lock className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className={`inline-flex items-center space-x-2 px-2 py-1 rounded text-sm ${getActionColorClass(log.action, log.success)}`}>
                        {getActionIcon(log.action, log.success)}
                        <span>{formatActionName(log.action)}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <p className="text-sm text-gray-300 font-mono">{log.resource}</p>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        {log.success ? (
                          <CheckCircle className="w-4 h-4 text-green-400" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-400" />
                        )}
                        <span className={`text-sm ${log.success ? 'text-green-400' : 'text-red-400'}`}>
                          {log.success ? 'Success' : 'Failed'}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <p className="text-sm text-gray-300 font-mono">{log.ipAddress}</p>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setSelectedLog(log)}
                          className="p-1 hover:bg-gray-600 rounded text-gray-400 hover:text-white transition-colors"
                          title="View details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {showAdminControls && !log.success && (
                          <button
                            onClick={() => handleInvestigate(log)}
                            className="p-1 hover:bg-yellow-600 rounded text-yellow-400 hover:text-white transition-colors"
                            title="Investigate suspicious activity"
                          >
                            <Search className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {logs.length === 0 && !loading && (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                <p className="text-gray-400">No audit logs found</p>
              </div>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <div className="text-sm text-gray-400">
                Showing {startIndex}-{endIndex} of {totalLogs} logs
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handlePageChange(filters.page - 1)}
                  disabled={filters.page === 1}
                  className="p-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 text-gray-300 rounded transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                
                <div className="flex items-center space-x-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const pageNum = Math.max(1, Math.min(totalPages - 4, filters.page - 2)) + i;
                    return (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`px-3 py-1 rounded transition-colors ${
                          pageNum === filters.page
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>
                
                <button
                  onClick={() => handlePageChange(filters.page + 1)}
                  disabled={filters.page === totalPages}
                  className="p-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 text-gray-300 rounded transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Log Detail Modal */}
      {selectedLog && (
        <LogDetailModal
          log={selectedLog}
          onClose={() => setSelectedLog(null)}
        />
      )}
    </div>
  );
};

export default AuditLogViewer;