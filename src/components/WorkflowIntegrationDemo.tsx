/**
 * WorkflowIntegrationDemo - Demonstration of AI-powered workflow and integration features
 */
import React, { useState } from 'react';
import {
  Bot, MessageSquare, Sparkles, Zap, Workflow, Plug, Brain, Target,
  Code, Database, Cloud, Mail, Webhook, Settings, Play, Pause,
  TrendingUp, CheckCircle, AlertCircle, Clock, Users, Star
} from 'lucide-react';

export const WorkflowIntegrationDemo: React.FC = () => {
  const [activeDemo, setActiveDemo] = useState<'workflow' | 'integration' | 'chat'>('workflow');

  const workflowFeatures = [
    {
      icon: Brain,
      title: 'AI Research Pipeline',
      description: 'Automated research workflow with AI-powered analysis, summarization, and insights generation',
      tags: ['AI', 'Research', 'Automation'],
      popularity: 95
    },
    {
      icon: Code,
      title: 'Smart Document Processor',
      description: 'AI-powered document processing with OCR, classification, and intelligent extraction',
      tags: ['AI', 'OCR', 'Classification'],
      popularity: 88
    },
    {
      icon: TrendingUp,
      title: 'Conversational Analytics',
      description: 'AI-driven analytics with natural language queries and chatbot integration',
      tags: ['AI', 'Analytics', 'NLP'],
      popularity: 92
    }
  ];

  const integrationFeatures = [
    {
      icon: Bot,
      title: 'OpenAI GPT',
      description: 'Advanced AI language models for text generation, analysis, and conversation',
      provider: 'OpenAI',
      rating: 4.9,
      pricing: 'Paid'
    },
    {
      icon: MessageSquare,
      title: 'Slack AI Bot',
      description: 'AI-powered Slack integration for intelligent team communication',
      provider: 'Slack',
      rating: 4.8,
      pricing: 'Freemium'
    },
    {
      icon: Cloud,
      title: 'AWS Bedrock',
      description: 'Fully managed service for foundation models via APIs',
      provider: 'AWS',
      rating: 4.4,
      pricing: 'Paid'
    }
  ];

  const chatExamples = [
    {
      user: "Help me create a workflow for processing research documents",
      assistant: "I'll help you create an AI-powered document processing workflow! This workflow will:\n\n🤖 Use OCR to extract text from PDFs and images\n📊 Classify documents by type (research, legal, technical)\n🔍 Extract key entities and insights\n📝 Generate summaries and tag documents\n\nWould you like me to set this up for you?"
    },
    {
      user: "What AI integrations work best with research workflows?",
      assistant: "For research workflows, I recommend these AI integrations:\n\n🧠 **OpenAI GPT-4**: Text analysis, summarization, Q&A\n🔍 **Anthropic Claude**: Safe document analysis, research assistance\n📊 **Pinecone**: Vector database for semantic search\n🔗 **Zapier AI**: Workflow automation with 5000+ app connections\n\nEach offers unique strengths. Which type of research tasks are you focusing on?"
    },
    {
      user: "How do I optimize my workflow performance?",
      assistant: "I can help optimize your workflows! Here's my analysis:\n\n⚡ **Performance Tips**:\n• Use parallel processing for independent tasks\n• Implement smart caching for repeated operations\n• Add error handling and retry logic\n• Monitor execution times and bottlenecks\n\n📊 **AI Optimization**:\n• Use appropriate model sizes for tasks\n• Batch similar requests together\n• Implement result caching\n\nWould you like me to analyze your specific workflows?"
    }
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <Sparkles className="w-12 h-12 text-purple-400 mr-4" />
            <h1 className="text-4xl font-bold">AI Workflow & Integration Hub</h1>
          </div>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Experience the power of AI-driven automation with intelligent workflows and seamless integrations
          </p>
        </div>

        {/* Demo Navigation */}
        <div className="flex justify-center mb-8">
          <div className="bg-gray-800 rounded-lg p-1 flex">
            <button
              onClick={() => setActiveDemo('workflow')}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeDemo === 'workflow'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Workflow className="w-5 h-5 mr-2 inline" />
              AI Workflows
            </button>
            <button
              onClick={() => setActiveDemo('integration')}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeDemo === 'integration'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Plug className="w-5 h-5 mr-2 inline" />
              AI Integrations
            </button>
            <button
              onClick={() => setActiveDemo('chat')}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeDemo === 'chat'
                  ? 'bg-green-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <MessageSquare className="w-5 h-5 mr-2 inline" />
              Chat Integration
            </button>
          </div>
        </div>

        {/* Demo Content */}
        {activeDemo === 'workflow' && (
          <div className="space-y-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold mb-4">AI-Powered Workflow Templates</h2>
              <p className="text-gray-400">
                Pre-built templates with AI integration for intelligent automation
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {workflowFeatures.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <div key={index} className="bg-gray-800 rounded-lg p-6 hover:bg-gray-700 transition-colors">
                    <div className="flex items-center mb-4">
                      <div className="p-3 bg-purple-600/20 rounded-lg mr-4">
                        <Icon className="w-6 h-6 text-purple-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold">{feature.title}</h3>
                        <div className="flex items-center text-sm text-gray-400">
                          <TrendingUp className="w-3 h-3 mr-1" />
                          {feature.popularity}% popularity
                        </div>
                      </div>
                    </div>
                    
                    <p className="text-gray-300 mb-4">{feature.description}</p>
                    
                    <div className="flex flex-wrap gap-2 mb-4">
                      {feature.tags.map(tag => (
                        <span key={tag} className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-xs">
                          {tag}
                        </span>
                      ))}
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <button className="flex items-center text-purple-400 hover:text-purple-300 text-sm">
                        <MessageSquare className="w-4 h-4 mr-1" />
                        Discuss with AI
                      </button>
                      <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm">
                        Use Template
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Workflow Demo Features */}
            <div className="bg-gray-800 rounded-lg p-8">
              <h3 className="text-xl font-bold mb-6 flex items-center">
                <Zap className="w-6 h-6 mr-2 text-yellow-400" />
                Key Workflow Features
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="text-center">
                  <Bot className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">AI Integration</h4>
                  <p className="text-sm text-gray-400">Built-in AI models for intelligent processing</p>
                </div>
                <div className="text-center">
                  <Settings className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">Visual Builder</h4>
                  <p className="text-sm text-gray-400">Drag-and-drop workflow creation</p>
                </div>
                <div className="text-center">
                  <TrendingUp className="w-8 h-8 text-green-400 mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">Real-time Analytics</h4>
                  <p className="text-sm text-gray-400">Monitor performance and optimize</p>
                </div>
                <div className="text-center">
                  <MessageSquare className="w-8 h-8 text-orange-400 mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">Chat Control</h4>
                  <p className="text-sm text-gray-400">Manage workflows via conversation</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeDemo === 'integration' && (
          <div className="space-y-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold mb-4">AI Integration Catalog</h2>
              <p className="text-gray-400">
                Connect powerful AI services and tools to enhance your workflows
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {integrationFeatures.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <div key={index} className="bg-gray-800 rounded-lg p-6 hover:bg-gray-700 transition-colors">
                    <div className="flex items-center mb-4">
                      <div className="p-3 bg-blue-600/20 rounded-lg mr-4">
                        <Icon className="w-6 h-6 text-blue-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold">{feature.title}</h3>
                        <p className="text-sm text-gray-400">{feature.provider}</p>
                      </div>
                    </div>
                    
                    <p className="text-gray-300 mb-4">{feature.description}</p>
                    
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center text-sm text-gray-400">
                        <Star className="w-3 h-3 mr-1 text-yellow-400" />
                        {feature.rating}/5
                      </div>
                      <span className="px-2 py-1 bg-green-600/20 text-green-300 rounded text-xs">
                        {feature.pricing}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <button className="flex items-center text-blue-400 hover:text-blue-300 text-sm">
                        <MessageSquare className="w-4 h-4 mr-1" />
                        Chat Setup
                      </button>
                      <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm">
                        Install
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Integration Categories */}
            <div className="bg-gray-800 rounded-lg p-8">
              <h3 className="text-xl font-bold mb-6 flex items-center">
                <Target className="w-6 h-6 mr-2 text-blue-400" />
                Integration Categories
              </h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {[
                  { icon: Brain, label: 'AI & ML', count: 15 },
                  { icon: MessageSquare, label: 'Communication', count: 8 },
                  { icon: Cloud, label: 'Cloud Services', count: 12 },
                  { icon: Database, label: 'Data & Analytics', count: 10 },
                  { icon: Code, label: 'Development', count: 6 },
                  { icon: Settings, label: 'Automation', count: 9 }
                ].map((category, index) => {
                  const Icon = category.icon;
                  return (
                    <div key={index} className="text-center p-4 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors">
                      <Icon className="w-6 h-6 mx-auto mb-2 text-blue-400" />
                      <h4 className="font-medium text-sm">{category.label}</h4>
                      <p className="text-xs text-gray-400">{category.count} available</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {activeDemo === 'chat' && (
          <div className="space-y-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold mb-4">AI Chat Integration</h2>
              <p className="text-gray-400">
                Interact with workflows and integrations through natural conversation
              </p>
            </div>

            <div className="max-w-4xl mx-auto space-y-6">
              {chatExamples.map((example, index) => (
                <div key={index} className="space-y-4">
                  {/* User Message */}
                  <div className="flex justify-end">
                    <div className="bg-purple-600 text-white p-4 rounded-lg max-w-2xl">
                      <p>{example.user}</p>
                    </div>
                  </div>
                  
                  {/* Assistant Response */}
                  <div className="flex justify-start">
                    <div className="bg-gray-800 text-white p-4 rounded-lg max-w-2xl">
                      <div className="flex items-center mb-2">
                        <Bot className="w-5 h-5 text-purple-400 mr-2" />
                        <span className="font-medium">AI Assistant</span>
                      </div>
                      <div className="whitespace-pre-line">{example.assistant}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Chat Features */}
            <div className="bg-gray-800 rounded-lg p-8">
              <h3 className="text-xl font-bold mb-6 flex items-center">
                <MessageSquare className="w-6 h-6 mr-2 text-green-400" />
                Chat Capabilities
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="text-center">
                  <Workflow className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">Workflow Creation</h4>
                  <p className="text-sm text-gray-400">Create and modify workflows through conversation</p>
                </div>
                <div className="text-center">
                  <Plug className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">Integration Setup</h4>
                  <p className="text-sm text-gray-400">Get guided help for integration configuration</p>
                </div>
                <div className="text-center">
                  <TrendingUp className="w-8 h-8 text-green-400 mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">Performance Analysis</h4>
                  <p className="text-sm text-gray-400">Analyze and optimize your automation</p>
                </div>
                <div className="text-center">
                  <Settings className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">Troubleshooting</h4>
                  <p className="text-sm text-gray-400">Get help with issues and errors</p>
                </div>
                <div className="text-center">
                  <Brain className="w-8 h-8 text-pink-400 mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">AI Recommendations</h4>
                  <p className="text-sm text-gray-400">Receive intelligent suggestions</p>
                </div>
                <div className="text-center">
                  <Users className="w-8 h-8 text-orange-400 mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">Learning & Training</h4>
                  <p className="text-sm text-gray-400">Learn best practices and techniques</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Call to Action */}
        <div className="text-center mt-12 p-8 bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-lg border border-purple-500/20">
          <h2 className="text-2xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-gray-300 mb-6 max-w-2xl mx-auto">
            Experience the power of AI-driven automation. Create intelligent workflows, 
            connect powerful integrations, and interact with everything through natural conversation.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium transition-colors">
              <Workflow className="w-5 h-5 mr-2 inline" />
              Explore Workflows
            </button>
            <button className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors">
              <Plug className="w-5 h-5 mr-2 inline" />
              Browse Integrations
            </button>
            <button className="px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg font-medium transition-colors">
              <MessageSquare className="w-5 h-5 mr-2 inline" />
              Start Chatting
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};