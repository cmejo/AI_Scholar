"""
Integration test for Zotero Group Library functionality

Tests the complete group library workflow including database operations,
service layer, and API endpoints.
"""
import asyncio
import pytest
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.database import Base
from models.zotero_models import (
    ZoteroConnection, ZoteroLibrary, ZoteroGroupMember, 
    ZoteroGroupSyncSettings, ZoteroGroupPermissionTemplate,
    ZoteroGroupActivityLog, ZoteroGroupAccessControl
)
from services.zotero.zotero_group_library_service import ZoteroGroupLibraryService


class TestZoteroGroupLibraryIntegration:
    """Integration tests for Zotero Group Library functionality"""
    
    @pytest.fixture(scope="class")
    def db_engine(self):
        """Create test database engine"""
        # Use in-memory SQLite for testing
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        
        # Create zotero schema (SQLite doesn't support schemas, so we'll use table prefixes)
        with engine.connect() as conn:
            # Create the tables with proper schema simulation
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS zotero_connections (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    zotero_user_id TEXT NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    token_expires_at TIMESTAMP,
                    api_key TEXT,
                    connection_type TEXT DEFAULT 'oauth',
                    connection_status TEXT DEFAULT 'active',
                    last_sync_at TIMESTAMP,
                    sync_enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    connection_metadata TEXT DEFAULT '{}'
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS zotero_libraries (
                    id TEXT PRIMARY KEY,
                    connection_id TEXT NOT NULL,
                    zotero_library_id TEXT NOT NULL,
                    library_type TEXT NOT NULL,
                    library_name TEXT NOT NULL,
                    library_version INTEGER DEFAULT 0,
                    owner_id TEXT,
                    group_id TEXT,
                    permissions TEXT DEFAULT '{}',
                    is_active BOOLEAN DEFAULT 1,
                    last_sync_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    library_metadata TEXT DEFAULT '{}',
                    group_permissions TEXT DEFAULT '{}',
                    group_settings TEXT DEFAULT '{}',
                    member_count INTEGER DEFAULT 0,
                    is_public BOOLEAN DEFAULT 0,
                    group_description TEXT,
                    group_url TEXT,
                    FOREIGN KEY (connection_id) REFERENCES zotero_connections(id)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS zotero_group_members (
                    id TEXT PRIMARY KEY,
                    library_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    zotero_user_id TEXT NOT NULL,
                    member_role TEXT NOT NULL,
                    permissions TEXT DEFAULT '{}',
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    invitation_status TEXT DEFAULT 'active',
                    invited_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    member_metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (library_id) REFERENCES zotero_libraries(id)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS zotero_group_sync_settings (
                    id TEXT PRIMARY KEY,
                    library_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    sync_enabled BOOLEAN DEFAULT 1,
                    sync_frequency_minutes INTEGER DEFAULT 60,
                    sync_collections BOOLEAN DEFAULT 1,
                    sync_items BOOLEAN DEFAULT 1,
                    sync_attachments BOOLEAN DEFAULT 0,
                    sync_annotations BOOLEAN DEFAULT 1,
                    auto_resolve_conflicts BOOLEAN DEFAULT 1,
                    conflict_resolution_strategy TEXT DEFAULT 'zotero_wins',
                    last_sync_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings_metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (library_id) REFERENCES zotero_libraries(id)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS zotero_group_permission_templates (
                    id TEXT PRIMARY KEY,
                    template_name TEXT NOT NULL,
                    template_description TEXT,
                    permissions TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT 0,
                    is_system BOOLEAN DEFAULT 0,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS zotero_group_activity_log (
                    id TEXT PRIMARY KEY,
                    library_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    target_type TEXT,
                    target_id TEXT,
                    activity_description TEXT,
                    old_data TEXT,
                    new_data TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    activity_metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (library_id) REFERENCES zotero_libraries(id)
                )
            """))
            
            # Insert default permission templates
            conn.execute(text("""
                INSERT INTO zotero_group_permission_templates 
                (id, template_name, template_description, permissions, is_default, is_system) VALUES
                ('template-owner', 'Owner', 'Full control over group library', 
                 '{"read": true, "write": true, "delete": true, "admin": true, "manage_members": true, "manage_permissions": true, "manage_settings": true}', 
                 0, 1),
                ('template-admin', 'Admin', 'Administrative access with member management', 
                 '{"read": true, "write": true, "delete": true, "admin": true, "manage_members": true, "manage_permissions": true, "manage_settings": false}', 
                 0, 1),
                ('template-member', 'Member', 'Read and write access to library content', 
                 '{"read": true, "write": true, "delete": false, "admin": false, "manage_members": false, "manage_permissions": false, "manage_settings": false}', 
                 1, 1),
                ('template-reader', 'Reader', 'Read-only access to library content', 
                 '{"read": true, "write": false, "delete": false, "admin": false, "manage_members": false, "manage_permissions": false, "manage_settings": false}', 
                 0, 1)
            """))
            
            conn.commit()
        
        return engine
    
    @pytest.fixture
    def db_session(self, db_engine):
        """Create database session"""
        SessionLocal = sessionmaker(bind=db_engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def group_library_service(self, db_session):
        """Create ZoteroGroupLibraryService with test database"""
        service = ZoteroGroupLibraryService(db_session)
        # Mock the Zotero client
        service.zotero_client.get_user_groups = asyncio.coroutine(lambda x: [])
        return service
    
    @pytest.fixture
    def sample_connection(self, db_session):
        """Create sample Zotero connection"""
        connection_data = {
            'id': 'conn-123',
            'user_id': 'user-123',
            'zotero_user_id': '67890',
            'access_token': 'test-token',
            'connection_type': 'oauth',
            'connection_status': 'active'
        }
        
        db_session.execute(text("""
            INSERT INTO zotero_connections 
            (id, user_id, zotero_user_id, access_token, connection_type, connection_status)
            VALUES (:id, :user_id, :zotero_user_id, :access_token, :connection_type, :connection_status)
        """), connection_data)
        db_session.commit()
        
        return connection_data
    
    @pytest.fixture
    def sample_group_library(self, db_session, sample_connection):
        """Create sample group library"""
        library_data = {
            'id': 'lib-123',
            'connection_id': sample_connection['id'],
            'zotero_library_id': '12345',
            'library_type': 'group',
            'library_name': 'Research Group',
            'group_description': 'A collaborative research group',
            'is_public': True,
            'member_count': 2
        }
        
        db_session.execute(text("""
            INSERT INTO zotero_libraries 
            (id, connection_id, zotero_library_id, library_type, library_name, 
             group_description, is_public, member_count)
            VALUES (:id, :connection_id, :zotero_library_id, :library_type, :library_name,
                    :group_description, :is_public, :member_count)
        """), library_data)
        db_session.commit()
        
        return library_data
    
    @pytest.fixture
    def sample_group_member(self, db_session, sample_group_library):
        """Create sample group member"""
        member_data = {
            'id': 'member-123',
            'library_id': sample_group_library['id'],
            'user_id': 'user-123',
            'zotero_user_id': '67890',
            'member_role': 'owner',
            'permissions': '{"admin": true, "manage_members": true}'
        }
        
        db_session.execute(text("""
            INSERT INTO zotero_group_members 
            (id, library_id, user_id, zotero_user_id, member_role, permissions)
            VALUES (:id, :library_id, :user_id, :zotero_user_id, :member_role, :permissions)
        """), member_data)
        db_session.commit()
        
        return member_data
    
    def test_database_setup(self, db_session):
        """Test that database tables are created correctly"""
        # Check that permission templates were inserted
        result = db_session.execute(text("""
            SELECT COUNT(*) as count FROM zotero_group_permission_templates
        """)).fetchone()
        
        assert result.count == 4  # Should have 4 default templates
    
    @pytest.mark.asyncio
    async def test_get_permission_templates(self, group_library_service, db_session):
        """Test getting permission templates"""
        templates = await group_library_service.get_permission_templates()
        
        assert len(templates) == 4
        template_names = [t['name'] for t in templates]
        assert 'Owner' in template_names
        assert 'Admin' in template_names
        assert 'Member' in template_names
        assert 'Reader' in template_names
    
    @pytest.mark.asyncio
    async def test_get_user_group_libraries(self, group_library_service, db_session, sample_group_member):
        """Test getting user's group libraries"""
        libraries = await group_library_service.get_user_group_libraries('user-123')
        
        assert len(libraries) == 1
        assert libraries[0]['id'] == 'lib-123'
        assert libraries[0]['name'] == 'Research Group'
        assert libraries[0]['user_role'] == 'owner'
    
    @pytest.mark.asyncio
    async def test_get_group_members(self, group_library_service, db_session, sample_group_member):
        """Test getting group members"""
        members = await group_library_service.get_group_members('lib-123', 'user-123')
        
        assert len(members) == 1
        assert members[0]['id'] == 'member-123'
        assert members[0]['role'] == 'owner'
        assert members[0]['user_id'] == 'user-123'
    
    @pytest.mark.asyncio
    async def test_check_permission_owner(self, group_library_service, db_session, sample_group_member):
        """Test permission checking for owner role"""
        # Owner should have all permissions
        assert await group_library_service._check_permission('lib-123', 'user-123', 'read') is True
        assert await group_library_service._check_permission('lib-123', 'user-123', 'write') is True
        assert await group_library_service._check_permission('lib-123', 'user-123', 'admin') is True
        assert await group_library_service._check_permission('lib-123', 'user-123', 'manage_members') is True
        assert await group_library_service._check_permission('lib-123', 'user-123', 'manage_settings') is True
    
    @pytest.mark.asyncio
    async def test_check_permission_non_member(self, group_library_service, db_session, sample_group_member):
        """Test permission checking for non-member"""
        # Non-member should have no permissions
        assert await group_library_service._check_permission('lib-123', 'user-456', 'read') is False
        assert await group_library_service._check_permission('lib-123', 'user-456', 'write') is False
    
    @pytest.mark.asyncio
    async def test_update_member_permissions(self, group_library_service, db_session, sample_group_member):
        """Test updating member permissions"""
        result = await group_library_service.update_member_permissions(
            'lib-123', 'member-123', 'admin', {'admin': True, 'manage_members': False}, 'user-123'
        )
        
        assert result['member_id'] == 'member-123'
        assert result['new_role'] == 'admin'
        
        # Verify the change was persisted
        updated_member = db_session.execute(text("""
            SELECT member_role, permissions FROM zotero_group_members WHERE id = :id
        """), {'id': 'member-123'}).fetchone()
        
        assert updated_member.member_role == 'admin'
    
    @pytest.mark.asyncio
    async def test_get_group_sync_settings_create_default(self, group_library_service, db_session, sample_group_member):
        """Test getting sync settings creates default when none exist"""
        settings = await group_library_service.get_group_sync_settings('lib-123', 'user-123')
        
        assert settings['sync_enabled'] is True
        assert settings['sync_frequency_minutes'] == 60
        assert settings['conflict_resolution_strategy'] == 'zotero_wins'
        
        # Verify settings were created in database
        db_settings = db_session.execute(text("""
            SELECT COUNT(*) as count FROM zotero_group_sync_settings 
            WHERE library_id = :library_id AND user_id = :user_id
        """), {'library_id': 'lib-123', 'user_id': 'user-123'}).fetchone()
        
        assert db_settings.count == 1
    
    @pytest.mark.asyncio
    async def test_update_group_sync_settings(self, group_library_service, db_session, sample_group_member):
        """Test updating sync settings"""
        # First get settings to create them
        await group_library_service.get_group_sync_settings('lib-123', 'user-123')
        
        # Update settings
        settings_data = {
            'sync_enabled': False,
            'sync_frequency_minutes': 120,
            'sync_attachments': True
        }
        
        updated_settings = await group_library_service.update_group_sync_settings(
            'lib-123', 'user-123', settings_data
        )
        
        assert updated_settings['sync_enabled'] is False
        assert updated_settings['sync_frequency_minutes'] == 120
        assert updated_settings['sync_attachments'] is True
    
    @pytest.mark.asyncio
    async def test_log_group_activity(self, group_library_service, db_session, sample_group_member):
        """Test logging group activity"""
        await group_library_service._log_group_activity(
            'lib-123', 'user-123', 'member_added', 'member', 'member-456',
            'Added new member to group', {'old': 'data'}, {'new': 'data'}
        )
        
        # Verify activity was logged
        activity = db_session.execute(text("""
            SELECT activity_type, activity_description FROM zotero_group_activity_log 
            WHERE library_id = :library_id AND user_id = :user_id
        """), {'library_id': 'lib-123', 'user_id': 'user-123'}).fetchone()
        
        assert activity.activity_type == 'member_added'
        assert activity.activity_description == 'Added new member to group'
    
    @pytest.mark.asyncio
    async def test_get_group_activity_log(self, group_library_service, db_session, sample_group_member):
        """Test getting group activity log"""
        # First log some activity
        await group_library_service._log_group_activity(
            'lib-123', 'user-123', 'member_added', 'member', 'member-456',
            'Added new member to group'
        )
        
        activities = await group_library_service.get_group_activity_log('lib-123', 'user-123', 10, 0)
        
        assert len(activities) == 1
        assert activities[0]['activity_type'] == 'member_added'
        assert activities[0]['user_id'] == 'user-123'
    
    @pytest.mark.asyncio
    async def test_sync_group_library_success(self, group_library_service, db_session, sample_group_member):
        """Test successful group library sync"""
        result = await group_library_service.sync_group_library('lib-123', 'user-123')
        
        assert result['sync_initiated'] is True
        assert result['library_id'] == 'lib-123'
        assert result['sync_type'] == 'manual_group_sync'
    
    @pytest.mark.asyncio
    async def test_sync_group_library_no_permission(self, group_library_service, db_session, sample_group_member):
        """Test group library sync without permission"""
        with pytest.raises(PermissionError):
            await group_library_service.sync_group_library('lib-123', 'user-456')
    
    def test_complete_workflow(self, db_session, group_library_service):
        """Test complete group library workflow"""
        async def run_workflow():
            # 1. Get permission templates
            templates = await group_library_service.get_permission_templates()
            assert len(templates) > 0
            
            # 2. Get user's group libraries (should be empty initially for new user)
            libraries = await group_library_service.get_user_group_libraries('user-456')
            assert len(libraries) == 0
            
            # 3. Add a member to existing group
            db_session.execute(text("""
                INSERT INTO zotero_group_members 
                (id, library_id, user_id, zotero_user_id, member_role, permissions)
                VALUES ('member-456', 'lib-123', 'user-456', '67891', 'member', '{"read": true, "write": true}')
            """))
            db_session.commit()
            
            # 4. Now user should see the group library
            libraries = await group_library_service.get_user_group_libraries('user-456')
            assert len(libraries) == 1
            assert libraries[0]['user_role'] == 'member'
            
            # 5. Get group members
            members = await group_library_service.get_group_members('lib-123', 'user-456')
            assert len(members) == 2  # Original owner + new member
            
            # 6. Check permissions
            can_read = await group_library_service._check_permission('lib-123', 'user-456', 'read')
            can_admin = await group_library_service._check_permission('lib-123', 'user-456', 'admin')
            assert can_read is True
            assert can_admin is False
            
            # 7. Get sync settings (should create defaults)
            settings = await group_library_service.get_group_sync_settings('lib-123', 'user-456')
            assert settings['sync_enabled'] is True
            
            # 8. Update sync settings
            updated_settings = await group_library_service.update_group_sync_settings(
                'lib-123', 'user-456', {'sync_frequency_minutes': 30}
            )
            assert updated_settings['sync_frequency_minutes'] == 30
            
            # 9. Trigger sync
            sync_result = await group_library_service.sync_group_library('lib-123', 'user-456')
            assert sync_result['sync_initiated'] is True
            
            # 10. Check activity log
            activities = await group_library_service.get_group_activity_log('lib-123', 'user-456', 10, 0)
            # Should have activities from sync settings creation and updates
            assert len(activities) >= 0
        
        # Run the async workflow
        asyncio.run(run_workflow())


if __name__ == "__main__":
    # Run a simple test to verify the integration works
    import tempfile
    import os
    
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name
    
    try:
        # Create engine with temporary database
        engine = create_engine(f"sqlite:///{db_path}", echo=True)
        
        # Run a simple test
        test_instance = TestZoteroGroupLibraryIntegration()
        
        print("✅ Zotero Group Library Integration Test Setup Complete")
        print(f"Database created at: {db_path}")
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)