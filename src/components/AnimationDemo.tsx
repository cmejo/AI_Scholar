import React, { useState, useEffect } from 'react';
import { Mic, Volume2, Brain, CheckCircle } from 'lucide-react';
import '../styles/animations.css';

export const AnimationDemo: React.FC = () => {
  const [currentDemo, setCurrentDemo] = useState<string>('recording');
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentDemo(prev => {
        switch (prev) {
          case 'recording': return 'processing';
          case 'processing': return 'success';
          case 'success': return 'speaking';
          case 'speaking': return 'recording';
          default: return 'recording';
        }
      });
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getDemoButton = () => {
    switch (currentDemo) {
      case 'recording':
        return {
          className: 'bg-red-600 voice-recording',
          icon: Mic,
          label: 'Recording Animation',
        };
      case 'processing':
        return {
          className: 'bg-yellow-600 voice-processing',
          icon: Mic,
          label: 'Processing Animation',
        };
      case 'success':
        return {
          className: 'bg-green-600 voice-success',
          icon: CheckCircle,
          label: 'Success Animation',
        };
      case 'speaking':
        return {
          className: 'bg-blue-600 animate-pulse-recording',
          icon: Volume2,
          label: 'Speaking Animation',
        };
      default:
        return {
          className: 'bg-purple-600',
          icon: Mic,
          label: 'Default State',
        };
    }
  };

  const demo = getDemoButton();
  const IconComponent = demo.icon;

  return (
    <div className="p-8 bg-gray-900 text-white min-h-screen">
      <h1 className="text-3xl font-bold mb-8 animate-fade-in">Voice Interface Animation Demo</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {/* Main Demo Button */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Current Demo: {demo.label}</h2>
          <button
            className={`p-4 rounded-lg ${demo.className} voice-state-transition`}
          >
            <IconComponent className="w-8 h-8 text-white" />
          </button>
          <p className="mt-2 text-sm text-gray-400">Auto-cycling every 3 seconds</p>
        </div>

        {/* Voice Wave Demo */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Voice Wave Animation</h2>
          <div className="voice-wave listening">
            <div className="voice-wave-bar h-1"></div>
            <div className="voice-wave-bar h-2"></div>
            <div className="voice-wave-bar h-3"></div>
            <div className="voice-wave-bar h-4"></div>
            <div className="voice-wave-bar h-3"></div>
            <div className="voice-wave-bar h-2"></div>
            <div className="voice-wave-bar h-1"></div>
          </div>
        </div>

        {/* Loading Animation */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Loading Animation</h2>
          <div className="voice-loading bg-gray-700 p-4 rounded">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-purple-500 border-t-transparent"></div>
                <div className="absolute inset-0 animate-ping rounded-full h-6 w-6 border border-purple-400 opacity-20"></div>
              </div>
              <span>Processing...</span>
            </div>
          </div>
        </div>

        {/* Confidence Bar Demo */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Confidence Bar</h2>
          <div className="space-y-2">
            <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-green-500 to-green-400 confidence-fill" style={{ width: '85%' }}></div>
            </div>
            <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-yellow-500 to-yellow-400 confidence-fill" style={{ width: '65%' }}></div>
            </div>
            <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-red-500 to-red-400 confidence-fill" style={{ width: '35%' }}></div>
            </div>
          </div>
        </div>

        {/* Button Hover Effects */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Button Hover Effects</h2>
          <div className="space-y-2">
            <button className="w-full p-2 bg-purple-600 rounded voice-button-hover">
              Hover Me
            </button>
            <button className="w-full p-2 bg-blue-600 rounded voice-state-transition hover:bg-blue-700">
              Smooth Transition
            </button>
          </div>
        </div>

        {/* Message Animations */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Message Animations</h2>
          <div className="space-y-2">
            <div className="p-3 bg-blue-900/40 border-l-4 border-blue-400 rounded message-voice-input">
              Voice Input Message
            </div>
            <div className="p-3 bg-gray-700 rounded animate-fade-in">
              Fade In Message
            </div>
            <div className="p-3 bg-gray-700 rounded animate-slide-in">
              Slide In Message
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="mt-8 flex space-x-4">
        <button
          onClick={() => setCurrentDemo('recording')}
          className="px-4 py-2 bg-red-600 rounded hover:bg-red-700 voice-state-transition"
        >
          Recording
        </button>
        <button
          onClick={() => setCurrentDemo('processing')}
          className="px-4 py-2 bg-yellow-600 rounded hover:bg-yellow-700 voice-state-transition"
        >
          Processing
        </button>
        <button
          onClick={() => setCurrentDemo('success')}
          className="px-4 py-2 bg-green-600 rounded hover:bg-green-700 voice-state-transition"
        >
          Success
        </button>
        <button
          onClick={() => setCurrentDemo('speaking')}
          className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 voice-state-transition"
        >
          Speaking
        </button>
      </div>
    </div>
  );
};

export default AnimationDemo;