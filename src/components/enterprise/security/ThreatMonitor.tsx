/**
 * Threat Monitor - Security threat detection and alert management
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  AlertTriangle,
  AlertCircle,
  Eye,
  EyeOff,
  Clock,
  User,
  Activity,
  CheckCircle,
  XCircle,
  RefreshCw,
  Bell,
  BellOff,
  Filter,
  TrendingUp,
  Zap,
  Lock
} from 'lucide-react';
import { SecurityAlert, ThreatDetection, SecurityAction } from '../../../types/security';
import { securityDashboardService } from '../../../services/securityDashboardService';

export interface ThreatMonitorProps {
  onSecurityAction?: (action: SecurityAction) => void;
  onAlertAction?: (alertId: string, action: 'resolve' | 'investigate' | 'escalate') => void;
  showAdminControls?: boolean;
}

interface ThreatFilters {
  severity?: string;
  type?: string;
  resolved?: boolean;
  timeRange?: { start: Date; end: Date };
}

export const ThreatMonitor: React.FC<ThreatMonitorProps> = ({
  onSecurityAction,
  onAlertAction,
  showAdminControls = true
}) => {
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [threats, setThreats] = useState<ThreatDetection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<ThreatFilters>({});
  const [selectedAlert, setSelectedAlert] = useState<SecurityAlert | null>(null);
  const [selectedThreat, setSelectedThreat] = useState<ThreatDetection | null>(null);
  const [realTimeEnabled, setRealTimeEnabled] = useState(true);
  const [autoMitigationEnabled, setAutoMitigationEnabled] = useState(false);
  const [threatResponseMode, setThreatResponseMode] = useState<'manual' | 'assisted' | 'automatic'>('manual');

  // Load security alerts and threats
  const loadSecurityData = useCallback(async () => {
    try {
      setError(null);
      const [alertData, securityMetrics] = await Promise.all([
        securityDashboardService.getSecurityAlerts(filters),
        securityDashboardService.getSecurityMetrics()
      ]);
      
      setAlerts(alertData);
      // Mock threat detection data - in real implementation, this would come from the service
      setThreats(generateMockThreats());
    } catch (err) {
      setError('Failed to load security data');
      console.error('Security data loading error:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Handle alert resolution
  const handleResolveAlert = async (alertId: string) => {
    try {
      const success = await securityDashboardService.performSecurityAction({
        type: 'resolve_alert',
        payload: { alertId, resolvedBy: 'admin', timestamp: new Date() }
      });
      
      if (success) {
        onSecurityAction?.({ type: 'resolve_alert', payload: { alertId } });
        onAlertAction?.(alertId, 'resolve');
        await loadSecurityData(); // Refresh data
      } else {
        setError('Failed to resolve alert');
      }
    } catch (err) {
      setError('Error resolving alert');
      console.error('Alert resolution error:', err);
    }
  };

  // Handle threat escalation
  const handleEscalateAlert = async (alertId: string) => {
    try {
      const success = await securityDashboardService.performSecurityAction({
        type: 'escalate_alert',
        payload: { alertId, escalatedBy: 'admin', timestamp: new Date() }
      });
      
      if (success) {
        onSecurityAction?.({ type: 'escalate_alert', payload: { alertId } });
        onAlertAction?.(alertId, 'escalate');
        await loadSecurityData();
      } else {
        setError('Failed to escalate alert');
      }
    } catch (err) {
      setError('Error escalating alert');
      console.error('Alert escalation error:', err);
    }
  };

  // Handle threat mitigation
  const handleMitigateThreat = async (threatId: string, mitigationAction: string) => {
    try {
      const success = await securityDashboardService.performSecurityAction({
        type: 'mitigate_threat',
        payload: { 
          threatId, 
          action: mitigationAction,
          mitigatedBy: 'admin',
          timestamp: new Date()
        }
      });
      
      if (success) {
        onSecurityAction?.({ type: 'mitigate_threat', payload: { threatId, action: mitigationAction } });
        await loadSecurityData();
      } else {
        setError('Failed to mitigate threat');
      }
    } catch (err) {
      setError('Error mitigating threat');
      console.error('Threat mitigation error:', err);
    }
  };

  // Handle bulk security actions
  const handleBulkSecurityAction = async (action: 'resolve_all' | 'escalate_critical' | 'auto_mitigate') => {
    try {
      let targetAlerts: SecurityAlert[] = [];
      
      switch (action) {
        case 'resolve_all':
          targetAlerts = alerts.filter(a => !a.resolved && a.severity !== 'critical');
          break;
        case 'escalate_critical':
          targetAlerts = alerts.filter(a => !a.resolved && a.severity === 'critical');
          break;
        case 'auto_mitigate':
          targetAlerts = alerts.filter(a => !a.resolved && ['low', 'medium'].includes(a.severity));
          break;
      }

      for (const alert of targetAlerts) {
        if (action === 'resolve_all' || action === 'auto_mitigate') {
          await handleResolveAlert(alert.id);
        } else if (action === 'escalate_critical') {
          await handleEscalateAlert(alert.id);
        }
      }

      // Log bulk action
      onSecurityAction?.({
        type: 'bulk_security_action',
        payload: {
          action,
          alertCount: targetAlerts.length,
          timestamp: new Date()
        }
      });

    } catch (err) {
      setError(`Failed to perform bulk action: ${action}`);
      console.error('Bulk security action error:', err);
    }
  };

  // Generate mock threat detection data
  const generateMockThreats = (): ThreatDetection[] => {
    const now = new Date();
    return [
      {
        id: 'threat_1',
        type: 'brute_force',
        severity: 'high',
        description: 'Multiple failed login attempts detected from IP 192.168.1.50',
        timestamp: new Date(now.getTime() - 30 * 60 * 1000),
        affectedUsers: ['user_123', 'user_456'],
        mitigationSteps: [
          'Block suspicious IP address',
          'Notify affected users',
          'Enable additional authentication factors'
        ],
        status: 'investigating'
      },
      {
        id: 'threat_2',
        type: 'anomalous_behavior',
        severity: 'medium',
        description: 'Unusual access pattern detected for user account',
        timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000),
        affectedUsers: ['user_789'],
        mitigationSteps: [
          'Review user activity logs',
          'Verify user identity',
          'Monitor ongoing activity'
        ],
        status: 'detected'
      },
      {
        id: 'threat_3',
        type: 'privilege_escalation',
        severity: 'critical',
        description: 'Unauthorized attempt to access admin functions',
        timestamp: new Date(now.getTime() - 45 * 60 * 1000),
        affectedUsers: ['user_999'],
        mitigationSteps: [
          'Immediately revoke elevated permissions',
          'Audit permission changes',
          'Investigate source of escalation'
        ],
        status: 'mitigated'
      }
    ];
  };

  // Get severity color
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-900';
      case 'high': return 'text-orange-400 bg-orange-900';
      case 'medium': return 'text-yellow-400 bg-yellow-900';
      case 'low': return 'text-blue-400 bg-blue-900';
      default: return 'text-gray-400 bg-gray-900';
    }
  };

  // Get threat type icon
  const getThreatTypeIcon = (type: string) => {
    switch (type) {
      case 'brute_force':
        return <Lock className="w-5 h-5" />;
      case 'anomalous_behavior':
        return <TrendingUp className="w-5 h-5" />;
      case 'privilege_escalation':
        return <Zap className="w-5 h-5" />;
      case 'data_exfiltration':
        return <Shield className="w-5 h-5" />;
      default:
        return <AlertTriangle className="w-5 h-5" />;
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'detected': return 'text-red-400';
      case 'investigating': return 'text-yellow-400';
      case 'mitigated': return 'text-blue-400';
      case 'resolved': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  // Format threat type
  const formatThreatType = (type: string) => {
    return type
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Initialize data loading
  useEffect(() => {
    loadSecurityData();
  }, [loadSecurityData]);

  // Real-time updates
  useEffect(() => {
    if (!realTimeEnabled) return;

    const interval = setInterval(() => {
      loadSecurityData();
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, [realTimeEnabled, loadSecurityData]);

  // Alert detail modal
  const AlertDetailModal = ({ alert, onClose }: { alert: SecurityAlert; onClose: () => void }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Alert Details</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <span className={`px-3 py-1 rounded text-sm font-medium ${getSeverityColor(alert.severity)} bg-opacity-20`}>
              {alert.severity.toUpperCase()}
            </span>
            <span className="px-3 py-1 bg-gray-700 text-gray-300 rounded text-sm">
              {formatThreatType(alert.type)}
            </span>
            {alert.resolved && (
              <span className="px-3 py-1 bg-green-900 text-green-200 rounded text-sm">
                RESOLVED
              </span>
            )}
          </div>
          
          <div>
            <h4 className="text-white font-medium mb-2">Message</h4>
            <p className="text-gray-300">{alert.message}</p>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-white font-medium mb-2">Timestamp</h4>
              <p className="text-gray-300">{alert.timestamp.toLocaleString()}</p>
            </div>
            <div>
              <h4 className="text-white font-medium mb-2">User ID</h4>
              <p className="text-gray-300">{alert.userId || 'N/A'}</p>
            </div>
          </div>
          
          {alert.details && Object.keys(alert.details).length > 0 && (
            <div>
              <h4 className="text-white font-medium mb-2">Additional Details</h4>
              <pre className="bg-gray-900 p-3 rounded text-sm text-gray-300 overflow-x-auto">
                {JSON.stringify(alert.details, null, 2)}
              </pre>
            </div>
          )}
          
          {!alert.resolved && (
            <div className="flex space-x-3 pt-4 border-t border-gray-700">
              <button
                onClick={() => {
                  handleResolveAlert(alert.id);
                  onClose();
                }}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
              >
                Resolve Alert
              </button>
              <button
                onClick={() => {
                  onAlertAction?.(alert.id, 'investigate');
                  onClose();
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
              >
                Investigate
              </button>
            </div>
          )}
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
            <span className="text-gray-300">Loading threat data...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Threat Overview */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Shield className="w-6 h-6 text-red-400" />
            <h2 className="text-xl font-semibold text-white">Threat Monitor</h2>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${realTimeEnabled ? 'bg-green-400' : 'bg-gray-400'}`}></div>
              <span className="text-sm text-gray-400">
                {realTimeEnabled ? 'Live' : 'Paused'}
              </span>
            </div>
            {showAdminControls && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-400">Response:</span>
                <select
                  value={threatResponseMode}
                  onChange={(e) => setThreatResponseMode(e.target.value as any)}
                  className="px-2 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="manual">Manual</option>
                  <option value="assisted">Assisted</option>
                  <option value="automatic">Automatic</option>
                </select>
              </div>
            )}
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setRealTimeEnabled(!realTimeEnabled)}
              className={`p-2 rounded-lg transition-colors ${
                realTimeEnabled ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {realTimeEnabled ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
            </button>
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
                onClick={() => setAutoMitigationEnabled(!autoMitigationEnabled)}
                className={`p-2 rounded-lg transition-colors ${
                  autoMitigationEnabled ? 'bg-orange-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
                title="Toggle automatic threat mitigation"
              >
                <Zap className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={loadSecurityData}
              className="p-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Threat Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Active Threats</p>
                <p className="text-2xl font-bold text-red-400">
                  {threats.filter(t => t.status === 'detected' || t.status === 'investigating').length}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </div>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Critical Alerts</p>
                <p className="text-2xl font-bold text-orange-400">
                  {alerts.filter(a => a.severity === 'critical' && !a.resolved).length}
                </p>
              </div>
              <AlertCircle className="w-8 h-8 text-orange-400" />
            </div>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Mitigated</p>
                <p className="text-2xl font-bold text-blue-400">
                  {threats.filter(t => t.status === 'mitigated').length}
                </p>
              </div>
              <Shield className="w-8 h-8 text-blue-400" />
            </div>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Resolved</p>
                <p className="text-2xl font-bold text-green-400">
                  {threats.filter(t => t.status === 'resolved').length}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-400" />
            </div>
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="bg-gray-700 rounded-lg p-4 mb-6 space-y-4">
            <h3 className="text-sm font-medium text-gray-300">Filter Threats & Alerts</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Severity</label>
                <select
                  value={filters.severity || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, severity: e.target.value || undefined }))}
                  className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">All severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Type</label>
                <select
                  value={filters.type || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value || undefined }))}
                  className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">All types</option>
                  <option value="brute_force">Brute Force</option>
                  <option value="anomalous_behavior">Anomalous Behavior</option>
                  <option value="privilege_escalation">Privilege Escalation</option>
                  <option value="data_exfiltration">Data Exfiltration</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={() => setFilters({})}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors"
                >
                  Clear Filters
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Administrative Controls Panel */}
        {showAdminControls && (
          <div className="bg-red-900 bg-opacity-20 border border-red-700 rounded-lg p-4 mb-6 space-y-4">
            <div className="flex items-center space-x-3">
              <Shield className="w-5 h-5 text-red-400" />
              <h3 className="text-sm font-medium text-red-300">Threat Response Controls</h3>
              <span className={`px-2 py-1 rounded text-xs ${
                autoMitigationEnabled ? 'bg-orange-800 text-orange-200' : 'bg-gray-800 text-gray-300'
              }`}>
                Auto-mitigation: {autoMitigationEnabled ? 'ON' : 'OFF'}
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="block text-sm text-red-300">Bulk Actions</label>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleBulkSecurityAction('resolve_all')}
                    className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors"
                  >
                    Resolve Low/Medium
                  </button>
                  <button
                    onClick={() => handleBulkSecurityAction('escalate_critical')}
                    className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
                  >
                    Escalate Critical
                  </button>
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="block text-sm text-red-300">Auto Response</label>
                <button
                  onClick={() => handleBulkSecurityAction('auto_mitigate')}
                  disabled={!autoMitigationEnabled}
                  className="px-3 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 text-white rounded text-sm transition-colors"
                >
                  Auto-Mitigate Threats
                </button>
              </div>
              
              <div className="space-y-2">
                <label className="block text-sm text-red-300">System Status</label>
                <div className="text-xs text-red-400">
                  Response Mode: <span className="text-white">{threatResponseMode}</span><br/>
                  Active Threats: <span className="text-white">{threats.filter(t => ['detected', 'investigating'].includes(t.status)).length}</span>
                </div>
              </div>
            </div>
            
            <div className="bg-red-800 bg-opacity-30 rounded p-3">
              <p className="text-sm text-red-200">
                <strong>Warning:</strong> Administrative actions will be logged and may affect system security posture.
                Use with caution and ensure proper authorization.
              </p>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-700 rounded-lg">
            <p className="text-red-200">{error}</p>
          </div>
        )}
      </div>

      {/* Active Threats */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Active Threats</h3>
        <div className="space-y-4">
          {threats.map((threat) => (
            <div key={threat.id} className={`p-4 rounded-lg border ${getSeverityColor(threat.severity)} bg-opacity-10 border-opacity-30`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    {getThreatTypeIcon(threat.type)}
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(threat.severity)} bg-opacity-20`}>
                      {threat.severity.toUpperCase()}
                    </span>
                    <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
                      {formatThreatType(threat.type)}
                    </span>
                    <span className={`text-sm ${getStatusColor(threat.status)}`}>
                      {threat.status.charAt(0).toUpperCase() + threat.status.slice(1)}
                    </span>
                  </div>
                  
                  <p className="text-white font-medium mb-2">{threat.description}</p>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-400 mb-3">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{threat.timestamp.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <User className="w-4 h-4" />
                      <span>{threat.affectedUsers.length} user(s) affected</span>
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-400 mb-1">Mitigation Steps:</p>
                    <ul className="text-sm text-gray-300 space-y-1">
                      {threat.mitigationSteps.map((step, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <span className="text-gray-500">•</span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
                
                {/* Threat Actions */}
                {showAdminControls && threat.status !== 'resolved' && (
                  <div className="flex items-center space-x-2 mt-4 pt-4 border-t border-gray-700">
                    <button
                      onClick={() => setSelectedThreat(threat)}
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                    >
                      View Details
                    </button>
                    {threat.status === 'detected' && (
                      <button
                        onClick={() => handleMitigateThreat(threat.id, 'investigate')}
                        className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white rounded text-sm transition-colors"
                      >
                        Investigate
                      </button>
                    )}
                    {threat.status === 'investigating' && (
                      <button
                        onClick={() => handleMitigateThreat(threat.id, 'mitigate')}
                        className="px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white rounded text-sm transition-colors"
                      >
                        Mitigate
                      </button>
                    )}
                    {threat.status === 'mitigated' && (
                      <button
                        onClick={() => handleMitigateThreat(threat.id, 'resolve')}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors"
                      >
                        Mark Resolved
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {threats.length === 0 && (
            <div className="text-center py-8">
              <Shield className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">No active threats detected</p>
            </div>
          )}
        </div>
      </div>

      {/* Security Alerts */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Security Alerts</h3>
        <div className="space-y-3">
          {alerts.slice(0, 10).map((alert) => (
            <div key={alert.id} className={`p-3 rounded-lg border ${getSeverityColor(alert.severity)} bg-opacity-10 border-opacity-30`}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-1">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)} bg-opacity-20`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
                      {formatThreatType(alert.type)}
                    </span>
                    {alert.resolved && (
                      <span className="px-2 py-1 bg-green-900 text-green-200 rounded text-xs">
                        RESOLVED
                      </span>
                    )}
                  </div>
                  <p className="text-white font-medium mb-1">{alert.message}</p>
                  <p className="text-sm text-gray-400">{alert.timestamp.toLocaleString()}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedAlert(alert)}
                    className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors"
                    title="View alert details"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  {!alert.resolved && showAdminControls && (
                    <>
                      <button
                        onClick={() => handleResolveAlert(alert.id)}
                        className="px-2 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors"
                      >
                        Resolve
                      </button>
                      {alert.severity === 'critical' && (
                        <button
                          onClick={() => handleEscalateAlert(alert.id)}
                          className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
                        >
                          Escalate
                        </button>
                      )}
                    </>
                  )}
                  {!alert.resolved && !showAdminControls && (
                    <button
                      onClick={() => handleResolveAlert(alert.id)}
                      className="px-2 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors"
                    >
                      Resolve
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {alerts.length === 0 && (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">No security alerts</p>
            </div>
          )}
        </div>
      </div>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <AlertDetailModal
          alert={selectedAlert}
          onClose={() => setSelectedAlert(null)}
        />
      )}

      {/* Threat Detail Modal */}
      {selectedThreat && (
        <ThreatDetailModal
          threat={selectedThreat}
          onClose={() => setSelectedThreat(null)}
          onAction={handleMitigateThreat}
        />
      )}
    </div>
  );
};

// Threat Detail Modal Component
const ThreatDetailModal = ({ 
  threat, 
  onClose, 
  onAction 
}: { 
  threat: ThreatDetection; 
  onClose: () => void;
  onAction: (threatId: string, action: string) => void;
}) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-gray-800 rounded-lg p-6 max-w-3xl w-full mx-4 max-h-[80vh] overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Threat Analysis</h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
        >
          <XCircle className="w-5 h-5" />
        </button>
      </div>
      
      <div className="space-y-6">
        {/* Threat Overview */}
        <div className="bg-gray-700 rounded-lg p-4">
          <div className="flex items-center space-x-3 mb-3">
            <span className={`px-3 py-1 rounded text-sm font-medium ${
              threat.severity === 'critical' ? 'bg-red-900 text-red-200' :
              threat.severity === 'high' ? 'bg-orange-900 text-orange-200' :
              threat.severity === 'medium' ? 'bg-yellow-900 text-yellow-200' :
              'bg-blue-900 text-blue-200'
            }`}>
              {threat.severity.toUpperCase()}
            </span>
            <span className="px-3 py-1 bg-gray-600 text-gray-300 rounded text-sm">
              {threat.type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
            </span>
            <span className={`px-3 py-1 rounded text-sm ${
              threat.status === 'detected' ? 'bg-red-800 text-red-200' :
              threat.status === 'investigating' ? 'bg-yellow-800 text-yellow-200' :
              threat.status === 'mitigated' ? 'bg-blue-800 text-blue-200' :
              'bg-green-800 text-green-200'
            }`}>
              {threat.status.charAt(0).toUpperCase() + threat.status.slice(1)}
            </span>
          </div>
          
          <h4 className="text-white font-medium mb-2">Description</h4>
          <p className="text-gray-300 mb-4">{threat.description}</p>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h5 className="text-white font-medium mb-1">Detection Time</h5>
              <p className="text-gray-300">{threat.timestamp.toLocaleString()}</p>
            </div>
            <div>
              <h5 className="text-white font-medium mb-1">Affected Users</h5>
              <p className="text-gray-300">{threat.affectedUsers.length} user(s)</p>
            </div>
          </div>
        </div>

        {/* Affected Users */}
        <div className="bg-gray-700 rounded-lg p-4">
          <h4 className="text-white font-medium mb-3">Affected Users</h4>
          <div className="space-y-2">
            {threat.affectedUsers.map((userId, index) => (
              <div key={index} className="flex items-center justify-between bg-gray-600 rounded p-2">
                <span className="text-gray-300">{userId}</span>
                <div className="flex space-x-2">
                  <button className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded">
                    View Profile
                  </button>
                  <button className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded">
                    Block User
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Mitigation Steps */}
        <div className="bg-gray-700 rounded-lg p-4">
          <h4 className="text-white font-medium mb-3">Recommended Mitigation Steps</h4>
          <div className="space-y-2">
            {threat.mitigationSteps.map((step, index) => (
              <div key={index} className="flex items-start space-x-3 bg-gray-600 rounded p-3">
                <span className="text-blue-400 font-bold">{index + 1}.</span>
                <span className="text-gray-300 flex-1">{step}</span>
                <button 
                  onClick={() => onAction(threat.id, `step_${index + 1}`)}
                  className="px-2 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded"
                >
                  Execute
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-3 pt-4 border-t border-gray-700">
          {threat.status === 'detected' && (
            <button
              onClick={() => {
                onAction(threat.id, 'investigate');
                onClose();
              }}
              className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded transition-colors"
            >
              Start Investigation
            </button>
          )}
          {threat.status === 'investigating' && (
            <button
              onClick={() => {
                onAction(threat.id, 'mitigate');
                onClose();
              }}
              className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded transition-colors"
            >
              Apply Mitigation
            </button>
          )}
          {threat.status === 'mitigated' && (
            <button
              onClick={() => {
                onAction(threat.id, 'resolve');
                onClose();
              }}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
            >
              Mark as Resolved
            </button>
          )}
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
);

export default ThreatMonitor;