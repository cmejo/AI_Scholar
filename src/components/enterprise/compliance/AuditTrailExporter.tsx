/**
 * AuditTrailExporter - Component for audit trail export and compliance reporting
 */
import React, { useState, useCallback } from 'react';
import {
  Download,
  FileText,
  Calendar,
  Filter,
  Search,
  Shield,
  CheckCircle,
  AlertTriangle,
  Clock,
  User,
  Activity,
  Database,
  Settings,
  Eye,
  Lock,
  Unlock,
  RefreshCw
} from 'lucide-react';

export interface AuditTrailExporterProps {
  onExport?: (data: any) => void;
}

interface AuditEvent {
  id: string;
  timestamp: Date;
  userId: string;
  userEmail: string;
  action: string;
  resource: string;
  resourceId: string;
  ipAddress: string;
  userAgent: string;
  outcome: 'success' | 'failure' | 'warning';
  details: Record<string, any>;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  compliance: {
    gdpr: boolean;
    hipaa: boolean;
    sox: boolean;
    pci: boolean;
  };
}

interface ComplianceReport {
  id: string;
  name: string;
  type: 'gdpr' | 'hipaa' | 'sox' | 'pci' | 'custom';
  description: string;
  dateRange: {
    start: Date;
    end: Date;
  };
  status: 'generating' | 'completed' | 'failed';
  createdAt: Date;
  createdBy: string;
  fileSize?: number;
  downloadUrl?: string;
}

export const AuditTrailExporter: React.FC<AuditTrailExporterProps> = ({
  onExport
}) => {
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [reports, setReports] = useState<ComplianceReport[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    end: new Date()
  });
  const [selectedCompliance, setSelectedCompliance] = useState<string>('all');
  const [selectedRiskLevel, setSelectedRiskLevel] = useState<string>('all');
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportFormat, setExportFormat] = useState<'csv' | 'json' | 'pdf'>('csv');

  // Load audit events
  const loadAuditEvents = useCallback(async () => {
    setLoading(true);
    try {
      // Mock audit events - replace with actual API call
      const mockEvents: AuditEvent[] = [
        {
          id: 'audit_1',
          timestamp: new Date(Date.now() - 3600000),
          userId: 'user_123',
          userEmail: 'admin@company.com',
          action: 'LOGIN',
          resource: 'authentication',
          resourceId: 'auth_session_456',
          ipAddress: '192.168.1.100',
          userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          outcome: 'success',
          details: { sessionDuration: 7200, mfaUsed: true },
          riskLevel: 'low',
          compliance: { gdpr: true, hipaa: false, sox: true, pci: false }
        },
        {
          id: 'audit_2',
          timestamp: new Date(Date.now() - 7200000),
          userId: 'user_456',
          userEmail: 'user@company.com',
          action: 'DATA_ACCESS',
          resource: 'document',
          resourceId: 'doc_789',
          ipAddress: '192.168.1.101',
          userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
          outcome: 'success',
          details: { documentType: 'sensitive', accessLevel: 'read' },
          riskLevel: 'medium',
          compliance: { gdpr: true, hipaa: true, sox: false, pci: false }
        },
        {
          id: 'audit_3',
          timestamp: new Date(Date.now() - 10800000),
          userId: 'user_789',
          userEmail: 'contractor@external.com',
          action: 'FAILED_LOGIN',
          resource: 'authentication',
          resourceId: 'auth_attempt_123',
          ipAddress: '203.0.113.45',
          userAgent: 'curl/7.68.0',
          outcome: 'failure',
          details: { reason: 'invalid_credentials', attempts: 3 },
          riskLevel: 'high',
          compliance: { gdpr: true, hipaa: false, sox: true, pci: true }
        }
      ];
      
      setAuditEvents(mockEvents);
    } catch (error) {
      console.error('Failed to load audit events:', error);
    } finally {
      setLoading(false);
    }
  }, [dateRange]);

  // Load compliance reports
  const loadReports = useCallback(async () => {
    try {
      const mockReports: ComplianceReport[] = [
        {
          id: 'report_1',
          name: 'GDPR Compliance Report - Q1 2024',
          type: 'gdpr',
          description: 'Quarterly GDPR compliance audit report',
          dateRange: {
            start: new Date('2024-01-01'),
            end: new Date('2024-03-31')
          },
          status: 'completed',
          createdAt: new Date(Date.now() - 86400000),
          createdBy: 'compliance@company.com',
          fileSize: 2048576,
          downloadUrl: '/reports/gdpr-q1-2024.pdf'
        },
        {
          id: 'report_2',
          name: 'SOX Audit Trail - January 2024',
          type: 'sox',
          description: 'Monthly SOX compliance audit trail',
          dateRange: {
            start: new Date('2024-01-01'),
            end: new Date('2024-01-31')
          },
          status: 'completed',
          createdAt: new Date(Date.now() - 172800000),
          createdBy: 'audit@company.com',
          fileSize: 1536000,
          downloadUrl: '/reports/sox-jan-2024.csv'
        }
      ];
      
      setReports(mockReports);
    } catch (error) {
      console.error('Failed to load reports:', error);
    }
  }, []);

  // Filter events
  const filteredEvents = auditEvents.filter(event => {
    const matchesSearch = event.userEmail.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         event.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         event.resource.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCompliance = selectedCompliance === 'all' || 
                             (selectedCompliance === 'gdpr' && event.compliance.gdpr) ||
                             (selectedCompliance === 'hipaa' && event.compliance.hipaa) ||
                             (selectedCompliance === 'sox' && event.compliance.sox) ||
                             (selectedCompliance === 'pci' && event.compliance.pci);
    
    const matchesRisk = selectedRiskLevel === 'all' || event.riskLevel === selectedRiskLevel;
    
    const matchesDate = event.timestamp >= dateRange.start && event.timestamp <= dateRange.end;
    
    return matchesSearch && matchesCompliance && matchesRisk && matchesDate;
  });

  // Generate report
  const generateReport = async (type: string) => {
    setLoading(true);
    try {
      const newReport: ComplianceReport = {
        id: `report_${Date.now()}`,
        name: `${type.toUpperCase()} Report - ${new Date().toLocaleDateString()}`,
        type: type as any,
        description: `Generated ${type.toUpperCase()} compliance report`,
        dateRange: { ...dateRange },
        status: 'generating',
        createdAt: new Date(),
        createdBy: 'current_user@company.com'
      };
      
      setReports(prev => [newReport, ...prev]);
      
      // Simulate report generation
      setTimeout(() => {
        setReports(prev => prev.map(r => 
          r.id === newReport.id 
            ? { ...r, status: 'completed' as const, fileSize: 1024000, downloadUrl: `/reports/${r.id}.pdf` }
            : r
        ));
      }, 3000);
      
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setLoading(false);
    }
  };

  // Export audit data
  const exportAuditData = () => {
    const exportData = {
      events: filteredEvents,
      metadata: {
        exportedAt: new Date(),
        exportedBy: 'current_user@company.com',
        totalEvents: filteredEvents.length,
        dateRange,
        filters: {
          search: searchTerm,
          compliance: selectedCompliance,
          riskLevel: selectedRiskLevel
        }
      }
    };
    
    onExport?.(exportData);
    setShowExportModal(false);
  };

  // Risk level badge
  const RiskBadge: React.FC<{ level: AuditEvent['riskLevel'] }> = ({ level }) => {
    const colors = {
      low: 'bg-green-400/10 text-green-400',
      medium: 'bg-yellow-400/10 text-yellow-400',
      high: 'bg-orange-400/10 text-orange-400',
      critical: 'bg-red-400/10 text-red-400'
    };
    
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${colors[level]}`}>
        {level.toUpperCase()}
      </span>
    );
  };

  // Outcome badge
  const OutcomeBadge: React.FC<{ outcome: AuditEvent['outcome'] }> = ({ outcome }) => {
    const config = {
      success: { icon: CheckCircle, color: 'text-green-400 bg-green-400/10' },
      failure: { icon: AlertTriangle, color: 'text-red-400 bg-red-400/10' },
      warning: { icon: AlertTriangle, color: 'text-yellow-400 bg-yellow-400/10' }
    };
    
    const { icon: Icon, color } = config[outcome];
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {outcome.toUpperCase()}
      </span>
    );
  };

  // Export modal
  const ExportModal: React.FC = () => {
    if (!showExportModal) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
          <h3 className="text-lg font-semibold text-white mb-4">Export Audit Data</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Export Format
              </label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as any)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="csv">CSV</option>
                <option value="json">JSON</option>
                <option value="pdf">PDF</option>
              </select>
            </div>
            
            <div className="text-sm text-gray-400">
              <p>Events to export: {filteredEvents.length}</p>
              <p>Date range: {dateRange.start.toLocaleDateString()} - {dateRange.end.toLocaleDateString()}</p>
            </div>
          </div>
          
          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={() => setShowExportModal(false)}
              className="px-4 py-2 text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={exportAuditData}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Export
            </button>
          </div>
        </div>
      </div>
    );
  };

  React.useEffect(() => {
    loadAuditEvents();
    loadReports();
  }, [loadAuditEvents, loadReports]);

  return (
    <div className="p-6 bg-gray-900 text-white">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Audit Trail & Compliance</h2>
        <p className="text-gray-400">Export audit trails and generate compliance reports</p>
      </div>

      {/* Controls */}
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search events..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Compliance</label>
            <select
              value={selectedCompliance}
              onChange={(e) => setSelectedCompliance(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            >
              <option value="all">All Standards</option>
              <option value="gdpr">GDPR</option>
              <option value="hipaa">HIPAA</option>
              <option value="sox">SOX</option>
              <option value="pci">PCI DSS</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Risk Level</label>
            <select
              value={selectedRiskLevel}
              onChange={(e) => setSelectedRiskLevel(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            >
              <option value="all">All Levels</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Actions</label>
            <button
              onClick={() => setShowExportModal(true)}
              className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <Download className="w-4 h-4 mr-2" />
              Export Data
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Start Date</label>
            <input
              type="date"
              value={dateRange.start.toISOString().split('T')[0]}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: new Date(e.target.value) }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">End Date</label>
            <input
              type="date"
              value={dateRange.end.toISOString().split('T')[0]}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: new Date(e.target.value) }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Audit Events */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Audit Events ({filteredEvents.length})</h3>
            <button
              onClick={loadAuditEvents}
              className="p-2 text-gray-400 hover:text-white"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <RefreshCw className="w-6 h-6 text-blue-400 animate-spin" />
              </div>
            ) : filteredEvents.length === 0 ? (
              <div className="text-center py-8">
                <Shield className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-400">No audit events found</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-700 max-h-96 overflow-y-auto">
                {filteredEvents.map(event => (
                  <div key={event.id} className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <User className="w-4 h-4 text-blue-400" />
                        <span className="font-medium text-white">{event.userEmail}</span>
                        <OutcomeBadge outcome={event.outcome} />
                      </div>
                      <RiskBadge level={event.riskLevel} />
                    </div>
                    
                    <div className="text-sm text-gray-300 mb-2">
                      <span className="font-medium">{event.action}</span> on {event.resource}
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-gray-400">
                      <span>{event.timestamp.toLocaleString()}</span>
                      <span>{event.ipAddress}</span>
                    </div>
                    
                    {/* Compliance badges */}
                    <div className="flex items-center space-x-1 mt-2">
                      {event.compliance.gdpr && <span className="px-1 py-0.5 bg-blue-400/10 text-blue-400 text-xs rounded">GDPR</span>}
                      {event.compliance.hipaa && <span className="px-1 py-0.5 bg-green-400/10 text-green-400 text-xs rounded">HIPAA</span>}
                      {event.compliance.sox && <span className="px-1 py-0.5 bg-purple-400/10 text-purple-400 text-xs rounded">SOX</span>}
                      {event.compliance.pci && <span className="px-1 py-0.5 bg-orange-400/10 text-orange-400 text-xs rounded">PCI</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Compliance Reports */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Compliance Reports</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => generateReport('gdpr')}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
              >
                Generate GDPR
              </button>
              <button
                onClick={() => generateReport('sox')}
                className="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700"
              >
                Generate SOX
              </button>
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            {reports.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-400">No reports generated</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-700 max-h-96 overflow-y-auto">
                {reports.map(report => (
                  <div key={report.id} className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-medium text-white">{report.name}</h4>
                        <p className="text-sm text-gray-400">{report.description}</p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        report.status === 'completed' ? 'bg-green-400/10 text-green-400' :
                        report.status === 'generating' ? 'bg-blue-400/10 text-blue-400' :
                        'bg-red-400/10 text-red-400'
                      }`}>
                        {report.status}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
                      <span>{report.dateRange.start.toLocaleDateString()} - {report.dateRange.end.toLocaleDateString()}</span>
                      {report.fileSize && <span>{(report.fileSize / 1024 / 1024).toFixed(1)} MB</span>}
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400">
                        Created by {report.createdBy}
                      </span>
                      {report.status === 'completed' && report.downloadUrl && (
                        <button className="flex items-center text-blue-400 hover:text-blue-300 text-sm">
                          <Download className="w-3 h-3 mr-1" />
                          Download
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <ExportModal />
    </div>
  );
};