// Security Dashboard Service - Real-time security monitoring and management
import { 
  SecurityMetrics, 
  SecurityAlert, 
  ActiveSession, 
  SecurityAuditLog, 
  ThreatDetection,
  SecurityAction 
} from '../types/security';

export class SecurityDashboardService {
  private alerts: SecurityAlert[] = [];
  private sessions: ActiveSession[] = [];
  private auditLogs: SecurityAuditLog[] = [];
  private threats: ThreatDetection[] = [];
  private listeners: Set<(data: SecurityMetrics) => void> = new Set();

  constructor() {
    this.initializeMockData();
    this.startRealTimeMonitoring();
  }

  /**
   * Get current security metrics
   */
  async getSecurityMetrics(): Promise<SecurityMetrics> {
    const now = new Date();
    const last24Hours = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    const recentLogs = this.auditLogs.filter(log => log.timestamp > last24Hours);
    const activeAlerts = this.alerts.filter(alert => !alert.resolved);
    
    return {
      overview: {
        activeSessions: this.sessions.filter(s => s.isActive).length,
        securityAlerts: activeAlerts.length,
        lastSecurityScan: new Date(now.getTime() - 5 * 60 * 1000), // 5 minutes ago
        threatLevel: this.calculateThreatLevel(activeAlerts)
      },
      sessions: this.sessions.filter(s => s.isActive),
      auditLogs: recentLogs.slice(0, 50), // Latest 50 logs
      alerts: activeAlerts.slice(0, 20), // Latest 20 alerts
      recentActivity: {
        totalEvents: recentLogs.length,
        failedLogins: recentLogs.filter(log => log.action === 'login_failed').length,
        rateLimitViolations: recentLogs.filter(log => log.action === 'rate_limit_exceeded').length,
        suspiciousActivities: recentLogs.filter(log => !log.success && log.action !== 'login_failed').length
      }
    };
  }

  /**
   * Subscribe to real-time security updates
   */
  subscribe(callback: (data: SecurityMetrics) => void): () => void {
    this.listeners.add(callback);
    
    // Send initial data
    this.getSecurityMetrics().then(callback);
    
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * Perform security action
   */
  async performSecurityAction(action: SecurityAction): Promise<boolean> {
    try {
      switch (action.type) {
        case 'terminate_session':
          return this.terminateSession(action.payload.sessionId);
        case 'resolve_alert':
          return this.resolveAlert(action.payload.alertId);
        case 'escalate_alert':
          return this.escalateAlert(action.payload.alertId);
        case 'mitigate_threat':
          return this.mitigateThreat(action.payload.threatId, action.payload.action);
        case 'block_user':
          return this.blockUser(action.payload.userId);
        case 'admin_action':
          return this.performAdminAction(action.payload);
        case 'investigate_log':
          return this.investigateLog(action.payload);
        case 'bulk_security_action':
          return this.logBulkAction(action.payload);
        case 'refresh_data':
          await this.refreshSecurityData();
          return true;
        default:
          return false;
      }
    } catch (error) {
      console.error('Security action failed:', error);
      return false;
    }
  }

  /**
   * Get active sessions with filtering
   */
  async getActiveSessions(filters?: {
    userId?: string;
    ipAddress?: string;
    timeRange?: { start: Date; end: Date };
  }): Promise<ActiveSession[]> {
    let sessions = this.sessions.filter(s => s.isActive);
    
    if (filters) {
      if (filters.userId) {
        sessions = sessions.filter(s => s.userId.includes(filters.userId!));
      }
      if (filters.ipAddress) {
        sessions = sessions.filter(s => s.ipAddress.includes(filters.ipAddress!));
      }
      if (filters.timeRange) {
        sessions = sessions.filter(s => 
          s.loginTime >= filters.timeRange!.start && 
          s.loginTime <= filters.timeRange!.end
        );
      }
    }
    
    return sessions;
  }

  /**
   * Get security alerts with filtering
   */
  async getSecurityAlerts(filters?: {
    severity?: string;
    type?: string;
    resolved?: boolean;
    timeRange?: { start: Date; end: Date };
  }): Promise<SecurityAlert[]> {
    let alerts = [...this.alerts];
    
    if (filters) {
      if (filters.severity) {
        alerts = alerts.filter(a => a.severity === filters.severity);
      }
      if (filters.type) {
        alerts = alerts.filter(a => a.type === filters.type);
      }
      if (filters.resolved !== undefined) {
        alerts = alerts.filter(a => a.resolved === filters.resolved);
      }
      if (filters.timeRange) {
        alerts = alerts.filter(a => 
          a.timestamp >= filters.timeRange!.start && 
          a.timestamp <= filters.timeRange!.end
        );
      }
    }
    
    return alerts.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  /**
   * Get audit logs with filtering and pagination
   */
  async getAuditLogs(filters?: {
    userId?: string;
    action?: string;
    success?: boolean;
    timeRange?: { start: Date; end: Date };
    page?: number;
    limit?: number;
  }): Promise<{ logs: SecurityAuditLog[]; total: number }> {
    let logs = [...this.auditLogs];
    
    if (filters) {
      if (filters.userId) {
        logs = logs.filter(l => l.userId.includes(filters.userId!));
      }
      if (filters.action) {
        logs = logs.filter(l => l.action.includes(filters.action!));
      }
      if (filters.success !== undefined) {
        logs = logs.filter(l => l.success === filters.success);
      }
      if (filters.timeRange) {
        logs = logs.filter(l => 
          l.timestamp >= filters.timeRange!.start && 
          l.timestamp <= filters.timeRange!.end
        );
      }
    }
    
    logs.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    
    const page = filters?.page || 1;
    const limit = filters?.limit || 50;
    const start = (page - 1) * limit;
    const end = start + limit;
    
    return {
      logs: logs.slice(start, end),
      total: logs.length
    };
  }

  /**
   * Terminate a user session
   */
  private async terminateSession(sessionId: string): Promise<boolean> {
    const sessionIndex = this.sessions.findIndex(s => s.id === sessionId);
    if (sessionIndex === -1) return false;
    
    this.sessions[sessionIndex].isActive = false;
    
    // Log the action
    this.addAuditLog({
      userId: 'admin',
      action: 'session_terminated',
      resource: sessionId,
      success: true,
      details: { sessionId, reason: 'admin_action' }
    });
    
    this.notifyListeners();
    return true;
  }

  /**
   * Resolve a security alert
   */
  private async resolveAlert(alertId: string): Promise<boolean> {
    const alert = this.alerts.find(a => a.id === alertId);
    if (!alert) return false;
    
    alert.resolved = true;
    
    // Log the action
    this.addAuditLog({
      userId: 'admin',
      action: 'alert_resolved',
      resource: alertId,
      success: true,
      details: { alertId, alertType: alert.type }
    });
    
    this.notifyListeners();
    return true;
  }

  /**
   * Block a user (terminate all sessions)
   */
  private async blockUser(userId: string): Promise<boolean> {
    const userSessions = this.sessions.filter(s => s.userId === userId && s.isActive);
    
    userSessions.forEach(session => {
      session.isActive = false;
    });
    
    // Log the action
    this.addAuditLog({
      userId: 'admin',
      action: 'user_blocked',
      resource: userId,
      success: true,
      details: { userId, sessionsTerminated: userSessions.length }
    });
    
    this.notifyListeners();
    return true;
  }

  /**
   * Escalate a security alert
   */
  private async escalateAlert(alertId: string): Promise<boolean> {
    const alert = this.alerts.find(a => a.id === alertId);
    if (!alert) return false;
    
    // Escalate severity if not already critical
    if (alert.severity !== 'critical') {
      const severityLevels = ['low', 'medium', 'high', 'critical'];
      const currentIndex = severityLevels.indexOf(alert.severity);
      alert.severity = severityLevels[Math.min(currentIndex + 1, 3)] as any;
    }
    
    // Log the action
    this.addAuditLog({
      userId: 'admin',
      action: 'alert_escalated',
      resource: alertId,
      success: true,
      details: { alertId, alertType: alert.type, newSeverity: alert.severity }
    });
    
    this.notifyListeners();
    return true;
  }

  /**
   * Mitigate a threat
   */
  private async mitigateThreat(threatId: string, mitigationAction: string): Promise<boolean> {
    // In a real implementation, this would interact with threat detection systems
    
    // Log the action
    this.addAuditLog({
      userId: 'admin',
      action: 'threat_mitigated',
      resource: threatId,
      success: true,
      details: { threatId, action: mitigationAction }
    });
    
    this.notifyListeners();
    return true;
  }

  /**
   * Perform administrative action on audit logs
   */
  private async performAdminAction(payload: any): Promise<boolean> {
    const { action, logIds, reason } = payload;
    
    // Log the administrative action
    this.addAuditLog({
      userId: 'admin',
      action: `admin_${action}`,
      resource: 'audit_logs',
      success: true,
      details: { action, logIds, reason, count: logIds.length }
    });
    
    // In a real implementation, this would perform the actual action
    // For now, we just log it
    
    this.notifyListeners();
    return true;
  }

  /**
   * Investigate a suspicious log entry
   */
  private async investigateLog(payload: any): Promise<boolean> {
    const { logId, userId, action, timestamp } = payload;
    
    // Log the investigation
    this.addAuditLog({
      userId: 'admin',
      action: 'investigation_started',
      resource: logId,
      success: true,
      details: { 
        investigatedLogId: logId, 
        investigatedUserId: userId, 
        investigatedAction: action,
        investigationTimestamp: timestamp
      }
    });
    
    this.notifyListeners();
    return true;
  }

  /**
   * Log bulk security action
   */
  private async logBulkAction(payload: any): Promise<boolean> {
    const { action, alertCount, timestamp } = payload;
    
    // Log the bulk action
    this.addAuditLog({
      userId: 'admin',
      action: 'bulk_security_action',
      resource: 'security_system',
      success: true,
      details: { bulkAction: action, affectedAlerts: alertCount, timestamp }
    });
    
    this.notifyListeners();
    return true;
  }

  /**
   * Refresh security data
   */
  private async refreshSecurityData(): Promise<void> {
    // Simulate data refresh
    await new Promise(resolve => setTimeout(resolve, 1000));
    this.notifyListeners();
  }

  /**
   * Calculate threat level based on active alerts
   */
  private calculateThreatLevel(alerts: SecurityAlert[]): 'low' | 'medium' | 'high' | 'critical' {
    const criticalAlerts = alerts.filter(a => a.severity === 'critical').length;
    const highAlerts = alerts.filter(a => a.severity === 'high').length;
    const mediumAlerts = alerts.filter(a => a.severity === 'medium').length;
    
    if (criticalAlerts > 0) return 'critical';
    if (highAlerts > 2) return 'high';
    if (highAlerts > 0 || mediumAlerts > 5) return 'medium';
    return 'low';
  }

  /**
   * Add audit log entry
   */
  private addAuditLog(log: Omit<SecurityAuditLog, 'id' | 'timestamp' | 'ipAddress' | 'userAgent'>): void {
    const auditLog: SecurityAuditLog = {
      ...log,
      id: `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      ipAddress: '192.168.1.100', // Mock IP
      userAgent: 'Mozilla/5.0 (Security Dashboard)' // Mock user agent
    };
    
    this.auditLogs.unshift(auditLog);
    
    // Keep only last 1000 logs
    if (this.auditLogs.length > 1000) {
      this.auditLogs = this.auditLogs.slice(0, 1000);
    }
  }

  /**
   * Notify all listeners of data changes
   */
  private async notifyListeners(): Promise<void> {
    const data = await this.getSecurityMetrics();
    this.listeners.forEach(callback => callback(data));
  }

  /**
   * Start real-time monitoring simulation
   */
  private startRealTimeMonitoring(): void {
    // Simulate real-time updates every 30 seconds
    setInterval(() => {
      this.simulateSecurityActivity();
      this.notifyListeners();
    }, 30000);
  }

  /**
   * Simulate security activity for demo purposes
   */
  private simulateSecurityActivity(): void {
    const now = new Date();
    
    // Randomly add new audit logs
    if (Math.random() < 0.3) {
      this.addAuditLog({
        userId: `user_${Math.floor(Math.random() * 100)}`,
        action: ['login_success', 'document_access', 'api_call', 'logout'][Math.floor(Math.random() * 4)],
        resource: 'system',
        success: Math.random() > 0.1 // 90% success rate
      });
    }
    
    // Randomly add security alerts
    if (Math.random() < 0.1) {
      const alertTypes = ['login_anomaly', 'suspicious_activity', 'rate_limit_exceeded'] as const;
      const severities = ['low', 'medium', 'high'] as const;
      
      this.alerts.unshift({
        id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: alertTypes[Math.floor(Math.random() * alertTypes.length)],
        severity: severities[Math.floor(Math.random() * severities.length)],
        message: 'Suspicious activity detected',
        timestamp: now,
        resolved: false,
        userId: `user_${Math.floor(Math.random() * 100)}`
      });
    }
    
    // Update session activity
    this.sessions.forEach(session => {
      if (session.isActive && Math.random() < 0.5) {
        session.lastActivity = now;
      }
    });
  }

  /**
   * Initialize mock data for demonstration
   */
  private initializeMockData(): void {
    const now = new Date();
    
    // Create mock active sessions
    for (let i = 0; i < 15; i++) {
      this.sessions.push({
        id: `session_${i}`,
        userId: `user_${i}`,
        userEmail: `user${i}@example.com`,
        loginTime: new Date(now.getTime() - Math.random() * 24 * 60 * 60 * 1000),
        lastActivity: new Date(now.getTime() - Math.random() * 60 * 60 * 1000),
        ipAddress: `192.168.1.${100 + i}`,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        location: ['New York', 'London', 'Tokyo', 'Sydney'][Math.floor(Math.random() * 4)],
        isActive: Math.random() > 0.2 // 80% active
      });
    }
    
    // Create mock security alerts
    const alertTypes = ['login_anomaly', 'suspicious_activity', 'rate_limit_exceeded'] as const;
    const severities = ['low', 'medium', 'high', 'critical'] as const;
    
    for (let i = 0; i < 8; i++) {
      this.alerts.push({
        id: `alert_${i}`,
        type: alertTypes[Math.floor(Math.random() * alertTypes.length)],
        severity: severities[Math.floor(Math.random() * severities.length)],
        message: `Security alert ${i + 1}: Suspicious activity detected`,
        timestamp: new Date(now.getTime() - Math.random() * 24 * 60 * 60 * 1000),
        resolved: Math.random() > 0.6, // 40% resolved
        userId: `user_${Math.floor(Math.random() * 100)}`
      });
    }
    
    // Create mock audit logs
    const actions = ['login_success', 'login_failed', 'document_access', 'api_call', 'logout', 'permission_change'];
    
    for (let i = 0; i < 100; i++) {
      this.auditLogs.push({
        id: `audit_${i}`,
        userId: `user_${Math.floor(Math.random() * 50)}`,
        action: actions[Math.floor(Math.random() * actions.length)],
        resource: 'system',
        success: Math.random() > 0.15, // 85% success rate
        timestamp: new Date(now.getTime() - Math.random() * 7 * 24 * 60 * 60 * 1000),
        ipAddress: `192.168.1.${Math.floor(Math.random() * 255)}`,
        userAgent: 'Mozilla/5.0 (Security System)',
        details: { source: 'security_dashboard' }
      });
    }
  }
}

export const securityDashboardService = new SecurityDashboardService();