import React, { useState } from 'react';
import { Menu, MessageCircle, User, LogIn, Settings, ChevronDown } from 'lucide-react';

interface HeaderProps {
  onToggleSidebar: () => void;
  currentView: string;
  user?: { name: string; email: string; role?: string } | null;
  onShowAuth?: () => void;
  onShowProfile?: () => void;
  onShowSettings?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ 
  onToggleSidebar, 
  currentView, 
  user, 
  onShowAuth, 
  onShowProfile,
  onShowSettings 
}) => {
  const [showUserMenu, setShowUserMenu] = useState(false);

  return (
    <header className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <button
          onClick={onToggleSidebar}
          className="text-gray-400 hover:text-white p-1 rounded-md hover:bg-gray-700 transition-colors"
          aria-label="Toggle sidebar"
        >
          <Menu className="w-6 h-6" />
        </button>
        
        <div className="flex items-center space-x-3">
          <MessageCircle className="w-8 h-8 text-purple-500" />
          <div>
            <h1 className="text-xl font-bold">AI Scholar</h1>
            <p className="text-sm text-gray-400 capitalize">{currentView}</p>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Settings Button - Always visible */}
        <button
          onClick={onShowSettings}
          className="text-gray-400 hover:text-white p-2 rounded-md hover:bg-gray-700 transition-colors"
          aria-label="Settings"
          title="Settings"
        >
          <Settings className="w-5 h-5" />
        </button>

        {user ? (
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 text-sm text-gray-300 hover:text-white transition-colors bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded-lg"
            >
              <User className="w-4 h-4" />
              <span className="hidden sm:inline">{user.name}</span>
              <ChevronDown className="w-4 h-4" />
            </button>

            {/* User Dropdown Menu */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50">
                <div className="p-3 border-b border-gray-600">
                  <p className="font-medium text-white">{user.name}</p>
                  <p className="text-sm text-gray-400">{user.email}</p>
                  {user.role && (
                    <p className="text-xs text-purple-400 capitalize mt-1">{user.role}</p>
                  )}
                </div>
                <div className="py-1">
                  <button
                    onClick={() => {
                      onShowProfile?.();
                      setShowUserMenu(false);
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 transition-colors flex items-center space-x-2"
                  >
                    <User className="w-4 h-4" />
                    <span>View Profile</span>
                  </button>
                  <button
                    onClick={() => {
                      onShowSettings?.();
                      setShowUserMenu(false);
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 transition-colors flex items-center space-x-2"
                  >
                    <Settings className="w-4 h-4" />
                    <span>Settings</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={onShowAuth}
            className="flex items-center space-x-2 text-sm text-gray-400 hover:text-white transition-colors bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded-lg"
          >
            <LogIn className="w-4 h-4" />
            <span>Sign In</span>
          </button>
        )}
      </div>

      {/* Click outside to close user menu */}
      {showUserMenu && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowUserMenu(false)}
        />
      )}
    </header>
  );
};