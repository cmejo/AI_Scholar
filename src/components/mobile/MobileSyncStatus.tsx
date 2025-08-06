import React, { useState, useEffect } from 'react';
import { 
  Wifi, 
  WifiOff, 
  RefreshCw, 
  AlertTriangle, 
  Check, 
  X, 
  Clock,
  Database,
  Smartphone,
  Cloud
} from 'lucide-react';
import { mobileSyncService, SyncStats, SyncConflict } from '../../services/mobileSyncService';

interface MobileSyncStatusProps {
  isVisible: boolean;
  onClose: () => void;
}

export const MobileSyncStatus: React.FC<MobileSyncStatusProps> = ({
  isVisible,
  onClose
}) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [syncStats, setSyncStats] = useState<SyncStats>({
    totalItems: 0,
    pendingSync: 0,
    conflicts: 0,
    lastSyncTime: 0,
    syncInProgress: false
  });
  const [conflicts, setConflicts] = useState<SyncConflict[]>([]);
  const [showConflicts, setShowConflicts] = useState(false);

  useEffect(() => {
    // Load initial data
    loadSyncStats();
    loadConflicts();

    // Set up event listeners
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    const handleSyncStarted = () => {
      setSyncStats(prev => ({ ...prev, syncInProgress: true }));
    };
    const handleSyncCompleted = () => {
      loadSyncStats();
    };
    const handleConflictDetected = () => {
      loadConflicts();
      loadSyncStats();
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    mobileSyncService.on('syncStarted', handleSyncStarted);
    mobileSyncService.on('syncCompleted', handleSyncCompleted);
    mobileSyncService.on('conflictDetected', handleConflictDetected);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      mobileSyncService.off('syncStarted', handleSyncStarted);
      mobileSyncService.off('syncCompleted', handleSyncCompleted);
      mobileSyncService.off('conflictDetected', handleConflictDetected);
    };
  }, []);

  const loadSyncStats = async () => {
    try {
      const stats = await mobileSyncService.getSyncStats();
      setSyncStats(stats);
    } catch (error) {
      console.error('Failed to load sync stats:', error);
    }
  };

  const loadConflicts = async () => {
    try {
      const conflictList = await mobileSyncService.getConflicts();
      setConflicts(conflictList);
    } catch (error) {
      console.error('Failed to load conflicts:', error);
    }
  };

  const handleManualSync = async () => {
    if (!isOnline) return;
    
    try {
      await mobileSyncService.performSync();
    } catch (error) {
      console.error('Manual sync failed:', error);
    }
  };

  const handleResolveConflict = async (conflictId: string, resolution: 'local' | 'remote' | 'merge') => {
    try {
      await mobileSyncService.resolveConflict(conflictId, resolution);
      loadConflicts();
      loadSyncStats();
    } catch (error) {
      console.error('Failed to resolve conflict:', error);
    }
  };

  const formatLastSyncTime = (timestamp: number) => {
    if (!timestamp) return 'Never';
    
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const getConnectionIcon = () => {
    if (isOnline) {
      return <Wifi className="text-green-400" size={20} />;
    } else {
      return <WifiOff className="text-red-400" size={20} />;
    }
  };

  const getSyncStatusIcon = () => {
    if (syncStats.syncInProgress) {
      return <RefreshCw className="text-blue-400 animate-spin" size={20} />;
    } else if (syncStats.conflicts > 0) {
      return <AlertTriangle className="text-yellow-400" size={20} />;
    } else if (syncStats.pendingSync > 0) {
      return <Clock className="text-orange-400" size={20} />;
    } else {
      return <Check className="text-green-400" size={20} />;
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-gray-800 rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Database className="text-blue-400" size={20} />
            <h2 className="text-lg font-semibold text-white">Sync Status</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Close sync status"
          >
            <X size={18} />
          </button>
        </div>

        {/* Connection Status */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              {getConnectionIcon()}
              <span className="text-white font-medium">
                {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
            {isOnline && (
              <button
                onClick={handleManualSync}
                disabled={syncStats.syncInProgress}
                className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-3 py-1 rounded-lg text-sm transition-colors"
              >
                <RefreshCw size={14} className={syncStats.syncInProgress ? 'animate-spin' : ''} />
                <span>Sync Now</span>
              </button>
            )}
          </div>
          
          <div className="text-sm text-gray-400">
            {isOnline ? 'Connected to server' : 'Working offline - changes will sync when online'}
          </div>
        </div>

        {/* Sync Statistics */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center space-x-2 mb-3">
            {getSyncStatusIcon()}
            <span className="text-white font-medium">Sync Status</span>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-3">
            <div className="bg-gray-700/50 rounded-lg p-3">
              <div className="text-2xl font-bold text-white">{syncStats.totalItems}</div>
              <div className="text-xs text-gray-400">Total Items</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-3">
              <div className="text-2xl font-bold text-orange-400">{syncStats.pendingSync}</div>
              <div className="text-xs text-gray-400">Pending Sync</div>
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Last sync:</span>
            <span className="text-white">{formatLastSyncTime(syncStats.lastSyncTime)}</span>
          </div>
        </div>

        {/* Conflicts Section */}
        {syncStats.conflicts > 0 && (
          <div className="p-4 border-b border-gray-700">
            <button
              onClick={() => setShowConflicts(!showConflicts)}
              className="flex items-center justify-between w-full text-left"
            >
              <div className="flex items-center space-x-2">
                <AlertTriangle className="text-yellow-400" size={18} />
                <span className="text-white font-medium">
                  {syncStats.conflicts} Conflict{syncStats.conflicts !== 1 ? 's' : ''}
                </span>
              </div>
              <div className="text-gray-400">
                {showConflicts ? '▼' : '▶'}
              </div>
            </button>

            {showConflicts && (
              <div className="mt-3 space-y-2">
                {conflicts.map((conflict) => (
                  <div key={conflict.id} className="bg-gray-700/50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-sm font-medium text-white">
                        {conflict.localData.type} conflict
                      </div>
                      <div className="text-xs text-gray-400">
                        {new Date(conflict.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                    
                    <div className="text-xs text-gray-400 mb-3">
                      Local and remote versions differ
                    </div>

                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleResolveConflict(conflict.id, 'local')}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs transition-colors"
                      >
                        <Smartphone size={12} className="inline mr-1" />
                        Keep Local
                      </button>
                      <button
                        onClick={() => handleResolveConflict(conflict.id, 'remote')}
                        className="flex-1 bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs transition-colors"
                      >
                        <Cloud size={12} className="inline mr-1" />
                        Keep Remote
                      </button>
                      <button
                        onClick={() => handleResolveConflict(conflict.id, 'merge')}
                        className="flex-1 bg-purple-600 hover:bg-purple-700 text-white px-2 py-1 rounded text-xs transition-colors"
                      >
                        Merge
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Storage Info */}
        <div className="p-4">
          <div className="text-sm text-gray-400 mb-2">Local Storage</div>
          <div className="bg-gray-700/50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white text-sm">Cached Documents</span>
              <span className="text-gray-400 text-sm">~2.3 MB</span>
            </div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-white text-sm">Offline Data</span>
              <span className="text-gray-400 text-sm">~850 KB</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-white text-sm">Total Used</span>
              <span className="text-gray-400 text-sm">~3.2 MB</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};