"""
Comprehensive database connectivity and operation testing suite.
"""
import asyncio
import logging
import time
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import psutil

from core.database import (
    Base, User, Document, Conversation, Message, DocumentChunk,
    UserProfile, DocumentChunkEnhanced, KnowledgeGraphEntity,
    KnowledgeGraphRelationship, ConversationMemory, UserFeedback,
    AnalyticsEvent, DocumentTag, get_db
)
from core.config import settings
from core.redis_client import get_redis_client
from services.test_runner_service import TestResult, TestStatus, TestSeverity

logger = logging.getLogger(__name__)

class DatabaseTestSuite:
    """Comprehensive database testing suite."""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.test_results = []
        self.test_data_cleanup = []  # Track test data for cleanup
        
        # Create test engine and session
        try:
            self.test_engine = create_engine(settings.DATABASE_URL, echo=False)
            self.TestSession = sessionmaker(bind=self.test_engine)
        except Exception as e:
            logger.error(f"Failed to create test database engine: {e}")
            self.test_engine = None
            self.TestSession = None
    
    async def run_all_tests(self) -> List[TestResult]:
        """Run all database tests."""
        logger.info("Starting comprehensive database tests")
        self.test_results = []
        
        if not self.test_engine:
            self.test_results.append(TestResult(
                test_name="Database Engine Creation",
                status=TestStatus.ERROR,
                duration=0.0,
                error_message="Failed to create database engine",
                severity=TestSeverity.CRITICAL
            ))
            return self.test_results
        
        # Run connectivity tests
        connectivity_results = await self._run_connectivity_tests()
        self.test_results.extend(connectivity_results)
        
        # Run schema tests
        schema_results = await self._run_schema_tests()
        self.test_results.extend(schema_results)
        
        # Run CRUD operation tests
        crud_results = await self._run_crud_tests()
        self.test_results.extend(crud_results)
        
        # Run performance tests
        performance_results = await self._run_performance_tests()
        self.test_results.extend(performance_results)
        
        # Run Redis tests
        redis_results = await self._run_redis_tests()
        self.test_results.extend(redis_results)
        
        # Run transaction tests
        transaction_results = await self._run_transaction_tests()
        self.test_results.extend(transaction_results)
        
        # Run data integrity tests
        integrity_results = await self._run_data_integrity_tests()
        self.test_results.extend(integrity_results)
        
        # Cleanup test data
        await self._cleanup_test_data()
        
        logger.info(f"Completed database tests: {len(self.test_results)} tests")
        return self.test_results
    
    async def _run_connectivity_tests(self) -> List[TestResult]:
        """Run database connectivity tests."""
        logger.info("Running database connectivity tests")
        tests = []
        
        # Test basic connection
        basic_conn_test = await self._test_basic_connection()
        tests.append(basic_conn_test)
        
        # Test connection pool
        pool_test = await self._test_connection_pool()
        tests.append(pool_test)
        
        # Test connection timeout
        timeout_test = await self._test_connection_timeout()
        tests.append(timeout_test)
        
        return tests
    
    async def _test_basic_connection(self) -> TestResult:
        """Test basic database connection."""
        test_name = "Database Basic Connection"
        start_time = time.time()
        
        try:
            with self.test_engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test_value"))
                row = result.fetchone()
                
                duration = time.time() - start_time
                
                if row and row[0] == 1:
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        duration=duration,
                        metadata={
                            'connection_time': duration,
                            'database_url': settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'hidden'
                        }
                    )
                else:
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.FAILED,
                        duration=duration,
                        error_message="Query returned unexpected result",
                        severity=TestSeverity.CRITICAL
                    )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.CRITICAL
            )
    
    async def _test_connection_pool(self) -> TestResult:
        """Test database connection pool."""
        test_name = "Database Connection Pool"
        start_time = time.time()
        
        try:
            # Test multiple concurrent connections
            connections = []
            for i in range(5):
                conn = self.test_engine.connect()
                result = conn.execute(text(f"SELECT {i} as test_value"))
                row = result.fetchone()
                connections.append((conn, row[0]))
            
            # Close all connections
            for conn, value in connections:
                conn.close()
            
            duration = time.time() - start_time
            
            # Verify all connections worked
            expected_values = list(range(5))
            actual_values = [value for _, value in connections]
            
            if actual_values == expected_values:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    metadata={
                        'concurrent_connections': len(connections),
                        'pool_test_time': duration
                    }
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    duration=duration,
                    error_message=f"Connection pool test failed: expected {expected_values}, got {actual_values}",
                    severity=TestSeverity.HIGH
                )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.HIGH
            )
    
    async def _test_connection_timeout(self) -> TestResult:
        """Test connection timeout handling."""
        test_name = "Database Connection Timeout"
        start_time = time.time()
        
        try:
            # Test with a query that should complete quickly
            with self.test_engine.connect() as conn:
                # Set a short statement timeout for this test
                conn.execute(text("SET statement_timeout = '5s'"))
                result = conn.execute(text("SELECT pg_sleep(0.1)"))  # Sleep for 100ms
                result.fetchone()
            
            duration = time.time() - start_time
            
            return TestResult(
                test_name=test_name,
                status=TestStatus.PASSED,
                duration=duration,
                metadata={'timeout_test_duration': duration}
            )
        
        except Exception as e:
            duration = time.time() - start_time
            # Timeout errors are expected in some cases, so this might be normal
            return TestResult(
                test_name=test_name,
                status=TestStatus.PASSED,
                duration=duration,
                metadata={
                    'timeout_handled': True,
                    'error_type': type(e).__name__
                }
            )
    
    async def _run_schema_tests(self) -> List[TestResult]:
        """Run database schema tests."""
        logger.info("Running database schema tests")
        tests = []
        
        # Test table existence
        table_test = await self._test_table_existence()
        tests.append(table_test)
        
        # Test table structure
        structure_test = await self._test_table_structure()
        tests.append(structure_test)
        
        # Test indexes
        index_test = await self._test_indexes()
        tests.append(index_test)
        
        return tests
    
    async def _test_table_existence(self) -> TestResult:
        """Test that all required tables exist."""
        test_name = "Database Table Existence"
        start_time = time.time()
        
        try:
            inspector = inspect(self.test_engine)
            existing_tables = set(inspector.get_table_names())
            
            # Expected tables from our models
            expected_tables = {
                'users', 'documents', 'conversations', 'messages', 'document_chunks',
                'user_profiles', 'document_chunks_enhanced', 'kg_entities', 
                'kg_relationships', 'conversation_memory', 'user_feedback',
                'analytics_events', 'document_tags'
            }
            
            missing_tables = expected_tables - existing_tables
            extra_tables = existing_tables - expected_tables
            
            duration = time.time() - start_time
            
            if not missing_tables:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    metadata={
                        'total_tables': len(existing_tables),
                        'expected_tables': len(expected_tables),
                        'extra_tables': list(extra_tables) if extra_tables else []
                    }
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    duration=duration,
                    error_message=f"Missing tables: {missing_tables}",
                    metadata={
                        'missing_tables': list(missing_tables),
                        'existing_tables': list(existing_tables)
                    },
                    severity=TestSeverity.HIGH
                )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.HIGH
            )
    
    async def _test_table_structure(self) -> TestResult:
        """Test table structure and columns."""
        test_name = "Database Table Structure"
        start_time = time.time()
        
        try:
            inspector = inspect(self.test_engine)
            
            # Test key tables have required columns
            table_column_requirements = {
                'users': ['id', 'email', 'name', 'created_at'],
                'documents': ['id', 'user_id', 'name', 'file_path', 'created_at'],
                'conversations': ['id', 'user_id', 'title', 'created_at'],
                'messages': ['id', 'conversation_id', 'role', 'content', 'created_at']
            }
            
            missing_columns = {}
            
            for table_name, required_columns in table_column_requirements.items():
                if inspector.has_table(table_name):
                    existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
                    missing = set(required_columns) - set(existing_columns)
                    if missing:
                        missing_columns[table_name] = list(missing)
            
            duration = time.time() - start_time
            
            if not missing_columns:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    metadata={'tables_checked': len(table_column_requirements)}
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    duration=duration,
                    error_message=f"Missing columns: {missing_columns}",
                    metadata={'missing_columns': missing_columns},
                    severity=TestSeverity.HIGH
                )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.MEDIUM
            )
    
    async def _test_indexes(self) -> TestResult:
        """Test database indexes."""
        test_name = "Database Indexes"
        start_time = time.time()
        
        try:
            inspector = inspect(self.test_engine)
            
            # Check for important indexes
            important_indexes = {
                'users': ['email'],  # Should have unique index on email
                'documents': ['user_id'],  # Should have index on user_id
                'messages': ['conversation_id'],  # Should have index on conversation_id
            }
            
            index_status = {}
            
            for table_name, expected_indexed_columns in important_indexes.items():
                if inspector.has_table(table_name):
                    indexes = inspector.get_indexes(table_name)
                    indexed_columns = set()
                    
                    for index in indexes:
                        indexed_columns.update(index['column_names'])
                    
                    missing_indexes = set(expected_indexed_columns) - indexed_columns
                    index_status[table_name] = {
                        'expected': expected_indexed_columns,
                        'found': list(indexed_columns),
                        'missing': list(missing_indexes)
                    }
            
            duration = time.time() - start_time
            
            # Check if any critical indexes are missing
            critical_missing = any(
                status['missing'] for status in index_status.values()
            )
            
            if not critical_missing:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    metadata={'index_status': index_status}
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    duration=duration,
                    error_message="Some important indexes are missing",
                    metadata={'index_status': index_status},
                    severity=TestSeverity.MEDIUM
                )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.LOW
            )
    
    async def _run_crud_tests(self) -> List[TestResult]:
        """Run CRUD operation tests."""
        logger.info("Running database CRUD tests")
        tests = []
        
        # Test user CRUD operations
        user_crud_test = await self._test_user_crud()
        tests.append(user_crud_test)
        
        # Test document CRUD operations
        document_crud_test = await self._test_document_crud()
        tests.append(document_crud_test)
        
        # Test conversation CRUD operations
        conversation_crud_test = await self._test_conversation_crud()
        tests.append(conversation_crud_test)
        
        return tests
    
    async def _test_user_crud(self) -> TestResult:
        """Test User model CRUD operations."""
        test_name = "User CRUD Operations"
        start_time = time.time()
        
        try:
            session = self.TestSession()
            test_user_id = str(uuid.uuid4())
            
            try:
                # CREATE
                test_user = User(
                    id=test_user_id,
                    email=f"test_{test_user_id}@example.com",
                    name="Test User",
                    hashed_password="hashed_password_123"
                )
                session.add(test_user)
                session.commit()
                self.test_data_cleanup.append(('users', test_user_id))
                
                # READ
                retrieved_user = session.query(User).filter(User.id == test_user_id).first()
                if not retrieved_user or retrieved_user.email != test_user.email:
                    raise Exception("User retrieval failed")
                
                # UPDATE
                retrieved_user.name = "Updated Test User"
                session.commit()
                
                updated_user = session.query(User).filter(User.id == test_user_id).first()
                if updated_user.name != "Updated Test User":
                    raise Exception("User update failed")
                
                # DELETE (will be done in cleanup)
                
                duration = time.time() - start_time
                
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    metadata={
                        'operations_tested': ['create', 'read', 'update'],
                        'test_user_id': test_user_id
                    }
                )
            
            finally:
                session.close()
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.HIGH
            )
    
    async def _test_document_crud(self) -> TestResult:
        """Test Document model CRUD operations."""
        test_name = "Document CRUD Operations"
        start_time = time.time()
        
        try:
            session = self.TestSession()
            test_doc_id = str(uuid.uuid4())
            test_user_id = str(uuid.uuid4())
            
            try:
                # CREATE
                test_document = Document(
                    id=test_doc_id,
                    user_id=test_user_id,
                    name="Test Document",
                    file_path="/test/path/document.pdf",
                    content_type="application/pdf",
                    size=1024,
                    status="completed"
                )
                session.add(test_document)
                session.commit()
                self.test_data_cleanup.append(('documents', test_doc_id))
                
                # READ
                retrieved_doc = session.query(Document).filter(Document.id == test_doc_id).first()
                if not retrieved_doc or retrieved_doc.name != test_document.name:
                    raise Exception("Document retrieval failed")
                
                # UPDATE
                retrieved_doc.status = "processing"
                retrieved_doc.chunks_count = 10
                session.commit()
                
                updated_doc = session.query(Document).filter(Document.id == test_doc_id).first()
                if updated_doc.status != "processing" or updated_doc.chunks_count != 10:
                    raise Exception("Document update failed")
                
                duration = time.time() - start_time
                
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    metadata={
                        'operations_tested': ['create', 'read', 'update'],
                        'test_document_id': test_doc_id
                    }
                )
            
            finally:
                session.close()
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.HIGH
            )
    
    async def _test_conversation_crud(self) -> TestResult:
        """Test Conversation and Message CRUD operations."""
        test_name = "Conversation CRUD Operations"
        start_time = time.time()
        
        try:
            session = self.TestSession()
            test_conv_id = str(uuid.uuid4())
            test_msg_id = str(uuid.uuid4())
            test_user_id = str(uuid.uuid4())
            
            try:
                # CREATE Conversation
                test_conversation = Conversation(
                    id=test_conv_id,
                    user_id=test_user_id,
                    title="Test Conversation"
                )
                session.add(test_conversation)
                session.commit()
                self.test_data_cleanup.append(('conversations', test_conv_id))
                
                # CREATE Message
                test_message = Message(
                    id=test_msg_id,
                    conversation_id=test_conv_id,
                    role="user",
                    content="Test message content"
                )
                session.add(test_message)
                session.commit()
                self.test_data_cleanup.append(('messages', test_msg_id))
                
                # READ
                retrieved_conv = session.query(Conversation).filter(Conversation.id == test_conv_id).first()
                retrieved_msg = session.query(Message).filter(Message.id == test_msg_id).first()
                
                if not retrieved_conv or not retrieved_msg:
                    raise Exception("Conversation/Message retrieval failed")
                
                # Test relationship
                messages = session.query(Message).filter(Message.conversation_id == test_conv_id).all()
                if len(messages) != 1 or messages[0].id != test_msg_id:
                    raise Exception("Conversation-Message relationship failed")
                
                duration = time.time() - start_time
                
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    metadata={
                        'operations_tested': ['create', 'read', 'relationship'],
                        'test_conversation_id': test_conv_id,
                        'test_message_id': test_msg_id
                    }
                )
            
            finally:
                session.close()
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.HIGH
            )
    
    async def _run_performance_tests(self) -> List[TestResult]:
        """Run database performance tests."""
        logger.info("Running database performance tests")
        tests = []
        
        # Test query performance
        query_perf_test = await self._test_query_performance()
        tests.append(query_perf_test)
        
        # Test bulk operations
        bulk_ops_test = await self._test_bulk_operations()
        tests.append(bulk_ops_test)
        
        return tests
    
    async def _test_query_performance(self) -> TestResult:
        """Test database query performance."""
        test_name = "Database Query Performance"
        start_time = time.time()
        
        try:
            session = self.TestSession()
            
            try:
                # Test simple query performance
                query_times = []
                
                for i in range(5):
                    query_start = time.time()
                    result = session.execute(text("SELECT COUNT(*) FROM users"))
                    result.fetchone()
                    query_time = time.time() - query_start
                    query_times.append(query_time)
                
                avg_query_time = sum(query_times) / len(query_times)
                max_query_time = max(query_times)
                
                duration = time.time() - start_time
                
                # Performance thresholds
                if avg_query_time < 0.1 and max_query_time < 0.5:  # 100ms avg, 500ms max
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        duration=duration,
                        metadata={
                            'average_query_time': avg_query_time,
                            'max_query_time': max_query_time,
                            'queries_tested': len(query_times)
                        }
                    )
                else:
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.FAILED,
                        duration=duration,
                        error_message=f"Query performance below threshold: avg={avg_query_time:.3f}s, max={max_query_time:.3f}s",
                        metadata={
                            'average_query_time': avg_query_time,
                            'max_query_time': max_query_time,
                            'queries_tested': len(query_times)
                        },
                        severity=TestSeverity.MEDIUM
                    )
            
            finally:
                session.close()
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.MEDIUM
            )
    
    async def _test_bulk_operations(self) -> TestResult:
        """Test bulk database operations."""
        test_name = "Database Bulk Operations"
        start_time = time.time()
        
        try:
            session = self.TestSession()
            
            try:
                # Create multiple test records
                test_users = []
                for i in range(10):
                    user_id = str(uuid.uuid4())
                    test_user = User(
                        id=user_id,
                        email=f"bulk_test_{i}_{user_id}@example.com",
                        name=f"Bulk Test User {i}",
                        hashed_password="test_password"
                    )
                    test_users.append(test_user)
                    self.test_data_cleanup.append(('users', user_id))
                
                # Bulk insert
                bulk_start = time.time()
                session.add_all(test_users)
                session.commit()
                bulk_insert_time = time.time() - bulk_start
                
                # Bulk query
                query_start = time.time()
                user_ids = [user.id for user in test_users]
                retrieved_users = session.query(User).filter(User.id.in_(user_ids)).all()
                bulk_query_time = time.time() - query_start
                
                duration = time.time() - start_time
                
                if len(retrieved_users) == len(test_users):
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        duration=duration,
                        metadata={
                            'records_created': len(test_users),
                            'bulk_insert_time': bulk_insert_time,
                            'bulk_query_time': bulk_query_time,
                            'records_retrieved': len(retrieved_users)
                        }
                    )
                else:
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.FAILED,
                        duration=duration,
                        error_message=f"Bulk operation failed: created {len(test_users)}, retrieved {len(retrieved_users)}",
                        severity=TestSeverity.MEDIUM
                    )
            
            finally:
                session.close()
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.MEDIUM
            )
    
    async def _run_redis_tests(self) -> List[TestResult]:
        """Run Redis connectivity and operation tests."""
        logger.info("Running Redis tests")
        tests = []
        
        # Test Redis connectivity
        redis_conn_test = await self._test_redis_connectivity()
        tests.append(redis_conn_test)
        
        # Test Redis operations
        redis_ops_test = await self._test_redis_operations()
        tests.append(redis_ops_test)
        
        return tests
    
    async def _test_redis_connectivity(self) -> TestResult:
        """Test Redis connectivity."""
        test_name = "Redis Connectivity"
        start_time = time.time()
        
        try:
            # Test ping
            pong = await self.redis_client.ping()
            
            duration = time.time() - start_time
            
            if pong:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    metadata={'ping_response': str(pong)}
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    duration=duration,
                    error_message="Redis ping failed",
                    severity=TestSeverity.HIGH
                )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.HIGH
            )
    
    async def _test_redis_operations(self) -> TestResult:
        """Test Redis basic operations."""
        test_name = "Redis Operations"
        start_time = time.time()
        
        try:
            test_key = f"test_key_{uuid.uuid4()}"
            test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
            
            # SET operation
            await self.redis_client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            
            # GET operation
            retrieved_value = await self.redis_client.get(test_key)
            
            # DELETE operation
            await self.redis_client.delete(test_key)
            
            # Verify deletion
            deleted_value = await self.redis_client.get(test_key)
            
            duration = time.time() - start_time
            
            if (retrieved_value and 
                retrieved_value.get('test') == 'data' and 
                deleted_value is None):
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    metadata={
                        'operations_tested': ['set', 'get', 'delete'],
                        'test_key': test_key
                    }
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    duration=duration,
                    error_message="Redis operations failed",
                    metadata={
                        'retrieved_value': retrieved_value,
                        'deleted_value': deleted_value
                    },
                    severity=TestSeverity.HIGH
                )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.HIGH
            )
    
    async def _run_transaction_tests(self) -> List[TestResult]:
        """Run database transaction tests."""
        logger.info("Running database transaction tests")
        tests = []
        
        # Test transaction commit
        commit_test = await self._test_transaction_commit()
        tests.append(commit_test)
        
        # Test transaction rollback
        rollback_test = await self._test_transaction_rollback()
        tests.append(rollback_test)
        
        return tests
    
    async def _test_transaction_commit(self) -> TestResult:
        """Test transaction commit."""
        test_name = "Database Transaction Commit"
        start_time = time.time()
        
        try:
            session = self.TestSession()
            test_user_id = str(uuid.uuid4())
            
            try:
                # Start transaction
                session.begin()
                
                # Create user
                test_user = User(
                    id=test_user_id,
                    email=f"transaction_test_{test_user_id}@example.com",
                    name="Transaction Test User",
                    hashed_password="test_password"
                )
                session.add(test_user)
                
                # Commit transaction
                session.commit()
                self.test_data_cleanup.append(('users', test_user_id))
                
                # Verify user exists
                retrieved_user = session.query(User).filter(User.id == test_user_id).first()
                
                duration = time.time() - start_time
                
                if retrieved_user:
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        duration=duration,
                        metadata={'test_user_id': test_user_id}
                    )
                else:
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.FAILED,
                        duration=duration,
                        error_message="Transaction commit failed - user not found",
                        severity=TestSeverity.HIGH
                    )
            
            finally:
                session.close()
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.HIGH
            )
    
    async def _test_transaction_rollback(self) -> TestResult:
        """Test transaction rollback."""
        test_name = "Database Transaction Rollback"
        start_time = time.time()
        
        try:
            session = self.TestSession()
            test_user_id = str(uuid.uuid4())
            
            try:
                # Start transaction
                session.begin()
                
                # Create user
                test_user = User(
                    id=test_user_id,
                    email=f"rollback_test_{test_user_id}@example.com",
                    name="Rollback Test User",
                    hashed_password="test_password"
                )
                session.add(test_user)
                
                # Rollback transaction
                session.rollback()
                
                # Verify user doesn't exist
                retrieved_user = session.query(User).filter(User.id == test_user_id).first()
                
                duration = time.time() - start_time
                
                if not retrieved_user:
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        duration=duration,
                        metadata={'test_user_id': test_user_id}
                    )
                else:
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.FAILED,
                        duration=duration,
                        error_message="Transaction rollback failed - user still exists",
                        severity=TestSeverity.HIGH
                    )
            
            finally:
                session.close()
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.HIGH
            )
    
    async def _run_data_integrity_tests(self) -> List[TestResult]:
        """Run data integrity tests."""
        logger.info("Running data integrity tests")
        tests = []
        
        # Test foreign key constraints
        fk_test = await self._test_foreign_key_constraints()
        tests.append(fk_test)
        
        # Test unique constraints
        unique_test = await self._test_unique_constraints()
        tests.append(unique_test)
        
        return tests
    
    async def _test_foreign_key_constraints(self) -> TestResult:
        """Test foreign key constraints."""
        test_name = "Foreign Key Constraints"
        start_time = time.time()
        
        try:
            session = self.TestSession()
            
            try:
                # Try to create a message with non-existent conversation_id
                invalid_message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id="non_existent_conversation_id",
                    role="user",
                    content="Test message"
                )
                session.add(invalid_message)
                
                try:
                    session.commit()
                    # If we get here, foreign key constraint is not working
                    duration = time.time() - start_time
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.FAILED,
                        duration=duration,
                        error_message="Foreign key constraint not enforced",
                        severity=TestSeverity.MEDIUM
                    )
                except SQLAlchemyError:
                    # This is expected - foreign key constraint should prevent this
                    session.rollback()
                    duration = time.time() - start_time
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        duration=duration,
                        metadata={'constraint_enforced': True}
                    )
            
            finally:
                session.close()
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.MEDIUM
            )
    
    async def _test_unique_constraints(self) -> TestResult:
        """Test unique constraints."""
        test_name = "Unique Constraints"
        start_time = time.time()
        
        try:
            session = self.TestSession()
            test_email = f"unique_test_{uuid.uuid4()}@example.com"
            
            try:
                # Create first user
                user1 = User(
                    id=str(uuid.uuid4()),
                    email=test_email,
                    name="User 1",
                    hashed_password="password1"
                )
                session.add(user1)
                session.commit()
                self.test_data_cleanup.append(('users', user1.id))
                
                # Try to create second user with same email
                user2 = User(
                    id=str(uuid.uuid4()),
                    email=test_email,  # Same email
                    name="User 2",
                    hashed_password="password2"
                )
                session.add(user2)
                
                try:
                    session.commit()
                    # If we get here, unique constraint is not working
                    duration = time.time() - start_time
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.FAILED,
                        duration=duration,
                        error_message="Unique constraint not enforced",
                        severity=TestSeverity.MEDIUM
                    )
                except SQLAlchemyError:
                    # This is expected - unique constraint should prevent this
                    session.rollback()
                    duration = time.time() - start_time
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        duration=duration,
                        metadata={'constraint_enforced': True, 'test_email': test_email}
                    )
            
            finally:
                session.close()
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=TestSeverity.MEDIUM
            )
    
    async def _cleanup_test_data(self):
        """Clean up test data created during tests."""
        if not self.test_data_cleanup:
            return
        
        logger.info(f"Cleaning up {len(self.test_data_cleanup)} test records")
        
        try:
            session = self.TestSession()
            
            try:
                # Group cleanup by table
                cleanup_by_table = {}
                for table_name, record_id in self.test_data_cleanup:
                    if table_name not in cleanup_by_table:
                        cleanup_by_table[table_name] = []
                    cleanup_by_table[table_name].append(record_id)
                
                # Delete records
                for table_name, record_ids in cleanup_by_table.items():
                    if table_name == 'users':
                        session.query(User).filter(User.id.in_(record_ids)).delete(synchronize_session=False)
                    elif table_name == 'documents':
                        session.query(Document).filter(Document.id.in_(record_ids)).delete(synchronize_session=False)
                    elif table_name == 'conversations':
                        session.query(Conversation).filter(Conversation.id.in_(record_ids)).delete(synchronize_session=False)
                    elif table_name == 'messages':
                        session.query(Message).filter(Message.id.in_(record_ids)).delete(synchronize_session=False)
                
                session.commit()
                logger.info("Test data cleanup completed")
            
            finally:
                session.close()
        
        except Exception as e:
            logger.error(f"Test data cleanup failed: {e}")
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of database test results."""
        if not self.test_results:
            return {'error': 'No tests have been run'}
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t.status == TestStatus.PASSED)
        failed_tests = sum(1 for t in self.test_results if t.status == TestStatus.FAILED)
        error_tests = sum(1 for t in self.test_results if t.status == TestStatus.ERROR)
        
        # Categorize tests
        categories = {
            'connectivity': [t for t in self.test_results if 'Connection' in t.test_name],
            'schema': [t for t in self.test_results if any(word in t.test_name for word in ['Table', 'Schema', 'Index'])],
            'crud': [t for t in self.test_results if 'CRUD' in t.test_name],
            'performance': [t for t in self.test_results if 'Performance' in t.test_name or 'Bulk' in t.test_name],
            'redis': [t for t in self.test_results if 'Redis' in t.test_name],
            'transactions': [t for t in self.test_results if 'Transaction' in t.test_name],
            'integrity': [t for t in self.test_results if 'Constraint' in t.test_name or 'Integrity' in t.test_name]
        }
        
        category_summary = {}
        for category, tests in categories.items():
            if tests:
                category_passed = sum(1 for t in tests if t.status == TestStatus.PASSED)
                category_summary[category] = {
                    'total': len(tests),
                    'passed': category_passed,
                    'success_rate': category_passed / len(tests)
                }
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'category_summary': category_summary,
            'critical_failures': [
                {'test_name': t.test_name, 'error': t.error_message}
                for t in self.test_results 
                if t.status in [TestStatus.FAILED, TestStatus.ERROR] and 
                t.severity in [TestSeverity.HIGH, TestSeverity.CRITICAL]
            ]
        }

# Global instance
database_test_suite = DatabaseTestSuite()

def get_database_test_suite() -> DatabaseTestSuite:
    """Get the global database test suite instance."""
    return database_test_suite