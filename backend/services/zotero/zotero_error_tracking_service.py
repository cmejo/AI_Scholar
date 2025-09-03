"""
Zotero Error Tracking Service

Provides comprehensive error tracking, reporting, and analysis for Zotero integration.
Captures, categorizes, and analyzes errors to improve system reliability and user experience.
"""

import asyncio
import json
import logging
import traceback
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ErrorCategory(Enum):
    """Error categories for classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    API_COMMUNICATION = "api_communication"
    DATA_VALIDATION = "data_validation"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    SYNC_OPERATION = "sync_operation"
    CITATION_GENERATION = "citation_generation"
    SEARCH_OPERATION = "search_operation"
    SYSTEM_RESOURCE = "system_resource"
    EXTERNAL_SERVICE = "external_service"
    USER_INPUT = "user_input"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for an error"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    library_id: Optional[str] = None
    operation: Optional[str] = None
    request_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    api_endpoint: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None


@dataclass
class ErrorReport:
    """Comprehensive error report"""
    id: str
    error_hash: str
    category: ErrorCategory
    severity: ErrorSeverity
    title: str
    message: str
    stack_trace: Optional[str]
    timestamp: datetime
    context: ErrorContext
    metadata: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


@dataclass
class ErrorSummary:
    """Error summary statistics"""
    total_errors: int
    unique_errors: int
    critical_errors: int
    high_priority_errors: int
    most_common_errors: List[Tuple[str, int]]
    error_rate_trend: List[Tuple[datetime, int]]
    affected_users: int
    resolution_rate: float


class ZoteroErrorTrackingService:
    """Service for tracking and analyzing Zotero integration errors"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def track_error(
        self,
        exception: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track an error occurrence"""
        try:
            # Generate error hash for deduplication
            error_hash = self._generate_error_hash(exception)
            
            # Create error report
            error_report = ErrorReport(
                id=f"err_{int(datetime.utcnow().timestamp())}_{error_hash[:8]}",
                error_hash=error_hash,
                category=category,
                severity=severity,
                title=self._generate_error_title(exception),
                message=str(exception),
                stack_trace=traceback.format_exc(),
                timestamp=datetime.utcnow(),
                context=context or ErrorContext(),
                metadata=metadata
            )
            
            # Store error report
            await self._store_error_report(error_report)
            
            # Log error based on severity
            if severity == ErrorSeverity.CRITICAL:
                self.logger.critical(f"Critical error tracked: {error_report.title}")
            elif severity == ErrorSeverity.HIGH:
                self.logger.error(f"High severity error tracked: {error_report.title}")
            else:
                self.logger.warning(f"Error tracked: {error_report.title}")
            
            return error_report.id
            
        except Exception as e:
            self.logger.error(f"Failed to track error: {e}")
            return ""
    
    def _generate_error_hash(self, exception: Exception) -> str:
        """Generate a hash for error deduplication"""
        # Create hash based on exception type and message
        error_signature = f"{type(exception).__name__}:{str(exception)}"
        return hashlib.md5(error_signature.encode()).hexdigest()
    
    def _generate_error_title(self, exception: Exception) -> str:
        """Generate a human-readable error title"""
        exception_name = type(exception).__name__
        
        # Map common exceptions to user-friendly titles
        title_mapping = {
            "ConnectionError": "Connection Failed",
            "TimeoutError": "Operation Timed Out",
            "ValidationError": "Data Validation Failed",
            "AuthenticationError": "Authentication Failed",
            "PermissionError": "Permission Denied",
            "FileNotFoundError": "File Not Found",
            "DatabaseError": "Database Operation Failed",
            "ValueError": "Invalid Value",
            "KeyError": "Missing Required Data",
            "AttributeError": "Attribute Access Error"
        }
        
        return title_mapping.get(exception_name, exception_name)
    
    async def _store_error_report(self, error_report: ErrorReport):
        """Store error report in database"""
        try:
            async with get_db_session() as session:
                # Check if this error hash already exists recently
                existing_query = text("""
                    SELECT id, COUNT(*) as occurrence_count
                    FROM zotero.error_reports 
                    WHERE error_hash = :error_hash 
                    AND timestamp >= :recent_threshold
                    GROUP BY id
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                recent_threshold = datetime.utcnow() - timedelta(hours=1)
                result = await session.execute(existing_query, {
                    "error_hash": error_report.error_hash,
                    "recent_threshold": recent_threshold
                })
                existing = result.fetchone()
                
                if existing:
                    # Update occurrence count for existing error
                    update_query = text("""
                        UPDATE zotero.error_reports 
                        SET occurrence_count = occurrence_count + 1,
                            last_occurrence = :timestamp
                        WHERE id = :id
                    """)
                    await session.execute(update_query, {
                        "id": existing[0],
                        "timestamp": error_report.timestamp
                    })
                else:
                    # Insert new error report
                    insert_query = text("""
                        INSERT INTO zotero.error_reports (
                            id, error_hash, category, severity, title, message,
                            stack_trace, timestamp, user_id, session_id, library_id,
                            operation, request_id, user_agent, ip_address, api_endpoint,
                            request_data, metadata, resolved, resolved_at, resolution_notes,
                            occurrence_count, last_occurrence
                        ) VALUES (
                            :id, :error_hash, :category, :severity, :title, :message,
                            :stack_trace, :timestamp, :user_id, :session_id, :library_id,
                            :operation, :request_id, :user_agent, :ip_address, :api_endpoint,
                            :request_data, :metadata, :resolved, :resolved_at, :resolution_notes,
                            1, :timestamp
                        )
                    """)
                    
                    await session.execute(insert_query, {
                        "id": error_report.id,
                        "error_hash": error_report.error_hash,
                        "category": error_report.category.value,
                        "severity": error_report.severity.value,
                        "title": error_report.title,
                        "message": error_report.message,
                        "stack_trace": error_report.stack_trace,
                        "timestamp": error_report.timestamp,
                        "user_id": error_report.context.user_id,
                        "session_id": error_report.context.session_id,
                        "library_id": error_report.context.library_id,
                        "operation": error_report.context.operation,
                        "request_id": error_report.context.request_id,
                        "user_agent": error_report.context.user_agent,
                        "ip_address": error_report.context.ip_address,
                        "api_endpoint": error_report.context.api_endpoint,
                        "request_data": json.dumps(error_report.context.request_data) if error_report.context.request_data else None,
                        "metadata": json.dumps(error_report.metadata) if error_report.metadata else None,
                        "resolved": error_report.resolved,
                        "resolved_at": error_report.resolved_at,
                        "resolution_notes": error_report.resolution_notes
                    })
                
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to store error report: {e}")
    
    async def get_error_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ErrorSummary:
        """Get comprehensive error summary"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            async with get_db_session() as session:
                # Total and unique errors
                total_query = text("""
                    SELECT 
                        SUM(occurrence_count) as total_errors,
                        COUNT(DISTINCT error_hash) as unique_errors,
                        SUM(CASE WHEN severity = 'critical' THEN occurrence_count ELSE 0 END) as critical_errors,
                        SUM(CASE WHEN severity = 'high' THEN occurrence_count ELSE 0 END) as high_errors
                    FROM zotero.error_reports 
                    WHERE timestamp >= :start_date AND timestamp <= :end_date
                """)
                result = await session.execute(total_query, {
                    "start_date": start_date,
                    "end_date": end_date
                })
                totals = result.fetchone()
                
                # Most common errors
                common_errors_query = text("""
                    SELECT title, SUM(occurrence_count) as total_occurrences
                    FROM zotero.error_reports 
                    WHERE timestamp >= :start_date AND timestamp <= :end_date
                    GROUP BY title
                    ORDER BY total_occurrences DESC
                    LIMIT 10
                """)
                result = await session.execute(common_errors_query, {
                    "start_date": start_date,
                    "end_date": end_date
                })
                most_common_errors = [(row[0], row[1]) for row in result.fetchall()]
                
                # Error rate trend (daily)
                trend_query = text("""
                    SELECT 
                        DATE_TRUNC('day', timestamp) as day,
                        SUM(occurrence_count) as daily_errors
                    FROM zotero.error_reports 
                    WHERE timestamp >= :start_date AND timestamp <= :end_date
                    GROUP BY DATE_TRUNC('day', timestamp)
                    ORDER BY day
                """)
                result = await session.execute(trend_query, {
                    "start_date": start_date,
                    "end_date": end_date
                })
                error_rate_trend = [(row[0], row[1]) for row in result.fetchall()]
                
                # Affected users
                users_query = text("""
                    SELECT COUNT(DISTINCT user_id) 
                    FROM zotero.error_reports 
                    WHERE timestamp >= :start_date AND timestamp <= :end_date
                    AND user_id IS NOT NULL
                """)
                result = await session.execute(users_query, {
                    "start_date": start_date,
                    "end_date": end_date
                })
                affected_users = result.scalar() or 0
                
                # Resolution rate
                resolution_query = text("""
                    SELECT 
                        COUNT(CASE WHEN resolved = true THEN 1 END) * 100.0 / COUNT(*) as resolution_rate
                    FROM zotero.error_reports 
                    WHERE timestamp >= :start_date AND timestamp <= :end_date
                """)
                result = await session.execute(resolution_query, {
                    "start_date": start_date,
                    "end_date": end_date
                })
                resolution_rate = float(result.scalar() or 0)
                
                return ErrorSummary(
                    total_errors=totals[0] or 0,
                    unique_errors=totals[1] or 0,
                    critical_errors=totals[2] or 0,
                    high_priority_errors=totals[3] or 0,
                    most_common_errors=most_common_errors,
                    error_rate_trend=error_rate_trend,
                    affected_users=affected_users,
                    resolution_rate=resolution_rate
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get error summary: {e}")
            raise
    
    async def get_error_details(self, error_id: str) -> Optional[ErrorReport]:
        """Get detailed information about a specific error"""
        try:
            async with get_db_session() as session:
                query = text("""
                    SELECT 
                        id, error_hash, category, severity, title, message, stack_trace,
                        timestamp, user_id, session_id, library_id, operation, request_id,
                        user_agent, ip_address, api_endpoint, request_data, metadata,
                        resolved, resolved_at, resolution_notes, occurrence_count, last_occurrence
                    FROM zotero.error_reports 
                    WHERE id = :error_id
                """)
                result = await session.execute(query, {"error_id": error_id})
                row = result.fetchone()
                
                if not row:
                    return None
                
                context = ErrorContext(
                    user_id=row[8],
                    session_id=row[9],
                    library_id=row[10],
                    operation=row[11],
                    request_id=row[12],
                    user_agent=row[13],
                    ip_address=row[14],
                    api_endpoint=row[15],
                    request_data=json.loads(row[16]) if row[16] else None
                )
                
                return ErrorReport(
                    id=row[0],
                    error_hash=row[1],
                    category=ErrorCategory(row[2]),
                    severity=ErrorSeverity(row[3]),
                    title=row[4],
                    message=row[5],
                    stack_trace=row[6],
                    timestamp=row[7],
                    context=context,
                    metadata=json.loads(row[17]) if row[17] else None,
                    resolved=row[18],
                    resolved_at=row[19],
                    resolution_notes=row[20]
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get error details: {e}")
            return None
    
    async def get_errors_by_category(
        self,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[ErrorReport]:
        """Get errors filtered by category and severity"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            async with get_db_session() as session:
                conditions = ["timestamp >= :start_date", "timestamp <= :end_date"]
                params = {"start_date": start_date, "end_date": end_date, "limit": limit}
                
                if category:
                    conditions.append("category = :category")
                    params["category"] = category.value
                
                if severity:
                    conditions.append("severity = :severity")
                    params["severity"] = severity.value
                
                query = text(f"""
                    SELECT 
                        id, error_hash, category, severity, title, message, stack_trace,
                        timestamp, user_id, session_id, library_id, operation, request_id,
                        user_agent, ip_address, api_endpoint, request_data, metadata,
                        resolved, resolved_at, resolution_notes, occurrence_count, last_occurrence
                    FROM zotero.error_reports 
                    WHERE {' AND '.join(conditions)}
                    ORDER BY timestamp DESC, occurrence_count DESC
                    LIMIT :limit
                """)
                
                result = await session.execute(query, params)
                
                errors = []
                for row in result.fetchall():
                    context = ErrorContext(
                        user_id=row[8],
                        session_id=row[9],
                        library_id=row[10],
                        operation=row[11],
                        request_id=row[12],
                        user_agent=row[13],
                        ip_address=row[14],
                        api_endpoint=row[15],
                        request_data=json.loads(row[16]) if row[16] else None
                    )
                    
                    errors.append(ErrorReport(
                        id=row[0],
                        error_hash=row[1],
                        category=ErrorCategory(row[2]),
                        severity=ErrorSeverity(row[3]),
                        title=row[4],
                        message=row[5],
                        stack_trace=row[6],
                        timestamp=row[7],
                        context=context,
                        metadata=json.loads(row[17]) if row[17] else None,
                        resolved=row[18],
                        resolved_at=row[19],
                        resolution_notes=row[20]
                    ))
                
                return errors
                
        except Exception as e:
            self.logger.error(f"Failed to get errors by category: {e}")
            return []
    
    async def resolve_error(
        self,
        error_id: str,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """Mark an error as resolved"""
        try:
            async with get_db_session() as session:
                query = text("""
                    UPDATE zotero.error_reports 
                    SET resolved = true, resolved_at = :resolved_at, resolution_notes = :resolution_notes
                    WHERE id = :error_id
                """)
                await session.execute(query, {
                    "error_id": error_id,
                    "resolved_at": datetime.utcnow(),
                    "resolution_notes": resolution_notes
                })
                await session.commit()
                
                self.logger.info(f"Error resolved: {error_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to resolve error: {e}")
            return False
    
    async def get_user_errors(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20
    ) -> List[ErrorReport]:
        """Get errors for a specific user"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            async with get_db_session() as session:
                query = text("""
                    SELECT 
                        id, error_hash, category, severity, title, message, stack_trace,
                        timestamp, user_id, session_id, library_id, operation, request_id,
                        user_agent, ip_address, api_endpoint, request_data, metadata,
                        resolved, resolved_at, resolution_notes, occurrence_count, last_occurrence
                    FROM zotero.error_reports 
                    WHERE user_id = :user_id
                    AND timestamp >= :start_date AND timestamp <= :end_date
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """)
                
                result = await session.execute(query, {
                    "user_id": user_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit
                })
                
                errors = []
                for row in result.fetchall():
                    context = ErrorContext(
                        user_id=row[8],
                        session_id=row[9],
                        library_id=row[10],
                        operation=row[11],
                        request_id=row[12],
                        user_agent=row[13],
                        ip_address=row[14],
                        api_endpoint=row[15],
                        request_data=json.loads(row[16]) if row[16] else None
                    )
                    
                    errors.append(ErrorReport(
                        id=row[0],
                        error_hash=row[1],
                        category=ErrorCategory(row[2]),
                        severity=ErrorSeverity(row[3]),
                        title=row[4],
                        message=row[5],
                        stack_trace=row[6],
                        timestamp=row[7],
                        context=context,
                        metadata=json.loads(row[17]) if row[17] else None,
                        resolved=row[18],
                        resolved_at=row[19],
                        resolution_notes=row[20]
                    ))
                
                return errors
                
        except Exception as e:
            self.logger.error(f"Failed to get user errors: {e}")
            return []


# Global error tracking service instance
error_tracking_service = ZoteroErrorTrackingService()