#!/usr/bin/env python3
"""
Test suite for Code Quality Analyzer

Tests all components of the code quality and technical debt analyzer:
- Code structure analysis
- Dependency analysis  
- Error handling analysis
- Documentation coverage analysis
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
import sys

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code_quality_analyzer import (
    CodeQualityAnalyzer,
    CodeStructureAnalyzer,
    DependencyAnalyzer,
    ErrorHandlingAnalyzer,
    DocumentationAnalyzer,
    QualityIssue,
    DependencyIssue,
    DocumentationGap
)

class TestCodeStructureAnalyzer(unittest.TestCase):
    """Test code structure analysis functionality"""
    
    def setUp(self):
        self.analyzer = CodeStructureAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_analyze_long_function(self):
        """Test detection of overly long functions"""
        long_function_code = '''
def very_long_function():
    """A function that is too long"""
''' + '\n'.join([f'    print("line {i}")' for i in range(60)])
        
        test_file = os.path.join(self.temp_dir, 'test_long.py')
        with open(test_file, 'w') as f:
            f.write(long_function_code)
        
        issues = self.analyzer._analyze_python_file(test_file)
        
        # Should detect function too long
        long_function_issues = [issue for issue in issues if issue.type == "function_too_long"]
        self.assertEqual(len(long_function_issues), 1)
        self.assertEqual(long_function_issues[0].severity, "medium")
    
    def test_analyze_many_parameters(self):
        """Test detection of functions with too many parameters"""
        many_params_code = '''
def function_with_many_params(a, b, c, d, e, f, g):
    """Function with too many parameters"""
    return a + b + c + d + e + f + g
'''
        
        test_file = os.path.join(self.temp_dir, 'test_params.py')
        with open(test_file, 'w') as f:
            f.write(many_params_code)
        
        issues = self.analyzer._analyze_python_file(test_file)
        
        # Should detect too many parameters
        param_issues = [issue for issue in issues if issue.type == "too_many_parameters"]
        self.assertEqual(len(param_issues), 1)
        self.assertEqual(param_issues[0].severity, "medium")
    
    def test_analyze_missing_docstring(self):
        """Test detection of missing docstrings"""
        no_docstring_code = '''
def function_without_docstring():
    return "hello"

class ClassWithoutDocstring:
    def method(self):
        pass
'''
        
        test_file = os.path.join(self.temp_dir, 'test_docstring.py')
        with open(test_file, 'w') as f:
            f.write(no_docstring_code)
        
        issues = self.analyzer._analyze_python_file(test_file)
        
        # Should detect missing docstrings (function, class, and method)
        docstring_issues = [issue for issue in issues if issue.type == "missing_docstring"]
        self.assertEqual(len(docstring_issues), 3)  # Function, class, and method
    
    def test_analyze_syntax_error(self):
        """Test handling of syntax errors"""
        syntax_error_code = '''
def broken_function(
    # Missing closing parenthesis
    return "broken"
'''
        
        test_file = os.path.join(self.temp_dir, 'test_syntax.py')
        with open(test_file, 'w') as f:
            f.write(syntax_error_code)
        
        issues = self.analyzer._analyze_python_file(test_file)
        
        # Should detect syntax error
        syntax_issues = [issue for issue in issues if issue.type == "syntax_error"]
        self.assertEqual(len(syntax_issues), 1)
        self.assertEqual(syntax_issues[0].severity, "critical")

class TestDependencyAnalyzer(unittest.TestCase):
    """Test dependency analysis functionality"""
    
    def setUp(self):
        self.analyzer = DependencyAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_analyze_requirements_file(self):
        """Test analysis of Python requirements file"""
        requirements_content = '''
# Test requirements
requests==2.25.1
flask==1.1.4
numpy==0.19.0
django==3.2.0
'''
        
        req_file = os.path.join(self.temp_dir, 'requirements.txt')
        with open(req_file, 'w') as f:
            f.write(requirements_content)
        
        issues = self.analyzer._analyze_requirements_file(req_file)
        
        # Should detect potentially outdated packages
        self.assertGreater(len(issues), 0)
        
        # Check that all issues are dependency issues
        for issue in issues:
            self.assertIsInstance(issue, DependencyIssue)
            self.assertEqual(issue.issue_type, "potentially_outdated")
    
    def test_analyze_package_json(self):
        """Test analysis of Node.js package.json file"""
        package_json_content = {
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "react": "16.14.0",
                "lodash": "4.17.20",
                "express": "^4.17.1"
            },
            "devDependencies": {
                "webpack": "4.46.0",
                "babel-core": "^6.26.3"
            }
        }
        
        package_file = os.path.join(self.temp_dir, 'package.json')
        with open(package_file, 'w') as f:
            json.dump(package_json_content, f)
        
        issues = self.analyzer._analyze_package_json(package_file)
        
        # Should detect potentially outdated packages
        self.assertGreater(len(issues), 0)
        
        # Check that all issues are dependency issues
        for issue in issues:
            self.assertIsInstance(issue, DependencyIssue)

class TestErrorHandlingAnalyzer(unittest.TestCase):
    """Test error handling analysis functionality"""
    
    def setUp(self):
        self.analyzer = ErrorHandlingAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_analyze_missing_error_handling(self):
        """Test detection of missing error handling"""
        risky_code = '''
def risky_function():
    """Function with risky operations but no error handling"""
    with open("nonexistent.txt", "r") as f:
        content = f.read()
    return content
'''
        
        test_file = os.path.join(self.temp_dir, 'test_risky.py')
        with open(test_file, 'w') as f:
            f.write(risky_code)
        
        issues = self.analyzer._analyze_file_error_handling(test_file)
        
        # Should detect missing error handling
        error_issues = [issue for issue in issues if issue.type == "missing_error_handling"]
        self.assertEqual(len(error_issues), 1)
        self.assertEqual(error_issues[0].severity, "medium")
    
    def test_analyze_bare_except(self):
        """Test detection of bare except clauses"""
        bare_except_code = '''
def function_with_bare_except():
    """Function with bare except clause"""
    try:
        risky_operation()
    except:
        pass
'''
        
        test_file = os.path.join(self.temp_dir, 'test_bare_except.py')
        with open(test_file, 'w') as f:
            f.write(bare_except_code)
        
        issues = self.analyzer._analyze_file_error_handling(test_file)
        
        # Should detect bare except
        bare_except_issues = [issue for issue in issues if issue.type == "bare_except"]
        self.assertEqual(len(bare_except_issues), 1)
        self.assertEqual(bare_except_issues[0].severity, "medium")
    
    def test_analyze_good_error_handling(self):
        """Test that good error handling doesn't trigger issues"""
        good_code = '''
def well_handled_function():
    """Function with proper error handling"""
    try:
        with open("file.txt", "r") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return None
    except IOError as e:
        logger.error(f"IO error: {e}")
        raise
'''
        
        test_file = os.path.join(self.temp_dir, 'test_good.py')
        with open(test_file, 'w') as f:
            f.write(good_code)
        
        issues = self.analyzer._analyze_file_error_handling(test_file)
        
        # Should not detect error handling issues
        error_issues = [issue for issue in issues if issue.type in ["missing_error_handling", "bare_except"]]
        self.assertEqual(len(error_issues), 0)

class TestDocumentationAnalyzer(unittest.TestCase):
    """Test documentation analysis functionality"""
    
    def setUp(self):
        self.analyzer = DocumentationAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_analyze_missing_module_docstring(self):
        """Test detection of missing module docstring"""
        no_module_docstring = '''
def some_function():
    """Function with docstring"""
    pass
'''
        
        test_file = os.path.join(self.temp_dir, 'test_module.py')
        with open(test_file, 'w') as f:
            f.write(no_module_docstring)
        
        gaps = self.analyzer._analyze_file_documentation(test_file)
        
        # Should detect missing module docstring
        module_gaps = [gap for gap in gaps if gap.gap_type == "missing_module_docstring"]
        self.assertEqual(len(module_gaps), 1)
    
    def test_analyze_missing_function_docstring(self):
        """Test detection of missing function docstrings"""
        no_function_docstring = '''
"""Module with docstring"""

def public_function():
    return "hello"

def _private_function():
    return "private"

def test_function():
    assert True
'''
        
        test_file = os.path.join(self.temp_dir, 'test_functions.py')
        with open(test_file, 'w') as f:
            f.write(no_function_docstring)
        
        gaps = self.analyzer._analyze_file_documentation(test_file)
        
        # Should detect missing docstring for public function only
        function_gaps = [gap for gap in gaps if gap.gap_type == "missing_docstring" and gap.function_name]
        self.assertEqual(len(function_gaps), 1)
        self.assertEqual(function_gaps[0].function_name, "public_function")
    
    def test_analyze_missing_type_hints(self):
        """Test detection of missing type hints"""
        no_type_hints = '''
"""Module with docstring"""

def function_without_hints(param):
    """Function without type hints"""
    return param * 2

def function_with_hints(param: int) -> int:
    """Function with type hints"""
    return param * 2
'''
        
        test_file = os.path.join(self.temp_dir, 'test_hints.py')
        with open(test_file, 'w') as f:
            f.write(no_type_hints)
        
        gaps = self.analyzer._analyze_file_documentation(test_file)
        
        # Should detect missing type hints for first function only
        hint_gaps = [gap for gap in gaps if gap.gap_type == "missing_type_hints"]
        self.assertEqual(len(hint_gaps), 1)
        self.assertEqual(hint_gaps[0].function_name, "function_without_hints")
    
    def test_analyze_incomplete_docstring(self):
        """Test detection of incomplete docstrings"""
        incomplete_docstring = '''
"""Module with docstring"""

def function_with_brief_docstring():
    """Brief"""
    return "hello"

def function_with_good_docstring():
    """
    This function has a comprehensive docstring that explains
    what it does, its parameters, and return value.
    """
    return "hello"
'''
        
        test_file = os.path.join(self.temp_dir, 'test_incomplete.py')
        with open(test_file, 'w') as f:
            f.write(incomplete_docstring)
        
        gaps = self.analyzer._analyze_file_documentation(test_file)
        
        # Should detect incomplete docstring for first function only
        incomplete_gaps = [gap for gap in gaps if gap.gap_type == "incomplete_docstring"]
        self.assertEqual(len(incomplete_gaps), 1)
        self.assertEqual(incomplete_gaps[0].function_name, "function_with_brief_docstring")

class TestCodeQualityAnalyzer(unittest.TestCase):
    """Test the main code quality analyzer"""
    
    def setUp(self):
        self.analyzer = CodeQualityAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_comprehensive_analysis(self):
        """Test comprehensive analysis of a sample codebase"""
        # Create sample files with various issues
        sample_code = '''
"""Sample module for testing"""

def long_function_with_issues(a, b, c, d, e, f):
    # This function has multiple issues:
    # - Too many parameters
    # - Missing docstring would be detected but we have one
    # - Missing error handling for file operations
    with open("test.txt", "r") as f:
        content = f.read()
    
    # Make it long enough to trigger length warning
''' + '\n'.join([f'    print("Processing line {i}")' for i in range(50)]) + '''
    return content

class UndocumentedClass:
    def method_without_docstring(self):
        try:
            return self.risky_operation()
        except:
            return None
'''
        
        # Create requirements file with outdated packages
        requirements_content = '''
requests==2.20.0
flask==0.12.0
numpy==1.15.0
'''
        
        # Create package.json with outdated packages
        package_json = {
            "dependencies": {
                "react": "16.0.0",
                "lodash": "4.0.0"
            }
        }
        
        # Write test files
        test_file = os.path.join(self.temp_dir, 'test_code.py')
        with open(test_file, 'w') as f:
            f.write(sample_code)
        
        req_file = os.path.join(self.temp_dir, 'requirements.txt')
        with open(req_file, 'w') as f:
            f.write(requirements_content)
        
        package_file = os.path.join(self.temp_dir, 'package.json')
        with open(package_file, 'w') as f:
            json.dump(package_json, f)
        
        # Run comprehensive analysis
        results = self.analyzer.analyze_codebase(self.temp_dir)
        
        # Verify results structure
        self.assertIn("timestamp", results)
        self.assertIn("analysis_summary", results)
        self.assertIn("code_structure_issues", results)
        self.assertIn("dependency_issues", results)
        self.assertIn("error_handling_issues", results)
        self.assertIn("documentation_gaps", results)
        self.assertIn("recommendations", results)
        
        # Verify we found some issues
        self.assertGreater(results["analysis_summary"]["total_issues"], 0)
        
        # Verify specific issue types were detected
        structure_issues = results["code_structure_issues"]
        self.assertTrue(any(issue["type"] == "too_many_parameters" for issue in structure_issues))
        
        dependency_issues = results["dependency_issues"]
        self.assertGreater(len(dependency_issues), 0)
        
        error_handling_issues = results["error_handling_issues"]
        self.assertTrue(any(issue["type"] == "bare_except" for issue in error_handling_issues))
        
        documentation_gaps = results["documentation_gaps"]
        self.assertTrue(any(gap["gap_type"] == "missing_docstring" for gap in documentation_gaps))
    
    def test_find_requirements_files(self):
        """Test finding requirements files"""
        # Create various requirements files
        req_files = [
            'requirements.txt',
            'requirements-dev.txt',
            'dev-requirements.txt'
        ]
        
        for req_file in req_files:
            file_path = os.path.join(self.temp_dir, req_file)
            with open(file_path, 'w') as f:
                f.write('requests==2.25.1\n')
        
        found_files = self.analyzer._find_requirements_files(self.temp_dir)
        
        # Should find all requirements files
        self.assertEqual(len(found_files), len(req_files))
        
        # Verify all files were found
        found_names = [os.path.basename(f) for f in found_files]
        for req_file in req_files:
            self.assertIn(req_file, found_names)
    
    def test_find_package_json_files(self):
        """Test finding package.json files"""
        # Create package.json files in different directories
        dirs = ['', 'frontend', 'backend/api']
        
        for dir_path in dirs:
            full_dir = os.path.join(self.temp_dir, dir_path)
            os.makedirs(full_dir, exist_ok=True)
            
            package_file = os.path.join(full_dir, 'package.json')
            with open(package_file, 'w') as f:
                json.dump({"name": "test", "version": "1.0.0"}, f)
        
        found_files = self.analyzer._find_package_json_files(self.temp_dir)
        
        # Should find all package.json files
        self.assertEqual(len(found_files), len(dirs))

def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestCodeStructureAnalyzer,
        TestDependencyAnalyzer,
        TestErrorHandlingAnalyzer,
        TestDocumentationAnalyzer,
        TestCodeQualityAnalyzer
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)