import React, { useState } from 'react';
import { Menu, MessageCircle, FileText, BarChart3, Shield, Workflow, Globe, Settings, Bell, User, Eye } from 'lucide-react';
import { AccessibilitySettings } from './AccessibilitySettings';
import { accessibilityService } from '../services/accessibilityService';

interface HeaderProps {
  onToggleSidebar: () => void;
  currentView: string;
  user?: any;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar, currentView, user }) => {
  const [showAccessibilitySettings, setShowAccessibilitySettings] = useState(false);
  const getViewIcon = () => {
    switch (currentView) {
      case 'chat': return <MessageCircle size={20} className="text-purple-400" />;
      case 'documents': return <FileText size={20} className="text-emerald-400" />;
      case 'analytics': return <BarChart3 size={20} className="text-blue-400" />;
      case 'security': return <Shield size={20} className="text-red-400" />;
      case 'workflows': return <Workflow size={20} className="text-yellow-400" />;
      case 'integrations': return <Globe size={20} className="text-indigo-400" />;
      default: return <MessageCircle size={20} className="text-purple-400" />;
    }
  };

  const getViewTitle = () => {
    switch (currentView) {
      case 'chat': return 'Enhanced RAG Chat';
      case 'documents': return 'Smart Document Manager';
      case 'analytics': return 'Enterprise Analytics';
      case 'security': return 'Security Dashboard';
      case 'workflows': return 'Workflow Manager';
      case 'integrations': return 'Integration Hub';
      default: return 'AI Scholar Enterprise';
    }
  };

  return (
    <header 
      className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between"
      role="banner"
      aria-label="Main navigation header"
    >
      <div className="flex items-center space-x-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors focus-ring"
          aria-label="Toggle sidebar navigation"
          aria-expanded="false"
          aria-controls="main-sidebar"
          title="Open navigation menu"
        >
          <Menu size={20} aria-hidden="true" />
        </button>
        
        <div className="flex items-center space-x-2">
          <div aria-hidden="true">{getViewIcon()}</div>
          <h1 className="text-xl font-semibold" id="main-heading">
            {getViewTitle()}
          </h1>
        </div>
      </div>
      
      <nav className="flex items-center space-x-4" role="navigation" aria-label="User actions">
        {/* System Status */}
        <div 
          className="hidden sm:flex items-center space-x-2 text-sm text-gray-400"
          role="status"
          aria-live="polite"
          aria-label="System status"
        >
          <div 
            className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"
            aria-hidden="true"
          ></div>
          <span>All Systems Operational</span>
        </div>

        {/* Notifications */}
        <button 
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors relative focus-ring"
          aria-label="Notifications (3 unread)"
          aria-describedby="notification-count"
          title="View notifications"
          onClick={() => accessibilityService.announce('Notifications panel opened', 'polite')}
        >
          <Bell size={16} aria-hidden="true" />
          <span 
            id="notification-count"
            className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full text-xs flex items-center justify-center text-white"
            aria-label="3 unread notifications"
          >
            3
          </span>
        </button>

        {/* Accessibility Settings Button */}
        <button 
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors focus-ring"
          aria-label="Open accessibility settings"
          title="Accessibility settings and options"
          onClick={() => {
            setShowAccessibilitySettings(true);
            accessibilityService.announce('Accessibility settings opened', 'polite');
          }}
        >
          <Eye size={16} aria-hidden="true" />
        </button>

        {/* User Menu */}
        {user && (
          <div className="flex items-center space-x-2" role="group" aria-label="User information">
            <div 
              className="w-8 h-8 bg-gradient-to-br from-purple-600 to-emerald-600 rounded-full flex items-center justify-center"
              aria-hidden="true"
            >
              <User size={16} />
            </div>
            <div className="hidden md:block">
              <div className="text-sm font-medium" aria-label={`User: ${user.name}`}>
                {user.name}
              </div>
              <div className="text-xs text-gray-400 capitalize" aria-label={`Role: ${user.role}`}>
                {user.role}
              </div>
            </div>
          </div>
        )}
        
        <button 
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors focus-ring"
          aria-label="Open general settings"
          title="Application settings"
          onClick={() => accessibilityService.announce('Settings panel opened', 'polite')}
        >
          <Settings size={16} aria-hidden="true" />
        </button>
      </nav>

      {/* Accessibility Settings Modal */}
      <AccessibilitySettings
        isOpen={showAccessibilitySettings}
        onClose={() => {
          setShowAccessibilitySettings(false);
          accessibilityService.announce('Accessibility settings closed', 'polite');
        }}
      />
    </header>
  );
};