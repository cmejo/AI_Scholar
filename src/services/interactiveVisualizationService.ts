/**
 * Interactive Visualization Service for Frontend
 * 
 * This service handles communication with the backend interactive visualization API
 * and provides real-time updates, collaboration features, and data management.
 */

// Types
export interface VisualizationData {
  data: Record<string, unknown>;
  layout: Record<string, unknown>;
  config: Record<string, unknown>;
  traces?: Array<Record<string, unknown>>;
}

export interface Annotation {
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

export interface Visualization {
  visualization_id: string;
  title: string;
  description: string;
  visualization_type: 'plotly' | 'd3' | 'chartjs' | 'custom';
  data: VisualizationData;
  owner_id: string;
  collaborators: string[];
  annotations: Annotation[];
  created_at: string;
  modified_at: string;
  version: number;
  is_public: boolean;
  tags: string[];
}

export interface InteractionEvent {
  event_id: string;
  interaction_type: 'click' | 'hover' | 'zoom' | 'pan' | 'select' | 'brush' | 'filter';
  data: Record<string, any>;
  coordinates?: { x: number; y: number };
  timestamp: string;
}

export interface VisualizationUpdate {
  update_id: string;
  user_id: string;
  update_type: 'data' | 'layout' | 'config' | 'annotation';
  changes: Record<string, any>;
  timestamp: string;
}

export interface CreateVisualizationRequest {
  title: string;
  description: string;
  visualization_type: string;
  data: Record<string, any>;
  layout?: Record<string, any>;
  config?: Record<string, any>;
  traces?: Array<Record<string, any>>;
  tags?: string[];
}

export interface UpdateVisualizationRequest {
  data_updates: Record<string, any>;
  update_type?: string;
}

export interface AddAnnotationRequest {
  content: string;
  position: { x: number; y: number };
  annotation_type?: string;
  style?: Record<string, any>;
}

class InteractiveVisualizationService {
  private baseUrl = '/api/visualizations';
  private eventListeners: Map<string, Set<(update: VisualizationUpdate) => void>> = new Map();
  private websocket: WebSocket | null = null;

  /**
   * Create a new visualization
   */
  async createVisualization(request: CreateVisualizationRequest): Promise<{ visualization_id: string; message: string }> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating visualization:', error);
      throw error;
    }
  }

  /**
   * Get all visualizations for the current user
   */
  async listVisualizations(): Promise<Visualization[]> {
    try {
      const response = await fetch(this.baseUrl);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error listing visualizations:', error);
      throw error;
    }
  }

  /**
   * Get a specific visualization by ID
   */
  async getVisualization(visualizationId: string): Promise<Visualization> {
    try {
      const response = await fetch(`${this.baseUrl}/${visualizationId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting visualization:', error);
      throw error;
    }
  }

  /**
   * Update visualization data with real-time sync
   */
  async updateVisualizationData(
    visualizationId: string, 
    request: UpdateVisualizationRequest
  ): Promise<{ message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/${visualizationId}/data`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating visualization data:', error);
      throw error;
    }
  }

  /**
   * Add annotation to visualization
   */
  async addAnnotation(
    visualizationId: string, 
    request: AddAnnotationRequest
  ): Promise<{ annotation_id: string; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/${visualizationId}/annotations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error adding annotation:', error);
      throw error;
    }
  }

  /**
   * Update existing annotation
   */
  async updateAnnotation(
    visualizationId: string,
    annotationId: string,
    updates: Record<string, any>
  ): Promise<{ message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/${visualizationId}/annotations/${annotationId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ updates }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating annotation:', error);
      throw error;
    }
  }

  /**
   * Delete annotation
   */
  async deleteAnnotation(visualizationId: string, annotationId: string): Promise<{ message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/${visualizationId}/annotations/${annotationId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error deleting annotation:', error);
      throw error;
    }
  }

  /**
   * Record user interaction with visualization
   */
  async recordInteraction(
    visualizationId: string,
    interaction: {
      interaction_type: string;
      interaction_data: Record<string, any>;
      coordinates?: { x: number; y: number };
    }
  ): Promise<{ message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/${visualizationId}/interactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(interaction),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error recording interaction:', error);
      throw error;
    }
  }

  /**
   * Add collaborator to visualization
   */
  async addCollaborator(visualizationId: string, collaboratorId: string): Promise<{ message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/${visualizationId}/collaborators`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ collaborator_id: collaboratorId }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error adding collaborator:', error);
      throw error;
    }
  }

  /**
   * Remove collaborator from visualization
   */
  async removeCollaborator(visualizationId: string, collaboratorId: string): Promise<{ message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/${visualizationId}/collaborators/${collaboratorId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error removing collaborator:', error);
      throw error;
    }
  }

  /**
   * Generate embed code for visualization
   */
  async generateEmbedCode(
    visualizationId: string,
    options: {
      width?: number;
      height?: number;
      interactive?: boolean;
    } = {}
  ): Promise<{ embed_code: string; width: number; height: number; interactive: boolean; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/${visualizationId}/embed`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating embed code:', error);
      throw error;
    }
  }

  /**
   * Join collaborative session for visualization
   */
  async joinSession(visualizationId: string): Promise<{ message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/${visualizationId}/sessions/join`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error joining session:', error);
      throw error;
    }
  }

  /**
   * Leave collaborative session
   */
  async leaveSession(visualizationId: string): Promise<{ message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/${visualizationId}/sessions/leave`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error leaving session:', error);
      throw error;
    }
  }

  /**
   * Get visualization updates since timestamp
   */
  async getVisualizationUpdates(
    visualizationId: string,
    since?: string
  ): Promise<{ updates: VisualizationUpdate[]; count: number }> {
    try {
      const url = new URL(`${this.baseUrl}/${visualizationId}/updates`, window.location.origin);
      if (since) {
        url.searchParams.set('since', since);
      }

      const response = await fetch(url.toString());
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting visualization updates:', error);
      throw error;
    }
  }

  /**
   * Get supported visualization libraries
   */
  async getSupportedLibraries(): Promise<{ libraries: Record<string, any>; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/libraries/supported`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting supported libraries:', error);
      throw error;
    }
  }

  /**
   * Subscribe to real-time updates for a visualization
   */
  subscribeToUpdates(visualizationId: string, callback: (update: VisualizationUpdate) => void): () => void {
    if (!this.eventListeners.has(visualizationId)) {
      this.eventListeners.set(visualizationId, new Set());
    }
    
    this.eventListeners.get(visualizationId)!.add(callback);

    // Set up WebSocket connection if not already established
    this.setupWebSocketConnection();

    // Return unsubscribe function
    return () => {
      const listeners = this.eventListeners.get(visualizationId);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          this.eventListeners.delete(visualizationId);
        }
      }
    };
  }

  /**
   * Set up WebSocket connection for real-time updates
   */
  private setupWebSocketConnection(): void {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/visualizations`;
      
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log('WebSocket connection established for visualizations');
      };

      this.websocket.onmessage = (event) => {
        try {
          const update: VisualizationUpdate & { visualization_id: string } = JSON.parse(event.data);
          const listeners = this.eventListeners.get(update.visualization_id);
          
          if (listeners) {
            listeners.forEach(callback => callback(update));
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.websocket.onclose = () => {
        console.log('WebSocket connection closed');
        // Attempt to reconnect after a delay
        setTimeout(() => {
          if (this.eventListeners.size > 0) {
            this.setupWebSocketConnection();
          }
        }, 5000);
      };

      this.websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Error setting up WebSocket connection:', error);
    }
  }

  /**
   * Close WebSocket connection
   */
  disconnect(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.eventListeners.clear();
  }

  /**
   * Create sample visualizations for testing
   */
  async createSampleVisualizations(): Promise<void> {
    const samples = [
      {
        title: 'Research Paper Citations Over Time',
        description: 'Line chart showing citation trends',
        visualization_type: 'plotly',
        data: {
          x: ['2020', '2021', '2022', '2023', '2024'],
          y: [45, 67, 89, 123, 156],
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Citations'
        },
        layout: {
          title: 'Citation Trends',
          xaxis: { title: 'Year' },
          yaxis: { title: 'Citations' }
        },
        config: { displayModeBar: true },
        traces: [{
          x: ['2020', '2021', '2022', '2023', '2024'],
          y: [45, 67, 89, 123, 156],
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Citations',
          line: { color: '#3B82F6' }
        }],
        tags: ['research', 'citations', 'trends']
      },
      {
        title: 'Knowledge Graph Network',
        description: 'D3.js network visualization of research concepts',
        visualization_type: 'd3',
        data: {
          nodes: [
            { id: 'AI', group: 1 },
            { id: 'Machine Learning', group: 1 },
            { id: 'Deep Learning', group: 1 },
            { id: 'Neural Networks', group: 2 },
            { id: 'Computer Vision', group: 2 },
            { id: 'NLP', group: 2 }
          ],
          links: [
            { source: 'AI', target: 'Machine Learning', value: 3 },
            { source: 'Machine Learning', target: 'Deep Learning', value: 2 },
            { source: 'Deep Learning', target: 'Neural Networks', value: 2 },
            { source: 'Deep Learning', target: 'Computer Vision', value: 1 },
            { source: 'Deep Learning', target: 'NLP', value: 1 }
          ]
        },
        layout: {
          width: 800,
          height: 600,
          force: {
            charge: -300,
            linkDistance: 50
          }
        },
        config: { interactive: true, zoomable: true },
        tags: ['knowledge-graph', 'network', 'concepts']
      },
      {
        title: 'Research Topic Distribution',
        description: 'Pie chart showing distribution of research topics',
        visualization_type: 'chartjs',
        data: {
          type: 'pie',
          data: {
            labels: ['AI/ML', 'Data Science', 'Computer Vision', 'NLP', 'Robotics', 'Other'],
            datasets: [{
              data: [35, 25, 15, 12, 8, 5],
              backgroundColor: [
                '#3B82F6',
                '#10B981',
                '#F59E0B',
                '#EF4444',
                '#8B5CF6',
                '#06B6D4'
              ]
            }]
          }
        },
        layout: { responsive: true },
        config: { maintainAspectRatio: false },
        tags: ['distribution', 'topics', 'research']
      }
    ];

    for (const sample of samples) {
      try {
        await this.createVisualization(sample);
        console.log(`Created sample visualization: ${sample.title}`);
      } catch (error) {
        console.error(`Error creating sample visualization ${sample.title}:`, error);
      }
    }
  }
}

// Export singleton instance
export const interactiveVisualizationService = new InteractiveVisualizationService();
export default interactiveVisualizationService;