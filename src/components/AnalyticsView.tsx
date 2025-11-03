import React, { useState, useEffect } from 'react';
import { 
  BarChart3, TrendingUp, Users, MessageSquare, FileText, 
  Activity, Clock, Zap, RefreshCw, Calendar, Download 
} from 'lucide-react';

interface AnalyticsData {
  totalQueries: number;
  avgResponseTime: number;
  successRate: number;
  activeUsers: number;
  documentsProcessed: number;
  workflowsExecuted: number;
}

const AnalyticsView: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData>({
    totalQueries: 1234,
    avgResponseTime: 1.2,
    successRate: 98.5,
    activeUsers: 12,
    documentsProcessed: 56,
    workflowsExecuted: 89
  });
  
  const [timeRange, setTimeRange] = useState('7d');
  const [isLoading, setIsLoading] = useState(false);

  const refreshData = async () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setAnalyticsData(prev => ({
        ...prev,
        totalQueries: prev.totalQueries + Math.floor(Math.random() * 50),
        avgResponseTime: Math.round((prev.avgResponseTime + (Math.random() - 0.5) * 0.2) * 10) / 10,
        successRate: Math.round((prev.successRate + (Math.random() - 0.5) * 2) * 10) / 10
      }));
      setIsLoading(false);
    }, 1000);
  };

  const MetricCard: React.FC<{
    title: string;
    value: string | number;
    change: string;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, change, icon, color }) => (
    <div style={{
      background: 'rgba(255,255,255,0.05)',
      borderRadius: '12px',
      padding: '20px',
      border: '1px solid rgba(255,255,255,0.1)'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '12px'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '8px',
          background: `linear-gradient(135deg, ${color}20 0%, ${color}40 100%)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: color
        }}>
          {icon}
        </div>
        <span style={{
          fontSize: '12px',
          color: change.startsWith('+') ? '#10b981' : '#ef4444',
          fontWeight: '500'
        }}>
          {change}
        </span>
      </div>
      
      <h3 style={{
        color: 'white',
        margin: '0 0 4px 0',
        fontSize: '24px',
        fontWeight: '600'
      }}>
        {value}
      </h3>
      
      <p style={{
        color: '#9ca3af',
        margin: 0,
        fontSize: '14px'
      }}>
        {title}
      </p>
    </div>
  );

  const ChartPlaceholder: React.FC<{ title: string; height?: string }> = ({ title, height = '200px' }) => (
    <div style={{
      background: 'rgba(255,255,255,0.05)',
      borderRadius: '12px',
      padding: '20px',
      border: '1px solid rgba(255,255,255,0.1)',
      height
    }}>
      <h3 style={{
        color: 'white',
        margin: '0 0 16px 0',
        fontSize: '16px',
        fontWeight: '500'
      }}>
        {title}
      </h3>
      
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: 'calc(100% - 40px)',
        color: '#9ca3af',
        flexDirection: 'column',
        gap: '8px'
      }}>
        <BarChart3 size={32} />
        <span style={{ fontSize: '14px' }}>Chart visualization coming soon</span>
      </div>
    </div>
  );

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
            Analytics Dashboard
          </h2>
          <p style={{
            color: '#9ca3af',
            margin: '4px 0 0 0',
            fontSize: '14px'
          }}>
            Monitor your AI Scholar usage and performance
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            style={{
              padding: '8px 12px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '6px',
              color: 'white',
              fontSize: '14px',
              outline: 'none'
            }}
          >
            <option value="24h" style={{ background: '#1a1a2e' }}>Last 24 hours</option>
            <option value="7d" style={{ background: '#1a1a2e' }}>Last 7 days</option>
            <option value="30d" style={{ background: '#1a1a2e' }}>Last 30 days</option>
            <option value="90d" style={{ background: '#1a1a2e' }}>Last 90 days</option>
          </select>
          
          <button
            onClick={refreshData}
            disabled={isLoading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 12px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '6px',
              color: 'white',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            <RefreshCw 
              size={14} 
              style={{ 
                animation: isLoading ? 'spin 1s linear infinite' : 'none' 
              }} 
            />
            Refresh
          </button>
          
          <button style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 12px',
            background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
            border: 'none',
            borderRadius: '6px',
            color: 'white',
            cursor: 'pointer',
            fontSize: '14px'
          }}>
            <Download size={14} />
            Export
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <MetricCard
          title="Total Queries"
          value={analyticsData.totalQueries.toLocaleString()}
          change="+12.5%"
          icon={<MessageSquare size={20} />}
          color="#60a5fa"
        />
        
        <MetricCard
          title="Avg Response Time"
          value={`${analyticsData.avgResponseTime}s`}
          change="-5.2%"
          icon={<Clock size={20} />}
          color="#10b981"
        />
        
        <MetricCard
          title="Success Rate"
          value={`${analyticsData.successRate}%`}
          change="+2.1%"
          icon={<TrendingUp size={20} />}
          color="#f59e0b"
        />
        
        <MetricCard
          title="Active Users"
          value={analyticsData.activeUsers}
          change="+8.3%"
          icon={<Users size={20} />}
          color="#8b5cf6"
        />
        
        <MetricCard
          title="Documents Processed"
          value={analyticsData.documentsProcessed}
          change="+15.7%"
          icon={<FileText size={20} />}
          color="#ef4444"
        />
        
        <MetricCard
          title="Workflows Executed"
          value={analyticsData.workflowsExecuted}
          change="+22.4%"
          icon={<Zap size={20} />}
          color="#06b6d4"
        />
      </div>

      {/* Charts */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1fr',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <ChartPlaceholder title="Query Volume Over Time" height="300px" />
        <ChartPlaceholder title="Response Time Distribution" height="300px" />
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '16px'
      }}>
        <ChartPlaceholder title="Most Active Users" height="250px" />
        <ChartPlaceholder title="Popular Query Types" height="250px" />
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default AnalyticsView;