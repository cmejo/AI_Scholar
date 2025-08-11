// Enterprise Security and Compliance Service
import { Permission, SecurityAuditLog, User } from '../types';

export class SecurityService {
  private auditLogs: SecurityAuditLog[] = [];
  private sessionTokens: Map<string, { userId: string; expires: Date; permissions: Permission[] }> = new Map();
  private rateLimits: Map<string, { count: number; resetTime: Date }> = new Map();

  /**
   * Authenticate user and create session
   */
  async authenticate(email: string, password: string): Promise<{ token: string; user: User } | null> {
    // Mock authentication - in production, verify against secure user store
    const user = await this.getUserByEmail(email);
    if (!user || !await this.verifyPassword(password, user.id)) {
      this.logSecurityEvent({
        userId: 'unknown',
        action: 'login_failed',
        resource: 'authentication',
        success: false,
        details: { email, reason: 'invalid_credentials' }
      });
      return null;
    }

    const token = this.generateSecureToken();
    const expires = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24 hours

    this.sessionTokens.set(token, {
      userId: user.id,
      expires,
      permissions: user.permissions
    });

    this.logSecurityEvent({
      userId: user.id,
      action: 'login_success',
      resource: 'authentication',
      success: true,
      details: { email }
    });

    return { token, user };
  }

  /**
   * Validate session token and check permissions
   */
  validateToken(token: string): { userId: string; permissions: Permission[] } | null {
    const session = this.sessionTokens.get(token);
    if (!session || session.expires < new Date()) {
      if (session) {
        this.sessionTokens.delete(token);
      }
      return null;
    }

    return {
      userId: session.userId,
      permissions: session.permissions
    };
  }

  /**
   * Check if user has permission for action on resource
   */
  hasPermission(permissions: Permission[], resource: string, action: string): boolean {
    return permissions.some(permission => 
      permission.resource === resource && permission.actions.includes(action as 'read' | 'write' | 'delete' | 'admin')
    );
  }

  /**
   * Rate limiting check
   */
  checkRateLimit(userId: string, limit: number = 100, windowMinutes: number = 60): boolean {
    const key = `${userId}_${Math.floor(Date.now() / (windowMinutes * 60 * 1000))}`;
    const current = this.rateLimits.get(key) || { count: 0, resetTime: new Date(Date.now() + windowMinutes * 60 * 1000) };
    
    if (current.count >= limit) {
      this.logSecurityEvent({
        userId,
        action: 'rate_limit_exceeded',
        resource: 'api',
        success: false,
        details: { limit, window: windowMinutes }
      });
      return false;
    }

    current.count++;
    this.rateLimits.set(key, current);
    return true;
  }

  /**
   * Log security event
   */
  logSecurityEvent(event: Omit<SecurityAuditLog, 'id' | 'timestamp' | 'ipAddress' | 'userAgent'>): void {
    const auditLog: SecurityAuditLog = {
      ...event,
      id: `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      ipAddress: '127.0.0.1', // In production, get from request
      userAgent: 'Browser/1.0' // In production, get from request
    };

    this.auditLogs.push(auditLog);
    
    // In production, also send to external security monitoring
    this.sendToSecurityMonitoring(auditLog);
  }

  /**
   * Get audit logs for compliance
   */
  getAuditLogs(filters: {
    userId?: string;
    action?: string;
    startDate?: Date;
    endDate?: Date;
    success?: boolean;
  } = {}): SecurityAuditLog[] {
    return this.auditLogs.filter(log => {
      if (filters.userId && log.userId !== filters.userId) return false;
      if (filters.action && log.action !== filters.action) return false;
      if (filters.startDate && log.timestamp < filters.startDate) return false;
      if (filters.endDate && log.timestamp > filters.endDate) return false;
      if (filters.success !== undefined && log.success !== filters.success) return false;
      return true;
    });
  }

  /**
   * Encrypt sensitive data
   */
  encryptData(data: string): string {
    // Mock encryption - in production, use proper encryption
    return btoa(data);
  }

  /**
   * Decrypt sensitive data
   */
  decryptData(encryptedData: string): string {
    // Mock decryption - in production, use proper decryption
    return atob(encryptedData);
  }

  /**
   * Validate data access permissions
   */
  validateDataAccess(userId: string, documentId: string, action: 'read' | 'write' | 'delete'): boolean {
    const session = Array.from(this.sessionTokens.values()).find(s => s.userId === userId);
    if (!session) return false;

    // Check document-specific permissions
    const hasDocumentPermission = this.hasPermission(session.permissions, 'documents', action);
    
    // Log access attempt
    this.logSecurityEvent({
      userId,
      action: `document_${action}`,
      resource: documentId,
      success: hasDocumentPermission,
      details: { documentId, action }
    });

    return hasDocumentPermission;
  }

  /**
   * Generate secure session token
   */
  private generateSecureToken(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Get user by email (mock implementation)
   */
  private async getUserByEmail(email: string): Promise<User | null> {
    // Mock user lookup
    if (email === 'admin@example.com') {
      return {
        id: 'user_admin',
        email,
        name: 'Admin User',
        role: 'admin',
        permissions: [
          { resource: 'documents', actions: ['read', 'write', 'delete', 'admin'] },
          { resource: 'users', actions: ['read', 'write', 'delete', 'admin'] },
          { resource: 'analytics', actions: ['read', 'admin'] }
        ],
        preferences: {
          theme: 'dark',
          language: 'en',
          defaultModel: 'mistral',
          responseLength: 'detailed',
          enableVoice: false,
          enableNotifications: true,
          customDashboard: { widgets: [], layout: 'grid', refreshInterval: 30 }
        },
        createdAt: new Date('2024-01-01'),
        lastLogin: new Date()
      };
    }
    return null;
  }

  /**
   * Verify password (mock implementation)
   */
  private async verifyPassword(password: string, userId: string): Promise<boolean> {
    // Mock password verification
    return password === 'admin123';
  }

  /**
   * Send to external security monitoring
   */
  private sendToSecurityMonitoring(log: SecurityAuditLog): void {
    // In production, send to SIEM or security monitoring service
    console.log('Security Event:', log);
  }

  /**
   * Clean up expired sessions
   */
  cleanupExpiredSessions(): void {
    const now = new Date();
    for (const [token, session] of this.sessionTokens.entries()) {
      if (session.expires < now) {
        this.sessionTokens.delete(token);
      }
    }
  }

  /**
   * Get security metrics
   */
  getSecurityMetrics(): {
    totalEvents: number;
    failedLogins: number;
    rateLimitViolations: number;
    activeSessions: number;
    recentThreats: SecurityAuditLog[];
  } {
    const now = new Date();
    const last24Hours = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    const recentLogs = this.auditLogs.filter(log => log.timestamp > last24Hours);
    
    return {
      totalEvents: recentLogs.length,
      failedLogins: recentLogs.filter(log => log.action === 'login_failed').length,
      rateLimitViolations: recentLogs.filter(log => log.action === 'rate_limit_exceeded').length,
      activeSessions: this.sessionTokens.size,
      recentThreats: recentLogs.filter(log => !log.success).slice(0, 10)
    };
  }
}

export const securityService = new SecurityService();