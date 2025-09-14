import React, { useState, useEffect, Suspense, lazy } from 'react';
import { EnhancedSidebar, ViewType } from './components/navigation/EnhancedSidebar';
import { EnhancedHeader } from './components/navigation/EnhancedHeader';
import { PerformanceMonitor } from './components/monitoring/PerformanceMonitor';
import { AccessibilityToolbar } from './components/accessibility/AccessibilityToolbar';
import { useMobileDetection } from './hooks/useMobileDetection';
import { ErrorBoundary } from './components/ErrorBoundary';

// Lazy load components for better performance
const ChatView = lazy(() => import('./components/views/ChatView'));
const DocumentsView = lazy(() => import('./components/views/DocumentsView'));
const AnalyticsView = lazy(() => import('./components/views/AnalyticsView'));
const SecurityView = lazy(() => import('./components/views/SecurityView'));
const WorkflowsView = lazy(() => import('./components/views/WorkflowsView'));
const IntegrationsView = lazy(() => import('./components/views/IntegrationsView'));
const SettingsView = lazy(() => import('./components/views/SettingsView'));
const ProfileView = lazy(() => import('./components/views/ProfileView'));
const HelpView = lazy(() => import('./components/views/HelpView'));
const AboutView = lazy(() => import('./components/views/AboutView'));

interface User {
  name: string;
  email: string;
  role: string;
  avatar?: string;
}

// Mock user for demonstration
const mockUser: User = {
  name: 'Administrator',
  email: 'account@cmejo.com',
  role: 'Administrator'
};

function App(): JSX.Element {
  console.log('🚀 AI SCHOLAR - STEP 2: ADVANCED NAVIGATION SYSTEM');
  
  // State management
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [user] = useState<User | null>(mockUser); // Will be replaced with actual auth
  const [performanceMonitorVisible, setPerformanceMonitorVisible] = useState(false);
  const [accessibilityToolbarVisible, setAccessibilityToolbarVisible] = useState(false);
  const [performanceMode, setPerformanceMode] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  
  // Device detection
  const { isMobile, isTablet, deviceType, screenWidth } = useMobileDetection();

  // Initialize app
  useEffect(() => {
    console.log('🚀 Step 2 Advanced App mounted - Enhanced navigation system active');
    document.title = 'AI Scholar - Advanced Research Assistant';
    
    // Auto-open sidebar on desktop
    if (!isMobile && screenWidth >= 1024) {
      setSidebarOpen(true);
    }
  }, [isMobile, screenWidth]);

  // Online/offline detection
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Performance monitoring toggle
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl+Shift+P to toggle performance monitor
      if (event.ctrlKey && event.shiftKey && event.key === 'P') {
        event.preventDefault();
        setPerformanceMonitorVisible(!performanceMonitorVisible);
      }
      
      // Ctrl+Shift+A to toggle accessibility toolbar
      if (event.ctrlKey && event.shiftKey && event.key === 'A') {
        event.preventDefault();
        setAccessibilityToolbarVisible(!accessibilityToolbarVisible);
      }
      
      // Ctrl+Shift+M to toggle performance mode
      if (event.ctrlKey && event.shiftKey && event.key === 'M') {
        event.preventDefault();
        setPerformanceMode(!performanceMode);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [performanceMonitorVisible, accessibilityToolbarVisible, performanceMode]);

  // Auto-close sidebar on mobile when view changes
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  }, [currentView, isMobile]);

  // Loading component
  const LoadingFallback = ({ viewName }: { viewName: string }) => (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100%',
      background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1b69 100%)',
      color: 'white'
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '3px solid rgba(16, 185, 129, 0.3)',
          borderTop: '3px solid #10b981',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 16px'
        }} />
        <p style={{ fontSize: '16px', color: '#9ca3af' }}>
          Loading {viewName}...
        </p>
      </div>
    </div>
  );

  // Placeholder component for views not yet implemented
  const PlaceholderView = ({ viewName, description }: { viewName: string; description: string }) => (
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
          <div>
            <h1 style={{ margin: 0, fontSize: '2em', color: '#10b981' }}>
              {viewName}
            </h1>
            <p style={{ margin: '5px 0 0 0', color: '#cbd5e1', fontSize: '1.1em' }}>
              {description}
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
            🚧 {viewName} - Enhanced Version Coming Soon
          </h2>
          <p style={{ fontSize: '16px', lineHeight: '1.6', marginBottom: '20px' }}>
            This section will contain the full {viewName.toLowerCase()} functionality with advanced features including:
          </p>
          
          <div style={{ 
            background: 'rgba(16, 185, 129, 0.1)', 
            padding: '20px', 
            borderRadius: '10px',
            border: '1px solid rgba(16, 185, 129, 0.3)'
          }}>
            <h3 style={{ color: '#10b981', marginTop: 0 }}>✨ Enhanced Features</h3>
            <ul style={{ lineHeight: '1.8' }}>
              <li>🎯 Advanced user interface with responsive design</li>
              <li>⚡ Performance-optimized lazy loading</li>
              <li>♿ Full accessibility compliance (WCAG)</li>
              <li>📱 Mobile-first responsive layout</li>
              <li>🔍 Real-time search and filtering</li>
              <li>📊 Integrated analytics and monitoring</li>
              <li>🔐 Enterprise-grade security features</li>
              <li>🌐 Multi-language support</li>
            </ul>
          </div>

          <div style={{ 
            marginTop: '20px',
            padding: '16px',
            background: 'rgba(59, 130, 246, 0.1)',
            borderRadius: '8px',
            border: '1px solid rgba(59, 130, 246, 0.3)'
          }}>
            <p style={{ margin: 0, fontSize: '14px', color: '#93c5fd' }}>
              💡 <strong>Pro Tip:</strong> Use keyboard shortcuts Alt+1-6 to quickly navigate between sections, 
              or Ctrl+Shift+P to toggle the performance monitor.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  // Render current view with lazy loading
  const renderCurrentView = () => {
    const viewComponents = {
      chat: () => <PlaceholderView viewName="AI Chat" description="Intelligent conversation interface with advanced AI capabilities" />,
      documents: () => <PlaceholderView viewName="Document Manager" description="Advanced document processing and analysis system" />,
      analytics: () => <PlaceholderView viewName="Analytics Dashboard" description="Comprehensive usage metrics and performance insights" />,
      security: () => <PlaceholderView viewName="Security Center" description="Enterprise-grade security monitoring and threat detection" />,
      workflows: () => <PlaceholderView viewName="Workflow Manager" description="Intelligent process automation and workflow orchestration" />,
      integrations: () => <PlaceholderView viewName="Integration Hub" description="Seamless third-party service connections and API management" />,
      settings: () => <PlaceholderView viewName="Settings" description="Comprehensive application configuration and preferences" />,
      profile: () => <PlaceholderView viewName="User Profile" description="Personal account management and customization options" />,
      help: () => <PlaceholderView viewName="Help Center" description="Comprehensive documentation, tutorials, and support resources" />,
      about: () => <PlaceholderView viewName="About AI Scholar" description="Application information, version details, and credits" />
    };

    const ViewComponent = viewComponents[currentView];
    
    return (
      <ErrorBoundary>
        <Suspense fallback={<LoadingFallback viewName={currentView} />}>
          <ViewComponent />
        </Suspense>
      </ErrorBoundary>
    );
  };

  return (
    <div style={{ 
      display: 'flex', 
      minHeight: '100vh', 
      background: '#1a1a1a',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Enhanced Sidebar */}
      <EnhancedSidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        currentView={currentView}
        onViewChange={setCurrentView}
        isMobile={isMobile}
        performanceMode={performanceMode}
      />

      {/* Main Content Area */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Enhanced Header */}
        <EnhancedHeader
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          currentView={currentView}
          user={user}
          onShowAuth={() => console.log('Show auth modal')}
          onShowProfile={() => setCurrentView('profile')}
          onShowSettings={() => setCurrentView('settings')}
          isMobile={isMobile}
          performanceMode={performanceMode}
          isOnline={isOnline}
        />

        {/* Main View Content */}
        <main style={{ 
          flex: 1, 
          overflow: 'hidden',
          position: 'relative'
        }}>
          {renderCurrentView()}
        </main>
      </div>

      {/* Performance Monitor */}
      <PerformanceMonitor
        isVisible={performanceMonitorVisible}
        onToggle={() => setPerformanceMonitorVisible(!performanceMonitorVisible)}
        position="top-right"
      />

      {/* Accessibility Toolbar */}
      <AccessibilityToolbar
        isVisible={accessibilityToolbarVisible}
        onToggle={() => setAccessibilityToolbarVisible(!accessibilityToolbarVisible)}
        position="left"
      />

      {/* Performance Mode Indicator */}
      {performanceMode && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(245, 158, 11, 0.9)',
          color: 'white',
          padding: '8px 16px',
          borderRadius: '20px',
          fontSize: '12px',
          fontWeight: 'bold',
          zIndex: 1000,
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(245, 158, 11, 0.3)'
        }}>
          ⚡ Performance Mode Active
        </div>
      )}

      {/* Device Info (Development) */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          background: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '8px',
          fontSize: '11px',
          fontFamily: 'monospace',
          zIndex: 999,
          border: '1px solid rgba(255, 255, 255, 0.2)'
        }}>
          {deviceType} | {screenWidth}px | {isMobile ? 'Mobile' : isTablet ? 'Tablet' : 'Desktop'}
        </div>
      )}

      {/* Global Styles */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        /* Smooth scrolling */
        html {
          scroll-behavior: smooth;
        }
        
        /* Focus styles for accessibility */
        *:focus {
          outline: 2px solid #10b981;
          outline-offset: 2px;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
        }
        
        ::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.1);
        }
        
        ::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.3);
          border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.5);
        }
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
          * {
            -webkit-tap-highlight-color: transparent;
          }
          
          input, textarea, select {
            font-size: 16px; /* Prevent zoom on iOS */
          }
        }
        
        /* Print styles */
        @media print {
          .no-print {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}

export default App;