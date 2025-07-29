import React, { useState, useEffect } from 'react';
import { AdvancedChatInterface } from './components/AdvancedChatInterface';
import { MemoryAwareChatInterface } from './components/MemoryAwareChatInterface';
import { EnhancedDocumentManager } from './components/EnhancedDocumentManager';
import { EnterpriseAnalyticsDashboard } from './components/EnterpriseAnalyticsDashboard';
import { SecurityDashboard } from './components/SecurityDashboard';
import { WorkflowManager } from './components/WorkflowManager';
import { IntegrationHub } from './components/IntegrationHub';
import { VoiceInterface } from './components/VoiceInterface';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { EnhancedChatProvider } from './contexts/EnhancedChatContext';
import { DocumentProvider } from './contexts/DocumentContext';
import { securityService } from './services/securityService';
import { analyticsService } from './services/analyticsService';
import { memoryService } from './services/memoryService';

type ViewType = 'chat' | 'documents' | 'analytics' | 'security' | 'workflows' | 'integrations';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Initialize enterprise features
    initializeEnterpriseFeatures();
  }, []);

  const initializeEnterpriseFeatures = async () => {
    // Mock user authentication
    const mockUser = {
      id: 'user_admin',
      email: 'admin@example.com',
      name: 'Admin User',
      role: 'admin'
    };
    setUser(mockUser);

    // Initialize security service
    securityService.cleanupExpiredSessions();

    // Log application start
    analyticsService.logQuery({
      id: `query_${Date.now()}`,
      query: 'Application started',
      userId: mockUser.id,
      timestamp: new Date(),
      responseTime: 0,
      satisfaction: 1,
      intent: 'system',
      documentsUsed: [],
      success: true
    });
  };

  const handleVoiceQuery = async (query: string): Promise<string> => {
    // Process voice query through the RAG system
    // This would integrate with your existing chat system
    
    // Log the voice interaction
    if (user) {
      analyticsService.logQuery({
        id: `voice_query_${Date.now()}`,
        query,
        userId: user.id,
        timestamp: new Date(),
        responseTime: 1200,
        satisfaction: 0.9,
        intent: 'voice_query',
        documentsUsed: [],
        success: true
      });

      // Add to memory
      memoryService.addMemory(user.id, {
        type: 'context',
        content: `Voice query: ${query}`,
        importance: 0.7,
        source: 'voice_interface',
        verified: true
      });
    }

    return `I heard you ask: "${query}". This is a mock response from the voice interface. In production, this would be processed through your RAG system.`;
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'chat':
        return (
          <div className="flex flex-col h-full">
            <MemoryAwareChatInterface />
            {voiceEnabled && (
              <div className="border-t border-gray-700 p-4">
                <VoiceInterface
                  onVoiceQuery={handleVoiceQuery}
                  enabled={voiceEnabled}
                  onToggle={setVoiceEnabled}
                />
              </div>
            )}
          </div>
        );
      case 'documents':
        return <EnhancedDocumentManager />;
      case 'analytics':
        return <EnterpriseAnalyticsDashboard />;
      case 'security':
        return <SecurityDashboard />;
      case 'workflows':
        return <WorkflowManager />;
      case 'integrations':
        return <IntegrationHub />;
      default:
        return <AdvancedChatInterface />;
    }
  };

  return (
    <DocumentProvider>
      <EnhancedChatProvider>
        <div className="h-screen bg-gray-900 text-white flex overflow-hidden">
          <Sidebar 
            isOpen={sidebarOpen} 
            onClose={() => setSidebarOpen(false)}
            currentView={currentView}
            onViewChange={setCurrentView}
            user={user}
            voiceEnabled={voiceEnabled}
            onToggleVoice={setVoiceEnabled}
          />
          
          <div className="flex-1 flex flex-col">
            <Header 
              onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
              currentView={currentView}
              user={user}
            />
            
            <main className="flex-1 overflow-hidden">
              {renderCurrentView()}
            </main>
          </div>
        </div>
      </EnhancedChatProvider>
    </DocumentProvider>
  );
}

export default App;