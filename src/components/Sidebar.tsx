import React from 'react';
import { X, MessageCircle, FileText, BarChart3, Shield, Workflow, Globe, Brain, Network, Zap, Mic, MicOff, User, Settings } from 'lucide-react';
import { useEnhancedChat } from '../contexts/EnhancedChatContext';
import { accessibilityService } from '../services/accessibilityService';

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
          aria-hidden="true"
        />
      )}
      
      <aside 
        id="main-sidebar"
        className={`
          fixed lg:relative left-0 top-0 h-full w-80 bg-gray-800 border-r border-gray-700 
          transform transition-transform duration-300 ease-in-out z-50
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
        role="complementary"
        aria-label="Main navigation sidebar"
        aria-hidden={!isOpen ? "true" : "false"}
      >
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Brain className="text-purple-400" size={20} aria-hidden="true" />
            <h2 className="text-lg font-semibold">Enterprise RAG</h2>
          </div>
          <button
            onClick={() => {
              onClose();
              accessibilityService.announce('Sidebar closed', 'polite');
            }}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors lg:hidden focus-ring"
            aria-label="Close sidebar navigation"
            title="Close sidebar (Escape key)"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        {/* User Profile */}
        {user && (
          <section className="p-4 border-b border-gray-700" aria-labelledby="user-profile-heading">
            <h3 id="user-profile-heading" className="sr-only">User Profile</h3>
            <div className="flex items-center space-x-3" role="group" aria-label="Current user information">
              <div 
                className="w-10 h-10 bg-gradient-to-br from-purple-600 to-emerald-600 rounded-full flex items-center justify-center"
                aria-hidden="true"
              >
                <User size={20} />
              </div>
              <div>
                <div className="text-white font-medium" aria-label={`User: ${user.name}`}>
                  {user.name}
                </div>
                <div className="text-gray-400 text-sm capitalize" aria-label={`Role: ${user.role}`}>
                  {user.role}
                </div>
              </div>
            </div>
          </section>
        )}
        
        {/* Navigation */}
        <nav className="p-4 space-y-2" role="navigation" aria-label="Main navigation">
          {navItems.map((item, index) => (
            <button
              key={item.id}
              onClick={() => {
                onViewChange(item.view);
                onClose();
                accessibilityService.announce(`Navigated to ${item.label}`, 'polite');
              }}
              className={`
                w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors focus-ring
                ${currentView === item.view 
                  ? 'bg-gradient-to-r from-purple-600 to-emerald-600 text-white' 
                  : 'hover:bg-gray-700 text-gray-300'
                }
              `}
              aria-current={currentView === item.view ? 'page' : undefined}
              aria-label={`Navigate to ${item.label}. Shortcut: Alt+${index + 1}`}
              title={`${item.label} - Alt+${index + 1}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onViewChange(item.view);
                  onClose();
                  accessibilityService.announce(`Navigated to ${item.label}`, 'polite');
                }
              }}
            >
              <item.icon size={18} aria-hidden="true" />
              <span>{item.label}</span>
              {currentView === item.view && (
                <span className="sr-only">Current page</span>
              )}
            </button>
          ))}
        </nav>

        {/* Voice Control */}
        <section className="p-4 border-t border-gray-700" aria-labelledby="voice-control-heading">
          <h3 id="voice-control-heading" className="sr-only">Voice Control</h3>
          <button
            onClick={() => {
              onToggleVoice(!voiceEnabled);
              accessibilityService.announce(
                `Voice Assistant ${!voiceEnabled ? 'enabled' : 'disabled'}`, 
                'assertive'
              );
            }}
            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors focus-ring ${
              voiceEnabled 
                ? 'bg-blue-600 text-white' 
                : 'hover:bg-gray-700 text-gray-300'
            }`}
            aria-pressed={voiceEnabled}
            aria-label={`Voice Assistant ${voiceEnabled ? 'enabled' : 'disabled'}. Click to ${voiceEnabled ? 'disable' : 'enable'}`}
            title={`Voice Assistant - ${voiceEnabled ? 'Click to disable' : 'Click to enable'}`}
          >
            {voiceEnabled ? <Mic size={18} aria-hidden="true" /> : <MicOff size={18} aria-hidden="true" />}
            <span>Voice Assistant</span>
            <span className="sr-only">{voiceEnabled ? 'Currently enabled' : 'Currently disabled'}</span>
          </button>
        </section>
        
        {/* Conversations (only for chat view) */}
        {currentView === 'chat' && (
          <section className="p-4 border-t border-gray-700" aria-labelledby="conversations-heading">
            <div className="flex items-center justify-between mb-3">
              <h3 id="conversations-heading" className="text-sm font-medium text-gray-400">
                Enhanced Conversations
              </h3>
              <button
                onClick={() => {
                  createNewConversation();
                  accessibilityService.announce('New conversation created', 'polite');
                }}
                className="text-xs bg-gradient-to-r from-purple-600 to-emerald-600 hover:from-purple-700 hover:to-emerald-700 px-2 py-1 rounded transition-colors focus-ring"
                aria-label="Create new conversation"
                title="Start a new conversation"
              >
                New
              </button>
            </div>
            
            <div 
              className="space-y-1 max-h-60 overflow-y-auto custom-scrollbar"
              role="list"
              aria-label="Conversation history"
            >
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => {
                    switchConversation(conversation.id);
                    accessibilityService.announce(`Switched to conversation: ${conversation.title}`, 'polite');
                  }}
                  className={`
                    w-full text-left px-3 py-2 rounded-lg text-sm transition-colors focus-ring
                    ${currentConversation?.id === conversation.id 
                      ? 'bg-gray-700 text-white border border-purple-500' 
                      : 'hover:bg-gray-700 text-gray-300'
                    }
                  `}
                  role="listitem"
                  aria-current={currentConversation?.id === conversation.id ? 'true' : undefined}
                  aria-label={`Switch to conversation: ${conversation.title}. ${conversation.messages.length} messages. ${
                    conversation.avgRelevanceScore > 0 ? `${(conversation.avgRelevanceScore * 100).toFixed(0)}% relevance. ` : ''
                  }${
                    conversation.avgConfidence > 0 ? `${(conversation.avgConfidence * 100).toFixed(0)}% confidence.` : ''
                  }`}
                  title={`${conversation.title} - ${conversation.messages.length} messages`}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      switchConversation(conversation.id);
                      accessibilityService.announce(`Switched to conversation: ${conversation.title}`, 'polite');
                    }
                  }}
                >
                  <div className="truncate">{conversation.title}</div>
                  {currentConversation?.id === conversation.id && (
                    <span className="sr-only">Current conversation</span>
                  )}
                  <div className="text-xs text-gray-500 mt-1 grid grid-cols-2 gap-1" aria-hidden="true">
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
          </section>
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
      </aside>
    </>
  );
};