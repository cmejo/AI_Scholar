import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { 
  Shield, AlertTriangle, Users, Activity, Lock, 
  Eye, Clock, TrendingUp, AlertCircle, CheckCircle,
  XCircle, Zap, Globe, Server, Database
} from 'lucide-react';

interface SecurityEvent {
  id: string;
  type: 'login' | 'failed_login' | 'permission_denied' | 'data_access' | 'system_alert';
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: Date;
  user?: string;
  ip?: string;
  description: string;
  resolved: boolean;
}

interface SecurityMetrics {
  totalEvents: number;
  criticalAlerts: number;
  activeThreats: number;
  blockedAttempts: number;
  securityScore: number;
  lastScan: Date;
}

export const SecurityDashboard: React.FC = () => {
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [metrics, setMetrics] = useState<SecurityMetrics>({
    totalEvents: 0,
    criticalAlerts: 0,
    activeThreats: 0,
    blockedAttempts: 0,
    securityScore: 95,
    lastScan: new Date()
  });
  const [selectedTimeRange, setSelectedTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [activeTab, setActiveTab] = useState<'overview' | 'events' | 'threats' | 'users'>('overview');

  // Mock data generation
  useEffect(() => {
    const generateMockEvents = () => {
      const eventTypes: SecurityEvent['type'][] = ['login', 'failed_login', 'permission_denied', 'data_access', 'system_alert'];
      const severities: SecurityEvent['severity'][] = ['low', 'medium', 'high', 'critical'];
      const users = ['admin@cmejo.com', 'user1@example.com', 'user2@example.com', 'unknown'];
      
      const events: SecurityEvent[] = [];
      for (let i = 0; i < 50; i++) {
        const event: SecurityEvent = {
          id: `event_${i}`,
          type: eventTypes[Math.floor(Math.random() * eventTypes.length)],
          severity: severities[Math.floor(Math.random() * severities.length)],
          timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
          user: users[Math.floor(Math.random() * users.length)],
          ip: `192.168.1.${Math.floor(Math.random() * 255)}`,
          description: generateEventDescription(),
          resolved: Math.random() > 0.3
        };
        events.push(event);
      }
      
      setSecurityEvents(events.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime()));
      
      // Update metrics
      const criticalEvents = events.filter(e => e.severity === 'critical' && !e.resolved);
      const failedLogins = events.filter(e => e.type === 'failed_login');
      
      setMetrics({
        totalEvents: events.length,
        criticalAlerts: criticalEvents.length,
        activeThreats: Math.floor(Math.random() * 5),
        blockedAttempts: failedLogins.length,
        securityScore: Math.max(70, 100 - criticalEvents.length * 5),
        lastScan: new Date()
      });
    };

    generateMockEvents();
    const interval = setInterval(generateMockEvents, 30000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  const generateEventDescription = (): string => {
    const descriptions = [
      'Successful user authentication',
      'Failed login attempt detected',
      'Unauthorized access attempt blocked',
      'Suspicious API request pattern',
      'Security scan completed',
      'Password policy violation',
      'Session timeout enforced',
      'Data export request logged',
      'Admin privilege escalation',
      'Firewall rule triggered'
    ];
    return descriptions[Math.floor(Math.random() * descriptions.length)];
  };

  const getSeverityColor = (severity: SecurityEvent['severity']) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const getEventIcon = (type: SecurityEvent['type']) => {
    switch (type) {
      case 'login': return <CheckCircle className="w-4 h-4" />;
      case 'failed_login': return <XCircle className="w-4 h-4" />;
      case 'permission_denied': return <Lock className="w-4 h-4" />;
      case 'data_access': return <Database className="w-4 h-4" />;
      case 'system_alert': return <AlertTriangle className="w-4 h-4" />;
    }
  };

  const resolveEvent = (eventId: string) => {
    setSecurityEvents(prev => 
      prev.map(event => 
        event.id === eventId ? { ...event, resolved: true } : event
      )
    );
  };

  const filteredEvents = securityEvents.filter(event => {
    const now = new Date();
    const eventTime = event.timestamp;
    const timeDiff = now.getTime() - eventTime.getTime();
    
    switch (selectedTimeRange) {
      case '1h': return timeDiff <= 60 * 60 * 1000;
      case '24h': return timeDiff <= 24 * 60 * 60 * 1000;
      case '7d': return timeDiff <= 7 * 24 * 60 * 60 * 1000;
      case '30d': return timeDiff <= 30 * 24 * 60 * 60 * 1000;
      default: return true;
    }
  });

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-600" />
            Security Dashboard
          </h1>
          <p className="text-gray-600 mt-1">Enterprise security monitoring and threat detection</p>
        </div>
        
        <div className="flex gap-3">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Zap className="w-4 h-4 mr-2" />
            Run Security Scan
          </Button>
        </div>
      </div>

      {/* Security Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100">Security Score</p>
                <p className="text-3xl font-bold">{metrics.securityScore}%</p>
              </div>
              <Shield className="w-8 h-8 text-green-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-red-500 to-red-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-100">Critical Alerts</p>
                <p className="text-3xl font-bold">{metrics.criticalAlerts}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-orange-500 to-orange-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100">Active Threats</p>
                <p className="text-3xl font-bold">{metrics.activeThreats}</p>
              </div>
              <Eye className="w-8 h-8 text-orange-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100">Blocked Attempts</p>
                <p className="text-3xl font-bold">{metrics.blockedAttempts}</p>
              </div>
              <Lock className="w-8 h-8 text-purple-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100">Total Events</p>
                <p className="text-3xl font-bold">{metrics.totalEvents}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-1 bg-gray-200 p-1 rounded-lg">
        {[
          { id: 'overview', label: 'Overview', icon: Activity },
          { id: 'events', label: 'Security Events', icon: AlertCircle },
          { id: 'threats', label: 'Threat Analysis', icon: AlertTriangle },
          { id: 'users', label: 'User Activity', icon: Users }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Security Trends
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>Login Success Rate</span>
                  <span className="text-green-600 font-semibold">94.2%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Threat Detection Rate</span>
                  <span className="text-blue-600 font-semibold">99.8%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Response Time</span>
                  <span className="text-purple-600 font-semibold">1.2s avg</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>System Uptime</span>
                  <span className="text-green-600 font-semibold">99.99%</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5" />
                Geographic Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {['United States', 'Canada', 'United Kingdom', 'Germany', 'Japan'].map((country, index) => (
                  <div key={country} className="flex justify-between items-center">
                    <span>{country}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${Math.random() * 80 + 20}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{Math.floor(Math.random() * 100)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'events' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Recent Security Events ({filteredEvents.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {filteredEvents.slice(0, 20).map(event => (
                <div
                  key={event.id}
                  className={`p-4 rounded-lg border ${getSeverityColor(event.severity)} ${
                    event.resolved ? 'opacity-60' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {getEventIcon(event.type)}
                      <div>
                        <div className="font-medium">{event.description}</div>
                        <div className="text-sm opacity-75 mt-1">
                          {event.user && `User: ${event.user} • `}
                          {event.ip && `IP: ${event.ip} • `}
                          {event.timestamp.toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(event.severity)}`}>
                        {event.severity.toUpperCase()}
                      </span>
                      {!event.resolved && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => resolveEvent(event.id)}
                        >
                          Resolve
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'threats' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Threat Categories
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { name: 'Brute Force Attacks', count: 12, trend: 'down' },
                  { name: 'SQL Injection Attempts', count: 3, trend: 'stable' },
                  { name: 'Cross-Site Scripting', count: 7, trend: 'up' },
                  { name: 'DDoS Attempts', count: 1, trend: 'down' },
                  { name: 'Malware Detection', count: 0, trend: 'stable' }
                ].map(threat => (
                  <div key={threat.name} className="flex justify-between items-center">
                    <span>{threat.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{threat.count}</span>
                      <span className={`text-xs ${
                        threat.trend === 'up' ? 'text-red-500' : 
                        threat.trend === 'down' ? 'text-green-500' : 'text-gray-500'
                      }`}>
                        {threat.trend === 'up' ? '↑' : threat.trend === 'down' ? '↓' : '→'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="w-5 h-5" />
                System Health
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { component: 'Authentication Service', status: 'healthy', uptime: '99.99%' },
                  { component: 'Database Security', status: 'healthy', uptime: '99.95%' },
                  { component: 'API Gateway', status: 'warning', uptime: '99.80%' },
                  { component: 'Firewall', status: 'healthy', uptime: '100%' },
                  { component: 'Intrusion Detection', status: 'healthy', uptime: '99.98%' }
                ].map(component => (
                  <div key={component.component} className="flex justify-between items-center">
                    <span>{component.component}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-600">{component.uptime}</span>
                      <div className={`w-3 h-3 rounded-full ${
                        component.status === 'healthy' ? 'bg-green-500' :
                        component.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                      }`} />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'users' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              User Security Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { user: 'admin@cmejo.com', lastLogin: '2 minutes ago', status: 'active', risk: 'low' },
                { user: 'user1@example.com', lastLogin: '1 hour ago', status: 'active', risk: 'low' },
                { user: 'user2@example.com', lastLogin: '3 hours ago', status: 'inactive', risk: 'medium' },
                { user: 'guest@example.com', lastLogin: '1 day ago', status: 'inactive', risk: 'high' }
              ].map(user => (
                <div key={user.user} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium">{user.user}</div>
                    <div className="text-sm text-gray-600">Last login: {user.lastLogin}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      user.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {user.status}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      user.risk === 'low' ? 'bg-green-100 text-green-800' :
                      user.risk === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {user.risk} risk
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Last Scan Info */}
      <div className="text-center text-sm text-gray-500">
        <Clock className="w-4 h-4 inline mr-1" />
        Last security scan: {metrics.lastScan.toLocaleString()}
      </div>
    </div>
  );
};