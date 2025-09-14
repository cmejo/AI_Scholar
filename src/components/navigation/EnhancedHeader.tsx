import React, { useState, useEffect, useRef } from 'react';
import { 
  Menu, Bell, Search, User, Settings, LogOut, LogIn, 
  Moon, Sun, Zap, Wifi, WifiOff, Activity, Shield,
  ChevronDown, Maximize2, Minimize2, Volume2, VolumeX,
  Accessibility, Globe, HelpCircle
} from 'lucide-react';
import { ViewType } from './EnhancedSidebar';

interface User {
  name: string;
  email: string;
  role: string;
  avatar?: string;
}

interface EnhancedHeaderProps {
  onToggleSidebar: () => void;
  currentView: ViewType;
  user?: User | null;
  onShowAuth?: () => void;
  onShowProfile?: () => void;
  onShowSettings?: () => void;
  isMobile: boolean;
  performanceMode?: boolean;
  isOnline?: boolean;
  connectionStatus?: 'connected' | 'disconnected' | 'checking';
  lastHealthCheck?: Date | null;
  onRefreshConnection?: () => void;
}

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
  timestamp: Date;
  read: boolean;
}

const mockNotifications: NotificationItem[] = [
  {
    id: '1',
    title: 'System Update',
    message: 'AI Scholar has been updated to version 2.1.0',
    type: 'info',
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    read: false
  },
  {
    id: '2',
    title: 'Document Processed',
    message: 'Your research paper has been successfully analyzed',
    type: 'success',
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    read: false
  },
  {
    id: '3',
    title: 'Performance Alert',
    message: 'High memory usage detected in analytics module',
    type: 'warning',
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    read: true
  }
];

export const EnhancedHeader: React.FC<EnhancedHeaderProps> = ({
  onToggleSidebar,
  currentView,
  user,
  onShowAuth,
  onShowProfile,
  onShowSettings,
  isMobile,
  performanceMode = false,
  isOnline = true
}) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [darkMode, setDarkMode] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [notifications, setNotifications] = useState(mockNotifications);
  
  const userMenuRef = useRef<HTMLDivElement>(null);
  const notificationRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search when opened
  useEffect(() => {
    if (showSearch && searchRef.current) {
      searchRef.current.focus();
    }
  }, [showSearch]);

  // Fullscreen detection
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (error) {
      console.error('Fullscreen toggle failed:', error);
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  const getViewTitle = (view: ViewType): string => {
    const titles: Record<ViewType, string> = {
      chat: 'AI Chat',
      documents: 'Document Manager',
      analytics: 'Analytics Dashboard',
      security: 'Security Center',
      workflows: 'Workflow Manager',
      integrations: 'Integration Hub',
      settings: 'Settings',
      profile: 'User Profile',
      help: 'Help Center',
      about: 'About AI Scholar'
    };
    return titles[view] || 'AI Scholar';
  };

  const markNotificationAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const formatTimeAgo = (date: Date): string => {
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  return (
    <header style={{
      background: 'linear-gradient(90deg, #1f2937 0%, #374151 100%)',
      borderBottom: '1px solid rgba(255,255,255,0.1)',
      padding: isMobile ? '12px 16px' : '16px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'relative',
      zIndex: 30,
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
    }}>
      {/* Left Section */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Mobile menu button */}
        {isMobile && (
          <button
            onClick={onToggleSidebar}
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
            aria-label="Toggle sidebar"
          >
            <Menu style={{ width: '20px', height: '20px' }} />
          </button>
        )}

        {/* Current view info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div>
            <h1 style={{ 
              margin: 0, 
              fontSize: isMobile ? '18px' : '20px', 
              fontWeight: 'bold',
              color: 'white'
            }}>
              {getViewTitle(currentView)}
            </h1>
            {!isMobile && (
              <p style={{ 
                margin: '2px 0 0 0', 
                fontSize: '14px', 
                color: '#9ca3af'
              }}>
                {performanceMode ? 'Performance Mode Active' : 'Advanced Research Assistant'}
              </p>
            )}
          </div>
          
          {/* Status indicators */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Online status */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 8px',
              borderRadius: '12px',
              background: isOnline ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
              fontSize: '12px',
              color: isOnline ? '#10b981' : '#ef4444'
            }}>
              {isOnline ? <Wifi style={{ width: '12px', height: '12px' }} /> : <WifiOff style={{ width: '12px', height: '12px' }} />}
              {!isMobile && <span>{isOnline ? 'Online' : 'Offline'}</span>}
            </div>
            
            {/* Performance indicator */}
            {performanceMode && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 8px',
                borderRadius: '12px',
                background: 'rgba(245, 158, 11, 0.2)',
                fontSize: '12px',
                color: '#f59e0b'
              }}>
                <Activity style={{ width: '12px', height: '12px' }} />
                {!isMobile && <span>Monitoring</span>}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Center Section - Search */}
      {!isMobile && (
        <div style={{ 
          flex: 1, 
          maxWidth: '400px', 
          margin: '0 24px',
          position: 'relative'
        }}>
          {showSearch ? (
            <div style={{ position: 'relative' }}>
              <input
                ref={searchRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onBlur={() => {
                  if (!searchQuery) setShowSearch(false);
                }}
                placeholder="Search documents, conversations, settings..."
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  padding: '8px 40px 8px 12px',
                  color: 'white',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'all 0.2s ease'
                }}
                onFocus={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.15)';
                  e.currentTarget.style.borderColor = '#10b981';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)';
                }}
              />
              <Search style={{
                position: 'absolute',
                right: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                width: '16px',
                height: '16px',
                color: '#9ca3af'
              }} />
            </div>
          ) : (
            <button
              onClick={() => setShowSearch(true)}
              style={{
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '8px',
                padding: '8px 12px',
                color: '#9ca3af',
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                width: '100%'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.15)';
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.3)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)';
              }}
            >
              <Search style={{ width: '16px', height: '16px' }} />
              <span>Search...</span>
            </button>
          )}
        </div>
      )}

      {/* Right Section */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {/* Mobile search */}
        {isMobile && (
          <button
            onClick={() => setShowSearch(!showSearch)}
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
            <Search style={{ width: '18px', height: '18px' }} />
          </button>
        )}

        {/* Quick actions */}
        {!isMobile && (
          <>
            {/* Sound toggle */}
            <button
              onClick={() => setSoundEnabled(!soundEnabled)}
              style={{
                background: 'none',
                border: 'none',
                color: soundEnabled ? '#10b981' : '#9ca3af',
                cursor: 'pointer',
                padding: '8px',
                borderRadius: '6px',
                transition: 'all 0.2s ease'
              }}
              title={soundEnabled ? 'Disable sounds' : 'Enable sounds'}
            >
              {soundEnabled ? <Volume2 style={{ width: '18px', height: '18px' }} /> : <VolumeX style={{ width: '18px', height: '18px' }} />}
            </button>

            {/* Fullscreen toggle */}
            <button
              onClick={toggleFullscreen}
              style={{
                background: 'none',
                border: 'none',
                color: '#9ca3af',
                cursor: 'pointer',
                padding: '8px',
                borderRadius: '6px',
                transition: 'all 0.2s ease'
              }}
              title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
              onMouseOver={(e) => e.currentTarget.style.color = 'white'}
              onMouseOut={(e) => e.currentTarget.style.color = '#9ca3af'}
            >
              {isFullscreen ? <Minimize2 style={{ width: '18px', height: '18px' }} /> : <Maximize2 style={{ width: '18px', height: '18px' }} />}
            </button>
          </>
        )}

        {/* Notifications */}
        <div style={{ position: 'relative' }} ref={notificationRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            style={{
              background: 'none',
              border: 'none',
              color: '#9ca3af',
              cursor: 'pointer',
              padding: '8px',
              borderRadius: '6px',
              transition: 'all 0.2s ease',
              position: 'relative'
            }}
            onMouseOver={(e) => e.currentTarget.style.color = 'white'}
            onMouseOut={(e) => e.currentTarget.style.color = '#9ca3af'}
            aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
          >
            <Bell style={{ width: '18px', height: '18px' }} />
            {unreadCount > 0 && (
              <span style={{
                position: 'absolute',
                top: '4px',
                right: '4px',
                background: '#ef4444',
                color: 'white',
                fontSize: '10px',
                fontWeight: 'bold',
                borderRadius: '50%',
                width: '16px',
                height: '16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                lineHeight: 1
              }}>
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {/* Notifications dropdown */}
          {showNotifications && (
            <div style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: '8px',
              width: '320px',
              background: '#374151',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '12px',
              boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)',
              zIndex: 100,
              overflow: 'hidden'
            }}>
              <div style={{
                padding: '16px',
                borderBottom: '1px solid rgba(255,255,255,0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <h3 style={{ margin: 0, color: 'white', fontSize: '16px' }}>Notifications</h3>
                {unreadCount > 0 && (
                  <span style={{ color: '#9ca3af', fontSize: '12px' }}>
                    {unreadCount} unread
                  </span>
                )}
              </div>
              
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    onClick={() => markNotificationAsRead(notification.id)}
                    style={{
                      padding: '12px 16px',
                      borderBottom: '1px solid rgba(255,255,255,0.05)',
                      cursor: 'pointer',
                      background: notification.read ? 'transparent' : 'rgba(16, 185, 129, 0.05)',
                      transition: 'background 0.2s ease'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                    onMouseOut={(e) => e.currentTarget.style.background = notification.read ? 'transparent' : 'rgba(16, 185, 129, 0.05)'}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                      <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: notification.type === 'error' ? '#ef4444' :
                                   notification.type === 'warning' ? '#f59e0b' :
                                   notification.type === 'success' ? '#10b981' : '#3b82f6',
                        marginTop: '6px',
                        flexShrink: 0
                      }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ 
                          color: 'white', 
                          fontSize: '14px', 
                          fontWeight: '500',
                          marginBottom: '4px'
                        }}>
                          {notification.title}
                        </div>
                        <div style={{ 
                          color: '#9ca3af', 
                          fontSize: '12px',
                          marginBottom: '4px'
                        }}>
                          {notification.message}
                        </div>
                        <div style={{ 
                          color: '#6b7280', 
                          fontSize: '11px'
                        }}>
                          {formatTimeAgo(notification.timestamp)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User menu */}
        <div style={{ position: 'relative' }} ref={userMenuRef}>
          {user ? (
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                padding: '4px',
                borderRadius: '8px',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
              onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
              onMouseOut={(e) => e.currentTarget.style.background = 'none'}
            >
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: user.avatar ? `url(${user.avatar})` : 'linear-gradient(45deg, #10b981, #3b82f6)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '14px',
                fontWeight: 'bold'
              }}>
                {!user.avatar && user.name.charAt(0).toUpperCase()}
              </div>
              {!isMobile && (
                <>
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontSize: '14px', fontWeight: '500' }}>{user.name}</div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>{user.role}</div>
                  </div>
                  <ChevronDown style={{ width: '16px', height: '16px', color: '#9ca3af' }} />
                </>
              )}
            </button>
          ) : (
            <button
              onClick={onShowAuth}
              style={{
                background: 'linear-gradient(45deg, #10b981, #059669)',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <LogIn style={{ width: '16px', height: '16px' }} />
              {!isMobile && <span>Sign In</span>}
            </button>
          )}

          {/* User dropdown menu */}
          {showUserMenu && user && (
            <div style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: '8px',
              width: '200px',
              background: '#374151',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '12px',
              boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)',
              zIndex: 100,
              overflow: 'hidden'
            }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <div style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>{user.name}</div>
                <div style={{ color: '#9ca3af', fontSize: '12px' }}>{user.email}</div>
              </div>
              
              <div style={{ padding: '8px 0' }}>
                <button
                  onClick={() => {
                    onShowProfile?.();
                    setShowUserMenu(false);
                  }}
                  style={{
                    width: '100%',
                    background: 'none',
                    border: 'none',
                    color: '#d1d5db',
                    cursor: 'pointer',
                    padding: '8px 16px',
                    fontSize: '14px',
                    textAlign: 'left',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    transition: 'background 0.2s ease'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'none'}
                >
                  <User style={{ width: '16px', height: '16px' }} />
                  Profile
                </button>
                
                <button
                  onClick={() => {
                    onShowSettings?.();
                    setShowUserMenu(false);
                  }}
                  style={{
                    width: '100%',
                    background: 'none',
                    border: 'none',
                    color: '#d1d5db',
                    cursor: 'pointer',
                    padding: '8px 16px',
                    fontSize: '14px',
                    textAlign: 'left',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    transition: 'background 0.2s ease'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'none'}
                >
                  <Settings style={{ width: '16px', height: '16px' }} />
                  Settings
                </button>
                
                <div style={{ height: '1px', background: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />
                
                <button
                  onClick={() => {
                    // Handle logout
                    setShowUserMenu(false);
                  }}
                  style={{
                    width: '100%',
                    background: 'none',
                    border: 'none',
                    color: '#ef4444',
                    cursor: 'pointer',
                    padding: '8px 16px',
                    fontSize: '14px',
                    textAlign: 'left',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    transition: 'background 0.2s ease'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'none'}
                >
                  <LogOut style={{ width: '16px', height: '16px' }} />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mobile search overlay */}
      {isMobile && showSearch && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          background: '#374151',
          border: '1px solid rgba(255,255,255,0.1)',
          borderTop: 'none',
          padding: '16px',
          zIndex: 100
        }}>
          <input
            ref={searchRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search..."
            style={{
              width: '100%',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '8px',
              padding: '12px',
              color: 'white',
              fontSize: '16px',
              outline: 'none'
            }}
          />
        </div>
      )}
    </header>
  );
};