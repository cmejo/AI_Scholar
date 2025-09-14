/**
 * DebugButtonTest - Simple component to test button interactions
 */
import React, { useState } from 'react';
import { AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

export const DebugButtonTest: React.FC = () => {
  const [clickCount, setClickCount] = useState(0);
  const [lastClicked, setLastClicked] = useState<string>('');

  const handleButtonClick = (buttonName: string) => {
    console.log(`Button clicked: ${buttonName}`);
    setClickCount(prev => prev + 1);
    setLastClicked(buttonName);
  };

  return (
    <div className="p-6 bg-gray-900 text-white min-h-screen">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">🔧 Button Interaction Debug Test</h1>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Click Counter</h2>
          <p className="text-lg mb-2">Total clicks: <span className="text-green-400 font-bold">{clickCount}</span></p>
          <p className="text-sm text-gray-400">Last clicked: {lastClicked || 'None'}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <button
            onClick={() => handleButtonClick('Primary Button')}
            className="flex items-center justify-center space-x-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <CheckCircle className="w-5 h-5" />
            <span>Primary Button</span>
          </button>

          <button
            onClick={() => handleButtonClick('Secondary Button')}
            className="flex items-center justify-center space-x-2 px-4 py-3 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-5 h-5" />
            <span>Secondary Button</span>
          </button>

          <button
            onClick={() => handleButtonClick('Danger Button')}
            className="flex items-center justify-center space-x-2 px-4 py-3 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
          >
            <AlertCircle className="w-5 h-5" />
            <span>Danger Button</span>
          </button>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Interactive Elements Test</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Test Input</label>
              <input
                type="text"
                placeholder="Type something..."
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                onChange={(e) => console.log('Input changed:', e.target.value)}
              />
            </div>

            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  onChange={(e) => {
                    console.log('Checkbox changed:', e.target.checked);
                    handleButtonClick('Checkbox');
                  }}
                  className="w-4 h-4"
                />
                <span>Test Checkbox</span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Test Select</label>
              <select
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                onChange={(e) => {
                  console.log('Select changed:', e.target.value);
                  handleButtonClick('Select');
                }}
              >
                <option value="">Choose an option</option>
                <option value="option1">Option 1</option>
                <option value="option2">Option 2</option>
                <option value="option3">Option 3</option>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Event Handler Test</h2>
          
          <div className="space-y-3">
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Click event:', e);
                handleButtonClick('Event Test Button');
              }}
              className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded transition-colors"
            >
              Event Handler Test
            </button>

            <button
              onMouseDown={() => console.log('Mouse down')}
              onMouseUp={() => console.log('Mouse up')}
              onClick={() => {
                console.log('Click detected');
                handleButtonClick('Mouse Event Button');
              }}
              className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded transition-colors"
            >
              Mouse Event Test
            </button>

            <div
              onClick={() => {
                console.log('Div clicked');
                handleButtonClick('Clickable Div');
              }}
              className="w-full px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded transition-colors cursor-pointer text-center"
            >
              Clickable Div Test
            </div>
          </div>
        </div>

        <div className="mt-6 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg">
          <h3 className="font-semibold mb-2">Debug Instructions:</h3>
          <ul className="text-sm space-y-1">
            <li>• Click any button and check if the counter increases</li>
            <li>• Open browser console to see click events</li>
            <li>• Test different interaction types</li>
            <li>• If buttons don't work, there's a JavaScript/React issue</li>
          </ul>
        </div>
      </div>
    </div>
  );
};