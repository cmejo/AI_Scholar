"""
Feature Flag Service for AI Scholar Advanced RAG
Manages feature flags for gradual rollout and A/B testing
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.core.database import get_db_session
from backend.core.redis_client import redis_client

logger = logging.getLogger(__name__)

Base = declarative_base()

class FeatureFlagStatus(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    SCHEDULED = "scheduled"
    CANARY = "canary"

class FeatureFlagTarget(Enum):
    ALL_USERS = "all_users"
    BETA_USERS = "beta_users"
    PREMIUM_USERS = "premium_users"
    INSTITUTION_USERS = "institution_users"
    MOBILE_USERS = "mobile_users"
    VOICE_USERS = "voice_users"
    SPECIFIC_USERS = "specific_users"

class FeatureFlagEnvironment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class FeatureFlagRule:
    """Feature flag rule configuration"""
    target: FeatureFlagTarget
    percentage: Optional[float] = None
    user_ids: Optional[List[str]] = None
    institution_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    conditions: Optional[Dict[str, Any]] = None
    environment: Optional[FeatureFlagEnvironment] = None

@dataclass
class FeatureFlagConfig:
    """Complete feature flag configuration"""
    name: str
    description: str
    status: FeatureFlagStatus
    rules: List[FeatureFlagRule]
    created_by: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class FeatureFlags(Base):
    """Feature flags database model"""
    __tablename__ = "feature_flags"
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False)
    rules = Column(JSON, default=[])
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})
    is_active = Column(Boolean, default=True)

class FeatureFlagUsage(Base):
    """Feature flag usage tracking"""
    __tablename__ = "feature_flag_usage"
    
    id = Column(String, primary_key=True)
    flag_name = Column(String, nullable=False)
    user_id = Column(String)
    session_id = Column(String)
    enabled = Column(Boolean, nullable=False)
    rule_matched = Column(String)
    environment = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default={})

class FeatureFlagService:
    """Feature flag management service"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes
        
        # Initialize default feature flags for advanced features
        self._initialize_default_flags()
    
    def _initialize_default_flags(self):
        """Initialize default feature flags for advanced features"""
        default_flags = [
            {
                "name": "mobile_accessibility",
                "description": "Mobile accessibility features including PWA and responsive design",
                "status": FeatureFlagStatus.PERCENTAGE,
                "rules": [
                    FeatureFlagRule(
                        target=FeatureFlagTarget.MOBILE_USERS,
                        percentage=100.0,
                        environment=FeatureFlagEnvironment.PRODUCTION
                    )
                ]
            },
            {
                "name": "voice_interface",
                "description": "Voice interface capabilities for speech-to-text and voice commands",
                "status": FeatureFlagStatus.PERCENTAGE,
                "rules": [
                    FeatureFlagRule(
                        target=FeatureFlagTarget.BETA_USERS,
                        percentage=50.0,
                        environment=FeatureFlagEnvironment.PRODUCTION
                    )
                ]
            },
            {
                "name": "external_integrations",
                "description": "External integrations with reference managers and academic databases",
                "status": FeatureFlagStatus.PERCENTAGE,
                "rules": [
                    FeatureFlagRule(
                        target=FeatureFlagTarget.PREMIUM_USERS,
                        percentage=100.0,
                        environment=FeatureFlagEnvironment.PRODUCTION
                    )
                ]
            },
            {
                "name": "educational_features",
                "description": "Educational enhancements including quizzes and spaced repetition",
                "status": FeatureFlagStatus.ENABLED,
                "rules": [
                    FeatureFlagRule(
                        target=FeatureFlagTarget.ALL_USERS,
                        environment=FeatureFlagEnvironment.PRODUCTION
                    )
                ]
            },
            {
                "name": "enterprise_compliance",
                "description": "Enterprise compliance and institutional features",
                "status": FeatureFlagStatus.PERCENTAGE,
                "rules": [
                    FeatureFlagRule(
                        target=FeatureFlagTarget.INSTITUTION_USERS,
                        percentage=100.0,
                        environment=FeatureFlagEnvironment.PRODUCTION
                    )
                ]
            },
            {
                "name": "interactive_content",
                "description": "Interactive content support including Jupyter notebooks",
                "status": FeatureFlagStatus.CANARY,
                "rules": [
                    FeatureFlagRule(
                        target=FeatureFlagTarget.BETA_USERS,
                        percentage=25.0,
                        environment=FeatureFlagEnvironment.PRODUCTION
                    )
                ]
            },
            {
                "name": "opportunity_matching",
                "description": "Funding and publication opportunity matching",
                "status": FeatureFlagStatus.PERCENTAGE,
                "rules": [
                    FeatureFlagRule(
                        target=FeatureFlagTarget.PREMIUM_USERS,
                        percentage=75.0,
                        environment=FeatureFlagEnvironment.PRODUCTION
                    )
                ]
            }
        ]
        
        # Create default flags if they don't exist
        with get_db_session() as db:
            for flag_config in default_flags:
                existing_flag = db.query(FeatureFlags).filter(
                    FeatureFlags.name == flag_config["name"]
                ).first()
                
                if not existing_flag:
                    new_flag = FeatureFlags(
                        id=self._generate_flag_id(flag_config["name"]),
                        name=flag_config["name"],
                        description=flag_config["description"],
                        status=flag_config["status"].value,
                        rules=[asdict(rule) for rule in flag_config["rules"]],
                        created_by="system",
                        metadata={"auto_created": True}
                    )
                    db.add(new_flag)
            
            db.commit()
    
    def _generate_flag_id(self, name: str) -> str:
        """Generate unique flag ID"""
        return hashlib.md5(f"flag_{name}_{datetime.utcnow().isoformat()}".encode()).hexdigest()
    
    def _get_cache_key(self, flag_name: str, user_context: Dict[str, Any] = None) -> str:
        """Generate cache key for flag evaluation"""
        context_hash = ""
        if user_context:
            context_str = json.dumps(user_context, sort_keys=True)
            context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
        
        return f"feature_flag:{flag_name}:{context_hash}"
    
    def is_enabled(self, flag_name: str, user_context: Dict[str, Any] = None) -> bool:
        """Check if feature flag is enabled for given context"""
        try:
            # Check cache first
            cache_key = self._get_cache_key(flag_name, user_context)
            cached_result = self.redis_client.get(cache_key)
            
            if cached_result is not None:
                result = json.loads(cached_result)
                self._track_usage(flag_name, user_context, result["enabled"], result.get("rule_matched"))
                return result["enabled"]
            
            # Evaluate flag
            result = self._evaluate_flag(flag_name, user_context)
            
            # Cache result
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(result)
            )
            
            # Track usage
            self._track_usage(flag_name, user_context, result["enabled"], result.get("rule_matched"))
            
            return result["enabled"]
            
        except Exception as e:
            logger.error(f"Error evaluating feature flag {flag_name}: {str(e)}")
            return False
    
    def _evaluate_flag(self, flag_name: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate feature flag based on rules"""
        with get_db_session() as db:
            flag = db.query(FeatureFlags).filter(
                FeatureFlags.name == flag_name,
                FeatureFlags.is_active == True
            ).first()
            
            if not flag:
                return {"enabled": False, "reason": "flag_not_found"}
            
            status = FeatureFlagStatus(flag.status)
            
            # Handle simple cases
            if status == FeatureFlagStatus.DISABLED:
                return {"enabled": False, "reason": "disabled"}
            
            if status == FeatureFlagStatus.ENABLED:
                return {"enabled": True, "reason": "enabled"}
            
            # Evaluate rules
            for rule_data in flag.rules:
                rule = FeatureFlagRule(**rule_data)
                
                if self._evaluate_rule(rule, user_context):
                    return {
                        "enabled": True,
                        "reason": "rule_matched",
                        "rule_matched": rule.target.value
                    }
            
            return {"enabled": False, "reason": "no_rules_matched"}
    
    def _evaluate_rule(self, rule: FeatureFlagRule, user_context: Dict[str, Any] = None) -> bool:
        """Evaluate individual rule"""
        if not user_context:
            user_context = {}
        
        # Check environment
        if rule.environment:
            current_env = user_context.get("environment", "production")
            if current_env != rule.environment.value:
                return False
        
        # Check time-based rules
        now = datetime.utcnow()
        if rule.start_date and now < rule.start_date:
            return False
        if rule.end_date and now > rule.end_date:
            return False
        
        # Check target-based rules
        if rule.target == FeatureFlagTarget.ALL_USERS:
            return self._check_percentage(rule.percentage, user_context)
        
        elif rule.target == FeatureFlagTarget.SPECIFIC_USERS:
            user_id = user_context.get("user_id")
            if user_id and rule.user_ids and user_id in rule.user_ids:
                return self._check_percentage(rule.percentage, user_context)
        
        elif rule.target == FeatureFlagTarget.BETA_USERS:
            is_beta = user_context.get("is_beta_user", False)
            if is_beta:
                return self._check_percentage(rule.percentage, user_context)
        
        elif rule.target == FeatureFlagTarget.PREMIUM_USERS:
            is_premium = user_context.get("is_premium_user", False)
            if is_premium:
                return self._check_percentage(rule.percentage, user_context)
        
        elif rule.target == FeatureFlagTarget.INSTITUTION_USERS:
            institution_id = user_context.get("institution_id")
            if institution_id:
                if not rule.institution_ids or institution_id in rule.institution_ids:
                    return self._check_percentage(rule.percentage, user_context)
        
        elif rule.target == FeatureFlagTarget.MOBILE_USERS:
            is_mobile = user_context.get("is_mobile", False)
            if is_mobile:
                return self._check_percentage(rule.percentage, user_context)
        
        elif rule.target == FeatureFlagTarget.VOICE_USERS:
            has_voice_enabled = user_context.get("voice_enabled", False)
            if has_voice_enabled:
                return self._check_percentage(rule.percentage, user_context)
        
        # Check custom conditions
        if rule.conditions:
            if self._evaluate_conditions(rule.conditions, user_context):
                return self._check_percentage(rule.percentage, user_context)
        
        return False
    
    def _check_percentage(self, percentage: Optional[float], user_context: Dict[str, Any]) -> bool:
        """Check if user falls within percentage rollout"""
        if percentage is None or percentage >= 100.0:
            return True
        
        if percentage <= 0.0:
            return False
        
        # Use consistent hash for user to ensure stable rollout
        user_id = user_context.get("user_id", "anonymous")
        session_id = user_context.get("session_id", "")
        hash_input = f"{user_id}:{session_id}"
        
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        user_percentage = (hash_value % 10000) / 100.0
        
        return user_percentage < percentage
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], user_context: Dict[str, Any]) -> bool:
        """Evaluate custom conditions"""
        for key, expected_value in conditions.items():
            actual_value = user_context.get(key)
            
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            elif actual_value != expected_value:
                return False
        
        return True
    
    def _track_usage(self, flag_name: str, user_context: Dict[str, Any], enabled: bool, rule_matched: str = None):
        """Track feature flag usage"""
        try:
            usage_record = FeatureFlagUsage(
                id=self._generate_flag_id(f"usage_{flag_name}"),
                flag_name=flag_name,
                user_id=user_context.get("user_id") if user_context else None,
                session_id=user_context.get("session_id") if user_context else None,
                enabled=enabled,
                rule_matched=rule_matched,
                environment=user_context.get("environment", "production") if user_context else "production",
                metadata=user_context or {}
            )
            
            with get_db_session() as db:
                db.add(usage_record)
                db.commit()
                
        except Exception as e:
            logger.error(f"Error tracking feature flag usage: {str(e)}")
    
    def create_flag(self, config: FeatureFlagConfig) -> str:
        """Create new feature flag"""
        with get_db_session() as db:
            flag_id = self._generate_flag_id(config.name)
            
            new_flag = FeatureFlags(
                id=flag_id,
                name=config.name,
                description=config.description,
                status=config.status.value,
                rules=[asdict(rule) for rule in config.rules],
                created_by=config.created_by,
                metadata=config.metadata or {}
            )
            
            db.add(new_flag)
            db.commit()
            
            # Clear cache
            self._clear_flag_cache(config.name)
            
            return flag_id
    
    def update_flag(self, flag_name: str, updates: Dict[str, Any]) -> bool:
        """Update existing feature flag"""
        with get_db_session() as db:
            flag = db.query(FeatureFlags).filter(
                FeatureFlags.name == flag_name
            ).first()
            
            if not flag:
                return False
            
            # Update fields
            for key, value in updates.items():
                if hasattr(flag, key):
                    setattr(flag, key, value)
            
            flag.updated_at = datetime.utcnow()
            db.commit()
            
            # Clear cache
            self._clear_flag_cache(flag_name)
            
            return True
    
    def delete_flag(self, flag_name: str) -> bool:
        """Delete feature flag"""
        with get_db_session() as db:
            flag = db.query(FeatureFlags).filter(
                FeatureFlags.name == flag_name
            ).first()
            
            if not flag:
                return False
            
            flag.is_active = False
            flag.updated_at = datetime.utcnow()
            db.commit()
            
            # Clear cache
            self._clear_flag_cache(flag_name)
            
            return True
    
    def get_flag(self, flag_name: str) -> Optional[Dict[str, Any]]:
        """Get feature flag configuration"""
        with get_db_session() as db:
            flag = db.query(FeatureFlags).filter(
                FeatureFlags.name == flag_name,
                FeatureFlags.is_active == True
            ).first()
            
            if not flag:
                return None
            
            return {
                "id": flag.id,
                "name": flag.name,
                "description": flag.description,
                "status": flag.status,
                "rules": flag.rules,
                "created_by": flag.created_by,
                "created_at": flag.created_at.isoformat(),
                "updated_at": flag.updated_at.isoformat(),
                "metadata": flag.metadata
            }
    
    def get_all_flags(self) -> List[Dict[str, Any]]:
        """Get all active feature flags"""
        with get_db_session() as db:
            flags = db.query(FeatureFlags).filter(
                FeatureFlags.is_active == True
            ).all()
            
            return [
                {
                    "id": flag.id,
                    "name": flag.name,
                    "description": flag.description,
                    "status": flag.status,
                    "rules": flag.rules,
                    "created_by": flag.created_by,
                    "created_at": flag.created_at.isoformat(),
                    "updated_at": flag.updated_at.isoformat(),
                    "metadata": flag.metadata
                }
                for flag in flags
            ]
    
    def get_usage_stats(self, flag_name: str, days: int = 7) -> Dict[str, Any]:
        """Get usage statistics for feature flag"""
        with get_db_session() as db:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            usage_records = db.query(FeatureFlagUsage).filter(
                FeatureFlagUsage.flag_name == flag_name,
                FeatureFlagUsage.timestamp >= start_date
            ).all()
            
            total_requests = len(usage_records)
            enabled_requests = sum(1 for record in usage_records if record.enabled)
            
            return {
                "flag_name": flag_name,
                "period_days": days,
                "total_requests": total_requests,
                "enabled_requests": enabled_requests,
                "enabled_percentage": (enabled_requests / total_requests * 100) if total_requests > 0 else 0,
                "unique_users": len(set(record.user_id for record in usage_records if record.user_id)),
                "environments": list(set(record.environment for record in usage_records if record.environment))
            }
    
    def _clear_flag_cache(self, flag_name: str):
        """Clear cache for specific flag"""
        try:
            # Clear all cached evaluations for this flag
            pattern = f"feature_flag:{flag_name}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Error clearing flag cache: {str(e)}")
    
    def bulk_evaluate(self, flag_names: List[str], user_context: Dict[str, Any] = None) -> Dict[str, bool]:
        """Evaluate multiple feature flags at once"""
        results = {}
        
        for flag_name in flag_names:
            results[flag_name] = self.is_enabled(flag_name, user_context)
        
        return results

# Global service instance
feature_flag_service = FeatureFlagService()
    """Feature flag configuration"""
    name: str
    description: str
    status: FeatureFlagStatus
    rules: List[FeatureFlagRule]
    default_value: bool = False
    created_by: str = "system"
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class FeatureFlag(Base):
    """Feature flag database model"""
    __tablename__ = "feature_flags"
    
    name = Column(String(100), primary_key=True)
    description = Column(Text)
    status = Column(String(20), default="disabled")
    rules = Column(JSON, default=list)
    default_value = Column(Boolean, default=False)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    usage_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)

class FeatureFlagUsage(Base):
    """Feature flag usage tracking"""
    __tablename__ = "feature_flag_usage"
    
    id = Column(String(36), primary_key=True)
    flag_name = Column(String(100), index=True)
    user_id = Column(String(36), index=True)
    enabled = Column(Boolean)
    rule_matched = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    metadata = Column(JSON, default=dict)

class FeatureFlagService:
    """Service for managing feature flags"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes
        self.cache_prefix = "feature_flag:"
        
    def create_feature_flag(self, config: FeatureFlagConfig) -> bool:
        """Create a new feature flag"""
        try:
            with get_db_session() as session:
                # Check if flag already exists
                existing_flag = session.query(FeatureFlag).filter_by(name=config.name).first()
                if existing_flag:
                    logger.warning(f"Feature flag {config.name} already exists")
                    return False
                
                # Create new flag
                flag = FeatureFlag(
                    name=config.name,
                    description=config.description,
                    status=config.status.value,
                    rules=[asdict(rule) for rule in config.rules],
                    default_value=config.default_value,
                    created_by=config.created_by,
                    tags=config.tags or [],
                    metadata=config.metadata or {}
                )
                
                session.add(flag)
                session.commit()
                
                # Clear cache
                self._clear_flag_cache(config.name)
                
                logger.info(f"Created feature flag: {config.name}")
                return True
                
        except Exception as e:
            logger.error(f"Error creating feature flag {config.name}: {str(e)}")
            return False
    
    def update_feature_flag(self, name: str, config: FeatureFlagConfig) -> bool:
        """Update an existing feature flag"""
        try:
            with get_db_session() as session:
                flag = session.query(FeatureFlag).filter_by(name=name).first()
                if not flag:
                    logger.warning(f"Feature flag {name} not found")
                    return False
                
                # Update flag
                flag.description = config.description
                flag.status = config.status.value
                flag.rules = [asdict(rule) for rule in config.rules]
                flag.default_value = config.default_value
                flag.tags = config.tags or []
                flag.metadata = config.metadata or {}
                flag.updated_at = datetime.utcnow()
                
                session.commit()
                
                # Clear cache
                self._clear_flag_cache(name)
                
                logger.info(f"Updated feature flag: {name}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating feature flag {name}: {str(e)}")
            return False
    
    def delete_feature_flag(self, name: str) -> bool:
        """Delete a feature flag"""
        try:
            with get_db_session() as session:
                flag = session.query(FeatureFlag).filter_by(name=name).first()
                if not flag:
                    logger.warning(f"Feature flag {name} not found")
                    return False
                
                session.delete(flag)
                session.commit()
                
                # Clear cache
                self._clear_flag_cache(name)
                
                logger.info(f"Deleted feature flag: {name}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting feature flag {name}: {str(e)}")
            return False
    
    def is_enabled(self, flag_name: str, user_id: str = None, context: Dict[str, Any] = None) -> bool:
        """Check if a feature flag is enabled for a user"""
        try:
            # Get flag configuration
            flag_config = self._get_flag_config(flag_name)
            if not flag_config:
                logger.warning(f"Feature flag {flag_name} not found")
                return False
            
            # Check cache first
            cache_key = f"{self.cache_prefix}result:{flag_name}:{user_id or 'anonymous'}"
            cached_result = self.redis_client.get(cache_key)
            if cached_result is not None:
                result = json.loads(cached_result)
                self._track_usage(flag_name, user_id, result['enabled'], result['rule'], context)
                return result['enabled']
            
            # Evaluate flag
            result = self._evaluate_flag(flag_config, user_id, context or {})
            
            # Cache result
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(result)
            )
            
            # Track usage
            self._track_usage(flag_name, user_id, result['enabled'], result['rule'], context)
            
            return result['enabled']
            
        except Exception as e:
            logger.error(f"Error checking feature flag {flag_name}: {str(e)}")
            return False
    
    def get_all_flags(self, user_id: str = None, context: Dict[str, Any] = None) -> Dict[str, bool]:
        """Get all feature flags for a user"""
        try:
            with get_db_session() as session:
                flags = session.query(FeatureFlag).all()
                
                result = {}
                for flag in flags:
                    result[flag.name] = self.is_enabled(flag.name, user_id, context)
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting all feature flags: {str(e)}")
            return {}
    
    def get_flag_info(self, flag_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a feature flag"""
        try:
            with get_db_session() as session:
                flag = session.query(FeatureFlag).filter_by(name=flag_name).first()
                if not flag:
                    return None
                
                return {
                    'name': flag.name,
                    'description': flag.description,
                    'status': flag.status,
                    'rules': flag.rules,
                    'default_value': flag.default_value,
                    'created_by': flag.created_by,
                    'created_at': flag.created_at.isoformat(),
                    'updated_at': flag.updated_at.isoformat(),
                    'tags': flag.tags,
                    'metadata': flag.metadata,
                    'usage_count': flag.usage_count,
                    'last_accessed': flag.last_accessed.isoformat() if flag.last_accessed else None
                }
                
        except Exception as e:
            logger.error(f"Error getting flag info {flag_name}: {str(e)}")
            return None
    
    def get_usage_stats(self, flag_name: str, days: int = 7) -> Dict[str, Any]:
        """Get usage statistics for a feature flag"""
        try:
            with get_db_session() as session:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                usage_records = session.query(FeatureFlagUsage).filter(
                    FeatureFlagUsage.flag_name == flag_name,
                    FeatureFlagUsage.timestamp >= start_date
                ).all()
                
                total_requests = len(usage_records)
                enabled_requests = sum(1 for record in usage_records if record.enabled)
                unique_users = len(set(record.user_id for record in usage_records if record.user_id))
                
                return {
                    'flag_name': flag_name,
                    'period_days': days,
                    'total_requests': total_requests,
                    'enabled_requests': enabled_requests,
                    'disabled_requests': total_requests - enabled_requests,
                    'enable_rate': enabled_requests / total_requests if total_requests > 0 else 0,
                    'unique_users': unique_users,
                    'daily_breakdown': self._get_daily_breakdown(usage_records, days)
                }
                
        except Exception as e:
            logger.error(f"Error getting usage stats for {flag_name}: {str(e)}")
            return {}
    
    def _get_flag_config(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get flag configuration from cache or database"""
        try:
            # Check cache first
            cache_key = f"{self.cache_prefix}config:{flag_name}"
            cached_config = self.redis_client.get(cache_key)
            if cached_config:
                return json.loads(cached_config)
            
            # Get from database
            with get_db_session() as session:
                flag = session.query(FeatureFlag).filter_by(name=flag_name).first()
                if not flag:
                    return None
                
                config = {
                    'name': flag.name,
                    'status': flag.status,
                    'rules': flag.rules,
                    'default_value': flag.default_value
                }
                
                # Cache configuration
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(config)
                )
                
                # Update access tracking
                flag.usage_count += 1
                flag.last_accessed = datetime.utcnow()
                session.commit()
                
                return config
                
        except Exception as e:
            logger.error(f"Error getting flag config {flag_name}: {str(e)}")
            return None
    
    def _evaluate_flag(self, flag_config: Dict[str, Any], user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate feature flag rules"""
        try:
            status = flag_config['status']
            rules = flag_config['rules']
            default_value = flag_config['default_value']
            
            # If disabled, return default value
            if status == FeatureFlagStatus.DISABLED.value:
                return {'enabled': default_value, 'rule': 'disabled'}
            
            # If enabled for all, return True
            if status == FeatureFlagStatus.ENABLED.value:
                return {'enabled': True, 'rule': 'enabled_all'}
            
            # Evaluate rules
            for rule in rules:
                if self._evaluate_rule(rule, user_id, context):
                    return {'enabled': True, 'rule': rule.get('target', 'unknown')}
            
            # No rules matched, return default
            return {'enabled': default_value, 'rule': 'default'}
            
        except Exception as e:
            logger.error(f"Error evaluating flag rules: {str(e)}")
            return {'enabled': False, 'rule': 'error'}
    
    def _evaluate_rule(self, rule: Dict[str, Any], user_id: str, context: Dict[str, Any]) -> bool:
        """Evaluate a single feature flag rule"""
        try:
            target = rule.get('target')
            
            # Check time-based conditions
            if rule.get('start_date'):
                start_date = datetime.fromisoformat(rule['start_date'])
                if datetime.utcnow() < start_date:
                    return False
            
            if rule.get('end_date'):
                end_date = datetime.fromisoformat(rule['end_date'])
                if datetime.utcnow() > end_date:
                    return False
            
            # Check user-specific conditions
            if target == FeatureFlagTarget.SPECIFIC_USERS.value:
                user_ids = rule.get('user_ids', [])
                return user_id in user_ids
            
            # Check percentage rollout
            if target == FeatureFlagTarget.ALL_USERS.value and rule.get('percentage'):
                percentage = rule['percentage']
                if user_id:
                    # Use consistent hash for user
                    user_hash = hash(user_id) % 100
                    return user_hash < percentage
                else:
                    # Random for anonymous users
                    import random
                    return random.random() * 100 < percentage
            
            # Check user type conditions
            if target == FeatureFlagTarget.BETA_USERS.value:
                return context.get('is_beta_user', False)
            
            if target == FeatureFlagTarget.PREMIUM_USERS.value:
                return context.get('is_premium_user', False)
            
            if target == FeatureFlagTarget.INSTITUTION_USERS.value:
                institution_ids = rule.get('institution_ids', [])
                user_institution = context.get('institution_id')
                return user_institution in institution_ids
            
            if target == FeatureFlagTarget.MOBILE_USERS.value:
                return context.get('is_mobile', False)
            
            # Check custom conditions
            conditions = rule.get('conditions', {})
            for key, expected_value in conditions.items():
                if context.get(key) != expected_value:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating rule: {str(e)}")
            return False
    
    def _track_usage(self, flag_name: str, user_id: str, enabled: bool, rule: str, context: Dict[str, Any]):
        """Track feature flag usage"""
        try:
            # Only track a sample of usage to avoid overwhelming the database
            import random
            if random.random() > 0.1:  # Track 10% of requests
                return
            
            with get_db_session() as session:
                usage = FeatureFlagUsage(
                    id=f"{flag_name}_{user_id or 'anon'}_{datetime.utcnow().timestamp()}",
                    flag_name=flag_name,
                    user_id=user_id,
                    enabled=enabled,
                    rule_matched=rule,
                    user_agent=context.get('user_agent'),
                    ip_address=context.get('ip_address'),
                    metadata=context
                )
                
                session.add(usage)
                session.commit()
                
        except Exception as e:
            logger.error(f"Error tracking usage for {flag_name}: {str(e)}")
    
    def _get_daily_breakdown(self, usage_records: List[FeatureFlagUsage], days: int) -> List[Dict[str, Any]]:
        """Get daily breakdown of usage statistics"""
        try:
            from collections import defaultdict
            
            daily_stats = defaultdict(lambda: {'total': 0, 'enabled': 0})
            
            for record in usage_records:
                date_key = record.timestamp.date().isoformat()
                daily_stats[date_key]['total'] += 1
                if record.enabled:
                    daily_stats[date_key]['enabled'] += 1
            
            # Fill in missing days
            result = []
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).date()
                date_key = date.isoformat()
                stats = daily_stats[date_key]
                
                result.append({
                    'date': date_key,
                    'total_requests': stats['total'],
                    'enabled_requests': stats['enabled'],
                    'enable_rate': stats['enabled'] / stats['total'] if stats['total'] > 0 else 0
                })
            
            return sorted(result, key=lambda x: x['date'])
            
        except Exception as e:
            logger.error(f"Error getting daily breakdown: {str(e)}")
            return []
    
    def _clear_flag_cache(self, flag_name: str):
        """Clear cache for a specific flag"""
        try:
            # Clear configuration cache
            config_key = f"{self.cache_prefix}config:{flag_name}"
            self.redis_client.delete(config_key)
            
            # Clear result cache (pattern matching)
            result_pattern = f"{self.cache_prefix}result:{flag_name}:*"
            keys = self.redis_client.keys(result_pattern)
            if keys:
                self.redis_client.delete(*keys)
                
        except Exception as e:
            logger.error(f"Error clearing cache for {flag_name}: {str(e)}")

# Predefined feature flags for advanced features
ADVANCED_FEATURE_FLAGS = [
    FeatureFlagConfig(
        name="mobile_accessibility",
        description="Enable mobile accessibility features and PWA support",
        status=FeatureFlagStatus.PERCENTAGE,
        rules=[
            FeatureFlagRule(
                target=FeatureFlagTarget.ALL_USERS,
                percentage=25.0  # Start with 25% rollout
            )
        ],
        tags=["mobile", "accessibility", "pwa"]
    ),
    FeatureFlagConfig(
        name="voice_interface",
        description="Enable voice interface and speech processing features",
        status=FeatureFlagStatus.PERCENTAGE,
        rules=[
            FeatureFlagRule(
                target=FeatureFlagTarget.BETA_USERS,
                percentage=100.0
            ),
            FeatureFlagRule(
                target=FeatureFlagTarget.ALL_USERS,
                percentage=10.0  # Limited rollout
            )
        ],
        tags=["voice", "speech", "accessibility"]
    ),
    FeatureFlagConfig(
        name="external_integrations",
        description="Enable external tool integrations (Zotero, Mendeley, etc.)",
        status=FeatureFlagStatus.PERCENTAGE,
        rules=[
            FeatureFlagRule(
                target=FeatureFlagTarget.PREMIUM_USERS,
                percentage=100.0
            ),
            FeatureFlagRule(
                target=FeatureFlagTarget.ALL_USERS,
                percentage=50.0
            )
        ],
        tags=["integrations", "external", "premium"]
    ),
    FeatureFlagConfig(
        name="educational_features",
        description="Enable quiz generation and spaced repetition features",
        status=FeatureFlagStatus.ENABLED,
        rules=[
            FeatureFlagRule(target=FeatureFlagTarget.ALL_USERS)
        ],
        tags=["education", "quiz", "learning"]
    ),
    FeatureFlagConfig(
        name="enterprise_compliance",
        description="Enable enterprise compliance and institutional features",
        status=FeatureFlagStatus.USER_LIST,
        rules=[
            FeatureFlagRule(
                target=FeatureFlagTarget.INSTITUTION_USERS,
                percentage=100.0
            )
        ],
        tags=["enterprise", "compliance", "institutional"]
    ),
    FeatureFlagConfig(
        name="interactive_content",
        description="Enable Jupyter notebook and interactive visualization support",
        status=FeatureFlagStatus.PERCENTAGE,
        rules=[
            FeatureFlagRule(
                target=FeatureFlagTarget.ALL_USERS,
                percentage=75.0
            )
        ],
        tags=["jupyter", "visualization", "interactive"]
    ),
    FeatureFlagConfig(
        name="opportunity_matching",
        description="Enable funding and publication opportunity matching",
        status=FeatureFlagStatus.PERCENTAGE,
        rules=[
            FeatureFlagRule(
                target=FeatureFlagTarget.ALL_USERS,
                percentage=30.0
            )
        ],
        tags=["funding", "publications", "opportunities"]
    )
]

# Global service instance
feature_flag_service = FeatureFlagService()

def initialize_feature_flags():
    """Initialize predefined feature flags"""
    try:
        for flag_config in ADVANCED_FEATURE_FLAGS:
            feature_flag_service.create_feature_flag(flag_config)
        
        logger.info("Feature flags initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing feature flags: {str(e)}")

# Decorator for feature flag checking
def feature_flag_required(flag_name: str, default: bool = False):
    """Decorator to check feature flags before executing functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get user context from kwargs or request
            user_id = kwargs.get('user_id')
            context = kwargs.get('context', {})
            
            if feature_flag_service.is_enabled(flag_name, user_id, context):
                return func(*args, **kwargs)
            else:
                if default:
                    return func(*args, **kwargs)
                else:
                    raise Exception(f"Feature {flag_name} is not enabled")
        
        return wrapper
    return decorator