#!/usr/bin/env python3
"""
Advanced Code Quality Improvements
Additional recommendations beyond the security fixes already implemented.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any

class AdvancedCodeQualityAnalyzer:
    """Analyzes codebase for advanced quality improvements"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.recommendations = []
    
    def analyze_codebase(self) -> Dict[str, Any]:
        """Perform comprehensive code quality analysis"""
        
        print("🔍 Analyzing codebase for advanced quality improvements...")
        
        # 1. Technical Debt Analysis
        debt_analysis = self.analyze_technical_debt()
        
        # 2. Performance Issues
        performance_issues = self.analyze_performance_issues()
        
        # 3. Code Organization
        organization_issues = self.analyze_code_organization()
        
        # 4. Testing Gaps
        testing_gaps = self.analyze_testing_gaps()
        
        # 5. Documentation Issues
        documentation_issues = self.analyze_documentation()
        
        # 6. Dependency Management
        dependency_issues = self.analyze_dependencies()
        
        return {
            "technical_debt": debt_analysis,
            "performance": performance_issues,
            "organization": organization_issues,
            "testing": testing_gaps,
            "documentation": documentation_issues,
            "dependencies": dependency_issues,
            "recommendations": self.recommendations
        }
    
    def analyze_technical_debt(self) -> Dict[str, Any]:
        """Analyze technical debt in the codebase"""
        
        debt_items = {
            "todo_comments": 0,
            "console_logs": 0,
            "large_files": [],
            "complex_functions": [],
            "code_duplication": []
        }
        
        # Scan for TODO comments and console.log statements
        for file_path in self.project_root.rglob("*.ts"):
            if self._should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text()
                
                # Count TODO comments
                todos = len(re.findall(r'//.*TODO|#.*TODO', content, re.IGNORECASE))
                debt_items["todo_comments"] += todos
                
                # Count console.log statements
                console_logs = len(re.findall(r'console\.(log|error|warn|debug)', content))
                debt_items["console_logs"] += console_logs
                
                # Check file size
                if len(content.splitlines()) > 500:
                    debt_items["large_files"].append({
                        "file": str(file_path.relative_to(self.project_root)),
                        "lines": len(content.splitlines())
                    })
                
                # Detect potential code duplication patterns
                self._detect_code_duplication(file_path, content, debt_items)
                
            except Exception as e:
                continue
        
        # Add recommendations based on findings
        if debt_items["todo_comments"] > 10:
            self.recommendations.append({
                "category": "Technical Debt",
                "priority": "Medium",
                "issue": f"Found {debt_items['todo_comments']} TODO comments",
                "solution": "Create GitHub issues for TODO items and remove comments",
                "effort": "2-4 hours"
            })
        
        if debt_items["console_logs"] > 5:
            self.recommendations.append({
                "category": "Technical Debt", 
                "priority": "Low",
                "issue": f"Found {debt_items['console_logs']} console.log statements",
                "solution": "Replace with proper logging service or remove debug statements",
                "effort": "1-2 hours"
            })
        
        return debt_items
    
    def analyze_performance_issues(self) -> Dict[str, Any]:
        """Analyze potential performance issues"""
        
        performance_issues = {
            "large_bundles": [],
            "inefficient_imports": [],
            "memory_leaks": [],
            "blocking_operations": []
        }
        
        # Check for inefficient imports
        for file_path in self.project_root.rglob("*.ts"):
            if self._should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text()
                
                # Check for barrel imports that could be optimized
                barrel_imports = re.findall(r'import \{[^}]+\} from [\'"][^\'"]*/index[\'"]', content)
                if barrel_imports:
                    performance_issues["inefficient_imports"].append({
                        "file": str(file_path.relative_to(self.project_root)),
                        "imports": len(barrel_imports)
                    })
                
                # Check for potential memory leaks (event listeners without cleanup)
                event_listeners = re.findall(r'addEventListener|on\w+\s*=', content)
                cleanup_patterns = re.findall(r'removeEventListener|cleanup|dispose|destroy', content)
                
                if len(event_listeners) > len(cleanup_patterns):
                    performance_issues["memory_leaks"].append({
                        "file": str(file_path.relative_to(self.project_root)),
                        "listeners": len(event_listeners),
                        "cleanup": len(cleanup_patterns)
                    })
                
            except Exception:
                continue
        
        # Add performance recommendations
        if performance_issues["inefficient_imports"]:
            self.recommendations.append({
                "category": "Performance",
                "priority": "Medium",
                "issue": "Inefficient barrel imports detected",
                "solution": "Use direct imports instead of barrel imports for better tree-shaking",
                "effort": "2-3 hours"
            })
        
        return performance_issues
    
    def analyze_code_organization(self) -> Dict[str, Any]:
        """Analyze code organization and structure"""
        
        organization_issues = {
            "service_pattern_violations": [],
            "missing_interfaces": [],
            "inconsistent_naming": [],
            "circular_dependencies": []
        }
        
        # Check service pattern consistency
        services_dir = self.project_root / "src" / "services"
        if services_dir.exists():
            for service_file in services_dir.glob("*.ts"):
                content = service_file.read_text()
                
                # Check if service follows singleton pattern
                if "class " in content and "private static instance" not in content:
                    organization_issues["service_pattern_violations"].append({
                        "file": str(service_file.relative_to(self.project_root)),
                        "issue": "Service doesn't follow singleton pattern"
                    })
                
                # Check for proper interface definitions
                if "class " in content and "interface " not in content:
                    organization_issues["missing_interfaces"].append({
                        "file": str(service_file.relative_to(self.project_root)),
                        "issue": "Service class without interface definition"
                    })
        
        # Add organization recommendations
        if organization_issues["service_pattern_violations"]:
            self.recommendations.append({
                "category": "Code Organization",
                "priority": "Medium", 
                "issue": "Inconsistent service patterns",
                "solution": "Implement consistent singleton pattern for services",
                "effort": "3-5 hours"
            })
        
        return organization_issues
    
    def analyze_testing_gaps(self) -> Dict[str, Any]:
        """Analyze testing coverage and gaps"""
        
        testing_gaps = {
            "untested_services": [],
            "missing_integration_tests": [],
            "no_error_handling_tests": [],
            "missing_performance_tests": []
        }
        
        # Check for services without tests
        services_dir = self.project_root / "src" / "services"
        test_dir = self.project_root / "src" / "test"
        
        if services_dir.exists():
            for service_file in services_dir.glob("*.ts"):
                service_name = service_file.stem
                test_file = test_dir / f"{service_name}.test.ts"
                
                if not test_file.exists():
                    testing_gaps["untested_services"].append({
                        "service": service_name,
                        "file": str(service_file.relative_to(self.project_root))
                    })
        
        # Add testing recommendations
        if testing_gaps["untested_services"]:
            self.recommendations.append({
                "category": "Testing",
                "priority": "High",
                "issue": f"{len(testing_gaps['untested_services'])} services without tests",
                "solution": "Create comprehensive test suites for all services",
                "effort": "8-12 hours"
            })
        
        return testing_gaps
    
    def analyze_documentation(self) -> Dict[str, Any]:
        """Analyze documentation quality and coverage"""
        
        doc_issues = {
            "missing_jsdoc": [],
            "outdated_readme": False,
            "missing_api_docs": [],
            "no_architecture_docs": False
        }
        
        # Check for JSDoc coverage
        for file_path in self.project_root.rglob("*.ts"):
            if self._should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text()
                
                # Count functions/methods without JSDoc
                functions = re.findall(r'(export\s+)?(async\s+)?function\s+\w+|^\s*(public|private|protected)?\s*(async\s+)?\w+\s*\(', content, re.MULTILINE)
                jsdoc_comments = re.findall(r'/\*\*[\s\S]*?\*/', content)
                
                if len(functions) > len(jsdoc_comments) and len(functions) > 2:
                    doc_issues["missing_jsdoc"].append({
                        "file": str(file_path.relative_to(self.project_root)),
                        "functions": len(functions),
                        "documented": len(jsdoc_comments)
                    })
                    
            except Exception:
                continue
        
        # Add documentation recommendations
        if doc_issues["missing_jsdoc"]:
            self.recommendations.append({
                "category": "Documentation",
                "priority": "Medium",
                "issue": "Missing JSDoc comments for functions",
                "solution": "Add comprehensive JSDoc comments for all public methods",
                "effort": "4-6 hours"
            })
        
        return doc_issues
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze dependency management issues"""
        
        dependency_issues = {
            "unused_dependencies": [],
            "outdated_packages": [],
            "security_vulnerabilities": [],
            "large_dependencies": []
        }
        
        # This would require package.json analysis and npm audit
        # For now, provide general recommendations
        
        self.recommendations.append({
            "category": "Dependencies",
            "priority": "Medium",
            "issue": "Dependency management optimization needed",
            "solution": "Run npm audit, update packages, remove unused dependencies",
            "effort": "2-3 hours"
        })
        
        return dependency_issues
    
    def _detect_code_duplication(self, file_path: Path, content: str, debt_items: Dict):
        """Detect potential code duplication patterns"""
        
        # Look for repeated function patterns
        functions = re.findall(r'(async\s+)?function\s+\w+\([^)]*\)\s*\{[^}]{50,200}\}', content, re.DOTALL)
        
        # Simple heuristic: if we have many similar-sized functions, there might be duplication
        if len(functions) > 5:
            function_sizes = [len(func) for func in functions]
            avg_size = sum(function_sizes) / len(function_sizes)
            similar_functions = [size for size in function_sizes if abs(size - avg_size) < 20]
            
            if len(similar_functions) > 3:
                debt_items["code_duplication"].append({
                    "file": str(file_path.relative_to(self.project_root)),
                    "potential_duplicates": len(similar_functions)
                })
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped in analysis"""
        skip_patterns = [
            "node_modules", ".git", "dist", "build", ".next",
            "coverage", "__pycache__", ".pytest_cache"
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)

def main():
    """Run advanced code quality analysis"""
    analyzer = AdvancedCodeQualityAnalyzer()
    results = analyzer.analyze_codebase()
    
    print("\\n" + "="*60)
    print("ADVANCED CODE QUALITY ANALYSIS RESULTS")
    print("="*60)
    
    # Print summary
    print(f"\\n📊 Analysis Summary:")
    print(f"TODO Comments: {results['technical_debt']['todo_comments']}")
    print(f"Console Logs: {results['technical_debt']['console_logs']}")
    print(f"Large Files: {len(results['technical_debt']['large_files'])}")
    print(f"Untested Services: {len(results['testing']['untested_services'])}")
    
    # Print recommendations
    print(f"\\n🎯 Recommendations ({len(results['recommendations'])} total):")
    
    for i, rec in enumerate(results['recommendations'], 1):
        priority_emoji = {
            "High": "🔴",
            "Medium": "🟡", 
            "Low": "🟢"
        }.get(rec['priority'], "⚪")
        
        print(f"\\n{priority_emoji} {i}. {rec['issue']}")
        print(f"   Category: {rec['category']}")
        print(f"   Solution: {rec['solution']}")
        print(f"   Effort: {rec['effort']}")
    
    return results

if __name__ == "__main__":
    main()