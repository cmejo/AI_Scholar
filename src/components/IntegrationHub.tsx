import { Calendar, Check, Database, Globe, Key, Mail, MessageSquare, Plus, Settings, Users, Webhook, X } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { integrationService } from '../services/integrationService';
import type { Integration } from '../types';

export const IntegrationHub: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [selectedIntegrationType, setSelectedIntegrationType] = useState<string>('');
  const [setupConfig, setSetupConfig] = useState<Record<string, unknown>>({});

  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = (): void => {
    // Mock integrations data
    const mockIntegrations: Integration[] = [
      {
        id: 'slack_1',
        type: 'slack',
        name: 'Slack Bot',
        config: { channels: ['#general', '#ai-support'] },
        status: 'active',
        lastSync: new Date()
      },
      {
        id: 'email_1',
        type: 'email',
        name: 'Email Support',
        config: { fromAddress: 'support@company.com' },
        status: 'active',
        lastSync: new Date()
      },
      {
        id: 'sso_1',
        type: 'sso',
        name: 'SAML SSO',
        config: { provider: 'okta' },
        status: 'inactive',
        lastSync: new Date()
      }
    ];
    setIntegrations(mockIntegrations);
  };

  const availableIntegrations = [
    {
      type: 'slack',
      name: 'Slack',
      description: 'Chat-based document queries and notifications',
      icon: <MessageSquare className="text-purple-400" size={24} />,
      category: 'Communication'
    },
    {
      type: 'teams',
      name: 'Microsoft Teams',
      description: 'Teams bot for document assistance',
      icon: <Users className="text-blue-400" size={24} />,
      category: 'Communication'
    },
    {
      type: 'email',
      name: 'Email',
      description: 'Query documents via email',
      icon: <Mail className="text-emerald-400" size={24} />,
      category: 'Communication'
    },
    {
      type: 'webhook',
      name: 'Webhooks',
      description: 'Real-time event notifications',
      icon: <Webhook className="text-yellow-400" size={24} />,
      category: 'API'
    },
    {
      type: 'sso',
      name: 'Single Sign-On',
      description: 'SAML, OAuth, and OIDC authentication',
      icon: <Key className="text-red-400" size={24} />,
      category: 'Security'
    },
    {
      type: 'api',
      name: 'REST API',
      description: 'External API integrations',
      icon: <Globe className="text-indigo-400" size={24} />,
      category: 'API'
    },
    {
      type: 'calendar',
      name: 'Calendar',
      description: 'Meeting preparation and scheduling',
      icon: <Calendar className="text-orange-400" size={24} />,
      category: 'Productivity'
    },
    {
      type: 'crm',
      name: 'CRM Systems',
      description: 'Salesforce, HubSpot, Pipedrive',
      icon: <Database className="text-pink-400" size={24} />,
      category: 'Business'
    }
  ];

  const setupIntegration = async (): Promise<void> => {
    try {
      let integration: Integration;
      
      switch (selectedIntegrationType) {
        case 'slack':
          integration = await integrationService.setupSlackIntegration(setupConfig as { botToken: string; signingSecret: string; channels: string[]; });
          break;
        case 'teams':
          integration = await integrationService.setupTeamsIntegration(setupConfig as { appId: string; appPassword: string; tenantId: string; });
          break;
        case 'email':
          integration = await integrationService.setupEmailIntegration(setupConfig as { smtpHost: string; smtpPort: number; username: string; password: string; fromAddress: string; });
          break;
        case 'sso':
          integration = await integrationService.setupSSOIntegration(setupConfig as { provider: "saml" | "oauth" | "oidc"; entityId: string; ssoUrl: string; certificate: string; });
          break;
        case 'webhook':
          integration = await integrationService.setupWebhook(setupConfig as { url: string; events: string[]; secret?: string; });
          break;
        case 'api':
          integration = await integrationService.setupAPIIntegration(setupConfig as { baseUrl: string; apiKey: string; endpoints: Record<string, string>; });
          break;
        default:
          throw new Error('Unknown integration type');
      }
      
      setIntegrations(prev => [...prev, integration]);
      setShowSetupModal(false);
      setSetupConfig({});
    } catch (error) {
      console.error('Failed to setup integration:', error instanceof Error ? error.message : String(error));
    }
  };

  const toggleIntegration = (integrationId: string): void => {
    setIntegrations(prev => prev.map(integration =>
      integration.id === integrationId
        ? { ...integration, status: integration.status === 'active' ? 'inactive' : 'active' }
        : integration
    ));
  };

  const removeIntegration = (integrationId: string): void => {
    setIntegrations(prev => prev.filter(integration => integration.id !== integrationId));
  };

  const getIntegrationConfig = (type: string) => {
    switch (type) {
      case 'slack':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Bot Token</label>
              <input
                type="password"
                value={(setupConfig.botToken as string) ?? ''}
                onChange={(e) => setSetupConfig({ ...setupConfig, botToken: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                placeholder="xoxb-..."
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Signing Secret</label>
              <input
                type="password"
                value={(setupConfig.signingSecret as string) ?? ''}
                onChange={(e) => setSetupConfig({ ...setupConfig, signingSecret: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                placeholder="Signing secret..."
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Channels (comma-separated)</label>
              <input
                type="text"
                value={(setupConfig.channels as string) ?? ''}
                onChange={(e) => setSetupConfig({ ...setupConfig, channels: e.target.value.split(',').map(c => c.trim()) })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                placeholder="#general, #support"
              />
            </div>
          </div>
        );
      
      case 'email':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">SMTP Host</label>
              <input
                type="text"
                value={(setupConfig.smtpHost as string) ?? ''}
                onChange={(e) => setSetupConfig({ ...setupConfig, smtpHost: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                placeholder="smtp.gmail.com"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">SMTP Port</label>
              <input
                type="number"
                value={(setupConfig.smtpPort as number) ?? ''}
                onChange={(e) => setSetupConfig({ ...setupConfig, smtpPort: parseInt(e.target.value) })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                placeholder="587"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Username</label>
              <input
                type="text"
                value={(setupConfig.username as string) ?? ''}
                onChange={(e) => setSetupConfig({ ...setupConfig, username: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                placeholder="your-email@domain.com"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Password</label>
              <input
                type="password"
                value={(setupConfig.password as string) ?? ''}
                onChange={(e) => setSetupConfig({ ...setupConfig, password: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                placeholder="App password or OAuth token"
              />
            </div>
          </div>
        );
      
      case 'sso':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Provider</label>
              <select
                value={(setupConfig.provider as string) ?? ''}
                onChange={(e) => setSetupConfig({ ...setupConfig, provider: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
              >
                <option value="">Select provider</option>
                <option value="saml">SAML</option>
                <option value="oauth">OAuth 2.0</option>
                <option value="oidc">OpenID Connect</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Entity ID</label>
              <input
                type="text"
                value={(setupConfig.entityId as string) ?? ''}
                onChange={(e) => setSetupConfig({ ...setupConfig, entityId: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                placeholder="https://your-app.com/saml/metadata"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">SSO URL</label>
              <input
                type="url"
                value={(setupConfig.ssoUrl as string) ?? ''}
                onChange={(e) => setSetupConfig({ ...setupConfig, ssoUrl: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                placeholder="https://idp.example.com/sso"
              />
            </div>
          </div>
        );
      
      default:
        return (
          <div className="text-center text-gray-400 py-8">
            Configuration form for {type} integration
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Integration Hub</h2>
          <p className="text-gray-400">Connect your RAG system with external services</p>
        </div>
        
        <button
          onClick={() => setShowSetupModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
        >
          <Plus size={16} />
          <span>Add Integration</span>
        </button>
      </div>

      {/* Active Integrations */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Active Integrations</h3>
        
        {integrations.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            No integrations configured yet. Add your first integration to get started.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {integrations.map((integration) => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onToggle={() => toggleIntegration(integration.id)}
                onRemove={() => removeIntegration(integration.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Available Integrations */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Available Integrations</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {availableIntegrations.map((integration) => (
            <div
              key={integration.type}
              className="border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors cursor-pointer"
              onClick={() => {
                setSelectedIntegrationType(integration.type);
                setShowSetupModal(true);
              }}
            >
              <div className="flex items-center space-x-3 mb-3">
                {integration.icon}
                <div>
                  <h4 className="text-white font-medium">{integration.name}</h4>
                  <span className="text-xs text-gray-400">{integration.category}</span>
                </div>
              </div>
              <p className="text-gray-400 text-sm">{integration.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Integration Statistics */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Integration Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">{integrations.length}</div>
            <div className="text-gray-400">Total Integrations</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-400">
              {integrations.filter(i => i.status === 'active').length}
            </div>
            <div className="text-gray-400">Active</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">247</div>
            <div className="text-gray-400">Events Today</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">98.5%</div>
            <div className="text-gray-400">Uptime</div>
          </div>
        </div>
      </div>

      {/* Setup Modal */}
      {showSetupModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">
                Setup {selectedIntegrationType.length > 0 ? availableIntegrations.find(i => i.type === selectedIntegrationType)?.name : 'Integration'}
              </h3>
              <button
                onClick={() => {
                  setShowSetupModal(false);
                  setSelectedIntegrationType('');
                  setSetupConfig({});
                }}
                className="text-gray-400 hover:text-white"
              >
                <X size={20} />
              </button>
            </div>
            
            {selectedIntegrationType.length === 0 ? (
              <div className="space-y-2">
                <p className="text-gray-400 mb-4">Select an integration type:</p>
                {availableIntegrations.map((integration) => (
                  <button
                    key={integration.type}
                    onClick={() => setSelectedIntegrationType(integration.type)}
                    className="w-full text-left p-3 border border-gray-700 rounded-lg hover:border-gray-600 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      {integration.icon}
                      <div>
                        <div className="text-white font-medium">{integration.name}</div>
                        <div className="text-gray-400 text-sm">{integration.description}</div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <>
                {getIntegrationConfig(selectedIntegrationType)}
                
                <div className="flex items-center justify-end space-x-3 mt-6">
                  <button
                    onClick={() => {
                      setSelectedIntegrationType('');
                      setSetupConfig({});
                    }}
                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => void setupIntegration()}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    Setup Integration
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

interface IntegrationCardProps {
  integration: Integration;
  onToggle: () => void;
  onRemove: () => void;
}

const IntegrationCard: React.FC<IntegrationCardProps> = ({
  integration,
  onToggle,
  onRemove
}) => {
  const getIntegrationIcon = (type: string): JSX.Element => {
    switch (type) {
      case 'slack': return <MessageSquare className="text-purple-400" size={20} />;
      case 'teams': return <Users className="text-blue-400" size={20} />;
      case 'email': return <Mail className="text-emerald-400" size={20} />;
      case 'webhook': return <Webhook className="text-yellow-400" size={20} />;
      case 'sso': return <Key className="text-red-400" size={20} />;
      case 'api': return <Globe className="text-indigo-400" size={20} />;
      default: return <Settings className="text-gray-400" size={20} />;
    }
  };

  return (
    <div className="border border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          {getIntegrationIcon(integration.type)}
          <div>
            <h4 className="text-white font-medium">{integration.name}</h4>
            <span className="text-xs text-gray-400 capitalize">{integration.type}</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={onToggle}
            className={`p-1 rounded transition-colors ${
              integration.status === 'active'
                ? 'text-emerald-400 hover:text-emerald-300'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            {integration.status === 'active' ? <Check size={16} /> : <X size={16} />}
          </button>
          
          <button
            onClick={onRemove}
            className="p-1 text-red-400 hover:text-red-300 transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Status:</span>
          <span className={`px-2 py-1 rounded-full text-xs ${
            integration.status === 'active'
              ? 'bg-emerald-600/20 text-emerald-400'
              : integration.status === 'error'
              ? 'bg-red-600/20 text-red-400'
              : 'bg-gray-600/20 text-gray-400'
          }`}>
            {integration.status}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Last Sync:</span>
          <span className="text-white text-xs">
            {integration.lastSync.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
};