"""
Reference Manager Integration Service

This service provides integration with popular reference managers:
- Zotero (via API)
- Mendeley (via API) 
- EndNote (via file import/export)

Supports OAuth authentication, library synchronization, and unified interface.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import base64
from urllib.parse import urlencode, parse_qs, urlparse

logger = logging.getLogger(__name__)

class ReferenceManagerType(Enum):
    ZOTERO = "zotero"
    MENDELEY = "mendeley"
    ENDNOTE = "endnote"

@dataclass
class BibliographicData:
    """Unified bibliographic data structure"""
    title: str
    authors: List[str]
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = None
    citation_count: Optional[int] = None
    url: Optional[str] = None
    pages: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    item_type: str = "article"
    tags: List[str] = None
    notes: Optional[str] = None
    date_added: Optional[datetime] = None
    date_modified: Optional[datetime] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.tags is None:
            self.tags = []

@dataclass
class AuthCredentials:
    """OAuth credentials for reference managers"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    scope: Optional[str] = None
    user_id: Optional[str] = None

@dataclass
class SyncResult:
    """Result of synchronization operation"""
    success: bool
    items_synced: int
    errors: List[str]
    last_sync: datetime
    total_items: int

class ZoteroIntegration:
    """Zotero API integration with OAuth authentication"""
    
    def __init__(self):
        self.base_url = "https://api.zotero.org"
        self.oauth_url = "https://www.zotero.org/oauth"
        
    async def get_authorization_url(self, client_id: str, redirect_uri: str) -> str:
        """Generate OAuth authorization URL"""
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'read write'
        }
        return f"{self.oauth_url}/authorize?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, client_id: str, 
                                    client_secret: str, redirect_uri: str) -> AuthCredentials:
        """Exchange authorization code for access token"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    'grant_type': 'authorization_code',
                    'code': code,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'redirect_uri': redirect_uri
                }
                
                async with session.post(f"{self.oauth_url}/access", data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        return AuthCredentials(
                            access_token=token_data['access_token'],
                            token_type=token_data.get('token_type', 'Bearer'),
                            user_id=token_data.get('userID')
                        )
                    else:
                        raise Exception(f"Token exchange failed: {response.status}")
        except Exception as e:
            logger.error(f"Zotero token exchange error: {e}")
            raise
    
    async def get_user_library(self, credentials: AuthCredentials, 
                             limit: int = 100) -> List[BibliographicData]:
        """Fetch user's Zotero library"""
        try:
            headers = {
                'Authorization': f"{credentials.token_type} {credentials.access_token}",
                'Zotero-API-Version': '3'
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/users/{credentials.user_id}/items"
                params = {'limit': limit, 'format': 'json', 'include': 'data'}
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        items = await response.json()
                        return [self._convert_zotero_item(item) for item in items]
                    else:
                        raise Exception(f"Library fetch failed: {response.status}")
        except Exception as e:
            logger.error(f"Zotero library fetch error: {e}")
            raise
    
    async def add_item_to_library(self, credentials: AuthCredentials, 
                                item: BibliographicData) -> bool:
        """Add item to Zotero library"""
        try:
            headers = {
                'Authorization': f"{credentials.token_type} {credentials.access_token}",
                'Zotero-API-Version': '3',
                'Content-Type': 'application/json'
            }
            
            zotero_item = self._convert_to_zotero_format(item)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/users/{credentials.user_id}/items"
                
                async with session.post(url, headers=headers, json=[zotero_item]) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Zotero item add error: {e}")
            return False
    
    def _convert_zotero_item(self, zotero_item: Dict) -> BibliographicData:
        """Convert Zotero item to unified format"""
        data = zotero_item.get('data', {})
        
        # Extract authors
        authors = []
        for creator in data.get('creators', []):
            if creator.get('firstName') and creator.get('lastName'):
                authors.append(f"{creator['firstName']} {creator['lastName']}")
            elif creator.get('name'):
                authors.append(creator['name'])
        
        return BibliographicData(
            title=data.get('title', ''),
            authors=authors,
            journal=data.get('publicationTitle'),
            year=self._extract_year(data.get('date')),
            doi=data.get('DOI'),
            abstract=data.get('abstractNote'),
            url=data.get('url'),
            pages=data.get('pages'),
            volume=data.get('volume'),
            issue=data.get('issue'),
            publisher=data.get('publisher'),
            isbn=data.get('ISBN'),
            item_type=data.get('itemType', 'article'),
            tags=[tag['tag'] for tag in data.get('tags', [])],
            notes=data.get('extra'),
            date_added=datetime.fromisoformat(zotero_item.get('dateAdded', '').replace('Z', '+00:00')) if zotero_item.get('dateAdded') else None,
            date_modified=datetime.fromisoformat(zotero_item.get('dateModified', '').replace('Z', '+00:00')) if zotero_item.get('dateModified') else None
        )
    
    def _convert_to_zotero_format(self, item: BibliographicData) -> Dict:
        """Convert unified format to Zotero item"""
        creators = []
        for author in item.authors:
            name_parts = author.split(' ', 1)
            if len(name_parts) == 2:
                creators.append({
                    'creatorType': 'author',
                    'firstName': name_parts[0],
                    'lastName': name_parts[1]
                })
            else:
                creators.append({
                    'creatorType': 'author',
                    'name': author
                })
        
        zotero_item = {
            'itemType': item.item_type,
            'title': item.title,
            'creators': creators,
            'abstractNote': item.abstract or '',
            'DOI': item.doi or '',
            'url': item.url or '',
            'pages': item.pages or '',
            'volume': item.volume or '',
            'issue': item.issue or '',
            'publisher': item.publisher or '',
            'ISBN': item.isbn or '',
            'extra': item.notes or '',
            'tags': [{'tag': tag} for tag in item.tags]
        }
        
        if item.journal:
            zotero_item['publicationTitle'] = item.journal
        if item.year:
            zotero_item['date'] = str(item.year)
            
        return zotero_item
    
    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """Extract year from date string"""
        if not date_str:
            return None
        try:
            # Try to extract 4-digit year
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
            if year_match:
                return int(year_match.group())
        except:
            pass
        return None

class MendeleyIntegration:
    """Mendeley API integration"""
    
    def __init__(self):
        self.base_url = "https://api.mendeley.com"
        self.oauth_url = "https://api.mendeley.com/oauth"
    
    async def get_authorization_url(self, client_id: str, redirect_uri: str) -> str:
        """Generate OAuth authorization URL"""
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'all'
        }
        return f"{self.oauth_url}/authorize?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, client_id: str, 
                                    client_secret: str, redirect_uri: str) -> AuthCredentials:
        """Exchange authorization code for access token"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
                headers = {
                    'Authorization': f'Basic {auth}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                
                data = {
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri
                }
                
                async with session.post(f"{self.oauth_url}/token", 
                                      headers=headers, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        return AuthCredentials(
                            access_token=token_data['access_token'],
                            refresh_token=token_data.get('refresh_token'),
                            token_type=token_data.get('token_type', 'Bearer'),
                            expires_in=token_data.get('expires_in')
                        )
                    else:
                        raise Exception(f"Token exchange failed: {response.status}")
        except Exception as e:
            logger.error(f"Mendeley token exchange error: {e}")
            raise
    
    async def get_user_library(self, credentials: AuthCredentials, 
                             limit: int = 100) -> List[BibliographicData]:
        """Fetch user's Mendeley library"""
        try:
            headers = {
                'Authorization': f"{credentials.token_type} {credentials.access_token}",
                'Accept': 'application/vnd.mendeley-document.1+json'
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/documents"
                params = {'limit': limit}
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        items = await response.json()
                        return [self._convert_mendeley_item(item) for item in items]
                    else:
                        raise Exception(f"Library fetch failed: {response.status}")
        except Exception as e:
            logger.error(f"Mendeley library fetch error: {e}")
            raise
    
    def _convert_mendeley_item(self, mendeley_item: Dict) -> BibliographicData:
        """Convert Mendeley item to unified format"""
        # Extract authors
        authors = []
        for author in mendeley_item.get('authors', []):
            if author.get('first_name') and author.get('last_name'):
                authors.append(f"{author['first_name']} {author['last_name']}")
        
        return BibliographicData(
            title=mendeley_item.get('title', ''),
            authors=authors,
            journal=mendeley_item.get('source'),
            year=mendeley_item.get('year'),
            doi=mendeley_item.get('identifiers', {}).get('doi'),
            abstract=mendeley_item.get('abstract'),
            keywords=mendeley_item.get('keywords', []),
            url=mendeley_item.get('websites', [{}])[0].get('url') if mendeley_item.get('websites') else None,
            pages=mendeley_item.get('pages'),
            volume=mendeley_item.get('volume'),
            issue=mendeley_item.get('issue'),
            publisher=mendeley_item.get('publisher'),
            isbn=mendeley_item.get('identifiers', {}).get('isbn'),
            item_type=mendeley_item.get('type', 'article'),
            tags=mendeley_item.get('tags', []),
            date_added=datetime.fromisoformat(mendeley_item.get('created').replace('Z', '+00:00')) if mendeley_item.get('created') else None,
            date_modified=datetime.fromisoformat(mendeley_item.get('last_modified').replace('Z', '+00:00')) if mendeley_item.get('last_modified') else None
        )

class EndNoteIntegration:
    """EndNote integration via file import/export"""
    
    def __init__(self):
        self.supported_formats = ['.enw', '.ris', '.xml']
    
    async def import_from_file(self, file_path: str) -> List[BibliographicData]:
        """Import references from EndNote file"""
        try:
            if file_path.endswith('.enw'):
                return await self._parse_enw_file(file_path)
            elif file_path.endswith('.ris'):
                return await self._parse_ris_file(file_path)
            elif file_path.endswith('.xml'):
                return await self._parse_xml_file(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
        except Exception as e:
            logger.error(f"EndNote import error: {e}")
            raise
    
    async def export_to_file(self, items: List[BibliographicData], 
                           file_path: str, format_type: str = 'ris') -> bool:
        """Export references to EndNote file"""
        try:
            if format_type == 'ris':
                return await self._export_to_ris(items, file_path)
            elif format_type == 'enw':
                return await self._export_to_enw(items, file_path)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
        except Exception as e:
            logger.error(f"EndNote export error: {e}")
            return False
    
    async def _parse_ris_file(self, file_path: str) -> List[BibliographicData]:
        """Parse RIS format file"""
        items = []
        current_item = {}
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line.startswith('TY  -'):
                    if current_item:
                        items.append(self._convert_ris_item(current_item))
                    current_item = {'type': line[6:]}
                elif line.startswith('ER  -'):
                    if current_item:
                        items.append(self._convert_ris_item(current_item))
                        current_item = {}
                elif '  - ' in line:
                    tag, value = line.split('  - ', 1)
                    if tag in current_item:
                        if isinstance(current_item[tag], list):
                            current_item[tag].append(value)
                        else:
                            current_item[tag] = [current_item[tag], value]
                    else:
                        current_item[tag] = value
        
        return items
    
    def _convert_ris_item(self, ris_item: Dict) -> BibliographicData:
        """Convert RIS item to unified format"""
        authors = []
        if 'AU' in ris_item:
            if isinstance(ris_item['AU'], list):
                authors = ris_item['AU']
            else:
                authors = [ris_item['AU']]
        
        return BibliographicData(
            title=ris_item.get('TI', ''),
            authors=authors,
            journal=ris_item.get('JO') or ris_item.get('T2'),
            year=int(ris_item['PY']) if ris_item.get('PY') and ris_item['PY'].isdigit() else None,
            doi=ris_item.get('DO'),
            abstract=ris_item.get('AB'),
            keywords=ris_item.get('KW', []) if isinstance(ris_item.get('KW'), list) else [ris_item.get('KW')] if ris_item.get('KW') else [],
            url=ris_item.get('UR'),
            pages=ris_item.get('SP'),
            volume=ris_item.get('VL'),
            issue=ris_item.get('IS'),
            publisher=ris_item.get('PB'),
            isbn=ris_item.get('SN'),
            item_type=self._map_ris_type(ris_item.get('type', 'JOUR'))
        )
    
    def _map_ris_type(self, ris_type: str) -> str:
        """Map RIS type to unified type"""
        type_mapping = {
            'JOUR': 'article',
            'BOOK': 'book',
            'CHAP': 'chapter',
            'CONF': 'conference',
            'THES': 'thesis',
            'RPRT': 'report'
        }
        return type_mapping.get(ris_type, 'article')
    
    async def _export_to_ris(self, items: List[BibliographicData], file_path: str) -> bool:
        """Export items to RIS format"""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                for item in items:
                    file.write(f"TY  - {self._map_to_ris_type(item.item_type)}\n")
                    file.write(f"TI  - {item.title}\n")
                    
                    for author in item.authors:
                        file.write(f"AU  - {author}\n")
                    
                    if item.journal:
                        file.write(f"JO  - {item.journal}\n")
                    if item.year:
                        file.write(f"PY  - {item.year}\n")
                    if item.doi:
                        file.write(f"DO  - {item.doi}\n")
                    if item.abstract:
                        file.write(f"AB  - {item.abstract}\n")
                    if item.url:
                        file.write(f"UR  - {item.url}\n")
                    if item.pages:
                        file.write(f"SP  - {item.pages}\n")
                    if item.volume:
                        file.write(f"VL  - {item.volume}\n")
                    if item.issue:
                        file.write(f"IS  - {item.issue}\n")
                    if item.publisher:
                        file.write(f"PB  - {item.publisher}\n")
                    
                    for keyword in item.keywords:
                        file.write(f"KW  - {keyword}\n")
                    
                    file.write("ER  -\n\n")
            
            return True
        except Exception as e:
            logger.error(f"RIS export error: {e}")
            return False
    
    def _map_to_ris_type(self, item_type: str) -> str:
        """Map unified type to RIS type"""
        type_mapping = {
            'article': 'JOUR',
            'book': 'BOOK',
            'chapter': 'CHAP',
            'conference': 'CONF',
            'thesis': 'THES',
            'report': 'RPRT'
        }
        return type_mapping.get(item_type, 'JOUR')
    
    async def _parse_enw_file(self, file_path: str) -> List[BibliographicData]:
        """Parse ENW format file (simplified implementation)"""
        # ENW parsing would be implemented here
        # For now, return empty list as placeholder
        logger.warning("ENW parsing not yet implemented")
        return []
    
    async def _parse_xml_file(self, file_path: str) -> List[BibliographicData]:
        """Parse XML format file (simplified implementation)"""
        # XML parsing would be implemented here
        # For now, return empty list as placeholder
        logger.warning("XML parsing not yet implemented")
        return []
    
    async def _export_to_enw(self, items: List[BibliographicData], file_path: str) -> bool:
        """Export to ENW format (simplified implementation)"""
        logger.warning("ENW export not yet implemented")
        return False

class ReferenceManagerService:
    """Unified reference manager service"""
    
    def __init__(self):
        self.zotero = ZoteroIntegration()
        self.mendeley = MendeleyIntegration()
        self.endnote = EndNoteIntegration()
        self.integrations = {
            ReferenceManagerType.ZOTERO: self.zotero,
            ReferenceManagerType.MENDELEY: self.mendeley,
            ReferenceManagerType.ENDNOTE: self.endnote
        }
    
    async def get_authorization_url(self, manager_type: ReferenceManagerType, 
                                  client_id: str, redirect_uri: str) -> str:
        """Get OAuth authorization URL for reference manager"""
        if manager_type == ReferenceManagerType.ENDNOTE:
            raise ValueError("EndNote does not support OAuth authentication")
        
        integration = self.integrations[manager_type]
        return await integration.get_authorization_url(client_id, redirect_uri)
    
    async def exchange_code_for_token(self, manager_type: ReferenceManagerType,
                                    code: str, client_id: str, client_secret: str,
                                    redirect_uri: str) -> AuthCredentials:
        """Exchange authorization code for access token"""
        if manager_type == ReferenceManagerType.ENDNOTE:
            raise ValueError("EndNote does not support OAuth authentication")
        
        integration = self.integrations[manager_type]
        return await integration.exchange_code_for_token(code, client_id, client_secret, redirect_uri)
    
    async def sync_library(self, manager_type: ReferenceManagerType,
                          credentials: Optional[AuthCredentials] = None,
                          file_path: Optional[str] = None,
                          limit: int = 100) -> SyncResult:
        """Synchronize library from reference manager"""
        try:
            start_time = datetime.now()
            errors = []
            
            if manager_type == ReferenceManagerType.ENDNOTE:
                if not file_path:
                    raise ValueError("File path required for EndNote integration")
                items = await self.endnote.import_from_file(file_path)
            else:
                if not credentials:
                    raise ValueError("Credentials required for online reference managers")
                integration = self.integrations[manager_type]
                items = await integration.get_user_library(credentials, limit)
            
            # Here you would typically save items to your database
            # For now, we'll just return the sync result
            
            return SyncResult(
                success=True,
                items_synced=len(items),
                errors=errors,
                last_sync=datetime.now(),
                total_items=len(items)
            )
            
        except Exception as e:
            logger.error(f"Library sync error: {e}")
            return SyncResult(
                success=False,
                items_synced=0,
                errors=[str(e)],
                last_sync=datetime.now(),
                total_items=0
            )
    
    async def add_item(self, manager_type: ReferenceManagerType,
                      item: BibliographicData,
                      credentials: Optional[AuthCredentials] = None,
                      file_path: Optional[str] = None) -> bool:
        """Add item to reference manager"""
        try:
            if manager_type == ReferenceManagerType.ENDNOTE:
                if not file_path:
                    raise ValueError("File path required for EndNote export")
                return await self.endnote.export_to_file([item], file_path)
            else:
                if not credentials:
                    raise ValueError("Credentials required for online reference managers")
                integration = self.integrations[manager_type]
                return await integration.add_item_to_library(credentials, item)
        except Exception as e:
            logger.error(f"Add item error: {e}")
            return False
    
    async def export_library(self, items: List[BibliographicData],
                           file_path: str, format_type: str = 'ris') -> bool:
        """Export library to file"""
        try:
            return await self.endnote.export_to_file(items, file_path, format_type)
        except Exception as e:
            logger.error(f"Export error: {e}")
            return False
    
    def get_supported_managers(self) -> List[str]:
        """Get list of supported reference managers"""
        return [manager.value for manager in ReferenceManagerType]
    
    def validate_credentials(self, credentials: AuthCredentials) -> bool:
        """Validate OAuth credentials"""
        return bool(credentials.access_token)