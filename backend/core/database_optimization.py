"""
Database optimization utilities for improved performance.
Includes indexing, query optimization, and connection pooling.
"""
import logging
from sqlalchemy import text, Index, create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Any
import time
import asyncio
from contextlib import asynccontextmanager

from core.config import settings
from core.database import Base, engine

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database optimization and performance monitoring utilities."""
    
    def __init__(self):
        self.engine = engine
        self.performance_metrics = {}
    
    async def create_performance_indexes(self):
        """Create indexes for improved query performance."""
        indexes_to_create = [
            # User-related indexes
            Index('idx_users_email', 'users.email'),
            Index('idx_users_created_at', 'users.created_at'),
            Index('idx_users_last_login', 'users.last_login'),
            Index('idx_users_active', 'users.is_active'),
            
            # Document-related indexes
            Index('idx_documents_user_id', 'documents.user_id'),
            Index('idx_documents_status', 'documents.status'),
            Index('idx_documents_created_at', 'documents.created_at'),
            Index('idx_documents_user_status', 'documents.user_id', 'documents.status'),
            
            # Conversation indexes
            Index('idx_conversations_user_id', 'conversations.user_id'),
            Index('idx_conversations_created_at', 'conversations.created_at'),
            Index('idx_conversations_updated_at', 'conversations.updated_at'),
            
            # Message indexes
            Index('idx_messages_conversation_id', 'messages.conversation_id'),
            Index('idx_messages_created_at', 'messages.created_at'),
            Index('idx_messages_role', 'messages.role'),
            Index('idx_messages_conv_created', 'messages.conversation_id', 'messages.created_at'),
            
            # Document chunk indexes
            Index('idx_chunks_document_id', 'document_chunks.document_id'),
            Index('idx_chunks_index', 'document_chunks.chunk_index'),
            Index('idx_chunks_doc_index', 'document_chunks.document_id', 'document_chunks.chunk_index'),
            
            # Enhanced chunk indexes
            Index('idx_chunks_enh_document_id', 'document_chunks_enhanced.document_id'),
            Index('idx_chunks_enh_parent_id', 'document_chunks_enhanced.parent_chunk_id'),
            Index('idx_chunks_enh_level', 'document_chunks_enhanced.chunk_level'),
            Index('idx_chunks_enh_doc_level', 'document_chunks_enhanced.document_id', 'document_chunks_enhanced.chunk_level'),
            
            # Knowledge graph indexes
            Index('idx_kg_entities_name', 'kg_entities.name'),
            Index('idx_kg_entities_type', 'kg_entities.type'),
            Index('idx_kg_entities_document_id', 'kg_entities.document_id'),
            Index('idx_kg_entities_importance', 'kg_entities.importance_score'),
            Index('idx_kg_relationships_source', 'kg_relationships.source_entity_id'),
            Index('idx_kg_relationships_target', 'kg_relationships.target_entity_id'),
            Index('idx_kg_relationships_type', 'kg_relationships.relationship_type'),
            Index('idx_kg_relationships_confidence', 'kg_relationships.confidence_score'),
            
            # Memory indexes
            Index('idx_memory_conversation_id', 'conversation_memory.conversation_id'),
            Index('idx_memory_type', 'conversation_memory.memory_type'),
            Index('idx_memory_timestamp', 'conversation_memory.timestamp'),
            Index('idx_memory_importance', 'conversation_memory.importance_score'),
            Index('idx_memory_expires', 'conversation_memory.expires_at'),
            
            # User profile indexes
            Index('idx_user_profiles_user_id', 'user_profiles.user_id'),
            Index('idx_user_profiles_updated', 'user_profiles.updated_at'),
            
            # Feedback indexes
            Index('idx_feedback_user_id', 'user_feedback.user_id'),
            Index('idx_feedback_message_id', 'user_feedback.message_id'),
            Index('idx_feedback_type', 'user_feedback.feedback_type'),
            Index('idx_feedback_processed', 'user_feedback.processed'),
            Index('idx_feedback_created', 'user_feedback.created_at'),
            
            # Analytics indexes
            Index('idx_analytics_user_id', 'analytics_events.user_id'),
            Index('idx_analytics_event_type', 'analytics_events.event_type'),
            Index('idx_analytics_timestamp', 'analytics_events.timestamp'),
            Index('idx_analytics_session', 'analytics_events.session_id'),
            Index('idx_analytics_user_timestamp', 'analytics_events.user_id', 'analytics_events.timestamp'),
            
            # Document tags indexes
            Index('idx_tags_document_id', 'document_tags.document_id'),
            Index('idx_tags_name', 'document_tags.tag_name'),
            Index('idx_tags_type', 'document_tags.tag_type'),
            Index('idx_tags_confidence', 'document_tags.confidence_score'),
            Index('idx_tags_generated_by', 'document_tags.generated_by'),
        ]
        
        try:
            with self.engine.connect() as conn:
                for index in indexes_to_create:
                    try:
                        index.create(conn, checkfirst=True)
                        logger.info(f"Created index: {index.name}")
                    except Exception as e:
                        logger.warning(f"Failed to create index {index.name}: {e}")
                
                conn.commit()
                logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
            raise
    
    async def analyze_query_performance(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze query performance and return metrics."""
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                # Execute EXPLAIN QUERY PLAN for SQLite
                explain_query = f"EXPLAIN QUERY PLAN {query}"
                explain_result = conn.execute(text(explain_query), params or {})
                query_plan = [dict(row._mapping) for row in explain_result]
                
                # Execute the actual query
                result = conn.execute(text(query), params or {})
                rows = result.fetchall()
                
                execution_time = time.time() - start_time
                
                return {
                    'execution_time': execution_time,
                    'row_count': len(rows),
                    'query_plan': query_plan,
                    'performance_score': self._calculate_performance_score(execution_time, len(rows))
                }
        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
            return {
                'execution_time': time.time() - start_time,
                'error': str(e),
                'performance_score': 0
            }
    
    def _calculate_performance_score(self, execution_time: float, row_count: int) -> float:
        """Calculate a performance score based on execution time and result size."""
        # Simple scoring: lower time and reasonable result size = higher score
        if execution_time == 0:
            return 100.0
        
        base_score = 100.0
        time_penalty = min(execution_time * 10, 50)  # Max 50 point penalty for time
        size_bonus = min(row_count / 1000, 10)  # Small bonus for returning data
        
        return max(base_score - time_penalty + size_bonus, 0)
    
    async def optimize_database_settings(self):
        """Apply database optimization settings."""
        optimization_queries = [
            # SQLite optimizations
            "PRAGMA journal_mode = WAL",  # Write-Ahead Logging for better concurrency
            "PRAGMA synchronous = NORMAL",  # Balance between safety and performance
            "PRAGMA cache_size = -128000",  # 128MB cache (increased from 64MB)
            "PRAGMA temp_store = MEMORY",  # Store temporary tables in memory
            "PRAGMA mmap_size = 536870912",  # 512MB memory-mapped I/O (increased from 256MB)
            "PRAGMA page_size = 4096",  # Optimal page size for most systems
            "PRAGMA auto_vacuum = INCREMENTAL",  # Incremental auto-vacuum
            "PRAGMA wal_autocheckpoint = 1000",  # Checkpoint every 1000 pages
            "PRAGMA optimize",  # Analyze and optimize database
        ]
        
        try:
            with self.engine.connect() as conn:
                for query in optimization_queries:
                    try:
                        conn.execute(text(query))
                        logger.info(f"Applied optimization: {query}")
                    except Exception as e:
                        logger.warning(f"Failed to apply optimization {query}: {e}")
                
                conn.commit()
                logger.info("Database optimization settings applied")
        except Exception as e:
            logger.error(f"Error applying database optimizations: {e}")
            raise
    
    async def vacuum_and_analyze(self):
        """Perform database maintenance operations."""
        maintenance_queries = [
            "VACUUM",  # Rebuild database file
            "ANALYZE",  # Update query planner statistics
        ]
        
        try:
            with self.engine.connect() as conn:
                for query in maintenance_queries:
                    try:
                        start_time = time.time()
                        conn.execute(text(query))
                        execution_time = time.time() - start_time
                        logger.info(f"Completed {query} in {execution_time:.2f}s")
                    except Exception as e:
                        logger.warning(f"Failed to execute {query}: {e}")
                
                conn.commit()
                logger.info("Database maintenance completed")
        except Exception as e:
            logger.error(f"Error during database maintenance: {e}")
            raise
    
    async def get_database_statistics(self) -> Dict[str, Any]:
        """Get database statistics for monitoring."""
        stats_queries = {
            'total_users': "SELECT COUNT(*) as count FROM users",
            'total_documents': "SELECT COUNT(*) as count FROM documents",
            'total_conversations': "SELECT COUNT(*) as count FROM conversations",
            'total_messages': "SELECT COUNT(*) as count FROM messages",
            'total_chunks': "SELECT COUNT(*) as count FROM document_chunks",
            'total_enhanced_chunks': "SELECT COUNT(*) as count FROM document_chunks_enhanced",
            'total_kg_entities': "SELECT COUNT(*) as count FROM kg_entities",
            'total_kg_relationships': "SELECT COUNT(*) as count FROM kg_relationships",
            'total_memory_items': "SELECT COUNT(*) as count FROM conversation_memory",
            'total_feedback': "SELECT COUNT(*) as count FROM user_feedback",
            'total_analytics_events': "SELECT COUNT(*) as count FROM analytics_events",
            'database_size': "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()",
        }
        
        statistics = {}
        
        try:
            with self.engine.connect() as conn:
                for stat_name, query in stats_queries.items():
                    try:
                        result = conn.execute(text(query))
                        row = result.fetchone()
                        if stat_name == 'database_size':
                            statistics[stat_name] = row[0] if row else 0
                        else:
                            statistics[stat_name] = row[0] if row else 0
                    except Exception as e:
                        logger.warning(f"Failed to get statistic {stat_name}: {e}")
                        statistics[stat_name] = 0
                
                # Add performance metrics
                statistics['performance_metrics'] = self.performance_metrics
                
        except Exception as e:
            logger.error(f"Error getting database statistics: {e}")
            statistics = {'error': str(e)}
        
        return statistics
    
    async def monitor_slow_queries(self, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        """Monitor and log slow queries."""
        # This would typically integrate with database logging
        # For now, return stored performance metrics that exceed threshold
        slow_queries = []
        
        for query_id, metrics in self.performance_metrics.items():
            if metrics.get('execution_time', 0) > threshold_seconds:
                slow_queries.append({
                    'query_id': query_id,
                    'execution_time': metrics['execution_time'],
                    'timestamp': metrics.get('timestamp', time.time()),
                    'query': metrics.get('query', 'Unknown')
                })
        
        return sorted(slow_queries, key=lambda x: x['execution_time'], reverse=True)
    
    def record_query_performance(self, query_id: str, execution_time: float, query: str = None):
        """Record query performance for monitoring."""
        self.performance_metrics[query_id] = {
            'execution_time': execution_time,
            'timestamp': time.time(),
            'query': query
        }
        
        # Keep only recent metrics (last 1000 queries)
        if len(self.performance_metrics) > 1000:
            oldest_key = min(self.performance_metrics.keys(), 
                           key=lambda k: self.performance_metrics[k]['timestamp'])
            del self.performance_metrics[oldest_key]

# Global database optimizer instance
db_optimizer = DatabaseOptimizer()

@asynccontextmanager
async def optimized_db_session():
    """Context manager for optimized database sessions."""
    from core.database import SessionLocal
    
    session = SessionLocal()
    start_time = time.time()
    
    try:
        yield session
    finally:
        execution_time = time.time() - start_time
        if execution_time > 0.5:  # Log slow sessions
            logger.warning(f"Slow database session: {execution_time:.2f}s")
        
        session.close()

async def initialize_database_optimizations():
    """Initialize all database optimizations."""
    try:
        await db_optimizer.optimize_database_settings()
        await db_optimizer.create_performance_indexes()
        logger.info("Database optimizations initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database optimizations: {e}")
        raise

async def perform_database_maintenance():
    """Perform regular database maintenance."""
    try:
        await db_optimizer.vacuum_and_analyze()
        logger.info("Database maintenance completed successfully")
    except Exception as e:
        logger.error(f"Database maintenance failed: {e}")
        raise