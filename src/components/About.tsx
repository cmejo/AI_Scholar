import React from 'react';
import { ExternalLink, Github, Brain, Zap, Shield, Users } from 'lucide-react';

interface AboutProps {
  onClose: () => void;
}

export const About: React.FC<AboutProps> = ({ onClose }) => {
  return (
    <div className="bg-gray-800 text-white p-6 rounded-lg max-w-4xl mx-auto max-h-[80vh] overflow-y-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-purple-400">About AI Scholar</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white text-xl"
          aria-label="Close about"
        >
          ×
        </button>
      </div>

      <div className="space-y-6">
        {/* Main Description */}
        <section>
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-6 rounded-lg mb-6">
            <div className="flex items-center mb-4">
              <Brain className="w-8 h-8 text-white mr-3" />
              <h3 className="text-2xl font-bold text-white">AI Scholar</h3>
            </div>
            <p className="text-white text-lg leading-relaxed">
              AI Scholar is an advanced research assistant powered by cutting-edge RAG (Retrieval-Augmented Generation) 
              technology. Our platform combines the power of artificial intelligence with intuitive design to revolutionize 
              how researchers, academics, and professionals interact with their document collections and conduct research.
            </p>
          </div>
        </section>

        {/* Key Features */}
        <section>
          <h3 className="text-xl font-semibold mb-4 text-purple-300">🚀 Key Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center mb-3">
                <Brain className="w-6 h-6 text-purple-400 mr-2" />
                <h4 className="font-semibold">Advanced RAG Technology</h4>
              </div>
              <p className="text-gray-300 text-sm">
                State-of-the-art retrieval-augmented generation for intelligent document querying and analysis.
              </p>
            </div>

            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center mb-3">
                <Zap className="w-6 h-6 text-yellow-400 mr-2" />
                <h4 className="font-semibold">Workflow Automation</h4>
              </div>
              <p className="text-gray-300 text-sm">
                Create and manage automated research workflows with seamless AI integration capabilities.
              </p>
            </div>

            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center mb-3">
                <Shield className="w-6 h-6 text-green-400 mr-2" />
                <h4 className="font-semibold">Enterprise Security</h4>
              </div>
              <p className="text-gray-300 text-sm">
                Comprehensive security dashboard with audit trails, access controls, and threat monitoring.
              </p>
            </div>

            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center mb-3">
                <Users className="w-6 h-6 text-blue-400 mr-2" />
                <h4 className="font-semibold">Collaborative Research</h4>
              </div>
              <p className="text-gray-300 text-sm">
                Multi-user support with role-based access and collaborative research capabilities.
              </p>
            </div>
          </div>
        </section>

        {/* Technology Stack */}
        <section>
          <h3 className="text-xl font-semibold mb-4 text-purple-300">🛠️ Technology Stack</h3>
          <div className="bg-gray-700 p-4 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <h4 className="font-semibold text-blue-400 mb-2">Frontend</h4>
                <ul className="text-gray-300 space-y-1">
                  <li>React 18</li>
                  <li>TypeScript</li>
                  <li>Tailwind CSS</li>
                  <li>Vite</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-green-400 mb-2">Backend</h4>
                <ul className="text-gray-300 space-y-1">
                  <li>FastAPI</li>
                  <li>Python</li>
                  <li>PostgreSQL</li>
                  <li>Redis</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-purple-400 mb-2">AI/ML</h4>
                <ul className="text-gray-300 space-y-1">
                  <li>ChromaDB</li>
                  <li>Ollama</li>
                  <li>OpenAI API</li>
                  <li>Transformers</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-orange-400 mb-2">Infrastructure</h4>
                <ul className="text-gray-300 space-y-1">
                  <li>Docker</li>
                  <li>Nginx</li>
                  <li>Docker Compose</li>
                  <li>GitHub Actions</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Mission Statement */}
        <section>
          <h3 className="text-xl font-semibold mb-4 text-purple-300">🎯 Our Mission</h3>
          <div className="bg-gray-700 p-4 rounded-lg">
            <p className="text-gray-300 leading-relaxed mb-4">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et 
              dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip 
              ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu 
              fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt 
              mollit anim id est laborum.
            </p>
            <p className="text-gray-300 leading-relaxed">
              Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam 
              rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt 
              explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur 
              magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia 
              dolor sit amet, consectetur, adipisci velit.
            </p>
          </div>
        </section>

        {/* Version Info */}
        <section>
          <h3 className="text-xl font-semibold mb-4 text-purple-300">📋 Version Information</h3>
          <div className="bg-gray-700 p-4 rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <h4 className="font-semibold text-blue-400">Version</h4>
                <p className="text-gray-300">2.0.0</p>
              </div>
              <div>
                <h4 className="font-semibold text-green-400">Release Date</h4>
                <p className="text-gray-300">January 2025</p>
              </div>
              <div>
                <h4 className="font-semibold text-purple-400">License</h4>
                <p className="text-gray-300">MIT License</p>
              </div>
            </div>
          </div>
        </section>

        {/* GitHub Repository */}
        <section>
          <h3 className="text-xl font-semibold mb-4 text-purple-300">🔗 Open Source</h3>
          <div className="bg-gray-700 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold mb-2">GitHub Repository</h4>
                <p className="text-gray-300 text-sm mb-3">
                  AI Scholar is open source! Explore the code, contribute to development, report issues, 
                  or fork the project to create your own research assistant.
                </p>
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="bg-blue-600 px-2 py-1 rounded">⭐ Star the repo</span>
                  <span className="bg-green-600 px-2 py-1 rounded">🍴 Fork & contribute</span>
                  <span className="bg-purple-600 px-2 py-1 rounded">🐛 Report issues</span>
                </div>
              </div>
              <a
                href="https://github.com/cmejo/AI_Scholar"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center bg-gray-900 hover:bg-black text-white px-6 py-3 rounded-lg transition-colors border border-gray-600"
              >
                <Github className="w-5 h-5 mr-2" />
                View on GitHub
                <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </div>
          </div>
        </section>

        {/* Contact */}
        <section>
          <h3 className="text-xl font-semibold mb-4 text-purple-300">📧 Contact</h3>
          <div className="bg-gray-700 p-4 rounded-lg">
            <p className="text-gray-300 mb-3">
              Have questions, suggestions, or want to collaborate? We'd love to hear from you!
            </p>
            <div className="flex flex-wrap gap-4">
              <a
                href="https://github.com/cmejo/AI_Scholar/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center text-blue-400 hover:text-blue-300 transition-colors"
              >
                GitHub Issues
                <ExternalLink className="w-4 h-4 ml-1" />
              </a>
              <a
                href="https://github.com/cmejo/AI_Scholar/discussions"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center text-green-400 hover:text-green-300 transition-colors"
              >
                Discussions
                <ExternalLink className="w-4 h-4 ml-1" />
              </a>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};