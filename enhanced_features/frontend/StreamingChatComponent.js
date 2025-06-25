// Enhanced Streaming Chat Component for React Frontend
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';

// Streaming Chat Hook
export const useStreamingChat = (apiUrl = 'http://localhost:5000') => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [streamError, setStreamError] = useState(null);
  const [streamMetrics, setStreamMetrics] = useState(null);
  const abortControllerRef = useRef(null);
  const socketRef = useRef(null);

  // Initialize WebSocket connection
  useEffect(() => {
    socketRef.current = io(apiUrl, {
      transports: ['websocket', 'polling']
    });

    const socket = socketRef.current;

    socket.on('connect', () => {
      console.log('Connected to streaming server');
    });

    socket.on('stream_start', (data) => {
      setIsStreaming(true);
      setStreamingMessage('');
      setStreamError(null);
      setStreamMetrics({ startTime: Date.now(), model: data.model });
    });

    socket.on('stream_chunk', (data) => {
      setStreamingMessage(prev => prev + data.content);
    });

    socket.on('stream_complete', (data) => {
      setIsStreaming(false);
      setStreamMetrics(prev => ({
        ...prev,
        endTime: Date.now(),
        totalDuration: Date.now() - (prev?.startTime || Date.now())
      }));
    });

    socket.on('stream_error', (data) => {
      setIsStreaming(false);
      setStreamError(data.error);
    });

    return () => {
      socket.disconnect();
    };
  }, [apiUrl]);

  // HTTP Streaming function
  const sendStreamingMessage = useCallback(async (message, sessionId, options = {}) => {
    try {
      setIsStreaming(true);
      setStreamingMessage('');
      setStreamError(null);
      
      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController();
      
      const response = await fetch(`${apiUrl}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          model: options.model || 'llama2:7b-chat',
          system_prompt: options.systemPrompt
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop(); // Keep incomplete line in buffer
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              switch (data.type) {
                case 'start':
                  setStreamMetrics({ 
                    startTime: Date.now(), 
                    streamId: data.stream_id,
                    model: data.model 
                  });
                  break;
                  
                case 'content':
                  setStreamingMessage(prev => prev + data.content);
                  break;
                  
                case 'complete':
                  setIsStreaming(false);
                  setStreamMetrics(prev => ({
                    ...prev,
                    endTime: Date.now(),
                    totalChunks: data.total_chunks,
                    duration: data.duration,
                    tokensPerSecond: data.tokens_per_second
                  }));
                  break;
                  
                case 'error':
                  setIsStreaming(false);
                  setStreamError(data.error);
                  break;
              }
            } catch (e) {
              console.error('Error parsing stream data:', e);
            }
          }
        }
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        setIsStreaming(false);
        setStreamError(error.message);
      }
    }
  }, [apiUrl]);

  // WebSocket streaming function
  const sendWebSocketMessage = useCallback((message, sessionId, options = {}) => {
    if (socketRef.current) {
      socketRef.current.emit('stream_message', {
        message,
        session_id: sessionId,
        model: options.model || 'llama2:7b-chat',
        system_prompt: options.systemPrompt
      });
    }
  }, []);

  // Cancel streaming
  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsStreaming(false);
  }, []);

  // Join chat session (for WebSocket)
  const joinChatSession = useCallback((sessionId) => {
    if (socketRef.current) {
      socketRef.current.emit('join_chat', { session_id: sessionId });
    }
  }, []);

  return {
    isStreaming,
    streamingMessage,
    streamError,
    streamMetrics,
    sendStreamingMessage,
    sendWebSocketMessage,
    cancelStream,
    joinChatSession
  };
};

// Enhanced Chat Message Component with Streaming
export const StreamingChatMessage = ({ 
  message, 
  isStreaming = false, 
  onRetry = null,
  showMetrics = false,
  metrics = null 
}) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  // Typewriter effect for streaming messages
  useEffect(() => {
    if (isStreaming && message) {
      const timer = setInterval(() => {
        setCurrentIndex(prev => {
          if (prev < message.length) {
            setDisplayedText(message.slice(0, prev + 1));
            return prev + 1;
          } else {
            clearInterval(timer);
            return prev;
          }
        });
      }, 20); // Adjust speed as needed

      return () => clearInterval(timer);
    } else {
      setDisplayedText(message);
      setCurrentIndex(message.length);
    }
  }, [message, isStreaming]);

  return (
    <div className="streaming-chat-message">
      <div className="message-content">
        {displayedText}
        {isStreaming && (
          <span className="streaming-cursor">▊</span>
        )}
      </div>
      
      {showMetrics && metrics && (
        <div className="stream-metrics">
          <small className="text-gray-500">
            {metrics.tokensPerSecond && (
              <span>⚡ {metrics.tokensPerSecond.toFixed(1)} tokens/sec</span>
            )}
            {metrics.duration && (
              <span className="ml-2">⏱️ {metrics.duration.toFixed(2)}s</span>
            )}
          </small>
        </div>
      )}
      
      {onRetry && (
        <button 
          onClick={onRetry}
          className="retry-button mt-2 text-blue-500 hover:text-blue-700"
        >
          🔄 Retry
        </button>
      )}
    </div>
  );
};

// Enhanced Chat Container with Streaming
export const EnhancedStreamingChatContainer = ({ sessionId, onSessionChange }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedModel, setSelectedModel] = useState('llama2:7b-chat');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef(null);

  const {
    isStreaming,
    streamingMessage,
    streamError,
    streamMetrics,
    sendStreamingMessage,
    sendWebSocketMessage,
    cancelStream,
    joinChatSession
  } = useStreamingChat();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  // Join session when sessionId changes
  useEffect(() => {
    if (sessionId) {
      joinChatSession(sessionId);
      loadSessionMessages(sessionId);
    }
  }, [sessionId, joinChatSession]);

  const loadSessionMessages = async (sessionId) => {
    try {
      const response = await fetch(`/api/chat/sessions/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isStreaming) return;

    const userMessage = {
      id: Date.now(),
      message_type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');

    // Add placeholder for AI response
    const aiMessageId = Date.now() + 1;
    const aiMessage = {
      id: aiMessageId,
      message_type: 'bot',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true
    };

    setMessages(prev => [...prev, aiMessage]);

    try {
      // Use HTTP streaming (you can switch to WebSocket if preferred)
      await sendStreamingMessage(inputMessage, sessionId, {
        model: selectedModel,
        systemPrompt: systemPrompt
      });

      // Update the AI message with final content
      setMessages(prev => prev.map(msg => 
        msg.id === aiMessageId 
          ? { ...msg, content: streamingMessage, isStreaming: false }
          : msg
      ));

    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => prev.map(msg => 
        msg.id === aiMessageId 
          ? { ...msg, content: 'Error: Failed to get response', isStreaming: false }
          : msg
      ));
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const retryLastMessage = () => {
    const lastUserMessage = [...messages].reverse().find(m => m.message_type === 'user');
    if (lastUserMessage) {
      setInputMessage(lastUserMessage.content);
    }
  };

  return (
    <div className="enhanced-streaming-chat-container flex flex-col h-full">
      {/* Chat Header with Settings */}
      <div className="chat-header bg-white border-b p-4 flex justify-between items-center">
        <h2 className="text-lg font-semibold">AI Scholar Chat</h2>
        <div className="flex items-center space-x-2">
          {isStreaming && (
            <button 
              onClick={cancelStream}
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
            >
              ⏹️ Stop
            </button>
          )}
          <button 
            onClick={() => setShowSettings(!showSettings)}
            className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            ⚙️ Settings
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="settings-panel bg-gray-50 p-4 border-b">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Model</label>
              <select 
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full p-2 border rounded"
              >
                <option value="llama2:7b-chat">Llama 2 7B Chat</option>
                <option value="mistral:7b-instruct">Mistral 7B Instruct</option>
                <option value="codellama:7b-instruct">CodeLlama 7B</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">System Prompt</label>
              <input 
                type="text"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="Optional system prompt..."
                className="w-full p-2 border rounded"
              />
            </div>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="messages-area flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div 
            key={message.id}
            className={`message ${message.message_type === 'user' ? 'user-message' : 'ai-message'}`}
          >
            <div className={`message-bubble ${
              message.message_type === 'user' 
                ? 'bg-blue-500 text-white ml-auto' 
                : 'bg-gray-200 text-gray-800'
            } p-3 rounded-lg max-w-3xl`}>
              <StreamingChatMessage 
                message={message.content}
                isStreaming={message.isStreaming}
                onRetry={message.message_type === 'bot' ? retryLastMessage : null}
                showMetrics={message.message_type === 'bot'}
                metrics={streamMetrics}
              />
            </div>
            <div className="message-timestamp text-xs text-gray-500 mt-1">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}

        {/* Current streaming message */}
        {isStreaming && streamingMessage && (
          <div className="message ai-message">
            <div className="message-bubble bg-gray-200 text-gray-800 p-3 rounded-lg max-w-3xl">
              <StreamingChatMessage 
                message={streamingMessage}
                isStreaming={true}
                showMetrics={true}
                metrics={streamMetrics}
              />
            </div>
          </div>
        )}

        {/* Stream error */}
        {streamError && (
          <div className="error-message bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <strong>Error:</strong> {streamError}
            <button 
              onClick={retryLastMessage}
              className="ml-2 text-red-500 hover:text-red-700"
            >
              🔄 Retry
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area bg-white border-t p-4">
        <div className="flex space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            className="flex-1 p-3 border rounded-lg resize-none"
            rows="2"
            disabled={isStreaming}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isStreaming}
            className={`px-6 py-3 rounded-lg font-medium ${
              !inputMessage.trim() || isStreaming
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {isStreaming ? '⏳' : '📤'}
          </button>
        </div>
        
        {/* Streaming status */}
        {isStreaming && (
          <div className="mt-2 text-sm text-gray-600 flex items-center">
            <div className="animate-pulse mr-2">🤖</div>
            AI is thinking...
            {streamMetrics?.tokensPerSecond && (
              <span className="ml-2">
                ({streamMetrics.tokensPerSecond.toFixed(1)} tokens/sec)
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// CSS for streaming effects
export const streamingStyles = `
.streaming-cursor {
  animation: blink 1s infinite;
  color: #3b82f6;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.message-bubble {
  word-wrap: break-word;
  transition: all 0.2s ease-in-out;
}

.user-message {
  display: flex;
  justify-content: flex-end;
}

.ai-message {
  display: flex;
  justify-content: flex-start;
}

.streaming-chat-message {
  position: relative;
}

.stream-metrics {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e5e7eb;
}

.retry-button {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  transition: color 0.2s ease-in-out;
}

.settings-panel {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.enhanced-streaming-chat-container {
  height: 100vh;
  max-height: 100vh;
}

.messages-area {
  scroll-behavior: smooth;
}

.input-area textarea {
  transition: border-color 0.2s ease-in-out;
}

.input-area textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
`;

export default EnhancedStreamingChatContainer;