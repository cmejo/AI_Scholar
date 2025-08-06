/**
 * Interactive Visualization Demo Component
 * 
 * This component demonstrates all the interactive visualization features
 * including Plotly, D3.js, Chart.js support, real-time updates, collaborative
 * annotations, and embedding capabilities.
 */

import React, { useState, useEffect } from 'react';
import {
  Play, Pause, Users, MessageSquare, Share2, Download,
  BarChart3, Network, PieChart, TrendingUp, Zap, Eye
} from 'lucide-react';
import InteractiveVisualization from './InteractiveVisualization';
import { interactiveVisualizationService, VisualizationData } from '../services/interactiveVisualizationService';

interface DemoVisualization {
  id: string;
  title: string;
  description: string;
  type: 'plotly' | 'd3' | 'chartjs' | 'custom';
  data: VisualizationData;
  icon: React.ReactNode;
  category: string;
}

export const InteractiveVisualizationDemo: React.FC = () => {
  const [selectedDemo, setSelectedDemo] = useState<string>('research-metrics');
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false);
  const [collaborativeMode, setCollaborativeMode] = useState(false);
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [activeUsers] = useState(['user1', 'user2', 'user3']);

  // Sample visualizations
  const demoVisualizations: DemoVisualization[] = [
    {
      id: 'research-metrics',
      title: 'Research Metrics Dashboard',
      description: 'Multi-trace Plotly visualization showing research output over time',
      type: 'plotly',
      category: 'Analytics',
      icon: <TrendingUp size={20} />,
      data: {
        data: {
          title: 'Research Metrics Over Time'
        },
        layout: {
          title: {
            text: 'Research Output Metrics',
            font: { color: '#ffffff', size: 18 }
          },
          xaxis: { 
            title: 'Year',
            color: '#ffffff',
            gridcolor: 'rgba(255,255,255,0.1)'
          },
          yaxis: { 
            title: 'Count',
            color: '#ffffff',
            gridcolor: 'rgba(255,255,255,0.1)'
          },
          showlegend: true,
          legend: { font: { color: '#ffffff' } },
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)'
        },
        config: {
          displayModeBar: true,
          responsive: true
        },
        traces: [
          {
            x: ['2020', '2021', '2022', '2023', '2024'],
            y: [45, 67, 89, 123, 156],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Citations',
            line: { color: '#3B82F6', width: 3 },
            marker: { size: 8 }
          },
          {
            x: ['2020', '2021', '2022', '2023', '2024'],
            y: [12, 18, 25, 34, 42],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Publications',
            line: { color: '#10B981', width: 3 },
            marker: { size: 8 }
          },
          {
            x: ['2020', '2021', '2022', '2023', '2024'],
            y: [5, 8, 12, 18, 25],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Collaborations',
            line: { color: '#F59E0B', width: 3 },
            marker: { size: 8 }
          }
        ]
      }
    },
    {
      id: 'knowledge-graph',
      title: 'AI Research Knowledge Graph',
      description: 'D3.js network visualization of research concepts and relationships',
      type: 'd3',
      category: 'Network',
      icon: <Network size={20} />,
      data: {
        data: {
          nodes: [
            { id: 'Artificial Intelligence', group: 1, size: 25 },
            { id: 'Machine Learning', group: 1, size: 22 },
            { id: 'Deep Learning', group: 1, size: 20 },
            { id: 'Neural Networks', group: 2, size: 18 },
            { id: 'Computer Vision', group: 2, size: 16 },
            { id: 'Natural Language Processing', group: 2, size: 16 },
            { id: 'Reinforcement Learning', group: 3, size: 14 },
            { id: 'Generative AI', group: 3, size: 14 },
            { id: 'Robotics', group: 4, size: 12 },
            { id: 'Ethics in AI', group: 4, size: 10 }
          ],
          links: [
            { source: 'Artificial Intelligence', target: 'Machine Learning', value: 8 },
            { source: 'Machine Learning', target: 'Deep Learning', value: 7 },
            { source: 'Deep Learning', target: 'Neural Networks', value: 6 },
            { source: 'Deep Learning', target: 'Computer Vision', value: 5 },
            { source: 'Deep Learning', target: 'Natural Language Processing', value: 5 },
            { source: 'Machine Learning', target: 'Reinforcement Learning', value: 4 },
            { source: 'Deep Learning', target: 'Generative AI', value: 4 },
            { source: 'Artificial Intelligence', target: 'Robotics', value: 3 },
            { source: 'Artificial Intelligence', target: 'Ethics in AI', value: 3 },
            { source: 'Computer Vision', target: 'Robotics', value: 2 }
          ]
        },
        layout: {
          width: 800,
          height: 600,
          force: {
            charge: -400,
            linkDistance: 100,
            gravity: 0.05
          }
        },
        config: {
          interactive: true,
          zoomable: true,
          draggable: true
        }
      }
    },
    {
      id: 'topic-distribution',
      title: 'Research Topic Distribution',
      description: 'Chart.js pie chart showing distribution of research areas',
      type: 'chartjs',
      category: 'Distribution',
      icon: <PieChart size={20} />,
      data: {
        data: {
          type: 'doughnut',
          data: {
            labels: [
              'AI/Machine Learning',
              'Data Science',
              'Computer Vision',
              'Natural Language Processing',
              'Robotics',
              'Human-Computer Interaction',
              'Other'
            ],
            datasets: [{
              data: [35, 20, 15, 12, 8, 6, 4],
              backgroundColor: [
                '#3B82F6',
                '#10B981',
                '#F59E0B',
                '#EF4444',
                '#8B5CF6',
                '#06B6D4',
                '#6B7280'
              ],
              borderColor: '#1F2937',
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              title: {
                display: true,
                text: 'Research Topic Distribution',
                color: '#ffffff',
                font: { size: 16 }
              },
              legend: {
                position: 'right',
                labels: {
                  color: '#ffffff',
                  padding: 20,
                  usePointStyle: true
                }
              }
            }
          }
        },
        layout: {
          responsive: true,
          maintainAspectRatio: false
        },
        config: {
          interaction: {
            intersect: false,
            mode: 'index'
          }
        }
      }
    },
    {
      id: 'collaboration-timeline',
      title: 'Collaboration Timeline',
      description: 'Interactive timeline showing research collaboration patterns',
      type: 'plotly',
      category: 'Timeline',
      icon: <BarChart3 size={20} />,
      data: {
        data: {},
        layout: {
          title: {
            text: 'Research Collaboration Timeline',
            font: { color: '#ffffff', size: 18 }
          },
          xaxis: { 
            title: 'Timeline',
            color: '#ffffff',
            type: 'date'
          },
          yaxis: { 
            title: 'Collaborators',
            color: '#ffffff'
          },
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)'
        },
        config: { displayModeBar: true },
        traces: [
          {
            x: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
            y: ['Dr. Smith', 'Dr. Johnson', 'Dr. Brown', 'Dr. Davis', 'Dr. Wilson', 'Dr. Miller'],
            z: [[1, 0, 1, 0, 1, 0], [0, 1, 1, 1, 0, 1], [1, 1, 0, 1, 1, 0], [0, 1, 1, 0, 1, 1], [1, 0, 1, 1, 0, 1], [0, 1, 0, 1, 1, 0]],
            type: 'heatmap',
            colorscale: 'Viridis',
            showscale: true
          }
        ]
      }
    }
  ];

  const selectedVisualization = demoVisualizations.find(viz => viz.id === selectedDemo);

  // Simulate real-time data updates
  useEffect(() => {
    if (!isRealTimeEnabled || !selectedVisualization) return;

    const interval = setInterval(() => {
      if (selectedVisualization.type === 'plotly' && selectedVisualization.data.traces) {
        // Simulate updating the last data point
        const traces = selectedVisualization.data.traces;
        traces.forEach(trace => {
          if (trace.y && Array.isArray(trace.y)) {
            const lastIndex = trace.y.length - 1;
            trace.y[lastIndex] = trace.y[lastIndex] + Math.floor(Math.random() * 10) - 5;
          }
        });
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isRealTimeEnabled, selectedVisualization]);

  const handleInteraction = (event: any) => {
    console.log('Visualization interaction:', event);
    // In a real app, this would send the interaction to the backend
  };

  const handleAnnotationAdd = (annotation: any) => {
    console.log('New annotation:', annotation);
    // In a real app, this would save the annotation to the backend
  };

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Interactive Visualization Demo
          </h1>
          <p className="text-gray-400">
            Explore advanced visualization features with Plotly, D3.js, and Chart.js support
          </p>
        </div>

        {/* Controls */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setIsRealTimeEnabled(!isRealTimeEnabled)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded transition-colors ${
                    isRealTimeEnabled 
                      ? 'bg-green-600 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {isRealTimeEnabled ? <Pause size={16} /> : <Play size={16} />}
                  <span className="text-sm">Real-time</span>
                </button>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCollaborativeMode(!collaborativeMode)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded transition-colors ${
                    collaborativeMode 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <Users size={16} />
                  <span className="text-sm">Collaborative</span>
                </button>
                {collaborativeMode && (
                  <span className="text-xs text-green-400">
                    {activeUsers.length} users online
                  </span>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowAnnotations(!showAnnotations)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded transition-colors ${
                    showAnnotations 
                      ? 'bg-yellow-600 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <MessageSquare size={16} />
                  <span className="text-sm">Annotations</span>
                </button>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button className="flex items-center space-x-2 px-3 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition-colors">
                <Share2 size={16} />
                <span className="text-sm">Share</span>
              </button>
              <button className="flex items-center space-x-2 px-3 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition-colors">
                <Download size={16} />
                <span className="text-sm">Export</span>
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Visualization Selector */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-4">Visualizations</h3>
              <div className="space-y-2">
                {demoVisualizations.map((viz) => (
                  <button
                    key={viz.id}
                    onClick={() => setSelectedDemo(viz.id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedDemo === viz.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      {viz.icon}
                      <div>
                        <div className="font-medium">{viz.title}</div>
                        <div className="text-xs opacity-75">{viz.category}</div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Features List */}
              <div className="mt-6 pt-4 border-t border-gray-700">
                <h4 className="text-sm font-semibold text-white mb-3">Features</h4>
                <div className="space-y-2 text-xs text-gray-400">
                  <div className="flex items-center space-x-2">
                    <Zap size={12} className="text-yellow-400" />
                    <span>Real-time Updates</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Users size={12} className="text-blue-400" />
                    <span>Collaborative Editing</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <MessageSquare size={12} className="text-green-400" />
                    <span>Interactive Annotations</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Share2 size={12} className="text-purple-400" />
                    <span>Embedding Support</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Eye size={12} className="text-red-400" />
                    <span>Multiple Libraries</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Visualization */}
          <div className="lg:col-span-3">
            {selectedVisualization && (
              <InteractiveVisualization
                visualizationId={selectedVisualization.id}
                title={selectedVisualization.title}
                description={selectedVisualization.description}
                type={selectedVisualization.type}
                data={selectedVisualization.data}
                width={800}
                height={600}
                interactive={true}
                collaborative={collaborativeMode}
                realTimeUpdates={isRealTimeEnabled}
                showAnnotations={showAnnotations}
                showControls={true}
                onInteraction={handleInteraction}
                onAnnotationAdd={handleAnnotationAdd}
                className="w-full"
              />
            )}
          </div>
        </div>

        {/* Info Panel */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">About This Demo</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-gray-300">
            <div>
              <h4 className="font-semibold text-white mb-2">Supported Libraries</h4>
              <ul className="space-y-1">
                <li>• Plotly.js - Interactive charts and graphs</li>
                <li>• D3.js - Custom network visualizations</li>
                <li>• Chart.js - Responsive chart components</li>
                <li>• Custom - Extensible visualization framework</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">Interactive Features</h4>
              <ul className="space-y-1">
                <li>• Real-time data binding and updates</li>
                <li>• Collaborative annotation system</li>
                <li>• Multi-user session management</li>
                <li>• Interaction tracking and analytics</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">Sharing & Embedding</h4>
              <ul className="space-y-1">
                <li>• Generate embeddable HTML code</li>
                <li>• Export visualizations as images</li>
                <li>• Share with collaboration permissions</li>
                <li>• Version control and snapshots</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractiveVisualizationDemo;