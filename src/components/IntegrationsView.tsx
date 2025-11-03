import React, { useState } from 'react';
import { 
  Puzzle, Plus, Settings, CheckCircle, AlertCircle, Eye, EyeOff, 
  ExternalLink, RefreshCw, Key, Globe, Database, X, Edit
} from 'lucide-react';

interface Integration {
  id: number;
  name: string;
  icon: string;
  status: 'Connected' | 'Available' | 'Error';
  description: string;
  apiKey?: string;
  category: 'AI Models' | 'Communication' | 'Storage' | 'Analytics' | 'Development';
  features: string[];
  setupUrl?: string;
}

const IntegrationsView: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([
    { 
      id: 1, 
      name: 'OpenAI GPT', 
      icon: '🤖', 
      status: 'Connected', 
      description: 'Advanced language models for chat and completion', 
      apiKey: 'sk-...abc123',
      category: 'AI Models',
      features: ['GPT-4', 'GPT-3.5-turbo', 'Text Completion', 'Chat Completion'],
      setupUrl: 'https://platform.openai.com/api-keys'
    },
    { 
      id: 2, 
      name: 'Hugging Face', 
      icon: '🤗', 
      status: 'Available', 
      description: '100,000+ open-source AI models', 
      apiKey: '',
      category: 'AI Models',
      features: ['Transformers', 'Datasets', 'Model Hub', 'Inference API'],
      setupUrl: 'https://huggingface.co/settings/tokens'
    },
    { 
      id: 3, 
      name: 'Anthropic Claude', 
      icon: '🧠', 
      status: 'Available', 
      description: 'Safe and helpful AI assistant', 
      apiKey: '',
      category: 'AI Models',
      features: ['Claude-3', 'Constitutional AI', 'Long Context', 'Safety Features'],
      setupUrl: 'https://console.anthropic.com/'
    },
    { 
      id: 4, 
      name: 'Google Cloud AI', 
      icon: '☁️', 
      status: 'Available', 
      description: 'Enterprise AI and ML services', 
      apiKey: '',
      category: 'AI Models',
      features: ['Vertex AI', 'AutoML', 'Vision API', 'Natural Language API'],
      setupUrl: 'https://console.cloud.google.com/'
    },
    { 
      id: 5, 
      name: 'AWS Bedrock', 
      icon: '🏗️', 
      status: 'Available', 
      description: 'Fully managed foundation models', 
      apiKey: '',
      category: 'AI Models',
      features: ['Claude', 'Llama 2', 'Titan', 'Jurassic-2'],
      setupUrl: 'https://aws.amazon.com/bedrock/'
    },
    { 
      id: 6, 
      name: 'Slack', 
      icon: '💬', 
      status: 'Connected', 
      description: 'Team communication and collaboration', 
      apiKey: 'xoxb-...xyz789',
      category: 'Communication',
      features: ['Bot Integration', 'Notifications', 'File Sharing', 'Workflows'],
      setupUrl: 'https://api.slack.com/apps'
    },
    { 
      id: 7, 
      name: 'Discord', 
      icon: '🎮', 
      status: 'Available', 
      description: 'Community and team communication', 
      apiKey: '',
      category: 'Communication',
      features: ['Bot Commands', 'Webhooks', 'Voice Integration', 'Rich Embeds'],
      setupUrl: 'https://discord.com/developers/applications'
    },
    { 
      id: 8, 
      name: 'GitHub', 
      icon: '🐙', 
      status: 'Available', 
      description: 'Code repository and collaboration', 
      apiKey: '',
      category: 'Development',
      features: ['Repository Access', 'Issue Tracking', 'Pull Requests', 'Actions'],
      setupUrl: 'https://github.com/settings/tokens'
    },
    { 
      id: 9, 
      name: 'Notion', 
      icon: '📝', 
      status: 'Available', 
      description: 'Knowledge management and documentation', 
      apiKey: '',
      category: 'Storage',
      features: ['Database Access', 'Page Creation', 'Content Sync', 'Templates'],
      setupUrl: 'https://www.notion.so/my-integrations'
    },
    { 
      id: 10, 
      name: 'Google Drive', 
      icon: '📁', 
      status: 'Available', 
      description: 'Cloud storage and file management', 
      apiKey: '',
      category: 'Storage',
      features: ['File Upload', 'Document Access', 'Sharing', 'Collaboration'],
      setupUrl: 'https://console.developers.google.com/'
    }
  ]);

  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showApiKey, setShowApiKey] = useState<{ [key: number]: boolean }>({});

  const categories = ['All', 'AI Models', 'Communication', 'Storage', 'Analytics', 'Development'];

  const filteredIntegrations = selectedCategory === 'All' 
    ? integrations 
    : integrations.filter(integration => integration.category === selectedCategory);

  const getStatusIcon = (status: Integration['status']) => {
    switch (status) {
      case 'Connected':
        return <CheckCircle size={16} style={{ color: '#10b981' }} />;
      case 'Available':
        return <Settings size={16} style={{ color: '#9ca3af' }} />;
      case 'Error':
        return <AlertCircle size={16} style={{ color: '#ef4444' }} />;
    }
  };

  const getStatusColor = (status: Integration['status']) => {
    switch (status) {
      case 'Connected': return '#10b981';
      case 'Available': return '#9ca3af';
      case 'Error': return '#ef4444';
    }
  };

  const connectIntegration = (integration: Integration) => {
    setSelectedIntegration(integration);
    setApiKeyInput(integration.apiKey || '');
    setShowApiKeyModal(true);
  };

  const saveApiKey = () => {
    if (!selectedIntegration || !apiKeyInput.trim()) return;

    setIntegrations(prev => prev.map(integration => {
      if (integration.id === selectedIntegration.id) {
        return {
          ...integration,
          apiKey: apiKeyInput,
          status: 'Connected' as const
        };
      }
      return integration;
    }));

    setShowApiKeyModal(false);
    setSelectedIntegration(null);
    setApiKeyInput('');
  };

  const disconnectIntegration = (id: number) => {
    setIntegrations(prev => prev.map(integration => {
      if (integration.id === id) {
        return {
          ...integration,
          apiKey: '',
          status: 'Available' as const
        };
      }
      return integration;
    }));
  };

  const toggleApiKeyVisibility = (id: number) => {
    setShowApiKey(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const maskApiKey = (apiKey: string) => {
    if (!apiKey) return '';
    if (apiKey.length <= 8) return '*'.repeat(apiKey.length);
    return apiKey.substring(0, 4) + '*'.repeat(apiKey.length - 8) + apiKey.substring(apiKey.length - 4);
  };

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
            Integrations Hub
          </h2>
          <p style={{
            color: '#9ca3af',
            margin: '4px 0 0 0',
            fontSize: '14px'
          }}>
            Connect your favorite tools and services to AI Scholar
          </p>
        </div>
        
        <button
          onClick={() => window.open('https://docs.aischolar.com/integrations', '_blank')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 20px',
            background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            border: 'none',
            borderRadius: '8px',
            color: 'white',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          <ExternalLink size={16} />
          Browse More
        </button>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '16px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ color: '#10b981', fontSize: '20px', fontWeight: '600', marginBottom: '4px' }}>
            {integrations.filter(i => i.status === 'Connected').length}
          </div>
          <div style={{ color: '#9ca3af', fontSize: '12px' }}>Connected</div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '16px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ color: '#9ca3af', fontSize: '20px', fontWeight: '600', marginBottom: '4px' }}>
            {integrations.filter(i => i.status === 'Available').length}
          </div>
          <div style={{ color: '#9ca3af', fontSize: '12px' }}>Available</div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '16px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ color: '#60a5fa', fontSize: '20px', fontWeight: '600', marginBottom: '4px' }}>
            {integrations.length}
          </div>
          <div style={{ color: '#9ca3af', fontSize: '12px' }}>Total</div>
        </div>
      </div>

      {/* Category Filter */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '24px',
        flexWrap: 'wrap'
      }}>
        {categories.map(category => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            style={{
              padding: '8px 16px',
              background: selectedCategory === category 
                ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
                : 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '20px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Integrations Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
        gap: '16px'
      }}>
        {filteredIntegrations.map(integration => (
          <div
            key={integration.id}
            style={{
              background: 'rgba(255,255,255,0.05)',
              borderRadius: '12px',
              padding: '20px',
              border: '1px solid rgba(255,255,255,0.1)',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.08)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
          >
            {/* Header */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '12px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '8px',
                  background: 'rgba(255,255,255,0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '20px'
                }}>
                  {integration.icon}
                </div>
                <div>
                  <h3 style={{
                    color: 'white',
                    margin: 0,
                    fontSize: '16px',
                    fontWeight: '500'
                  }}>
                    {integration.name}
                  </h3>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    marginTop: '2px'
                  }}>
                    {getStatusIcon(integration.status)}
                    <span style={{
                      fontSize: '12px',
                      color: getStatusColor(integration.status),
                      fontWeight: '500'
                    }}>
                      {integration.status}
                    </span>
                  </div>
                </div>
              </div>

              <div style={{
                fontSize: '10px',
                color: '#6b7280',
                background: 'rgba(255,255,255,0.1)',
                padding: '4px 8px',
                borderRadius: '12px'
              }}>
                {integration.category}
              </div>
            </div>

            {/* Description */}
            <p style={{
              color: '#9ca3af',
              fontSize: '14px',
              margin: '0 0 12px 0',
              lineHeight: '1.4'
            }}>
              {integration.description}
            </p>

            {/* Features */}
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '6px',
              marginBottom: '16px'
            }}>
              {integration.features.slice(0, 3).map((feature, index) => (
                <span
                  key={index}
                  style={{
                    fontSize: '11px',
                    color: '#9ca3af',
                    background: 'rgba(255,255,255,0.1)',
                    padding: '2px 6px',
                    borderRadius: '8px'
                  }}
                >
                  {feature}
                </span>
              ))}
              {integration.features.length > 3 && (
                <span style={{
                  fontSize: '11px',
                  color: '#6b7280'
                }}>
                  +{integration.features.length - 3} more
                </span>
              )}
            </div>

            {/* API Key Display */}
            {integration.status === 'Connected' && integration.apiKey && (
              <div style={{
                background: 'rgba(255,255,255,0.05)',
                padding: '8px 12px',
                borderRadius: '6px',
                marginBottom: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <Key size={12} style={{ color: '#9ca3af' }} />
                  <span style={{
                    fontSize: '12px',
                    color: '#9ca3af',
                    fontFamily: 'monospace'
                  }}>
                    {showApiKey[integration.id] ? integration.apiKey : maskApiKey(integration.apiKey)}
                  </span>
                </div>
                <button
                  onClick={() => toggleApiKeyVisibility(integration.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#9ca3af',
                    cursor: 'pointer',
                    padding: '2px'
                  }}
                >
                  {showApiKey[integration.id] ? <EyeOff size={12} /> : <Eye size={12} />}
                </button>
              </div>
            )}

            {/* Actions */}
            <div style={{
              display: 'flex',
              gap: '8px'
            }}>
              {integration.status === 'Connected' ? (
                <>
                  <button
                    onClick={() => connectIntegration(integration)}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      background: 'rgba(255,255,255,0.1)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '6px',
                      color: 'white',
                      cursor: 'pointer',
                      fontSize: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '4px'
                    }}
                  >
                    <Edit size={12} />
                    Configure
                  </button>
                  <button
                    onClick={() => disconnectIntegration(integration.id)}
                    style={{
                      padding: '8px 12px',
                      background: 'rgba(239, 68, 68, 0.2)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      borderRadius: '6px',
                      color: '#ef4444',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    Disconnect
                  </button>
                </>
              ) : (
                <button
                  onClick={() => connectIntegration(integration)}
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                    border: 'none',
                    borderRadius: '6px',
                    color: 'white',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: '500'
                  }}
                >
                  Connect
                </button>
              )}
              
              {integration.setupUrl && (
                <button
                  onClick={() => window.open(integration.setupUrl, '_blank')}
                  style={{
                    padding: '8px 12px',
                    background: 'rgba(255,255,255,0.1)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '6px',
                    color: '#9ca3af',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  <ExternalLink size={12} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* API Key Modal */}
      {showApiKeyModal && selectedIntegration && (
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
                Configure {selectedIntegration.name}
              </h3>
              <button
                onClick={() => setShowApiKeyModal(false)}
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

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                API Key
              </label>
              <input
                type="password"
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                placeholder="Enter your API key..."
                style={{
                  width: '100%',
                  padding: '12px',
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  color: 'white',
                  fontSize: '14px',
                  outline: 'none',
                  fontFamily: 'monospace'
                }}
              />
              <p style={{
                color: '#6b7280',
                fontSize: '12px',
                margin: '8px 0 0 0'
              }}>
                Your API key will be stored securely and encrypted.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setShowApiKeyModal(false)}
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
                Cancel
              </button>
              <button
                onClick={saveApiKey}
                disabled={!apiKeyInput.trim()}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: apiKeyInput.trim()
                    ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
                    : 'rgba(156, 163, 175, 0.2)',
                  border: 'none',
                  color: 'white',
                  borderRadius: '8px',
                  cursor: apiKeyInput.trim() ? 'pointer' : 'not-allowed',
                  fontWeight: '600',
                  transition: 'all 0.2s ease'
                }}
              >
                Save & Connect
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationsView;