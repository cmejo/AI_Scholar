import React from 'react';
import { X, MessageCircle, FileText, BarChart3, Shield, Workflow, Globe, Brain, Network, Zap, Mic, MicOff, User, Settings } from 'lucide-react';
import { useEnhancedChat } from '../contexts/EnhancedChatContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentView: string;
  onViewChange: (view: any) => void;
  user?: any;
  voiceEnabled: boolean;
  onToggleVoice: (enabled: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  isOpen, 
  onClose, 
  currentView, 
  onViewChange,
  user,
  voiceEnabled,
  onToggleVoice
}) => {
  const { conversations, currentConversation, createNewConversation, switchConversation } = useEnhancedChat();

  const navItems = [
    { id: 'chat', label: 'Enhanced Chat', icon: Brain, view: 'chat' },
    { id: 'documents', label: 'Smart Documents', icon: Network, view: 'documents' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, view: 'analytics' },
    { id: 'security', label: 'Security', icon: Shield, view: 'security' },
    { id: 'workflows', label: 'Workflows', icon: Workflow, view: 'workflows' },
    { id: 'integrations', label: 'Integrations', icon: Globe, view: 'integrations' },
  ];

  return (
    <>
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      <div className={`
        fixed lg:relative left-0 top-0 h-full w-80 bg-gray-800 border-r border-gray-700 
        transform transition-transform duration-300 ease-in-out z-50
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Brain className="text-purple-400" size={20} />
            <h2 className="text-lg font-semibold">Enterprise RAG</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors lg:hidden"
          >
            <X size={18} />
          </button>
        </div>

        {/* User Profile */}
        {user && (
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-emerald-600 rounded-full flex items-center justify-center">
                <User size={20} />
              </div>
              <div>
                <div className="text-white font-medium">{user.name}</div>
                <div className="text-gray-400 text-sm capitalize">{user.role}</div>
              </div>
            </div>
          </div>
        )}
        
        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                onViewChange(item.view);
                onClose();
              }}
              className={`
                w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors
                ${currentView === item.view 
                  ? 'bg-gradient-to-r from-purple-600 to-emerald-600 text-white' 
                  : 'hover:bg-gray-700 text-gray-300'
                }
              `}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Voice Control */}
        <div className="p-4 border-t border-gray-700">
          <button
            onClick={() => onToggleVoice(!voiceEnabled)}
            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
              voiceEnabled 
                ? 'bg-blue-600 text-white' 
                : 'hover:bg-gray-700 text-gray-300'
            }`}
          >
            {voiceEnabled ? <Mic size={18} /> : <MicOff size={18} />}
            <span>Voice Assistant</span>
          </button>
        </div>
        
        {/* Conversations (only for chat view) */}
        {currentView === 'chat' && (
          <div className="p-4 border-t border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-400">Enhanced Conversations</h3>
              <button
                onClick={createNewConversation}
                className="text-xs bg-gradient-to-r from-purple-600 to-emerald-600 hover:from-purple-700 hover:to-emerald-700 px-2 py-1 rounded transition-colors"
              >
                New
              </button>
            </div>
            
            <div className="space-y-1 max-h-60 overflow-y-auto">
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => switchConversation(conversation.id)}
                  className={`
                    w-full text-left px-3 py-2 rounded-lg text-sm transition-colors
                    ${currentConversation?.id === conversation.id 
                      ? 'bg-gray-700 text-white border border-purple-500' 
                      : 'hover:bg-gray-700 text-gray-300'
                    }
                  `}
                >
                  <div className="truncate">{conversation.title}</div>
                  <div className="text-xs text-gray-500 mt-1 grid grid-cols-2 gap-1">
                    <span>{conversation.messages.length} messages</span>
                    {conversation.avgRelevanceScore > 0 && (
                      <span className="text-emerald-400">
                        {(conversation.avgRelevanceScore * 100).toFixed(0)}% rel
                      </span>
                    )}
                    {conversation.avgReasoningSteps > 0 && (
                      <span className="text-purple-400">
                        {conversation.avgReasoningSteps.toFixed(1)} steps
                      </span>
                    )}
                    {conversation.avgConfidence > 0 && (
                      <span className="text-blue-400">
                        {(conversation.avgConfidence * 100).toFixed(0)}% conf
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Enhanced Features Info */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-gray-800/50 rounded-lg p-3 text-xs">
            <div className="text-purple-300 font-medium mb-2 flex items-center space-x-1">
              <Zap size={12} />
              <span>Enterprise Features:</span>
            </div>
            <div className="space-y-1 text-gray-400">
              <div className="flex items-center space-x-2">
                <Brain size={10} className="text-purple-400" />
                <span>Multi-Modal Processing</span>
              </div>
              <div className="flex items-center space-x-2">
                <Network size={10} className="text-emerald-400" />
                <span>Hybrid Search</span>
              </div>
              <div className="flex items-center space-x-2">
                <Shield size={10} className="text-blue-400" />
                <span>Enterprise Security</span>
              </div>
              <div className="flex items-center space-x-2">
                <BarChart3 size={10} className="text-yellow-400" />
                <span>Advanced Analytics</span>
              </div>
              <div className="flex items-center space-x-2">
                <Globe size={10} className="text-indigo-400" />
                <span>External Integrations</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};