"""
Zotero Export and Sharing Service

This service handles conversation export with proper citations,
reference sharing between users, and research project reference collections.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.models.zotero_models import (
    ZoteroItem, ZoteroCollection, ZoteroSharedCollection, 
    ZoteroSharedReference, ZoteroConversationExport
)
from backend.services.zotero.zotero_citation_service import ZoteroCitationService
from backend.core.database import get_db


class ZoteroExportSharingService:
    """Service for handling export and sharing functionality"""
    
    def __init__(self, db: Session):
        self.db = db
        self.citation_service = ZoteroCitationService(db)
    
    async def export_conversation_with_citations(
        self,
        user_id: str,
        conversation_id: str,
        conversation_data: Dict[str, Any],
        citation_style: str = "apa"
    ) -> Dict[str, Any]:
        """
        Export conversation with proper citations for referenced papers
        
        Args:
            user_id: ID of the user exporting
            conversation_id: ID of the conversation
            conversation_data: Conversation messages and metadata
            citation_style: Citation style to use (apa, mla, chicago)
            
        Returns:
            Dict containing exported conversation with citations
        """
        try:
            # Extract referenced items from conversation
            referenced_items = await self._extract_referenced_items(
                user_id, conversation_data
            )
            
            # Generate citations for referenced items
            citations = {}
            bibliography = []
            
            for item_id in referenced_items:
                item = self.db.query(ZoteroItem).filter(
                    ZoteroItem.id == item_id,
                    ZoteroItem.user_id == user_id
                ).first()
                
                if item:
                    citation = await self.citation_service.generate_citation(
                        item_id, citation_style
                    )
                    citations[item_id] = citation
                    bibliography.append(citation)
            
            # Process conversation messages to include inline citations
            processed_messages = await self._process_messages_with_citations(
                conversation_data.get("messages", []), citations
            )
            
            # Create export record
            export_record = ZoteroConversationExport(
                id=str(uuid.uuid4()),
                user_id=user_id,
                conversation_id=conversation_id,
                export_data={
                    "conversation": {
                        "id": conversation_id,
                        "title": conversation_data.get("title", "Untitled Conversation"),
                        "created_at": conversation_data.get("created_at"),
                        "messages": processed_messages
                    },
                    "citations": citations,
                    "bibliography": sorted(set(bibliography)),
                    "citation_style": citation_style,
                    "referenced_items": list(referenced_items)
                },
                citation_style=citation_style,
                created_at=datetime.utcnow()
            )
            
            self.db.add(export_record)
            self.db.commit()
            
            return {
                "export_id": export_record.id,
                "conversation": export_record.export_data["conversation"],
                "bibliography": export_record.export_data["bibliography"],
                "citation_count": len(citations),
                "export_date": export_record.created_at.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to export conversation: {str(e)}")
    
    async def share_reference_with_user(
        self,
        owner_id: str,
        target_user_id: str,
        reference_id: str,
        permission_level: str = "read",
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Share a reference with another user
        
        Args:
            owner_id: ID of the user sharing the reference
            target_user_id: ID of the user receiving the share
            reference_id: ID of the reference to share
            permission_level: Permission level (read, comment, edit)
            message: Optional message to include with the share
            
        Returns:
            Dict containing share details
        """
        try:
            # Verify reference exists and belongs to owner
            reference = self.db.query(ZoteroItem).filter(
                ZoteroItem.id == reference_id,
                ZoteroItem.user_id == owner_id
            ).first()
            
            if not reference:
                raise ValueError("Reference not found or access denied")
            
            # Check if already shared
            existing_share = self.db.query(ZoteroSharedReference).filter(
                ZoteroSharedReference.reference_id == reference_id,
                ZoteroSharedReference.shared_with_user_id == target_user_id
            ).first()
            
            if existing_share:
                # Update existing share
                existing_share.permission_level = permission_level
                existing_share.message = message
                existing_share.updated_at = datetime.utcnow()
                share_record = existing_share
            else:
                # Create new share
                share_record = ZoteroSharedReference(
                    id=str(uuid.uuid4()),
                    reference_id=reference_id,
                    owner_user_id=owner_id,
                    shared_with_user_id=target_user_id,
                    permission_level=permission_level,
                    message=message,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(share_record)
            
            self.db.commit()
            
            return {
                "share_id": share_record.id,
                "reference_id": reference_id,
                "reference_title": reference.title,
                "shared_with": target_user_id,
                "permission_level": permission_level,
                "message": message,
                "shared_at": share_record.created_at.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to share reference: {str(e)}")
    
    async def create_research_project_collection(
        self,
        user_id: str,
        project_name: str,
        description: Optional[str] = None,
        reference_ids: Optional[List[str]] = None,
        collaborator_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a research project reference collection
        
        Args:
            user_id: ID of the user creating the project
            project_name: Name of the research project
            description: Optional project description
            reference_ids: List of reference IDs to include
            collaborator_ids: List of user IDs to collaborate with
            
        Returns:
            Dict containing project collection details
        """
        try:
            # Create shared collection
            collection = ZoteroSharedCollection(
                id=str(uuid.uuid4()),
                name=project_name,
                description=description,
                owner_user_id=user_id,
                collection_type="research_project",
                is_public=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(collection)
            self.db.flush()  # Get the ID
            
            # Add references to collection
            if reference_ids:
                await self._add_references_to_collection(
                    collection.id, reference_ids, user_id
                )
            
            # Add collaborators
            if collaborator_ids:
                await self._add_collaborators_to_collection(
                    collection.id, collaborator_ids, user_id
                )
            
            self.db.commit()
            
            return {
                "collection_id": collection.id,
                "name": project_name,
                "description": description,
                "owner_id": user_id,
                "reference_count": len(reference_ids) if reference_ids else 0,
                "collaborator_count": len(collaborator_ids) if collaborator_ids else 0,
                "created_at": collection.created_at.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create research project: {str(e)}")
    
    async def get_shared_references(
        self,
        user_id: str,
        include_owned: bool = True,
        include_received: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get references shared by or with the user
        
        Args:
            user_id: ID of the user
            include_owned: Include references shared by the user
            include_received: Include references shared with the user
            
        Returns:
            Dict containing shared and received references
        """
        result = {"shared_by_me": [], "shared_with_me": []}
        
        if include_owned:
            # References shared by the user
            shared_by_query = self.db.query(ZoteroSharedReference).filter(
                ZoteroSharedReference.owner_user_id == user_id
            ).all()
            
            for share in shared_by_query:
                reference = self.db.query(ZoteroItem).filter(
                    ZoteroItem.id == share.reference_id
                ).first()
                
                if reference:
                    result["shared_by_me"].append({
                        "share_id": share.id,
                        "reference": {
                            "id": reference.id,
                            "title": reference.title,
                            "authors": reference.creators,
                            "year": reference.publication_year
                        },
                        "shared_with": share.shared_with_user_id,
                        "permission_level": share.permission_level,
                        "shared_at": share.created_at.isoformat()
                    })
        
        if include_received:
            # References shared with the user
            shared_with_query = self.db.query(ZoteroSharedReference).filter(
                ZoteroSharedReference.shared_with_user_id == user_id
            ).all()
            
            for share in shared_with_query:
                reference = self.db.query(ZoteroItem).filter(
                    ZoteroItem.id == share.reference_id
                ).first()
                
                if reference:
                    result["shared_with_me"].append({
                        "share_id": share.id,
                        "reference": {
                            "id": reference.id,
                            "title": reference.title,
                            "authors": reference.creators,
                            "year": reference.publication_year
                        },
                        "shared_by": share.owner_user_id,
                        "permission_level": share.permission_level,
                        "message": share.message,
                        "shared_at": share.created_at.isoformat()
                    })
        
        return result
    
    async def get_research_project_collections(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get research project collections for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of research project collections
        """
        collections = self.db.query(ZoteroSharedCollection).filter(
            or_(
                ZoteroSharedCollection.owner_user_id == user_id,
                ZoteroSharedCollection.collaborators.any(user_id=user_id)
            )
        ).all()
        
        result = []
        for collection in collections:
            # Get reference count
            reference_count = len(collection.references) if collection.references else 0
            
            # Get collaborator count
            collaborator_count = len(collection.collaborators) if collection.collaborators else 0
            
            result.append({
                "collection_id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "owner_id": collection.owner_user_id,
                "is_owner": collection.owner_user_id == user_id,
                "reference_count": reference_count,
                "collaborator_count": collaborator_count,
                "created_at": collection.created_at.isoformat(),
                "updated_at": collection.updated_at.isoformat()
            })
        
        return result
    
    async def _extract_referenced_items(
        self,
        user_id: str,
        conversation_data: Dict[str, Any]
    ) -> set:
        """Extract referenced item IDs from conversation data"""
        referenced_items = set()
        
        messages = conversation_data.get("messages", [])
        for message in messages:
            content = message.get("content", "")
            
            # Look for reference patterns in message content
            # This could be enhanced with more sophisticated parsing
            if "zotero_ref:" in content:
                import re
                refs = re.findall(r'zotero_ref:([a-f0-9-]+)', content)
                referenced_items.update(refs)
            
            # Check message metadata for references
            metadata = message.get("metadata", {})
            if "referenced_items" in metadata:
                referenced_items.update(metadata["referenced_items"])
        
        return referenced_items
    
    async def _process_messages_with_citations(
        self,
        messages: List[Dict[str, Any]],
        citations: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Process messages to include inline citations"""
        processed_messages = []
        
        for message in messages:
            content = message.get("content", "")
            
            # Replace reference patterns with citations
            for item_id, citation in citations.items():
                content = content.replace(
                    f"zotero_ref:{item_id}",
                    f"({citation})"
                )
            
            processed_message = message.copy()
            processed_message["content"] = content
            processed_messages.append(processed_message)
        
        return processed_messages
    
    async def _add_references_to_collection(
        self,
        collection_id: str,
        reference_ids: List[str],
        user_id: str
    ):
        """Add references to a collection"""
        # This would typically involve a many-to-many relationship
        # For now, we'll store reference IDs in the collection metadata
        collection = self.db.query(ZoteroSharedCollection).filter(
            ZoteroSharedCollection.id == collection_id
        ).first()
        
        if collection:
            if not collection.metadata:
                collection.metadata = {}
            
            collection.metadata["reference_ids"] = reference_ids
            collection.updated_at = datetime.utcnow()
    
    async def _add_collaborators_to_collection(
        self,
        collection_id: str,
        collaborator_ids: List[str],
        owner_id: str
    ):
        """Add collaborators to a collection"""
        # This would typically involve a many-to-many relationship
        # For now, we'll store collaborator IDs in the collection metadata
        collection = self.db.query(ZoteroSharedCollection).filter(
            ZoteroSharedCollection.id == collection_id
        ).first()
        
        if collection:
            if not collection.metadata:
                collection.metadata = {}
            
            collection.metadata["collaborator_ids"] = collaborator_ids
            collection.updated_at = datetime.utcnow()