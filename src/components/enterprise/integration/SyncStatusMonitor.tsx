/**
 * SyncStatusMonitor - Component for monitoring integration synchronization
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Activity,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Calendar,
  Database,
  Cloud,
  Zap,
  Settings,
  Play,
  Pause,
  RotateCcw,
  Eye,
  Download,
  Filter,
  Search
} from 'lucide-react';

export interface SyncStatusMonitorProps {
  integrationId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface SyncStatus {
  id: string;
  integrationId: string;
  integrationName: string;
  status: 'success' | 'failed' | 'in_progress' | 'pending' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  duration?: number;
  recordsProcessed: number;
  recordsTotal: number;
  errorCount: number;
  errorMessage?: string;
  syncType: 'full' | 'incremental' | 'manual';
  triggeredBy: string;
  dataSize: number;
  throughput: number;
  conflicts: number;
  conflictResolution: 'auto' | 'manual' | 'skip';
}

interface SyncMetrics {
  totalSyncs: number;
  successfulSyncs: number;
  failedSyncs: number;
  averageDuration: number;
  averageThroughput: number;
  totalDataSynced: number;
  lastSyncTime?: Date;
  nextScheduledSync?: Date;
  successRate: number;
}

export const SyncStatusMonitor: React.FC<SyncStatusMonitorProps> = ({
  integrationId,
  autoRefresh = true,
  refreshInterval = 30000
}) => {
  const [syncStatuses, setSyncStatuses] = useState<SyncStatus[]>([]);
  const [metrics, setMetrics] = useState<SyncMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedSync, setSelectedSync] = useState<SyncStatus | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Load sync data
  const loadSyncData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusesData, metricsData] = await Promise.all([
        loadSyncStatuses(),
        loadSyncMetrics()
      ]);
      
      setSyncStatuses(statusesData);
      setMetrics(metricsData);
      setError(null);
    } catch (err) {
      setError('Failed to load sync data');
      console.error('Failed to load sync data:', err);
    } finally {
      setLoading(false);
    }
  }, [integrationId]);

  // Auto refresh
  useEffect(() => {
    loadSyncData();
    
    if (autoRefresh) {
      const interval = setInterval(loadSyncData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [loadSyncData, autoRefresh, refreshInterval]);

  // Mock data loading
  const loadSyncStatuses = async (): Promise<SyncStatus[]> => {
    return [
      {
        id: 'sync_1',
        integrationId: 'int_1',
        integrationName: 'AWS S3 Storage',
        status: 'success',
        startTime: new Date(Date.now() - 3600000),
        endTime: new Date(Date.now() - 3300000),
        duration: 300000,
        recordsProcessed: 1250,
        recordsTotal: 1250,
        errorCount: 0,
        syncType: 'incremental',
        triggeredBy: 'scheduler',
        dataSize: 52428800, // 50MB
        throughput: 174762, // bytes/second
        conflicts: 0,
        conflictResolution: 'auto'
      },
      {
        id: 'sync_2',
        integrationId: 'int_2',
        integrationName: 'PostgreSQL Database',
        status: 'in_progress',
        startTime: new Date(Date.now() - 1800000),
        recordsProcessed: 850,
        recordsTotal: 1200,
        errorCount: 2,
        syncType: 'full',
        triggeredBy: 'user_admin',
        dataSize: 31457280, // 30MB
        throughput: 17476, // bytes/second
        conflicts: 1,
        conflictResolution: 'manual'
      },
      {
        id: 'sync_3',
        integrationId: 'int_3',
        integrationName: 'Slack Notifications',
        status: 'failed',
        startTime: new Date(Date.now() - 7200000),
        endTime: new Date(Date.now() - 7020000),
        duration: 180000,
        recordsProcessed: 45,
        recordsTotal: 100,
        errorCount: 15,
        errorMessage: 'Rate limit exceeded. Please try again later.',
        syncType: 'manual',
        triggeredBy: 'user_john',
        dataSize: 1048576, // 1MB
        throughput: 5825, // bytes/second
        conflicts: 0,
        conflictResolution: 'skip'
      },
      {
        id: 'sync_4',
        integrationId: 'int_4',
        integrationName: 'OpenAI API',
        status: 'pending',
        startTime: new Date(Date.now() + 1800000),
        recordsProcessed: 0,
        recordsTotal: 500,
        errorCount: 0,
        syncType: 'incremental',
        triggeredBy: 'scheduler',
        dataSize: 10485760, // 10MB
        throughput: 0,
        conflicts: 0,
        conflictResolution: 'auto'
      }
    ];
  };

  const loadSyncMetrics = async (): Promise<SyncMetrics> => {
    return {
      totalSyncs: 156,
      successfulSyncs: 142,
      failedSyncs: 14,
      averageDuration: 245000, // 4 minutes 5 seconds
      averageThroughput: 87381, // bytes/second
      totalDataSynced: 13631488000, // ~12.7GB
      lastSyncTime: new Date(Date.now() - 3600000),
      nextScheduledSync: new Date(Date.now() + 1800000),
      successRate: 91.0
    };
  };

  // Handle retry sync
  const handleRetrySync = async (syncId: string) => {
    try {
      const sync = syncStatuses.find(s => s.id === syncId);
      if (!sync) return;

      // Create new sync with retry
      const retrySyncStatus: SyncStatus = {
        ...sync,
        id: `sync_retry_${Date.now()}`,
        status: 'in_progress',
        startTime: new Date(),
        endTime: undefined,
        duration: undefined,
        recordsProcessed: 0,
        errorCount: 0,
        errorMessage: undefined,
        triggeredBy: 'retry'
      };

      setSyncStatuses(prev => [retrySyncStatus, ...prev]);
      
      // Simulate sync progress
      setTimeout(() => {
        setSyncStatuses(prev => prev.map(s => 
          s.id === retrySyncStatus.id 
            ? { ...s, status: 'success', endTime: new Date(), duration: 120000, recordsProcessed: s.recordsTotal }
            : s
        ));
      }, 3000);
    } catch (error) {
      console.error('Failed to retry sync:', error);
    }
  };

  // Handle conflict resolution
  const handleResolveConflicts = async (syncId: string) => {
    try {
      const sync = syncStatuses.find(s => s.id === syncId);
      if (!sync) return;

      // Show conflict resolution options
      const resolution = prompt('Choose conflict resolution strategy:\n1. Auto-resolve (keep latest)\n2. Manual review\n3. Skip conflicts\n\nEnter 1, 2, or 3:');
      
      let conflictResolution: 'auto' | 'manual' | 'skip' = 'auto';
      switch (resolution) {
        case '2':
          conflictResolution = 'manual';
          break;
        case '3':
          conflictResolution = 'skip';
          break;
        default:
          conflictResolution = 'auto';
      }

      // Update sync with resolved conflicts
      setSyncStatuses(prev => prev.map(s => 
        s.id === syncId 
          ? { ...s, conflicts: 0, conflictResolution, status: 'success' }
          : s
      ));
    } catch (error) {
      console.error('Failed to resolve conflicts:', error);
    }
  };

  // Handle pause sync
  const handlePauseSync = async (syncId: string) => {
    try {
      setSyncStatuses(prev => prev.map(s => 
        s.id === syncId && s.status === 'in_progress'
          ? { ...s, status: 'cancelled', endTime: new Date() }
          : s
      ));
    } catch (error) {
      console.error('Failed to pause sync:', error);
    }
  };

  // Filter sync statuses
  const filteredSyncs = syncStatuses.filter(sync => {
    const matchesSearch = sync.integrationName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         sync.triggeredBy.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || sync.status === statusFilter;
    const matchesType = typeFilter === 'all' || sync.syncType === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  // Format bytes
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format duration
  const formatDuration = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  // Status badge component
  const StatusBadge: React.FC<{ status: SyncStatus['status'] }> = ({ status }) => {
    const statusConfig = {
      success: { icon: CheckCircle, color: 'text-green-400 bg-green-400/10', label: 'Success' },
      failed: { icon: XCircle, color: 'text-red-400 bg-red-400/10', label: 'Failed' },
      in_progress: { icon: RefreshCw, color: 'text-blue-400 bg-blue-400/10', label: 'In Progress' },
      pending: { icon: Clock, color: 'text-yellow-400 bg-yellow-400/10', label: 'Pending' },
      cancelled: { icon: AlertTriangle, color: 'text-gray-400 bg-gray-400/10', label: 'Cancelled' }
    };

    const config = statusConfig[status];
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className={`w-3 h-3 mr-1 ${status === 'in_progress' ? 'animate-spin' : ''}`} />
        {config.label}
      </span>
    );
  };

  // Progress bar component
  const ProgressBar: React.FC<{ current: number; total: number }> = ({ current, total }) => {
    const percentage = total > 0 ? (current / total) * 100 : 0;
    
    return (
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div
          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    );
  };

  // Sync details modal
  const SyncDetailsModal: React.FC = () => {
    if (!showDetails || !selectedSync) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              Sync Details: {selectedSync.integrationName}
            </h3>
            <button
              onClick={() => setShowDetails(false)}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
                <StatusBadge status={selectedSync.status} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Sync Type</label>
                <p className="text-white capitalize">{selectedSync.syncType}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Triggered By</label>
                <p className="text-white">{selectedSync.triggeredBy}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Start Time</label>
                <p className="text-white">{selectedSync.startTime.toLocaleString()}</p>
              </div>
              {selectedSync.endTime && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">End Time</label>
                  <p className="text-white">{selectedSync.endTime.toLocaleString()}</p>
                </div>
              )}
              {selectedSync.duration && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Duration</label>
                  <p className="text-white">{formatDuration(selectedSync.duration)}</p>
                </div>
              )}
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Progress</label>
                <div className="space-y-2">
                  <ProgressBar current={selectedSync.recordsProcessed} total={selectedSync.recordsTotal} />
                  <p className="text-sm text-gray-400">
                    {selectedSync.recordsProcessed} / {selectedSync.recordsTotal} records
                    ({((selectedSync.recordsProcessed / selectedSync.recordsTotal) * 100).toFixed(1)}%)
                  </p>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Data Size</label>
                <p className="text-white">{formatBytes(selectedSync.dataSize)}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Throughput</label>
                <p className="text-white">{formatBytes(selectedSync.throughput)}/s</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Errors</label>
                <p className="text-white">{selectedSync.errorCount}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Conflicts</label>
                <p className="text-white">
                  {selectedSync.conflicts} ({selectedSync.conflictResolution})
                </p>
              </div>
            </div>
          </div>

          {selectedSync.errorMessage && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">Error Message</label>
              <div className="bg-red-900/20 border border-red-500/30 rounded p-3">
                <p className="text-red-400 text-sm">{selectedSync.errorMessage}</p>
              </div>
            </div>
          )}

          <div className="flex justify-end">
            <button
              onClick={() => setShowDetails(false)}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">Error</h3>
        <p className="text-gray-400 mb-4">{error}</p>
        <button
          onClick={loadSyncData}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-900 text-white">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Sync Status Monitor</h2>
            <p className="text-gray-400">Monitor data synchronization across all integrations</p>
          </div>
          <button
            onClick={loadSyncData}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Health Status */}
      <div className="bg-gray-800 rounded-lg p-6 mb-8">
        <h3 className="text-lg font-semibold text-white mb-4">Integration Health</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-300">All systems operational</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span className="text-sm text-gray-300">2 integrations need attention</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="text-sm text-gray-300">1 integration offline</span>
          </div>
        </div>
      </div>

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Syncs</p>
                <p className="text-2xl font-bold">{metrics.totalSyncs}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Success Rate</p>
                <p className="text-2xl font-bold">{metrics.successRate.toFixed(1)}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Avg Duration</p>
                <p className="text-2xl font-bold">{formatDuration(metrics.averageDuration)}</p>
              </div>
              <Clock className="w-8 h-8 text-yellow-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Data Synced</p>
                <p className="text-2xl font-bold">{formatBytes(metrics.totalDataSynced)}</p>
              </div>
              <Database className="w-8 h-8 text-purple-500" />
            </div>
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search syncs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          >
            <option value="all">All Status</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="in_progress">In Progress</option>
            <option value="pending">Pending</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          >
            <option value="all">All Types</option>
            <option value="full">Full Sync</option>
            <option value="incremental">Incremental</option>
            <option value="manual">Manual</option>
          </select>
        </div>
      </div>

      {/* Sync Status List */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        {filteredSyncs.length === 0 ? (
          <div className="text-center py-8">
            <RefreshCw className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Sync Records Found</h3>
            <p className="text-gray-400">No sync records match your current filters.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {filteredSyncs.map(sync => (
              <div key={sync.id} className="p-6 hover:bg-gray-700/50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <Zap className="w-5 h-5 text-blue-400" />
                      <h3 className="font-semibold text-white">{sync.integrationName}</h3>
                      <StatusBadge status={sync.status} />
                      <span className="px-2 py-1 bg-gray-600 text-gray-300 text-xs rounded capitalize">
                        {sync.syncType}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4 text-sm">
                      <div>
                        <span className="text-gray-400">Started:</span>
                        <span className="text-gray-300 ml-2">{sync.startTime.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Triggered by:</span>
                        <span className="text-gray-300 ml-2">{sync.triggeredBy}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Data Size:</span>
                        <span className="text-gray-300 ml-2">{formatBytes(sync.dataSize)}</span>
                      </div>
                      {sync.duration && (
                        <div>
                          <span className="text-gray-400">Duration:</span>
                          <span className="text-gray-300 ml-2">{formatDuration(sync.duration)}</span>
                        </div>
                      )}
                    </div>

                    {/* Progress */}
                    <div className="mb-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-400">Progress</span>
                        <span className="text-sm text-gray-300">
                          {sync.recordsProcessed} / {sync.recordsTotal} records
                        </span>
                      </div>
                      <ProgressBar current={sync.recordsProcessed} total={sync.recordsTotal} />
                    </div>

                    {/* Error message */}
                    {sync.errorMessage && (
                      <div className="mt-3 p-3 bg-red-900/20 border border-red-500/30 rounded">
                        <p className="text-sm text-red-400">{sync.errorMessage}</p>
                      </div>
                    )}

                    {/* Stats */}
                    <div className="flex items-center space-x-6 text-xs text-gray-400 mt-3">
                      {sync.errorCount > 0 && (
                        <div className="flex items-center">
                          <XCircle className="w-3 h-3 mr-1 text-red-400" />
                          {sync.errorCount} errors
                        </div>
                      )}
                      {sync.conflicts > 0 && (
                        <div className="flex items-center">
                          <AlertTriangle className="w-3 h-3 mr-1 text-yellow-400" />
                          {sync.conflicts} conflicts
                        </div>
                      )}
                      <div className="flex items-center">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        {formatBytes(sync.throughput)}/s
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => {
                        setSelectedSync(sync);
                        setShowDetails(true);
                      }}
                      className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded"
                      title="View Details"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    {sync.status === 'in_progress' && (
                      <button
                        onClick={() => handlePauseSync(sync.id)}
                        className="p-2 text-gray-400 hover:text-yellow-400 hover:bg-gray-600 rounded"
                        title="Cancel Sync"
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                    )}
                    {(sync.status === 'failed' || sync.status === 'cancelled') && (
                      <button
                        onClick={() => handleRetrySync(sync.id)}
                        className="p-2 text-gray-400 hover:text-green-400 hover:bg-gray-600 rounded"
                        title="Retry Sync"
                      >
                        <RotateCcw className="w-4 h-4" />
                      </button>
                    )}
                    {sync.conflicts > 0 && (
                      <button
                        onClick={() => handleResolveConflicts(sync.id)}
                        className="p-2 text-gray-400 hover:text-yellow-400 hover:bg-gray-600 rounded"
                        title="Resolve Conflicts"
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <SyncDetailsModal />
    </div>
  );
};