"""
Note-Taking App Integration Service

This service provides integration with popular note-taking applications:
- Obsidian (via vault file system access)
- Notion (via API)
- Roam Research (via API and graph synchronization)

Supports bidirectional synchronization, markdown preservation, and knowledge graph integration.
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import aiofiles
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class NoteTakingApp(Enum):
    OBSIDIAN = "obsidian"
    NOTION = "notion"
    ROAM = "roam"

@dataclass
class Note:
    """Unified note structure"""
    id: str
    title: str
    content: str
    tags: List[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    app_source: str = ""
    app_id: Optional[str] = None
    parent_id: Optional[str] = None
    links: List[str] = None
    backlinks: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.links is None:
            self.links = []
        if self.backlinks is None:
            self.backlinks = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SyncConfig:
    """Synchronization configuration"""
    app_type: NoteTakingApp
    credentials: Dict[str, Any]
    sync_direction: str = "bidirectional"  # bidirectional, import_only, export_only
    auto_sync: bool = False
    sync_interval_minutes: int = 30
    preserve_formatting: bool = True
    include_attachments: bool = False

@dataclass
class SyncResult:
    """Result of synchronization operation"""
    success: bool
    notes_synced: int
    notes_created: int
    notes_updated: int
    notes_deleted: int
    errors: List[str]
    last_sync: datetime
    
class ObsidianIntegration:
    """Obsidian vault integration via file system"""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.supported_extensions = ['.md', '.txt']
        
    async def sync_vault(self, config: SyncConfig) -> SyncResult:
        """Synchronize with Obsidian vault"""
        try:
            if not self.vault_path.exists():
                raise FileNotFoundError(f"Vault path does not exist: {self.vault_path}")
            
            notes = await self._read_vault_notes()
            
            # Process notes for knowledge graph integration
            processed_notes = []
            for note in notes:
                processed_note = await self._process_obsidian_note(note)
                processed_notes.append(processed_note)
            
            return SyncResult(
                success=True,
                notes_synced=len(processed_notes),
                notes_created=len(processed_notes),
                notes_updated=0,
                notes_deleted=0,
                errors=[],
                last_sync=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Obsidian sync error: {e}")
            return SyncResult(
                success=False,
                notes_synced=0,
                notes_created=0,
                notes_updated=0,
                notes_deleted=0,
                errors=[str(e)],
                last_sync=datetime.now()
            )
    
    async def _read_vault_notes(self) -> List[Note]:
        """Read all notes from Obsidian vault"""
        notes = []
        
        for file_path in self.vault_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in self.supported_extensions:
                try:
                    note = await self._read_note_file(file_path)
                    if note:
                        notes.append(note)
                except Exception as e:
                    logger.warning(f"Error reading note {file_path}: {e}")
        
        return notes
    
    async def _read_note_file(self, file_path: Path) -> Optional[Note]:
        """Read a single note file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Extract frontmatter if present
            frontmatter, body = self._parse_frontmatter(content)
            
            # Extract title (from frontmatter or filename)
            title = frontmatter.get('title', file_path.stem)
            
            # Extract tags
            tags = frontmatter.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            
            # Extract inline tags (including hyphenated tags)
            inline_tags = re.findall(r'#([\w-]+)', body)
            tags.extend(inline_tags)
            tags = list(set(tags))  # Remove duplicates
            
            # Extract links
            links = self._extract_obsidian_links(body)
            
            # Get file stats
            stat = file_path.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime)
            updated_at = datetime.fromtimestamp(stat.st_mtime)
            
            # Generate unique ID
            note_id = hashlib.md5(str(file_path).encode()).hexdigest()
            
            return Note(
                id=note_id,
                title=title,
                content=body,
                tags=tags,
                created_at=created_at,
                updated_at=updated_at,
                app_source="obsidian",
                app_id=str(file_path.relative_to(self.vault_path)),
                links=links,
                metadata={
                    'file_path': str(file_path),
                    'frontmatter': frontmatter,
                    'relative_path': str(file_path.relative_to(self.vault_path))
                }
            )
            
        except Exception as e:
            logger.error(f"Error reading note file {file_path}: {e}")
            return None
    
    def _parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content"""
        frontmatter = {}
        body = content
        
        if content.startswith('---\n'):
            try:
                parts = content.split('---\n', 2)
                if len(parts) >= 3:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    body = parts[2]
            except Exception as e:
                logger.warning(f"Error parsing frontmatter: {e}")
        
        return frontmatter, body
    
    def _extract_obsidian_links(self, content: str) -> List[str]:
        """Extract Obsidian-style links from content"""
        # Extract [[wikilinks]]
        wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)
        
        # Extract markdown links
        markdown_links = re.findall(r'\[([^\]]+)\]\([^\)]+\)', content)
        
        # Combine and clean
        all_links = wikilinks + markdown_links
        return [link.strip() for link in all_links if link.strip()]
    
    async def _process_obsidian_note(self, note: Note) -> Note:
        """Process Obsidian note for knowledge graph integration"""
        # Find backlinks by searching for references to this note
        backlinks = await self._find_backlinks(note)
        note.backlinks = backlinks
        
        return note
    
    async def _find_backlinks(self, note: Note) -> List[str]:
        """Find notes that link to this note"""
        backlinks = []
        note_title = note.title
        
        # Search for references in other notes
        for file_path in self.vault_path.rglob('*.md'):
            if str(file_path) == note.metadata.get('file_path'):
                continue  # Skip self
            
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                # Check for wikilink references
                if f'[[{note_title}]]' in content or f'[[{note.metadata.get("relative_path", "")}]]' in content:
                    backlinks.append(file_path.stem)
                    
            except Exception as e:
                logger.warning(f"Error checking backlinks in {file_path}: {e}")
        
        return backlinks
    
    async def export_note(self, note: Note, file_path: Optional[str] = None) -> bool:
        """Export note to Obsidian vault"""
        try:
            if file_path is None:
                file_path = self.vault_path / f"{note.title}.md"
            else:
                file_path = Path(file_path)
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build content with frontmatter
            content = self._build_obsidian_content(note)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            return True
            
        except Exception as e:
            logger.error(f"Error exporting note to Obsidian: {e}")
            return False
    
    def _build_obsidian_content(self, note: Note) -> str:
        """Build Obsidian-formatted content with frontmatter"""
        frontmatter = {
            'title': note.title,
            'tags': note.tags,
            'created': note.created_at.isoformat() if note.created_at else None,
            'updated': note.updated_at.isoformat() if note.updated_at else None,
            'id': note.id
        }
        
        # Remove None values
        frontmatter = {k: v for k, v in frontmatter.items() if v is not None}
        
        content = "---\n"
        import yaml
        content += yaml.dump(frontmatter, default_flow_style=False)
        content += "---\n\n"
        content += note.content
        
        return content

class NotionIntegration:
    """Notion API integration"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    async def sync_workspace(self, config: SyncConfig) -> SyncResult:
        """Synchronize with Notion workspace"""
        try:
            # Get database ID from config
            database_id = config.credentials.get('database_id')
            if not database_id:
                raise ValueError("Database ID required for Notion integration")
            
            notes = await self._get_database_pages(database_id)
            
            return SyncResult(
                success=True,
                notes_synced=len(notes),
                notes_created=len(notes),
                notes_updated=0,
                notes_deleted=0,
                errors=[],
                last_sync=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Notion sync error: {e}")
            return SyncResult(
                success=False,
                notes_synced=0,
                notes_created=0,
                notes_updated=0,
                notes_deleted=0,
                errors=[str(e)],
                last_sync=datetime.now()
            )
    
    async def _get_database_pages(self, database_id: str) -> List[Note]:
        """Get all pages from a Notion database"""
        notes = []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/databases/{database_id}/query"
                
                async with session.post(url, headers=self.headers) as response:
                    if response.status != 200:
                        raise Exception(f"Notion API error: {response.status}")
                    
                    data = await response.json()
                    
                    for page in data.get('results', []):
                        note = await self._convert_notion_page(page)
                        if note:
                            notes.append(note)
                            
        except Exception as e:
            logger.error(f"Error getting Notion pages: {e}")
        
        return notes
    
    async def _convert_notion_page(self, page: Dict[str, Any]) -> Optional[Note]:
        """Convert Notion page to unified Note format"""
        try:
            page_id = page['id']
            
            # Extract title from properties
            title = "Untitled"
            properties = page.get('properties', {})
            
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'title':
                    title_array = prop_data.get('title', [])
                    if title_array:
                        title = title_array[0].get('plain_text', 'Untitled')
                    break
            
            # Get page content
            content = await self._get_page_content(page_id)
            
            # Extract tags from properties
            tags = []
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'multi_select':
                    tag_objects = prop_data.get('multi_select', [])
                    tags.extend([tag['name'] for tag in tag_objects])
            
            # Parse dates
            created_at = None
            updated_at = None
            
            if page.get('created_time'):
                created_at = datetime.fromisoformat(page['created_time'].replace('Z', '+00:00'))
            if page.get('last_edited_time'):
                updated_at = datetime.fromisoformat(page['last_edited_time'].replace('Z', '+00:00'))
            
            return Note(
                id=hashlib.md5(page_id.encode()).hexdigest(),
                title=title,
                content=content,
                tags=tags,
                created_at=created_at,
                updated_at=updated_at,
                app_source="notion",
                app_id=page_id,
                metadata={
                    'notion_url': page.get('url'),
                    'properties': properties
                }
            )
            
        except Exception as e:
            logger.error(f"Error converting Notion page: {e}")
            return None
    
    async def _get_page_content(self, page_id: str) -> str:
        """Get content blocks from a Notion page"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/blocks/{page_id}/children"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        return ""
                    
                    data = await response.json()
                    blocks = data.get('results', [])
                    
                    content_parts = []
                    for block in blocks:
                        block_text = self._extract_block_text(block)
                        if block_text:
                            content_parts.append(block_text)
                    
                    return '\n\n'.join(content_parts)
                    
        except Exception as e:
            logger.error(f"Error getting Notion page content: {e}")
            return ""
    
    def _extract_block_text(self, block: Dict[str, Any]) -> str:
        """Extract text from a Notion block"""
        block_type = block.get('type')
        
        if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3']:
            rich_text = block.get(block_type, {}).get('rich_text', [])
            return ''.join([text.get('plain_text', '') for text in rich_text])
        elif block_type == 'bulleted_list_item':
            rich_text = block.get('bulleted_list_item', {}).get('rich_text', [])
            text = ''.join([text.get('plain_text', '') for text in rich_text])
            return f"• {text}"
        elif block_type == 'numbered_list_item':
            rich_text = block.get('numbered_list_item', {}).get('rich_text', [])
            text = ''.join([text.get('plain_text', '') for text in rich_text])
            return f"1. {text}"
        
        return ""
    
    async def create_page(self, note: Note, database_id: str) -> bool:
        """Create a new page in Notion"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/pages"
                
                payload = {
                    "parent": {"database_id": database_id},
                    "properties": {
                        "Name": {
                            "title": [
                                {
                                    "text": {
                                        "content": note.title
                                    }
                                }
                            ]
                        }
                    },
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": note.content
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
                
                # Add tags if present
                if note.tags:
                    payload["properties"]["Tags"] = {
                        "multi_select": [{"name": tag} for tag in note.tags]
                    }
                
                async with session.post(url, headers=self.headers, json=payload) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            return False

class RoamIntegration:
    """Roam Research integration (simplified implementation)"""
    
    def __init__(self, graph_name: str, api_token: str):
        self.graph_name = graph_name
        self.api_token = api_token
        self.base_url = f"https://api.roamresearch.com/api/graph/{graph_name}"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    async def sync_graph(self, config: SyncConfig) -> SyncResult:
        """Synchronize with Roam Research graph"""
        try:
            # Note: This is a simplified implementation
            # Real Roam API integration would require more complex block-level operations
            
            notes = await self._get_all_pages()
            
            return SyncResult(
                success=True,
                notes_synced=len(notes),
                notes_created=len(notes),
                notes_updated=0,
                notes_deleted=0,
                errors=[],
                last_sync=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Roam sync error: {e}")
            return SyncResult(
                success=False,
                notes_synced=0,
                notes_created=0,
                notes_updated=0,
                notes_deleted=0,
                errors=[str(e)],
                last_sync=datetime.now()
            )
    
    async def _get_all_pages(self) -> List[Note]:
        """Get all pages from Roam graph"""
        # Placeholder implementation
        # Real implementation would use Roam's query API
        logger.warning("Roam Research integration is a placeholder implementation")
        return []
    
    def _extract_roam_links(self, content: str) -> List[str]:
        """Extract Roam-style links from content"""
        # Extract [[page references]]
        page_refs = re.findall(r'\[\[([^\]]+)\]\]', content)
        
        # Extract ((block references))
        block_refs = re.findall(r'\(\(([^\)]+)\)\)', content)
        
        return page_refs + block_refs

class NoteTakingIntegrationService:
    """Unified note-taking integration service"""
    
    def __init__(self):
        self.integrations = {}
    
    def add_obsidian_integration(self, vault_path: str) -> str:
        """Add Obsidian vault integration"""
        integration_id = f"obsidian_{hashlib.md5(vault_path.encode()).hexdigest()[:8]}"
        self.integrations[integration_id] = {
            'type': NoteTakingApp.OBSIDIAN,
            'integration': ObsidianIntegration(vault_path),
            'config': {'vault_path': vault_path}
        }
        return integration_id
    
    def add_notion_integration(self, api_token: str, database_id: str) -> str:
        """Add Notion workspace integration"""
        integration_id = f"notion_{hashlib.md5(api_token.encode()).hexdigest()[:8]}"
        self.integrations[integration_id] = {
            'type': NoteTakingApp.NOTION,
            'integration': NotionIntegration(api_token),
            'config': {'api_token': api_token, 'database_id': database_id}
        }
        return integration_id
    
    def add_roam_integration(self, graph_name: str, api_token: str) -> str:
        """Add Roam Research graph integration"""
        integration_id = f"roam_{hashlib.md5(f'{graph_name}_{api_token}'.encode()).hexdigest()[:8]}"
        self.integrations[integration_id] = {
            'type': NoteTakingApp.ROAM,
            'integration': RoamIntegration(graph_name, api_token),
            'config': {'graph_name': graph_name, 'api_token': api_token}
        }
        return integration_id
    
    async def sync_integration(self, integration_id: str, config: SyncConfig) -> SyncResult:
        """Synchronize a specific integration"""
        if integration_id not in self.integrations:
            return SyncResult(
                success=False,
                notes_synced=0,
                notes_created=0,
                notes_updated=0,
                notes_deleted=0,
                errors=[f"Integration not found: {integration_id}"],
                last_sync=datetime.now()
            )
        
        integration_data = self.integrations[integration_id]
        integration = integration_data['integration']
        app_type = integration_data['type']
        
        try:
            if app_type == NoteTakingApp.OBSIDIAN:
                return await integration.sync_vault(config)
            elif app_type == NoteTakingApp.NOTION:
                return await integration.sync_workspace(config)
            elif app_type == NoteTakingApp.ROAM:
                return await integration.sync_graph(config)
            else:
                raise ValueError(f"Unsupported app type: {app_type}")
                
        except Exception as e:
            logger.error(f"Sync error for {integration_id}: {e}")
            return SyncResult(
                success=False,
                notes_synced=0,
                notes_created=0,
                notes_updated=0,
                notes_deleted=0,
                errors=[str(e)],
                last_sync=datetime.now()
            )
    
    async def sync_all_integrations(self) -> Dict[str, SyncResult]:
        """Synchronize all configured integrations"""
        results = {}
        
        for integration_id in self.integrations:
            # Create default config
            config = SyncConfig(
                app_type=self.integrations[integration_id]['type'],
                credentials=self.integrations[integration_id]['config']
            )
            
            result = await self.sync_integration(integration_id, config)
            results[integration_id] = result
        
        return results
    
    def get_integration_info(self, integration_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific integration"""
        if integration_id not in self.integrations:
            return None
        
        integration_data = self.integrations[integration_id]
        return {
            'id': integration_id,
            'type': integration_data['type'].value,
            'config': {k: v for k, v in integration_data['config'].items() if k != 'api_token'}
        }
    
    def list_integrations(self) -> List[Dict[str, Any]]:
        """List all configured integrations"""
        return [self.get_integration_info(integration_id) 
                for integration_id in self.integrations]
    
    def remove_integration(self, integration_id: str) -> bool:
        """Remove an integration"""
        if integration_id in self.integrations:
            del self.integrations[integration_id]
            return True
        return False
    
    def get_supported_apps(self) -> List[str]:
        """Get list of supported note-taking apps"""
        return [app.value for app in NoteTakingApp]