import React, { useState, useEffect } from 'react';
import { 
  BarChart3, TrendingUp, Users, MessageSquare, Clock, 
  Activity, Eye, Download, Filter, Calendar, Search,
  Zap, Target, Award, AlertTriangle, CheckCircle,
  ArrowUp, ArrowDown, Minus, RefreshCw
} from 'lucide-react';

interface AnalyticsMetric {
  id: string;
  name: string;
  value: number;
  previousValue: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  change: number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

interface QueryLog {
  id: string;
  query: string;
  timestamp: Date;
  responseTime: number;
  mode: string;
  userId: string;
  success: boolean;
  tokens: number;
}

interface UserBehavior {
  userId: string;
  sessionDuration: number;
  queriesCount: number;
  documentsUploaded: number;
  lastActive: Date;
  preferredMode: string;
  avgResponseTime: number;
}

interface PerformanceMetric {
  timestamp: Date;
  responseTime: number;
  memoryUsage: number;
  cpuUsage: number;
  activeUsers: number;
  errorRate: number;
}

export const EnhancedAnalyticsDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [selectedMetric, setSelectedMetric] = useState<string>('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Mock data
  const [metrics] = useState<AnalyticsMetric[]>([
    {
      id: 'total_queries',
      name: 'Total Queries',
      value: 1247,
      previousValue: 1089,
      unit: '',
      trend: 'up',
      change: 14.5,
      icon: MessageSquare,
      color: '#10b981'
    },
    {
      id: 'active_users',
      name: 'Active Users',
      value: 89,
      previousValue: 76,
      unit: '',
      trend: 'up',
      change: 17.1,
      icon: Users,
      color: '#3b82f6'
    },
    {
      id: 'avg_response_time',
      name: 'Avg Response Time',
      value: 1.2,
      previousValue: 1.8,
      unit: 's',
      trend: 'down',
      change: -33.3,
      icon: Clock,
      color: '#f59e0b'
    },
    {
      id: 'success_rate',
      name: 'Success Rate',
      value: 98.5,
      previousValue: 97.2,
      unit: '%',
      trend: 'up',
      change: 1.3,
      icon: CheckCircle,
      color: '#10b981'
    },
    {
      id: 'documents_processed',
      name: 'Documents Processed',
      value: 342,
      previousValue: 298,
      unit: '',
      trend: 'up',
      change: 14.8,
      icon: Eye,
      color: '#8b5cf6'
    },
    {
      id: 'error_rate',
      name: 'Error Rate',
      value: 1.5,
      previousValue: 2.8,
      unit: '%',
      trend: 'down',
      change: -46.4,
      icon: AlertTriangle,
      color: '#ef4444'
    }
  ]);

  const [queryLogs] = useState<QueryLog[]>([
    {
      id: '1',
      query: 'Summarize the latest research on quantum computing',
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      responseTime: 1200,
      mode: 'fact_checked',
      userId: 'user_123',
      success: true,
      tokens: 450
    },
    {
      id: '2',
      query: 'What are the implications of AI in healthcare?',
      timestamp: new Date(Date.now() - 12 * 60 * 1000),
      responseTime: 890,
      mode: 'chain_of_thought',
      userId: 'user_456',
      success: true,
      tokens: 320
    },
    {
      id: '3',
      query: 'Analyze this research paper on climate change',
      timestamp: new Date(Date.now() - 18 * 60 * 1000),
      responseTime: 2100,
      mode: 'standard',
      userId: 'user_789',
      success: true,
      tokens: 680
    }
  ]);

  const [userBehaviors] = useState<UserBehavior[]>([
    {
      userId: 'user_123',
      sessionDuration: 45,
      queriesCount: 12,
      documentsUploaded: 3,
      lastActive: new Date(Date.now() - 10 * 60 * 1000),
      preferredMode: 'fact_checked',
      avgResponseTime: 1100
    },
    {
      userId: 'user_456',
      sessionDuration: 32,
      queriesCount: 8,
      documentsUploaded: 1,
      lastActive: new Date(Date.now() - 5 * 60 * 1000),
      preferredMode: 'chain_of_thought',
      avgResponseTime: 950
    }
  ]);

  const [performanceData] = useState<PerformanceMetric[]>(
    Array.from({ length: 24 }, (_, i) => ({
      timestamp: new Date(Date.now() - (23 - i) * 60 * 60 * 1000),
      responseTime: 800 + Math.random() * 800,
      memoryUsage: 60 + Math.random() * 30,
      cpuUsage: 20 + Math.random() * 40,
      activeUsers: Math.floor(50 + Math.random() * 50),
      errorRate: Math.random() * 5
    }))
  );

  const refreshData = () => {
    setIsLoading(true);
    setTimeout(() => {
      setLastUpdated(new Date());
      setIsLoading(false);
    }, 1000);
  };

  const formatNumber = (num: number, unit: string = '') => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M${unit}`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K${unit}`;
    }
    return `${num}${unit}`;
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return <ArrowUp style={{ width: '12px', height: '12px' }} />;
      case 'down': return <ArrowDown style={{ width: '12px', height: '12px' }} />;
      default: return <Minus style={{ width: '12px', height: '12px' }} />;
    }
  };

  const getTrendColor = (trend: 'up' | 'down' | 'stable', isPositive: boolean = true) => {
    if (trend === 'stable') return '#9ca3af';
    const goodTrend = isPositive ? trend === 'up' : trend === 'down';
    return goodTrend ? '#10b981' : '#ef4444';
  };

  return (
    <div style={{
      padding: '24px',
      background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1b69 100%)',
      color: 'white',
      minHeight: '100vh',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '32px'
      }}>
        <div>
          <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: '#10b981' }}>
            📊 Analytics Dashboard
          </h1>
          <p style={{ margin: 0, color: '#9ca3af' }}>
            Comprehensive insights into system performance and user behavior
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            style={{
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '8px',
              padding: '8px 12px',
              color: 'white',
              fontSize: '14px',
              outline: 'none'
            }}
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          
          <button
            onClick={refreshData}
            disabled={isLoading}
            style={{
              background: 'rgba(16, 185, 129, 0.2)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: '#10b981',
              padding: '8px 12px',
              borderRadius: '8px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '14px'
            }}
          >
            <RefreshCw style={{ 
              width: '14px', 
              height: '14px',
              animation: isLoading ? 'spin 1s linear infinite' : 'none'
            }} />
            Refresh
          </button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '20px',
        marginBottom: '32px'
      }}>
        {metrics.map((metric) => {
          const IconComponent = metric.icon;
          const isPositiveMetric = !['avg_response_time', 'error_rate'].includes(metric.id);
          
          return (
            <div
              key={metric.id}
              style={{
                background: 'rgba(255,255,255,0.05)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '16px',
                padding: '24px',
                transition: 'all 0.3s ease',
                cursor: 'pointer'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '8px'
                  }}>
                    <IconComponent style={{ width: '20px', height: '20px', color: metric.color }} />
                    <span style={{ fontSize: '14px', color: '#9ca3af' }}>{metric.name}</span>
                  </div>
                  
                  <div style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '8px' }}>
                    {formatNumber(metric.value, metric.unit)}
                  </div>
                  
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '12px',
                    color: getTrendColor(metric.trend, isPositiveMetric)
                  }}>
                    {getTrendIcon(metric.trend)}
                    <span>
                      {Math.abs(metric.change).toFixed(1)}% vs previous {timeRange}
                    </span>
                  </div>
                </div>
                
                <div style={{
                  width: '60px',
                  height: '40px',
                  background: `linear-gradient(45deg, ${metric.color}20, ${metric.color}10)`,
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <TrendingUp style={{ width: '20px', height: '20px', color: metric.color }} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detailed Analytics Sections */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* Query Logs */}
        <div style={{
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '16px',
          padding: '24px'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: 0, color: '#10b981', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MessageSquare style={{ width: '20px', height: '20px' }} />
              Recent Query Logs
            </h3>
            <button style={{
              background: 'rgba(59, 130, 246, 0.2)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              color: '#60a5fa',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: 'pointer'
            }}>
              View All
            </button>
          </div>
          
          <div style={{ maxHeight: '300px', overflow: 'auto' }}>
            {queryLogs.map((log) => (
              <div
                key={log.id}
                style={{
                  background: 'rgba(255,255,255,0.05)',
                  borderRadius: '8px',
                  padding: '16px',
                  marginBottom: '12px',
                  border: '1px solid rgba(255,255,255,0.1)'
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '8px'
                }}>
                  <div style={{ flex: 1, marginRight: '12px' }}>
                    <div style={{ fontSize: '14px', marginBottom: '4px' }}>
                      "{log.query}"
                    </div>
                    <div style={{
                      display: 'flex',
                      gap: '12px',
                      fontSize: '12px',
                      color: '#9ca3af'
                    }}>
                      <span>🕒 {log.timestamp.toLocaleTimeString()}</span>
                      <span>⚡ {log.responseTime}ms</span>
                      <span>🎯 {log.tokens} tokens</span>
                      <span style={{
                        color: log.mode === 'fact_checked' ? '#10b981' :
                              log.mode === 'chain_of_thought' ? '#60a5fa' : '#9ca3af'
                      }}>
                        🧠 {log.mode}
                      </span>
                    </div>
                  </div>
                  <div style={{
                    background: log.success ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                    color: log.success ? '#10b981' : '#ef4444',
                    padding: '4px 8px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: 'bold'
                  }}>
                    {log.success ? 'SUCCESS' : 'ERROR'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* User Behavior Summary */}
        <div style={{
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '16px',
          padding: '24px'
        }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#3b82f6', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users style={{ width: '20px', height: '20px' }} />
            User Behavior
          </h3>
          
          {userBehaviors.map((user, index) => (
            <div
              key={user.userId}
              style={{
                background: 'rgba(255,255,255,0.05)',
                borderRadius: '8px',
                padding: '16px',
                marginBottom: '12px'
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '8px'
              }}>
                <span style={{ fontSize: '14px', fontWeight: 'bold' }}>
                  User #{index + 1}
                </span>
                <span style={{
                  fontSize: '11px',
                  color: '#9ca3af',
                  background: 'rgba(255,255,255,0.1)',
                  padding: '2px 6px',
                  borderRadius: '10px'
                }}>
                  {user.preferredMode}
                </span>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
                <div>
                  <span style={{ color: '#9ca3af' }}>Session:</span> {user.sessionDuration}min
                </div>
                <div>
                  <span style={{ color: '#9ca3af' }}>Queries:</span> {user.queriesCount}
                </div>
                <div>
                  <span style={{ color: '#9ca3af' }}>Docs:</span> {user.documentsUploaded}
                </div>
                <div>
                  <span style={{ color: '#9ca3af' }}>Avg RT:</span> {user.avgResponseTime}ms
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance Chart */}
      <div style={{
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '16px',
        padding: '24px'
      }}>
        <h3 style={{ margin: '0 0 20px 0', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity style={{ width: '20px', height: '20px' }} />
          Performance Metrics ({timeRange})
        </h3>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>
              {performanceData[performanceData.length - 1]?.responseTime.toFixed(0)}ms
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Avg Response Time</div>
          </div>
          
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>
              {performanceData[performanceData.length - 1]?.memoryUsage.toFixed(1)}%
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Memory Usage</div>
          </div>
          
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>
              {performanceData[performanceData.length - 1]?.cpuUsage.toFixed(1)}%
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>CPU Usage</div>
          </div>
          
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#8b5cf6' }}>
              {performanceData[performanceData.length - 1]?.activeUsers}
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Active Users</div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{
        marginTop: '32px',
        padding: '16px',
        textAlign: 'center',
        fontSize: '12px',
        color: '#6b7280',
        borderTop: '1px solid rgba(255,255,255,0.1)'
      }}>
        Last updated: {lastUpdated.toLocaleString()} • 
        Data refreshes automatically every 30 seconds • 
        {metrics.reduce((sum, m) => sum + m.value, 0).toLocaleString()} total data points analyzed
      </div>
    </div>
  );
};