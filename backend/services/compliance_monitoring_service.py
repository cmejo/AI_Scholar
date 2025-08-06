"""
Enhanced Compliance Monitoring Service for Enterprise Features
Implements automated policy checking, ethical compliance monitoring,
violation detection with severity classification, and real-time dashboard
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import json
import re
import logging
from enum import Enum

from core.database import (
    get_db, Institution, InstitutionalPolicy, ComplianceViolation, 
    UserRole, AuditLog, User, Document, Message
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ViolationSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PolicyType(Enum):
    RESEARCH_ETHICS = "research_ethics"
    DATA_USAGE = "data_usage"
    COLLABORATION = "collaboration"
    CONTENT_FILTERING = "content_filtering"
    ACCESS_CONTROL = "access_control"
    PUBLICATION_ETHICS = "publication_ethics"
    DATA_PRIVACY = "data_privacy"

class ComplianceMonitoringService:
    """Enhanced service for monitoring institutional compliance and policy enforcement"""
    
    def __init__(self):
        self.policy_checkers = {
            PolicyType.RESEARCH_ETHICS.value: self._check_research_ethics,
            PolicyType.DATA_USAGE.value: self._check_data_usage,
            PolicyType.COLLABORATION.value: self._check_collaboration_policy,
            PolicyType.CONTENT_FILTERING.value: self._check_content_filtering,
            PolicyType.ACCESS_CONTROL.value: self._check_access_control,
            PolicyType.PUBLICATION_ETHICS.value: self._check_publication_ethics,
            PolicyType.DATA_PRIVACY.value: self._check_data_privacy
        }
        
        # Enhanced ethical compliance patterns
        self.ethical_patterns = {
            'human_subjects': {
                'keywords': ['human subjects', 'participants', 'volunteers', 'clinical trial', 
                           'survey participants', 'interview subjects', 'study participants'],
                'required_approvals': ['irb', 'ethics committee', 'institutional review board', 
                                     'ethics approval', 'human subjects approval'],
                'severity': ViolationSeverity.HIGH
            },
            'animal_research': {
                'keywords': ['animal research', 'laboratory animals', 'mice', 'rats', 'primates',
                           'animal subjects', 'animal testing', 'animal experiments'],
                'required_approvals': ['iacuc', 'animal care committee', 'animal ethics', 
                                     'animal welfare approval'],
                'severity': ViolationSeverity.HIGH
            },
            'genetic_research': {
                'keywords': ['genetic engineering', 'gene editing', 'crispr', 'genetic modification',
                           'recombinant dna', 'gene therapy', 'genetic manipulation'],
                'required_approvals': ['biosafety committee', 'genetic research approval', 
                                     'recombinant dna approval'],
                'severity': ViolationSeverity.CRITICAL
            },
            'data_privacy': {
                'keywords': ['personal data', 'private information', 'confidential data', 
                           'sensitive information', 'personally identifiable'],
                'required_approvals': ['data protection approval', 'privacy review', 
                                     'data handling protocol'],
                'severity': ViolationSeverity.MEDIUM
            }
        }
        
        # Real-time monitoring cache
        self._violation_cache = {}
        self._dashboard_cache = {}
        self._cache_expiry = timedelta(minutes=5)
    
    async def check_institutional_guidelines(self, user_id: str, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced automated policy checking with real-time monitoring"""
        db = next(get_db())
        try:
            logger.info(f"Checking compliance for user {user_id}, action: {action}")
            
            # Get user's institution and role
            user_role = db.query(UserRole).filter(
                and_(UserRole.user_id == user_id, UserRole.is_active == True)
            ).first()
            
            if not user_role:
                logger.warning(f"No institutional affiliation found for user {user_id}")
                return {"compliant": True, "message": "No institutional affiliation"}
            
            # Get active policies for the institution with priority ordering
            policies = db.query(InstitutionalPolicy).filter(
                and_(
                    InstitutionalPolicy.institution_id == user_role.institution_id,
                    InstitutionalPolicy.is_active == True,
                    InstitutionalPolicy.effective_date <= datetime.now()
                )
            ).order_by(InstitutionalPolicy.enforcement_level.desc()).all()
            
            logger.info(f"Found {len(policies)} policies for institution {user_role.institution_id}")
            for policy in policies:
                logger.info(f"Policy: {policy.policy_name} (type: {policy.policy_type}, active: {policy.is_active})")
            
            violations = []
            warnings = []
            policy_results = []
            
            # Enhanced policy checking with detailed results
            for policy in policies:
                logger.info(f"Checking policy: {policy.policy_name} (type: {policy.policy_type})")
                result = await self._check_policy_compliance(
                    policy, user_id, action, context, db
                )
                
                logger.info(f"Policy {policy.policy_name} result: {result}")
                
                policy_results.append({
                    'policy_id': policy.id,
                    'policy_name': policy.policy_name,
                    'policy_type': policy.policy_type,
                    'result': result
                })
                
                if result['violation']:
                    violation_data = {
                        **result,
                        'policy_id': policy.id,
                        'policy_name': policy.policy_name,
                        'enforcement_level': policy.enforcement_level,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if policy.enforcement_level == 'blocking':
                        violations.append(violation_data)
                    else:
                        warnings.append(violation_data)
            
            # Real-time violation tracking
            if violations or warnings:
                await self._update_real_time_violations(
                    user_role.institution_id, violations, warnings
                )
            
            # Enhanced logging with context
            await self._log_compliance_check(
                user_id, user_role.institution_id, action, 
                violations, warnings, db, context
            )
            
            compliance_result = {
                "compliant": len(violations) == 0,
                "violations": violations,
                "warnings": warnings,
                "institution_id": user_role.institution_id,
                "policy_results": policy_results,
                "check_timestamp": datetime.now().isoformat(),
                "risk_score": self._calculate_risk_score(violations, warnings)
            }
            
            logger.info(f"Compliance check completed for user {user_id}: {compliance_result['compliant']}")
            return compliance_result
            
        except Exception as e:
            logger.error(f"Error in compliance check: {str(e)}")
            raise
        finally:
            db.close()
    
    async def monitor_ethical_compliance(self, research_proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced ethical compliance monitoring for research proposals"""
        db = next(get_db())
        try:
            user_id = research_proposal.get('user_id')
            content = research_proposal.get('content', '')
            title = research_proposal.get('title', '')
            research_type = research_proposal.get('research_type', 'general')
            
            logger.info(f"Monitoring ethical compliance for research proposal: {title}")
            
            # Get user's institution
            user_role = db.query(UserRole).filter(
                and_(UserRole.user_id == user_id, UserRole.is_active == True)
            ).first()
            
            if not user_role:
                logger.warning(f"No institutional oversight for user {user_id}")
                return {"compliant": True, "message": "No institutional oversight"}
            
            # Enhanced ethical issue detection
            ethical_issues = await self._detect_ethical_issues_enhanced(
                content, title, research_type
            )
            
            # Check against institutional ethics policies
            ethics_policies = db.query(InstitutionalPolicy).filter(
                and_(
                    InstitutionalPolicy.institution_id == user_role.institution_id,
                    InstitutionalPolicy.policy_type == PolicyType.RESEARCH_ETHICS.value,
                    InstitutionalPolicy.is_active == True
                )
            ).all()
            
            policy_violations = []
            for policy in ethics_policies:
                policy_result = await self._check_research_ethics_detailed(
                    policy, content, title, research_type
                )
                if policy_result['violations']:
                    policy_violations.extend(policy_result['violations'])
            
            # Combine detected issues with policy violations
            all_violations = ethical_issues + policy_violations
            
            # Create violation records
            violation_records = []
            for issue in all_violations:
                violation = ComplianceViolation(
                    user_id=user_id,
                    institution_id=user_role.institution_id,
                    policy_id=issue.get('policy_id', 'ethics_general'),
                    violation_type='ethical_concern',
                    severity=issue['severity'],
                    description=issue['description'],
                    context_data={
                        "research_proposal": research_proposal,
                        "detection_method": issue.get('detection_method', 'automated'),
                        "confidence_score": issue.get('confidence_score', 0.8)
                    }
                )
                db.add(violation)
                violation_records.append({
                    'id': violation.id,
                    'category': issue['category'],
                    'severity': issue['severity'],
                    'description': issue['description'],
                    'recommendations': issue.get('recommendations', []),
                    'required_actions': issue.get('required_actions', [])
                })
            
            db.commit()
            
            # Calculate compliance score
            compliance_score = self._calculate_ethics_compliance_score(all_violations)
            
            # Determine review requirements
            critical_issues = [v for v in all_violations if v['severity'] == ViolationSeverity.CRITICAL.value]
            high_issues = [v for v in all_violations if v['severity'] == ViolationSeverity.HIGH.value]
            
            requires_review = len(critical_issues) > 0 or len(high_issues) > 2
            requires_committee_review = len(critical_issues) > 0
            
            result = {
                "compliant": len(all_violations) == 0,
                "ethical_issues": violation_records,
                "requires_review": requires_review,
                "requires_committee_review": requires_committee_review,
                "compliance_score": compliance_score,
                "risk_assessment": {
                    "critical_issues": len(critical_issues),
                    "high_issues": len(high_issues),
                    "medium_issues": len([v for v in all_violations if v['severity'] == ViolationSeverity.MEDIUM.value]),
                    "low_issues": len([v for v in all_violations if v['severity'] == ViolationSeverity.LOW.value])
                },
                "next_steps": self._generate_ethics_next_steps(all_violations),
                "review_timeline": self._calculate_review_timeline(all_violations)
            }
            
            logger.info(f"Ethics compliance check completed: {result['compliant']}, score: {compliance_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error in ethical compliance monitoring: {str(e)}")
            raise
        finally:
            db.close()
    
    async def detect_violations(self, institution_id: str, time_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Enhanced violation detection and classification with detailed reporting"""
        db = next(get_db())
        try:
            logger.info(f"Detecting violations for institution {institution_id}")
            
            # Build query with filters
            query = db.query(ComplianceViolation).filter(
                ComplianceViolation.institution_id == institution_id
            )
            
            if time_range:
                if 'start' in time_range:
                    query = query.filter(ComplianceViolation.detected_at >= time_range['start'])
                if 'end' in time_range:
                    query = query.filter(ComplianceViolation.detected_at <= time_range['end'])
            
            violations = query.order_by(desc(ComplianceViolation.detected_at)).all()
            
            # Enhanced classification with detailed analysis
            classified_violations = {
                'critical': [],
                'high': [],
                'medium': [],
                'low': []
            }
            
            # Violation patterns and trends
            violation_patterns = {}
            user_violation_counts = {}
            policy_violation_counts = {}
            
            for violation in violations:
                # Basic violation data
                violation_data = {
                    'id': violation.id,
                    'user_id': violation.user_id,
                    'policy_id': violation.policy_id,
                    'violation_type': violation.violation_type,
                    'description': violation.description,
                    'detected_at': violation.detected_at,
                    'resolution_status': violation.resolution_status,
                    'context_data': violation.context_data,
                    'resolution_notes': violation.resolution_notes,
                    'resolved_at': violation.resolved_at
                }
                
                # Add to severity classification
                classified_violations[violation.severity].append(violation_data)
                
                # Track patterns
                pattern_key = f"{violation.violation_type}_{violation.severity}"
                violation_patterns[pattern_key] = violation_patterns.get(pattern_key, 0) + 1
                
                # Track user violations
                user_violation_counts[violation.user_id] = user_violation_counts.get(violation.user_id, 0) + 1
                
                # Track policy violations
                policy_violation_counts[violation.policy_id] = policy_violation_counts.get(violation.policy_id, 0) + 1
            
            # Calculate violation statistics
            total_violations = len(violations)
            resolved_violations = len([v for v in violations if v.resolution_status == 'resolved'])
            open_violations = len([v for v in violations if v.resolution_status == 'open'])
            
            # Identify trends and anomalies
            trends = await self._analyze_violation_trends(violations, time_range)
            anomalies = await self._detect_violation_anomalies(violations)
            
            # Generate risk assessment
            risk_assessment = self._calculate_institutional_risk(classified_violations)
            
            # Identify repeat offenders
            repeat_offenders = [
                user_id for user_id, count in user_violation_counts.items() 
                if count >= 3
            ]
            
            # Policy effectiveness analysis
            policy_effectiveness = await self._analyze_policy_effectiveness(
                policy_violation_counts, db
            )
            
            result = {
                'violations': classified_violations,
                'statistics': {
                    'total_violations': total_violations,
                    'resolved_violations': resolved_violations,
                    'open_violations': open_violations,
                    'resolution_rate': (resolved_violations / total_violations * 100) if total_violations > 0 else 0
                },
                'patterns': violation_patterns,
                'trends': trends,
                'anomalies': anomalies,
                'risk_assessment': risk_assessment,
                'repeat_offenders': repeat_offenders,
                'policy_effectiveness': policy_effectiveness,
                'recommendations': self._generate_violation_recommendations(
                    classified_violations, trends, anomalies
                ),
                'generated_at': datetime.now()
            }
            
            logger.info(f"Violation detection completed: {total_violations} violations found")
            return result
            
        except Exception as e:
            logger.error(f"Error in violation detection: {str(e)}")
            raise
        finally:
            db.close()
    
    async def generate_compliance_dashboard_data(self, institution_id: str) -> Dict[str, Any]:
        """Generate enhanced real-time compliance dashboard with comprehensive monitoring"""
        db = next(get_db())
        try:
            logger.info(f"Generating compliance dashboard for institution {institution_id}")
            
            # Check cache first
            cache_key = f"dashboard_{institution_id}"
            if cache_key in self._dashboard_cache:
                cached_data, cache_time = self._dashboard_cache[cache_key]
                if datetime.now() - cache_time < self._cache_expiry:
                    logger.info("Returning cached dashboard data")
                    return cached_data
            
            # Time ranges for analysis
            now = datetime.now()
            last_30_days = now - timedelta(days=30)
            last_7_days = now - timedelta(days=7)
            last_24_hours = now - timedelta(hours=24)
            
            # Enhanced violation statistics with time-based analysis
            violation_stats_30d = db.query(
                ComplianceViolation.severity,
                func.count(ComplianceViolation.id).label('count')
            ).filter(
                and_(
                    ComplianceViolation.institution_id == institution_id,
                    ComplianceViolation.detected_at >= last_30_days
                )
            ).group_by(ComplianceViolation.severity).all()
            
            violation_stats_7d = db.query(
                ComplianceViolation.severity,
                func.count(ComplianceViolation.id).label('count')
            ).filter(
                and_(
                    ComplianceViolation.institution_id == institution_id,
                    ComplianceViolation.detected_at >= last_7_days
                )
            ).group_by(ComplianceViolation.severity).all()
            
            violation_stats_24h = db.query(
                ComplianceViolation.severity,
                func.count(ComplianceViolation.id).label('count')
            ).filter(
                and_(
                    ComplianceViolation.institution_id == institution_id,
                    ComplianceViolation.detected_at >= last_24_hours
                )
            ).group_by(ComplianceViolation.severity).all()
            
            # Compliance rate calculation with enhanced metrics
            total_checks = db.query(AuditLog).filter(
                and_(
                    AuditLog.institution_id == institution_id,
                    AuditLog.action.like('%compliance_check%'),
                    AuditLog.timestamp >= last_30_days
                )
            ).count()
            
            violations_count = db.query(ComplianceViolation).filter(
                and_(
                    ComplianceViolation.institution_id == institution_id,
                    ComplianceViolation.detected_at >= last_30_days
                )
            ).count()
            
            compliance_rate = ((total_checks - violations_count) / total_checks * 100) if total_checks > 0 else 100
            
            # Real-time alerts and critical issues
            critical_violations = db.query(ComplianceViolation).filter(
                and_(
                    ComplianceViolation.institution_id == institution_id,
                    ComplianceViolation.severity == ViolationSeverity.CRITICAL.value,
                    ComplianceViolation.resolution_status == 'open'
                )
            ).all()
            
            # Recent violations with enhanced details
            recent_violations = db.query(ComplianceViolation).filter(
                ComplianceViolation.institution_id == institution_id
            ).order_by(desc(ComplianceViolation.detected_at)).limit(20).all()
            
            # Policy effectiveness with detailed metrics
            policies = db.query(InstitutionalPolicy).filter(
                InstitutionalPolicy.institution_id == institution_id
            ).all()
            
            policy_effectiveness = []
            for policy in policies:
                policy_violations_30d = db.query(ComplianceViolation).filter(
                    and_(
                        ComplianceViolation.policy_id == policy.id,
                        ComplianceViolation.detected_at >= last_30_days
                    )
                ).count()
                
                policy_violations_total = db.query(ComplianceViolation).filter(
                    ComplianceViolation.policy_id == policy.id
                ).count()
                
                policy_effectiveness.append({
                    'policy_id': policy.id,
                    'policy_name': policy.policy_name,
                    'policy_type': policy.policy_type,
                    'violations_30d': policy_violations_30d,
                    'violations_total': policy_violations_total,
                    'enforcement_level': policy.enforcement_level,
                    'effectiveness_score': self._calculate_policy_effectiveness_score(
                        policy_violations_30d, policy_violations_total
                    )
                })
            
            # User compliance metrics
            user_compliance_stats = await self._get_user_compliance_stats(institution_id, db)
            
            # Trend analysis
            trend_data = await self._get_compliance_trends(institution_id, db)
            
            # Risk assessment
            risk_assessment = await self._get_institutional_risk_assessment(institution_id, db)
            
            # Performance metrics
            performance_metrics = {
                'average_resolution_time': await self._calculate_average_resolution_time(institution_id, db),
                'resolution_rate': await self._calculate_resolution_rate(institution_id, db),
                'repeat_violation_rate': await self._calculate_repeat_violation_rate(institution_id, db)
            }
            
            # Generate dashboard data
            dashboard_data = {
                'violation_statistics': {
                    '30_days': {stat.severity: stat.count for stat in violation_stats_30d},
                    '7_days': {stat.severity: stat.count for stat in violation_stats_7d},
                    '24_hours': {stat.severity: stat.count for stat in violation_stats_24h}
                },
                'compliance_metrics': {
                    'compliance_rate': compliance_rate,
                    'total_checks': total_checks,
                    'violations_count': violations_count,
                    'critical_open_violations': len(critical_violations)
                },
                'real_time_alerts': [
                    {
                        'id': v.id,
                        'violation_type': v.violation_type,
                        'severity': v.severity,
                        'description': v.description,
                        'detected_at': v.detected_at,
                        'user_id': v.user_id
                    } for v in critical_violations
                ],
                'recent_violations': [
                    {
                        'id': v.id,
                        'violation_type': v.violation_type,
                        'severity': v.severity,
                        'detected_at': v.detected_at,
                        'resolution_status': v.resolution_status,
                        'user_id': v.user_id,
                        'policy_id': v.policy_id
                    } for v in recent_violations
                ],
                'policy_effectiveness': policy_effectiveness,
                'user_compliance_stats': user_compliance_stats,
                'trend_data': trend_data,
                'risk_assessment': risk_assessment,
                'performance_metrics': performance_metrics,
                'system_health': {
                    'monitoring_active': True,
                    'last_check': now,
                    'policies_active': len([p for p in policies if p.is_active]),
                    'total_policies': len(policies)
                },
                'generated_at': now
            }
            
            # Cache the result
            self._dashboard_cache[cache_key] = (dashboard_data, now)
            
            logger.info(f"Dashboard generated successfully with {violations_count} violations")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating compliance dashboard: {str(e)}")
            raise
        finally:
            db.close()
    
    async def _check_policy_compliance(self, policy: InstitutionalPolicy, user_id: str, 
                                     action: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Check compliance against a specific policy"""
        policy_type = policy.policy_type
        
        logger.info(f"Checking policy type: {policy_type}, available checkers: {list(self.policy_checkers.keys())}")
        
        if policy_type in self.policy_checkers:
            return await self.policy_checkers[policy_type](policy, user_id, action, context, db)
        
        return {"violation": False, "message": f"Policy type '{policy_type}' not implemented"}
    
    async def _check_research_ethics(self, policy: InstitutionalPolicy, user_id: str, 
                                   action: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Check research ethics compliance"""
        rules = policy.rules or {}
        
        # Check for human subjects research
        if action == 'document_upload' and context.get('content'):
            content = context['content'].lower()
            
            # Look for indicators of human subjects research
            human_subjects_keywords = [
                'human subjects', 'participants', 'survey', 'interview', 
                'consent form', 'irb', 'ethics approval'
            ]
            
            if any(keyword in content for keyword in human_subjects_keywords):
                # Check if IRB approval is mentioned
                if 'irb' not in content and 'ethics approval' not in content:
                    violation = ComplianceViolation(
                        user_id=user_id,
                        institution_id=policy.institution_id,
                        policy_id=policy.id,
                        violation_type='missing_ethics_approval',
                        severity='high',
                        description='Research involving human subjects detected without ethics approval documentation',
                        context_data=context
                    )
                    db.add(violation)
                    db.commit()
                    
                    return {
                        "violation": True,
                        "message": "Human subjects research requires ethics approval documentation",
                        "severity": "high"
                    }
        
        return {"violation": False}
    
    async def _check_data_usage(self, policy: InstitutionalPolicy, user_id: str, 
                              action: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Check data usage compliance"""
        rules = policy.rules or {}
        
        if action == 'document_upload':
            # Check file size limits
            max_file_size = rules.get('max_file_size_mb', 100)
            file_size_mb = context.get('file_size', 0) / (1024 * 1024)
            
            if file_size_mb > max_file_size:
                violation = ComplianceViolation(
                    user_id=user_id,
                    institution_id=policy.institution_id,
                    policy_id=policy.id,
                    violation_type='file_size_exceeded',
                    severity='medium',
                    description=f'File size ({file_size_mb:.1f}MB) exceeds limit ({max_file_size}MB)',
                    context_data=context
                )
                db.add(violation)
                db.commit()
                
                return {
                    "violation": True,
                    "message": f"File size exceeds institutional limit of {max_file_size}MB",
                    "severity": "medium"
                }
        
        return {"violation": False}
    
    async def _check_collaboration_policy(self, policy: InstitutionalPolicy, user_id: str, 
                                        action: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Check collaboration policy compliance"""
        rules = policy.rules or {}
        
        if action == 'share_document':
            # Check external sharing restrictions
            if rules.get('restrict_external_sharing', False):
                recipient_email = context.get('recipient_email', '')
                institution_domain = rules.get('institution_domain', '')
                
                if institution_domain and not recipient_email.endswith(f'@{institution_domain}'):
                    violation = ComplianceViolation(
                        user_id=user_id,
                        institution_id=policy.institution_id,
                        policy_id=policy.id,
                        violation_type='external_sharing_violation',
                        severity='medium',
                        description='Document shared with external recipient against policy',
                        context_data=context
                    )
                    db.add(violation)
                    db.commit()
                    
                    return {
                        "violation": True,
                        "message": "External document sharing is restricted by institutional policy",
                        "severity": "medium"
                    }
        
        return {"violation": False}
    
    async def _check_content_filtering(self, policy: InstitutionalPolicy, user_id: str, 
                                     action: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Check content filtering compliance"""
        rules = policy.rules or {}
        
        if action in ['document_upload', 'chat_message']:
            content = context.get('content', '')
            
            # Check for prohibited content
            prohibited_terms = rules.get('prohibited_terms', [])
            
            for term in prohibited_terms:
                if re.search(term, content, re.IGNORECASE):
                    violation = ComplianceViolation(
                        user_id=user_id,
                        institution_id=policy.institution_id,
                        policy_id=policy.id,
                        violation_type='prohibited_content',
                        severity='high',
                        description=f'Content contains prohibited term: {term}',
                        context_data=context
                    )
                    db.add(violation)
                    db.commit()
                    
                    return {
                        "violation": True,
                        "message": f"Content contains prohibited term: {term}",
                        "severity": "high"
                    }
        
        return {"violation": False}
    
    async def _check_access_control(self, policy: InstitutionalPolicy, user_id: str, 
                                  action: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Check access control compliance"""
        rules = policy.rules or {}
        
        # Check time-based access restrictions
        if rules.get('time_restrictions'):
            current_hour = datetime.now().hour
            allowed_hours = rules['time_restrictions'].get('allowed_hours', [])
            
            if allowed_hours and current_hour not in allowed_hours:
                violation = ComplianceViolation(
                    user_id=user_id,
                    institution_id=policy.institution_id,
                    policy_id=policy.id,
                    violation_type='time_restriction_violation',
                    severity='low',
                    description=f'Access attempted outside allowed hours: {current_hour}:00',
                    context_data=context
                )
                db.add(violation)
                db.commit()
                
                return {
                    "violation": True,
                    "message": "Access restricted during current time period",
                    "severity": "low"
                }
        
        return {"violation": False}
    
    async def _detect_ethical_issues(self, content: str) -> List[Dict[str, Any]]:
        """Detect potential ethical issues in research content"""
        issues = []
        content_lower = content.lower()
        
        # Check for sensitive research areas
        sensitive_keywords = {
            'human_subjects': ['human subjects', 'participants', 'volunteers', 'clinical trial'],
            'animal_research': ['animal', 'mice', 'rats', 'primates', 'laboratory animals'],
            'genetic_research': ['genetic', 'dna', 'genome', 'crispr', 'gene editing'],
            'data_privacy': ['personal data', 'private information', 'confidential', 'sensitive data']
        }
        
        for category, keywords in sensitive_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                # Check for appropriate approvals or safeguards
                approval_keywords = ['approved', 'ethics committee', 'irb', 'consent', 'protocol']
                
                if not any(approval in content_lower for approval in approval_keywords):
                    issues.append({
                        'category': category,
                        'severity': 'high' if category in ['human_subjects', 'genetic_research'] else 'medium',
                        'description': f'Potential {category.replace("_", " ")} research without documented approval',
                        'policy_id': f'ethics_{category}'
                    })
        
        return issues
    
    async def _log_compliance_check(self, user_id: str, institution_id: str, action: str, 
                                  violations: List[Dict], warnings: List[Dict], db: Session, 
                                  context: Dict[str, Any] = None):
        """Enhanced logging for compliance checks with detailed context"""
        audit_log = AuditLog(
            user_id=user_id,
            institution_id=institution_id,
            action=f'compliance_check_{action}',
            resource_type='compliance',
            resource_id=f'{user_id}_{action}',
            success=len(violations) == 0,
            audit_metadata={
                'violations_count': len(violations),
                'warnings_count': len(warnings),
                'violations': violations,
                'warnings': warnings,
                'context': context,
                'check_timestamp': datetime.now().isoformat()
            }
        )
        db.add(audit_log)
        db.commit()
    
    def _calculate_risk_score(self, violations: List[Dict], warnings: List[Dict]) -> float:
        """Calculate risk score based on violations and warnings"""
        score = 0.0
        
        # Weight violations by severity
        severity_weights = {
            ViolationSeverity.CRITICAL.value: 10.0,
            ViolationSeverity.HIGH.value: 5.0,
            ViolationSeverity.MEDIUM.value: 2.0,
            ViolationSeverity.LOW.value: 1.0
        }
        
        for violation in violations:
            severity = violation.get('severity', ViolationSeverity.LOW.value)
            score += severity_weights.get(severity, 1.0)
        
        for warning in warnings:
            severity = warning.get('severity', ViolationSeverity.LOW.value)
            score += severity_weights.get(severity, 1.0) * 0.5  # Warnings have half weight
        
        return min(score, 100.0)  # Cap at 100
    
    async def _update_real_time_violations(self, institution_id: str, violations: List[Dict], warnings: List[Dict]):
        """Update real-time violation tracking"""
        cache_key = f"violations_{institution_id}"
        self._violation_cache[cache_key] = {
            'violations': violations,
            'warnings': warnings,
            'timestamp': datetime.now()
        }
    
    async def _detect_ethical_issues_enhanced(self, content: str, title: str, research_type: str) -> List[Dict[str, Any]]:
        """Enhanced ethical issue detection with pattern matching"""
        issues = []
        content_lower = content.lower()
        title_lower = title.lower()
        
        for category, pattern_data in self.ethical_patterns.items():
            keywords = pattern_data['keywords']
            required_approvals = pattern_data['required_approvals']
            severity = pattern_data['severity']
            
            # Check if any keywords are present
            keyword_matches = [kw for kw in keywords if kw in content_lower or kw in title_lower]
            
            if keyword_matches:
                # Check for required approvals
                approval_found = any(approval in content_lower for approval in required_approvals)
                
                if not approval_found:
                    issues.append({
                        'category': category,
                        'severity': severity.value,
                        'description': f'Research involving {category.replace("_", " ")} detected without required approval documentation',
                        'matched_keywords': keyword_matches,
                        'required_approvals': required_approvals,
                        'policy_id': f'ethics_{category}',
                        'detection_method': 'pattern_matching',
                        'confidence_score': min(len(keyword_matches) * 0.3, 1.0),
                        'recommendations': self._get_ethics_recommendations(category),
                        'required_actions': self._get_required_actions(category)
                    })
        
        return issues
    
    def _calculate_ethics_compliance_score(self, violations: List[Dict]) -> float:
        """Calculate ethics compliance score"""
        if not violations:
            return 100.0
        
        penalty_weights = {
            ViolationSeverity.CRITICAL.value: 30.0,
            ViolationSeverity.HIGH.value: 15.0,
            ViolationSeverity.MEDIUM.value: 8.0,
            ViolationSeverity.LOW.value: 3.0
        }
        
        total_penalty = sum(
            penalty_weights.get(v['severity'], 3.0) for v in violations
        )
        
        return max(100.0 - total_penalty, 0.0)
    
    def _generate_ethics_next_steps(self, violations: List[Dict]) -> List[str]:
        """Generate next steps for ethics compliance"""
        if not violations:
            return ["No immediate action required"]
        
        next_steps = []
        critical_violations = [v for v in violations if v['severity'] == ViolationSeverity.CRITICAL.value]
        high_violations = [v for v in violations if v['severity'] == ViolationSeverity.HIGH.value]
        
        if critical_violations:
            next_steps.append("URGENT: Halt research activities until critical issues are resolved")
            next_steps.append("Contact institutional ethics committee immediately")
        
        if high_violations:
            next_steps.append("Submit research proposal to ethics review board")
            next_steps.append("Obtain required approvals before proceeding")
        
        next_steps.append("Review institutional ethics policies")
        next_steps.append("Consult with ethics advisor or committee")
        
        return next_steps
    
    def _calculate_review_timeline(self, violations: List[Dict]) -> Dict[str, Any]:
        """Calculate expected review timeline"""
        if not violations:
            return {"required": False}
        
        critical_count = len([v for v in violations if v['severity'] == ViolationSeverity.CRITICAL.value])
        high_count = len([v for v in violations if v['severity'] == ViolationSeverity.HIGH.value])
        
        if critical_count > 0:
            return {
                "required": True,
                "urgency": "immediate",
                "estimated_days": 1,
                "review_type": "emergency_committee_review"
            }
        elif high_count > 0:
            return {
                "required": True,
                "urgency": "high",
                "estimated_days": 7,
                "review_type": "expedited_review"
            }
        else:
            return {
                "required": True,
                "urgency": "standard",
                "estimated_days": 30,
                "review_type": "standard_review"
            }
    
    def _get_ethics_recommendations(self, category: str) -> List[str]:
        """Get ethics recommendations by category"""
        recommendations = {
            'human_subjects': [
                "Submit IRB application before beginning research",
                "Develop informed consent procedures",
                "Ensure participant privacy and confidentiality"
            ],
            'animal_research': [
                "Submit IACUC protocol for review",
                "Ensure proper animal care and housing",
                "Minimize animal use and suffering"
            ],
            'genetic_research': [
                "Submit biosafety protocol for review",
                "Ensure proper containment procedures",
                "Consider ethical implications of genetic modifications"
            ],
            'data_privacy': [
                "Implement data protection measures",
                "Obtain proper consent for data use",
                "Ensure compliance with privacy regulations"
            ]
        }
        return recommendations.get(category, ["Consult with ethics committee"])
    
    def _get_required_actions(self, category: str) -> List[str]:
        """Get required actions by category"""
        actions = {
            'human_subjects': [
                "Obtain IRB approval",
                "Develop consent forms",
                "Complete human subjects training"
            ],
            'animal_research': [
                "Obtain IACUC approval",
                "Complete animal care training",
                "Establish veterinary oversight"
            ],
            'genetic_research': [
                "Obtain biosafety approval",
                "Establish containment protocols",
                "Complete biosafety training"
            ],
            'data_privacy': [
                "Implement data protection plan",
                "Obtain data use agreements",
                "Complete privacy training"
            ]
        }
        return actions.get(category, ["Contact ethics committee"])
    
    async def _check_research_ethics_detailed(self, policy: InstitutionalPolicy, 
                                            content: str, title: str, research_type: str) -> Dict[str, Any]:
        """Detailed research ethics policy checking"""
        violations = []
        rules = policy.rules or {}
        
        # Check specific policy rules
        if rules.get('require_irb_approval', False):
            if 'irb' not in content.lower() and 'ethics approval' not in content.lower():
                violations.append({
                    'category': 'missing_irb_approval',
                    'severity': ViolationSeverity.HIGH.value,
                    'description': 'IRB approval required but not documented',
                    'policy_id': policy.id
                })
        
        # Check for prohibited research areas
        prohibited_areas = rules.get('prohibited_research_areas', [])
        for area in prohibited_areas:
            if area.lower() in content.lower() or area.lower() in title.lower():
                violations.append({
                    'category': 'prohibited_research',
                    'severity': ViolationSeverity.CRITICAL.value,
                    'description': f'Research in prohibited area: {area}',
                    'policy_id': policy.id
                })
        
        return {'violations': violations}
    
    async def _analyze_violation_trends(self, violations: List, time_range: Optional[Dict[str, datetime]]) -> Dict[str, Any]:
        """Analyze violation trends over time"""
        if not violations:
            return {"trend": "stable", "change_rate": 0.0}
        
        # Group violations by day
        daily_counts = {}
        for violation in violations:
            date_key = violation.detected_at.date()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        # Calculate trend
        dates = sorted(daily_counts.keys())
        if len(dates) < 2:
            return {"trend": "insufficient_data", "change_rate": 0.0}
        
        recent_avg = sum(daily_counts[date] for date in dates[-7:]) / min(7, len(dates))
        older_avg = sum(daily_counts[date] for date in dates[:-7]) / max(1, len(dates) - 7)
        
        change_rate = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0.0
        
        if change_rate > 20:
            trend = "increasing"
        elif change_rate < -20:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "change_rate": change_rate,
            "daily_average": recent_avg,
            "total_days": len(dates)
        }
    
    async def _detect_violation_anomalies(self, violations: List) -> List[Dict[str, Any]]:
        """Detect anomalies in violation patterns"""
        anomalies = []
        
        # Check for unusual spikes
        daily_counts = {}
        for violation in violations:
            date_key = violation.detected_at.date()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        if daily_counts:
            avg_daily = sum(daily_counts.values()) / len(daily_counts)
            threshold = avg_daily * 3  # 3x average is considered anomalous
            
            for date, count in daily_counts.items():
                if count > threshold:
                    anomalies.append({
                        'type': 'violation_spike',
                        'date': date,
                        'count': count,
                        'threshold': threshold,
                        'severity': 'high' if count > threshold * 2 else 'medium'
                    })
        
        return anomalies
    
    def _calculate_institutional_risk(self, classified_violations: Dict[str, List]) -> Dict[str, Any]:
        """Calculate institutional risk assessment"""
        critical_count = len(classified_violations.get('critical', []))
        high_count = len(classified_violations.get('high', []))
        medium_count = len(classified_violations.get('medium', []))
        low_count = len(classified_violations.get('low', []))
        
        # Risk score calculation
        risk_score = (critical_count * 10 + high_count * 5 + medium_count * 2 + low_count * 1)
        
        # Risk level determination
        if risk_score >= 50:
            risk_level = "critical"
        elif risk_score >= 25:
            risk_level = "high"
        elif risk_score >= 10:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'critical_violations': critical_count,
            'high_violations': high_count,
            'total_violations': critical_count + high_count + medium_count + low_count
        }
    
    async def _analyze_policy_effectiveness(self, policy_violation_counts: Dict[str, int], db: Session) -> List[Dict[str, Any]]:
        """Analyze policy effectiveness"""
        effectiveness_data = []
        
        for policy_id, violation_count in policy_violation_counts.items():
            policy = db.query(InstitutionalPolicy).filter(
                InstitutionalPolicy.id == policy_id
            ).first()
            
            if policy:
                # Calculate effectiveness score (lower violations = higher effectiveness)
                max_violations = max(policy_violation_counts.values()) if policy_violation_counts else 1
                effectiveness_score = max(0, 100 - (violation_count / max_violations * 100))
                
                effectiveness_data.append({
                    'policy_id': policy_id,
                    'policy_name': policy.policy_name,
                    'violation_count': violation_count,
                    'effectiveness_score': effectiveness_score,
                    'enforcement_level': policy.enforcement_level
                })
        
        return sorted(effectiveness_data, key=lambda x: x['effectiveness_score'], reverse=True)
    
    def _generate_violation_recommendations(self, classified_violations: Dict[str, List], 
                                          trends: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on violation analysis"""
        recommendations = []
        
        critical_count = len(classified_violations.get('critical', []))
        high_count = len(classified_violations.get('high', []))
        
        if critical_count > 0:
            recommendations.append(f"URGENT: Address {critical_count} critical violations immediately")
            recommendations.append("Consider implementing emergency compliance measures")
        
        if high_count > 5:
            recommendations.append(f"High priority: Review and strengthen policies causing {high_count} high-severity violations")
        
        if trends.get('trend') == 'increasing':
            recommendations.append("Violation trend is increasing - review compliance training and policies")
        
        if anomalies:
            recommendations.append("Unusual violation patterns detected - investigate potential systemic issues")
        
        if not recommendations:
            recommendations.append("Maintain current compliance monitoring practices")
        
        return recommendations
    
    def _calculate_policy_effectiveness_score(self, violations_30d: int, violations_total: int) -> float:
        """Calculate policy effectiveness score"""
        if violations_total == 0:
            return 100.0
        
        # Recent violations should have more weight
        recent_weight = violations_30d * 2
        total_weight = violations_total
        
        # Higher violations = lower effectiveness
        effectiveness = max(0, 100 - (recent_weight + total_weight) * 2)
        return min(effectiveness, 100.0)
    
    async def _get_user_compliance_stats(self, institution_id: str, db: Session) -> Dict[str, Any]:
        """Get user compliance statistics"""
        # Get violation counts by user
        user_violations = db.query(
            ComplianceViolation.user_id,
            func.count(ComplianceViolation.id).label('violation_count')
        ).filter(
            ComplianceViolation.institution_id == institution_id
        ).group_by(ComplianceViolation.user_id).all()
        
        total_users = db.query(UserRole).filter(
            and_(
                UserRole.institution_id == institution_id,
                UserRole.is_active == True
            )
        ).count()
        
        users_with_violations = len(user_violations)
        compliance_rate = ((total_users - users_with_violations) / total_users * 100) if total_users > 0 else 100
        
        return {
            'total_users': total_users,
            'users_with_violations': users_with_violations,
            'user_compliance_rate': compliance_rate,
            'average_violations_per_user': sum(uv.violation_count for uv in user_violations) / max(users_with_violations, 1)
        }
    
    async def _get_compliance_trends(self, institution_id: str, db: Session) -> Dict[str, Any]:
        """Get compliance trends over time"""
        # Get violations for the last 30 days grouped by day
        last_30_days = datetime.now() - timedelta(days=30)
        
        daily_violations = db.query(
            func.date(ComplianceViolation.detected_at).label('date'),
            func.count(ComplianceViolation.id).label('count')
        ).filter(
            and_(
                ComplianceViolation.institution_id == institution_id,
                ComplianceViolation.detected_at >= last_30_days
            )
        ).group_by(func.date(ComplianceViolation.detected_at)).all()
        
        trend_data = [
            {'date': str(dv.date), 'violations': dv.count}
            for dv in daily_violations
        ]
        
        return {
            'daily_violations': trend_data,
            'period': '30_days'
        }
    
    async def _get_institutional_risk_assessment(self, institution_id: str, db: Session) -> Dict[str, Any]:
        """Get institutional risk assessment"""
        # Get open critical and high violations
        critical_open = db.query(ComplianceViolation).filter(
            and_(
                ComplianceViolation.institution_id == institution_id,
                ComplianceViolation.severity == ViolationSeverity.CRITICAL.value,
                ComplianceViolation.resolution_status == 'open'
            )
        ).count()
        
        high_open = db.query(ComplianceViolation).filter(
            and_(
                ComplianceViolation.institution_id == institution_id,
                ComplianceViolation.severity == ViolationSeverity.HIGH.value,
                ComplianceViolation.resolution_status == 'open'
            )
        ).count()
        
        # Calculate risk level
        if critical_open > 0:
            risk_level = "critical"
        elif high_open > 3:
            risk_level = "high"
        elif high_open > 0:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            'risk_level': risk_level,
            'critical_open_violations': critical_open,
            'high_open_violations': high_open,
            'requires_immediate_attention': critical_open > 0 or high_open > 5
        }
    
    async def _calculate_average_resolution_time(self, institution_id: str, db: Session) -> float:
        """Calculate average violation resolution time in hours"""
        resolved_violations = db.query(ComplianceViolation).filter(
            and_(
                ComplianceViolation.institution_id == institution_id,
                ComplianceViolation.resolution_status == 'resolved',
                ComplianceViolation.resolved_at.isnot(None)
            )
        ).all()
        
        if not resolved_violations:
            return 0.0
        
        total_hours = sum(
            (v.resolved_at - v.detected_at).total_seconds() / 3600
            for v in resolved_violations
        )
        
        return total_hours / len(resolved_violations)
    
    async def _calculate_resolution_rate(self, institution_id: str, db: Session) -> float:
        """Calculate violation resolution rate"""
        total_violations = db.query(ComplianceViolation).filter(
            ComplianceViolation.institution_id == institution_id
        ).count()
        
        resolved_violations = db.query(ComplianceViolation).filter(
            and_(
                ComplianceViolation.institution_id == institution_id,
                ComplianceViolation.resolution_status == 'resolved'
            )
        ).count()
        
        return (resolved_violations / total_violations * 100) if total_violations > 0 else 0.0
    
    async def _calculate_repeat_violation_rate(self, institution_id: str, db: Session) -> float:
        """Calculate repeat violation rate"""
        # Get users with multiple violations
        user_violation_counts = db.query(
            ComplianceViolation.user_id,
            func.count(ComplianceViolation.id).label('count')
        ).filter(
            ComplianceViolation.institution_id == institution_id
        ).group_by(ComplianceViolation.user_id).all()
        
        repeat_offenders = len([uvc for uvc in user_violation_counts if uvc.count > 1])
        total_users_with_violations = len(user_violation_counts)
        
        return (repeat_offenders / total_users_with_violations * 100) if total_users_with_violations > 0 else 0.0
    
    # Add new policy checkers
    async def _check_publication_ethics(self, policy: InstitutionalPolicy, user_id: str, 
                                      action: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Check publication ethics compliance"""
        rules = policy.rules or {}
        
        if action == 'document_upload' and context.get('document_type') == 'manuscript':
            content = context.get('content', '').lower()
            
            # Check for plagiarism indicators
            if rules.get('check_plagiarism', True):
                # Simple plagiarism detection (in real implementation, use proper tools)
                suspicious_phrases = rules.get('suspicious_phrases', [])
                for phrase in suspicious_phrases:
                    if phrase.lower() in content:
                        violation = ComplianceViolation(
                            user_id=user_id,
                            institution_id=policy.institution_id,
                            policy_id=policy.id,
                            violation_type='potential_plagiarism',
                            severity='high',
                            description=f'Potential plagiarism detected: suspicious phrase found',
                            context_data=context
                        )
                        db.add(violation)
                        db.commit()
                        
                        return {
                            "violation": True,
                            "message": "Potential plagiarism detected in manuscript",
                            "severity": "high"
                        }
        
        return {"violation": False}
    
    async def _check_data_privacy(self, policy: InstitutionalPolicy, user_id: str, 
                                action: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Check data privacy compliance"""
        rules = policy.rules or {}
        
        if action in ['document_upload', 'data_processing']:
            content = context.get('content', '').lower()
            
            # Check for personal data indicators
            personal_data_patterns = [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email pattern
                r'\b\d{3}-\d{3}-\d{4}\b'  # Phone pattern
            ]
            
            for pattern in personal_data_patterns:
                if re.search(pattern, content):
                    violation = ComplianceViolation(
                        user_id=user_id,
                        institution_id=policy.institution_id,
                        policy_id=policy.id,
                        violation_type='personal_data_exposure',
                        severity='medium',
                        description='Personal data detected without proper protection',
                        context_data=context
                    )
                    db.add(violation)
                    db.commit()
                    
                    return {
                        "violation": True,
                        "message": "Personal data detected - ensure proper privacy protection",
                        "severity": "medium"
                    }
        
        return {"violation": False}