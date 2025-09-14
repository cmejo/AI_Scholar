import React, { useState } from 'react';
import { Calendar, Clock, Users, Activity } from 'lucide-react';

interface ActivityData {
  date: string;
  users: number;
  messages: number;
}

interface UserActivityChartProps {
  data: ActivityData[];
}

export const UserActivityChart: React.FC<UserActivityChartProps> = ({ data }) => {
  const [selectedPeriod, setSelectedPeriod] = useState<'day' | 'week' | 'month'>('week');
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const processData = () => {
    if (selectedPeriod === 'day') {
      return data.slice(-7);
    } else if (selectedPeriod === 'week') {
      return data.slice(-30);
    } else {
      return data;
    }
  };

  const chartData = processData();
  const maxValue = Math.max(...chartData.map(d => Math.max(d.users, d.messages)));

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    if (selectedPeriod === 'day') {
      return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    } else if (selectedPeriod === 'week') {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } else {
      return date.toLocaleDateString('en-US', { month: 'short' });
    }
  };

  const getHourlyData = () => {
    // Mock hourly data for demonstration
    const hours = Array.from({ length: 24 }, (_, i) => i);
    return hours.map(hour => ({
      hour,
      users: Math.floor(Math.random() * 100) + 20,
      messages: Math.floor(Math.random() * 200) + 50,
    }));
  };

  const hourlyData = getHourlyData();
  const maxHourlyValue = Math.max(...hourlyData.map(d => Math.max(d.users, d.messages)));

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-white flex items-center">
          <Activity className="w-5 h-5 mr-2 text-purple-500" />
          User Activity
        </h3>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setSelectedPeriod('day')}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              selectedPeriod === 'day'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            7D
          </button>
          <button
            onClick={() => setSelectedPeriod('week')}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              selectedPeriod === 'week'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            30D
          </button>
          <button
            onClick={() => setSelectedPeriod('month')}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              selectedPeriod === 'month'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            90D
          </button>
        </div>
      </div>

      {/* Main Chart */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
              <span className="text-sm text-gray-300">Users</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-sm text-gray-300">Messages</span>
            </div>
          </div>
          
          {hoveredIndex !== null && (
            <div className="bg-gray-700 rounded-lg p-2 text-sm">
              <p className="text-white font-medium">{formatDate(chartData[hoveredIndex].date)}</p>
              <p className="text-purple-400">Users: {chartData[hoveredIndex].users}</p>
              <p className="text-blue-400">Messages: {chartData[hoveredIndex].messages}</p>
            </div>
          )}
        </div>

        <div className="relative h-48 bg-gray-900 rounded-lg p-4">
          <div className="flex items-end justify-between h-full space-x-1">
            {chartData.map((item, index) => (
              <div
                key={index}
                className="flex-1 flex flex-col justify-end space-y-1 cursor-pointer"
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
              >
                <div
                  className="bg-blue-500 rounded-t opacity-80 hover:opacity-100 transition-opacity"
                  style={{
                    height: `${(item.messages / maxValue) * 100}%`,
                    minHeight: '2px'
                  }}
                />
                <div
                  className="bg-purple-500 rounded-t opacity-80 hover:opacity-100 transition-opacity"
                  style={{
                    height: `${(item.users / maxValue) * 100}%`,
                    minHeight: '2px'
                  }}
                />
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-between mt-2 text-xs text-gray-400">
          {chartData.map((item, index) => (
            <span key={index} className={`${index % Math.ceil(chartData.length / 5) === 0 ? 'block' : 'hidden'}`}>
              {formatDate(item.date)}
            </span>
          ))}
        </div>
      </div>

      {/* Hourly Heatmap */}
      <div className="border-t border-gray-700 pt-6">
        <h4 className="text-lg font-medium text-white mb-4 flex items-center">
          <Clock className="w-4 h-4 mr-2 text-gray-400" />
          Activity by Hour
        </h4>
        
        <div className="grid grid-cols-12 gap-1">
          {hourlyData.map((item, index) => (
            <div
              key={index}
              className="aspect-square rounded flex items-center justify-center text-xs font-medium relative group cursor-pointer"
              style={{
                backgroundColor: `rgba(147, 51, 234, ${(item.users / maxHourlyValue) * 0.8 + 0.1})`,
              }}
            >
              <span className="text-white">{item.hour}</span>
              
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-gray-700 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                {item.hour}:00 - {item.users} users, {item.messages} messages
              </div>
            </div>
          ))}
        </div>
        
        <div className="flex justify-between mt-2 text-xs text-gray-400">
          <span>12 AM</span>
          <span>6 AM</span>
          <span>12 PM</span>
          <span>6 PM</span>
          <span>11 PM</span>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="border-t border-gray-700 pt-4 mt-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-white">
              {chartData.reduce((sum, item) => sum + item.users, 0).toLocaleString()}
            </p>
            <p className="text-sm text-gray-400">Total Users</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-white">
              {chartData.reduce((sum, item) => sum + item.messages, 0).toLocaleString()}
            </p>
            <p className="text-sm text-gray-400">Total Messages</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-white">
              {Math.round(chartData.reduce((sum, item) => sum + item.users, 0) / chartData.length)}
            </p>
            <p className="text-sm text-gray-400">Avg Daily Users</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-white">
              {(chartData.reduce((sum, item) => sum + item.messages, 0) / chartData.reduce((sum, item) => sum + item.users, 0) || 0).toFixed(1)}
            </p>
            <p className="text-sm text-gray-400">Msgs per User</p>
          </div>
        </div>
      </div>
    </div>
  );
};