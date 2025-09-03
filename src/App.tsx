import { Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { AccessibilityFeatures } from './components/AccessibilityFeatures';
import { AccessibilityToolbar } from './components/AccessibilityToolbar';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import VoiceInterface from './components/VoiceInterface';
import { DocumentProvider } from './contexts/DocumentContext';
import { EnhancedChatProvider } from './contexts/EnhancedChatContext';
import { useMobileDetection } from './hooks/useMobileDetection';
import { accessibilityService } from './services/accessibilityService';
import { analyticsService } from './services/analyticsService';
import { authService } from './services/authService';
import { memoryService } from './services/memoryService';
import { securityService } from './services/securityService';
import { User } from './types/user';
import { globalErrorHandler } from './utils/globalErrorHandler';

// Enhanced lazy loading with performance monitoring
import PerformanceMonitor from './components/PerformanceMonitor';
import { createMonitoredLazyComponent } from './utils/codeSplitting';

const AdvancedChatInterface = createMonitoredLazyComponent(
  () => import('./components/AdvancedChatInterface').then(module => ({ default: module.AdvancedChatInterface })),
  'AdvancedChatInterface'
);

const EnhancedDocumentManager = createMonitoredLazyComponent(
  () => import('./components/EnhancedDocumentManager').then(module => ({ default: module.EnhancedDocumentManager })),
  'EnhancedDocumentManager'
);

const EnterpriseAnalyticsDashboard = createMonitoredLazyComponent(
  () => import('./components/EnterpriseAnalyticsDashboard').then(module => ({ default: module.EnterpriseAnalyticsDashboard })),
  'EnterpriseAnalyticsDashboard'
);

const SecurityDashboard = createMonitoredLazyComponent(
  () => import('./components/SecurityDashboard').then(module => ({ default: module.SecurityDashboard })),
  'SecurityDashboard'
);

const WorkflowManager = createMonitoredLazyComponent(
  () => import('./components/WorkflowManager').then(module => ({ default: module.WorkflowManager })),
  'WorkflowManager'
);

const IntegrationHub = createMonitoredLazyComponent(
  () => import('./components/IntegrationHub').then(module => ({ default: module.IntegrationHub })),
  'IntegrationHub'
);

const MemoryAwareChatInterface = createMonitoredLazyComponent(
  () => import('./components/MemoryAwareChatInterface').then(module => ({ default: module.MemoryAwareChatInterface })),
  'MemoryAwareChatInterface'
);

const MobileLayout = createMonitoredLazyComponent(
  () => import('./components/mobile/MobileLayout').then(module => ({ default: module.MobileLayout })),
  'MobileLayout'
);

// Loading component for Suspense fallback
const ComponentLoader: React.FC = () => (
  <div className="flex items-center justify-center h-full">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
  </div>
);

type ViewType = 'chat' | 'documents' | 'analytics' | 'security' | 'workflows' | 'integrations';

function App(): JSX.Element {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const { isMobile, isTablet } = useMobileDetection();

  useEffect(() => {
    // Initialize global error handling
    globalErrorHandler.updateConfig({
      enableConsoleLogging: process.env.NODE_ENV === 'development',
      enableErrorReporting: true,
      enableUserNotification: true,
    });

    // Initialize enterprise features
    void initializeEnterpriseFeatures();
    
    // Initialize accessibility features
    accessibilityService.announce('AI Scholar Enterprise application loaded', 'polite');
    
    // Set up global keyboard shortcuts
    const handleKeyDown = (event: KeyboardEvent) => {
      // Alt + 1-6 for quick navigation
      if (event.altKey && event.key >= '1' && event.key <= '6') {
        event.preventDefault();
        const views: ViewType[] = ['chat', 'documents', 'analytics', 'security', 'workflows', 'integrations'];
        const viewIndex = parseInt(event.key) - 1;
        if (views[viewIndex] !== undefined) {
          setCurrentView(views[viewIndex]);
          accessibilityService.announce(`Navigated to ${views[viewIndex]}`, 'polite');
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const initializeEnterpriseFeatures = useCallback(async (): Promise<void> => {
    // Mock user authentication
    // TODO: Replace with real authentication service
    try {
      const authenticatedUser = await authService.getCurrentUser();
      if (authenticatedUser) {
        setUser(authenticatedUser);
      } else {
        // Redirect to login or show auth modal
        console.warn('No authenticated user found - redirecting to login');
        // window.location.href = '/login';
      }
    } catch (error) {
      console.error('Authentication failed:', error);
      // Handle authentication error appropriately
      setUser(null);
    }

    // Initialize security service
    securityService.cleanupExpiredSessions();

    // Log application start (only if user is authenticated)
    if (user) {
      analyticsService.logQuery({
        id: `query_${Date.now()}`,
        query: 'Application started',
        userId: user.id,
        timestamp: new Date(),
        responseTime: 0,
        satisfaction: 1,
        intent: 'system',
        documentsUsed: [],
        success: true
      });
    }
  }, []);

  const handleVoiceQuery = useCallback(async (query: string): Promise<string> => {
    // Process voice query through the RAG system
    // This would integrate with your existing chat system
    
    // Log the voice interaction
    if (user !== null) {
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
  }, [user]);

  const renderCurrentView = useMemo((): JSX.Element => {
    switch (currentView) {
      case 'chat':
        return (
          <div className="flex flex-col h-full">
            <Suspense fallback={<ComponentLoader />}>
              <MemoryAwareChatInterface />
            </Suspense>
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
        return (
          <Suspense fallback={<ComponentLoader />}>
            <EnhancedDocumentManager />
          </Suspense>
        );
      case 'analytics':
        return (
          <Suspense fallback={<ComponentLoader />}>
            <EnterpriseAnalyticsDashboard />
          </Suspense>
        );
      case 'security':
        return (
          <Suspense fallback={<ComponentLoader />}>
            <SecurityDashboard />
          </Suspense>
        );
      case 'workflows':
        return (
          <Suspense fallback={<ComponentLoader />}>
            <WorkflowManager />
          </Suspense>
        );
      case 'integrations':
        return (
          <Suspense fallback={<ComponentLoader />}>
            <IntegrationHub />
          </Suspense>
        );
      default:
        return (
          <Suspense fallback={<ComponentLoader />}>
            <AdvancedChatInterface />
          </Suspense>
        );
    }
  }, [currentView, voiceEnabled, handleVoiceQuery]);

  // Memoize view change handler to prevent unnecessary re-renders
  const handleViewChange = useCallback((view: ViewType) => {
    setCurrentView(view);
    accessibilityService.announcePageChange(view);
  }, []);

  // Use mobile layout for mobile and tablet devices
  if (isMobile || isTablet) {
    return (
      <ErrorBoundary>
        <DocumentProvider>
          <EnhancedChatProvider>
            <AccessibilityFeatures>
              <Suspense fallback={<ComponentLoader />}>
                <MobileLayout
                  currentView={currentView}
                  onViewChange={handleViewChange}
                  user={user}
                  voiceEnabled={voiceEnabled}
                  onToggleVoice={setVoiceEnabled}
                >
                  {renderCurrentView}
                </MobileLayout>
              </Suspense>
            </AccessibilityFeatures>
          </EnhancedChatProvider>
        </DocumentProvider>
      </ErrorBoundary>
    );
  }

  // Memoize sidebar handlers to prevent unnecessary re-renders
  const handleToggleSidebar = useCallback(() => setSidebarOpen(!sidebarOpen), [sidebarOpen]);
  const handleCloseSidebar = useCallback(() => setSidebarOpen(false), []);

  // Desktop layout
  return (
    <ErrorBoundary>
      <DocumentProvider>
        <EnhancedChatProvider>
          <AccessibilityFeatures>
            <div className="h-screen bg-gray-900 text-white flex overflow-hidden">
              <Sidebar 
                isOpen={sidebarOpen} 
                onClose={handleCloseSidebar}
                currentView={currentView}
                onViewChange={handleViewChange}
                user={user}
                voiceEnabled={voiceEnabled}
                onToggleVoice={setVoiceEnabled}
              />
              
              <div className="flex-1 flex flex-col">
                <Header 
                  onToggleSidebar={handleToggleSidebar}
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
                  {renderCurrentView}
                </main>
              </div>
              
              {/* Accessibility Toolbar */}
              <AccessibilityToolbar />
              
              {/* Performance Monitor (development only) */}
              <PerformanceMonitor 
                componentName="App"
                enabled={typeof window !== 'undefined' && window.location.hostname === 'localhost'}
                threshold={16}
              />
            </div>
          </AccessibilityFeatures>
        </EnhancedChatProvider>
      </DocumentProvider>
    </ErrorBoundary>
  );
}

export default App;