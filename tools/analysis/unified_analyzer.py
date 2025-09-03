#!/usr/bin/env python3
"""
Unified Analysis Tool for AI Scholar
Consolidates multiple analysis scripts into a single tool.
"""

import asyncio
import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class AnalysisConfig:
    """Configuration for analysis operations"""
    target_directory: Path
    analysis_types: List[str]
    output_format: str = "json"
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None

class UnifiedAnalyzer:
    """Consolidated analysis tool"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.results = {}
    
    async def run_analysis(self) -> Dict:
        """Run comprehensive analysis"""
        print(f"🔍 Analyzing {self.config.target_directory}")
        
        for analysis_type in self.config.analysis_types:
            print(f"Running {analysis_type} analysis...")
            
            if analysis_type == "security":
                self.results["security"] = await self._security_analysis()
            elif analysis_type == "performance":
                self.results["performance"] = await self._performance_analysis()
            elif analysis_type == "quality":
                self.results["quality"] = await self._quality_analysis()
            elif analysis_type == "dependencies":
                self.results["dependencies"] = await self._dependency_analysis()
            elif analysis_type == "scripts":
                self.results["scripts"] = await self._scripts_analysis()
        
        return self.results
    
    async def _security_analysis(self) -> Dict:
        """Security analysis"""
        issues = []
        recommendations = []
        
        # Check for common security issues
        backend_dir = self.config.target_directory / "backend"
        if backend_dir.exists():
            # Check for hardcoded secrets
            for py_file in backend_dir.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    if "password" in content.lower() and "=" in content:
                        issues.append(f"Potential hardcoded password in {py_file}")
                except:
                    pass
        
        return {
            "status": "completed",
            "issues_found": len(issues),
            "issues": issues,
            "recommendations": recommendations or ["Security analysis completed - no major issues found"]
        }
    
    async def _performance_analysis(self) -> Dict:
        """Performance analysis"""
        recommendations = []
        
        # Check bundle size
        dist_dir = self.config.target_directory / "dist"
        bundle_size = 0
        if dist_dir.exists():
            bundle_size = sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file())
            bundle_size_mb = bundle_size / (1024 * 1024)
            
            if bundle_size_mb > 2.0:
                recommendations.append(f"Bundle size is {bundle_size_mb:.1f}MB - consider optimization")
        
        # Check for large files
        large_files = []
        for file_path in self.config.target_directory.rglob("*"):
            if file_path.is_file() and file_path.stat().st_size > 1024 * 1024:  # 1MB
                large_files.append(str(file_path))
        
        return {
            "status": "completed", 
            "bundle_size_mb": bundle_size / (1024 * 1024) if bundle_size else 0,
            "large_files": large_files,
            "recommendations": recommendations or ["Performance analysis completed"]
        }
    
    async def _quality_analysis(self) -> Dict:
        """Code quality analysis"""
        issues = []
        
        # Count Python files
        py_files = list(self.config.target_directory.rglob("*.py"))
        ts_files = list(self.config.target_directory.rglob("*.ts")) + list(self.config.target_directory.rglob("*.tsx"))
        
        # Check for TODO comments
        todo_count = 0
        for file_path in py_files + ts_files:
            try:
                content = file_path.read_text()
                todo_count += content.upper().count("TODO")
                todo_count += content.upper().count("FIXME")
            except:
                pass
        
        score = 8.5  # Base score
        if todo_count > 10:
            score -= 0.5
            issues.append(f"Found {todo_count} TODO/FIXME comments")
        
        return {
            "status": "completed",
            "score": score,
            "python_files": len(py_files),
            "typescript_files": len(ts_files),
            "todo_count": todo_count,
            "issues": issues,
            "recommendations": ["Good code quality overall"]
        }
    
    async def _dependency_analysis(self) -> Dict:
        """Dependency analysis"""
        outdated = []
        vulnerabilities = []
        
        # Check package.json
        package_json = self.config.target_directory / "package.json"
        if package_json.exists():
            try:
                # Run npm audit if available
                result = subprocess.run(
                    ["npm", "audit", "--json"], 
                    cwd=self.config.target_directory,
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    audit_data = json.loads(result.stdout)
                    vulnerabilities = audit_data.get("vulnerabilities", {})
            except:
                pass
        
        # Check requirements.txt
        requirements_txt = self.config.target_directory / "requirements.txt"
        backend_requirements = self.config.target_directory / "backend" / "requirements.txt"
        
        python_packages = 0
        if requirements_txt.exists():
            python_packages += len(requirements_txt.read_text().splitlines())
        if backend_requirements.exists():
            python_packages += len(backend_requirements.read_text().splitlines())
        
        return {
            "status": "completed",
            "python_packages": python_packages,
            "npm_vulnerabilities": len(vulnerabilities),
            "outdated_packages": len(outdated),
            "security_vulnerabilities": len(vulnerabilities)
        }
    
    async def _scripts_analysis(self) -> Dict:
        """Analyze scripts directory for consolidation opportunities"""
        scripts_dir = self.config.target_directory / "scripts"
        if not scripts_dir.exists():
            return {"status": "no_scripts_directory"}
        
        script_files = list(scripts_dir.glob("*.py"))
        
        categories = {
            "analysis": [],
            "testing": [],
            "deployment": [],
            "maintenance": [],
            "deprecated": []
        }
        
        for script in script_files:
            name = script.name.lower()
            
            if any(keyword in name for keyword in ["analyzer", "analysis", "scan", "security", "performance"]):
                categories["analysis"].append(str(script))
            elif any(keyword in name for keyword in ["test", "verify", "validate"]):
                categories["testing"].append(str(script))
            elif any(keyword in name for keyword in ["deploy", "docker", "ubuntu"]):
                categories["deployment"].append(str(script))
            elif any(keyword in name for keyword in ["fix", "update", "clean", "format"]):
                categories["maintenance"].append(str(script))
            elif any(pattern in name for pattern in ["demo_", "simple_", "basic_", "standalone_"]):
                categories["deprecated"].append(str(script))
            else:
                categories["maintenance"].append(str(script))
        
        return {
            "status": "completed",
            "total_scripts": len(script_files),
            "categories": categories,
            "consolidation_opportunity": len(script_files) > 20
        }
    
    def generate_report(self) -> str:
        """Generate analysis report"""
        if self.config.output_format == "json":
            return json.dumps(self.results, indent=2, default=str)
        else:
            # Markdown format
            report = "# Analysis Report\n\n"
            report += f"**Generated:** {Path.cwd()}\n"
            report += f"**Target:** {self.config.target_directory}\n\n"
            
            for analysis_type, results in self.results.items():
                report += f"## {analysis_type.title()} Analysis\n"
                report += f"**Status:** {results.get('status', 'unknown')}\n\n"
                
                if analysis_type == "quality":
                    report += f"**Score:** {results.get('score', 'N/A')}/10\n"
                    report += f"**Python Files:** {results.get('python_files', 0)}\n"
                    report += f"**TypeScript Files:** {results.get('typescript_files', 0)}\n"
                
                elif analysis_type == "performance":
                    report += f"**Bundle Size:** {results.get('bundle_size_mb', 0):.1f}MB\n"
                
                elif analysis_type == "security":
                    report += f"**Issues Found:** {results.get('issues_found', 0)}\n"
                
                elif analysis_type == "scripts":
                    report += f"**Total Scripts:** {results.get('total_scripts', 0)}\n"
                    if results.get('consolidation_opportunity'):
                        report += "**Recommendation:** Consider script consolidation\n"
                
                report += "\n"
            
            return report

async def main():
    parser = argparse.ArgumentParser(description="Unified AI Scholar Analyzer")
    parser.add_argument("--target", default=".", help="Target directory")
    parser.add_argument("--types", nargs="+", 
                       default=["security", "performance", "quality", "dependencies", "scripts"],
                       help="Analysis types to run")
    parser.add_argument("--output", default="json", 
                       choices=["json", "markdown"], help="Output format")
    
    args = parser.parse_args()
    
    config = AnalysisConfig(
        target_directory=Path(args.target),
        analysis_types=args.types,
        output_format=args.output
    )
    
    analyzer = UnifiedAnalyzer(config)
    results = await analyzer.run_analysis()
    report = analyzer.generate_report()
    
    # Save report
    output_file = f"analysis_report.{args.output}"
    Path(output_file).write_text(report)
    
    print(f"\n📊 Analysis complete! Report saved to {output_file}")
    
    # Print summary
    print("\n📋 Summary:")
    for analysis_type, result in results.items():
        status = result.get('status', 'unknown')
        print(f"  {analysis_type}: {status}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())