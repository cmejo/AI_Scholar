import React, { useState, useEffect } from 'react';
import { 
  Menu, MessageCircle, FileText, BarChart3, Shield, Settings, 
  User, HelpCircle, Info, ChevronLeft, ChevronRight, Zap,
  Workflow, Network, Monitor, Accessibility
} from 'lucide-react';

export type ViewType = 'chat' | 'documents' | 'analytics' | 'security' | 'workflows' | 'integrations' | 'settings' | 'profile' | 'help' | 'about';

interface NavigationItem {
  id: ViewType;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  shortcut?: string;
  badge?: string;
  category: 'main' | 'tools' | 'system';
}

interface EnhancedSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  isMobile: boolean;
  performanceMode?: boolean;
}

const navigationItems: NavigationItem[] = [
  // Main Features
  { 
    id: 'chat', 
    label: 'AI Chat', 
    icon: MessageCircle, 
    description: 'Intelligent conversation interface',
    shortcut: 'Alt+1',
    category: 'main'
  },
  { 
    id: 'documents', 
    label: 'Documents', 
    icon: FileText, 
    description: 'Document management and analysis',
    shortcut: 'Alt+2',
    category: 'main'
  },
  { 
    id: 'analytics', 
    label: 'Analytics', 
    icon: BarChart3, 
    description: 'Usage metrics and insights',
    shortcut: 'Alt+3',
    badge: 'New',
    category: 'main'
  },
  
  // Tools
  { 
    id: 'workflows', 
    label: 'Workflows', 
    icon: Workflow, 
    description: 'Process automation and management',
    shortcut: 'Alt+4',
    category: 'tools'
  },
  { 
    id: 'integrations', 
    label: 'Integrations', 
    icon: Network, 
    description: 'Third-party service connections',
    shortcut: 'Alt+5',
    category: 'tools'
  },
  { 
    id: 'security', 
    label: 'Security', 
    icon: Shield, 
    description: 'Security dashboard and monitoring',
    shortcut: 'Alt+6',
    category: 'tools'
  },
  
  // System
  { 
    id: 'settings', 
    label: 'Settings', 
    icon: Settings, 
    description: 'Application configuration',
    category: 'system'
  },
  { 
    id: 'profile', 
    label: 'Profile', 
    icon: User, 
    description: 'User account management',
    category: 'system'
  },
  { 
    id: 'help', 
    label: 'Help', 
    icon: HelpCircle, 
    description: 'Documentation and support',
    category: 'system'
  },
  { 
    id: 'about', 
    label: 'About', 
    icon: Info, 
    description: 'Application information',
    category: 'system'
  },
];

export const EnhancedSidebar: React.FC<EnhancedSidebarProps> = ({
  isOpen,
  onToggle,
  currentView,
  onViewChange,
  isMobile,
  performanceMode = false
}) => {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(new Set());

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.altKey && !event.ctrlKey && !event.shiftKey) {
        const shortcutMap: Record<string, ViewType> = {
          '1': 'chat',
          '2': 'documents', 
          '3': 'analytics',
          '4': 'workflows',
          '5': 'integrations',
          '6': 'security'
        };
        
        const view = shortcutMap[event.key];
        if (view) {
          event.preventDefault();
          onViewChange(view);
          
          // Announce navigation for screen readers
          const item = navigationItems.find(item => item.id === view);
          if (item) {
            const announcement = `Navigated to ${item.label}`;
            const ariaLive = document.createElement('div');
            ariaLive.setAttribute('aria-live', 'polite');
            ariaLive.setAttribute('aria-atomic', 'true');
            ariaLive.className = 'sr-only';
            ariaLive.textContent = announcement;
            document.body.appendChild(ariaLive);
            setTimeout(() => document.body.removeChild(ariaLive), 1000);
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onViewChange]);

  const toggleCategory = (category: string) => {
    const newCollapsed = new Set(collapsedCategories);
    if (newCollapsed.has(category)) {
      newCollapsed.delete(category);
    } else {
      newCollapsed.add(category);
    }
    setCollapsedCategories(newCollapsed);
  };

  const renderNavigationSection = (category: 'main' | 'tools' | 'system', title: string) => {
    const items = navigationItems.filter(item => item.category === category);
    const isCollapsed = collapsedCategories.has(category);
    
    return (
      <div key={category} className="navigation-section">
        {isOpen && (
          <button
            onClick={() => toggleCategory(category)}
            className="category-header"
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 20px',
              background: 'none',
              border: 'none',
              color: '#9ca3af',
              fontSize: '12px',
              fontWeight: '600',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              cursor: 'pointer',
              transition: 'color 0.2s ease'
            }}
            onMouseOver={(e) => e.currentTarget.style.color = '#d1d5db'}
            onMouseOut={(e) => e.currentTarget.style.color = '#9ca3af'}
            aria-expanded={!isCollapsed}
            aria-controls={`nav-section-${category}`}
          >
            <span>{title}</span>
            {isCollapsed ? 
              <ChevronRight style={{ width: '14px', height: '14px' }} /> : 
              <ChevronLeft style={{ width: '14px', height: '14px' }} />
            }
          </button>
        )}
        
        <div 
          id={`nav-section-${category}`}
          style={{ 
            display: isCollapsed && isOpen ? 'none' : 'block',
            marginBottom: '16px'
          }}
        >
          {items.map((item) => {
            const IconComponent = item.icon;
            const isActive = currentView === item.id;
            const isHovered = hoveredItem === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                onMouseEnter={() => setHoveredItem(item.id)}
                onMouseLeave={() => setHoveredItem(null)}
                className="nav-item"
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  padding: isOpen ? '12px 20px' : '12px',
                  background: isActive ? 'rgba(16, 185, 129, 0.15)' : 
                             isHovered ? 'rgba(255,255,255,0.05)' : 'none',
                  border: 'none',
                  color: isActive ? '#10b981' : isHovered ? 'white' : '#9ca3af',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  borderLeft: isActive ? '3px solid #10b981' : '3px solid transparent',
                  justifyContent: isOpen ? 'flex-start' : 'center',
                  position: 'relative',
                  borderRadius: isOpen ? '0 8px 8px 0' : '8px',
                  margin: isOpen ? '0' : '4px 8px'
                }}
                aria-label={`${item.label}${item.shortcut ? ` (${item.shortcut})` : ''}`}
                title={!isOpen ? `${item.label}${item.shortcut ? ` (${item.shortcut})` : ''}` : undefined}
              >
                <IconComponent style={{ 
                  width: '20px', 
                  height: '20px',
                  marginRight: isOpen ? '12px' : '0',
                  flexShrink: 0
                }} />
                
                {isOpen && (
                  <>
                    <div style={{ flex: 1, textAlign: 'left' }}>
                      <div style={{ 
                        fontSize: '14px', 
                        fontWeight: '500',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        {item.label}
                        {item.badge && (
                          <span style={{
                            background: '#ef4444',
                            color: 'white',
                            fontSize: '10px',
                            padding: '2px 6px',
                            borderRadius: '10px',
                            fontWeight: '600'
                          }}>
                            {item.badge}
                          </span>
                        )}
                      </div>
                      {!performanceMode && (
                        <div style={{ 
                          fontSize: '11px', 
                          color: '#6b7280',
                          marginTop: '2px'
                        }}>
                          {item.description}
                        </div>
                      )}
                    </div>
                    
                    {item.shortcut && (
                      <div style={{
                        fontSize: '10px',
                        color: '#6b7280',
                        background: 'rgba(255,255,255,0.1)',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontFamily: 'monospace'
                      }}>
                        {item.shortcut}
                      </div>
                    )}
                  </>
                )}
                
                {/* Performance indicator */}
                {performanceMode && isActive && (
                  <div style={{
                    position: 'absolute',
                    top: '4px',
                    right: '4px',
                    width: '6px',
                    height: '6px',
                    background: '#10b981',
                    borderRadius: '50%',
                    animation: 'pulse 2s infinite'
                  }} />
                )}
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Mobile overlay */}
      {isMobile && isOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            zIndex: 40,
            backdropFilter: 'blur(4px)'
          }}
          onClick={onToggle}
          aria-hidden="true"
        />
      )}
      
      {/* Sidebar */}
      <aside
        style={{
          width: isOpen ? '280px' : '70px',
          background: 'linear-gradient(180deg, #374151 0%, #1f2937 100%)',
          transition: 'width 0.3s ease',
          borderRight: '1px solid rgba(255,255,255,0.1)',
          position: isMobile ? 'fixed' : 'relative',
          left: isMobile && !isOpen ? '-280px' : '0',
          top: 0,
          height: '100vh',
          zIndex: 50,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
        aria-label="Main navigation"
        role="navigation"
      >
        {/* Sidebar Header */}
        <div style={{ 
          padding: '20px', 
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: isOpen ? 'space-between' : 'center',
          flexShrink: 0
        }}>
          {isOpen && (
            <div style={{ 
              color: 'white', 
              fontWeight: 'bold', 
              fontSize: '1.2em',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Zap style={{ width: '20px', height: '20px', color: '#10b981' }} />
              AI Scholar
              {performanceMode && (
                <Monitor style={{ width: '16px', height: '16px', color: '#f59e0b' }} />
              )}
            </div>
          )}
          
          <button
            onClick={onToggle}
            style={{
              background: 'none',
              border: 'none',
              color: '#9ca3af',
              cursor: 'pointer',
              padding: '8px',
              borderRadius: '6px',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
              e.currentTarget.style.color = 'white';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'none';
              e.currentTarget.style.color = '#9ca3af';
            }}
            aria-label={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            aria-expanded={isOpen}
          >
            <Menu style={{ width: '20px', height: '20px' }} />
          </button>
        </div>

        {/* Navigation Items */}
        <nav style={{ 
          padding: '20px 0', 
          flex: 1, 
          overflowY: 'auto',
          overflowX: 'hidden'
        }}>
          {renderNavigationSection('main', 'Main Features')}
          {renderNavigationSection('tools', 'Tools')}
          {renderNavigationSection('system', 'System')}
        </nav>

        {/* Accessibility indicator */}
        {isOpen && (
          <div style={{
            padding: '16px 20px',
            borderTop: '1px solid rgba(255,255,255,0.1)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: '#6b7280',
            fontSize: '12px'
          }}>
            <Accessibility style={{ width: '14px', height: '14px' }} />
            <span>Keyboard navigation enabled</span>
          </div>
        )}
      </aside>

      {/* Add pulse animation */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        .sr-only {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
          border: 0;
        }
      `}</style>
    </>
  );
};