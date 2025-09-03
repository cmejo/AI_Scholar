#!/usr/bin/env python3
"""
Test Consolidation Tool for AI Scholar
Analyzes and optimizes the test suite.
"""

import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class TestInfo:
    """Information about a test file"""
    file_path: Path
    test_functions: List[str]
    test_classes: List[str]
    imports: List[str]
    markers: List[str]

class TestConsolidator:
    """Consolidate and optimize test suite"""
    
    def __init__(self, test_directories: List[Path]):
        self.test_directories = test_directories
        self.test_files: Dict[Path, TestInfo] = {}
    
    def analyze_test_suite(self) -> Dict:
        """Analyze test suite for optimization opportunities"""
        print("🧪 Analyzing test suite...")
        
        # Scan all test files
        for test_dir in self.test_directories:
            if test_dir.exists():
                print(f"  Scanning {test_dir}...")
                for test_file in test_dir.glob("**/test_*.py"):
                    self.test_files[test_file] = self._analyze_test_file(test_file)
        
        duplicates = self._find_duplicate_tests()
        slow_tests = self._find_slow_tests()
        overlapping_tests = self._find_overlapping_tests()
        
        return {
            "total_test_files": len(self.test_files),
            "duplicate_tests": len(duplicates),
            "slow_tests": len(slow_tests),
            "overlapping_tests": len(overlapping_tests),
            "recommendations": self._generate_recommendations(),
            "duplicates": [str(f) for f in duplicates],
            "slow_test_files": [str(f) for f in slow_tests]
        }
    
    def _analyze_test_file(self, file_path: Path) -> TestInfo:
        """Analyze individual test file"""
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            
            test_functions = []
            test_classes = []
            imports = []
            markers = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    test_functions.append(node.name)
                elif isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                    test_classes.append(node.name)
                elif isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
            
            return TestInfo(
                file_path=file_path,
                test_functions=test_functions,
                test_classes=test_classes,
                imports=imports,
                markers=markers
            )
        except Exception as e:
            print(f"  Warning: Error analyzing {file_path}: {e}")
            return TestInfo(file_path, [], [], [], [])
    
    def _find_duplicate_tests(self) -> List[Path]:
        """Find potentially duplicate test files"""
        duplicates = []
        seen_signatures = {}
        
        for file_path, test_info in self.test_files.items():
            # Simple signature based on function names
            signature = tuple(sorted(test_info.test_functions))
            
            if signature in seen_signatures and len(signature) > 0:
                duplicates.append(file_path)
            else:
                seen_signatures[signature] = file_path
        
        return duplicates
    
    def _find_slow_tests(self) -> List[Path]:
        """Find potentially slow tests"""
        slow_tests = []
        
        for file_path, test_info in self.test_files.items():
            # Heuristics for slow tests
            path_str = str(file_path).lower()
            if any(keyword in path_str for keyword in 
                   ['integration', 'comprehensive', 'e2e', 'load', 'stress']):
                slow_tests.append(file_path)
            
            # Check for database/external dependencies
            if any(imp in test_info.imports for imp in 
                   ['sqlalchemy', 'redis', 'docker', 'requests', 'aiohttp']):
                slow_tests.append(file_path)
        
        return list(set(slow_tests))  # Remove duplicates
    
    def _find_overlapping_tests(self) -> List[tuple]:
        """Find tests with significant overlap"""
        overlaps = []
        
        files = list(self.test_files.items())
        for i, (file1, info1) in enumerate(files):
            for file2, info2 in files[i+1:]:
                overlap_ratio = self._calculate_overlap(info1, info2)
                if overlap_ratio > 0.7:  # 70% overlap threshold
                    overlaps.append((file1, file2, overlap_ratio))
        
        return overlaps
    
    def _calculate_overlap(self, info1: TestInfo, info2: TestInfo) -> float:
        """Calculate overlap ratio between two test files"""
        functions1 = set(info1.test_functions)
        functions2 = set(info2.test_functions)
        
        if not functions1 or not functions2:
            return 0.0
        
        intersection = len(functions1.intersection(functions2))
        union = len(functions1.union(functions2))
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = [
            "Consider marking slow tests with @pytest.mark.slow",
            "Use parallel test execution with pytest-xdist (-n auto)",
            "Implement test fixtures for common setup",
            "Consider test categorization (unit/integration/e2e)",
            "Remove or consolidate duplicate test files"
        ]
        
        if len(self.test_files) > 100:
            recommendations.append("Large test suite - consider organizing into subdirectories")
        
        return recommendations
    
    def optimize_pytest_config(self) -> str:
        """Generate optimized pytest configuration"""
        config = '''[tool.pytest.ini_options]
minversion = "7.0"
addopts = [
    "-ra",
    "--strict-markers", 
    "--cov=backend",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-fail-under=80",
    "-n auto",
    "--dist=worksteal",
    "--maxfail=5",
    "--tb=short"
]

testpaths = ["tests", "backend/tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]

markers = [
    "slow: marks tests as slow (deselect with '-m \\"not slow\\"')",
    "integration: marks tests as integration tests", 
    "unit: marks tests as unit tests",
    "api: marks tests as API tests",
    "security: marks tests as security tests",
    "performance: marks tests as performance tests"
]

filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning"
]
'''
        
        config_file = Path("pytest.ini")
        config_file.write_text(config)
        
        return str(config_file)
    
    def generate_test_optimization_plan(self) -> str:
        """Generate detailed test optimization plan"""
        analysis = self.analyze_test_suite()
        
        plan = "# Test Suite Optimization Plan\n\n"
        plan += f"**Generated:** {Path.cwd()}\n"
        plan += f"**Total Test Files:** {analysis['total_test_files']}\n\n"
        
        plan += "## Summary\n"
        plan += f"- Duplicate tests: {analysis['duplicate_tests']}\n"
        plan += f"- Slow tests: {analysis['slow_tests']}\n"
        plan += f"- Overlapping tests: {analysis['overlapping_tests']}\n\n"
        
        if analysis['duplicates']:
            plan += "## Duplicate Tests (Consider removing)\n"
            for duplicate in analysis['duplicates']:
                plan += f"- `{duplicate}`\n"
            plan += "\n"
        
        if analysis['slow_test_files']:
            plan += "## Slow Tests (Mark with @pytest.mark.slow)\n"
            for slow_test in analysis['slow_test_files']:
                plan += f"- `{slow_test}`\n"
            plan += "\n"
        
        plan += "## Recommendations\n"
        for i, rec in enumerate(analysis['recommendations'], 1):
            plan += f"{i}. {rec}\n"
        
        plan += "\n## Implementation Steps\n"
        plan += "1. Apply optimized pytest configuration\n"
        plan += "2. Mark slow tests with appropriate decorators\n"
        plan += "3. Remove or consolidate duplicate tests\n"
        plan += "4. Organize tests into logical categories\n"
        plan += "5. Set up parallel test execution\n"
        
        return plan

def main():
    test_dirs = [Path("tests"), Path("backend/tests"), Path("src/test")]
    consolidator = TestConsolidator(test_dirs)
    
    results = consolidator.analyze_test_suite()
    config_file = consolidator.optimize_pytest_config()
    optimization_plan = consolidator.generate_test_optimization_plan()
    
    print(f"\n📊 Test Analysis Results:")
    print(f"  Total test files: {results['total_test_files']}")
    print(f"  Potential duplicates: {results['duplicate_tests']}")
    print(f"  Slow tests: {results['slow_tests']}")
    print(f"  Overlapping tests: {results['overlapping_tests']}")
    
    print(f"\n✅ Optimized pytest config saved to {config_file}")
    
    # Save optimization plan
    plan_file = Path("test_optimization_plan.md")
    plan_file.write_text(optimization_plan)
    print(f"📋 Test optimization plan saved to {plan_file}")
    
    return results

if __name__ == "__main__":
    main()