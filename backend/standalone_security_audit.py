#!/usr/bin/env python3
"""
Standalone security audit script for Zotero integration.
This script performs security checks without requiring the full application stack.
"""
import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
import logging


class StandaloneSecurityAuditor:
    """Standalone security auditor for Zotero integration."""
    
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
    
    def run_security_audit(self):
        """Run comprehensive security audit."""
        print("🔒 Starting Standalone Zotero Security Audit")
        print(f"Audit ID: {self.audit_results['audit_id']}")
        print("=" * 60)
        
        # Run security checks
        self._check_file_permissions()
        self._check_configuration_files()
        self._check_dependency_vulnerabilities()
        self._check_code_security()
        self._check_environment_variables()
        self._check_documentation()
        
        # Calculate overall score
        self._calculate_overall_score()
        
        # Generate report
        report_file = self._generate_audit_report()
        
        print("\n" + "=" * 60)
        print("🔒 Standalone Security Audit Complete")
        print(f"Overall Security Score: {self.audit_results['overall_score']:.1f}/10.0")
        print(f"Vulnerabilities Found: {len(self.audit_results['vulnerabilities'])}")
        print(f"Recommendations: {len(self.audit_results['recommendations'])}")
        print(f"Detailed Report: {report_file}")
        
        return self.audit_results['overall_score'] >= 7.0
    
    def _check_file_permissions(self):
        """Check file permissions for security issues."""
        print("📁 Checking File Permissions...")
        
        score = 5.0
        issues = []
        
        # Check for world-writable files
        try:
            result = subprocess.run(
                ['find', '.', '-type', 'f', '-perm', '0002'],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.stdout.strip():
                world_writable = result.stdout.strip().split('\n')
                score -= min(len(world_writable) * 0.5, 2.0)
                issues.append(f"Found {len(world_writable)} world-writable files")
                self.audit_results['vulnerabilities'].append({
                    'category': 'file_permissions',
                    'severity': 'medium',
                    'description': f'World-writable files found: {", ".join(world_writable[:5])}'
                })
        
        except Exception as e:
            self.logger.warning(f"Could not check file permissions: {e}")
        
        # Check for executable config files
        config_files = ['.env', 'config.json', '*.conf', '*.ini']
        for pattern in config_files:
            try:
                result = subprocess.run(
                    ['find', '.', '-name', pattern, '-executable'],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent
                )
                
                if result.stdout.strip():
                    executable_configs = result.stdout.strip().split('\n')
                    score -= min(len(executable_configs) * 0.3, 1.0)
                    issues.append(f"Executable config files: {len(executable_configs)}")
            
            except Exception:
                continue
        
        self.audit_results['checks']['file_permissions'] = {
            'score': max(score, 0.0),
            'max_score': 5.0,
            'issues': issues
        }
        
        if score >= 4.0:
            self.logger.info("✓ File permissions check passed")
        else:
            self.logger.warning(f"⚠ File permissions issues found: {issues}")
    
    def _check_configuration_files(self):
        """Check configuration files for security issues."""
        print("⚙️ Checking Configuration Files...")
        
        score = 5.0
        issues = []
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        config_files = ['.env', '.env.example', 'config.json', 'docker-compose.yml']
        
        for config_file in config_files:
            file_path = Path(__file__).parent / config_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Check for hardcoded secrets
                    import re
                    for pattern in secret_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            score -= 1.0
                            issues.append(f"Potential hardcoded secret in {config_file}")
                            self.audit_results['vulnerabilities'].append({
                                'category': 'configuration',
                                'severity': 'high',
                                'description': f'Potential hardcoded secret in {config_file}'
                            })
                            break
                    
                    # Check for debug mode in production configs
                    if 'production' in config_file.lower() or 'prod' in config_file.lower():
                        if re.search(r'debug\s*=\s*true', content, re.IGNORECASE):
                            score -= 0.5
                            issues.append(f"Debug mode enabled in {config_file}")
                
                except Exception as e:
                    self.logger.warning(f"Could not read {config_file}: {e}")
        
        # Check for missing security configuration
        security_config_path = Path(__file__).parent / 'config' / 'zotero_security_config.json'
        if not security_config_path.exists():
            score -= 1.0
            issues.append("Security configuration file missing")
            self.audit_results['recommendations'].append(
                "Create comprehensive security configuration file"
            )
        else:
            self.logger.info("✓ Security configuration file found")
        
        self.audit_results['checks']['configuration'] = {
            'score': max(score, 0.0),
            'max_score': 5.0,
            'issues': issues
        }
        
        if score >= 4.0:
            self.logger.info("✓ Configuration files check passed")
        else:
            self.logger.warning(f"⚠ Configuration issues found: {issues}")
    
    def _check_dependency_vulnerabilities(self):
        """Check for dependency vulnerabilities."""
        print("📦 Checking Dependency Vulnerabilities...")
        
        score = 5.0
        vulnerabilities_found = 0
        
        # Check Python dependencies with safety
        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode != 0 and result.stdout:
                try:
                    safety_output = json.loads(result.stdout)
                    vulnerabilities_found = len(safety_output)
                    score -= min(vulnerabilities_found * 0.3, 3.0)
                    
                    self.audit_results['vulnerabilities'].append({
                        'category': 'dependencies',
                        'severity': 'high' if vulnerabilities_found > 5 else 'medium',
                        'description': f'{vulnerabilities_found} known vulnerabilities in Python dependencies'
                    })
                    
                    self.logger.warning(f"⚠ Found {vulnerabilities_found} dependency vulnerabilities")
                
                except json.JSONDecodeError:
                    self.logger.warning("Could not parse safety check output")
            else:
                self.logger.info("✓ No known vulnerabilities in Python dependencies")
        
        except FileNotFoundError:
            score -= 1.0
            self.audit_results['recommendations'].append(
                'Install safety tool for dependency vulnerability checking: pip install safety'
            )
            self.logger.warning("⚠ Safety tool not available for dependency checking")
        
        # Check for outdated packages
        try:
            result = subprocess.run(
                ['pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                outdated_packages = json.loads(result.stdout)
                if len(outdated_packages) > 20:
                    score -= 0.5
                    self.audit_results['recommendations'].append(
                        f'{len(outdated_packages)} packages are outdated - consider updating'
                    )
                    self.logger.warning(f"⚠ {len(outdated_packages)} outdated packages found")
                else:
                    self.logger.info("✓ Dependencies are reasonably up to date")
        
        except Exception as e:
            self.logger.warning(f"Could not check outdated packages: {e}")
        
        self.audit_results['checks']['dependencies'] = {
            'score': max(score, 0.0),
            'max_score': 5.0,
            'vulnerabilities_found': vulnerabilities_found
        }
    
    def _check_code_security(self):
        """Check code security using static analysis."""
        print("🔍 Checking Code Security...")
        
        score = 5.0
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
                    else:
                        self.logger.warning(f"⚠ Found {issues_found} security issues in code")
                
                except json.JSONDecodeError:
                    self.logger.warning("Could not parse bandit output")
        
        except FileNotFoundError:
            score -= 1.0
            self.audit_results['recommendations'].append(
                'Install bandit for code security analysis: pip install bandit'
            )
            self.logger.warning("⚠ Bandit tool not available for code security analysis")
        
        self.audit_results['checks']['code_security'] = {
            'score': max(score, 0.0),
            'max_score': 5.0,
            'issues_found': issues_found
        }
    
    def _check_environment_variables(self):
        """Check environment variables for security issues."""
        print("🌍 Checking Environment Variables...")
        
        score = 5.0
        issues = []
        
        # Check for required security environment variables
        required_env_vars = [
            'SECRET_KEY',
            'DATABASE_PASSWORD',
            'ZOTERO_CLIENT_SECRET'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            score -= len(missing_vars) * 0.5
            issues.append(f"Missing environment variables: {', '.join(missing_vars)}")
            self.audit_results['recommendations'].append(
                f"Set required environment variables: {', '.join(missing_vars)}"
            )
        
        # Check for weak secrets
        secret_key = os.getenv('SECRET_KEY', '')
        if secret_key and len(secret_key) < 32:
            score -= 1.0
            issues.append("SECRET_KEY is too short (should be at least 32 characters)")
            self.audit_results['vulnerabilities'].append({
                'category': 'environment',
                'severity': 'high',
                'description': 'SECRET_KEY is too short for secure operation'
            })
        
        # Check for debug mode in production
        debug_mode = os.getenv('DEBUG', 'false').lower()
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        
        if debug_mode == 'true' and environment == 'production':
            score -= 2.0
            issues.append("Debug mode enabled in production environment")
            self.audit_results['vulnerabilities'].append({
                'category': 'environment',
                'severity': 'high',
                'description': 'Debug mode is enabled in production environment'
            })
        
        self.audit_results['checks']['environment'] = {
            'score': max(score, 0.0),
            'max_score': 5.0,
            'issues': issues
        }
        
        if score >= 4.0:
            self.logger.info("✓ Environment variables check passed")
        else:
            self.logger.warning(f"⚠ Environment issues found: {issues}")
    
    def _check_documentation(self):
        """Check for security documentation."""
        print("📚 Checking Security Documentation...")
        
        score = 5.0
        missing_docs = []
        
        # Check for required security documentation
        required_docs = [
            'docs/ZOTERO_SECURITY_GUIDELINES.md',
            'docs/ZOTERO_SECURITY_AUDIT_PROCEDURES.md',
            'config/zotero_security_config.json'
        ]
        
        for doc_path in required_docs:
            full_path = Path(__file__).parent / doc_path
            if not full_path.exists():
                missing_docs.append(doc_path)
                score -= 1.0
        
        if missing_docs:
            self.audit_results['recommendations'].append(
                f"Create missing security documentation: {', '.join(missing_docs)}"
            )
            self.logger.warning(f"⚠ Missing security documentation: {missing_docs}")
        else:
            self.logger.info("✓ Security documentation is complete")
        
        self.audit_results['checks']['documentation'] = {
            'score': max(score, 0.0),
            'max_score': 5.0,
            'missing_docs': missing_docs
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
        """Generate audit report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.args.output_format == 'json':
            report_file = f"standalone_security_audit_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(self.audit_results, f, indent=2, default=str)
        
        elif self.args.output_format == 'markdown':
            report_file = f"standalone_security_audit_{timestamp}.md"
            self._generate_markdown_report(report_file)
        
        else:  # text
            report_file = f"standalone_security_audit_{timestamp}.txt"
            self._generate_text_report(report_file)
        
        return report_file
    
    def _generate_markdown_report(self, filename):
        """Generate markdown audit report."""
        with open(filename, 'w') as f:
            f.write(f"# Standalone Zotero Security Audit Report\n\n")
            f.write(f"**Audit ID:** {self.audit_results['audit_id']}\n")
            f.write(f"**Timestamp:** {self.audit_results['timestamp']}\n")
            f.write(f"**Overall Score:** {self.audit_results['overall_score']:.1f}/10.0\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Vulnerabilities:** {len(self.audit_results['vulnerabilities'])}\n")
            f.write(f"- **Recommendations:** {len(self.audit_results['recommendations'])}\n\n")
            
            # Detailed results
            f.write("## Detailed Results\n\n")
            for check_name, check_data in self.audit_results['checks'].items():
                f.write(f"### {check_name.replace('_', ' ').title()}\n\n")
                f.write(f"**Score:** {check_data['score']:.1f}/{check_data['max_score']:.1f}\n\n")
                
                if 'issues' in check_data and check_data['issues']:
                    f.write("**Issues:**\n")
                    for issue in check_data['issues']:
                        f.write(f"- {issue}\n")
                    f.write("\n")
            
            # Vulnerabilities
            if self.audit_results['vulnerabilities']:
                f.write("## Vulnerabilities\n\n")
                for i, vuln in enumerate(self.audit_results['vulnerabilities'], 1):
                    f.write(f"### {i}. {vuln['category'].replace('_', ' ').title()}\n\n")
                    f.write(f"**Severity:** {vuln['severity'].title()}\n")
                    f.write(f"**Description:** {vuln['description']}\n\n")
            
            # Recommendations
            if self.audit_results['recommendations']:
                f.write("## Recommendations\n\n")
                for i, rec in enumerate(self.audit_results['recommendations'], 1):
                    f.write(f"{i}. {rec}\n")
    
    def _generate_text_report(self, filename):
        """Generate text audit report."""
        with open(filename, 'w') as f:
            f.write("Standalone Zotero Security Audit Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Audit ID: {self.audit_results['audit_id']}\n")
            f.write(f"Timestamp: {self.audit_results['timestamp']}\n")
            f.write(f"Overall Score: {self.audit_results['overall_score']:.1f}/10.0\n\n")
            
            f.write("SUMMARY:\n")
            f.write(f"Vulnerabilities: {len(self.audit_results['vulnerabilities'])}\n")
            f.write(f"Recommendations: {len(self.audit_results['recommendations'])}\n\n")
            
            f.write("DETAILED RESULTS:\n")
            for check_name, check_data in self.audit_results['checks'].items():
                f.write(f"\n{check_name.replace('_', ' ').title()}:\n")
                f.write(f"Score: {check_data['score']:.1f}/{check_data['max_score']:.1f}\n")
                
                if 'issues' in check_data and check_data['issues']:
                    f.write("Issues:\n")
                    for issue in check_data['issues']:
                        f.write(f"  - {issue}\n")
            
            if self.audit_results['vulnerabilities']:
                f.write("\nVULNERABILITIES:\n")
                for i, vuln in enumerate(self.audit_results['vulnerabilities'], 1):
                    f.write(f"{i}. {vuln['category']} ({vuln['severity']}): {vuln['description']}\n")
            
            if self.audit_results['recommendations']:
                f.write("\nRECOMMENDATIONS:\n")
                for i, rec in enumerate(self.audit_results['recommendations'], 1):
                    f.write(f"{i}. {rec}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Standalone Zotero Integration Security Audit"
    )
    
    parser.add_argument(
        '--output-format',
        choices=['json', 'markdown', 'text'],
        default='text',
        help='Output format for audit report'
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
    auditor = StandaloneSecurityAuditor(args)
    
    try:
        success = auditor.run_security_audit()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Audit interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Audit failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()