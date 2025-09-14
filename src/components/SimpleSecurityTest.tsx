/**
 * SimpleSecurityTest - Minimal test component to isolate button interaction issues
 */
import React, { useState } from 'react';
import { Shield, AlertCircle, Users, Activity, RefreshCw } from 'lucide-react';

export const SimpleSecurityTest: React.FC = () => {
  const [clickCount, setClickCount] = useState(0);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'sessions' | 'alerts'>('overview');
  const [lastAction, setLastAction] = useState<string>('');

  const handleClick = (action: string) => {
    console.log(`Action clicked: ${action}`);
    setClickCount(prev => prev + 1);
    setLastAction(action);
  };

  const handleTabClick = (tab: 'overview' | 'sessions' | 'alerts') => {
    console.log(`Tab clicked: ${tab}`);
    setSelectedTab(tab);
    handleClick(`Tab: ${tab}`);
  };

  return (
    <div className="p-6 bg-gray-900 text-white min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2 flex items-center">
                <Shield className="w-8 h-8 mr-3 text-blue-500" />
                Security Dashboard Test
              </h1>
              <p className="text-gray-400">Testing button interactions and component functionality</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-400">
                Clicks: <span className="text-green-400 font-bold">{clickCount}</span>
              </div>
              <button
                onClick={() => handleClick('Refresh')}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Security Status</p>
                <p className="text-lg font-bold text-green-400">Good</p>
              </div>
              <Shield className="w-8 h-8 text-green-500" />
            </div>
            <button
              onClick={() => handleClick('Security Status')}
              className="mt-3 w-full px-3 py-2 bg-green-600 hover:bg-green-700 rounded text-sm transition-colors"
            >
              View Details
            </button>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Active Sessions</p>
                <p className="text-2xl font-bold">5</p>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>
            <button
              onClick={() => handleClick('View Sessions')}
              className="mt-3 w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
            >
              Manage Sessions
            </button>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Security Alerts</p>
                <p className="text-2xl font-bold text-orange-400">2</p>
              </div>
              <AlertCircle className="w-8 h-8 text-orange-500" />
            </div>
            <button
              onClick={() => handleClick('View Alerts')}
              className="mt-3 w-full px-3 py-2 bg-orange-600 hover:bg-orange-700 rounded text-sm transition-colors"
            >
              View Alerts
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-6">
          <div className="flex space-x-1 bg-gray-800 rounded-lg p-1">
            {[
              { id: 'overview', label: 'Overview', icon: Activity },
              { id: 'sessions', label: 'Sessions', icon: Users },
              { id: 'alerts', label: 'Alerts', icon: AlertCircle }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => handleTabClick(id as any)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                  selectedTab === id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">
            {selectedTab.charAt(0).toUpperCase() + selectedTab.slice(1)} Content
          </h2>
          
          {selectedTab === 'overview' && (
            <div className="space-y-4">
              <p className="text-gray-300">Security overview and recent activity</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => handleClick('Change Password')}
                  className="px-4 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors text-left"
                >
                  <div className="font-semibold">Change Password</div>
                  <div className="text-sm text-purple-200">Update your account password</div>
                </button>
                <button
                  onClick={() => handleClick('View Activity')}
                  className="px-4 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors text-left"
                >
                  <div className="font-semibold">View Activity</div>
                  <div className="text-sm text-indigo-200">Check recent account activity</div>
                </button>
              </div>
            </div>
          )}

          {selectedTab === 'sessions' && (
            <div className="space-y-4">
              <p className="text-gray-300">Active user sessions</p>
              <div className="space-y-2">
                {[1, 2, 3].map(i => (
                  <div key={i} className="flex items-center justify-between p-3 bg-gray-700 rounded">
                    <div>
                      <div className="font-medium">Session {i}</div>
                      <div className="text-sm text-gray-400">192.168.1.{i} - Chrome</div>
                    </div>
                    <button
                      onClick={() => handleClick(`Terminate Session ${i}`)}
                      className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm transition-colors"
                    >
                      Terminate
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedTab === 'alerts' && (
            <div className="space-y-4">
              <p className="text-gray-300">Security alerts and notifications</p>
              <div className="space-y-2">
                {[
                  { id: 1, message: 'Failed login attempt detected', severity: 'medium' },
                  { id: 2, message: 'Unusual activity from new location', severity: 'high' }
                ].map(alert => (
                  <div key={alert.id} className="flex items-center justify-between p-3 bg-gray-700 rounded">
                    <div>
                      <div className="font-medium">{alert.message}</div>
                      <div className="text-sm text-gray-400">Severity: {alert.severity}</div>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleClick(`Resolve Alert ${alert.id}`)}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm transition-colors"
                      >
                        Resolve
                      </button>
                      <button
                        onClick={() => handleClick(`Investigate Alert ${alert.id}`)}
                        className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 rounded text-sm transition-colors"
                      >
                        Investigate
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Status Display */}
        <div className="mt-6 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold">Last Action</h3>
              <p className="text-sm text-gray-400">{lastAction || 'None'}</p>
            </div>
            <div>
              <h3 className="font-semibold">Total Clicks</h3>
              <p className="text-2xl font-bold text-green-400">{clickCount}</p>
            </div>
          </div>
        </div>

        {/* Debug Info */}
        <div className="mt-4 p-4 bg-gray-800 rounded-lg">
          <h3 className="font-semibold mb-2">Debug Information</h3>
          <div className="text-sm space-y-1">
            <div>Selected Tab: <span className="text-blue-400">{selectedTab}</span></div>
            <div>Click Count: <span className="text-green-400">{clickCount}</span></div>
            <div>Last Action: <span className="text-yellow-400">{lastAction || 'None'}</span></div>
            <div>Component Status: <span className="text-green-400">Loaded</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};