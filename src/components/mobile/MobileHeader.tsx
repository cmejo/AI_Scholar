import {
    BarChart3,
    Bell,
    FileText,
    Globe,
    Menu,
    MessageCircle,
    Mic,
    MicOff,
    MoreVertical,
    RefreshCw,
    Search,
    Settings,
    Shield,
    User,
    Wifi,
    WifiOff,
    Workflow
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { mobileSyncService } from '../../services/mobileSyncService';
import { AccessibilitySettings } from '../AccessibilitySettings';
import { MobileSyncStatus } from './MobileSyncStatus';

import { MobileHeaderProps } from '../../types/ui';

interface ExtendedMobileHeaderProps extends MobileHeaderProps {
  isNavOpen: boolean;
}

export const MobileHeader: React.FC<ExtendedMobileHeaderProps> = ({
  currentView,
  user,
  onToggleNav,
  voiceEnabled,
  onToggleVoice,
  isNavOpen
}) => {
  const [showAccessibilitySettings, setShowAccessibilitySettings] = useState(false);
  const [showSyncStatus, setShowSyncStatus] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [syncInProgress, setSyncInProgress] = useState(false);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    const handleSyncStarted = () => setSyncInProgress(true);
    const handleSyncCompleted = () => setSyncInProgress(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    mobileSyncService.on('syncStarted', handleSyncStarted);
    mobileSyncService.on('syncCompleted', handleSyncCompleted);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      mobileSyncService.off('syncStarted', handleSyncStarted);
      mobileSyncService.off('syncCompleted', handleSyncCompleted);
    };
  }, []);
  const getViewIcon = () => {
    const iconProps = { size: 20, className: "text-white" };
    
    switch (currentView) {
      case 'chat': return <MessageCircle {...iconProps} className="text-purple-400" />;
      case 'documents': return <FileText {...iconProps} className="text-emerald-400" />;
      case 'analytics': return <BarChart3 {...iconProps} className="text-blue-400" />;
      case 'security': return <Shield {...iconProps} className="text-red-400" />;
      case 'workflows': return <Workflow {...iconProps} className="text-yellow-400" />;
      case 'integrations': return <Globe {...iconProps} className="text-indigo-400" />;
      default: return <MessageCircle {...iconProps} className="text-purple-400" />;
    }
  };

  const getViewTitle = () => {
    switch (currentView) {
      case 'chat': return 'Chat';
      case 'documents': return 'Documents';
      case 'analytics': return 'Analytics';
      case 'security': return 'Security';
      case 'workflows': return 'Workflows';
      case 'integrations': return 'Integrations';
      default: return 'AI Scholar';
    }
  };

  return (
    <header className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between relative z-50 safe-area-inset-top min-h-16">
      {/* Left Section */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onToggleNav}
          className={`
            p-3 rounded-lg transition-all duration-200 touch-manipulation min-w-touch-target min-h-touch-target flex items-center justify-center tap-highlight-none
            ${isNavOpen 
              ? 'bg-purple-600 text-white scale-95' 
              : 'hover:bg-gray-700 active:bg-gray-600 active:scale-95'
            }
          `}
          aria-label="Toggle navigation"
        >
          <Menu size={20} />
        </button>
        
        <div className="flex items-center space-x-3 flex-1 min-w-0">
          {getViewIcon()}
          <h1 className="text-responsive-lg font-semibold truncate">
            {getViewTitle()}
          </h1>
        </div>
      </div>
      
      {/* Right Section */}
      <div className="flex items-center space-x-1 flex-shrink-0">
        {/* Voice Toggle */}
        <button
          onClick={() => onToggleVoice(!voiceEnabled)}
          className={`
            p-2 rounded-lg transition-all duration-200 touch-manipulation min-w-touch-target min-h-touch-target flex items-center justify-center tap-highlight-none
            ${voiceEnabled 
              ? 'bg-blue-600 text-white scale-95' 
              : 'hover:bg-gray-700 active:bg-gray-600 active:scale-95'
            }
          `}
          aria-label={voiceEnabled ? 'Disable voice' : 'Enable voice'}
        >
          {voiceEnabled ? <Mic size={18} /> : <MicOff size={18} />}
        </button>

        {/* Sync Status */}
        <button
          onClick={() => setShowSyncStatus(true)}
          className={`
            p-2 rounded-lg transition-all duration-200 touch-manipulation min-w-touch-target min-h-touch-target flex items-center justify-center tap-highlight-none
            ${isOnline ? 'hover:bg-gray-700 active:bg-gray-600 active:scale-95' : 'bg-red-600/20'}
          `}
          aria-label={`Sync status: ${isOnline ? 'online' : 'offline'}`}
        >
          {syncInProgress ? (
            <RefreshCw size={18} className="animate-spin text-blue-400" />
          ) : isOnline ? (
            <Wifi size={18} className="text-green-400" />
          ) : (
            <WifiOff size={18} className="text-red-400" />
          )}
        </button>

        {/* Search Button - Hidden on very small screens */}
        <button
          className="p-2 hover:bg-gray-700 active:bg-gray-600 active:scale-95 rounded-lg transition-all duration-200 touch-manipulation min-w-touch-target min-h-touch-target flex items-center justify-center tap-highlight-none hidden xs:flex"
          aria-label="Search"
        >
          <Search size={18} />
        </button>

        {/* Notifications */}
        <button 
          className="p-2 hover:bg-gray-700 active:bg-gray-600 active:scale-95 rounded-lg transition-all duration-200 touch-manipulation min-w-touch-target min-h-touch-target flex items-center justify-center tap-highlight-none relative"
          aria-label="Notifications"
        >
          <Bell size={18} />
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-xs flex items-center justify-center text-white font-bold">
            3
          </span>
        </button>

        {/* User Avatar */}
        {user && (
          <button 
            className="p-2 hover:bg-gray-700 active:bg-gray-600 active:scale-95 rounded-lg transition-all duration-200 touch-manipulation min-w-touch-target min-h-touch-target flex items-center justify-center tap-highlight-none"
            aria-label="User menu"
          >
            <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-emerald-600 rounded-full flex items-center justify-center">
              <User size={16} />
            </div>
          </button>
        )}

        {/* Accessibility Settings - Hidden on very small screens */}
        <button
          onClick={() => setShowAccessibilitySettings(true)}
          className="p-2 hover:bg-gray-700 active:bg-gray-600 active:scale-95 rounded-lg transition-all duration-200 touch-manipulation min-w-touch-target min-h-touch-target flex items-center justify-center tap-highlight-none hidden xs:flex"
          aria-label="Accessibility settings"
        >
          <Settings size={18} />
        </button>

        {/* More Options */}
        <button
          className="p-2 hover:bg-gray-700 active:bg-gray-600 active:scale-95 rounded-lg transition-all duration-200 touch-manipulation min-w-touch-target min-h-touch-target flex items-center justify-center tap-highlight-none"
          aria-label="More options"
        >
          <MoreVertical size={18} />
        </button>
      </div>

      {/* Connection Status Indicator */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-500 to-blue-500 opacity-75" />
      
      {/* Accessibility Settings Modal */}
      <AccessibilitySettings
        isOpen={showAccessibilitySettings}
        onClose={() => setShowAccessibilitySettings(false)}
      />

      {/* Sync Status Modal */}
      <MobileSyncStatus
        isVisible={showSyncStatus}
        onClose={() => setShowSyncStatus(false)}
      />
    </header>
  );
};