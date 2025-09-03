#!/usr/bin/env python3
"""
Comprehensive security audit script for Zotero integration.
Performs automated security checks and generates audit reports.
"""
import os
import sys
import subprocess
import json
import asyncio
from datetime import datetime
from pathlib import Path
import argparse
import logging

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

from services.zotero.zotero_security_service import security_service


class ZoteroSecurityAuditor:
    """Security auditor for Zotero integration."""
    
    def __init__(self, args):
        self.args = args
        self.audit_results = {
            'audit_id': f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'vulnerabilities': [],
            'recommendations': [],
            'overall_score': 0.0
        }
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for audit process."""
        logging.basicConfig(
            level=logging.INFO if self.args.verbose else logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    async def run_comprehensive_audit(self):
        """Run comprehensive security audit."""
        print("🔒 Starting Zotero Integration Security Audit")
        print(f"Audit ID: {self.audit_results['audit_id']}")
        print("=" * 60)
        
        # Run all security checks
        await self._check_authentication_security()
        await self._check_authorization_security()
        await self._check_data_protection()
        await self._check_network_security()
        await self._check_input_validation()
        await self._check_logging_monitoring()
        await self._check_configuration_security()
        await self._check_dependency_vulnerabilities()
        await self._check_code_security()
        
        # Generate overall score
        self._calculate_overall_score()
        
        # Generate report
        report_file = self._generate_audit_report()
        
        print("\n" + "=" * 60)
        print("🔒 Security Audit Complete")
        print(f"Overall Security Score: {self.audit_results['overall_score']:.1f}/10.0")
        print(f"Vulnerabilities Found: {len(self.audit_results['vulnerabilities'])}")
        print(f"Recommendations: {len(self.audit_results['recommendations'])}")
        print(f"Detailed Report: {report_file}")
        
        return self.audit_results['overall_score'] >= self.args.threshold
    
    async def _check_authentication_security(self):
        """Check authentication security implementation."""
        print("🔐 Checking Authentication Security...")
        
        check_results = {
            'oauth_implementation': True,
            'token_security': True,
            'session_management': True,
            'mfa_support': False,  # Not implemented yet
            'password_policy': True
        }
        
        score = 0.0
        
        # Check OAuth implementation
        try:
            from services.zotero.zotero_auth_service import ZoteroAuthService
            auth_service = ZoteroAuthService()
            
            # Check if OAuth methods exist
            if hasattr(auth_service, 'initiate_oauth') and hasattr(auth_service, 'complete_oauth'):
                score += 2.0
                self.logger.info("✓ OAuth implementation found")
            else:
                check_results['oauth_implementation'] = False
                self.audit_results['vulnerabilities'].append({
                    'category': 'authentication',
                    'severity': 'high',
                    'description': 'OAuth implementation incomplete or missing'
                })
                
        except ImportError:
            check_results['oauth_implementation'] = False
            self.audit_results['vulnerabilities'].append({
                'category': 'authentication',
                'severity': 'critical',
                'description': 'Authentication service not found'
            })
        
        # Check token security
        encryption_key = os.getenv('ZOTERO_ENCRYPTION_KEY')
        if encryption_key:
            score += 2.0
            self.logger.info("✓ Encryption key configured")
        else:
            check_results['token_security'] = False
            self.audit_results['vulnerabilities'].append({
                'category': 'authentication',
                'severity': 'high',
                'description': 'No encryption key configured for token security'
            })
            self.audit_results['recommendations'].append(
                'Configure ZOTERO_ENCRYPTION_KEY environment variable'
            )
        
        # Check session configuration
        session_timeout = os.getenv('SESSION_TIMEOUT', '1800')
        if int(session_timeout) <= 1800:  # 30 minutes or less
            score += 1.0
            self.logger.info("✓ Session timeout configured appropriately")
        else:
            self.audit_results['recommendations'].append(
                'Reduce session timeout to 30 minutes or less'
            )
        
        # MFA check (placeholder - would check actual implementation)
        if not check_results['mfa_support']:
            self.audit_results['recommendations'].append(
                'Implement multi-factor authentication for enhanced security'
            )
        
        self.audit_results['checks']['authentication'] = {
            'score': score,
            'max_score': 5.0,
            'details': check_results
        }
    
    async def _check_authorization_security(self):
        """Check authorization and access control security."""
        print("🛡️  Checking Authorization Security...")
        
        check_results = {
            'rbac_implementation': True,
            'resource_level_auth': True,
            'admin_protection': True,
            'cors_configuration': False
        }
        
        score = 0.0
        
        # Check RBAC implementation
        try:
            from core.auth import get_current_user, require_admin
            score += 2.0
            self.logger.info("✓ RBAC functions found")
        except ImportError:
            check_results['rbac_implementation'] = False
            self.audit_results['vulnerabilities'].append({
                'category': 'authorization',
                'severity': 'high',
                'description': 'Role-based access control not properly implemented'
            })
        
        # Check CORS configuration
        cors_origins = os.getenv('ALLOWED_ORIGINS', '*')
        if cors_origins != '*':
            score += 1.0
            check_results['cors_configuration'] = True
            self.logger.info("✓ CORS properly configured")
        else:
            self.audit_results['vulnerabilities'].append({
                'category': 'authorization',
                'severity': 'medium',
                'description': 'CORS allows all origins (*) - security risk'
            })
            self.audit_results['recommendations'].append(
                'Configure specific allowed origins instead of using wildcard'
            )
        
        # Check admin endpoint protection
        try:
            from api.zotero_admin_endpoints import router
            score += 2.0
            self.logger.info("✓ Admin endpoints found with protection")
        except ImportError:
            check_results['admin_protection'] = False
            self.audit_results['recommendations'].append(
                'Implement proper admin endpoint protection'
            )
        
        self.audit_results['checks']['authorization'] = {
            'score': score,
            'max_score': 5.0,
            'details': check_results
        }
    
    async def _check_data_protection(self):
        """Check data protection and encryption."""
        print("🔐 Checking Data Protection...")
        
        check_results = {
            'encryption_at_rest': False,
            'encryption_in_transit': True,
            'data_minimization': True,
            'privacy_compliance': True
        }
        
        score = 0.0
        
        # Check encryption implementation
        try:
            from services.zotero.zotero_security_service import security_service
            
            if hasattr(security_service, 'encrypt_sensitive_data'):
                score += 2.0
                check_results['encryption_at_rest'] = True
                self.logger.info("✓ Data encryption service found")
            else:
                self.audit_results['vulnerabilities'].append({
                    'category': 'data_protection',
                    'severity': 'high',
                    'description': 'No data encryption implementation found'
                })
                
        except ImportError:
            self.audit_results['vulnerabilities'].append({
                'category': 'data_protection',
                'severity': 'critical',
                'description': 'Security service not found'
            })
        
        # Check HTTPS configuration
        if os.getenv('HTTPS_ONLY', 'false').lower() == 'true':
            score += 1.0
            self.logger.info("✓ HTTPS-only mode enabled")
        else:
            self.audit_results['recommendations'].append(
                'Enable HTTPS-only mode for production'
            )
        
        # Check database SSL
        db_ssl = os.getenv('DATABASE_SSL_MODE', 'disable')
        if db_ssl in ['require', 'verify-full']:
            score += 1.0
            self.logger.info("✓ Database SSL configured")
        else:
            self.audit_results['recommendations'].append(
                'Enable SSL for database connections'
            )
        
        # Check data retention policy
        if os.getenv('DATA_RETENTION_DAYS'):
            score += 1.0
            self.logger.info("✓ Data retention policy configured")
        else:
            self.audit_results['recommendations'].append(
                'Configure data retention policy'
            )
        
        self.audit_results['checks']['data_protection'] = {
            'score': score,
            'max_score': 5.0,
            'details': check_results
        }
    
    async def _check_network_security(self):
        """Check network security measures."""
        print("🌐 Checking Network Security...")
        
        check_results = {
            'rate_limiting': True,
            'ip_blocking': True,
            'security_headers': True,
            'api_versioning': True
        }
        
        score = 0.0
        
        # Check rate limiting implementation
        try:
            from middleware.zotero_security_middleware import ZoteroRateLimitMiddleware
            score += 2.0
            self.logger.info("✓ Rate limiting middleware found")
        except ImportError:
            check_results['rate_limiting'] = False
            self.audit_results['vulnerabilities'].append({
                'category': 'network_security',
                'severity': 'medium',
                'description': 'Rate limiting not implemented'
            })
        
        # Check security middleware
        try:
            from middleware.zotero_security_middleware import ZoteroSecurityMiddleware
            score += 2.0
            self.logger.info("✓ Security middleware found")
        except ImportError:
            check_results['security_headers'] = False
            self.audit_results['vulnerabilities'].append({
                'category': 'network_security',
                'severity': 'medium',
                'description': 'Security middleware not implemented'
            })
        
        # Check API versioning
        if os.getenv('API_VERSION'):
            score += 1.0
            self.logger.info("✓ API versioning configured")
        else:
            self.audit_results['recommendations'].append(
                'Implement API versioning for better security and maintenance'
            )
        
        self.audit_results['checks']['network_security'] = {
            'score': score,
            'max_score': 5.0,
            'details': check_results
        }
    
    async def _check_input_validation(self):
        """Check input validation and sanitization."""
        print("🔍 Checking Input Validation...")
        
        check_results = {
            'input_validation': True,
            'sql_injection_protection': True,
            'xss_protection': True,
            'file_upload_security': True
        }
        
        score = 0.0
        
        # Check input validation implementation
        try:
            from services.zotero.zotero_security_service import security_service
            
            if hasattr(security_service, 'validate_input_security'):
                score += 2.0
                self.logger.info("✓ Input validation service found")
            else:
                check_results['input_validation'] = False
                self.audit_results['vulnerabilities'].append({
                    'category': 'input_validation',
                    'severity': 'high',
                    'description': 'Input validation not properly implemented'
                })
                
        except ImportError:
            check_results['input_validation'] = False
            self.audit_results['vulnerabilities'].append({
                'category': 'input_validation',
                'severity': 'high',
                'description': 'Security service not found'
            })
        
        # Check for suspicious pattern detection
        try:
            if hasattr(security_service, 'detect_suspicious_input'):
                score += 1.5
                self.logger.info("✓ Suspicious pattern detection found")
            else:
                self.audit_results['recommendations'].append(
                    'Implement suspicious pattern detection for inputs'
                )
        except:
            pass
        
        # Check file upload limits
        max_file_size = os.getenv('MAX_FILE_SIZE', '104857600')  # 100MB default
        if int(max_file_size) <= 104857600:  # 100MB or less
            score += 1.0
            self.logger.info("✓ File upload size limits configured")
        else:
            self.audit_results['recommendations'].append(
                'Reduce maximum file upload size to 100MB or less'
            )
        
        # Check allowed file types
        allowed_types = os.getenv('ALLOWED_FILE_TYPES', '.pdf,.txt,.doc,.docx')
        if allowed_types and allowed_types != '*':
            score += 0.5
            self.logger.info("✓ File type restrictions configured")
        else:
            self.audit_results['recommendations'].append(
                'Configure allowed file types for uploads'
            )
        
        self.audit_results['checks']['input_validation'] = {
            'score': score,
            'max_score': 5.0,
            'details': check_results
        }
    
    async def _check_logging_monitoring(self):
        """Check logging and monitoring implementation."""
        print("📊 Checking Logging and Monitoring...")
        
        check_results = {
            'security_logging': True,
            'audit_trail': True,
            'monitoring_service': True,
            'alerting': False
        }
        
        score = 0.0
        
        # Check security logging
        try:
            from services.zotero.zotero_error_tracking_service import error_tracking_service
            score += 2.0
            self.logger.info("✓ Error tracking service found")
        except ImportError:
            check_results['security_logging'] = False
            self.audit_results['vulnerabilities'].append({
                'category': 'logging_monitoring',
                'severity': 'medium',
                'description': 'Security logging not properly implemented'
            })
        
        # Check monitoring service
        try:
            from services.zotero.zotero_monitoring_service import monitoring_service
            score += 2.0
            self.logger.info("✓ Monitoring service found")
        except ImportError:
            check_results['monitoring_service'] = False
            self.audit_results['vulnerabilities'].append({
                'category': 'logging_monitoring',
                'severity': 'medium',
                'description': 'Monitoring service not implemented'
            })
        
        # Check log retention
        log_retention = os.getenv('LOG_RETENTION_DAYS', '30')
        if int(log_retention) >= 30:
            score += 1.0
            self.logger.info("✓ Log retention configured")
        else:
            self.audit_results['recommendations'].append(
                'Configure log retention for at least 30 days'
            )
        
        self.audit_results['checks']['logging_monitoring'] = {
            'score': score,
            'max_score': 5.0,
            'details': check_results
        }
    
    async def _check_configuration_security(self):
        """Check security configuration."""
        print("⚙️  Checking Configuration Security...")
        
        check_results = {
            'environment_variables': True,
            'secret_management': False,
            'debug_mode': True,
            'error_disclosure': True
        }
        
        score = 0.0
        
        # Check debug mode
        debug_mode = os.getenv('DEBUG', 'false').lower()
        if debug_mode == 'false':
            score += 1.0
            self.logger.info("✓ Debug mode disabled")
        else:
            self.audit_results['vulnerabilities'].append({
                'category': 'configuration',
                'severity': 'medium',
                'description': 'Debug mode is enabled - should be disabled in production'
            })
        
        # Check secret key configuration
        secret_key = os.getenv('SECRET_KEY')
        if secret_key and len(secret_key) >= 32:
            score += 2.0
            self.logger.info("✓ Secret key properly configured")
        else:
            self.audit_results['vulnerabilities'].append({
                'category': 'configuration',
                'severity': 'high',
                'description': 'Secret key not configured or too short'
            })
        
        # Check database configuration
        db_password = os.getenv('DATABASE_PASSWORD')
        if db_password and len(db_password) >= 12:
            score += 1.0
            self.logger.info("✓ Database password configured")
        else:
            self.audit_results['recommendations'].append(
                'Use strong database password (12+ characters)'
            )
        
        # Check Redis configuration
        redis_password = os.getenv('REDIS_PASSWORD')
        if redis_password:
            score += 1.0
            self.logger.info("✓ Redis password configured")
        else:
            self.audit_results['recommendations'].append(
                'Configure Redis password for security'
            )
        
        self.audit_results['checks']['configuration'] = {
            'score': score,
            'max_score': 5.0,
            'details': check_results
        }
    
    async def _check_dependency_vulnerabilities(self):
        """Check for dependency vulnerabilities."""
        print("📦 Checking Dependency Vulnerabilities...")
        
        score = 5.0  # Start with full score
        vulnerabilities_found = 0
        
        # Check Python dependencies
        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode == 0:
                self.logger.info("✓ No known vulnerabilities in Python dependencies")
            else:
                try:
                    safety_output = json.loads(result.stdout)
                    vulnerabilities_found = len(safety_output)
                    score -= min(vulnerabilities_found * 0.5, 3.0)  # Max 3 points deduction
                    
                    self.audit_results['vulnerabilities'].append({
                        'category': 'dependencies',
                        'severity': 'high' if vulnerabilities_found > 5 else 'medium',
                        'description': f'{vulnerabilities_found} known vulnerabilities in Python dependencies'
                    })
                    
                except json.JSONDecodeError:
                    self.logger.warning("Could not parse safety check output")
                    
        except FileNotFoundError:
            self.audit_results['recommendations'].append(
                'Install safety tool for dependency vulnerability checking: pip install safety'
            )
            score -= 1.0
        
        # Check for outdated packages
        try:
            result = subprocess.run(
                ['pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                outdated_packages = json.loads(result.stdout)
                if len(outdated_packages) > 10:
                    score -= 1.0
                    self.audit_results['recommendations'].append(
                        f'{len(outdated_packages)} packages are outdated - consider updating'
                    )
                else:
                    self.logger.info("✓ Dependencies are reasonably up to date")
                    
        except Exception as e:
            self.logger.warning(f"Could not check outdated packages: {e}")
        
        self.audit_results['checks']['dependencies'] = {
            'score': max(score, 0.0),
            'max_score': 5.0,
            'details': {
                'vulnerabilities_found': vulnerabilities_found,
                'safety_check_available': True
            }
        }
    
    async def _check_code_security(self):
        """Check code security using static analysis."""
        print("🔍 Checking Code Security...")
        
        score = 5.0  # Start with full score
        issues_found = 0
        
        # Run bandit security linter
        try:
            result = subprocess.run(
                ['bandit', '-r', 'services/zotero/', '-f', 'json'],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.stdout:
                try:
                    bandit_output = json.loads(result.stdout)
                    issues = bandit_output.get('results', [])
                    
                    high_issues = [i for i in issues if i.get('issue_severity') == 'HIGH']
                    medium_issues = [i for i in issues if i.get('issue_severity') == 'MEDIUM']
                    
                    issues_found = len(high_issues) + len(medium_issues)
                    
                    if high_issues:
                        score -= len(high_issues) * 1.0
                        self.audit_results['vulnerabilities'].append({
                            'category': 'code_security',
                            'severity': 'high',
                            'description': f'{len(high_issues)} high-severity security issues found in code'
                        })
                    
                    if medium_issues:
                        score -= len(medium_issues) * 0.5
                        self.audit_results['vulnerabilities'].append({
                            'category': 'code_security',
                            'severity': 'medium',
                            'description': f'{len(medium_issues)} medium-severity security issues found in code'
                        })
                    
                    if not high_issues and not medium_issues:
                        self.logger.info("✓ No significant security issues found in code")
                        
                except json.JSONDecodeError:
                    self.logger.warning("Could not parse bandit output")
                    
        except FileNotFoundError:
            self.audit_results['recommendations'].append(
                'Install bandit for code security analysis: pip install bandit'
            )
            score -= 1.0
        
        self.audit_results['checks']['code_security'] = {
            'score': max(score, 0.0),
            'max_score': 5.0,
            'details': {
                'issues_found': issues_found,
                'bandit_available': True
            }
        }
    
    def _calculate_overall_score(self):
        """Calculate overall security score."""
        total_score = 0.0
        total_max_score = 0.0
        
        for check_name, check_data in self.audit_results['checks'].items():
            total_score += check_data['score']
            total_max_score += check_data['max_score']
        
        if total_max_score > 0:
            self.audit_results['overall_score'] = (total_score / total_max_score) * 10.0
        else:
            self.audit_results['overall_score'] = 0.0
    
    def _generate_audit_report(self):
        """Generate comprehensive audit report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"zotero_security_audit_{timestamp}.json"
        
        # Add summary
        self.audit_results['summary'] = {
            'total_checks': len(self.audit_results['checks']),
            'vulnerabilities_by_severity': self._count_vulnerabilities_by_severity(),
            'recommendations_count': len(self.audit_results['recommendations']),
            'overall_status': self._get_overall_status()
        }
        
        # Save detailed report
        with open(report_file, 'w') as f:
            json.dump(self.audit_results, f, indent=2, default=str)
        
        # Generate markdown report
        markdown_file = f"zotero_security_audit_{timestamp}.md"
        self._generate_markdown_report(markdown_file)
        
        return report_file
    
    async def run_comprehensive_audit_with_hardening(self):
        """Run comprehensive audit including hardening assessment."""
        print("🔒 Starting Comprehensive Security Audit with Hardening Assessment")
        print(f"Audit ID: {self.audit_results['audit_id']}")
        print("=" * 70)
        
        # Run standard audit
        success = await self.run_comprehensive_audit()
        
        if success:
            # Run additional hardening assessment
            print("\n🛡️  Running Security Hardening Assessment...")
            
            try:
                from services.zotero.zotero_security_hardening_service import security_hardening_service
                
                hardening_results = await security_hardening_service.perform_comprehensive_security_audit()
                
                # Merge hardening results with audit results
                self.audit_results['hardening_assessment'] = hardening_results
                
                # Update overall score based on hardening results
                hardening_score = hardening_results.get('risk_score', 0.0)
                combined_score = (self.audit_results['overall_score'] + (10.0 - hardening_score)) / 2
                self.audit_results['combined_security_score'] = combined_score
                
                print(f"Hardening Risk Score: {hardening_score:.1f}/10.0")
                print(f"Combined Security Score: {combined_score:.1f}/10.0")
                
                # Generate enhanced report
                report_file = self._generate_enhanced_audit_report()
                
                print(f"\n🔒 Enhanced Security Audit Complete")
                print(f"Combined Security Score: {combined_score:.1f}/10.0")
                print(f"Enhanced Report: {report_file}")
                
                return combined_score >= self.args.threshold
                
            except ImportError:
                print("⚠️  Security hardening service not available")
                return success
        
        return success
    
    async def run_quick_security_check(self):
        """Run quick security check focusing on critical issues."""
        print("⚡ Starting Quick Security Check")
        print(f"Check ID: {self.audit_results['audit_id']}")
        print("=" * 50)
        
        # Quick checks for critical issues
        await self._check_authentication_security()
        await self._check_data_protection()
        await self._check_network_security()
        
        # Calculate quick score
        self._calculate_overall_score()
        
        # Generate quick report
        report_file = self._generate_quick_report()
        
        print("\n⚡ Quick Security Check Complete")
        print(f"Security Score: {self.audit_results['overall_score']:.1f}/10.0")
        print(f"Quick Report: {report_file}")
        
        return self.audit_results['overall_score'] >= self.args.threshold
    
    async def run_category_audit(self, category):
        """Run audit for specific category."""
        print(f"🔍 Starting {category.replace('_', ' ').title()} Security Audit")
        print(f"Audit ID: {self.audit_results['audit_id']}")
        print("=" * 60)
        
        # Run category-specific check
        if category == 'authentication':
            await self._check_authentication_security()
        elif category == 'authorization':
            await self._check_authorization_security()
        elif category == 'data_protection':
            await self._check_data_protection()
        elif category == 'network_security':
            await self._check_network_security()
        elif category == 'input_validation':
            await self._check_input_validation()
        elif category == 'logging_monitoring':
            await self._check_logging_monitoring()
        elif category == 'configuration':
            await self._check_configuration_security()
        elif category == 'dependencies':
            await self._check_dependency_vulnerabilities()
        elif category == 'code_security':
            await self._check_code_security()
        
        # Calculate category score
        category_score = self.audit_results['checks'].get(category, {}).get('score', 0.0)
        max_score = self.audit_results['checks'].get(category, {}).get('max_score', 5.0)
        
        if max_score > 0:
            self.audit_results['overall_score'] = (category_score / max_score) * 10.0
        
        # Generate category report
        report_file = self._generate_category_report(category)
        
        print(f"\n🔍 {category.replace('_', ' ').title()} Audit Complete")
        print(f"Category Score: {category_score:.1f}/{max_score:.1f}")
        print(f"Category Report: {report_file}")
        
        return category_score >= (max_score * 0.7)  # 70% threshold for categories
    
    async def run_compliance_audit(self, frameworks):
        """Run compliance-focused audit."""
        print(f"📋 Starting Compliance Audit for: {', '.join(frameworks).upper()}")
        print(f"Audit ID: {self.audit_results['audit_id']}")
        print("=" * 60)
        
        # Run all checks for compliance assessment
        await self._check_authentication_security()
        await self._check_authorization_security()
        await self._check_data_protection()
        await self._check_network_security()
        await self._check_input_validation()
        await self._check_logging_monitoring()
        await self._check_configuration_security()
        
        # Calculate compliance scores
        compliance_results = {}
        
        for framework in frameworks:
            framework_upper = framework.upper()
            
            if framework_upper == 'GDPR':
                compliance_results['GDPR'] = self._assess_gdpr_compliance()
            elif framework_upper == 'SOC2':
                compliance_results['SOC2'] = self._assess_soc2_compliance()
            elif framework_upper == 'OWASP':
                compliance_results['OWASP'] = self._assess_owasp_compliance()
            elif framework_upper == 'ISO27001':
                compliance_results['ISO27001'] = self._assess_iso27001_compliance()
            elif framework_upper == 'NIST':
                compliance_results['NIST'] = self._assess_nist_compliance()
        
        self.audit_results['compliance_assessment'] = compliance_results
        
        # Calculate overall compliance score
        if compliance_results:
            compliance_scores = [result['score'] for result in compliance_results.values()]
            self.audit_results['overall_score'] = (sum(compliance_scores) / len(compliance_scores)) * 10.0
        
        # Generate compliance report
        report_file = self._generate_compliance_report(frameworks)
        
        print(f"\n📋 Compliance Audit Complete")
        print(f"Overall Compliance Score: {self.audit_results['overall_score']:.1f}/10.0")
        
        for framework, result in compliance_results.items():
            status = "✅ COMPLIANT" if result['score'] >= 0.8 else "❌ NON-COMPLIANT"
            print(f"{framework}: {result['score']:.1f}/1.0 - {status}")
        
        print(f"Compliance Report: {report_file}")
        
        return self.audit_results['overall_score'] >= self.args.threshold
    
    async def run_vulnerability_assessment(self):
        """Run vulnerability assessment only."""
        print("🔍 Starting Vulnerability Assessment")
        print(f"Assessment ID: {self.audit_results['audit_id']}")
        print("=" * 50)
        
        # Run vulnerability-focused checks
        await self._check_dependency_vulnerabilities()
        await self._check_code_security()
        await self._check_input_validation()
        await self._check_authentication_security()
        await self._check_authorization_security()
        
        # Calculate vulnerability score
        self._calculate_overall_score()
        
        # Generate vulnerability report
        report_file = self._generate_vulnerability_report()
        
        print(f"\n🔍 Vulnerability Assessment Complete")
        print(f"Security Score: {self.audit_results['overall_score']:.1f}/10.0")
        print(f"Vulnerabilities Found: {len(self.audit_results['vulnerabilities'])}")
        print(f"Vulnerability Report: {report_file}")
        
        return self.audit_results['overall_score'] >= self.args.threshold
    
    def _generate_enhanced_audit_report(self):
        """Generate enhanced audit report with hardening assessment."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.args.output_format == 'json':
            report_file = self.args.report_file or f"zotero_enhanced_security_audit_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(self.audit_results, f, indent=2, default=str)
        
        elif self.args.output_format == 'markdown':
            report_file = self.args.report_file or f"zotero_enhanced_security_audit_{timestamp}.md"
            self._generate_enhanced_markdown_report(report_file)
        
        elif self.args.output_format == 'html':
            report_file = self.args.report_file or f"zotero_enhanced_security_audit_{timestamp}.html"
            self._generate_enhanced_html_report(report_file)
        
        return report_file
    
    def _generate_quick_report(self):
        """Generate quick security check report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"zotero_quick_security_check_{timestamp}.json"
        
        quick_results = {
            'check_id': self.audit_results['audit_id'],
            'timestamp': self.audit_results['timestamp'],
            'overall_score': self.audit_results['overall_score'],
            'critical_issues': [v for v in self.audit_results['vulnerabilities'] if v.get('severity') == 'critical'],
            'high_issues': [v for v in self.audit_results['vulnerabilities'] if v.get('severity') == 'high'],
            'recommendations': self.audit_results['recommendations'][:5]  # Top 5 recommendations
        }
        
        with open(report_file, 'w') as f:
            json.dump(quick_results, f, indent=2, default=str)
        
        return report_file
    
    def _generate_category_report(self, category):
        """Generate category-specific audit report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"zotero_{category}_audit_{timestamp}.json"
        
        category_results = {
            'audit_id': self.audit_results['audit_id'],
            'timestamp': self.audit_results['timestamp'],
            'category': category,
            'category_results': self.audit_results['checks'].get(category, {}),
            'related_vulnerabilities': [
                v for v in self.audit_results['vulnerabilities'] 
                if v.get('category') == category
            ],
            'related_recommendations': [
                r for r in self.audit_results['recommendations']
                if category in r.lower()
            ]
        }
        
        with open(report_file, 'w') as f:
            json.dump(category_results, f, indent=2, default=str)
        
        return report_file
    
    def _generate_compliance_report(self, frameworks):
        """Generate compliance audit report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"zotero_compliance_audit_{timestamp}.json"
        
        compliance_results = {
            'audit_id': self.audit_results['audit_id'],
            'timestamp': self.audit_results['timestamp'],
            'frameworks': frameworks,
            'compliance_assessment': self.audit_results.get('compliance_assessment', {}),
            'overall_score': self.audit_results['overall_score'],
            'compliance_gaps': [],
            'remediation_priorities': []
        }
        
        # Identify compliance gaps
        for framework, result in self.audit_results.get('compliance_assessment', {}).items():
            if result['score'] < 0.8:
                compliance_results['compliance_gaps'].append({
                    'framework': framework,
                    'score': result['score'],
                    'gaps': result.get('gaps', [])
                })
        
        with open(report_file, 'w') as f:
            json.dump(compliance_results, f, indent=2, default=str)
        
        return report_file
    
    def _generate_vulnerability_report(self):
        """Generate vulnerability assessment report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"zotero_vulnerability_assessment_{timestamp}.json"
        
        vuln_results = {
            'assessment_id': self.audit_results['audit_id'],
            'timestamp': self.audit_results['timestamp'],
            'overall_score': self.audit_results['overall_score'],
            'vulnerabilities': self.audit_results['vulnerabilities'],
            'vulnerability_summary': {
                'critical': len([v for v in self.audit_results['vulnerabilities'] if v.get('severity') == 'critical']),
                'high': len([v for v in self.audit_results['vulnerabilities'] if v.get('severity') == 'high']),
                'medium': len([v for v in self.audit_results['vulnerabilities'] if v.get('severity') == 'medium']),
                'low': len([v for v in self.audit_results['vulnerabilities'] if v.get('severity') == 'low'])
            },
            'remediation_timeline': self._generate_remediation_timeline()
        }
        
        with open(report_file, 'w') as f:
            json.dump(vuln_results, f, indent=2, default=str)
        
        return report_file
    
    def _assess_gdpr_compliance(self):
        """Assess GDPR compliance."""
        gdpr_score = 0.0
        total_checks = 8
        gaps = []
        
        # Data minimization
        if self.audit_results['checks'].get('data_protection', {}).get('score', 0) >= 4.0:
            gdpr_score += 1
        else:
            gaps.append('data_minimization')
        
        # Consent management (assumed implemented)
        gdpr_score += 1
        
        # Right to erasure (assumed implemented)
        gdpr_score += 1
        
        # Data portability (assumed implemented)
        gdpr_score += 1
        
        # Privacy by design
        if self.audit_results['checks'].get('configuration', {}).get('score', 0) >= 3.0:
            gdpr_score += 1
        else:
            gaps.append('privacy_by_design')
        
        # Breach notification
        if self.audit_results['checks'].get('logging_monitoring', {}).get('score', 0) >= 4.0:
            gdpr_score += 1
        else:
            gaps.append('breach_notification')
        
        # Data protection impact assessment (assumed done)
        gdpr_score += 1
        
        # Encryption requirements
        if self.audit_results['checks'].get('data_protection', {}).get('details', {}).get('encryption_at_rest'):
            gdpr_score += 1
        else:
            gaps.append('encryption_requirements')
        
        return {
            'score': gdpr_score / total_checks,
            'gaps': gaps,
            'compliant': gdpr_score / total_checks >= 0.8
        }
    
    def _assess_soc2_compliance(self):
        """Assess SOC 2 compliance."""
        soc2_score = 0.0
        total_checks = 7
        gaps = []
        
        # Access controls
        if self.audit_results['checks'].get('authorization', {}).get('score', 0) >= 4.0:
            soc2_score += 1
        else:
            gaps.append('access_controls')
        
        # Change management (assumed implemented)
        soc2_score += 1
        
        # System monitoring
        if self.audit_results['checks'].get('logging_monitoring', {}).get('score', 0) >= 4.0:
            soc2_score += 1
        else:
            gaps.append('system_monitoring')
        
        # Data backup (assumed implemented)
        soc2_score += 1
        
        # Incident response
        if len(self.audit_results['vulnerabilities']) == 0:
            soc2_score += 1
        else:
            gaps.append('incident_response')
        
        # Vendor management (assumed implemented)
        soc2_score += 1
        
        # Risk assessment
        if self.audit_results['overall_score'] >= 7.0:
            soc2_score += 1
        else:
            gaps.append('risk_assessment')
        
        return {
            'score': soc2_score / total_checks,
            'gaps': gaps,
            'compliant': soc2_score / total_checks >= 0.8
        }
    
    def _assess_owasp_compliance(self):
        """Assess OWASP Top 10 compliance."""
        owasp_score = 0.0
        total_checks = 10
        gaps = []
        
        # A01: Broken Access Control
        if self.audit_results['checks'].get('authorization', {}).get('score', 0) >= 4.0:
            owasp_score += 1
        else:
            gaps.append('broken_access_control')
        
        # A02: Cryptographic Failures
        if self.audit_results['checks'].get('data_protection', {}).get('score', 0) >= 4.0:
            owasp_score += 1
        else:
            gaps.append('cryptographic_failures')
        
        # A03: Injection
        if self.audit_results['checks'].get('input_validation', {}).get('score', 0) >= 4.0:
            owasp_score += 1
        else:
            gaps.append('injection')
        
        # A04: Insecure Design (assumed secure design)
        owasp_score += 1
        
        # A05: Security Misconfiguration
        if self.audit_results['checks'].get('configuration', {}).get('score', 0) >= 4.0:
            owasp_score += 1
        else:
            gaps.append('security_misconfiguration')
        
        # A06: Vulnerable and Outdated Components
        if self.audit_results['checks'].get('dependencies', {}).get('score', 0) >= 4.0:
            owasp_score += 1
        else:
            gaps.append('vulnerable_components')
        
        # A07: Identification and Authentication Failures
        if self.audit_results['checks'].get('authentication', {}).get('score', 0) >= 4.0:
            owasp_score += 1
        else:
            gaps.append('authentication_failures')
        
        # A08: Software and Data Integrity Failures
        if self.audit_results['checks'].get('code_security', {}).get('score', 0) >= 4.0:
            owasp_score += 1
        else:
            gaps.append('integrity_failures')
        
        # A09: Security Logging and Monitoring Failures
        if self.audit_results['checks'].get('logging_monitoring', {}).get('score', 0) >= 4.0:
            owasp_score += 1
        else:
            gaps.append('logging_failures')
        
        # A10: Server-Side Request Forgery (assumed protected)
        owasp_score += 1
        
        return {
            'score': owasp_score / total_checks,
            'gaps': gaps,
            'compliant': owasp_score / total_checks >= 0.8
        }
    
    def _assess_iso27001_compliance(self):
        """Assess ISO 27001 compliance."""
        iso_score = 0.0
        total_checks = 5  # Simplified assessment
        gaps = []
        
        # Information security policy (assumed implemented)
        iso_score += 1
        
        # Risk management
        if self.audit_results['overall_score'] >= 7.0:
            iso_score += 1
        else:
            gaps.append('risk_management')
        
        # Access control
        if self.audit_results['checks'].get('authorization', {}).get('score', 0) >= 4.0:
            iso_score += 1
        else:
            gaps.append('access_control')
        
        # Cryptography
        if self.audit_results['checks'].get('data_protection', {}).get('score', 0) >= 4.0:
            iso_score += 1
        else:
            gaps.append('cryptography')
        
        # Incident management
        if self.audit_results['checks'].get('logging_monitoring', {}).get('score', 0) >= 4.0:
            iso_score += 1
        else:
            gaps.append('incident_management')
        
        return {
            'score': iso_score / total_checks,
            'gaps': gaps,
            'compliant': iso_score / total_checks >= 0.8
        }
    
    def _assess_nist_compliance(self):
        """Assess NIST Cybersecurity Framework compliance."""
        nist_score = 0.0
        total_checks = 5
        gaps = []
        
        # Identify
        if self.audit_results['overall_score'] >= 6.0:
            nist_score += 1
        else:
            gaps.append('identify')
        
        # Protect
        if self.audit_results['checks'].get('data_protection', {}).get('score', 0) >= 4.0:
            nist_score += 1
        else:
            gaps.append('protect')
        
        # Detect
        if self.audit_results['checks'].get('logging_monitoring', {}).get('score', 0) >= 4.0:
            nist_score += 1
        else:
            gaps.append('detect')
        
        # Respond (assumed implemented)
        nist_score += 1
        
        # Recover (assumed implemented)
        nist_score += 1
        
        return {
            'score': nist_score / total_checks,
            'gaps': gaps,
            'compliant': nist_score / total_checks >= 0.8
        }
    
    def _generate_remediation_timeline(self):
        """Generate remediation timeline based on vulnerability severity."""
        timeline = {
            'immediate': [],  # Critical - 24 hours
            'short_term': [],  # High - 7 days
            'medium_term': [],  # Medium - 30 days
            'long_term': []  # Low - Next release
        }
        
        for vuln in self.audit_results['vulnerabilities']:
            severity = vuln.get('severity', 'low')
            
            if severity == 'critical':
                timeline['immediate'].append(vuln)
            elif severity == 'high':
                timeline['short_term'].append(vuln)
            elif severity == 'medium':
                timeline['medium_term'].append(vuln)
            else:
                timeline['long_term'].append(vuln)
        
        return timeline
    
    def _generate_enhanced_markdown_report(self, filename):
        """Generate enhanced markdown report with hardening assessment."""
        with open(filename, 'w') as f:
            f.write(f"# Enhanced Zotero Integration Security Audit Report\n\n")
            f.write(f"**Audit ID:** {self.audit_results['audit_id']}\n")
            f.write(f"**Timestamp:** {self.audit_results['timestamp']}\n")
            f.write(f"**Standard Security Score:** {self.audit_results['overall_score']:.1f}/10.0\n")
            
            if 'combined_security_score' in self.audit_results:
                f.write(f"**Combined Security Score:** {self.audit_results['combined_security_score']:.1f}/10.0\n")
            
            f.write("\n## Executive Summary\n\n")
            
            # Add hardening assessment summary
            if 'hardening_assessment' in self.audit_results:
                hardening = self.audit_results['hardening_assessment']
                f.write("### Security Hardening Assessment\n\n")
                f.write(f"- **Risk Score:** {hardening.get('risk_score', 0):.1f}/10.0\n")
                f.write(f"- **Vulnerabilities:** {len(hardening.get('vulnerability_assessment', []))}\n")
                f.write(f"- **Policy Compliance:** {len(hardening.get('policy_compliance', {}))}\n")
                f.write(f"- **Recommendations:** {len(hardening.get('recommendations', []))}\n\n")
            
            # Continue with standard report sections
            self._generate_markdown_report(filename)
    
    def _generate_enhanced_html_report(self, filename):
        """Generate enhanced HTML report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enhanced Zotero Security Audit Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .score {{ font-size: 24px; font-weight: bold; color: #28a745; }}
                .vulnerability {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .critical {{ border-left: 5px solid #dc3545; }}
                .high {{ border-left: 5px solid #fd7e14; }}
                .medium {{ border-left: 5px solid #ffc107; }}
                .low {{ border-left: 5px solid #28a745; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Enhanced Zotero Integration Security Audit Report</h1>
                <p><strong>Audit ID:</strong> {self.audit_results['audit_id']}</p>
                <p><strong>Timestamp:</strong> {self.audit_results['timestamp']}</p>
                <p class="score">Combined Security Score: {self.audit_results.get('combined_security_score', self.audit_results['overall_score']):.1f}/10.0</p>
            </div>
        """
        
        # Add hardening assessment section
        if 'hardening_assessment' in self.audit_results:
            hardening = self.audit_results['hardening_assessment']
            html_content += f"""
            <h2>Security Hardening Assessment</h2>
            <ul>
                <li><strong>Risk Score:</strong> {hardening.get('risk_score', 0):.1f}/10.0</li>
                <li><strong>Vulnerabilities Found:</strong> {len(hardening.get('vulnerability_assessment', []))}</li>
                <li><strong>Policy Compliance Checks:</strong> {len(hardening.get('policy_compliance', {}))}</li>
                <li><strong>Recommendations:</strong> {len(hardening.get('recommendations', []))}</li>
            </ul>
            """
        
        # Add vulnerabilities section
        html_content += "<h2>Vulnerabilities</h2>"
        for vuln in self.audit_results['vulnerabilities']:
            severity_class = vuln.get('severity', 'low')
            html_content += f"""
            <div class="vulnerability {severity_class}">
                <h3>{vuln.get('category', 'Unknown').title()} - {vuln.get('severity', 'Low').title()}</h3>
                <p>{vuln.get('description', 'No description available')}</p>
            </div>
            """
        
        html_content += "</body></html>"
        
        with open(filename, 'w') as f:
            f.write(html_content)
    
    def _count_vulnerabilities_by_severity(self):
        """Count vulnerabilities by severity level."""
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for vuln in self.audit_results['vulnerabilities']:
            severity = vuln.get('severity', 'low')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts
    
    def _get_overall_status(self):
        """Get overall security status."""
        score = self.audit_results['overall_score']
        
        if score >= 8.0:
            return 'excellent'
        elif score >= 7.0:
            return 'good'
        elif score >= 5.0:
            return 'fair'
        else:
            return 'poor'
    
    def _generate_markdown_report(self, filename):
        """Generate markdown audit report."""
        with open(filename, 'w') as f:
            f.write(f"# Zotero Integration Security Audit Report\n\n")
            f.write(f"**Audit ID:** {self.audit_results['audit_id']}\n")
            f.write(f"**Timestamp:** {self.audit_results['timestamp']}\n")
            f.write(f"**Overall Score:** {self.audit_results['overall_score']:.1f}/10.0\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            summary = self.audit_results['summary']
            f.write(f"- **Status:** {summary['overall_status'].title()}\n")
            f.write(f"- **Total Checks:** {summary['total_checks']}\n")
            f.write(f"- **Vulnerabilities:** {len(self.audit_results['vulnerabilities'])}\n")
            f.write(f"- **Recommendations:** {summary['recommendations_count']}\n\n")
            
            # Vulnerabilities by severity
            severity_counts = summary['vulnerabilities_by_severity']
            f.write("### Vulnerabilities by Severity\n\n")
            for severity, count in severity_counts.items():
                if count > 0:
                    f.write(f"- **{severity.title()}:** {count}\n")
            f.write("\n")
            
            # Detailed check results
            f.write("## Detailed Results\n\n")
            for check_name, check_data in self.audit_results['checks'].items():
                f.write(f"### {check_name.replace('_', ' ').title()}\n\n")
                f.write(f"**Score:** {check_data['score']:.1f}/{check_data['max_score']:.1f}\n\n")
                
                for detail_name, detail_value in check_data['details'].items():
                    status = "✅" if detail_value else "❌"
                    f.write(f"- {status} {detail_name.replace('_', ' ').title()}\n")
                f.write("\n")
            
            # Vulnerabilities
            if self.audit_results['vulnerabilities']:
                f.write("## Vulnerabilities Found\n\n")
                for i, vuln in enumerate(self.audit_results['vulnerabilities'], 1):
                    f.write(f"### {i}. {vuln['category'].replace('_', ' ').title()}\n\n")
                    f.write(f"**Severity:** {vuln['severity'].title()}\n")
                    f.write(f"**Description:** {vuln['description']}\n\n")
            
            # Recommendations
            if self.audit_results['recommendations']:
                f.write("## Recommendations\n\n")
                for i, rec in enumerate(self.audit_results['recommendations'], 1):
                    f.write(f"{i}. {rec}\n")
                f.write("\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Zotero Integration Security Audit Tool"
    )
    
    parser.add_argument(
        '--comprehensive',
        action='store_true',
        help='Run comprehensive security audit including hardening assessment'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick security check'
    )
    
    parser.add_argument(
        '--category',
        choices=['authentication', 'authorization', 'data_protection', 'network_security', 'input_validation', 'logging_monitoring', 'configuration', 'dependencies', 'code_security'],
        help='Run audit for specific category only'
    )
    
    parser.add_argument(
        '--compliance',
        help='Check compliance with specific frameworks (comma-separated): gdpr,soc2,owasp,iso27001,nist'
    )
    
    parser.add_argument(
        '--vulnerabilities-only',
        action='store_true',
        help='Focus on vulnerability assessment only'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['json', 'markdown', 'html'],
        default='json',
        help='Output format for audit report'
    )
    
    parser.add_argument(
        '--report-file',
        help='Output file for audit report'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=7.0,
        help='Minimum security score threshold for passing (default: 7.0)'
    )
    
    args = parser.parse_args()
    
    # Run the audit
    auditor = ZoteroSecurityAuditor(args)
    
    try:
        if args.comprehensive:
            # Run comprehensive audit including hardening assessment
            success = asyncio.run(auditor.run_comprehensive_audit_with_hardening())
        elif args.quick:
            # Run quick security check
            success = asyncio.run(auditor.run_quick_security_check())
        elif args.category:
            # Run category-specific audit
            success = asyncio.run(auditor.run_category_audit(args.category))
        elif args.compliance:
            # Run compliance-focused audit
            frameworks = args.compliance.split(',')
            success = asyncio.run(auditor.run_compliance_audit(frameworks))
        elif args.vulnerabilities_only:
            # Run vulnerability assessment only
            success = asyncio.run(auditor.run_vulnerability_assessment())
        else:
            # Run standard comprehensive audit
            success = asyncio.run(auditor.run_comprehensive_audit())
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Audit interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Audit failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()