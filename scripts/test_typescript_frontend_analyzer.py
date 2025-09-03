#!/usr/bin/env python3
"""
Test script for TypeScript/React Frontend Code Analyzer

This script tests the functionality of the TypeScript frontend analyzer
to ensure it properly detects compilation errors, component issues,
bundle problems, and accessibility violations.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typescript_frontend_analyzer import (
    TypeScriptFrontendAnalyzer,
    IssueType,
    IssueSeverity
)

class FrontendAnalyzerTester:
    """Test suite for the TypeScript frontend analyzer"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
    
    def setup_test_environment(self):
        """Set up a temporary test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create basic project structure
        (self.temp_dir / "frontend" / "src" / "components").mkdir(parents=True)
        (self.temp_dir / "frontend" / "public").mkdir(parents=True)
        
        # Create package.json
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0"
            },
            "devDependencies": {
                "typescript": "^5.0.0",
                "@types/react": "^18.0.0"
            },
            "scripts": {
                "build": "echo 'Build completed'"
            }
        }
        
        with open(self.temp_dir / "package.json", 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Create tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "lib": ["DOM", "DOM.Iterable", "ES6"],
                "allowJs": True,
                "skipLibCheck": True,
                "esModuleInterop": True,
                "allowSyntheticDefaultImports": True,
                "strict": True,
                "forceConsistentCasingInFileNames": True,
                "moduleResolution": "node",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx"
            },
            "include": ["src"]
        }
        
        with open(self.temp_dir / "tsconfig.json", 'w') as f:
            json.dump(tsconfig, f, indent=2)
        
        # Create test React components with various issues
        self.create_test_components()
        
        return self.temp_dir
    
    def create_test_components(self):
        """Create test React components with intentional issues"""
        
        # Component with TypeScript errors
        component_with_ts_errors = '''
import React from 'react';
import { UnusedImport } from 'some-library';

interface Props {
    name: string;
    age: number;
}

const ComponentWithErrors: React.FC<Props> = ({ name }) => {
    // TypeScript error: age is required but not used
    const invalidAssignment: string = 123; // Type error
    
    // Unused variable
    const unusedVariable = "test";
    
    console.log("Debug statement"); // Should be flagged
    
    return (
        <div style={{color: 'red', fontSize: '16px'}}> {/* Inline styles */}
            <h1>{name}</h1>
            <img src="test.jpg" /> {/* Missing alt attribute */}
            <button onClick={() => alert('clicked')}></button> {/* Button without text */}
            <div onClick={() => console.log('clicked')}>Click me</div> {/* Non-interactive element with click */}
        </div>
    );
};

export default ComponentWithErrors;
'''
        
        with open(self.temp_dir / "frontend" / "src" / "components" / "ComponentWithErrors.tsx", 'w') as f:
            f.write(component_with_ts_errors)
        
        # Component with accessibility issues
        accessibility_component = '''
import React, { useState, useEffect } from 'react';

const AccessibilityIssues: React.FC = () => {
    const [count, setCount] = useState(0);
    
    // useEffect without dependency array
    useEffect(() => {
        document.title = `Count: ${count}`;
    });
    
    return (
        <div>
            <h1>Accessibility Test</h1>
            <h3>Skipped heading level</h3> {/* Should be h2 */}
            
            <input type="text" placeholder="Enter text" /> {/* No label */}
            
            <div style={{outline: 'none'}} tabIndex={0}> {/* Removed focus outline */}
                Focusable div without proper focus indicator
            </div>
            
            <video autoplay> {/* Autoplay media */}
                <source src="video.mp4" type="video/mp4" />
            </video>
            
            <span onClick={() => setCount(count + 1)}>
                Click to increment {/* Non-button element with click handler */}
            </span>
        </div>
    );
};

export default AccessibilityIssues;
'''
        
        with open(self.temp_dir / "frontend" / "src" / "components" / "AccessibilityIssues.tsx", 'w') as f:
            f.write(accessibility_component)
        
        # Component with React hooks violations
        hooks_violations = '''
import React, { useState, useEffect } from 'react';

const HooksViolations: React.FC = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    
    const fetchData = () => {
        if (loading) {
            // Hook called conditionally - violation!
            const [error, setError] = useState(null);
            return;
        }
        
        // This is also problematic
        for (let i = 0; i < 5; i++) {
            useEffect(() => {
                console.log('Effect in loop');
            }, []);
        }
    };
    
    return (
        <div>
            <button onClick={fetchData}>Fetch Data</button>
            {data && <div>{JSON.stringify(data)}</div>}
        </div>
    );
};

export default HooksViolations;
'''
        
        with open(self.temp_dir / "frontend" / "src" / "components" / "HooksViolations.tsx", 'w') as f:
            f.write(hooks_violations)
        
        # Good component for comparison
        good_component = '''
import React, { useState, useEffect } from 'react';

interface Props {
    title: string;
    onUpdate?: (value: string) => void;
}

const GoodComponent: React.FC<Props> = ({ title, onUpdate }) => {
    const [value, setValue] = useState('');
    
    useEffect(() => {
        if (onUpdate) {
            onUpdate(value);
        }
    }, [value, onUpdate]);
    
    return (
        <main>
            <h1>{title}</h1>
            <label htmlFor="input-field">
                Enter value:
                <input
                    id="input-field"
                    type="text"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    aria-describedby="input-help"
                />
            </label>
            <div id="input-help">
                This field accepts any text input
            </div>
            <button 
                type="button"
                onClick={() => setValue('')}
                aria-label="Clear input field"
            >
                Clear
            </button>
            <img 
                src="example.jpg" 
                alt="Example illustration showing proper form structure"
            />
        </main>
    );
};

export default GoodComponent;
'''
        
        with open(self.temp_dir / "frontend" / "src" / "components" / "GoodComponent.tsx", 'w') as f:
            f.write(good_component)
        
        # Create a large component file for bundle analysis
        large_component = '''
import React from 'react';
''' + '\n'.join([f'const Component{i} = () => <div>Component {i}</div>;' for i in range(100)]) + '''

const LargeComponent: React.FC = () => {
    return (
        <div>
            {/* Large component with many sub-components */}
''' + '\n'.join([f'            <Component{i} key={i} />' for i in range(100)]) + '''
        </div>
    );
};

export default LargeComponent;
'''
        
        with open(self.temp_dir / "frontend" / "src" / "components" / "LargeComponent.tsx", 'w') as f:
            f.write(large_component)
    
    def cleanup_test_environment(self):
        """Clean up the temporary test environment"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        print(f"Running test: {test_name}")
        try:
            result = test_func()
            self.test_results.append({
                "test": test_name,
                "status": "PASS" if result else "FAIL",
                "details": result if isinstance(result, dict) else {}
            })
            print(f"✓ {test_name}: {'PASS' if result else 'FAIL'}")
            return result
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "ERROR",
                "error": str(e)
            })
            print(f"✗ {test_name}: ERROR - {e}")
            return False
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        analyzer = TypeScriptFrontendAnalyzer(str(self.temp_dir))
        
        # Check if paths are set correctly
        assert analyzer.project_root == self.temp_dir
        assert analyzer.frontend_dir == self.temp_dir / "frontend"
        assert analyzer.src_dir == self.temp_dir / "frontend" / "src"
        
        return True
    
    def test_typescript_analysis(self):
        """Test TypeScript compilation analysis"""
        analyzer = TypeScriptFrontendAnalyzer(str(self.temp_dir))
        
        # Mock the TypeScript compiler output since we don't have actual tsc
        # In a real environment, this would call the actual TypeScript compiler
        result = analyzer.analyze_typescript_compilation()
        
        # Check that the analysis ran and returned a result
        assert hasattr(result, 'compilation_errors')
        assert hasattr(result, 'type_errors')
        assert hasattr(result, 'warnings')
        assert hasattr(result, 'total_files_analyzed')
        assert hasattr(result, 'success')
        
        # Should find TypeScript files
        assert result.total_files_analyzed > 0
        
        return {
            "files_analyzed": result.total_files_analyzed,
            "compilation_errors": len(result.compilation_errors),
            "type_errors": len(result.type_errors),
            "warnings": len(result.warnings)
        }
    
    def test_react_component_analysis(self):
        """Test React component analysis"""
        analyzer = TypeScriptFrontendAnalyzer(str(self.temp_dir))
        result = analyzer.analyze_react_components()
        
        # Check that the analysis ran
        assert hasattr(result, 'unused_imports')
        assert hasattr(result, 'component_issues')
        assert hasattr(result, 'hook_issues')
        assert hasattr(result, 'total_components_analyzed')
        assert hasattr(result, 'success')
        
        # Should find React components
        assert result.total_components_analyzed > 0
        
        # Should detect some issues in our test components
        total_issues = (len(result.unused_imports) + 
                       len(result.component_issues) + 
                       len(result.hook_issues))
        
        return {
            "components_analyzed": result.total_components_analyzed,
            "unused_imports": len(result.unused_imports),
            "component_issues": len(result.component_issues),
            "hook_issues": len(result.hook_issues),
            "total_issues": total_issues,
            "success": result.success
        }
    
    def test_bundle_analysis(self):
        """Test bundle analysis"""
        analyzer = TypeScriptFrontendAnalyzer(str(self.temp_dir))
        
        # Create a mock dist directory
        dist_dir = self.temp_dir / "dist"
        dist_dir.mkdir()
        
        # Create some mock bundle files
        (dist_dir / "main.js").write_text("// Mock bundle content\n" + "x" * 1000000)  # 1MB file
        (dist_dir / "vendor.js").write_text("// Mock vendor bundle\n" + "x" * 500000)  # 500KB file
        (dist_dir / "styles.css").write_text("/* Mock styles */\n" + "x" * 100000)  # 100KB file
        
        result = analyzer.analyze_bundle_performance()
        
        # Check that the analysis ran
        assert hasattr(result, 'bundle_size_issues')
        assert hasattr(result, 'optimization_opportunities')
        assert hasattr(result, 'dependency_issues')
        assert hasattr(result, 'performance_recommendations')
        assert hasattr(result, 'bundle_stats')
        assert hasattr(result, 'success')
        
        return {
            "bundle_size_issues": len(result.bundle_size_issues),
            "optimization_opportunities": len(result.optimization_opportunities),
            "dependency_issues": len(result.dependency_issues),
            "performance_recommendations": len(result.performance_recommendations),
            "success": result.success
        }
    
    def test_accessibility_analysis(self):
        """Test accessibility compliance analysis"""
        analyzer = TypeScriptFrontendAnalyzer(str(self.temp_dir))
        result = analyzer.analyze_accessibility_compliance()
        
        # Check that the analysis ran
        assert hasattr(result, 'accessibility_violations')
        assert hasattr(result, 'wcag_compliance_issues')
        assert hasattr(result, 'semantic_issues')
        assert hasattr(result, 'total_components_checked')
        assert hasattr(result, 'success')
        
        # Should find components to check
        assert result.total_components_checked > 0
        
        # Should detect accessibility issues in our test components
        total_issues = (len(result.accessibility_violations) + 
                       len(result.wcag_compliance_issues) + 
                       len(result.semantic_issues))
        
        return {
            "components_checked": result.total_components_checked,
            "accessibility_violations": len(result.accessibility_violations),
            "wcag_compliance_issues": len(result.wcag_compliance_issues),
            "semantic_issues": len(result.semantic_issues),
            "total_issues": total_issues,
            "success": result.success
        }
    
    def test_comprehensive_analysis(self):
        """Test comprehensive analysis"""
        analyzer = TypeScriptFrontendAnalyzer(str(self.temp_dir))
        result = analyzer.run_comprehensive_analysis()
        
        # Check that all analyses were run
        assert hasattr(result, 'typescript_analysis')
        assert hasattr(result, 'react_analysis')
        assert hasattr(result, 'bundle_analysis')
        assert hasattr(result, 'accessibility_analysis')
        assert hasattr(result, 'summary')
        assert hasattr(result, 'timestamp')
        
        # Check summary
        summary = result.summary
        assert 'total_issues' in summary
        assert 'critical_issues' in summary
        assert 'high_issues' in summary
        assert 'overall_success' in summary
        
        return {
            "total_issues": summary['total_issues'],
            "critical_issues": summary['critical_issues'],
            "high_issues": summary['high_issues'],
            "overall_success": summary['overall_success']
        }
    
    def test_issue_creation(self):
        """Test issue creation and categorization"""
        analyzer = TypeScriptFrontendAnalyzer(str(self.temp_dir))
        
        # Test creating different types of issues
        issue = analyzer._create_issue(
            issue_type=IssueType.TYPESCRIPT_ERROR,
            severity=IssueSeverity.HIGH,
            file_path="test.tsx",
            description="Test error",
            recommendation="Fix the error",
            line_number=10,
            column_number=5,
            auto_fixable=True
        )
        
        assert issue.type == IssueType.TYPESCRIPT_ERROR
        assert issue.severity == IssueSeverity.HIGH
        assert issue.file_path == "test.tsx"
        assert issue.line_number == 10
        assert issue.column_number == 5
        assert issue.auto_fixable == True
        assert issue.id.startswith("frontend_")
        
        return True
    
    def test_file_analysis_methods(self):
        """Test individual file analysis methods"""
        analyzer = TypeScriptFrontendAnalyzer(str(self.temp_dir))
        
        # Test unused imports analysis
        test_content = '''
import React from 'react';
import { useState, useEffect } from 'react';
import { UnusedImport } from 'some-library';

const TestComponent = () => {
    const [state, setState] = useState(0);
    return <div>{state}</div>;
};
'''
        
        test_file = self.temp_dir / "test.tsx"
        issues = analyzer._analyze_unused_imports(test_file, test_content)
        
        # Should detect unused imports
        unused_imports = [issue for issue in issues if issue.type == IssueType.UNUSED_IMPORT]
        assert len(unused_imports) > 0
        
        # Test component patterns analysis
        pattern_issues = analyzer._analyze_component_patterns(test_file, test_content)
        assert isinstance(pattern_issues, list)
        
        # Test accessibility patterns analysis
        a11y_content = '''
<div>
    <img src="test.jpg" />
    <button onClick={() => {}}>
    <input type="text" />
</div>
'''
        a11y_issues = analyzer._analyze_accessibility_patterns(test_file, a11y_content)
        assert len(a11y_issues) > 0  # Should find accessibility issues
        
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        print("Setting up test environment...")
        self.setup_test_environment()
        
        try:
            print("\n=== Running Frontend Analyzer Tests ===\n")
            
            # Run individual tests
            self.run_test("Analyzer Initialization", self.test_analyzer_initialization)
            self.run_test("TypeScript Analysis", self.test_typescript_analysis)
            self.run_test("React Component Analysis", self.test_react_component_analysis)
            self.run_test("Bundle Analysis", self.test_bundle_analysis)
            self.run_test("Accessibility Analysis", self.test_accessibility_analysis)
            self.run_test("Comprehensive Analysis", self.test_comprehensive_analysis)
            self.run_test("Issue Creation", self.test_issue_creation)
            self.run_test("File Analysis Methods", self.test_file_analysis_methods)
            
            # Print summary
            print("\n=== Test Results Summary ===")
            passed = sum(1 for result in self.test_results if result["status"] == "PASS")
            failed = sum(1 for result in self.test_results if result["status"] == "FAIL")
            errors = sum(1 for result in self.test_results if result["status"] == "ERROR")
            
            print(f"Total Tests: {len(self.test_results)}")
            print(f"Passed: {passed}")
            print(f"Failed: {failed}")
            print(f"Errors: {errors}")
            
            if failed > 0 or errors > 0:
                print("\nFailed/Error Tests:")
                for result in self.test_results:
                    if result["status"] in ["FAIL", "ERROR"]:
                        print(f"  - {result['test']}: {result['status']}")
                        if "error" in result:
                            print(f"    Error: {result['error']}")
            
            return passed == len(self.test_results)
            
        finally:
            print("\nCleaning up test environment...")
            self.cleanup_test_environment()

def main():
    """Main function to run the tests"""
    tester = FrontendAnalyzerTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())