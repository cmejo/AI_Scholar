import React from 'react';
import { ExternalLink, Book, MessageCircle, Settings, Search, FileText, BarChart3, Shield } from 'lucide-react';

interface HelpProps {
  onClose: () => void;
}

export const Help: React.FC<HelpProps> = ({ onClose }) => {
  return (
    <div className="bg-gray-800 text-white p-6 rounded-lg max-w-4xl mx-auto max-h-[80vh] overflow-y-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-purple-400">Help & Documentation</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white text-xl"
          aria-label="Close help"
        >
          ×
        </button>
      </div>

      <div className="space-y-6">
        {/* Quick Start */}
        <section>
          <h3 className="text-xl font-semibold mb-3 text-purple-300">🚀 Quick Start</h3>
          <div className="bg-gray-700 p-4 rounded-lg">
            <p className="mb-3">Welcome to AI Scholar! Here's how to get started:</p>
            <ol className="list-decimal list-inside space-y-2 text-gray-300">
              <li>Create an account or sign in to access all features</li>
              <li>Upload documents to build your research corpus</li>
              <li>Use the RAG system to query your documents with AI</li>
              <li>Explore workflows and integrations for automation</li>
              <li>Analyze your research with built-in analytics</li>
            </ol>
          </div>
        </section>

        {/* Features Overview */}
        <section>
          <h3 className="text-xl font-semibold mb-3 text-purple-300">✨ Features Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center mb-2">
                <MessageCircle className="w-5 h-5 text-blue-400 mr-2" />
                <h4 className="font-semibold">AI Chat Assistant</h4>
              </div>
              <p className="text-gray-300 text-sm">
                Intelligent conversation with multiple modes including chain-of-thought reasoning and fact-checking.
              </p>
            </div>

            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center mb-2">
                <Search className="w-5 h-5 text-green-400 mr-2" />
                <h4 className="font-semibold">RAG System</h4>
              </div>
              <p className="text-gray-300 text-sm">
                Query your document corpus using advanced retrieval-augmented generation technology.
              </p>
            </div>

            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center mb-2">
                <FileText className="w-5 h-5 text-yellow-400 mr-2" />
                <h4 className="font-semibold">Document Management</h4>
              </div>
              <p className="text-gray-300 text-sm">
                Upload, organize, and analyze research documents with AI-powered insights.
              </p>
            </div>

            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center mb-2">
                <BarChart3 className="w-5 h-5 text-purple-400 mr-2" />
                <h4 className="font-semibold">Analytics Dashboard</h4>
              </div>
              <p className="text-gray-300 text-sm">
                Track usage patterns, performance metrics, and research insights.
              </p>
            </div>

            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center mb-2">
                <Settings className="w-5 h-5 text-orange-400 mr-2" />
                <h4 className="font-semibold">Workflow Automation</h4>
              </div>
              <p className="text-gray-300 text-sm">
                Create and manage automated research workflows with AI integration.
              </p>
            </div>

            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center mb-2">
                <Shield className="w-5 h-5 text-red-400 mr-2" />
                <h4 className="font-semibold">Security Dashboard</h4>
              </div>
              <p className="text-gray-300 text-sm">
                Monitor security, manage access controls, and audit system activity.
              </p>
            </div>
          </div>
        </section>

        {/* Keyboard Shortcuts */}
        <section>
          <h3 className="text-xl font-semibold mb-3 text-purple-300">⌨️ Keyboard Shortcuts</h3>
          <div className="bg-gray-700 p-4 rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p><kbd className="bg-gray-600 px-2 py-1 rounded">Ctrl + M</kbd> - Toggle voice features</p>
                <p><kbd className="bg-gray-600 px-2 py-1 rounded">Space</kbd> - Start voice input</p>
                <p><kbd className="bg-gray-600 px-2 py-1 rounded">Enter</kbd> - Send message</p>
              </div>
              <div>
                <p><kbd className="bg-gray-600 px-2 py-1 rounded">Shift + Enter</kbd> - New line</p>
                <p><kbd className="bg-gray-600 px-2 py-1 rounded">Ctrl + /</kbd> - Show shortcuts</p>
                <p><kbd className="bg-gray-600 px-2 py-1 rounded">Esc</kbd> - Close modals</p>
              </div>
            </div>
          </div>
        </section>

        {/* Voice Features */}
        <section>
          <h3 className="text-xl font-semibold mb-3 text-purple-300">🎤 Voice Features</h3>
          <div className="bg-gray-700 p-4 rounded-lg">
            <p className="mb-3">AI Scholar includes advanced voice capabilities:</p>
            <ul className="list-disc list-inside space-y-1 text-gray-300">
              <li>Voice-to-text input for hands-free interaction</li>
              <li>Text-to-speech for accessibility</li>
              <li>Multiple language support</li>
              <li>Customizable voice settings</li>
              <li>Auto-listening mode for continuous interaction</li>
            </ul>
          </div>
        </section>

        {/* Troubleshooting */}
        <section>
          <h3 className="text-xl font-semibold mb-3 text-purple-300">🔧 Troubleshooting</h3>
          <div className="bg-gray-700 p-4 rounded-lg">
            <div className="space-y-3">
              <div>
                <h4 className="font-semibold text-yellow-400">Voice not working?</h4>
                <p className="text-gray-300 text-sm">Check browser permissions and ensure microphone access is enabled.</p>
              </div>
              <div>
                <h4 className="font-semibold text-yellow-400">Documents not uploading?</h4>
                <p className="text-gray-300 text-sm">Verify file format (PDF, DOCX, TXT) and size limits (max 10MB per file).</p>
              </div>
              <div>
                <h4 className="font-semibold text-yellow-400">RAG queries slow?</h4>
                <p className="text-gray-300 text-sm">Large document collections may take longer to process. Consider optimizing your corpus.</p>
              </div>
            </div>
          </div>
        </section>

        {/* GitHub Link */}
        <section>
          <h3 className="text-xl font-semibold mb-3 text-purple-300">📚 Additional Resources</h3>
          <div className="bg-gray-700 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold mb-1">Source Code & Documentation</h4>
                <p className="text-gray-300 text-sm">
                  Visit our GitHub repository for detailed documentation, API references, and contribution guidelines.
                </p>
              </div>
              <a
                href="https://github.com/cmejo/AI_Scholar"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <Book className="w-4 h-4 mr-2" />
                GitHub
                <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};