/**
 * Interactive Visualization Component for AI Scholar Advanced RAG System
 * 
 * This component provides comprehensive support for interactive visualizations
 * including Plotly, D3.js, Chart.js, and other visualization libraries with
 * real-time updates, collaborative annotations, and embedding capabilities.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Play, Pause, Share2, MessageSquare, Download, Settings,
  Maximize2, Minimize2, Users, Eye, EyeOff, Edit3, Save,
  RotateCcw, Zap, Code, Image, FileText, Link, Copy
} from 'lucide-react';

// Mock D3 and Chart.js for now - in production, install proper packages
const d3 = {
  select: () => ({
    selectAll: () => ({ remove: () => {} }),
    append: () => ({ attr: () => ({ attr: () => ({}) }) }),
    selectAll: () => ({ data: () => ({ enter: () => ({ append: () => ({ attr: () => ({ attr: () => ({ call: () => {} }) }) }) }) }) })
  }),
  forceSimulation: () => ({ force: () => ({ force: () => ({ force: () => ({}) }) }) }),
  forceLink: () => ({ id: () => ({}) }),
  forceManyBody: () => ({ strength: () => ({}) }),
  forceCenter: () => ({}),
  schemeCategory10: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
  drag: () => ({ on: () => ({}) })
} as any;

const Chart = class {
  constructor(ctx: any, config: any) {
    // Mock Chart.js constructor
  }
} as any;

// Mock Plotly
const Plotly = {
  newPlot: async () => {},
  on: () => {}
} as any;

// Types for visualization data
interface VisualizationData {
  data: Record<string, any>;
  layout: Record<string, any>;
  config: Record<string, any>;
  traces?: Array<Record<string, any>>;
}

interface Annotation {
  annotation_id: string;
  user_id: string;
  content: string;
  position: { x: number; y: number };
  annotation_type: 'text' | 'arrow' | 'shape' | 'highlight';
  style: Record<string, any>;
  created_at: string;
  modified_at: string;
  replies: string[];
}

interface InteractionEvent {
  event_id: string;
  interaction_type: 'click' | 'hover' | 'zoom' | 'pan' | 'select' | 'brush' | 'filter';
  data: Record<string, any>;
  coordinates?: { x: number; y: number };
  timestamp: string;
}

interface VisualizationProps {
  visualizationId?: string;
  title: string;
  description?: string;
  type: 'plotly' | 'd3' | 'chartjs' | 'custom';
  data: VisualizationData;
  width?: number;
  height?: number;
  interactive?: boolean;
  collaborative?: boolean;
  realTimeUpdates?: boolean;
  showAnnotations?: boolean;
  showControls?: boolean;
  onDataUpdate?: (data: VisualizationData) => void;
  onInteraction?: (event: InteractionEvent) => void;
  onAnnotationAdd?: (annotation: Omit<Annotation, 'annotation_id' | 'created_at' | 'modified_at'>) => void;
  className?: string;
}

export const InteractiveVisualization: React.FC<VisualizationProps> = ({
  visualizationId,
  title,
  description,
  type,
  data,
  width = 800,
  height = 600,
  interactive = true,
  collaborative = false,
  realTimeUpdates = false,
  showAnnotations = true,
  showControls = true,
  onDataUpdate,
  onInteraction,
  onAnnotationAdd,
  className = ''
}) => {
  // State management
  const [isPlaying, setIsPlaying] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [activeUsers, setActiveUsers] = useState<string[]>([]);
  const [isAnnotating, setIsAnnotating] = useState(false);
  const [annotationMode, setAnnotationMode] = useState<'text' | 'arrow' | 'shape' | 'highlight'>('text');
  const [selectedAnnotation, setSelectedAnnotation] = useState<string | null>(null);
  const [interactionHistory, setInteractionHistory] = useState<InteractionEvent[]>([]);
  const [embedCode, setEmbedCode] = useState<string>('');
  const [showEmbedDialog, setShowEmbedDialog] = useState(false);

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const plotlyRef = useRef<HTMLDivElement>(null);
  const d3Ref = useRef<HTMLDivElement>(null);
  const chartjsRef = useRef<HTMLCanvasElement>(null);
  const annotationLayerRef = useRef<HTMLDivElement>(null);

  // Load external libraries dynamically
  const loadPlotly = useCallback(async () => {
    if ((window as any).Plotly) return (window as any).Plotly;
    
    // Return our mock Plotly for now
    return Plotly;
  }, []);

  const loadD3 = useCallback(async () => {
    if (window.d3) return window.d3;
    
    const script = document.createElement('script');
    script.src = 'https://d3js.org/d3.v7.min.js';
    document.head.appendChild(script);
    
    return new Promise((resolve) => {
      script.onload = () => resolve(window.d3);
    });
  }, []);

  const loadChartJS = useCallback(async () => {
    if (window.Chart) return window.Chart;
    
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js';
    document.head.appendChild(script);
    
    return new Promise((resolve) => {
      script.onload = () => resolve(window.Chart);
    });
  }, []);

  // Render visualization based on type
  const renderVisualization = useCallback(async () => {
    if (!containerRef.current) return;

    try {
      switch (type) {
        case 'plotly':
          await renderPlotlyVisualization();
          break;
        case 'd3':
          await renderD3Visualization();
          break;
        case 'chartjs':
          await renderChartJSVisualization();
          break;
        case 'custom':
          await renderCustomVisualization();
          break;
      }
    } catch (error) {
      console.error('Error rendering visualization:', error);
    }
  }, [type, data, width, height]);

  const renderPlotlyVisualization = async () => {
    const Plotly = await loadPlotly();
    if (!plotlyRef.current || !Plotly) return;

    const config = {
      displayModeBar: interactive,
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
      ...data.config
    };

    const layout = {
      width,
      height,
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { color: '#ffffff' },
      ...data.layout
    };

    await Plotly.newPlot(plotlyRef.current, data.traces || [data.data], layout, config);

    // Add interaction listeners
    if (interactive && onInteraction && plotlyRef.current) {
      (plotlyRef.current as any).on('plotly_click', (eventData: any) => {
        const event: InteractionEvent = {
          event_id: `${Date.now()}-click`,
          interaction_type: 'click',
          data: eventData,
          coordinates: eventData.points?.[0] ? {
            x: eventData.points[0].x,
            y: eventData.points[0].y
          } : undefined,
          timestamp: new Date().toISOString()
        };
        onInteraction(event);
        setInteractionHistory(prev => [...prev, event]);
      });

      (plotlyRef.current as any).on('plotly_hover', (eventData: any) => {
        const event: InteractionEvent = {
          event_id: `${Date.now()}-hover`,
          interaction_type: 'hover',
          data: eventData,
          timestamp: new Date().toISOString()
        };
        onInteraction(event);
      });
    }
  };

  const renderD3Visualization = async () => {
    const d3 = await loadD3();
    if (!d3Ref.current || !d3) return;

    // Clear previous visualization
    d3.select(d3Ref.current).selectAll('*').remove();

    const svg = d3.select(d3Ref.current)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('background', 'transparent');

    // Example D3 visualization (can be customized based on data)
    if (data.data.nodes && data.data.links) {
      // Network graph
      const simulation = d3.forceSimulation(data.data.nodes)
        .force('link', d3.forceLink(data.data.links).id((d: any) => d.id))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));

      const link = svg.append('g')
        .selectAll('line')
        .data(data.data.links)
        .enter().append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', (d: any) => Math.sqrt(d.value || 1));

      const node = svg.append('g')
        .selectAll('circle')
        .data(data.data.nodes)
        .enter().append('circle')
        .attr('r', 5)
        .attr('fill', (d: any) => d3.schemeCategory10[d.group % 10])
        .call(d3.drag()
          .on('start', (event: any, d: any) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event: any, d: any) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event: any, d: any) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }));

      simulation.on('tick', () => {
        link
          .attr('x1', (d: any) => d.source.x)
          .attr('y1', (d: any) => d.source.y)
          .attr('x2', (d: any) => d.target.x)
          .attr('y2', (d: any) => d.target.y);

        node
          .attr('cx', (d: any) => d.x)
          .attr('cy', (d: any) => d.y);
      });

      // Add interaction listeners
      if (interactive && onInteraction) {
        node.on('click', (event: any, d: any) => {
          const interactionEvent: InteractionEvent = {
            event_id: `${Date.now()}-click`,
            interaction_type: 'click',
            data: { node: d },
            coordinates: { x: event.x, y: event.y },
            timestamp: new Date().toISOString()
          };
          onInteraction(interactionEvent);
          setInteractionHistory(prev => [...prev, interactionEvent]);
        });
      }
    }
  };

  const renderChartJSVisualization = async () => {
    const Chart = await loadChartJS();
    if (!chartjsRef.current || !Chart) return;

    const ctx = chartjsRef.current.getContext('2d');
    if (!ctx) return;

    new Chart(ctx, {
      type: data.data.type || 'line',
      data: data.data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#ffffff'
            }
          }
        },
        scales: {
          x: {
            ticks: { color: '#ffffff' },
            grid: { color: 'rgba(255,255,255,0.1)' }
          },
          y: {
            ticks: { color: '#ffffff' },
            grid: { color: 'rgba(255,255,255,0.1)' }
          }
        },
        onClick: interactive && onInteraction ? (event: any, elements: any) => {
          const interactionEvent: InteractionEvent = {
            event_id: `${Date.now()}-click`,
            interaction_type: 'click',
            data: { elements },
            coordinates: { x: event.x, y: event.y },
            timestamp: new Date().toISOString()
          };
          onInteraction(interactionEvent);
          setInteractionHistory(prev => [...prev, interactionEvent]);
        } : undefined,
        ...data.config
      }
    });
  };

  const renderCustomVisualization = async () => {
    // Placeholder for custom visualization rendering
    if (!containerRef.current) return;
    
    containerRef.current.innerHTML = `
      <div class="flex items-center justify-center h-full text-gray-400">
        <div class="text-center">
          <div class="text-4xl mb-4">📊</div>
          <h3 class="text-lg font-semibold mb-2">${title}</h3>
          <p class="text-sm">${description || 'Custom visualization'}</p>
          <pre class="mt-4 text-xs bg-gray-800 p-4 rounded overflow-auto max-w-md">
${JSON.stringify(data.data, null, 2)}
          </pre>
        </div>
      </div>
    `;
  };

  // Handle annotation creation
  const handleAnnotationClick = (event: React.MouseEvent) => {
    if (!isAnnotating || !onAnnotationAdd) return;

    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const annotation: Omit<Annotation, 'annotation_id' | 'created_at' | 'modified_at'> = {
      user_id: 'current_user', // This would come from auth context
      content: 'New annotation',
      position: { x, y },
      annotation_type: annotationMode,
      style: {
        color: '#3B82F6',
        fontSize: 14,
        backgroundColor: 'rgba(59, 130, 246, 0.1)'
      },
      replies: []
    };

    onAnnotationAdd(annotation);
    setIsAnnotating(false);
  };

  // Generate embed code
  const generateEmbedCode = () => {
    const embedHtml = `
<div id="visualization-${visualizationId}" style="width:${width}px;height:${height}px;"></div>
<script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
<script>
  var data = ${JSON.stringify(data.traces || [data.data])};
  var layout = ${JSON.stringify({ ...data.layout, width, height })};
  var config = ${JSON.stringify({ ...data.config, displayModeBar: interactive })};
  
  Plotly.newPlot('visualization-${visualizationId}', data, layout, config);
</script>
    `.trim();
    
    setEmbedCode(embedHtml);
    setShowEmbedDialog(true);
  };

  // Copy embed code to clipboard
  const copyEmbedCode = async () => {
    try {
      await navigator.clipboard.writeText(embedCode);
      // Show success message (could use a toast notification)
    } catch (error) {
      console.error('Failed to copy embed code:', error);
    }
  };

  // Real-time updates effect
  useEffect(() => {
    if (realTimeUpdates && visualizationId) {
      // Set up WebSocket or polling for real-time updates
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`/api/visualizations/${visualizationId}/updates`);
          const updates = await response.json();
          
          if (updates.updates && updates.updates.length > 0) {
            // Apply updates to visualization
            renderVisualization();
          }
        } catch (error) {
          console.error('Error fetching updates:', error);
        }
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [realTimeUpdates, visualizationId, renderVisualization]);

  // Initial render effect
  useEffect(() => {
    renderVisualization();
  }, [renderVisualization]);

  return (
    <div className={`bg-gray-800 rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      {showControls && (
        <div className="bg-gray-900 px-4 py-3 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <h3 className="text-lg font-semibold text-white">{title}</h3>
              {description && (
                <span className="text-sm text-gray-400">{description}</span>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              {/* Real-time controls */}
              {realTimeUpdates && (
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="p-2 text-gray-400 hover:text-white transition-colors"
                  title={isPlaying ? 'Pause updates' : 'Resume updates'}
                >
                  {isPlaying ? <Pause size={16} /> : <Play size={16} />}
                </button>
              )}

              {/* Annotation controls */}
              {showAnnotations && (
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => setIsAnnotating(!isAnnotating)}
                    className={`p-2 transition-colors ${
                      isAnnotating 
                        ? 'text-blue-400 bg-blue-400/20' 
                        : 'text-gray-400 hover:text-white'
                    }`}
                    title="Add annotation"
                  >
                    <MessageSquare size={16} />
                  </button>
                  
                  {isAnnotating && (
                    <select
                      value={annotationMode}
                      onChange={(e) => setAnnotationMode(e.target.value as any)}
                      className="bg-gray-700 text-white text-xs px-2 py-1 rounded"
                    >
                      <option value="text">Text</option>
                      <option value="arrow">Arrow</option>
                      <option value="shape">Shape</option>
                      <option value="highlight">Highlight</option>
                    </select>
                  )}
                </div>
              )}

              {/* Collaboration indicator */}
              {collaborative && activeUsers.length > 0 && (
                <div className="flex items-center space-x-1 text-green-400">
                  <Users size={16} />
                  <span className="text-xs">{activeUsers.length}</span>
                </div>
              )}

              {/* Share and embed */}
              <button
                onClick={generateEmbedCode}
                className="p-2 text-gray-400 hover:text-white transition-colors"
                title="Generate embed code"
              >
                <Share2 size={16} />
              </button>

              {/* Settings */}
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 text-gray-400 hover:text-white transition-colors"
                title="Settings"
              >
                <Settings size={16} />
              </button>

              {/* Fullscreen */}
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-2 text-gray-400 hover:text-white transition-colors"
                title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
              >
                {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Visualization Container */}
      <div 
        ref={containerRef}
        className={`relative ${isFullscreen ? 'fixed inset-0 z-50 bg-gray-800' : ''}`}
        style={{ width, height }}
        onClick={handleAnnotationClick}
      >
        {/* Plotly container */}
        {type === 'plotly' && (
          <div ref={plotlyRef} className="w-full h-full" />
        )}

        {/* D3 container */}
        {type === 'd3' && (
          <div ref={d3Ref} className="w-full h-full" />
        )}

        {/* Chart.js container */}
        {type === 'chartjs' && (
          <canvas ref={chartjsRef} className="w-full h-full" />
        )}

        {/* Annotation layer */}
        {showAnnotations && (
          <div 
            ref={annotationLayerRef}
            className="absolute inset-0 pointer-events-none"
          >
            {annotations.map((annotation) => (
              <div
                key={annotation.annotation_id}
                className="absolute pointer-events-auto"
                style={{
                  left: annotation.position.x,
                  top: annotation.position.y,
                  transform: 'translate(-50%, -50%)'
                }}
              >
                <div 
                  className="bg-blue-500 text-white text-xs px-2 py-1 rounded shadow-lg cursor-pointer"
                  onClick={() => setSelectedAnnotation(annotation.annotation_id)}
                >
                  {annotation.content}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Annotation cursor */}
        {isAnnotating && (
          <div className="absolute inset-0 cursor-crosshair bg-blue-500/5" />
        )}
      </div>

      {/* Embed Dialog */}
      {showEmbedDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Embed Code</h3>
              <button
                onClick={() => setShowEmbedDialog(false)}
                className="text-gray-400 hover:text-white"
              >
                ×
              </button>
            </div>
            
            <textarea
              value={embedCode}
              readOnly
              className="w-full h-40 bg-gray-900 text-white text-sm p-3 rounded border border-gray-600 font-mono"
            />
            
            <div className="flex justify-end space-x-2 mt-4">
              <button
                onClick={copyEmbedCode}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <Copy size={16} />
                <span>Copy Code</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveVisualization;