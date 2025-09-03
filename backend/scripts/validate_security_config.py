#!/usr/bin/env python3
"""
Security configuration validator for Zotero integration.
Validates security configuration against best practices and compliance requirements.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import argparse
import logging

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))


class SecurityConfigValidator:
    """Validates security configuration for Zotero integration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': [],
            'compliance_status': {}
        }
    
    def validate_config_file(self, config_path: str) -> Dict[str, Any]:
        """Validate security configuration file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            return self.validate_config(config)
            
        except FileNotFoundError:
            self.validation_results['valid'] = False
            self.validation_results['errors'].append(f"Configuration file not found: {config_path}")
            return self.validation_results
        
        except json.JSONDecodeError as e:
            self.validation_results['valid'] = False
            self.validation_results['errors'].append(f"Invalid JSON in configuration file: {str(e)}")
            return self.validation_results
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate security configuration dictionary."""
        # Reset validation results
        self.validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': [],
            'compliance_status': {}
        }
        
        # Validate required sections
        self._validate_required_sections(config)
        
        # Validate authentication policies
        if 'security_policies' in config and 'authentication' in config['security_policies']:
            self._validate_authentication_policy(config['security_policies']['authentication'])
        
        # Validate authorization policies
        if 'security_policies' in config and 'authorization' in config['security_policies']:
            self._validate_authorization_policy(config['security_policies']['authorization'])
        
        # Validate data protection policies
        if 'security_policies' in config and 'data_protection' in config['security_policies']:
            self._validate_data_protection_policy(config['security_policies']['data_protection'])
        
        # Validate network security policies
        if 'security_policies' in config and 'network_security' in config['security_policies']:
            self._validate_network_security_policy(config['security_policies']['network_security'])
        
        # Validate input validation policies
        if 'security_policies' in config and 'input_validation' in config['security_policies']:
            self._validate_input_validation_policy(config['security_policies']['input_validation'])
        
        # Validate logging and monitoring policies
        if 'security_policies' in config and 'logging_monitoring' in config['security_policies']:
            self._validate_logging_monitoring_policy(config['security_policies']['logging_monitoring'])
        
        # Validate compliance frameworks
        if 'compliance_frameworks' in config:
            self._validate_compliance_frameworks(config['compliance_frameworks'])
        
        # Validate security headers
        if 'security_headers' in config:
            self._validate_security_headers(config['security_headers'])
        
        # Validate environment-specific configurations
        if 'environment_specific' in config:
            self._validate_environment_configs(config['environment_specific'])
        
        return self.validation_results
    
    def _validate_required_sections(self, config: Dict[str, Any]) -> None:
        """Validate that required configuration sections are present."""
        required_sections = [
            'security_policies',
            'compliance_frameworks',
            'security_headers'
        ]
        
        for section in required_sections:
            if section not in config:
                self.validation_results['errors'].append(f"Missing required section: {section}")
                self.validation_results['valid'] = False
    
    def _validate_authentication_policy(self, auth_config: Dict[str, Any]) -> None:
        """Validate authentication policy configuration."""
        # OAuth2 validation
        if not auth_config.get('oauth2_enabled', False):
            self.validation_results['warnings'].append("OAuth2 is not enabled - consider enabling for better security")
        
        # Password policy validation
        password_min_length = auth_config.get('password_min_length', 0)
        if password_min_length < 12:
            self.validation_results['errors'].append("Password minimum length should be at least 12 characters")
            self.validation_results['valid'] = False
        
        # Password complexity validation
        complexity = auth_config.get('password_complexity', {})
        required_complexity = ['require_uppercase', 'require_lowercase', 'require_numbers', 'require_special_chars']
        
        for requirement in required_complexity:
            if not complexity.get(requirement, False):
                self.validation_results['warnings'].append(f"Password complexity requirement missing: {requirement}")
        
        # Account lockout validation
        lockout = auth_config.get('account_lockout', {})
        max_attempts = lockout.get('max_attempts', 0)
        if max_attempts == 0 or max_attempts > 10:
            self.validation_results['warnings'].append("Account lockout max attempts should be between 1 and 10")
        
        lockout_duration = lockout.get('lockout_duration', 0)
        if lockout_duration < 300:  # 5 minutes
            self.validation_results['warnings'].append("Account lockout duration should be at least 5 minutes (300 seconds)")
        
        # Session management validation
        session = auth_config.get('session_management', {})
        max_session_duration = session.get('max_session_duration', 0)
        if max_session_duration > 3600:  # 1 hour
            self.validation_results['warnings'].append("Maximum session duration should not exceed 1 hour for security")
        
        if not session.get('secure_cookies', False):
            self.validation_results['errors'].append("Secure cookies must be enabled")
            self.validation_results['valid'] = False
        
        if not session.get('httponly_cookies', False):
            self.validation_results['errors'].append("HttpOnly cookies must be enabled")
            self.validation_results['valid'] = False
        
        # MFA validation
        if not auth_config.get('mfa_required_for_admin', False):
            self.validation_results['recommendations'].append("Consider requiring MFA for admin accounts")
    
    def _validate_authorization_policy(self, authz_config: Dict[str, Any]) -> None:
        """Validate authorization policy configuration."""
        if not authz_config.get('rbac_enabled', False):
            self.validation_results['errors'].append("Role-based access control (RBAC) must be enabled")
            self.validation_results['valid'] = False
        
        if not authz_config.get('resource_level_auth', False):
            self.validation_results['warnings'].append("Resource-level authorization should be enabled")
        
        if not authz_config.get('admin_endpoints_protected', False):
            self.validation_results['errors'].append("Admin endpoints must be protected")
            self.validation_results['valid'] = False
        
        # CORS validation
        cors = authz_config.get('cors_configuration', {})
        allowed_origins = cors.get('allowed_origins', [])
        
        if '*' in allowed_origins:
            self.validation_results['errors'].append("CORS should not allow all origins (*) in production")
            self.validation_results['valid'] = False
        
        if not cors.get('allow_credentials', False):
            self.validation_results['warnings'].append("CORS credentials should be properly configured")
    
    def _validate_data_protection_policy(self, data_config: Dict[str, Any]) -> None:
        """Validate data protection policy configuration."""
        if not data_config.get('encryption_at_rest', False):
            self.validation_results['errors'].append("Encryption at rest must be enabled")
            self.validation_results['valid'] = False
        
        if not data_config.get('encryption_in_transit', False):
            self.validation_results['errors'].append("Encryption in transit must be enabled")
            self.validation_results['valid'] = False
        
        # Key management validation
        key_mgmt = data_config.get('key_management', {})
        key_rotation_days = key_mgmt.get('key_rotation_days', 0)
        if key_rotation_days == 0 or key_rotation_days > 365:
            self.validation_results['warnings'].append("Key rotation should be configured for at least annually")
        
        # Data retention validation
        retention = data_config.get('data_retention', {})
        if not retention:
            self.validation_results['warnings'].append("Data retention policies should be configured")
        
        # Privacy controls validation
        privacy = data_config.get('privacy_controls', {})
        required_privacy_controls = ['data_minimization', 'consent_management', 'right_to_erasure']
        
        for control in required_privacy_controls:
            if not privacy.get(control, False):
                self.validation_results['warnings'].append(f"Privacy control should be enabled: {control}")
    
    def _validate_network_security_policy(self, network_config: Dict[str, Any]) -> None:
        """Validate network security policy configuration."""
        # TLS validation
        tls_version = network_config.get('tls_version', '')
        if tls_version not in ['1.2', '1.3']:
            self.validation_results['errors'].append("TLS version should be 1.2 or 1.3")
            self.validation_results['valid'] = False
        
        if not network_config.get('hsts_enabled', False):
            self.validation_results['warnings'].append("HTTP Strict Transport Security (HSTS) should be enabled")
        
        # Rate limiting validation
        rate_limiting = network_config.get('rate_limiting', {})
        if not rate_limiting.get('enabled', False):
            self.validation_results['warnings'].append("Rate limiting should be enabled")
        
        default_limit = rate_limiting.get('default_limit', 0)
        if default_limit > 10000:
            self.validation_results['warnings'].append("Default rate limit seems high - consider lowering for better security")
        
        # DDoS protection validation
        ddos = network_config.get('ddos_protection', {})
        if not ddos.get('enabled', False):
            self.validation_results['recommendations'].append("Consider enabling DDoS protection")
    
    def _validate_input_validation_policy(self, input_config: Dict[str, Any]) -> None:
        """Validate input validation policy configuration."""
        if not input_config.get('enabled', False):
            self.validation_results['errors'].append("Input validation must be enabled")
            self.validation_results['valid'] = False
        
        max_input_length = input_config.get('max_input_length', 0)
        if max_input_length == 0 or max_input_length > 100000:
            self.validation_results['warnings'].append("Maximum input length should be reasonable (e.g., 10,000 characters)")
        
        max_file_size = input_config.get('max_file_size', 0)
        if max_file_size > 104857600:  # 100MB
            self.validation_results['warnings'].append("Maximum file size should not exceed 100MB for security")
        
        allowed_file_types = input_config.get('allowed_file_types', [])
        if not allowed_file_types:
            self.validation_results['warnings'].append("Allowed file types should be explicitly defined")
        
        if not input_config.get('suspicious_pattern_detection', False):
            self.validation_results['recommendations'].append("Consider enabling suspicious pattern detection")
    
    def _validate_logging_monitoring_policy(self, logging_config: Dict[str, Any]) -> None:
        """Validate logging and monitoring policy configuration."""
        if not logging_config.get('security_logging', False):
            self.validation_results['errors'].append("Security logging must be enabled")
            self.validation_results['valid'] = False
        
        if not logging_config.get('audit_logging', False):
            self.validation_results['warnings'].append("Audit logging should be enabled")
        
        log_retention_days = logging_config.get('log_retention_days', 0)
        if log_retention_days < 30:
            self.validation_results['warnings'].append("Log retention should be at least 30 days")
        
        # Alerting validation
        alerting = logging_config.get('alerting', {})
        if not alerting.get('enabled', False):
            self.validation_results['warnings'].append("Security alerting should be enabled")
        
        channels = alerting.get('channels', [])
        if not channels:
            self.validation_results['warnings'].append("Alert notification channels should be configured")
    
    def _validate_compliance_frameworks(self, compliance_config: Dict[str, Any]) -> None:
        """Validate compliance framework configurations."""
        enabled_frameworks = []
        
        for framework, config in compliance_config.items():
            if config.get('enabled', False):
                enabled_frameworks.append(framework)
                
                # Validate framework-specific requirements
                requirements = config.get('requirements', {})
                if not requirements:
                    self.validation_results['warnings'].append(f"No requirements defined for {framework} compliance")
                
                # Framework-specific validations
                if framework == 'gdpr':
                    self._validate_gdpr_compliance(requirements)
                elif framework == 'soc2':
                    self._validate_soc2_compliance(requirements)
                elif framework == 'owasp':
                    self._validate_owasp_compliance(requirements)
        
        if not enabled_frameworks:
            self.validation_results['recommendations'].append("Consider enabling at least one compliance framework")
        
        self.validation_results['compliance_status'] = {
            'enabled_frameworks': enabled_frameworks,
            'total_frameworks': len(compliance_config)
        }
    
    def _validate_gdpr_compliance(self, requirements: Dict[str, Any]) -> None:
        """Validate GDPR compliance requirements."""
        critical_requirements = ['data_minimization', 'consent_management', 'right_to_erasure', 'privacy_by_design']
        
        for requirement in critical_requirements:
            if not requirements.get(requirement, False):
                self.validation_results['warnings'].append(f"GDPR requirement not enabled: {requirement}")
    
    def _validate_soc2_compliance(self, requirements: Dict[str, Any]) -> None:
        """Validate SOC 2 compliance requirements."""
        critical_requirements = ['access_controls', 'system_monitoring', 'incident_response']
        
        for requirement in critical_requirements:
            if not requirements.get(requirement, False):
                self.validation_results['warnings'].append(f"SOC 2 requirement not enabled: {requirement}")
    
    def _validate_owasp_compliance(self, requirements: Dict[str, Any]) -> None:
        """Validate OWASP compliance requirements."""
        critical_requirements = ['injection_prevention', 'broken_authentication', 'broken_access_control']
        
        for requirement in critical_requirements:
            if not requirements.get(requirement, False):
                self.validation_results['warnings'].append(f"OWASP requirement not enabled: {requirement}")
    
    def _validate_security_headers(self, headers_config: Dict[str, Any]) -> None:
        """Validate security headers configuration."""
        critical_headers = ['strict_transport_security', 'content_security_policy', 'x_content_type_options']
        
        for header in critical_headers:
            if header not in headers_config or not headers_config[header].get('enabled', False):
                self.validation_results['warnings'].append(f"Security header should be enabled: {header}")
        
        # CSP validation
        csp = headers_config.get('content_security_policy', {})
        if csp.get('enabled', False):
            policy = csp.get('policy', '')
            if 'unsafe-eval' in policy:
                self.validation_results['warnings'].append("CSP policy contains 'unsafe-eval' - consider removing for better security")
            if "'unsafe-inline'" in policy and 'script-src' in policy:
                self.validation_results['warnings'].append("CSP policy allows unsafe inline scripts - consider using nonces or hashes")
    
    def _validate_environment_configs(self, env_configs: Dict[str, Any]) -> None:
        """Validate environment-specific configurations."""
        # Production environment validation
        prod_config = env_configs.get('production', {})
        if prod_config.get('debug_mode', False):
            self.validation_results['errors'].append("Debug mode must be disabled in production")
            self.validation_results['valid'] = False
        
        if prod_config.get('detailed_errors', False):
            self.validation_results['errors'].append("Detailed errors must be disabled in production")
            self.validation_results['valid'] = False
        
        security_level = prod_config.get('security_level', '')
        if security_level != 'maximum':
            self.validation_results['warnings'].append("Production security level should be set to 'maximum'")
        
        # Development environment validation
        dev_config = env_configs.get('development', {})
        if not dev_config.get('debug_mode', False):
            self.validation_results['recommendations'].append("Consider enabling debug mode in development for easier troubleshooting")
    
    def generate_report(self, output_format: str = 'json') -> str:
        """Generate validation report."""
        if output_format == 'json':
            return json.dumps(self.validation_results, indent=2)
        
        elif output_format == 'markdown':
            return self._generate_markdown_report()
        
        elif output_format == 'text':
            return self._generate_text_report()
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_markdown_report(self) -> str:
        """Generate markdown validation report."""
        report = "# Security Configuration Validation Report\n\n"
        
        # Overall status
        status = "✅ VALID" if self.validation_results['valid'] else "❌ INVALID"
        report += f"**Overall Status:** {status}\n\n"
        
        # Errors
        if self.validation_results['errors']:
            report += "## ❌ Errors\n\n"
            for error in self.validation_results['errors']:
                report += f"- {error}\n"
            report += "\n"
        
        # Warnings
        if self.validation_results['warnings']:
            report += "## ⚠️ Warnings\n\n"
            for warning in self.validation_results['warnings']:
                report += f"- {warning}\n"
            report += "\n"
        
        # Recommendations
        if self.validation_results['recommendations']:
            report += "## 💡 Recommendations\n\n"
            for recommendation in self.validation_results['recommendations']:
                report += f"- {recommendation}\n"
            report += "\n"
        
        # Compliance status
        if self.validation_results['compliance_status']:
            report += "## 📋 Compliance Status\n\n"
            compliance = self.validation_results['compliance_status']
            report += f"- **Enabled Frameworks:** {', '.join(compliance.get('enabled_frameworks', []))}\n"
            report += f"- **Total Frameworks:** {compliance.get('total_frameworks', 0)}\n"
        
        return report
    
    def _generate_text_report(self) -> str:
        """Generate text validation report."""
        report = "Security Configuration Validation Report\n"
        report += "=" * 50 + "\n\n"
        
        # Overall status
        status = "VALID" if self.validation_results['valid'] else "INVALID"
        report += f"Overall Status: {status}\n\n"
        
        # Summary
        report += f"Errors: {len(self.validation_results['errors'])}\n"
        report += f"Warnings: {len(self.validation_results['warnings'])}\n"
        report += f"Recommendations: {len(self.validation_results['recommendations'])}\n\n"
        
        # Details
        if self.validation_results['errors']:
            report += "ERRORS:\n"
            for i, error in enumerate(self.validation_results['errors'], 1):
                report += f"{i}. {error}\n"
            report += "\n"
        
        if self.validation_results['warnings']:
            report += "WARNINGS:\n"
            for i, warning in enumerate(self.validation_results['warnings'], 1):
                report += f"{i}. {warning}\n"
            report += "\n"
        
        if self.validation_results['recommendations']:
            report += "RECOMMENDATIONS:\n"
            for i, recommendation in enumerate(self.validation_results['recommendations'], 1):
                report += f"{i}. {recommendation}\n"
            report += "\n"
        
        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Zotero integration security configuration"
    )
    
    parser.add_argument(
        'config_file',
        help='Path to security configuration file'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['json', 'markdown', 'text'],
        default='json',
        help='Output format for validation report'
    )
    
    parser.add_argument(
        '--output-file',
        help='Output file for validation report'
    )
    
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    
    # Validate configuration
    validator = SecurityConfigValidator()
    results = validator.validate_config_file(args.config_file)
    
    # Generate report
    report = validator.generate_report(args.output_format)
    
    # Output report
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(report)
        print(f"Validation report written to: {args.output_file}")
    else:
        print(report)
    
    # Determine exit code
    has_errors = len(results['errors']) > 0
    has_warnings = len(results['warnings']) > 0
    
    if has_errors:
        sys.exit(1)
    elif args.strict and has_warnings:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()