import React, { useState } from 'react';
import { 
  Shield, Lock, Unlock, Eye, AlertTriangle, CheckCircle, 
  Key, Globe, Database, Activity, RefreshCw, Download, 
  Users, Clock, Bell, Settings, X
} from 'lucide-react';

interface SecurityEvent {
  id: number;
  event: string;
  user: string;
  time: string;
  type: 'success' | 'warning' | 'error' | 'info';
  ip?: string;
  location?: string;
}

interface SecuritySetting {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  category: 'Authentication' | 'Access Control' | 'Monitoring' | 'Data Protection';
}

const SecurityView: React.FC = () => {
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([
    { id: 1, event: 'Successful login', user: 'Administrator', time: '2 minutes ago', type: 'success', ip: '192.168.1.100', location: 'New York, US' },
    { id: 2, event: 'API key rotated', user: 'System', time: '1 hour ago', type: 'info', ip: 'Internal', location: 'System' },
    { id: 3, event: 'Failed login attempt', user: 'Unknown', time: '3 hours ago', type: 'warning', ip: '203.0.113.42', location: 'Unknown' },
    { id: 4, event: 'Password changed', user: 'Administrator', time: '1 day ago', type: 'success', ip: '192.168.1.100', location: 'New York, US' },
    { id: 5, event: 'Suspicious API usage detected', user: 'api_user_123', time: '2 days ago', type: 'error', ip: '198.51.100.25', location: 'London, UK' },
    { id: 6, event: 'Two-factor authentication enabled', user: 'Administrator', time: '3 days ago', type: 'success', ip: '192.168.1.100', location: 'New York, US' }
  ]);

  const [securitySettings, setSecuritySettings] = useState<SecuritySetting[]>([
    { id: 'twoFactorAuth', name: 'Two-Factor Authentication', description: 'Require 2FA for all user logins', enabled: true, category: 'Authentication' },
    { id: 'apiRateLimit', name: 'API Rate Limiting', description: 'Limit API requests per user/IP', enabled: true, category: 'Access Control' },
    { id: 'auditLogging', name: 'Audit Logging', description: 'Log all user actions and system events', enabled: true, category: 'Monitoring' },
    { id: 'ipWhitelisting', name: 'IP Whitelisting', description: 'Only allow access from approved IP addresses', enabled: false, category: 'Access Control' },
    { id: 'sessionTimeout', name: 'Session Timeout', description: 'Automatically log out inactive users', enabled: true, category: 'Authentication' },
    { id: 'dataEncryption', name: 'Data Encryption at Rest', description: 'Encrypt all stored data', enabled: true, category: 'Data Protection' },
    { id: 'sslOnly', name: 'Force HTTPS', description: 'Require SSL/TLS for all connections', enabled: true, category: 'Data Protection' },
    { id: 'bruteForceProtection', name: 'Brute Force Protection', description: 'Block repeated failed login attempts', enabled: true, category: 'Authentication' },
    { id: 'anomalyDetection', name: 'Anomaly Detection', description: 'Monitor for unusual user behavior', enabled: false, category: 'Monitoring' },
    { id: 'backupEncryption', name: 'Backup Encryption', description: 'Encrypt all backup files', enabled: true, category: 'Data Protection' }
  ]);

  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [showEventDetails, setShowEventDetails] = useState<SecurityEvent | null>(null);

  const categories = ['All', 'Authentication', 'Access Control', 'Monitoring', 'Data Protection'];

  const filteredSettings = selectedCategory === 'All' 
    ? securitySettings 
    : securitySettings.filter(setting => setting.category === selectedCategory);

  const toggleSetting = (id: string) => {
    setSecuritySettings(prev => prev.map(setting => 
      setting.id === id ? { ...setting, enabled: !setting.enabled } : setting
    ));
  };

  const getEventIcon = (type: SecurityEvent['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle size={16} style={{ color: '#10b981' }} />;
      case 'warning':
        return <AlertTriangle size={16} style={{ color: '#f59e0b' }} />;
      case 'error':
        return <AlertTriangle size={16} style={{ color: '#ef4444' }} />;
      case 'info':
        return <Activity size={16} style={{ color: '#60a5fa' }} />;
    }
  };

  const getEventColor = (type: SecurityEvent['type']) => {
    switch (type) {
      case 'success': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'error': return '#ef4444';
      case 'info': return '#60a5fa';
    }
  };

  const securityScore = Math.round((securitySettings.filter(s => s.enabled).length / securitySettings.length) * 100);

  return (
    <div style={{
      padding: '24px',
      height: '100%',
      overflow: 'auto'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px'
      }}>
        <div>
          <h2 style={{
            color: 'white',
            margin: 0,
            fontSize: '24px',
            fontWeight: '600'
          }}>
            Security Center
          </h2>
          <p style={{
            color: '#9ca3af',
            margin: '4px 0 0 0',
            fontSize: '14px'
          }}>
            Monitor and manage your AI Scholar security settings
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '12px' }}>
          <button style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 16px',
            background: 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: '8px',
            color: 'white',
            cursor: 'pointer',
            fontSize: '14px'
          }}>
            <RefreshCw size={16} />
            Refresh
          </button>
          
          <button style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 16px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            border: 'none',
            borderRadius: '8px',
            color: 'white',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500'
          }}>
            <Download size={16} />
            Export Report
          </button>
        </div>
      </div>

      {/* Security Overview */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '20px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            marginBottom: '12px'
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '8px',
              background: `linear-gradient(135deg, ${securityScore >= 80 ? '#10b981' : securityScore >= 60 ? '#f59e0b' : '#ef4444'}20 0%, ${securityScore >= 80 ? '#10b981' : securityScore >= 60 ? '#f59e0b' : '#ef4444'}40 100%)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: securityScore >= 80 ? '#10b981' : securityScore >= 60 ? '#f59e0b' : '#ef4444'
            }}>
              <Shield size={20} />
            </div>
            <div>
              <h3 style={{
                color: 'white',
                margin: 0,
                fontSize: '24px',
                fontWeight: '600'
              }}>
                {securityScore}%
              </h3>
              <p style={{
                color: '#9ca3af',
                margin: 0,
                fontSize: '14px'
              }}>
                Security Score
              </p>
            </div>
          </div>
          <div style={{
            width: '100%',
            height: '4px',
            background: 'rgba(255,255,255,0.2)',
            borderRadius: '2px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${securityScore}%`,
              height: '100%',
              background: securityScore >= 80 ? '#10b981' : securityScore >= 60 ? '#f59e0b' : '#ef4444',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '20px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <Activity size={20} style={{ color: '#60a5fa' }} />
            <span style={{ color: 'white', fontSize: '16px', fontWeight: '500' }}>Active Sessions</span>
          </div>
          <div style={{ color: 'white', fontSize: '24px', fontWeight: '600' }}>3</div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '20px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <AlertTriangle size={20} style={{ color: '#f59e0b' }} />
            <span style={{ color: 'white', fontSize: '16px', fontWeight: '500' }}>Security Alerts</span>
          </div>
          <div style={{ color: 'white', fontSize: '24px', fontWeight: '600' }}>
            {securityEvents.filter(e => e.type === 'warning' || e.type === 'error').length}
          </div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '20px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <Key size={20} style={{ color: '#8b5cf6' }} />
            <span style={{ color: 'white', fontSize: '16px', fontWeight: '500' }}>API Keys</span>
          </div>
          <div style={{ color: 'white', fontSize: '24px', fontWeight: '600' }}>5</div>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '24px'
      }}>
        {/* Security Settings */}
        <div>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <h3 style={{
              color: 'white',
              margin: 0,
              fontSize: '18px',
              fontWeight: '600'
            }}>
              Security Settings
            </h3>
            
            <div style={{
              display: 'flex',
              gap: '8px'
            }}>
              {categories.map(category => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  style={{
                    padding: '4px 8px',
                    background: selectedCategory === category 
                      ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                      : 'rgba(255,255,255,0.1)',
                    border: 'none',
                    borderRadius: '12px',
                    color: 'white',
                    cursor: 'pointer',
                    fontSize: '11px',
                    fontWeight: '500'
                  }}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          <div style={{
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '12px',
            overflow: 'hidden'
          }}>
            {filteredSettings.map((setting, index) => (
              <div
                key={setting.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '16px 20px',
                  borderBottom: index < filteredSettings.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none'
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{
                    color: 'white',
                    fontSize: '14px',
                    fontWeight: '500',
                    marginBottom: '4px'
                  }}>
                    {setting.name}
                  </div>
                  <div style={{
                    color: '#9ca3af',
                    fontSize: '12px'
                  }}>
                    {setting.description}
                  </div>
                </div>
                
                <button
                  onClick={() => toggleSetting(setting.id)}
                  style={{
                    width: '44px',
                    height: '24px',
                    borderRadius: '12px',
                    border: 'none',
                    background: setting.enabled 
                      ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                      : 'rgba(156, 163, 175, 0.3)',
                    cursor: 'pointer',
                    position: 'relative',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    background: 'white',
                    position: 'absolute',
                    top: '3px',
                    left: setting.enabled ? '23px' : '3px',
                    transition: 'left 0.2s ease'
                  }} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Security Events */}
        <div>
          <h3 style={{
            color: 'white',
            margin: '0 0 16px 0',
            fontSize: '18px',
            fontWeight: '600'
          }}>
            Recent Security Events
          </h3>

          <div style={{
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '12px',
            overflow: 'hidden',
            maxHeight: '400px',
            overflowY: 'auto'
          }}>
            {securityEvents.map((event, index) => (
              <div
                key={event.id}
                onClick={() => setShowEventDetails(event)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px 16px',
                  borderBottom: index < securityEvents.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: `${getEventColor(event.type)}20`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginRight: '12px'
                }}>
                  {getEventIcon(event.type)}
                </div>
                
                <div style={{ flex: 1 }}>
                  <div style={{
                    color: 'white',
                    fontSize: '14px',
                    fontWeight: '500',
                    marginBottom: '2px'
                  }}>
                    {event.event}
                  </div>
                  <div style={{
                    color: '#9ca3af',
                    fontSize: '12px'
                  }}>
                    {event.user} • {event.time}
                  </div>
                </div>
                
                <div style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: getEventColor(event.type)
                }} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Event Details Modal */}
      {showEventDetails && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            padding: '30px',
            borderRadius: '15px',
            border: '1px solid rgba(255,255,255,0.2)',
            maxWidth: '500px',
            width: '90%'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '20px'
            }}>
              <h3 style={{
                color: 'white',
                margin: 0,
                fontSize: '20px',
                fontWeight: '600'
              }}>
                Security Event Details
              </h3>
              <button
                onClick={() => setShowEventDetails(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#9ca3af',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ color: '#9ca3af', fontSize: '12px', marginBottom: '4px', display: 'block' }}>
                  Event Type
                </label>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  {getEventIcon(showEventDetails.type)}
                  <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                    {showEventDetails.event}
                  </span>
                </div>
              </div>

              <div>
                <label style={{ color: '#9ca3af', fontSize: '12px', marginBottom: '4px', display: 'block' }}>
                  User
                </label>
                <span style={{ color: 'white', fontSize: '14px' }}>
                  {showEventDetails.user}
                </span>
              </div>

              <div>
                <label style={{ color: '#9ca3af', fontSize: '12px', marginBottom: '4px', display: 'block' }}>
                  Time
                </label>
                <span style={{ color: 'white', fontSize: '14px' }}>
                  {showEventDetails.time}
                </span>
              </div>

              {showEventDetails.ip && (
                <div>
                  <label style={{ color: '#9ca3af', fontSize: '12px', marginBottom: '4px', display: 'block' }}>
                    IP Address
                  </label>
                  <span style={{ color: 'white', fontSize: '14px', fontFamily: 'monospace' }}>
                    {showEventDetails.ip}
                  </span>
                </div>
              )}

              {showEventDetails.location && (
                <div>
                  <label style={{ color: '#9ca3af', fontSize: '12px', marginBottom: '4px', display: 'block' }}>
                    Location
                  </label>
                  <span style={{ color: 'white', fontSize: '14px' }}>
                    {showEventDetails.location}
                  </span>
                </div>
              )}
            </div>

            <div style={{
              display: 'flex',
              gap: '12px',
              marginTop: '24px'
            }}>
              <button
                onClick={() => setShowEventDetails(null)}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: 'rgba(156, 163, 175, 0.2)',
                  border: '1px solid rgba(156, 163, 175, 0.3)',
                  color: '#9ca3af',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                Close
              </button>
              {(showEventDetails.type === 'warning' || showEventDetails.type === 'error') && (
                <button
                  style={{
                    flex: 1,
                    padding: '12px',
                    background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                    border: 'none',
                    color: 'white',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  Block IP
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SecurityView;