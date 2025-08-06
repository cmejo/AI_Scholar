import React, { useState, useEffect } from 'react';
import { AdvancedChatInterface } from './components/AdvancedChatInterface';
import { MemoryAwareChatInterface } from './components/MemoryAwareChatInterface';
import { EnhancedDocumentManager } from './components/EnhancedDocumentManager';
import { EnterpriseAnalyticsDashboard } from './components/EnterpriseAnalyticsDashboard';
import { SecurityDashboard } from './components/SecurityDashboard';
import { WorkflowManager } from './components/WorkflowManager';
import { IntegrationHub } from './components/IntegrationHub';
import VoiceInterface from './components/VoiceInterface';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { MobileLayout } from './components/mobile/MobileLayout';
import { AccessibilityFeatures } from './components/AccessibilityFeatures';
import { AccessibilityToolbar } from './components/AccessibilityToolbar';
import { EnhancedChatProvider } from './contexts/EnhancedChatContext';
import { DocumentProvider } from './contexts/DocumentContext';
import { useMobileDetection } from './hooks/useMobileDetection';
import { securityService } from './services/securityService';
import { analyticsService } from './services/analyticsService';
import { memoryService } from './services/memoryService';
import { accessibilityService } from './services/accessibilityService';

type ViewType = 'chat' | 'documents' | 'analytics' | 'security' | 'workflows' | 'integrations';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [user, setUser] = useState<any>(null);
  const { isMobile, isTablet } = useMobileDetection();

  useEffect(() => {
    // Initialize enterprise features
    initializeEnterpriseFeatures();
    
    // Initialize accessibility features
    accessibilityService.announce('AI Scholar Enterprise application loaded', 'polite');
    
    // Set up global keyboard shortcuts
    const handleKeyDown = (event: KeyboardEvent) => {
      // Alt + 1-6 for quick navigation
      if (event.altKey && event.key >= '1' && event.key <= '6') {
        event.preventDefault();
        const views: ViewType[] = ['chat', 'documents', 'analytics', 'security', 'workflows', 'integrations'];
        const viewIndex = parseInt(event.key) - 1;
        if (views[viewIndex]) {
          setCurrentView(views[viewIndex]);
          accessibilityService.announce(`Navigated to ${views[viewIndex]}`, 'polite');
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
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

  // Use mobile layout for mobile and tablet devices
  if (isMobile || isTablet) {
    return (
      <DocumentProvider>
        <EnhancedChatProvider>
          <AccessibilityFeatures>
            <MobileLayout
              currentView={currentView}
              onViewChange={(view) => {
                setCurrentView(view);
                accessibilityService.announcePageChange(view);
              }}
              user={user}
              voiceEnabled={voiceEnabled}
              onToggleVoice={setVoiceEnabled}
            >
              {renderCurrentView()}
            </MobileLayout>
          </AccessibilityFeatures>
        </EnhancedChatProvider>
      </DocumentProvider>
    );
  }

  // Desktop layout
  return (
    <DocumentProvider>
      <EnhancedChatProvider>
        <AccessibilityFeatures>
          <div className="h-screen bg-gray-900 text-white flex overflow-hidden">
            <Sidebar 
              isOpen={sidebarOpen} 
              onClose={() => setSidebarOpen(false)}
              currentView={currentView}
              onViewChange={(view) => {
                setCurrentView(view);
                accessibilityService.announcePageChange(view);
              }}
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
              
              <main 
                id="main-content"
                className="flex-1 overflow-hidden"
                role="main"
                aria-label="Main application content"
                tabIndex={-1}
              >
                {renderCurrentView()}
              </main>
            </div>
            
            {/* Accessibility Toolbar */}
            <AccessibilityToolbar />
          </div>
        </AccessibilityFeatures>
      </EnhancedChatProvider>
    </DocumentProvider>
  );
}

export default App;