// Security and Compliance Types
export interface SecurityAuditLog {
  id: string;
  userId: string;
  action: string;
  resource: string;
  success: boolean;
  timestamp: Date;
  ipAddress: string;
  userAgent: string;
  details?: Record<string, any>;
}

export interface ActiveSession {
  id: string;
  userId: string;
  userEmail: string;
  loginTime: Date;
  lastActivity: Date;
  ipAddress: string;
  userAgent: string;
  location?: string;
  isActive: boolean;
}

export interface SecurityAlert {
  id: string;
  type: 'login_anomaly' | 'permission_escalation' | 'suspicious_activity' | 'rate_limit_exceeded' | 'unauthorized_access';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: Date;
  resolved: boolean;
  userId?: string;
  details?: Record<string, any>;
}

export interface SecurityMetrics {
  overview: {
    activeSessions: number;
    securityAlerts: number;
    lastSecurityScan: Date;
    threatLevel: 'low' | 'medium' | 'high' | 'critical';
  };
  sessions: ActiveSession[];
  auditLogs: SecurityAuditLog[];
  alerts: SecurityAlert[];
  recentActivity: {
    totalEvents: number;
    failedLogins: number;
    rateLimitViolations: number;
    suspiciousActivities: number;
  };
}

export interface Permission {
  resource: string;
  actions: ('read' | 'write' | 'delete' | 'admin')[];
}

export interface SecurityAction {
  type: 'terminate_session' | 'resolve_alert' | 'escalate_alert' | 'mitigate_threat' | 'block_user' | 'admin_action' | 'investigate_log' | 'bulk_security_action' | 'refresh_data';
  payload?: any;
}

export interface ThreatDetection {
  id: string;
  type: 'brute_force' | 'anomalous_behavior' | 'privilege_escalation' | 'data_exfiltration';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  timestamp: Date;
  affectedUsers: string[];
  mitigationSteps: string[];
  status: 'detected' | 'investigating' | 'mitigated' | 'resolved';
}