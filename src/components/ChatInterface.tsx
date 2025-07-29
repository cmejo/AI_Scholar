import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Loader2 } from 'lucide-react';
import { useChat } from '../contexts/ChatContext';
import { useDocument } from '../contexts/DocumentContext';

export const ChatInterface: React.FC = () => {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { currentConversation, sendMessage } = useChat();
  const { documents } = useDocument();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setIsTyping(true);

    try {
      await sendMessage(userMessage);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsTyping(false);
    }
  };

  const messages = currentConversation?.messages || [];

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Bot size={48} className="mb-4 text-gray-600" />
            <h3 className="text-xl font-semibold mb-2">Welcome to AI Scholar</h3>
            <p className="text-center max-w-md">
              I'm your AI assistant with access to your documents. Ask me anything about your uploaded content!
            </p>
            {documents.length > 0 && (
              <div className="mt-4 text-sm">
                <p className="mb-2">Available documents:</p>
                <div className="flex flex-wrap gap-2">
                  {documents.slice(0, 3).map((doc) => (
                    <span key={doc.id} className="bg-gray-800 px-2 py-1 rounded text-xs">
                      {doc.name}
                    </span>
                  ))}
                  {documents.length > 3 && (
                    <span className="text-gray-400 text-xs">
                      +{documents.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`flex max-w-[80%] ${
                    message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  } items-start space-x-2`}
                >
                  <div className={`
                    w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                    ${message.role === 'user' 
                      ? 'bg-blue-600 ml-2' 
                      : 'bg-emerald-600 mr-2'
                    }
                  `}>
                    {message.role === 'user' ? (
                      <User size={16} />
                    ) : (
                      <Bot size={16} />
                    )}
                  </div>
                  
                  <div className={`
                    px-4 py-2 rounded-2xl
                    ${message.role === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-800 text-gray-100'
                    }
                  `}>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-600">
                        <div className="flex items-center space-x-1 text-xs text-gray-400 mb-1">
                          <FileText size={12} />
                          <span>Sources:</span>
                        </div>
                        {message.sources.map((source, idx) => (
                          <div key={idx} className="text-xs text-gray-300 mb-1">
                            📄 {source.document} (p. {source.page})
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-2">
                  <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center">
                    <Bot size={16} />
                  </div>
                  <div className="bg-gray-800 px-4 py-2 rounded-2xl">
                    <div className="flex items-center space-x-1">
                      <Loader2 size={16} className="animate-spin" />
                      <span className="text-sm text-gray-400">Thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-700 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything about your documents..."
              className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isTyping}
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </form>
        
        <div className="mt-2 text-xs text-gray-500 text-center">
          AI Scholar can make mistakes. Please verify important information.
        </div>
      </div>
    </div>
  );
};