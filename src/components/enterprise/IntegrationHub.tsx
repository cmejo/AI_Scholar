import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { 
  Plug, Settings, Plus, Edit, Trash2, RefreshCw,
  CheckCircle, XCircle, AlertCircle, Clock, Zap,
  Database, Cloud, Mail, MessageSquare, BarChart3,
  Shield, Key, Globe, Server, Activity, Link
} from 'lucide-react';

interface Integration {
  id: string;
  name: string;
  type: 'database' | 'cloud_storage' | 'email' | 'messaging' | 'analytics' | 'security' | 'api';
  provider: string;
  status: 'connected' | 'disconnected' | 'error' | 'syncing';
  lastSync?: Date;
  config: {
    endpoint?: string;
    apiKey?: string;
    credentials?: Record<string, any>;
    settings?: Record<string, any>;
  };
  metrics: {
    totalRequests: number;
    successRate: number;
    avgResponseTime: number;
    lastError?: string;
  };
  isActive: boolean;
}

interface IntegrationTemplate {
  id: string;
  name: string;
  provider: string;
  type: Integration['type'];
  description: string;
  icon: React.ComponentType<any>;
  popular: boolean;
  setupComplexity: 'easy' | 'medium' | 'advanced';
}

export const IntegrationHub: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [templates, setTemplates] = useState<IntegrationTemplate[]>([]);
  const [activeTab, setActiveTab] = useState<'active' | 'available' | 'logs' | 'settings'>('active');
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [isConfiguring, setIsConfiguring] = useState(false);

  // Mock data
  useEffect(() => {
    const mockIntegrations: Integration[] = [
      {
        id: 'int_1',
        name: 'PostgreSQL Database',
        type: 'database',
        provider: 'PostgreSQL',
        status: 'connected',
        lastSync: new Date(Date.now() - 5 * 60 * 1000),
        config: {
          endpoint: 'localhost:5432',
          credentials: { database: 'ai_scholar' }
        },
        metrics: {
          totalRequests: 1247,
          successRate: 99.2,
          avgResponseTime: 45,
        },
        isActive: true
      },
      {
        id: 'int_2',
        name: 'AWS S3 Storage',
        type: 'cloud_storage',
        provider: 'Amazon Web Services',
        status: 'connected',
        lastSync: new Date(Date.now() - 15 * 60 * 1000),
        config: {
          endpoint: 's3.amazonaws.com',
          settings: { region: 'us-east-1', bucket: 'ai-scholar-docs' }
        },
        metrics: {
          totalRequests: 456,
          successRate: 98.7,
          avgResponseTime: 120,
        },
        isActive: true
      },
      {
        id: 'int_3',
        name: 'SendGrid Email',
        type: 'email',
        provider: 'SendGrid',
        status: 'error',
        lastSync: new Date(Date.now() - 2 * 60 * 60 * 1000),
        config: {
          endpoint: 'api.sendgrid.com',
        },
        metrics: {
          totalRequests: 89,
          successRate: 87.6,
          avgResponseTime: 200,
          lastError: 'API rate limit exceeded'
        },
        isActive: false
      },
      {
        id: 'int_4',
        name: 'Slack Notifications',
        type: 'messaging',
        provider: 'Slack',
        status: 'connected',
        lastSync: new Date(Date.now() - 1 * 60 * 1000),
        config: {
          endpoint: 'hooks.slack.com',
          settings: { channel: '#ai-scholar-alerts' }
        },
        metrics: {
          totalRequests: 234,
          successRate: 96.8,
          avgResponseTime: 80,
        },
        isActive: true
      }
    ];

    const mockTemplates: IntegrationTemplate[] = [
      {
        id: 'tpl_1',
        name: 'Google Drive',
        provider: 'Google',
        type: 'cloud_storage',
        description: 'Store and sync documents with Google Drive',
        icon: Cloud,
        popular: true,
        setupComplexity: 'easy'
      },
      {
        id: 'tpl_2',
        name: 'Microsoft Teams',
        provider: 'Microsoft',
        type: 'messaging',
        description: 'Send notifications and updates to Teams channels',
        icon: MessageSquare,
        popular: true,
        setupComplexity: 'medium'
      },
      {
        id: 'tpl_3',
        name: 'Google Analytics',
        provider: 'Google',
        type: 'analytics',
        description: 'Track user behavior and application usage',
        icon: BarChart3,
        popular: false,
        setupComplexity: 'medium'
      },
      {
        id: 'tpl_4',
        name: 'Auth0',
        provider: 'Auth0',
        type: 'security',
        description: 'Enterprise authentication and authorization',
        icon: Shield,
        popular: true,
        setupComplexity: 'advanced'
      },
      {
        id: 'tpl_5',
        name: 'MongoDB',
        provider: 'MongoDB',
        type: 'database',
        description: 'NoSQL document database integration',
        icon: Database,
        popular: false,
        setupComplexity: 'medium'
      },
      {
        id: 'tpl_6',
        name: 'Webhook API',
        provider: 'Custom',
        type: 'api',
        description: 'Custom webhook integration for external services',
        icon: Link,
        popular: false,
        setupComplexity: 'advanced'
      }
    ];

    setIntegrations(mockIntegrations);
    setTemplates(mockTemplates);
  }, []);

  const getStatusIcon = (status: Integration['status']) => {
    switch (status) {
      case 'connected': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'disconnected': return <XCircle className="w-4 h-4 text-gray-500" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'syncing': return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
    }
  };

  const getTypeIcon = (type: Integration['type']) => {
    switch (type) {
      case 'database': return <Database className="w-5 h-5" />;
      case 'cloud_storage': return <Cloud className="w-5 h-5" />;
      case 'email': return <Mail className="w-5 h-5" />;
      case 'messaging': return <MessageSquare className="w-5 h-5" />;
      case 'analytics': return <BarChart3 className="w-5 h-5" />;
      case 'security': return <Shield className="w-5 h-5" />;
      case 'api': return <Link className="w-5 h-5" />;
    }
  };

  const getComplexityColor = (complexity: IntegrationTemplate['setupComplexity']) => {
    switch (complexity) {
      case 'easy': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
    }
  };

  const testConnection = async (integrationId: string) => {
    setIntegrations(prev =>
      prev.map(int =>
        int.id === integrationId ? { ...int, status: 'syncing' } : int
      )
    );

    // Simulate API call
    setTimeout(() => {
      setIntegrations(prev =>
        prev.map(int =>
          int.id === integrationId 
            ? { 
                ...int, 
                status: Math.random() > 0.2 ? 'connected' : 'error',
                lastSync: new Date()
              } 
            : int
        )
      );
    }, 2000);
  };

  const toggleIntegration = (integrationId: string) => {
    setIntegrations(prev =>
      prev.map(int =>
        int.id === integrationId ? { ...int, isActive: !int.isActive } : int
      )
    );
  };

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Plug className="w-8 h-8 text-blue-600" />
            Integration Hub
          </h1>
          <p className="text-gray-600 mt-1">Seamless third-party service connections and API management</p>
        </div>
        
        <div className="flex gap-3">
          <Button variant="outline" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Monitor
          </Button>
          <Button className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Integration
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100">Active Integrations</p>
                <p className="text-3xl font-bold">{integrations.filter(i => i.isActive).length}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100">Connected Services</p>
                <p className="text-3xl font-bold">{integrations.filter(i => i.status === 'connected').length}</p>
              </div>
              <Plug className="w-8 h-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100">API Requests</p>
                <p className="text-3xl font-bold">
                  {integrations.reduce((acc, i) => acc + i.metrics.totalRequests, 0)}
                </p>
              </div>
              <Zap className="w-8 h-8 text-purple-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-orange-500 to-orange-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100">Success Rate</p>
                <p className="text-3xl font-bold">
                  {Math.round(integrations.reduce((acc, i) => acc + i.metrics.successRate, 0) / integrations.length)}%
                </p>
              </div>
              <Activity className="w-8 h-8 text-orange-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-1 bg-gray-200 p-1 rounded-lg">
        {[
          { id: 'active', label: 'Active Integrations', icon: CheckCircle },
          { id: 'available', label: 'Available Services', icon: Plus },
          { id: 'logs', label: 'Activity Logs', icon: Activity },
          { id: 'settings', label: 'Settings', icon: Settings }
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
      {activeTab === 'active' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {integrations.map(integration => (
            <Card key={integration.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    {getTypeIcon(integration.type)}
                    <div>
                      <CardTitle className="text-lg">{integration.name}</CardTitle>
                      <p className="text-sm text-gray-600">{integration.provider}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(integration.status)}
                    <span className="text-sm font-medium capitalize">{integration.status}</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Integration Metrics */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Requests:</span>
                      <span className="font-semibold ml-1">{integration.metrics.totalRequests}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Success Rate:</span>
                      <span className="font-semibold ml-1">{integration.metrics.successRate}%</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Avg Response:</span>
                      <span className="font-semibold ml-1">{integration.metrics.avgResponseTime}ms</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Last Sync:</span>
                      <span className="font-semibold ml-1">
                        {integration.lastSync ? integration.lastSync.toLocaleTimeString() : 'Never'}
                      </span>
                    </div>
                  </div>

                  {/* Error Message */}
                  {integration.metrics.lastError && (
                    <div className="bg-red-50 border border-red-200 rounded p-3">
                      <p className="text-red-800 text-sm">{integration.metrics.lastError}</p>
                    </div>
                  )}

                  {/* Connection Details */}
                  <div className="bg-gray-50 rounded p-3">
                    <h5 className="text-sm font-medium mb-2">Connection Details:</h5>
                    <div className="space-y-1 text-xs">
                      {integration.config.endpoint && (
                        <div><span className="text-gray-600">Endpoint:</span> {integration.config.endpoint}</div>
                      )}
                      {integration.config.settings && Object.entries(integration.config.settings).map(([key, value]) => (
                        <div key={key}><span className="text-gray-600">{key}:</span> {String(value)}</div>
                      ))}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => testConnection(integration.id)}
                      disabled={integration.status === 'syncing'}
                    >
                      <RefreshCw className={`w-3 h-3 mr-1 ${integration.status === 'syncing' ? 'animate-spin' : ''}`} />
                      Test
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => toggleIntegration(integration.id)}
                    >
                      {integration.isActive ? 'Disable' : 'Enable'}
                    </Button>
                    <Button size="sm" variant="outline">
                      <Settings className="w-3 h-3" />
                    </Button>
                    <Button size="sm" variant="outline">
                      <Edit className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'available' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map(template => (
            <Card key={template.id} className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <template.icon className="w-6 h-6 text-blue-600" />
                    <div>
                      <h3 className="font-medium">{template.name}</h3>
                      <p className="text-sm text-gray-600">{template.provider}</p>
                    </div>
                  </div>
                  {template.popular && (
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                      Popular
                    </span>
                  )}
                </div>
                
                <p className="text-sm text-gray-600 mb-4">{template.description}</p>
                
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-gray-600">Setup:</span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getComplexityColor(template.setupComplexity)}`}>
                    {template.setupComplexity}
                  </span>
                </div>
                
                <Button size="sm" className="w-full">
                  <Plus className="w-3 h-3 mr-1" />
                  Add Integration
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'logs' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Integration Activity Logs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {[
                { time: '2 minutes ago', integration: 'PostgreSQL Database', action: 'Connection successful', status: 'success' },
                { time: '5 minutes ago', integration: 'AWS S3 Storage', action: 'File uploaded: document.pdf', status: 'success' },
                { time: '12 minutes ago', integration: 'Slack Notifications', action: 'Message sent to #ai-scholar-alerts', status: 'success' },
                { time: '1 hour ago', integration: 'SendGrid Email', action: 'API rate limit exceeded', status: 'error' },
                { time: '2 hours ago', integration: 'PostgreSQL Database', action: 'Query executed: SELECT * FROM users', status: 'success' },
                { time: '3 hours ago', integration: 'AWS S3 Storage', action: 'Bucket sync completed', status: 'success' }
              ].map((log, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div className="flex items-center gap-3">
                    {log.status === 'success' ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-500" />
                    )}
                    <div>
                      <div className="font-medium text-sm">{log.integration}</div>
                      <div className="text-sm text-gray-600">{log.action}</div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">{log.time}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'settings' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Global Settings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-medium">Auto-retry failed connections</div>
                    <div className="text-sm text-gray-600">Automatically retry failed API calls</div>
                  </div>
                  <input type="checkbox" defaultChecked className="rounded" />
                </div>
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-medium">Connection timeout</div>
                    <div className="text-sm text-gray-600">Maximum wait time for API responses</div>
                  </div>
                  <select className="border rounded px-2 py-1">
                    <option>30 seconds</option>
                    <option>60 seconds</option>
                    <option>120 seconds</option>
                  </select>
                </div>
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-medium">Rate limiting</div>
                    <div className="text-sm text-gray-600">Enable rate limiting for API calls</div>
                  </div>
                  <input type="checkbox" defaultChecked className="rounded" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="w-5 h-5" />
                API Key Management
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>Master API Key</span>
                  <Button size="sm" variant="outline">
                    <Key className="w-3 h-3 mr-1" />
                    Regenerate
                  </Button>
                </div>
                <div className="flex justify-between items-center">
                  <span>Webhook Secret</span>
                  <Button size="sm" variant="outline">
                    <RefreshCw className="w-3 h-3 mr-1" />
                    Rotate
                  </Button>
                </div>
                <div className="flex justify-between items-center">
                  <span>SSL Certificates</span>
                  <Button size="sm" variant="outline">
                    <Shield className="w-3 h-3 mr-1" />
                    Update
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};