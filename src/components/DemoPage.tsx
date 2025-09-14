import React, { useState } from 'react';
import { 
  Users, 
  BarChart3, 
  Shield, 
  MessageSquare, 
  TrendingUp, 
  Activity,
  Eye,
  Clock,
  CheckCircle,
  Star
} from 'lucide-react';

export const DemoPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'features' | 'analytics' | 'auth'>('features');

  const features = [
    {
      icon: MessageSquare,
      title: 'AI-Powered Chat',
      description: 'Advanced conversational AI with voice support and multiple chat modes',
      color: 'text-purple-500'
    },
    {
      icon: BarChart3,
      title: 'Analytics Dashboard',
      description: 'Comprehensive usage analytics with real-time metrics and insights',
      color: 'text-blue-500'
    },
    {
      icon: Shield,
      title: 'User Authentication',
      description: 'Secure login/register system with profile management',
      color: 'text-green-500'
    },
    {
      icon: Activity,
      title: 'Performance Monitoring',
      description: 'Real-time system health and performance tracking',
      color: 'text-yellow-500'
    }
  ];

  const analyticsFeatures = [
    'User activity tracking and trends',
    'Content engagement analytics',
    'Performance metrics and uptime monitoring',
    'Real-time dashboard with interactive charts',
    'Export capabilities for data analysis',
    'Hourly activity heatmaps'
  ];

  const authFeatures = [
    'Secure user registration and login',
    'Password strength validation',
    'Forgot password functionality',
    'User profile management',
    'Role-based access control',
    'Session management'
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 py-20">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <h1 className="text-5xl font-bold mb-6">Reddit AEO Platform</h1>
          <p className="text-xl text-purple-100 mb-8 max-w-3xl mx-auto">
            A comprehensive AI-powered platform with advanced analytics, user management, 
            and intelligent chat capabilities for Reddit AEO operations.
          </p>
          <div className="flex justify-center space-x-4">
            <div className="bg-white/20 rounded-lg px-6 py-3">
              <div className="flex items-center space-x-2">
                <Users className="w-5 h-5" />
                <span>User Management</span>
              </div>
            </div>
            <div className="bg-white/20 rounded-lg px-6 py-3">
              <div className="flex items-center space-x-2">
                <BarChart3 className="w-5 h-5" />
                <span>Analytics Dashboard</span>
              </div>
            </div>
            <div className="bg-white/20 rounded-lg px-6 py-3">
              <div className="flex items-center space-x-2">
                <MessageSquare className="w-5 h-5" />
                <span>AI Chat</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex justify-center space-x-2 mb-8">
          <button
            onClick={() => setActiveTab('features')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'features'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Core Features
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'analytics'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Analytics Features
          </button>
          <button
            onClick={() => setActiveTab('auth')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'auth'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Authentication
          </button>
        </div>

        {/* Content Sections */}
        {activeTab === 'features' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                  <div className="flex items-center space-x-4 mb-4">
                    <Icon className={`w-8 h-8 ${feature.color}`} />
                    <h3 className="text-xl font-semibold">{feature.title}</h3>
                  </div>
                  <p className="text-gray-300">{feature.description}</p>
                </div>
              );
            })}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-8">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-2xl font-semibold mb-6 flex items-center">
                <BarChart3 className="w-6 h-6 mr-3 text-blue-500" />
                Analytics Dashboard Features
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-lg font-medium mb-3 text-blue-400">Key Metrics</h4>
                  <ul className="space-y-2">
                    {analyticsFeatures.map((feature, index) => (
                      <li key={index} className="flex items-center space-x-2 text-gray-300">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="bg-gray-700 rounded-lg p-4">
                  <h4 className="text-lg font-medium mb-3 text-green-400">Sample Metrics</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-300">Total Users</span>
                      <span className="text-white font-semibold">2,847</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-300">Active Sessions</span>
                      <span className="text-white font-semibold">1,234</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-300">Messages Today</span>
                      <span className="text-white font-semibold">15,692</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-300">Uptime</span>
                      <span className="text-green-400 font-semibold">99.9%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'auth' && (
          <div className="space-y-8">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-2xl font-semibold mb-6 flex items-center">
                <Shield className="w-6 h-6 mr-3 text-green-500" />
                Authentication System
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-lg font-medium mb-3 text-green-400">Security Features</h4>
                  <ul className="space-y-2">
                    {authFeatures.map((feature, index) => (
                      <li key={index} className="flex items-center space-x-2 text-gray-300">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="bg-gray-700 rounded-lg p-4">
                  <h4 className="text-lg font-medium mb-3 text-purple-400">User Roles</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300">Admin</span>
                      <span className="bg-red-600 text-white px-2 py-1 rounded text-xs">Full Access</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300">Researcher</span>
                      <span className="bg-blue-600 text-white px-2 py-1 rounded text-xs">Advanced</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300">Student</span>
                      <span className="bg-green-600 text-white px-2 py-1 rounded text-xs">Basic</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300">Guest</span>
                      <span className="bg-gray-600 text-white px-2 py-1 rounded text-xs">Limited</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stats Section */}
      <div className="bg-gray-800 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">Platform Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-purple-500 mb-2">99.9%</div>
              <div className="text-gray-300">Uptime</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-blue-500 mb-2">2.8K+</div>
              <div className="text-gray-300">Active Users</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-500 mb-2">150ms</div>
              <div className="text-gray-300">Avg Response</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-yellow-500 mb-2">24/7</div>
              <div className="text-gray-300">Monitoring</div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-900 py-8 border-t border-gray-700">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <p className="text-gray-400">
            Reddit AEO Platform - Advanced Analytics & User Management System
          </p>
        </div>
      </div>
    </div>
  );
};