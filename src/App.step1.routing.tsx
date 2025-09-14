import React, { useState } from 'react';
import { Menu, MessageCircle, FileText, BarChart3, Shield, Settings, User, HelpCircle, Info } from 'lucide-react';

type ViewType = 'chat' | 'documents' | 'analytics' | 'security' | 'settings' | 'profile' | 'help' | 'about';

interface NavigationItem {
  id: ViewType;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const navigationItems: NavigationItem[] = [
  { id: 'chat', label: 'AI Chat', icon: MessageCircle, description: 'Intelligent conversation interface' },
  { id: 'documents', label: 'Documents', icon: FileText, description: 'Document management and analysis' },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, description: 'Usage metrics and insights' },
  { id: 'security', label: 'Security', icon: Shield, description: 'Security dashboard and monitoring' },
  { id: 'settings', label: 'Settings', icon: Settings, description: 'Application configuration' },
  { id: 'profile', label: 'Profile', icon: User, description: 'User account management' },
  { id: 'help', label: 'Help', icon: HelpCircle, description: 'Documentation and support' },
  { id: 'about', label: 'About', icon: Info, description: 'Application information' },
];

function App(): JSX.Element {
  console.log('🚀 AI SCHOLAR - STEP 1: ROUTING & NAVIGATION');
  
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  React.useEffect(() => {
    console.log('🚀 Step 1 App mounted - Adding routing and navigation');
    document.title = 'AI Scholar - Advanced Research Assistant';
  }, []);

  const renderView = () => {
    const currentItem = navigationItems.find(item => item.id === currentView);
    const IconComponent = currentItem?.icon || MessageCircle;

    return (
      <div style={{ 
        padding: '40px', 
        background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1b69 100%)', 
        color: 'white', 
        minHeight: '100vh',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            marginBottom: '30px',
            padding: '20px',
            background: 'rgba(255,255,255,0.1)',
            borderRadius: '15px',
            backdropFilter: 'blur(10px)'
          }}>
            <IconComponent style={{ width: '32px', height: '32px', color: '#10b981', marginRight: '15px' }} />
            <div>
              <h1 style={{ margin: 0, fontSize: '2em', color: '#10b981' }}>
                {currentItem?.label || 'AI Scholar'}
              </h1>
              <p style={{ margin: '5px 0 0 0', color: '#cbd5e1', fontSize: '1.1em' }}>
                {currentItem?.description || 'Advanced Research Assistant'}
              </p>
            </div>
          </div>

          <div style={{ 
            background: 'rgba(255,255,255,0.05)', 
            padding: '30px', 
            borderRadius: '15px',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            <h2 style={{ color: '#60a5fa', marginTop: 0 }}>
              🚧 {currentItem?.label} - Coming Soon
            </h2>
            <p style={{ fontSize: '16px', lineHeight: '1.6', marginBottom: '20px' }}>
              This section will contain the full {currentItem?.label.toLowerCase()} functionality. 
              Currently showing placeholder content while we build out the features.
            </p>
            
            {currentView === 'chat' && (
              <div style={{ 
                background: 'rgba(16, 185, 129, 0.1)', 
                padding: '20px', 
                borderRadius: '10px',
                border: '1px solid rgba(16, 185, 129, 0.3)'
              }}>
                <h3 style={{ color: '#10b981', marginTop: 0 }}>🤖 AI Chat Interface</h3>
                <p>Features to be implemented:</p>
                <ul style={{ lineHeight: '1.8' }}>
                  <li>Multi-mode AI conversations (standard, chain-of-thought, fact-checked)</li>
                  <li>Voice interface with speech-to-text and text-to-speech</li>
                  <li>Context-aware responses and memory</li>
                  <li>Integration with RAG system for document queries</li>
                </ul>
              </div>
            )}

            {currentView === 'documents' && (
              <div style={{ 
                background: 'rgba(59, 130, 246, 0.1)', 
                padding: '20px', 
                borderRadius: '10px',
                border: '1px solid rgba(59, 130, 246, 0.3)'
              }}>
                <h3 style={{ color: '#3b82f6', marginTop: 0 }}>📄 Document Management</h3>
                <p>Features to be implemented:</p>
                <ul style={{ lineHeight: '1.8' }}>
                  <li>PDF upload and processing</li>
                  <li>Document analysis and summarization</li>
                  <li>Vector search and semantic queries</li>
                  <li>Document collections and organization</li>
                </ul>
              </div>
            )}

            {currentView === 'analytics' && (
              <div style={{ 
                background: 'rgba(245, 158, 11, 0.1)', 
                padding: '20px', 
                borderRadius: '10px',
                border: '1px solid rgba(245, 158, 11, 0.3)'
              }}>
                <h3 style={{ color: '#f59e0b', marginTop: 0 }}>📊 Analytics Dashboard</h3>
                <p>Features to be implemented:</p>
                <ul style={{ lineHeight: '1.8' }}>
                  <li>Usage metrics and performance monitoring</li>
                  <li>User behavior analytics</li>
                  <li>Content analytics and insights</li>
                  <li>Real-time monitoring and alerts</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#1a1a1a' }}>
      {/* Sidebar */}
      <div style={{
        width: sidebarOpen ? '280px' : '70px',
        background: 'linear-gradient(180deg, #374151 0%, #1f2937 100%)',
        transition: 'width 0.3s ease',
        borderRight: '1px solid rgba(255,255,255,0.1)',
        position: 'relative'
      }}>
        {/* Sidebar Header */}
        <div style={{ 
          padding: '20px', 
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: sidebarOpen ? 'space-between' : 'center'
        }}>
          {sidebarOpen && (
            <div style={{ color: 'white', fontWeight: 'bold', fontSize: '1.2em' }}>
              AI Scholar
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            style={{
              background: 'none',
              border: 'none',
              color: '#9ca3af',
              cursor: 'pointer',
              padding: '8px',
              borderRadius: '6px',
              transition: 'all 0.2s ease'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
              e.currentTarget.style.color = 'white';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'none';
              e.currentTarget.style.color = '#9ca3af';
            }}
          >
            <Menu style={{ width: '20px', height: '20px' }} />
          </button>
        </div>

        {/* Navigation Items */}
        <nav style={{ padding: '20px 0' }}>
          {navigationItems.map((item) => {
            const IconComponent = item.icon;
            const isActive = currentView === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  padding: sidebarOpen ? '12px 20px' : '12px',
                  background: isActive ? 'rgba(16, 185, 129, 0.2)' : 'none',
                  border: 'none',
                  color: isActive ? '#10b981' : '#9ca3af',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  borderLeft: isActive ? '3px solid #10b981' : '3px solid transparent',
                  justifyContent: sidebarOpen ? 'flex-start' : 'center'
                }}
                onMouseOver={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                    e.currentTarget.style.color = 'white';
                  }
                }}
                onMouseOut={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'none';
                    e.currentTarget.style.color = '#9ca3af';
                  }
                }}
              >
                <IconComponent style={{ 
                  width: '20px', 
                  height: '20px',
                  marginRight: sidebarOpen ? '12px' : '0'
                }} />
                {sidebarOpen && (
                  <span style={{ fontSize: '14px', fontWeight: '500' }}>
                    {item.label}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {renderView()}
      </div>
    </div>
  );
}

export default App;