/**
 * WorkflowBuilder - Visual workflow creation and editing interface
 * Implements drag-and-drop functionality for building workflows
 */
import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Plus,
  Save,
  Play,
  Settings,
  Trash2,
  Copy,
  Undo,
  Redo,
  ZoomIn,
  ZoomOut,
  Grid,
  Download,
  Upload,
  Eye,
  EyeOff,
  Move,
  MousePointer,
  Square,
  Circle,
  ArrowRight,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Zap,
  Filter,
  Database,
  Mail,
  Webhook,
  Code,
  FileText,
  Tag,
  Share2
} from 'lucide-react';
import type {
  WorkflowDefinition,
  WorkflowNode,
  WorkflowConnection,
  WorkflowCanvas,
  WorkflowTrigger,
  WorkflowCondition,
  WorkflowAction,
  WorkflowTemplate
} from '../../../types/workflow';
import { WorkflowManagementService } from '../../../services/workflowManagementService';

export interface WorkflowBuilderProps {
  workflowId?: string;
  template?: WorkflowTemplate;
  onSave?: (workflow: WorkflowDefinition) => void;
  onCancel?: () => void;
  onTest?: (workflow: WorkflowDefinition) => void;
  readOnly?: boolean;
}

interface DragState {
  isDragging: boolean;
  dragType: 'node' | 'canvas' | 'connection' | null;
  dragData: any;
  startPosition: { x: number; y: number };
  currentPosition: { x: number; y: number };
}

interface SelectionState {
  selectedNodes: string[];
  selectedConnections: string[];
  selectionBox?: {
    start: { x: number; y: number };
    end: { x: number; y: number };
  };
}

const workflowService = new WorkflowManagementService();

export const WorkflowBuilder: React.FC<WorkflowBuilderProps> = ({
  workflowId,
  template,
  onSave,
  onCancel,
  onTest,
  readOnly = false
}) => {
  // Core state
  const [workflow, setWorkflow] = useState<Partial<WorkflowDefinition>>({
    name: template?.name || 'New Workflow',
    description: template?.description || '',
    status: 'draft',
    triggers: template?.definition.triggers || [],
    conditions: template?.definition.conditions || [],
    actions: template?.definition.actions || [],
    tags: template?.definition.tags || []
  });

  const [canvas, setCanvas] = useState<WorkflowCanvas>({
    nodes: [],
    connections: [],
    zoom: 1,
    pan: { x: 0, y: 0 }
  });

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    dragType: null,
    dragData: null,
    startPosition: { x: 0, y: 0 },
    currentPosition: { x: 0, y: 0 }
  });
  const [selection, setSelection] = useState<SelectionState>({
    selectedNodes: [],
    selectedConnections: []
  });
  const [showGrid, setShowGrid] = useState(true);
  const [snapToGrid, setSnapToGrid] = useState(true);
  const [tool, setTool] = useState<'select' | 'pan' | 'connect'>('select');

  // Refs
  const canvasRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // History for undo/redo
  const [history, setHistory] = useState<WorkflowCanvas[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Load existing workflow
  useEffect(() => {
    if (workflowId) {
      loadWorkflow();
    } else if (template) {
      initializeFromTemplate();
    }
  }, [workflowId, template]);

  const loadWorkflow = async () => {
    if (!workflowId) return;
    
    try {
      setLoading(true);
      const workflowData = await workflowService.getWorkflow(workflowId);
      setWorkflow(workflowData);
      
      // Convert workflow to canvas format
      const nodes = convertWorkflowToNodes(workflowData);
      const connections = generateConnections(nodes);
      
      setCanvas({
        nodes,
        connections,
        zoom: 1,
        pan: { x: 0, y: 0 }
      });
      
      addToHistory({ nodes, connections, zoom: 1, pan: { x: 0, y: 0 } });
    } catch (err) {
      setError('Failed to load workflow');
      console.error('Failed to load workflow:', err);
    } finally {
      setLoading(false);
    }
  };

  const initializeFromTemplate = () => {
    if (!template) return;
    
    const nodes = convertWorkflowToNodes(template.definition);
    const connections = generateConnections(nodes);
    
    setCanvas({
      nodes,
      connections,
      zoom: 1,
      pan: { x: 0, y: 0 }
    });
    
    addToHistory({ nodes, connections, zoom: 1, pan: { x: 0, y: 0 } });
  };

  const convertWorkflowToNodes = (workflowData: Partial<WorkflowDefinition>): WorkflowNode[] => {
    const nodes: WorkflowNode[] = [];
    let yOffset = 100;
    
    // Add trigger nodes
    workflowData.triggers?.forEach((trigger, index) => {
      nodes.push({
        id: `trigger_${trigger.id}`,
        type: 'trigger',
        position: { x: 100, y: yOffset + (index * 120) },
        data: trigger,
        connections: []
      });
    });
    
    // Add condition nodes
    workflowData.conditions?.forEach((condition, index) => {
      nodes.push({
        id: `condition_${condition.id}`,
        type: 'condition',
        position: { x: 350, y: yOffset + (index * 120) },
        data: condition,
        connections: []
      });
    });
    
    // Add action nodes
    workflowData.actions?.forEach((action, index) => {
      nodes.push({
        id: `action_${action.id}`,
        type: 'action',
        position: { x: 600, y: yOffset + (index * 120) },
        data: action,
        connections: []
      });
    });
    
    return nodes;
  };

  const generateConnections = (nodes: WorkflowNode[]): WorkflowConnection[] => {
    const connections: WorkflowConnection[] = [];
    
    // Simple linear connection for now
    for (let i = 0; i < nodes.length - 1; i++) {
      connections.push({
        id: `conn_${i}`,
        sourceNodeId: nodes[i].id,
        targetNodeId: nodes[i + 1].id,
        type: 'success'
      });
    }
    
    return connections;
  };

  const addToHistory = (canvasState: WorkflowCanvas) => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push({ ...canvasState });
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  };

  const undo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      setCanvas({ ...history[historyIndex - 1] });
    }
  };

  const redo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      setCanvas({ ...history[historyIndex + 1] });
    }
  };

  // Node type configurations
  const nodeTypes = {
    trigger: {
      icon: Zap,
      color: 'bg-green-500',
      borderColor: 'border-green-400',
      textColor: 'text-green-100',
      types: [
        { type: 'manual', label: 'Manual Trigger', icon: MousePointer },
        { type: 'schedule', label: 'Scheduled', icon: Clock },
        { type: 'document_upload', label: 'Document Upload', icon: FileText },
        { type: 'api_call', label: 'API Call', icon: Code },
        { type: 'webhook', label: 'Webhook', icon: Webhook }
      ]
    },
    condition: {
      icon: Filter,
      color: 'bg-yellow-500',
      borderColor: 'border-yellow-400',
      textColor: 'text-yellow-100',
      types: [
        { type: 'document_size', label: 'Document Size', icon: FileText },
        { type: 'document_type', label: 'Document Type', icon: Tag },
        { type: 'user_role', label: 'User Role', icon: Share2 },
        { type: 'time_of_day', label: 'Time of Day', icon: Clock },
        { type: 'custom', label: 'Custom Logic', icon: Code }
      ]
    },
    action: {
      icon: Settings,
      color: 'bg-blue-500',
      borderColor: 'border-blue-400',
      textColor: 'text-blue-100',
      types: [
        { type: 'auto_tag', label: 'Auto Tag', icon: Tag },
        { type: 'send_notification', label: 'Send Notification', icon: Mail },
        { type: 'generate_summary', label: 'Generate Summary', icon: FileText },
        { type: 'update_metadata', label: 'Update Metadata', icon: Database },
        { type: 'create_backup', label: 'Create Backup', icon: Copy },
        { type: 'api_call', label: 'API Call', icon: Code },
        { type: 'transform_data', label: 'Transform Data', icon: Settings }
      ]
    }
  };

  // Drag and drop handlers
  const handleMouseDown = useCallback((e: React.MouseEvent, type: 'node' | 'canvas', data?: any) => {
    if (readOnly) return;
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setDragState({
      isDragging: true,
      dragType: type,
      dragData: data,
      startPosition: { x, y },
      currentPosition: { x, y }
    });
  }, [readOnly]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragState.isDragging) return;
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setDragState(prev => ({
      ...prev,
      currentPosition: { x, y }
    }));
    
    if (dragState.dragType === 'node' && dragState.dragData) {
      // Update node position
      const deltaX = x - dragState.startPosition.x;
      const deltaY = y - dragState.startPosition.y;
      
      setCanvas(prev => ({
        ...prev,
        nodes: prev.nodes.map(node =>
          node.id === dragState.dragData.id
            ? {
                ...node,
                position: {
                  x: node.position.x + deltaX,
                  y: node.position.y + deltaY
                }
              }
            : node
        )
      }));
      
      setDragState(prev => ({
        ...prev,
        startPosition: { x, y }
      }));
    } else if (dragState.dragType === 'canvas') {
      // Pan canvas
      const deltaX = x - dragState.startPosition.x;
      const deltaY = y - dragState.startPosition.y;
      
      setCanvas(prev => ({
        ...prev,
        pan: {
          x: prev.pan.x + deltaX,
          y: prev.pan.y + deltaY
        }
      }));
      
      setDragState(prev => ({
        ...prev,
        startPosition: { x, y }
      }));
    }
  }, [dragState]);

  const handleMouseUp = useCallback(() => {
    if (dragState.isDragging) {
      addToHistory(canvas);
      setDragState({
        isDragging: false,
        dragType: null,
        dragData: null,
        startPosition: { x: 0, y: 0 },
        currentPosition: { x: 0, y: 0 }
      });
    }
  }, [dragState.isDragging, canvas]);

  // Add event listeners
  useEffect(() => {
    const handleGlobalMouseMove = (e: MouseEvent) => {
      if (dragState.isDragging) {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;
        
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        setDragState(prev => ({
          ...prev,
          currentPosition: { x, y }
        }));
      }
    };

    const handleGlobalMouseUp = () => {
      if (dragState.isDragging) {
        handleMouseUp();
      }
    };

    if (dragState.isDragging) {
      document.addEventListener('mousemove', handleGlobalMouseMove);
      document.addEventListener('mouseup', handleGlobalMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleGlobalMouseMove);
      document.removeEventListener('mouseup', handleGlobalMouseUp);
    };
  }, [dragState.isDragging, handleMouseUp]);

  // Node creation
  const createNode = useCallback((nodeType: 'trigger' | 'condition' | 'action', subType: string, position: { x: number; y: number }) => {
    const id = `${nodeType}_${Date.now()}`;
    
    let data: WorkflowTrigger | WorkflowCondition | WorkflowAction;
    
    switch (nodeType) {
      case 'trigger':
        data = {
          id,
          type: subType as WorkflowTrigger['type'],
          config: {},
          enabled: true
        };
        break;
      case 'condition':
        data = {
          id,
          type: subType as WorkflowCondition['type'],
          operator: 'equals',
          value: ''
        };
        break;
      case 'action':
        data = {
          id,
          type: subType as WorkflowAction['type'],
          name: nodeTypes[nodeType].types.find(t => t.type === subType)?.label || subType,
          config: {},
          enabled: true,
          order: canvas.nodes.filter(n => n.type === 'action').length + 1
        };
        break;
    }
    
    const newNode: WorkflowNode = {
      id,
      type: nodeType,
      position: snapToGrid ? {
        x: Math.round(position.x / 20) * 20,
        y: Math.round(position.y / 20) * 20
      } : position,
      data,
      connections: []
    };
    
    setCanvas(prev => ({
      ...prev,
      nodes: [...prev.nodes, newNode]
    }));
    
    // Update workflow definition
    setWorkflow(prev => {
      const updated = { ...prev };
      switch (nodeType) {
        case 'trigger':
          updated.triggers = [...(updated.triggers || []), data as WorkflowTrigger];
          break;
        case 'condition':
          updated.conditions = [...(updated.conditions || []), data as WorkflowCondition];
          break;
        case 'action':
          updated.actions = [...(updated.actions || []), data as WorkflowAction];
          break;
      }
      return updated;
    });
    
    addToHistory({
      ...canvas,
      nodes: [...canvas.nodes, newNode]
    });
  }, [canvas, snapToGrid]);

  // Save workflow
  const handleSave = async () => {
    if (!workflow.name?.trim()) {
      setError('Workflow name is required');
      return;
    }
    
    try {
      setLoading(true);
      
      const workflowData: Partial<WorkflowDefinition> = {
        ...workflow,
        triggers: workflow.triggers || [],
        conditions: workflow.conditions || [],
        actions: workflow.actions || [],
        tags: workflow.tags || [],
        version: (workflow.version || 0) + 1,
        isTemplate: false
      };
      
      let savedWorkflow: WorkflowDefinition;
      
      if (workflowId) {
        savedWorkflow = await workflowService.updateWorkflow(workflowId, workflowData);
      } else {
        savedWorkflow = await workflowService.createWorkflow(workflowData as Omit<WorkflowDefinition, 'id' | 'createdAt' | 'updatedAt'>);
      }
      
      setWorkflow(savedWorkflow);
      onSave?.(savedWorkflow);
      setError(null);
    } catch (err) {
      setError('Failed to save workflow');
      console.error('Failed to save workflow:', err);
    } finally {
      setLoading(false);
    }
  };

  // Test workflow
  const handleTest = async () => {
    if (!workflow.name?.trim()) {
      setError('Please save the workflow before testing');
      return;
    }
    
    try {
      setLoading(true);
      
      if (workflowId) {
        await workflowService.executeWorkflow(workflowId, { test: true });
      }
      
      onTest?.(workflow as WorkflowDefinition);
    } catch (err) {
      setError('Failed to test workflow');
      console.error('Failed to test workflow:', err);
    } finally {
      setLoading(false);
    }
  };

  // Zoom controls
  const handleZoom = (delta: number) => {
    setCanvas(prev => ({
      ...prev,
      zoom: Math.max(0.1, Math.min(3, prev.zoom + delta))
    }));
  };

  // Reset canvas view
  const resetView = () => {
    setCanvas(prev => ({
      ...prev,
      zoom: 1,
      pan: { x: 0, y: 0 }
    }));
  };

  if (loading && !canvas.nodes.length) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900 text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading workflow...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center space-x-4">
          <input
            type="text"
            value={workflow.name || ''}
            onChange={(e) => setWorkflow(prev => ({ ...prev, name: e.target.value }))}
            className="text-xl font-semibold bg-transparent border-none outline-none text-white placeholder-gray-400"
            placeholder="Workflow Name"
            disabled={readOnly}
          />
          <span className="text-sm text-gray-400">
            {workflow.status === 'draft' ? 'Draft' : workflow.status}
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Tool selection */}
          <div className="flex items-center space-x-1 bg-gray-700 rounded p-1">
            <button
              onClick={() => setTool('select')}
              className={`p-2 rounded ${tool === 'select' ? 'bg-blue-600' : 'hover:bg-gray-600'}`}
              title="Select Tool"
            >
              <MousePointer className="w-4 h-4" />
            </button>
            <button
              onClick={() => setTool('pan')}
              className={`p-2 rounded ${tool === 'pan' ? 'bg-blue-600' : 'hover:bg-gray-600'}`}
              title="Pan Tool"
            >
              <Move className="w-4 h-4" />
            </button>
          </div>
          
          {/* View controls */}
          <div className="flex items-center space-x-1 bg-gray-700 rounded p-1">
            <button
              onClick={() => handleZoom(-0.1)}
              className="p-2 hover:bg-gray-600 rounded"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="px-2 text-sm">{Math.round(canvas.zoom * 100)}%</span>
            <button
              onClick={() => handleZoom(0.1)}
              className="p-2 hover:bg-gray-600 rounded"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={resetView}
              className="p-2 hover:bg-gray-600 rounded"
              title="Reset View"
            >
              <Square className="w-4 h-4" />
            </button>
          </div>
          
          {/* Grid toggle */}
          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`p-2 rounded ${showGrid ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
            title="Toggle Grid"
          >
            <Grid className="w-4 h-4" />
          </button>
          
          {/* History controls */}
          <div className="flex items-center space-x-1 bg-gray-700 rounded p-1">
            <button
              onClick={undo}
              disabled={historyIndex <= 0}
              className="p-2 hover:bg-gray-600 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              title="Undo"
            >
              <Undo className="w-4 h-4" />
            </button>
            <button
              onClick={redo}
              disabled={historyIndex >= history.length - 1}
              className="p-2 hover:bg-gray-600 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              title="Redo"
            >
              <Redo className="w-4 h-4" />
            </button>
          </div>
          
          {/* Action buttons */}
          {!readOnly && (
            <>
              <button
                onClick={handleTest}
                disabled={loading}
                className="flex items-center px-3 py-2 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
                title="Test Workflow"
              >
                <Play className="w-4 h-4 mr-1" />
                Test
              </button>
              <button
                onClick={handleSave}
                disabled={loading}
                className="flex items-center px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
                title="Save Workflow"
              >
                <Save className="w-4 h-4 mr-1" />
                Save
              </button>
            </>
          )}
          
          {onCancel && (
            <button
              onClick={onCancel}
              className="px-3 py-2 bg-gray-600 hover:bg-gray-700 rounded"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-4 bg-red-900/50 border-l-4 border-red-500 text-red-200">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            {error}
          </div>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Node Palette */}
        {!readOnly && (
          <div className="w-64 bg-gray-800 border-r border-gray-700 p-4 overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Components</h3>
            
            {Object.entries(nodeTypes).map(([nodeType, config]) => (
              <div key={nodeType} className="mb-6">
                <h4 className="text-sm font-medium text-gray-300 mb-2 capitalize flex items-center">
                  <config.icon className="w-4 h-4 mr-2" />
                  {nodeType}s
                </h4>
                <div className="space-y-2">
                  {config.types.map((type) => (
                    <div
                      key={type.type}
                      draggable
                      onDragStart={(e) => {
                        e.dataTransfer.setData('application/json', JSON.stringify({
                          nodeType,
                          subType: type.type,
                          label: type.label
                        }));
                      }}
                      className={`flex items-center p-2 rounded cursor-move hover:bg-gray-700 ${config.color} ${config.textColor} bg-opacity-20 border ${config.borderColor} border-opacity-30`}
                    >
                      <type.icon className="w-4 h-4 mr-2" />
                      <span className="text-sm">{type.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Canvas */}
        <div className="flex-1 relative overflow-hidden">
          <div
            ref={canvasRef}
            className="w-full h-full relative cursor-crosshair"
            onMouseDown={(e) => tool === 'pan' && handleMouseDown(e, 'canvas')}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (readOnly) return;
              
              try {
                const data = JSON.parse(e.dataTransfer.getData('application/json'));
                const rect = canvasRef.current?.getBoundingClientRect();
                if (!rect) return;
                
                const x = (e.clientX - rect.left - canvas.pan.x) / canvas.zoom;
                const y = (e.clientY - rect.top - canvas.pan.y) / canvas.zoom;
                
                createNode(data.nodeType, data.subType, { x, y });
              } catch (err) {
                console.error('Failed to create node:', err);
              }
            }}
            style={{
              transform: `scale(${canvas.zoom}) translate(${canvas.pan.x}px, ${canvas.pan.y}px)`,
              transformOrigin: '0 0'
            }}
          >
            {/* Grid */}
            {showGrid && (
              <div
                className="absolute inset-0 opacity-20"
                style={{
                  backgroundImage: `
                    linear-gradient(to right, #374151 1px, transparent 1px),
                    linear-gradient(to bottom, #374151 1px, transparent 1px)
                  `,
                  backgroundSize: '20px 20px'
                }}
              />
            )}

            {/* SVG for connections */}
            <svg
              ref={svgRef}
              className="absolute inset-0 w-full h-full pointer-events-none"
              style={{ zIndex: 1 }}
            >
              {canvas.connections.map((connection) => {
                const sourceNode = canvas.nodes.find(n => n.id === connection.sourceNodeId);
                const targetNode = canvas.nodes.find(n => n.id === connection.targetNodeId);
                
                if (!sourceNode || !targetNode) return null;
                
                const sourceX = sourceNode.position.x + 120; // Node width
                const sourceY = sourceNode.position.y + 30; // Half node height
                const targetX = targetNode.position.x;
                const targetY = targetNode.position.y + 30;
                
                const midX = (sourceX + targetX) / 2;
                
                return (
                  <g key={connection.id}>
                    <path
                      d={`M ${sourceX} ${sourceY} C ${midX} ${sourceY} ${midX} ${targetY} ${targetX} ${targetY}`}
                      stroke={connection.type === 'success' ? '#10b981' : connection.type === 'failure' ? '#ef4444' : '#f59e0b'}
                      strokeWidth="2"
                      fill="none"
                      markerEnd="url(#arrowhead)"
                    />
                  </g>
                );
              })}
              
              {/* Arrow marker */}
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="7"
                  refX="9"
                  refY="3.5"
                  orient="auto"
                >
                  <polygon
                    points="0 0, 10 3.5, 0 7"
                    fill="#10b981"
                  />
                </marker>
              </defs>
            </svg>

            {/* Nodes */}
            {canvas.nodes.map((node) => {
              const config = nodeTypes[node.type];
              const Icon = config.icon;
              
              return (
                <div
                  key={node.id}
                  className={`absolute w-32 h-16 rounded-lg border-2 ${config.color} ${config.borderColor} ${config.textColor} cursor-move shadow-lg`}
                  style={{
                    left: node.position.x,
                    top: node.position.y,
                    zIndex: 2
                  }}
                  onMouseDown={(e) => !readOnly && handleMouseDown(e, 'node', node)}
                >
                  <div className="p-2 h-full flex flex-col justify-center items-center text-center">
                    <Icon className="w-5 h-5 mb-1" />
                    <span className="text-xs font-medium truncate w-full">
                      {node.type === 'action' ? (node.data as WorkflowAction).name : 
                       node.type === 'trigger' ? (node.data as WorkflowTrigger).type :
                       (node.data as WorkflowCondition).type}
                    </span>
                  </div>
                  
                  {/* Connection points */}
                  <div className="absolute -right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 bg-gray-600 rounded-full border-2 border-gray-400"></div>
                  <div className="absolute -left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 bg-gray-600 rounded-full border-2 border-gray-400"></div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};