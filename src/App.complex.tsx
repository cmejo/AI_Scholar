import { Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { AccessibilityFeatures } from './components/AccessibilityFeatures';
import { AccessibilityToolbar } from './components/AccessibilityToolbar';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import VoiceInterface from './components/VoiceInterface';
import { DocumentProvider } from './contexts/DocumentContext';
import { EnhancedChatProvider } from './contexts/EnhancedChatContext';
import { EnterpriseAuthProvider } from './contexts/EnterpriseAuthContext';
import { useMobileDetection } from './hooks/useMobileDetection';
import { useEnterpriseAuth } from './hooks/useEnterpriseAuth';
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
import { 
  createEnterpriseComponent, 
  EnterprisePerformanceMonitor,
  initializeEnterpriseCodeSplitting 
} from './components/enterprise';

const AdvancedChatInterface = createMonitoredLazyComponent(
  () => import('./components/AdvancedChatInterface').then(module => ({ default: module.AdvancedChatInterface })),
  'AdvancedChatInterface'
);

const EnhancedDocumentManager = createMonitoredLazyComponent(
  () => import('./components/EnhancedDocumentManager').then(module => ({ default: module.EnhancedDocumentManager })),
  'EnhancedDocumentManager'
);

// Enterprise components with enhanced monitoring
const EnterpriseAnalyticsDashboard = createEnterpriseComponent(
  'EnterpriseAnalyticsDashboard',
  'analytics',
  () => import('./components/enterprise/EnterpriseAnalyticsDashboard').then(module => ({ default: module.EnterpriseAnalyticsDashboard })),
  { criticalComponent: true, preload: true }
);

const SecurityDashboard = createEnterpriseComponent(
  'SecurityDashboard',
  'security',
  () => import('./components/enterprise/SecurityDashboard').then(module => ({ default: module.SecurityDashboard })),
  { criticalComponent: true, preload: true }
);

const WorkflowManager = createEnterpriseComponent(
  'WorkflowManager',
  'workflow',
  () => import('./components/enterprise/WorkflowManager').then(module => ({ default: module.WorkflowManager }))
);

const IntegrationHub = createEnterpriseComponent(
  'IntegrationHub',
  'integration',
  () => import('./components/enterprise/IntegrationHub').then(module => ({ default: module.IntegrationHub }))
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

// Main App Content Component (uses enterprise auth)
function AppContent(): JSX.Element {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const { isMobile, isTablet } = useMobileDetection();
  
  // Use enterprise authentication
  const { 
    user, 
    isAuthenticated, 
    isLoading, 
    canAccessFeature,
    sessionTimeRemaining 
  } = useEnterpriseAuth();

  useEffect(() => {
    // Initialize global error handling
    globalErrorHandler.updateConfig({
      enableConsoleLogging: process.env.NODE_ENV === 'development',
      enableErrorReporting: true,
      enableUserNotification: true,
    });

    // Initialize enterprise code splitting and performance monitoring
    initializeEnterpriseCodeSplitting();

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
  }, [user]);

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
    // Show loading state during authentication
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-full bg-gray-900 text-white">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
            <p className="text-gray-300">Loading...</p>
          </div>
        </div>
      );
    }

    // Show login prompt if not authenticated
    if (!isAuthenticated) {
      return (
        <div className="flex items-center justify-center h-full bg-gray-900 text-white">
          <div className="text-center max-w-md">
            <h2 className="text-2xl font-bold text-white mb-4">Welcome to AI Scholar</h2>
            <p className="text-gray-400 mb-6">Please log in to access the application.</p>
            <button
              onClick={() => window.location.href = '/login'}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-medium"
            >
              Go to Login
            </button>
          </div>
        </div>
      );
    }

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
        if (!canAccessFeature('analytics')) {
          return (
            <div className="flex items-center justify-center h-full bg-gray-900 text-white">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Access Restricted</h3>
                <p className="text-gray-400">You don't have permission to access analytics.</p>
              </div>
            </div>
          );
        }
        return (
          <Suspense fallback={<ComponentLoader />}>
            <EnterpriseAnalyticsDashboard />
          </Suspense>
        );
      case 'security':
        if (!canAccessFeature('security')) {
          return (
            <div className="flex items-center justify-center h-full bg-gray-900 text-white">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Access Restricted</h3>
                <p className="text-gray-400">You don't have permission to access security features.</p>
              </div>
            </div>
          );
        }
        return (
          <Suspense fallback={<ComponentLoader />}>
            <SecurityDashboard />
          </Suspense>
        );
      case 'workflows':
        if (!canAccessFeature('workflows')) {
          return (
            <div className="flex items-center justify-center h-full bg-gray-900 text-white">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Access Restricted</h3>
                <p className="text-gray-400">You don't have permission to access workflow management.</p>
              </div>
            </div>
          );
        }
        return (
          <Suspense fallback={<ComponentLoader />}>
            <WorkflowManager />
          </Suspense>
        );
      case 'integrations':
        if (!canAccessFeature('integrations')) {
          return (
            <div className="flex items-center justify-center h-full bg-gray-900 text-white">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Access Restricted</h3>
                <p className="text-gray-400">You don't have permission to access integrations.</p>
              </div>
            </div>
          );
        }
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
  }, [currentView, voiceEnabled, handleVoiceQuery, isLoading, isAuthenticated, canAccessFeature]);

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

              {/* Enterprise Performance Monitor */}
              <EnterprisePerformanceMonitor
                enabled={typeof window !== 'undefined' && window.location.hostname === 'localhost'}
                showDetails={process.env.NODE_ENV === 'development'}
                position="bottom-right"
              />
            </div>
          </AccessibilityFeatures>
        </EnhancedChatProvider>
      </DocumentProvider>
    </ErrorBoundary>
  );
}

export default App;