import React from 'react';
import { Menu, MessageCircle, FileText, BarChart3, Shield, Workflow, Globe, Settings, Bell, User } from 'lucide-react';

interface HeaderProps {
  onToggleSidebar: () => void;
  currentView: string;
  user?: any;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar, currentView, user }) => {
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
    <header className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <Menu size={20} />
        </button>
        
        <div className="flex items-center space-x-2">
          {getViewIcon()}
          <h1 className="text-xl font-semibold">{getViewTitle()}</h1>
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
        {/* System Status */}
        <div className="hidden sm:flex items-center space-x-2 text-sm text-gray-400">
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
          <span>All Systems Operational</span>
        </div>

        {/* Notifications */}
        <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors relative">
          <Bell size={16} />
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full text-xs flex items-center justify-center text-white">
            3
          </span>
        </button>

        {/* User Menu */}
        {user && (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-emerald-600 rounded-full flex items-center justify-center">
              <User size={16} />
            </div>
            <div className="hidden md:block">
              <div className="text-sm font-medium">{user.name}</div>
              <div className="text-xs text-gray-400 capitalize">{user.role}</div>
            </div>
          </div>
        )}
        
        <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
          <Settings size={16} />
        </button>
      </div>
    </header>
  );
};