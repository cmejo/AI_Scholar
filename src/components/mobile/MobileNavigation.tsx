import React from 'react';
import { 
  X, 
  MessageCircle, 
  FileText, 
  BarChart3, 
  Shield, 
  Workflow, 
  Globe, 
  Brain, 
  Network, 
  Zap, 
  User, 
  Settings,
  HelpCircle,
  LogOut,
  ChevronRight
} from 'lucide-react';

interface MobileNavigationProps {
  isOpen: boolean;
  onClose: () => void;
  currentView: string;
  onViewChange: (view: string) => void;
  user?: any;
}

export const MobileNavigation: React.FC<MobileNavigationProps> = ({
  isOpen,
  onClose,
  currentView,
  onViewChange,
  user
}) => {
  const navItems = [
    { id: 'chat', label: 'Enhanced Chat', icon: Brain, view: 'chat', color: 'text-purple-400' },
    { id: 'documents', label: 'Smart Documents', icon: Network, view: 'documents', color: 'text-emerald-400' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, view: 'analytics', color: 'text-blue-400' },
    { id: 'security', label: 'Security', icon: Shield, view: 'security', color: 'text-red-400' },
    { id: 'workflows', label: 'Workflows', icon: Workflow, view: 'workflows', color: 'text-yellow-400' },
    { id: 'integrations', label: 'Integrations', icon: Globe, view: 'integrations', color: 'text-indigo-400' },
  ];

  const handleNavItemClick = (view: string) => {
    onViewChange(view);
    onClose();
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={onClose}
        />
      )}

      {/* Navigation Panel */}
      <div className={`
        fixed left-0 top-0 h-full w-80 max-w-[85vw] bg-gray-800 border-r border-gray-700 
        transform transition-transform duration-300 ease-in-out z-50 safe-area-inset-left
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Brain className="text-purple-400" size={24} />
            <div>
              <h2 className="text-lg font-semibold">AI Scholar</h2>
              <p className="text-xs text-gray-400">Enterprise RAG</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-3 hover:bg-gray-700 active:bg-gray-600 active:scale-95 rounded-lg transition-all duration-200 touch-manipulation min-w-touch-target min-h-touch-target flex items-center justify-center tap-highlight-none"
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        {/* User Profile */}
        {user && (
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center space-x-3 p-3 bg-gray-700/50 rounded-lg">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-emerald-600 rounded-full flex items-center justify-center">
                <User size={24} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-white font-medium truncate">{user.name}</div>
                <div className="text-gray-400 text-sm capitalize">{user.role}</div>
                <div className="text-xs text-emerald-400">Online</div>
              </div>
              <ChevronRight size={16} className="text-gray-400" />
            </div>
          </div>
        )}
        
        {/* Navigation Items */}
        <nav className="p-4 space-y-1 flex-1 overflow-y-auto">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleNavItemClick(item.view)}
              className={`
                w-full flex items-center space-x-3 px-4 py-4 rounded-lg transition-all duration-200 touch-manipulation min-h-touch-target tap-highlight-none
                ${currentView === item.view 
                  ? 'bg-gradient-to-r from-purple-600 to-emerald-600 text-white shadow-lg scale-[1.02]' 
                  : 'hover:bg-gray-700 active:bg-gray-600 active:scale-98 text-gray-300'
                }
              `}
            >
              <item.icon size={20} className={currentView === item.view ? 'text-white' : item.color} />
              <span className="font-medium">{item.label}</span>
              {currentView === item.view && (
                <div className="ml-auto w-2 h-2 bg-white rounded-full" />
              )}
            </button>
          ))}
        </nav>

        {/* Enhanced Features Info */}
        <div className="p-4 border-t border-gray-700">
          <div className="bg-gray-700/30 rounded-lg p-3 mb-3">
            <div className="text-purple-300 font-medium mb-2 flex items-center space-x-2">
              <Zap size={14} />
              <span className="text-sm">Enterprise Features</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
              <div className="flex items-center space-x-1">
                <Brain size={10} className="text-purple-400" />
                <span>Multi-Modal</span>
              </div>
              <div className="flex items-center space-x-1">
                <Network size={10} className="text-emerald-400" />
                <span>Hybrid Search</span>
              </div>
              <div className="flex items-center space-x-1">
                <Shield size={10} className="text-blue-400" />
                <span>Security</span>
              </div>
              <div className="flex items-center space-x-1">
                <BarChart3 size={10} className="text-yellow-400" />
                <span>Analytics</span>
              </div>
            </div>
          </div>

          {/* Bottom Actions */}
          <div className="space-y-2">
            <button className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-700 active:bg-gray-600 active:scale-98 text-gray-300 transition-all duration-200 touch-manipulation min-h-touch-target tap-highlight-none">
              <Settings size={18} />
              <span className="text-responsive">Settings</span>
            </button>
            <button className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-700 active:bg-gray-600 active:scale-98 text-gray-300 transition-all duration-200 touch-manipulation min-h-touch-target tap-highlight-none">
              <HelpCircle size={18} />
              <span className="text-responsive">Help & Support</span>
            </button>
            {user && (
              <button className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-red-600 active:bg-red-700 active:scale-98 text-red-400 hover:text-white transition-all duration-200 touch-manipulation min-h-touch-target tap-highlight-none">
                <LogOut size={18} />
                <span className="text-responsive">Sign Out</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
};