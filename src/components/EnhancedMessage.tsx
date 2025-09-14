import React, { useState } from 'react';
import { User, Bot, Mic, Brain, CheckCircle } from 'lucide-react';
import { Message } from '../types/chat';
import SpeakerButton from './SpeakerButton';
import ThoughtProcess from './ThoughtProcess';
import Citation from './Citation';
import '../styles/animations.css';

interface EnhancedMessageProps {
  message: Message;
  showReasoning: boolean;
  showCitations: boolean;
  className?: string;
}

export const EnhancedMessage: React.FC<EnhancedMessageProps> = ({
  message,
  showReasoning,
  showCitations,
  className = '',
}) => {
  const [reasoningExpanded, setReasoningExpanded] = useState(false);
  const isUser = message.sender === 'user';
  const isVoiceMessage = message.type === 'voice';
  const hasReasoning = message.metadata?.reasoning && message.metadata.reasoning.length > 0;
  const hasCitations = message.metadata?.sources && message.metadata.sources.length > 0;

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getModeIndicator = () => {
    if (!message.metadata?.mode) return null;

    const modeConfig = {
      chain_of_thought: { icon: Brain, color: 'text-purple-400', label: 'Chain of Thought' },
      fact_checked: { icon: CheckCircle, color: 'text-green-400', label: 'Fact Checked' },
      voice: { icon: Mic, color: 'text-blue-400', label: 'Voice' },
    };

    const config = modeConfig[message.metadata.mode as keyof typeof modeConfig];
    if (!config) return null;

    const IconComponent = config.icon;
    return (
      <div className="flex items-center space-x-1 text-xs" title={config.label}>
        <IconComponent className={`w-3 h-3 ${config.color}`} />
        <span className={config.color}>{config.label}</span>
      </div>
    );
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} ${className} ${
      isUser ? 'message-user' : 'message-assistant'
    }`}>
      <div className={`max-w-xs lg:max-w-2xl ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Message Bubble */}
        <div
          className={`px-4 py-3 rounded-lg transition-all duration-200 hover:shadow-lg ${
            isUser
              ? 'bg-purple-600 text-white hover:bg-purple-700'
              : 'bg-gray-700 text-gray-100 hover:bg-gray-600'
          } ${isVoiceMessage ? 'border-l-4 border-blue-400 voice-focus-ring' : ''}`}
        >
          {/* Message Header */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              {isUser ? (
                <User className="w-4 h-4" />
              ) : (
                <Bot className="w-4 h-4" />
              )}
              <span className="text-xs font-medium">
                {isUser ? 'You' : 'AI Scholar'}
              </span>
              {isVoiceMessage && (
                <Mic className="w-3 h-3 text-blue-300" title="Voice message" />
              )}
            </div>

            <div className="flex items-center space-x-2">
              {getModeIndicator()}
              <SpeakerButton 
                text={message.content} 
                messageId={message.id}
                size="sm"
              />
            </div>
          </div>

          {/* Enhanced Voice Transcription Notice */}
          {isVoiceMessage && message.metadata?.voiceTranscription && (
            <div className="mb-2 p-3 bg-gradient-to-r from-blue-900/40 to-purple-900/40 border border-blue-700/50 rounded-lg text-xs animate-bounce-in">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <Mic className="w-4 h-4 text-blue-300 animate-pulse-recording" />
                    <div className="absolute -top-1 -right-1 w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                  </div>
                  <span className="text-blue-300 font-medium">Voice Input</span>
                </div>
                {message.metadata.confidence && (
                  <div className="flex items-center space-x-2">
                    <div className="w-12 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-400 to-blue-300 confidence-fill"
                        style={{ width: `${message.metadata.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-blue-400 text-xs font-medium animate-fade-in">
                      {Math.round(message.metadata.confidence * 100)}%
                    </span>
                  </div>
                )}
              </div>
              <p className="text-blue-100 italic leading-relaxed">"{message.metadata.voiceTranscription}"</p>
            </div>
          )}

          {/* Message Content */}
          <div className="prose prose-sm max-w-none">
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>

          {/* Enhanced Processing Time */}
          {message.metadata?.processingTime && (
            <div className="mt-2 flex items-center space-x-2 text-xs opacity-70 animate-fade-in">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span>Processed in {message.metadata.processingTime}ms</span>
            </div>
          )}
        </div>

        {/* Chain of Thought Reasoning */}
        {hasReasoning && showReasoning && (
          <div className="mt-3 thought-expand">
            <ThoughtProcess
              steps={message.metadata!.reasoning!}
              isExpanded={reasoningExpanded}
              onToggle={() => setReasoningExpanded(!reasoningExpanded)}
            />
          </div>
        )}

        {/* Citations */}
        {hasCitations && showCitations && (
          <div className="mt-3 animate-fade-in">
            <Citation citations={message.metadata!.sources!} />
          </div>
        )}

        {/* Timestamp */}
        <div className={`mt-1 text-xs opacity-70 ${isUser ? 'text-right' : 'text-left'}`}>
          {formatTimestamp(message.timestamp)}
        </div>
      </div>
    </div>
  );
};

export default EnhancedMessage;