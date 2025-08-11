import { Download, Maximize2, Network, Search, Settings } from 'lucide-react';
import React, { useEffect, useRef, useState } from 'react';

interface Node {
  id: string;
  label: string;
  type: 'concept' | 'document' | 'entity' | 'topic';
  size: number;
  color: string;
  connections: number;
}

interface Edge {
  id: string;
  source: string;
  target: string;
  weight: number;
  type: 'related' | 'mentions' | 'contains' | 'similar';
}

import { KnowledgeGraphProps } from '../types/ui';

// KnowledgeGraphProps is now imported from types/ui.ts
interface KnowledgeGraphUIProps extends KnowledgeGraphProps {
  onEdgeSelect?: (edgeId: string) => void;
}

export const KnowledgeGraphUI: React.FC<KnowledgeGraphUIProps> = ({
  documents,
  selectedNodes = [],
  onNodeSelect,
  onEdgeSelect
}) => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | Node['type']>('all');
  const [layoutType, setLayoutType] = useState<'force' | 'hierarchical' | 'circular'>('force');
  const [showSettings, setShowSettings] = useState(false);
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    generateGraphData();
  }, [generateGraphData]);

  useEffect(() => {
    renderGraph();
  }, [renderGraph]);

  const generateGraphData = useCallback(() => {
    const generatedNodes: Node[] = [];
    const generatedEdges: Edge[] = [];

    // Generate nodes from documents
    documents.forEach((doc) => {
      // Document node
      generatedNodes.push({
        id: `doc_${doc.id}`,
        label: doc.name,
        type: 'document',
        size: 20,
        color: '#3B82F6',
        connections: 0
      });

      // Extract concepts (mock implementation)
      const concepts = extractConcepts(doc.content);
      concepts.forEach((concept) => {
        const nodeId = `concept_${concept.toLowerCase().replace(/\s+/g, '_')}`;
        
        if (!generatedNodes.find(n => n.id === nodeId)) {
          generatedNodes.push({
            id: nodeId,
            label: concept,
            type: 'concept',
            size: 15,
            color: '#10B981',
            connections: 0
          });
        }

        // Create edge between document and concept
        generatedEdges.push({
          id: `edge_${doc.id}_${nodeId}`,
          source: `doc_${doc.id}`,
          target: nodeId,
          weight: Math.random() * 0.5 + 0.5,
          type: 'contains'
        });
      });

      // Extract entities (mock implementation)
      const entities = extractEntities(doc.content);
      entities.forEach((entity) => {
        const nodeId = `entity_${entity.toLowerCase().replace(/\s+/g, '_')}`;
        
        if (!generatedNodes.find(n => n.id === nodeId)) {
          generatedNodes.push({
            id: nodeId,
            label: entity,
            type: 'entity',
            size: 12,
            color: '#F59E0B',
            connections: 0
          });
        }

        // Create edge between document and entity
        generatedEdges.push({
          id: `edge_${doc.id}_${nodeId}`,
          source: `doc_${doc.id}`,
          target: nodeId,
          weight: Math.random() * 0.3 + 0.3,
          type: 'mentions'
        });
      });
    });

    // Create concept-to-concept relationships
    const concepts = generatedNodes.filter(n => n.type === 'concept');
    for (let i = 0; i < concepts.length; i++) {
      for (let j = i + 1; j < concepts.length; j++) {
        if (Math.random() > 0.7) { // 30% chance of connection
          generatedEdges.push({
            id: `edge_${concepts[i].id}_${concepts[j].id}`,
            source: concepts[i].id,
            target: concepts[j].id,
            weight: Math.random() * 0.4 + 0.2,
            type: 'related'
          });
        }
      }
    }

    // Update connection counts
    generatedNodes.forEach(node => {
      node.connections = generatedEdges.filter(
        edge => edge.source === node.id || edge.target === node.id
      ).length;
    });

    setNodes(generatedNodes);
    setEdges(generatedEdges);
  }, [documents]);

  const extractConcepts = (content: string): string[] => {
    // Mock concept extraction
    const concepts = [
      'Machine Learning', 'Neural Networks', 'Deep Learning', 'Artificial Intelligence',
      'Natural Language Processing', 'Computer Vision', 'Data Science', 'Algorithm',
      'Transformer', 'Attention Mechanism', 'Embedding', 'Classification'
    ];
    
    return concepts.filter(concept => 
      content.toLowerCase().includes(concept.toLowerCase())
    ).slice(0, 5);
  };

  const extractEntities = (content: string): string[] => {
    // Mock entity extraction
    const entities = [
      'BERT', 'GPT', 'ResNet', 'ImageNet', 'COCO', 'Stanford', 'MIT',
      'Google', 'OpenAI', 'Facebook', 'Microsoft', 'Amazon'
    ];
    
    return entities.filter(entity => 
      content.toLowerCase().includes(entity.toLowerCase())
    ).slice(0, 3);
  };

  const renderGraph = useCallback(() => {
    if (!svgRef.current) return;

    const svg = svgRef.current;
    const { width, height } = dimensions;

    // Clear previous content
    svg.innerHTML = '';

    // Filter nodes and edges
    const filteredNodes = nodes.filter(node => {
      const matchesFilter = filterType === 'all' || node.type === filterType;
      const matchesSearch = searchTerm === '' || 
        node.label.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesFilter && matchesSearch;
    });

    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = edges.filter(edge => 
      filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)
    );

    // Calculate positions based on layout type
    const positions = calculateLayout(filteredNodes, filteredEdges, width, height, layoutType);

    // Create SVG elements
    const svgElement = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svgElement.setAttribute('width', width.toString());
    svgElement.setAttribute('height', height.toString());

    // Add edges
    filteredEdges.forEach(edge => {
      const sourcePos = positions[edge.source];
      const targetPos = positions[edge.target];
      
      if (sourcePos && targetPos) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', sourcePos.x.toString());
        line.setAttribute('y1', sourcePos.y.toString());
        line.setAttribute('x2', targetPos.x.toString());
        line.setAttribute('y2', targetPos.y.toString());
        line.setAttribute('stroke', '#6B7280');
        line.setAttribute('stroke-width', (edge.weight * 3).toString());
        line.setAttribute('opacity', '0.6');
        line.style.cursor = 'pointer';
        
        line.addEventListener('click', () => onEdgeSelect?.(edge.id));
        
        svgElement.appendChild(line);
      }
    });

    // Add nodes
    filteredNodes.forEach(node => {
      const pos = positions[node.id];
      if (!pos) return;

      const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      group.style.cursor = 'pointer';
      
      // Node circle
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', pos.x.toString());
      circle.setAttribute('cy', pos.y.toString());
      circle.setAttribute('r', node.size.toString());
      circle.setAttribute('fill', node.color);
      circle.setAttribute('stroke', selectedNodes.includes(node.id) ? '#FFFFFF' : node.color);
      circle.setAttribute('stroke-width', selectedNodes.includes(node.id) ? '3' : '1');
      
      // Node label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', pos.x.toString());
      text.setAttribute('y', (pos.y + node.size + 15).toString());
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('fill', '#FFFFFF');
      text.setAttribute('font-size', '12');
      text.setAttribute('font-family', 'Arial, sans-serif');
      text.textContent = node.label.length > 15 ? node.label.substring(0, 15) + '...' : node.label;
      
      group.appendChild(circle);
      group.appendChild(text);
      
      group.addEventListener('click', () => onNodeSelect?.(node.id));
      
      svgElement.appendChild(group);
    });

    svg.appendChild(svgElement);
  }, [nodes, edges, layoutType, filterType, searchTerm, dimensions]);

  const calculateLayout = (
    nodes: Node[], 
    edges: Edge[], 
    width: number, 
    height: number, 
    layout: string
  ): Record<string, { x: number; y: number }> => {
    const positions: Record<string, { x: number; y: number }> = {};

    switch (layout) {
      case 'circular':
        nodes.forEach((node, index) => {
          const angle = (2 * Math.PI * index) / nodes.length;
          const radius = Math.min(width, height) * 0.3;
          positions[node.id] = {
            x: width / 2 + radius * Math.cos(angle),
            y: height / 2 + radius * Math.sin(angle)
          };
        });
        break;

      case 'hierarchical':
        const levels = new Map<string, number>();
        const documentNodes = nodes.filter(n => n.type === 'document');
        const conceptNodes = nodes.filter(n => n.type === 'concept');
        const entityNodes = nodes.filter(n => n.type === 'entity');

        documentNodes.forEach((node, index) => {
          positions[node.id] = {
            x: (width / (documentNodes.length + 1)) * (index + 1),
            y: height * 0.2
          };
        });

        conceptNodes.forEach((node, index) => {
          positions[node.id] = {
            x: (width / (conceptNodes.length + 1)) * (index + 1),
            y: height * 0.5
          };
        });

        entityNodes.forEach((node, index) => {
          positions[node.id] = {
            x: (width / (entityNodes.length + 1)) * (index + 1),
            y: height * 0.8
          };
        });
        break;

      default: // force-directed
        // Simple force-directed layout simulation
        nodes.forEach((node, index) => {
          positions[node.id] = {
            x: Math.random() * (width - 100) + 50,
            y: Math.random() * (height - 100) + 50
          };
        });

        // Simple force simulation (simplified)
        for (let iteration = 0; iteration < 50; iteration++) {
          // Repulsion between nodes
          nodes.forEach(nodeA => {
            nodes.forEach(nodeB => {
              if (nodeA.id !== nodeB.id) {
                const posA = positions[nodeA.id];
                const posB = positions[nodeB.id];
                const dx = posA.x - posB.x;
                const dy = posA.y - posB.y;
                const distance = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = 1000 / (distance * distance);
                
                posA.x += (dx / distance) * force * 0.1;
                posA.y += (dy / distance) * force * 0.1;
              }
            });
          });

          // Attraction along edges
          edges.forEach(edge => {
            const sourcePos = positions[edge.source];
            const targetPos = positions[edge.target];
            if (sourcePos && targetPos) {
              const dx = targetPos.x - sourcePos.x;
              const dy = targetPos.y - sourcePos.y;
              const distance = Math.sqrt(dx * dx + dy * dy) || 1;
              const force = distance * 0.01 * edge.weight;
              
              sourcePos.x += (dx / distance) * force;
              sourcePos.y += (dy / distance) * force;
              targetPos.x -= (dx / distance) * force;
              targetPos.y -= (dy / distance) * force;
            }
          });

          // Keep nodes within bounds
          nodes.forEach(node => {
            const pos = positions[node.id];
            pos.x = Math.max(50, Math.min(width - 50, pos.x));
            pos.y = Math.max(50, Math.min(height - 50, pos.y));
          });
        }
        break;
    }

    return positions;
  };

  const exportGraph = () => {
    const graphData = {
      nodes: nodes.filter(node => {
        const matchesFilter = filterType === 'all' || node.type === filterType;
        const matchesSearch = searchTerm === '' || 
          node.label.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesFilter && matchesSearch;
      }),
      edges: edges.filter(edge => {
        const filteredNodeIds = new Set(nodes.map(n => n.id));
        return filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target);
      })
    };

    const dataStr = JSON.stringify(graphData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'knowledge_graph.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Network className="text-purple-400" size={24} />
          <div>
            <h3 className="text-lg font-semibold text-white">Knowledge Graph</h3>
            <p className="text-sm text-gray-400">
              {nodes.length} nodes, {edges.length} connections
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <Settings size={16} />
          </button>
          <button
            onClick={exportGraph}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <Download size={16} />
          </button>
          <button
            onClick={() => setDimensions({ width: window.innerWidth - 100, height: window.innerHeight - 100 })}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <Maximize2 size={16} />
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center space-x-4 mb-4">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search nodes..."
            className="w-full bg-gray-700 border border-gray-600 rounded-lg pl-10 pr-4 py-2 text-white"
          />
        </div>

        {/* Filter */}
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as any)}
          className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
        >
          <option value="all">All Types</option>
          <option value="document">Documents</option>
          <option value="concept">Concepts</option>
          <option value="entity">Entities</option>
          <option value="topic">Topics</option>
        </select>

        {/* Layout */}
        <select
          value={layoutType}
          onChange={(e) => setLayoutType(e.target.value as any)}
          className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
        >
          <option value="force">Force-Directed</option>
          <option value="hierarchical">Hierarchical</option>
          <option value="circular">Circular</option>
        </select>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="mb-4 p-4 bg-gray-700 rounded-lg">
          <h4 className="text-white font-medium mb-3">Graph Settings</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Node Size</label>
              <input
                type="range"
                min="5"
                max="30"
                defaultValue="15"
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Edge Thickness</label>
              <input
                type="range"
                min="1"
                max="5"
                defaultValue="2"
                className="w-full"
              />
            </div>
          </div>
        </div>
      )}

      {/* Graph Visualization */}
      <div className="flex-1 bg-gray-900 rounded-lg overflow-hidden">
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="w-full h-full"
        />
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center space-x-6 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
          <span className="text-gray-400">Documents</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-emerald-500 rounded-full"></div>
          <span className="text-gray-400">Concepts</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
          <span className="text-gray-400">Entities</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
          <span className="text-gray-400">Topics</span>
        </div>
      </div>
    </div>
  );
};