#!/usr/bin/env python3
"""
Comprehensive integration test for Zotero Reference Sharing System
Tests the complete workflow of reference sharing, collections, and discussions.
"""
import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from services.zotero.zotero_reference_sharing_service import ZoteroReferenceSharingService
from models.zotero_models import (
    ZoteroItem, ZoteroLibrary, ZoteroConnection,
    ZoteroUserReferenceShare, ZoteroSharedReferenceCollection,
    ZoteroCollectionCollaborator, ZoteroSharedCollectionReference,
    ZoteroReferenceDiscussion, ZoteroSharingNotification
)
from core.database import Base

# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test_zotero_reference_sharing.db"

class ZoteroReferenceSharingIntegrationTest:
    """Integration test for Zotero Reference Sharing System"""
    
    def __init__(self):
        self.engine = create_engine(TEST_DATABASE_URL, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.test_data = {}
        
    def setup_database(self):
        """Create test database and tables"""
        print("Setting up test database...")
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
        
        # Create zotero schema if it doesn't exist (for PostgreSQL compatibility)
        with self.engine.connect() as conn:
            try:
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS zotero"))
                conn.commit()
            except Exception:
                # SQLite doesn't support schemas, ignore the error
                pass
        
        print("✓ Database setup complete")
    
    def create_test_data(self):
        """Create test data for the integration test"""
        print("Creating test data...")
        
        db = self.SessionLocal()
        try:
            # Create test users (simulated)
            self.test_data['users'] = {
                'user1': 'test-user-1',
                'user2': 'test-user-2',
                'user3': 'test-user-3'
            }
            
            # Create test library
            library = ZoteroLibrary(
                id='test-library-1',
                user_id=self.test_data['users']['user1'],
                zotero_library_id='12345',
                library_type='user',
                library_name='Test Library',
                access_level='owner'
            )
            db.add(library)
            
            # Create test connection
            connection = ZoteroConnection(
                id='test-connection-1',
                user_id=self.test_data['users']['user1'],
                access_token='test-token',
                refresh_token='test-refresh',
                token_expires_at=datetime.utcnow(),
                connection_status='connected'
            )
            db.add(connection)
            
            # Create test references
            references = []
            for i in range(3):
                ref = ZoteroItem(
                    id=f'test-ref-{i+1}',
                    library_id='test-library-1',
                    zotero_item_key=f'TESTKEY{i+1}',
                    item_type='article',
                    title=f'Test Research Paper {i+1}',
                    creators=[{
                        'firstName': f'Author{i+1}',
                        'lastName': f'Lastname{i+1}',
                        'creatorType': 'author'
                    }],
                    publication_title=f'Test Journal {i+1}',
                    publication_year=2024,
                    doi=f'10.1000/test{i+1}',
                    abstract_note=f'This is the abstract for test paper {i+1}',
                    tags=[f'tag{i+1}', 'test'],
                    extra_fields={'test': True}
                )
                references.append(ref)
                db.add(ref)
            
            self.test_data['references'] = references
            
            db.commit()
            print("✓ Test data created")
            
        except Exception as e:
            db.rollback()
            print(f"✗ Failed to create test data: {e}")
            raise
        finally:
            db.close()
    
    async def test_reference_sharing_workflow(self):
        """Test the complete reference sharing workflow"""
        print("\n=== Testing Reference Sharing Workflow ===")
        
        db = self.SessionLocal()
        service = ZoteroReferenceSharingService(db)
        
        try:
            # Test 1: Share a reference
            print("1. Testing reference sharing...")
            share_result = await service.share_reference_with_user(
                reference_id='test-ref-1',
                owner_user_id=self.test_data['users']['user1'],
                shared_with_user_id=self.test_data['users']['user2'],
                permission_level='read',
                share_message='Check out this interesting paper!'
            )
            
            assert share_result['reference_id'] == 'test-ref-1'
            assert share_result['shared_with_user_id'] == self.test_data['users']['user2']
            print("✓ Reference shared successfully")
            
            # Test 2: Get shared references
            print("2. Testing get shared references...")
            shared_refs = await service.get_shared_references(
                self.test_data['users']['user1'], as_owner=True
            )
            
            assert len(shared_refs) == 1
            assert shared_refs[0]['reference_title'] == 'Test Research Paper 1'
            print("✓ Retrieved shared references successfully")
            
            # Test 3: Get references shared with user
            shared_with_refs = await service.get_shared_references(
                self.test_data['users']['user2'], as_owner=False
            )
            
            assert len(shared_with_refs) == 1
            assert shared_with_refs[0]['owner_user_id'] == self.test_data['users']['user1']
            print("✓ Retrieved references shared with user successfully")
            
        except Exception as e:
            print(f"✗ Reference sharing workflow failed: {e}")
            raise
        finally:
            db.close()
    
    async def test_shared_collections_workflow(self):
        """Test the shared collections workflow"""
        print("\n=== Testing Shared Collections Workflow ===")
        
        db = self.SessionLocal()
        service = ZoteroReferenceSharingService(db)
        
        try:
            # Test 1: Create shared collection
            print("1. Testing collection creation...")
            collection_result = await service.create_shared_collection(
                name='Research Project Alpha',
                owner_user_id=self.test_data['users']['user1'],
                description='A collaborative research project on AI',
                collection_type='research_project',
                is_public=False
            )
            
            collection_id = collection_result['collection_id']
            assert collection_result['name'] == 'Research Project Alpha'
            print("✓ Collection created successfully")
            
            # Test 2: Add collaborator
            print("2. Testing add collaborator...")
            collaborator_result = await service.add_collaborator_to_collection(
                collection_id=collection_id,
                user_id=self.test_data['users']['user2'],
                invited_by=self.test_data['users']['user1'],
                permission_level='edit',
                role='collaborator',
                invitation_message='Join my research project!'
            )
            
            assert collaborator_result['user_id'] == self.test_data['users']['user2']
            assert collaborator_result['permission_level'] == 'edit'
            print("✓ Collaborator added successfully")
            
            # Test 3: Add reference to collection
            print("3. Testing add reference to collection...")
            ref_result = await service.add_reference_to_collection(
                collection_id=collection_id,
                reference_id='test-ref-1',
                added_by=self.test_data['users']['user1'],
                notes='This is a key paper for our research',
                tags=['important', 'foundational'],
                is_featured=True
            )
            
            assert ref_result['reference_id'] == 'test-ref-1'
            print("✓ Reference added to collection successfully")
            
            # Test 4: Get user collections
            print("4. Testing get user collections...")
            user_collections = await service.get_user_collections(
                self.test_data['users']['user1']
            )
            
            assert len(user_collections) == 1
            assert user_collections[0]['name'] == 'Research Project Alpha'
            assert user_collections[0]['reference_count'] == 1
            print("✓ Retrieved user collections successfully")
            
            # Test 5: Get collection references
            print("5. Testing get collection references...")
            collection_refs = await service.get_collection_references(
                collection_id=collection_id,
                user_id=self.test_data['users']['user1']
            )
            
            assert len(collection_refs) == 1
            assert collection_refs[0]['reference_title'] == 'Test Research Paper 1'
            assert collection_refs[0]['is_featured'] == True
            print("✓ Retrieved collection references successfully")
            
            # Store collection_id for discussion tests
            self.test_data['collection_id'] = collection_id
            
        except Exception as e:
            print(f"✗ Shared collections workflow failed: {e}")
            raise
        finally:
            db.close()
    
    async def test_discussions_workflow(self):
        """Test the discussions workflow"""
        print("\n=== Testing Discussions Workflow ===")
        
        db = self.SessionLocal()
        service = ZoteroReferenceSharingService(db)
        
        try:
            # Test 1: Add discussion comment
            print("1. Testing add discussion...")
            discussion_result = await service.add_reference_discussion(
                reference_id='test-ref-1',
                user_id=self.test_data['users']['user1'],
                content='This paper provides excellent insights into the topic!',
                discussion_type='comment',
                collection_id=self.test_data['collection_id']
            )
            
            discussion_id = discussion_result['discussion_id']
            assert discussion_result['content'] == 'This paper provides excellent insights into the topic!'
            print("✓ Discussion added successfully")
            
            # Test 2: Add reply to discussion
            print("2. Testing add reply to discussion...")
            reply_result = await service.add_reference_discussion(
                reference_id='test-ref-1',
                user_id=self.test_data['users']['user2'],
                content='I agree! The methodology is particularly interesting.',
                discussion_type='comment',
                collection_id=self.test_data['collection_id'],
                parent_discussion_id=discussion_id
            )
            
            assert reply_result['parent_discussion_id'] == discussion_id
            print("✓ Reply added successfully")
            
            # Test 3: Get reference discussions
            print("3. Testing get reference discussions...")
            discussions = await service.get_reference_discussions(
                reference_id='test-ref-1',
                user_id=self.test_data['users']['user1'],
                collection_id=self.test_data['collection_id']
            )
            
            assert len(discussions) == 2
            assert discussions[0]['discussion_type'] == 'comment'
            print("✓ Retrieved discussions successfully")
            
        except Exception as e:
            print(f"✗ Discussions workflow failed: {e}")
            raise
        finally:
            db.close()
    
    async def test_notifications_workflow(self):
        """Test the notifications workflow"""
        print("\n=== Testing Notifications Workflow ===")
        
        db = self.SessionLocal()
        service = ZoteroReferenceSharingService(db)
        
        try:
            # Test 1: Get user notifications
            print("1. Testing get user notifications...")
            notifications = await service.get_user_notifications(
                user_id=self.test_data['users']['user2'],
                unread_only=False
            )
            
            # Should have notifications from sharing and collaboration
            assert len(notifications) > 0
            print(f"✓ Retrieved {len(notifications)} notifications")
            
            # Test 2: Mark notification as read
            if notifications:
                print("2. Testing mark notification as read...")
                notification_id = notifications[0]['notification_id']
                success = await service.mark_notification_as_read(
                    notification_id=notification_id,
                    user_id=self.test_data['users']['user2']
                )
                
                assert success == True
                print("✓ Notification marked as read successfully")
            
        except Exception as e:
            print(f"✗ Notifications workflow failed: {e}")
            raise
        finally:
            db.close()
    
    async def test_advanced_sharing_features(self):
        """Test advanced sharing features"""
        print("\n=== Testing Advanced Sharing Features ===")
        
        db = self.SessionLocal()
        service = ZoteroReferenceSharingService(db)
        
        try:
            # Test 1: Share multiple references
            print("1. Testing multiple reference sharing...")
            for i in range(2, 4):  # Share refs 2 and 3
                await service.share_reference_with_user(
                    reference_id=f'test-ref-{i}',
                    owner_user_id=self.test_data['users']['user1'],
                    shared_with_user_id=self.test_data['users']['user3'],
                    permission_level='comment',
                    share_message=f'Reference {i} for your review'
                )
            
            shared_refs = await service.get_shared_references(
                self.test_data['users']['user1'], as_owner=True
            )
            
            # Should now have 3 shared references total
            assert len(shared_refs) == 3
            print("✓ Multiple references shared successfully")
            
            # Test 2: Create public collection
            print("2. Testing public collection creation...")
            public_collection = await service.create_shared_collection(
                name='Public Research Collection',
                owner_user_id=self.test_data['users']['user1'],
                description='A public collection for community research',
                collection_type='bibliography',
                is_public=True
            )
            
            assert public_collection['is_public'] == True
            assert public_collection['access_code'] is not None
            print("✓ Public collection created successfully")
            
            # Test 3: Add multiple references to collection
            print("3. Testing multiple references in collection...")
            collection_id = self.test_data['collection_id']
            
            for i in range(2, 4):
                await service.add_reference_to_collection(
                    collection_id=collection_id,
                    reference_id=f'test-ref-{i}',
                    added_by=self.test_data['users']['user1'],
                    notes=f'Reference {i} notes',
                    tags=[f'ref{i}', 'batch-added']
                )
            
            collection_refs = await service.get_collection_references(
                collection_id=collection_id,
                user_id=self.test_data['users']['user1']
            )
            
            assert len(collection_refs) == 3  # Now has 3 references
            print("✓ Multiple references added to collection successfully")
            
        except Exception as e:
            print(f"✗ Advanced sharing features failed: {e}")
            raise
        finally:
            db.close()
    
    def cleanup_database(self):
        """Clean up test database"""
        print("\nCleaning up test database...")
        try:
            os.remove("test_zotero_reference_sharing.db")
            print("✓ Test database cleaned up")
        except FileNotFoundError:
            print("✓ No cleanup needed")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Zotero Reference Sharing Integration Tests")
        print("=" * 60)
        
        try:
            # Setup
            self.setup_database()
            self.create_test_data()
            
            # Run test workflows
            await self.test_reference_sharing_workflow()
            await self.test_shared_collections_workflow()
            await self.test_discussions_workflow()
            await self.test_notifications_workflow()
            await self.test_advanced_sharing_features()
            
            print("\n" + "=" * 60)
            print("🎉 All integration tests passed successfully!")
            print("✓ Reference sharing between users")
            print("✓ Shared collections and collaboration")
            print("✓ Discussion and annotation features")
            print("✓ Notification system")
            print("✓ Advanced sharing features")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Integration tests failed: {e}")
            return False
        
        finally:
            self.cleanup_database()

async def main():
    """Main test runner"""
    test_runner = ZoteroReferenceSharingIntegrationTest()
    success = await test_runner.run_all_tests()
    
    if success:
        print("\n🎯 Task 11.2 Implementation Complete!")
        print("The Zotero Reference Sharing System is fully functional with:")
        print("• Reference sharing between AI Scholar users ✓")
        print("• Shared reference collections and projects ✓") 
        print("• Collaborative annotation and discussion features ✓")
        print("• Comprehensive test coverage ✓")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)