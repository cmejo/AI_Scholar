import React from 'react';
import { TrendingUp, TrendingDown, Users, MessageSquare } from 'lucide-react';

interface UsageData {
  date: string;
  users: number;
  messages: number;
}

interface UsageMetricsProps {
  data: UsageData[];
  timeRange: string;
}

export const UsageMetrics: React.FC<UsageMetricsProps> = ({ data, timeRange }) => {
  const calculateTrend = (values: number[]) => {
    if (values.length < 2) return 0;
    const recent = values.slice(-7).reduce((a, b) => a + b, 0) / 7;
    const previous = values.slice(-14, -7).reduce((a, b) => a + b, 0) / 7;
    return previous > 0 ? ((recent - previous) / previous) * 100 : 0;
  };

  const userValues = data.map(d => d.users);
  const messageValues = data.map(d => d.messages);
  
  const userTrend = calculateTrend(userValues);
  const messageTrend = calculateTrend(messageValues);

  const maxUsers = Math.max(...userValues);
  const maxMessages = Math.max(...messageValues);

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-white">Usage Trends</h3>
        <span className="text-sm text-gray-400 capitalize">{timeRange}</span>
      </div>

      {/* Trend Summary */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-300 text-sm">User Activity</span>
            <Users className="w-4 h-4 text-purple-400" />
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-lg font-semibold text-white">
              {userValues[userValues.length - 1]?.toLocaleString() || 0}
            </span>
            <div className={`flex items-center text-sm ${
              userTrend >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {userTrend >= 0 ? (
                <TrendingUp className="w-3 h-3 mr-1" />
              ) : (
                <TrendingDown className="w-3 h-3 mr-1" />
              )}
              {Math.abs(userTrend).toFixed(1)}%
            </div>
          </div>
        </div>

        <div className="bg-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-300 text-sm">Messages</span>
            <MessageSquare className="w-4 h-4 text-blue-400" />
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-lg font-semibold text-white">
              {messageValues[messageValues.length - 1]?.toLocaleString() || 0}
            </span>
            <div className={`flex items-center text-sm ${
              messageTrend >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {messageTrend >= 0 ? (
                <TrendingUp className="w-3 h-3 mr-1" />
              ) : (
                <TrendingDown className="w-3 h-3 mr-1" />
              )}
              {Math.abs(messageTrend).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Mini Chart */}
      <div className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Daily Active Users</span>
            <span className="text-sm text-gray-400">Peak: {maxUsers.toLocaleString()}</span>
          </div>
          <div className="flex items-end space-x-1 h-16">
            {data.slice(-14).map((item, index) => (
              <div
                key={index}
                className="flex-1 bg-purple-600 rounded-t opacity-70 hover:opacity-100 transition-opacity"
                style={{
                  height: `${(item.users / maxUsers) * 100}%`,
                  minHeight: '2px'
                }}
                title={`${item.date}: ${item.users} users`}
              />
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Daily Messages</span>
            <span className="text-sm text-gray-400">Peak: {maxMessages.toLocaleString()}</span>
          </div>
          <div className="flex items-end space-x-1 h-16">
            {data.slice(-14).map((item, index) => (
              <div
                key={index}
                className="flex-1 bg-blue-600 rounded-t opacity-70 hover:opacity-100 transition-opacity"
                style={{
                  height: `${(item.messages / maxMessages) * 100}%`,
                  minHeight: '2px'
                }}
                title={`${item.date}: ${item.messages} messages`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-sm text-gray-400">Avg Daily Users</p>
            <p className="text-lg font-semibold text-white">
              {Math.round(userValues.reduce((a, b) => a + b, 0) / userValues.length).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Avg Daily Messages</p>
            <p className="text-lg font-semibold text-white">
              {Math.round(messageValues.reduce((a, b) => a + b, 0) / messageValues.length).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Messages per User</p>
            <p className="text-lg font-semibold text-white">
              {(messageValues.reduce((a, b) => a + b, 0) / userValues.reduce((a, b) => a + b, 0) || 0).toFixed(1)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};