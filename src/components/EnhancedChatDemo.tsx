import React from 'react';
import { EnhancedChatInterface } from './EnhancedChatInterface';
import { EnhancedChatProvider } from '../contexts/EnhancedChatContext';
import { DocumentProvider } from '../contexts/DocumentContext';

/**
 * Demo component showcasing the Enhanced Chat Interface
 * with all advanced features including:
 * - Memory-aware conversations
 * - Uncertainty visualization
 * - Chain-of-thought reasoning
 * - Feedback collection
 */
export const EnhancedChatDemo: React.FC = () => {
  return (
    <div className="h-screen bg-gray-900 text-white">
      <div className="container mx-auto h-full">
        <DocumentProvider>
          <EnhancedChatProvider>
            <div className="h-full flex flex-col">
              {/* Demo Header */}
              <div className="bg-gray-800 border-b border-gray-700 p-4">
                <h1 className="text-2xl font-bold text-center mb-2">
                  Enhanced RAG Chat Interface Demo
                </h1>
                <p className="text-gray-400 text-center text-sm">
                  Featuring memory awareness, uncertainty quantification, reasoning transparency, and feedback learning
                </p>
                
                {/* Feature Highlights */}
                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                  <div className="bg-purple-900/30 rounded p-2 text-center">
                    <div className="text-purple-400 font-medium">Memory Context</div>
                    <div className="text-gray-400">Remembers conversations</div>
                  </div>
                  <div className="bg-yellow-900/30 rounded p-2 text-center">
                    <div className="text-yellow-400 font-medium">Uncertainty</div>
                    <div className="text-gray-400">Shows confidence levels</div>
                  </div>
                  <div className="bg-green-900/30 rounded p-2 text-center">
                    <div className="text-green-400 font-medium">Reasoning</div>
                    <div className="text-gray-400">Transparent thinking</div>
                  </div>
                  <div className="bg-blue-900/30 rounded p-2 text-center">
                    <div className="text-blue-400 font-medium">Feedback</div>
                    <div className="text-gray-400">Learns from users</div>
                  </div>
                </div>
              </div>
              
              {/* Chat Interface */}
              <div className="flex-1">
                <EnhancedChatInterface />
              </div>
              
              {/* Demo Footer */}
              <div className="bg-gray-800 border-t border-gray-700 p-2 text-center text-xs text-gray-500">
                Task 10.1: Enhanced Chat Interface Components - Memory-aware conversations with reasoning transparency
              </div>
            </div>
          </EnhancedChatProvider>
        </DocumentProvider>
      </div>
    </div>
  );
};