"""
Interactive Visualization Service for AI Scholar Advanced RAG System

This service provides interactive visualization support with real-time updates,
collaborative annotation, and support for multiple visualization libraries.
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import base64
import hashlib

logger = logging.getLogger(__name__)

class VisualizationType(Enum):
    PLOTLY = "plotly"
    D3 = "d3"
    MATPLOTLIB = "matplotlib"
    BOKEH = "bokeh"
    CHART_JS = "chartjs"
    CUSTOM = "custom"

class InteractionType(Enum):
    CLICK = "click"
    HOVER = "hover"
    ZOOM = "zoom"
    PAN = "pan"
    SELECT = "select"
    BRUSH = "brush"
    FILTER = "filter"

@dataclass
class VisualizationData:
    """Data structure for visualization content"""
    data: Dict[str, Any]
    layout: Dict[str, Any]
    config: Dict[str, Any]
    traces: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.traces is None:
            self.traces = []

@dataclass
class InteractionEvent:
    """User interaction event with visualization"""
    event_id: str
    visualization_id: str
    interaction_type: InteractionType
    data: Dict[str, Any]
    user_id: str
    timestamp: datetime
    coordinates: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        if self.coordinates is None:
            self.coordinates = {}

@dataclass
class Annotation:
    """Annotation on visualization"""
    annotation_id: str
    visualization_id: str
    user_id: str
    content: str
    position: Dict[str, float]
    annotation_type: str  # 'text', 'arrow', 'shape', 'highlight'
    style: Dict[str, Any]
    created_at: datetime
    modified_at: datetime
    replies: List[str] = None
    
    def __post_init__(self):
        if self.replies is None:
            self.replies = []

@dataclass
class Visualization:
    """Complete visualization object"""
    visualization_id: str
    title: str
    description: str
    visualization_type: VisualizationType
    data: VisualizationData
    owner_id: str
    collaborators: List[str]
    annotations: List[Annotation]
    interaction_history: List[InteractionEvent]
    created_at: datetime
    modified_at: datetime
    version: int = 1
    is_public: bool = False
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class VisualizationUpdate:
    """Update to visualization data"""
    update_id: str
    visualization_id: str
    user_id: str
    update_type: str  # 'data', 'layout', 'config', 'annotation'
    changes: Dict[str, Any]
    timestamp: datetime

class InteractiveVisualizationService:
    """Service for managing interactive visualizations"""
    
    def __init__(self):
        self.visualizations: Dict[str, Visualization] = {}
        self.active_sessions: Dict[str, List[str]] = {}  # viz_id -> user_ids
        self.update_queue: Dict[str, List[VisualizationUpdate]] = {}
        
        # Supported visualization libraries and their configurations
        self.supported_libraries = {
            VisualizationType.PLOTLY: {
                'name': 'Plotly.js',
                'version': '2.26.0',
                'cdn': 'https://cdn.plot.ly/plotly-2.26.0.min.js',
                'features': ['interactive', 'real-time', 'collaborative']
            },
            VisualizationType.D3: {
                'name': 'D3.js',
                'version': '7.8.5',
                'cdn': 'https://d3js.org/d3.v7.min.js',
                'features': ['custom', 'interactive', 'animations']
            },
            VisualizationType.CHART_JS: {
                'name': 'Chart.js',
                'version': '4.4.0',
                'cdn': 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js',
                'features': ['responsive', 'animated', 'interactive']
            }
        }
    
    async def create_visualization(
        self,
        title: str,
        description: str,
        visualization_type: VisualizationType,
        data: VisualizationData,
        owner_id: str,
        tags: Optional[List[str]] = None
    ) -> Visualization:
        """Create a new interactive visualization"""
        try:
            visualization_id = str(uuid.uuid4())
            
            visualization = Visualization(
                visualization_id=visualization_id,
                title=title,
                description=description,
                visualization_type=visualization_type,
                data=data,
                owner_id=owner_id,
                collaborators=[],
                annotations=[],
                interaction_history=[],
                created_at=datetime.now(),
                modified_at=datetime.now(),
                tags=tags or []
            )
            
            self.visualizations[visualization_id] = visualization
            self.update_queue[visualization_id] = []
            
            logger.info(f"Created visualization {visualization_id} for user {owner_id}")
            return visualization
            
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            raise Exception(f"Failed to create visualization: {str(e)}")
    
    async def get_visualization(self, visualization_id: str, user_id: str) -> Optional[Visualization]:
        """Get visualization with access control"""
        try:
            visualization = self.visualizations.get(visualization_id)
            if not visualization:
                return None
            
            # Check access permissions
            if (visualization.owner_id != user_id and 
                user_id not in visualization.collaborators and 
                not visualization.is_public):
                logger.warning(f"User {user_id} attempted to access visualization {visualization_id} without permission")
                return None
            
            return visualization
            
        except Exception as e:
            logger.error(f"Error getting visualization {visualization_id}: {str(e)}")
            return None
    
    async def update_visualization_data(
        self,
        visualization_id: str,
        user_id: str,
        data_updates: Dict[str, Any],
        update_type: str = 'data'
    ) -> bool:
        """Update visualization data with real-time sync"""
        try:
            visualization = await self.get_visualization(visualization_id, user_id)
            if not visualization:
                return False
            
            # Create update record
            update = VisualizationUpdate(
                update_id=str(uuid.uuid4()),
                visualization_id=visualization_id,
                user_id=user_id,
                update_type=update_type,
                changes=data_updates,
                timestamp=datetime.now()
            )
            
            # Apply updates based on type
            if update_type == 'data':
                visualization.data.data.update(data_updates)
            elif update_type == 'layout':
                visualization.data.layout.update(data_updates)
            elif update_type == 'config':
                visualization.data.config.update(data_updates)
            elif update_type == 'traces':
                if 'traces' in data_updates:
                    visualization.data.traces = data_updates['traces']
            
            visualization.modified_at = datetime.now()
            visualization.version += 1
            
            # Add to update queue for real-time sync
            self.update_queue[visualization_id].append(update)
            
            # Notify active sessions
            await self._notify_active_sessions(visualization_id, update)
            
            logger.info(f"Updated visualization {visualization_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating visualization {visualization_id}: {str(e)}")
            return False
    
    async def add_annotation(
        self,
        visualization_id: str,
        user_id: str,
        content: str,
        position: Dict[str, float],
        annotation_type: str = 'text',
        style: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add annotation to visualization"""
        try:
            visualization = await self.get_visualization(visualization_id, user_id)
            if not visualization:
                return None
            
            annotation = Annotation(
                annotation_id=str(uuid.uuid4()),
                visualization_id=visualization_id,
                user_id=user_id,
                content=content,
                position=position,
                annotation_type=annotation_type,
                style=style or {},
                created_at=datetime.now(),
                modified_at=datetime.now()
            )
            
            visualization.annotations.append(annotation)
            visualization.modified_at = datetime.now()
            
            # Create update for real-time sync
            update = VisualizationUpdate(
                update_id=str(uuid.uuid4()),
                visualization_id=visualization_id,
                user_id=user_id,
                update_type='annotation',
                changes={'action': 'add', 'annotation': asdict(annotation)},
                timestamp=datetime.now()
            )
            
            self.update_queue[visualization_id].append(update)
            await self._notify_active_sessions(visualization_id, update)
            
            logger.info(f"Added annotation {annotation.annotation_id} to visualization {visualization_id}")
            return annotation.annotation_id
            
        except Exception as e:
            logger.error(f"Error adding annotation: {str(e)}")
            return None
    
    async def update_annotation(
        self,
        visualization_id: str,
        annotation_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing annotation"""
        try:
            visualization = await self.get_visualization(visualization_id, user_id)
            if not visualization:
                return False
            
            # Find annotation
            annotation = None
            for ann in visualization.annotations:
                if ann.annotation_id == annotation_id:
                    annotation = ann
                    break
            
            if not annotation:
                return False
            
            # Check if user can edit (owner or annotation creator)
            if annotation.user_id != user_id and visualization.owner_id != user_id:
                return False
            
            # Apply updates
            if 'content' in updates:
                annotation.content = updates['content']
            if 'position' in updates:
                annotation.position.update(updates['position'])
            if 'style' in updates:
                annotation.style.update(updates['style'])
            
            annotation.modified_at = datetime.now()
            visualization.modified_at = datetime.now()
            
            # Create update for real-time sync
            update = VisualizationUpdate(
                update_id=str(uuid.uuid4()),
                visualization_id=visualization_id,
                user_id=user_id,
                update_type='annotation',
                changes={'action': 'update', 'annotation_id': annotation_id, 'updates': updates},
                timestamp=datetime.now()
            )
            
            self.update_queue[visualization_id].append(update)
            await self._notify_active_sessions(visualization_id, update)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating annotation {annotation_id}: {str(e)}")
            return False
    
    async def delete_annotation(
        self,
        visualization_id: str,
        annotation_id: str,
        user_id: str
    ) -> bool:
        """Delete annotation"""
        try:
            visualization = await self.get_visualization(visualization_id, user_id)
            if not visualization:
                return False
            
            # Find and remove annotation
            for i, annotation in enumerate(visualization.annotations):
                if annotation.annotation_id == annotation_id:
                    # Check permissions
                    if annotation.user_id != user_id and visualization.owner_id != user_id:
                        return False
                    
                    visualization.annotations.pop(i)
                    visualization.modified_at = datetime.now()
                    
                    # Create update for real-time sync
                    update = VisualizationUpdate(
                        update_id=str(uuid.uuid4()),
                        visualization_id=visualization_id,
                        user_id=user_id,
                        update_type='annotation',
                        changes={'action': 'delete', 'annotation_id': annotation_id},
                        timestamp=datetime.now()
                    )
                    
                    self.update_queue[visualization_id].append(update)
                    await self._notify_active_sessions(visualization_id, update)
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting annotation {annotation_id}: {str(e)}")
            return False
    
    async def record_interaction(
        self,
        visualization_id: str,
        user_id: str,
        interaction_type: InteractionType,
        interaction_data: Dict[str, Any],
        coordinates: Optional[Dict[str, float]] = None
    ) -> bool:
        """Record user interaction with visualization"""
        try:
            visualization = await self.get_visualization(visualization_id, user_id)
            if not visualization:
                return False
            
            interaction = InteractionEvent(
                event_id=str(uuid.uuid4()),
                visualization_id=visualization_id,
                interaction_type=interaction_type,
                data=interaction_data,
                user_id=user_id,
                timestamp=datetime.now(),
                coordinates=coordinates
            )
            
            visualization.interaction_history.append(interaction)
            
            # Limit interaction history size
            if len(visualization.interaction_history) > 1000:
                visualization.interaction_history = visualization.interaction_history[-500:]
            
            logger.info(f"Recorded {interaction_type.value} interaction on visualization {visualization_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording interaction: {str(e)}")
            return False
    
    async def add_collaborator(self, visualization_id: str, collaborator_id: str, owner_id: str) -> bool:
        """Add collaborator to visualization"""
        try:
            visualization = await self.get_visualization(visualization_id, owner_id)
            if not visualization or visualization.owner_id != owner_id:
                return False
            
            if collaborator_id not in visualization.collaborators:
                visualization.collaborators.append(collaborator_id)
                visualization.modified_at = datetime.now()
                logger.info(f"Added collaborator {collaborator_id} to visualization {visualization_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding collaborator: {str(e)}")
            return False
    
    async def remove_collaborator(self, visualization_id: str, collaborator_id: str, owner_id: str) -> bool:
        """Remove collaborator from visualization"""
        try:
            visualization = await self.get_visualization(visualization_id, owner_id)
            if not visualization or visualization.owner_id != owner_id:
                return False
            
            if collaborator_id in visualization.collaborators:
                visualization.collaborators.remove(collaborator_id)
                visualization.modified_at = datetime.now()
                logger.info(f"Removed collaborator {collaborator_id} from visualization {visualization_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing collaborator: {str(e)}")
            return False
    
    async def generate_embed_code(
        self,
        visualization_id: str,
        user_id: str,
        width: int = 800,
        height: int = 600,
        interactive: bool = True
    ) -> Optional[str]:
        """Generate embeddable HTML code for visualization"""
        try:
            visualization = await self.get_visualization(visualization_id, user_id)
            if not visualization:
                return None
            
            # Generate embed HTML based on visualization type
            if visualization.visualization_type == VisualizationType.PLOTLY:
                embed_code = self._generate_plotly_embed(visualization, width, height, interactive)
            elif visualization.visualization_type == VisualizationType.D3:
                embed_code = self._generate_d3_embed(visualization, width, height, interactive)
            elif visualization.visualization_type == VisualizationType.CHART_JS:
                embed_code = self._generate_chartjs_embed(visualization, width, height, interactive)
            else:
                embed_code = self._generate_generic_embed(visualization, width, height, interactive)
            
            return embed_code
            
        except Exception as e:
            logger.error(f"Error generating embed code: {str(e)}")
            return None
    
    def _generate_plotly_embed(self, visualization: Visualization, width: int, height: int, interactive: bool) -> str:
        """Generate Plotly embed code"""
        config = {
            'displayModeBar': interactive,
            'responsive': True,
            'displaylogo': False
        }
        
        # Enhanced embed code with better styling and error handling
        return f"""
<div id="plotly-div-{visualization.visualization_id}" style="width:{width}px;height:{height}px;background:#1f2937;border-radius:8px;"></div>
<script src="{self.supported_libraries[VisualizationType.PLOTLY]['cdn']}"></script>
<script>
    try {{
        var data = {json.dumps(visualization.data.traces or [visualization.data.data])};
        var layout = {json.dumps({**visualization.data.layout, 'width': width, 'height': height, 'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)', 'font': {'color': '#ffffff'}})};
        var config = {json.dumps(config)};
        
        Plotly.newPlot('plotly-div-{visualization.visualization_id}', data, layout, config);
        
        // Add real-time update capability
        if (typeof window.visualizationUpdates === 'undefined') {{
            window.visualizationUpdates = {{}};
        }}
        
        window.visualizationUpdates['{visualization.visualization_id}'] = function(updateData) {{
            if (updateData.update_type === 'data') {{
                Plotly.restyle('plotly-div-{visualization.visualization_id}', updateData.changes);
            }} else if (updateData.update_type === 'layout') {{
                Plotly.relayout('plotly-div-{visualization.visualization_id}', updateData.changes);
            }}
        }};
    }} catch (error) {{
        console.error('Error rendering Plotly visualization:', error);
        document.getElementById('plotly-div-{visualization.visualization_id}').innerHTML = 
            '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9ca3af;">Error loading visualization</div>';
    }}
</script>
"""
    
    def _generate_d3_embed(self, visualization: Visualization, width: int, height: int, interactive: bool) -> str:
        """Generate D3.js embed code"""
        return f"""
<div id="d3-viz-{visualization.visualization_id}" style="width:{width}px;height:{height}px;background:#1f2937;border-radius:8px;"></div>
<script src="{self.supported_libraries[VisualizationType.D3]['cdn']}"></script>
<script>
    try {{
        var data = {json.dumps(visualization.data.data)};
        var config = {json.dumps(visualization.data.config)};
        
        // Clear any existing content
        d3.select("#d3-viz-{visualization.visualization_id}").selectAll("*").remove();
        
        var svg = d3.select("#d3-viz-{visualization.visualization_id}")
            .append("svg")
            .attr("width", {width})
            .attr("height", {height})
            .style("background", "transparent");
        
        // Network graph implementation
        if (data.nodes && data.links) {{
            var simulation = d3.forceSimulation(data.nodes)
                .force("link", d3.forceLink(data.links).id(d => d.id))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter({width} / 2, {height} / 2));
            
            var link = svg.append("g")
                .selectAll("line")
                .data(data.links)
                .enter().append("line")
                .attr("stroke", "#999")
                .attr("stroke-opacity", 0.6)
                .attr("stroke-width", d => Math.sqrt(d.value || 1));
            
            var node = svg.append("g")
                .selectAll("circle")
                .data(data.nodes)
                .enter().append("circle")
                .attr("r", 8)
                .attr("fill", d => d3.schemeCategory10[d.group % 10])
                .style("cursor", "pointer");
            
            // Add labels
            var label = svg.append("g")
                .selectAll("text")
                .data(data.nodes)
                .enter().append("text")
                .text(d => d.id)
                .attr("font-size", "12px")
                .attr("fill", "#ffffff")
                .attr("text-anchor", "middle")
                .attr("dy", "0.35em");
            
            if ({str(interactive).lower()}) {{
                node.call(d3.drag()
                    .on("start", function(event, d) {{
                        if (!event.active) simulation.alphaTarget(0.3).restart();
                        d.fx = d.x;
                        d.fy = d.y;
                    }})
                    .on("drag", function(event, d) {{
                        d.fx = event.x;
                        d.fy = event.y;
                    }})
                    .on("end", function(event, d) {{
                        if (!event.active) simulation.alphaTarget(0);
                        d.fx = null;
                        d.fy = null;
                    }}));
            }}
            
            simulation.on("tick", function() {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
                
                label
                    .attr("x", d => d.x)
                    .attr("y", d => d.y);
            }});
        }}
        
        // Add real-time update capability
        if (typeof window.visualizationUpdates === 'undefined') {{
            window.visualizationUpdates = {{}};
        }}
        
        window.visualizationUpdates['{visualization.visualization_id}'] = function(updateData) {{
            // Re-render with new data
            if (updateData.update_type === 'data') {{
                // Update data and re-render
                Object.assign(data, updateData.changes);
                // Re-render logic would go here
            }}
        }};
    }} catch (error) {{
        console.error('Error rendering D3 visualization:', error);
        document.getElementById('d3-viz-{visualization.visualization_id}').innerHTML = 
            '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9ca3af;">Error loading visualization</div>';
    }}
</script>
"""
    
    def _generate_chartjs_embed(self, visualization: Visualization, width: int, height: int, interactive: bool) -> str:
        """Generate Chart.js embed code"""
        return f"""
<div style="width:{width}px;height:{height}px;background:#1f2937;border-radius:8px;padding:10px;">
    <canvas id="chartjs-{visualization.visualization_id}"></canvas>
</div>
<script src="{self.supported_libraries[VisualizationType.CHART_JS]['cdn']}"></script>
<script>
    try {{
        var ctx = document.getElementById('chartjs-{visualization.visualization_id}').getContext('2d');
        var chartConfig = {json.dumps(visualization.data.data)};
        
        // Enhance config with dark theme
        if (!chartConfig.options) chartConfig.options = {{}};
        if (!chartConfig.options.plugins) chartConfig.options.plugins = {{}};
        if (!chartConfig.options.plugins.legend) chartConfig.options.plugins.legend = {{}};
        if (!chartConfig.options.plugins.legend.labels) chartConfig.options.plugins.legend.labels = {{}};
        chartConfig.options.plugins.legend.labels.color = '#ffffff';
        
        if (!chartConfig.options.scales) chartConfig.options.scales = {{}};
        ['x', 'y'].forEach(axis => {{
            if (!chartConfig.options.scales[axis]) chartConfig.options.scales[axis] = {{}};
            if (!chartConfig.options.scales[axis].ticks) chartConfig.options.scales[axis].ticks = {{}};
            if (!chartConfig.options.scales[axis].grid) chartConfig.options.scales[axis].grid = {{}};
            chartConfig.options.scales[axis].ticks.color = '#ffffff';
            chartConfig.options.scales[axis].grid.color = 'rgba(255,255,255,0.1)';
        }});
        
        chartConfig.options.responsive = true;
        chartConfig.options.maintainAspectRatio = false;
        
        var chart = new Chart(ctx, chartConfig);
        
        // Add real-time update capability
        if (typeof window.visualizationUpdates === 'undefined') {{
            window.visualizationUpdates = {{}};
        }}
        
        window.visualizationUpdates['{visualization.visualization_id}'] = function(updateData) {{
            if (updateData.update_type === 'data') {{
                Object.assign(chart.data, updateData.changes);
                chart.update();
            }}
        }};
    }} catch (error) {{
        console.error('Error rendering Chart.js visualization:', error);
        document.getElementById('chartjs-{visualization.visualization_id}').parentElement.innerHTML = 
            '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9ca3af;">Error loading visualization</div>';
    }}
</script>
"""
    
    def _generate_generic_embed(self, visualization: Visualization, width: int, height: int, interactive: bool) -> str:
        """Generate generic embed code"""
        return f"""
<div id="viz-{visualization.visualization_id}" style="width:{width}px;height:{height}px;">
    <h3>{visualization.title}</h3>
    <p>{visualization.description}</p>
    <pre>{json.dumps(visualization.data.data, indent=2)}</pre>
</div>
"""
    
    async def _notify_active_sessions(self, visualization_id: str, update: VisualizationUpdate):
        """Notify active sessions about updates (placeholder for WebSocket implementation)"""
        # In a real implementation, this would send WebSocket messages
        # to all active sessions viewing this visualization
        active_users = self.active_sessions.get(visualization_id, [])
        logger.info(f"Notifying {len(active_users)} active users about update to {visualization_id}")
    
    async def join_session(self, visualization_id: str, user_id: str) -> bool:
        """Join collaborative session for visualization"""
        try:
            visualization = await self.get_visualization(visualization_id, user_id)
            if not visualization:
                return False
            
            if visualization_id not in self.active_sessions:
                self.active_sessions[visualization_id] = []
            
            if user_id not in self.active_sessions[visualization_id]:
                self.active_sessions[visualization_id].append(user_id)
            
            logger.info(f"User {user_id} joined session for visualization {visualization_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining session: {str(e)}")
            return False
    
    async def leave_session(self, visualization_id: str, user_id: str) -> bool:
        """Leave collaborative session"""
        try:
            if visualization_id in self.active_sessions:
                if user_id in self.active_sessions[visualization_id]:
                    self.active_sessions[visualization_id].remove(user_id)
                    
                    # Clean up empty sessions
                    if not self.active_sessions[visualization_id]:
                        del self.active_sessions[visualization_id]
            
            logger.info(f"User {user_id} left session for visualization {visualization_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error leaving session: {str(e)}")
            return False
    
    async def list_user_visualizations(self, user_id: str) -> List[Dict[str, Any]]:
        """List all visualizations accessible to user"""
        try:
            user_visualizations = []
            
            for visualization in self.visualizations.values():
                if (visualization.owner_id == user_id or 
                    user_id in visualization.collaborators or 
                    visualization.is_public):
                    
                    user_visualizations.append({
                        'visualization_id': visualization.visualization_id,
                        'title': visualization.title,
                        'description': visualization.description,
                        'type': visualization.visualization_type.value,
                        'created_at': visualization.created_at.isoformat(),
                        'modified_at': visualization.modified_at.isoformat(),
                        'owner_id': visualization.owner_id,
                        'is_owner': visualization.owner_id == user_id,
                        'collaborators_count': len(visualization.collaborators),
                        'annotations_count': len(visualization.annotations),
                        'version': visualization.version,
                        'tags': visualization.tags
                    })
            
            return sorted(user_visualizations, key=lambda x: x['modified_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing visualizations for user {user_id}: {str(e)}")
            return []
    
    async def get_visualization_updates(self, visualization_id: str, since_timestamp: Optional[datetime] = None) -> List[VisualizationUpdate]:
        """Get updates for visualization since timestamp"""
        try:
            updates = self.update_queue.get(visualization_id, [])
            
            if since_timestamp:
                updates = [update for update in updates if update.timestamp > since_timestamp]
            
            return updates
            
        except Exception as e:
            logger.error(f"Error getting updates for visualization {visualization_id}: {str(e)}")
            return []
    
    async def stream_data_update(
        self,
        visualization_id: str,
        user_id: str,
        data_stream: Dict[str, Any],
        update_interval: float = 1.0
    ) -> bool:
        """Stream real-time data updates to visualization"""
        try:
            visualization = await self.get_visualization(visualization_id, user_id)
            if not visualization:
                return False
            
            # Create streaming update
            update = VisualizationUpdate(
                update_id=str(uuid.uuid4()),
                visualization_id=visualization_id,
                user_id=user_id,
                update_type='stream',
                changes=data_stream,
                timestamp=datetime.now()
            )
            
            # Add to update queue
            self.update_queue[visualization_id].append(update)
            
            # Notify active sessions immediately
            await self._notify_active_sessions(visualization_id, update)
            
            logger.info(f"Streamed data update to visualization {visualization_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error streaming data update: {str(e)}")
            return False
    
    async def create_visualization_snapshot(
        self,
        visualization_id: str,
        user_id: str,
        snapshot_name: str
    ) -> Optional[str]:
        """Create a snapshot of current visualization state"""
        try:
            visualization = await self.get_visualization(visualization_id, user_id)
            if not visualization:
                return None
            
            snapshot_id = str(uuid.uuid4())
            snapshot = {
                'snapshot_id': snapshot_id,
                'visualization_id': visualization_id,
                'name': snapshot_name,
                'data': asdict(visualization.data),
                'annotations': [asdict(ann) for ann in visualization.annotations],
                'created_by': user_id,
                'created_at': datetime.now().isoformat(),
                'version': visualization.version
            }
            
            # Store snapshot (in production, this would go to a database)
            if not hasattr(self, 'snapshots'):
                self.snapshots = {}
            self.snapshots[snapshot_id] = snapshot
            
            logger.info(f"Created snapshot {snapshot_id} for visualization {visualization_id}")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Error creating visualization snapshot: {str(e)}")
            return None
    
    async def restore_visualization_snapshot(
        self,
        visualization_id: str,
        snapshot_id: str,
        user_id: str
    ) -> bool:
        """Restore visualization from snapshot"""
        try:
            visualization = await self.get_visualization(visualization_id, user_id)
            if not visualization or visualization.owner_id != user_id:
                return False
            
            if not hasattr(self, 'snapshots') or snapshot_id not in self.snapshots:
                return False
            
            snapshot = self.snapshots[snapshot_id]
            
            # Restore data
            visualization.data = VisualizationData(**snapshot['data'])
            visualization.modified_at = datetime.now()
            visualization.version += 1
            
            # Create update for real-time sync
            update = VisualizationUpdate(
                update_id=str(uuid.uuid4()),
                visualization_id=visualization_id,
                user_id=user_id,
                update_type='restore',
                changes={'snapshot_id': snapshot_id, 'data': snapshot['data']},
                timestamp=datetime.now()
            )
            
            self.update_queue[visualization_id].append(update)
            await self._notify_active_sessions(visualization_id, update)
            
            logger.info(f"Restored visualization {visualization_id} from snapshot {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring visualization snapshot: {str(e)}")
            return False

# Global service instance
interactive_visualization_service = InteractiveVisualizationService()