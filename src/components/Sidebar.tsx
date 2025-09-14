import React from 'react';
import { 
  MessageCircle, 
  FileText, 
  BarChart3, 
  Shield, 
  Workflow, 
  Plug,
  Brain,
  X,
  User,
  LogIn,
  Settings,
  HelpCircle,
  Info
} from 'lucide-react';

type ViewType = 'chat' | 'documents' | 'analytics' | 'security' | 'workflows' | 'integrations' | 'rag' | 'profile' | 'settings' | 'help' | 'about';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  user?: { name: string; email: string } | null;
  voiceEnabled?: boolean;
  onToggleVoice?: (enabled: boolean) => void;
  onShowAuth?: () => void;
  onShowProfile?: () => void;
}

const navigationItems = [
  { id: 'chat' as ViewType, label: 'Chat', icon: MessageCircle, description: 'AI Research Assistant' },
  { id: 'rag' as ViewType, label: 'Scientific RAG', icon: Brain, description: 'Query Scientific Literature' },
  { id: 'documents' as ViewType, label: 'Documents', icon: FileText, description: 'Document Management' },
  { id: 'analytics' as ViewType, label: 'Analytics', icon: BarChart3, description: 'Usage Analytics' },
  { id: 'security' as ViewType, label: 'Security', icon: Shield, description: 'Security Dashboard' },
  { id: 'workflows' as ViewType, label: 'Workflows', icon: Workflow, description: 'Process Management' },
  { id: 'integrations' as ViewType, label: 'Integrations', icon: Plug, description: 'Third-party Services' },
];

const utilityItems = [
  { id: 'help' as ViewType, label: 'Help', icon: HelpCircle, description: 'Documentation & Support' },
  { id: 'about' as ViewType, label: 'About', icon: Info, description: 'About AI Scholar' },
];

export const Sidebar: React.FC<SidebarProps> = ({ 
  isOpen, 
  onClose, 
  currentView, 
  onViewChange, 
  user,
  voiceEnabled = false,
  onToggleVoice,
  onShowAuth,
  onShowProfile
}) => {
  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={`
        fixed lg:static inset-y-0 left-0 z-50 w-64 bg-gray-800 border-r border-gray-700 
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-gray-700 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Navigation</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white p-1 rounded-md hover:bg-gray-700 transition-colors lg:hidden"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Items */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            <div className="space-y-2">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentView === item.id;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onViewChange(item.id);
                      onClose(); // Close sidebar on mobile after selection
                    }}
                    className={`
                      w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors
                      ${isActive 
                        ? 'bg-purple-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }
                    `}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{item.label}</div>
                      <div className="text-xs opacity-75 truncate">{item.description}</div>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Utility Items */}
            <div className="pt-4 border-t border-gray-700">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-2 px-3">
                Support
              </div>
              <div className="space-y-2">
                {utilityItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = currentView === item.id;
                  
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        onViewChange(item.id);
                        onClose(); // Close sidebar on mobile after selection
                      }}
                      className={`
                        w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors
                        ${isActive 
                          ? 'bg-purple-600 text-white' 
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                        }
                      `}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium">{item.label}</div>
                        <div className="text-xs opacity-75 truncate">{item.description}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-700 space-y-3">
            {user ? (
              <div className="space-y-3">
                <div className="text-sm text-gray-400">
                  <div className="font-medium text-white">{user.name}</div>
                  <div className="truncate">{user.email}</div>
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={onShowProfile}
                    className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-white rounded-lg transition-colors text-sm"
                  >
                    <User className="w-4 h-4" />
                    <span>Profile</span>
                  </button>
                  <button 
                    onClick={() => onViewChange('settings')}
                    className="flex items-center justify-center px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-white rounded-lg transition-colors"
                  >
                    <Settings className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-sm text-gray-400">
                  <div>Guest User</div>
                  <div className="text-xs">Limited access</div>
                </div>
                
                <button
                  onClick={onShowAuth}
                  className="w-full flex items-center justify-center space-x-2 px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors text-sm"
                >
                  <LogIn className="w-4 h-4" />
                  <span>Sign In</span>
                </button>
              </div>
            )}
            
            {onToggleVoice && (
              <div className="pt-3 border-t border-gray-700">
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={voiceEnabled}
                    onChange={(e) => onToggleVoice(e.target.checked)}
                    className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-gray-300">Voice Interface</span>
                </label>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};