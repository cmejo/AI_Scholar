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
    <main className="flex flex-col h-full" role="main" aria-label="Chat interface">
      {/* Messages Area */}
      <section 
        className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
        id="main-content"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500" role="status">
            <Bot size={48} className="mb-4 text-gray-600" aria-hidden="true" />
            <h2 className="text-xl font-semibold mb-2">Welcome to AI Scholar</h2>
            <p className="text-center max-w-md">
              I'm your AI assistant with access to your documents. Ask me anything about your uploaded content!
            </p>
            {documents.length > 0 && (
              <div className="mt-4 text-sm" role="region" aria-labelledby="available-docs-heading">
                <h3 id="available-docs-heading" className="mb-2">Available documents:</h3>
                <div className="flex flex-wrap gap-2" role="list">
                  {documents.slice(0, 3).map((doc) => (
                    <span 
                      key={doc.id} 
                      className="bg-gray-800 px-2 py-1 rounded text-xs"
                      role="listitem"
                    >
                      {doc.name}
                    </span>
                  ))}
                  {documents.length > 3 && (
                    <span className="text-gray-400 text-xs" role="listitem">
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
                role="group"
                aria-label={`${message.role === 'user' ? 'User' : 'Assistant'} message`}
              >
                <div
                  className={`flex max-w-[80%] ${
                    message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  } items-start space-x-2`}
                >
                  <div 
                    className={`
                      w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                      ${message.role === 'user' 
                        ? 'bg-blue-600 ml-2' 
                        : 'bg-emerald-600 mr-2'
                      }
                    `}
                    aria-hidden="true"
                  >
                    {message.role === 'user' ? (
                      <User size={16} />
                    ) : (
                      <Bot size={16} />
                    )}
                  </div>
                  
                  <div 
                    className={`
                      px-4 py-2 rounded-2xl
                      ${message.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-800 text-gray-100'
                      }
                    `}
                    role="article"
                    aria-label={`Message from ${message.role === 'user' ? 'user' : 'AI assistant'}`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-600" role="region" aria-labelledby={`sources-${index}`}>
                        <div className="flex items-center space-x-1 text-xs text-gray-400 mb-1">
                          <FileText size={12} aria-hidden="true" />
                          <span id={`sources-${index}`}>Sources:</span>
                        </div>
                        <ul role="list" aria-label="Source documents">
                          {message.sources.map((source, idx) => (
                            <li key={idx} className="text-xs text-gray-300 mb-1" role="listitem">
                              📄 {source.document} (p. {source.page})
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start" role="status" aria-live="polite" aria-label="AI is typing">
                <div className="flex items-start space-x-2">
                  <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center" aria-hidden="true">
                    <Bot size={16} />
                  </div>
                  <div className="bg-gray-800 px-4 py-2 rounded-2xl">
                    <div className="flex items-center space-x-1">
                      <Loader2 size={16} className="animate-spin" aria-hidden="true" />
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
      <section className="border-t border-gray-700 p-4" role="region" aria-label="Message input">
        <form onSubmit={handleSubmit} className="flex space-x-4" role="search">
          <div className="flex-1 relative">
            <label htmlFor="chat-input" className="sr-only">
              Ask a question about your documents
            </label>
            <input
              id="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything about your documents..."
              className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus-ring"
              disabled={isTyping}
              aria-describedby="chat-disclaimer"
              autoComplete="off"
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus-ring"
              aria-label="Send message"
            >
              <Send size={18} aria-hidden="true" />
            </button>
          </div>
        </form>
        
        <div id="chat-disclaimer" className="mt-2 text-xs text-gray-500 text-center" role="note">
          AI Scholar can make mistakes. Please verify important information.
        </div>
      </section>
    </main>
  );
};