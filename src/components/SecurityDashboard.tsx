import { Activity, AlertTriangle, Download, Eye, Filter, Lock, Shield, Users } from 'lucide-react';
import React, { useCallback, useEffect, useState } from 'react';
import { securityService } from '../services/securityService';
import type { SecurityAuditLog } from '../types';

export const SecurityDashboard: React.FC = () => {
  const [auditLogs, setAuditLogs] = useState<SecurityAuditLog[]>([]);
  const [securityMetrics, setSecurityMetrics] = useState<{
    totalEvents: number;
    failedLogins: number;
    rateLimitViolations: number;
    activeSessions: number;
    recentThreats?: SecurityAuditLog[];
  } | null>(null);
  const [filters, setFilters] = useState({
    action: '',
    success: '',
    userId: '',
    startDate: '',
    endDate: ''
  });
  const [showFilters, setShowFilters] = useState(false);

  const loadSecurityData = useCallback((): void => {
    // Apply filters
    const filterObj: Record<string, unknown> = {};
    if (filters.action.length > 0) filterObj.action = filters.action;
    if (filters.success.length > 0) filterObj.success = filters.success === 'true';
    if (filters.userId.length > 0) filterObj.userId = filters.userId;
    if (filters.startDate.length > 0) filterObj.startDate = new Date(filters.startDate);
    if (filters.endDate.length > 0) filterObj.endDate = new Date(filters.endDate);

    const logs = securityService.getAuditLogs(filterObj);
    setAuditLogs(logs);
    
    const metrics = securityService.getSecurityMetrics();
    setSecurityMetrics(metrics);
  }, [filters]);

  useEffect(() => {
    loadSecurityData();
  }, [loadSecurityData]);



  const exportAuditLogs = (): void => {
    const csvContent = [
      ['Timestamp', 'User ID', 'Action', 'Resource', 'Success', 'IP Address', 'User Agent'].join(','),
      ...auditLogs.map(log => [
        log.timestamp.toISOString(),
        log.userId,
        log.action,
        log.resource,
        log.success.toString(),
        log.ipAddress,
        `"${log.userAgent}"`
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `security_audit_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center">
            <Shield className="text-blue-400 mr-3" size={28} />
            Security Dashboard
          </h2>
          <p className="text-gray-400">Monitor security events and compliance</p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
          >
            <Filter size={16} />
            <span>Filters</span>
          </button>
          <button
            onClick={exportAuditLogs}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
          >
            <Download size={16} />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Security Metrics */}
      {securityMetrics != null && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <SecurityMetricCard
            title="Total Events"
            value={securityMetrics.totalEvents}
            icon={<Activity className="text-blue-400" size={24} />}
            trend="neutral"
          />
          <SecurityMetricCard
            title="Failed Logins"
            value={securityMetrics.failedLogins}
            icon={<AlertTriangle className="text-red-400" size={24} />}
            trend="warning"
          />
          <SecurityMetricCard
            title="Rate Limit Violations"
            value={securityMetrics.rateLimitViolations}
            icon={<Lock className="text-yellow-400" size={24} />}
            trend="warning"
          />
          <SecurityMetricCard
            title="Active Sessions"
            value={securityMetrics.activeSessions}
            icon={<Users className="text-emerald-400" size={24} />}
            trend="positive"
          />
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Filter Audit Logs</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Action</label>
              <select
                value={filters.action}
                onChange={(e) => setFilters({ ...filters, action: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
              >
                <option value="">All Actions</option>
                <option value="login_success">Login Success</option>
                <option value="login_failed">Login Failed</option>
                <option value="document_read">Document Read</option>
                <option value="document_write">Document Write</option>
                <option value="document_delete">Document Delete</option>
                <option value="rate_limit_exceeded">Rate Limit Exceeded</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">Success</label>
              <select
                value={filters.success}
                onChange={(e) => setFilters({ ...filters, success: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
              >
                <option value="">All</option>
                <option value="true">Success</option>
                <option value="false">Failed</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">User ID</label>
              <input
                type="text"
                value={filters.userId}
                onChange={(e) => setFilters({ ...filters, userId: e.target.value })}
                placeholder="Filter by user..."
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">Start Date</label>
              <input
                type="date"
                value={filters.startDate}
                onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">End Date</label>
              <input
                type="date"
                value={filters.endDate}
                onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
          </div>
        </div>
      )}

      {/* Recent Threats */}
      {(securityMetrics?.recentThreats?.length ?? 0) > 0 && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <AlertTriangle className="text-red-400 mr-2" size={20} />
            Recent Security Threats
          </h3>
          <div className="space-y-3">
            {(securityMetrics.recentThreats ?? []).slice(0, 5).map((threat: SecurityAuditLog, index: number) => (
              <div key={index} className="flex items-center justify-between p-3 bg-red-900/20 border border-red-800 rounded-lg">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="text-red-400" size={16} />
                  <div>
                    <div className="text-white font-medium">{threat.action}</div>
                    <div className="text-gray-400 text-sm">{threat.userId} • {threat.ipAddress}</div>
                  </div>
                </div>
                <div className="text-gray-400 text-sm">
                  {threat.timestamp.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Audit Log Table */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Eye className="text-blue-400 mr-2" size={20} />
          Audit Log ({auditLogs.length} events)
        </h3>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left text-gray-400 py-3 px-4">Timestamp</th>
                <th className="text-left text-gray-400 py-3 px-4">User</th>
                <th className="text-left text-gray-400 py-3 px-4">Action</th>
                <th className="text-left text-gray-400 py-3 px-4">Resource</th>
                <th className="text-left text-gray-400 py-3 px-4">Status</th>
                <th className="text-left text-gray-400 py-3 px-4">IP Address</th>
                <th className="text-left text-gray-400 py-3 px-4">Details</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.slice(0, 50).map((log, index) => (
                <tr key={index} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                  <td className="py-3 px-4 text-gray-300">
                    {log.timestamp.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-gray-300">
                    {log.userId}
                  </td>
                  <td className="py-3 px-4 text-gray-300">
                    {log.action}
                  </td>
                  <td className="py-3 px-4 text-gray-300">
                    {log.resource}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      log.success 
                        ? 'bg-emerald-600/20 text-emerald-400' 
                        : 'bg-red-600/20 text-red-400'
                    }`}>
                      {log.success ? 'Success' : 'Failed'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-300">
                    {log.ipAddress}
                  </td>
                  <td className="py-3 px-4 text-gray-300">
                    {(log.details != null && Object.keys(log.details).length > 0) && (
                      <button
                        onClick={() => {
                          // Show details modal
                          alert(JSON.stringify(log.details, null, 2));
                        }}
                        className="text-blue-400 hover:text-blue-300 text-xs"
                      >
                        View Details
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {auditLogs.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            No audit logs found matching the current filters.
          </div>
        )}
      </div>

      {/* Compliance Status */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Compliance Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ComplianceCard
            title="GDPR Compliance"
            status="compliant"
            description="Data protection and privacy requirements met"
          />
          <ComplianceCard
            title="SOC 2 Type II"
            status="compliant"
            description="Security controls and procedures verified"
          />
          <ComplianceCard
            title="ISO 27001"
            status="in-progress"
            description="Information security management system implementation"
          />
        </div>
      </div>
    </div>
  );
};

interface SecurityMetricCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  trend: 'positive' | 'negative' | 'warning' | 'neutral';
}

const SecurityMetricCard: React.FC<SecurityMetricCardProps> = ({ title, value, icon }) => {

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
        </div>
        <div className="p-3 bg-gray-700 rounded-lg">
          {icon}
        </div>
      </div>
    </div>
  );
};

interface ComplianceCardProps {
  title: string;
  status: 'compliant' | 'non-compliant' | 'in-progress';
  description: string;
}

const ComplianceCard: React.FC<ComplianceCardProps> = ({ title, status, description }) => {
  const statusConfig = {
    compliant: { color: 'text-emerald-400', bg: 'bg-emerald-600/20', text: 'Compliant' },
    'non-compliant': { color: 'text-red-400', bg: 'bg-red-600/20', text: 'Non-Compliant' },
    'in-progress': { color: 'text-yellow-400', bg: 'bg-yellow-600/20', text: 'In Progress' }
  };

  const config = statusConfig[status];

  return (
    <div className="border border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-white font-medium">{title}</h4>
        <span className={`px-2 py-1 rounded-full text-xs ${config.bg} ${config.color}`}>
          {config.text}
        </span>
      </div>
      <p className="text-gray-400 text-sm">{description}</p>
    </div>
  );
};