#!/usr/bin/env python3
"""
Automated Fix Integration System
Integrates the automated fix engine with the existing analysis infrastructure
to provide seamless fix application based on detected issues.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import subprocess

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automated_fix_engine import AutoFixEngine, FixType, FixResult
from issue_reporting_system import ComprehensiveIssueReportingSystem, IssueType, IssueSeverity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class FixRecommendation:
    """Recommendation for applying a fix"""
    issue_id: str
    fix_type: FixType
    confidence: float  # 0.0 to 1.0
    risk_level: str    # "safe", "low", "medium", "high"
    description: str
    auto_applicable: bool
    requires_review: bool

class AutomatedFixIntegration:
    """Integration system for automated fixes"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.fix_engine = AutoFixEngine(str(self.project_root))
        self.issue_reporter = ComprehensiveIssueReportingSystem(str(self.project_root))
        
        # Load configuration
        self.config = self._load_configuration()
        
        # Track applied fixes
        self.applied_fixes: List[FixResult] = []
        self.fix_recommendations: List[FixRecommendation] = []
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration for automated fixes"""
        config_file = self.project_root / "scripts" / "automated_fix_config.json"
        
        default_config = {
            "auto_apply_safe_fixes": True,
            "require_confirmation_for_medium_risk": True,
            "skip_high_risk_fixes": True,
            "create_backups": True,
            "max_fixes_per_run": 50,
            "fix_types_enabled": {
                "code_formatting": True,
                "dependency_updates": True,
                "configuration_fixes": True,
                "ubuntu_optimizations": True
            },
            "issue_type_mapping": {
                "syntax_error": "code_formatting",
                "style_violation": "code_formatting",
                "outdated_dependency": "dependency_updates",
                "configuration_error": "configuration_fixes",
                "ubuntu_compatibility": "ubuntu_optimizations"
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}, using defaults")
        
        return default_config
    
    def analyze_and_fix(self, analysis_report_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze issues and apply automated fixes"""
        logger.info("Starting integrated analysis and fix process...")
        
        # Step 1: Run comprehensive analysis if no report provided
        if analysis_report_path is None:
            logger.info("Running comprehensive analysis...")
            analysis_report = self._run_comprehensive_analysis()
        else:
            logger.info(f"Loading analysis report from {analysis_report_path}")
            with open(analysis_report_path, 'r') as f:
                analysis_report = json.load(f)
        
        # Step 2: Generate fix recommendations
        logger.info("Generating fix recommendations...")
        self.fix_recommendations = self._generate_fix_recommendations(analysis_report)
        
        # Step 3: Apply automated fixes
        logger.info("Applying automated fixes...")
        self.applied_fixes = self._apply_recommended_fixes()
        
        # Step 4: Generate comprehensive report
        logger.info("Generating fix report...")
        fix_report = self._generate_integrated_report(analysis_report)
        
        return fix_report
    
    def _run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive codebase analysis"""
        try:
            # Run the comprehensive analysis script
            result = subprocess.run([
                sys.executable, 
                str(self.project_root / "scripts" / "run_comprehensive_issue_reporting.py"),
                "--output", "temp_analysis_report.json"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                with open(self.project_root / "temp_analysis_report.json", 'r') as f:
                    return json.load(f)
            else:
                logger.error(f"Analysis failed: {result.stderr}")
                return {"issues": [], "summary": {"total_issues": 0}}
        
        except Exception as e:
            logger.error(f"Failed to run analysis: {e}")
            return {"issues": [], "summary": {"total_issues": 0}}
    
    def _generate_fix_recommendations(self, analysis_report: Dict[str, Any]) -> List[FixRecommendation]:
        """Generate fix recommendations based on analysis results"""
        recommendations = []
        
        issues = analysis_report.get("issues", [])
        
        for issue in issues:
            recommendation = self._create_fix_recommendation(issue)
            if recommendation:
                recommendations.append(recommendation)
        
        # Sort by confidence and risk level
        recommendations.sort(key=lambda x: (x.confidence, x.risk_level == "safe"), reverse=True)
        
        return recommendations
    
    def _create_fix_recommendation(self, issue: Dict[str, Any]) -> Optional[FixRecommendation]:
        """Create fix recommendation for a specific issue"""
        issue_type = issue.get("type", "").lower()
        issue_severity = issue.get("severity", "").lower()
        
        # Map issue type to fix type
        fix_type_mapping = self.config.get("issue_type_mapping", {})
        fix_type_str = fix_type_mapping.get(issue_type)
        
        if not fix_type_str:
            return None
        
        try:
            fix_type = FixType(fix_type_str)
        except ValueError:
            return None
        
        # Determine confidence and risk level
        confidence, risk_level = self._calculate_fix_confidence_and_risk(issue)
        
        # Check if fix type is enabled
        if not self.config.get("fix_types_enabled", {}).get(fix_type_str, False):
            return None
        
        return FixRecommendation(
            issue_id=issue.get("id", "unknown"),
            fix_type=fix_type,
            confidence=confidence,
            risk_level=risk_level,
            description=f"Fix {issue_type}: {issue.get('description', '')}",
            auto_applicable=self._is_auto_applicable(fix_type, risk_level),
            requires_review=self._requires_review(risk_level)
        )
    
    def _calculate_fix_confidence_and_risk(self, issue: Dict[str, Any]) -> tuple[float, str]:
        """Calculate confidence and risk level for a fix"""
        issue_type = issue.get("type", "").lower()
        issue_severity = issue.get("severity", "").lower()
        
        # Base confidence by issue type
        confidence_map = {
            "syntax_error": 0.9,
            "style_violation": 0.95,
            "formatting_issue": 0.98,
            "outdated_dependency": 0.7,
            "configuration_error": 0.8,
            "ubuntu_compatibility": 0.75,
            "security_vulnerability": 0.6
        }
        
        confidence = confidence_map.get(issue_type, 0.5)
        
        # Adjust confidence based on severity
        if issue_severity == "critical":
            confidence *= 0.8  # Lower confidence for critical issues
        elif issue_severity == "high":
            confidence *= 0.9
        elif issue_severity == "low":
            confidence *= 1.1
        
        # Determine risk level
        if issue_type in ["formatting_issue", "style_violation"] and issue_severity in ["low", "medium"]:
            risk_level = "safe"
        elif issue_type in ["syntax_error", "configuration_error"] and issue_severity != "critical":
            risk_level = "low"
        elif issue_type in ["outdated_dependency", "ubuntu_compatibility"]:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return min(confidence, 1.0), risk_level
    
    def _is_auto_applicable(self, fix_type: FixType, risk_level: str) -> bool:
        """Determine if fix can be applied automatically"""
        if risk_level == "safe" and self.config.get("auto_apply_safe_fixes", True):
            return True
        
        if risk_level == "low" and not self.config.get("require_confirmation_for_low_risk", False):
            return True
        
        return False
    
    def _requires_review(self, risk_level: str) -> bool:
        """Determine if fix requires manual review"""
        return risk_level in ["medium", "high"]
    
    def _apply_recommended_fixes(self) -> List[FixResult]:
        """Apply recommended fixes based on configuration"""
        applied_fixes = []
        fixes_applied = 0
        max_fixes = self.config.get("max_fixes_per_run", 50)
        
        for recommendation in self.fix_recommendations:
            if fixes_applied >= max_fixes:
                logger.info(f"Reached maximum fixes per run ({max_fixes})")
                break
            
            if not recommendation.auto_applicable:
                logger.info(f"Skipping fix {recommendation.issue_id} - requires manual intervention")
                continue
            
            if recommendation.risk_level == "high" and self.config.get("skip_high_risk_fixes", True):
                logger.info(f"Skipping high-risk fix {recommendation.issue_id}")
                continue
            
            # Apply the fix
            fix_result = self._apply_single_fix(recommendation)
            if fix_result:
                applied_fixes.append(fix_result)
                fixes_applied += 1
                logger.info(f"Applied fix {recommendation.issue_id}: {fix_result.description}")
        
        return applied_fixes
    
    def _apply_single_fix(self, recommendation: FixRecommendation) -> Optional[FixResult]:
        """Apply a single fix based on recommendation"""
        try:
            if recommendation.fix_type == FixType.CODE_FORMATTING:
                results = self.fix_engine.apply_code_formatting_fixes()
                return results[0] if results else None
            
            elif recommendation.fix_type == FixType.DEPENDENCY_UPDATE:
                results = self.fix_engine.apply_dependency_updates()
                return results[0] if results else None
            
            elif recommendation.fix_type == FixType.CONFIGURATION_FIX:
                results = self.fix_engine.apply_configuration_fixes()
                return results[0] if results else None
            
            elif recommendation.fix_type == FixType.UBUNTU_OPTIMIZATION:
                results = self.fix_engine.apply_ubuntu_optimizations()
                return results[0] if results else None
        
        except Exception as e:
            logger.error(f"Failed to apply fix {recommendation.issue_id}: {e}")
            return FixResult(
                success=False,
                fix_type=recommendation.fix_type,
                file_path="unknown",
                description=f"Failed to apply {recommendation.description}",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )
        
        return None
    
    def _generate_integrated_report(self, analysis_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive integrated report"""
        report = {
            "timestamp": self.fix_engine.generate_fix_report()["timestamp"],
            "analysis_summary": analysis_report.get("summary", {}),
            "fix_recommendations": {
                "total_recommendations": len(self.fix_recommendations),
                "auto_applicable": len([r for r in self.fix_recommendations if r.auto_applicable]),
                "requires_review": len([r for r in self.fix_recommendations if r.requires_review]),
                "by_risk_level": self._count_by_risk_level(),
                "by_fix_type": self._count_by_fix_type()
            },
            "applied_fixes": {
                "total_applied": len(self.applied_fixes),
                "successful": len([f for f in self.applied_fixes if f.success]),
                "failed": len([f for f in self.applied_fixes if not f.success]),
                "by_type": self._count_applied_fixes_by_type()
            },
            "remaining_issues": self._calculate_remaining_issues(analysis_report),
            "recommendations": [
                {
                    "issue_id": r.issue_id,
                    "fix_type": r.fix_type.value,
                    "confidence": r.confidence,
                    "risk_level": r.risk_level,
                    "description": r.description,
                    "auto_applicable": r.auto_applicable,
                    "requires_review": r.requires_review
                }
                for r in self.fix_recommendations
            ],
            "applied_fixes_details": [
                {
                    "success": f.success,
                    "fix_type": f.fix_type.value,
                    "file_path": f.file_path,
                    "description": f.description,
                    "changes_made": f.changes_made,
                    "error_message": f.error_message
                }
                for f in self.applied_fixes
            ]
        }
        
        return report
    
    def _count_by_risk_level(self) -> Dict[str, int]:
        """Count recommendations by risk level"""
        counts = {"safe": 0, "low": 0, "medium": 0, "high": 0}
        for rec in self.fix_recommendations:
            counts[rec.risk_level] = counts.get(rec.risk_level, 0) + 1
        return counts
    
    def _count_by_fix_type(self) -> Dict[str, int]:
        """Count recommendations by fix type"""
        counts = {}
        for rec in self.fix_recommendations:
            fix_type = rec.fix_type.value
            counts[fix_type] = counts.get(fix_type, 0) + 1
        return counts
    
    def _count_applied_fixes_by_type(self) -> Dict[str, int]:
        """Count applied fixes by type"""
        counts = {}
        for fix in self.applied_fixes:
            fix_type = fix.fix_type.value
            counts[fix_type] = counts.get(fix_type, 0) + 1
        return counts
    
    def _calculate_remaining_issues(self, analysis_report: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate remaining issues after fixes"""
        total_issues = analysis_report.get("summary", {}).get("total_issues", 0)
        fixed_issues = len([f for f in self.applied_fixes if f.success])
        
        return {
            "total_original": total_issues,
            "fixed": fixed_issues,
            "remaining": max(0, total_issues - fixed_issues),
            "fix_rate": (fixed_issues / total_issues * 100) if total_issues > 0 else 0
        }
    
    def save_integrated_report(self, output_path: str = "integrated_fix_report.json"):
        """Save integrated report to file"""
        # Run analysis first if not done
        if not self.fix_recommendations:
            report = self.analyze_and_fix()
        else:
            report = self._generate_integrated_report({"issues": [], "summary": {"total_issues": 0}})
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Integrated fix report saved to {output_path}")
        return report


def main():
    """Main function for running integrated analysis and fixes"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Fix Integration System")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--analysis-report", help="Path to existing analysis report")
    parser.add_argument("--output", default="integrated_fix_report.json", help="Output report file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without applying")
    parser.add_argument("--auto-apply", action="store_true", help="Automatically apply safe fixes")
    
    args = parser.parse_args()
    
    # Initialize integration system
    integration = AutomatedFixIntegration(args.project_root)
    
    # Override config for dry run
    if args.dry_run:
        integration.config["auto_apply_safe_fixes"] = False
        integration.config["require_confirmation_for_medium_risk"] = True
        integration.config["skip_high_risk_fixes"] = True
    
    if args.auto_apply:
        integration.config["auto_apply_safe_fixes"] = True
        integration.config["require_confirmation_for_medium_risk"] = False
    
    logger.info("Starting integrated analysis and fix process...")
    
    # Run analysis and fixes
    report = integration.analyze_and_fix(args.analysis_report)
    
    # Save report
    integration.save_integrated_report(args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("AUTOMATED FIX INTEGRATION SUMMARY")
    print("="*60)
    print(f"Total recommendations: {report['fix_recommendations']['total_recommendations']}")
    print(f"Auto-applicable fixes: {report['fix_recommendations']['auto_applicable']}")
    print(f"Fixes requiring review: {report['fix_recommendations']['requires_review']}")
    print(f"Fixes applied: {report['applied_fixes']['total_applied']}")
    print(f"Successful fixes: {report['applied_fixes']['successful']}")
    print(f"Failed fixes: {report['applied_fixes']['failed']}")
    
    if report.get('remaining_issues'):
        print(f"Fix rate: {report['remaining_issues']['fix_rate']:.1f}%")
    
    print(f"\nDetailed report saved to: {args.output}")


if __name__ == "__main__":
    main()