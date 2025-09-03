#!/usr/bin/env python3
"""
Automated Fix System Demo
Demonstrates the capabilities of the automated fix application system.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automated_fix_engine import AutoFixEngine, FixType
from automated_fix_integration import AutomatedFixIntegration

def create_demo_project():
    """Create a demo project with various issues to fix"""
    demo_dir = Path(tempfile.mkdtemp(prefix="automated_fix_demo_"))
    
    print(f"Creating demo project at: {demo_dir}")
    
    # Create directory structure
    (demo_dir / "backend").mkdir()
    (demo_dir / "frontend" / "src").mkdir(parents=True)
    (demo_dir / "scripts").mkdir()
    (demo_dir / "config").mkdir()
    
    # Create Python files with formatting issues
    python_code = '''import os,sys
import json
def hello_world( ):
    print("Hello World")
    x=1+2
    y = 3 + 4
    return x,y

class MyClass:
    def __init__(self,name):
        self.name=name
    def get_name(self):
        return self.name
'''
    
    (demo_dir / "backend" / "main.py").write_text(python_code)
    
    # Create TypeScript files with formatting issues
    typescript_code = '''import React from 'react';
import {useState,useEffect} from 'react';

const MyComponent=()=>{
const[count,setCount]=useState(0);
useEffect(()=>{
console.log('Component mounted');
},[]);

return(
<div>
<h1>Count: {count}</h1>
<button onClick={()=>setCount(count+1)}>Increment</button>
</div>
);
};

export default MyComponent;
'''
    
    (demo_dir / "frontend" / "src" / "MyComponent.tsx").write_text(typescript_code)
    
    # Create package.json with outdated dependencies
    package_json = {
        "name": "demo-project",
        "version": "1.0.0",
        "dependencies": {
            "react": "^17.0.0",
            "typescript": "^4.0.0"
        },
        "devDependencies": {
            "vite": "^4.0.0",
            "@types/node": "^18.0.0"
        }
    }
    
    with open(demo_dir / "package.json", 'w') as f:
        json.dump(package_json, f, indent=2)
    
    # Create requirements.txt with outdated dependencies
    requirements = '''fastapi==0.100.0
uvicorn==0.20.0
pydantic==1.10.0
requests==2.28.0
'''
    
    (demo_dir / "backend" / "requirements.txt").write_text(requirements)
    
    # Create Docker Compose with issues
    docker_compose = '''version: '3.8'
services:
  backend:
    image: python:3.11-slim
    volumes:
      - .:/app
    ports:
      - "8000:8000"
  frontend:
    image: node:20-alpine
    volumes:
      - .:/app
    ports:
      - "3000:3000"
  database:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_PASSWORD: password
'''
    
    (demo_dir / "docker-compose.yml").write_text(docker_compose)
    
    # Create Dockerfile with issues
    dockerfile = '''FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN apt-get update
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
'''
    
    (demo_dir / "Dockerfile").write_text(dockerfile)
    
    # Create shell script with issues
    shell_script = '''#!/bin/sh
apt-get update && apt-get install -y docker
docker-compose up -d
echo "Deployment complete"
'''
    
    (demo_dir / "deploy.sh").write_text(shell_script)
    
    # Create malformed JSON config
    malformed_json = '{"name":"demo","version":"1.0.0","config":{"debug":true,"port":8000}}'
    (demo_dir / "config" / "app.json").write_text(malformed_json)
    
    return demo_dir

def demonstrate_code_formatting(demo_dir: Path):
    """Demonstrate code formatting fixes"""
    print("\n" + "="*60)
    print("DEMONSTRATING CODE FORMATTING FIXES")
    print("="*60)
    
    fix_engine = AutoFixEngine(str(demo_dir))
    
    # Show original files
    print("\nOriginal Python file (backend/main.py):")
    print("-" * 40)
    print((demo_dir / "backend" / "main.py").read_text()[:200] + "...")
    
    print("\nOriginal TypeScript file (frontend/src/MyComponent.tsx):")
    print("-" * 40)
    print((demo_dir / "frontend" / "src" / "MyComponent.tsx").read_text()[:200] + "...")
    
    # Apply formatting fixes
    print("\nApplying code formatting fixes...")
    results = fix_engine.apply_code_formatting_fixes()
    
    for result in results:
        if result.success:
            print(f"✓ Fixed {result.file_path}: {', '.join(result.changes_made)}")
        else:
            print(f"✗ Failed to fix {result.file_path}: {result.error_message}")
    
    return results

def demonstrate_dependency_updates(demo_dir: Path):
    """Demonstrate dependency update fixes"""
    print("\n" + "="*60)
    print("DEMONSTRATING DEPENDENCY UPDATE FIXES")
    print("="*60)
    
    fix_engine = AutoFixEngine(str(demo_dir))
    
    # Show original dependencies
    print("\nOriginal Python requirements (backend/requirements.txt):")
    print("-" * 40)
    print((demo_dir / "backend" / "requirements.txt").read_text())
    
    print("\nOriginal Node.js dependencies (package.json):")
    print("-" * 40)
    with open(demo_dir / "package.json", 'r') as f:
        package_data = json.load(f)
    print(f"React: {package_data['dependencies']['react']}")
    print(f"TypeScript: {package_data['dependencies']['typescript']}")
    print(f"Vite: {package_data['devDependencies']['vite']}")
    
    # Apply dependency updates
    print("\nApplying dependency updates...")
    results = fix_engine.apply_dependency_updates()
    
    for result in results:
        if result.success:
            print(f"✓ Updated {result.file_path}: {', '.join(result.changes_made)}")
        else:
            print(f"✗ Failed to update {result.file_path}: {result.error_message}")
    
    # Show updated dependencies
    if results:
        print("\nUpdated Python requirements:")
        print("-" * 40)
        print((demo_dir / "backend" / "requirements.txt").read_text())
        
        print("\nUpdated Node.js dependencies:")
        print("-" * 40)
        with open(demo_dir / "package.json", 'r') as f:
            updated_package_data = json.load(f)
        print(f"React: {updated_package_data['dependencies']['react']}")
        print(f"TypeScript: {updated_package_data['dependencies']['typescript']}")
        print(f"Vite: {updated_package_data['devDependencies']['vite']}")
    
    return results

def demonstrate_configuration_fixes(demo_dir: Path):
    """Demonstrate configuration file fixes"""
    print("\n" + "="*60)
    print("DEMONSTRATING CONFIGURATION FIXES")
    print("="*60)
    
    fix_engine = AutoFixEngine(str(demo_dir))
    
    # Show original configurations
    print("\nOriginal Docker Compose (docker-compose.yml):")
    print("-" * 40)
    print((demo_dir / "docker-compose.yml").read_text()[:300] + "...")
    
    print("\nOriginal Dockerfile:")
    print("-" * 40)
    print((demo_dir / "Dockerfile").read_text())
    
    print("\nOriginal JSON config (config/app.json):")
    print("-" * 40)
    print((demo_dir / "config" / "app.json").read_text())
    
    # Apply configuration fixes
    print("\nApplying configuration fixes...")
    results = fix_engine.apply_configuration_fixes()
    
    for result in results:
        if result.success:
            print(f"✓ Fixed {result.file_path}: {', '.join(result.changes_made)}")
        else:
            print(f"✗ Failed to fix {result.file_path}: {result.error_message}")
    
    return results

def demonstrate_ubuntu_optimizations(demo_dir: Path):
    """Demonstrate Ubuntu-specific optimizations"""
    print("\n" + "="*60)
    print("DEMONSTRATING UBUNTU OPTIMIZATIONS")
    print("="*60)
    
    fix_engine = AutoFixEngine(str(demo_dir))
    
    # Show original shell script
    print("\nOriginal deployment script (deploy.sh):")
    print("-" * 40)
    print((demo_dir / "deploy.sh").read_text())
    
    # Apply Ubuntu optimizations
    print("\nApplying Ubuntu optimizations...")
    results = fix_engine.apply_ubuntu_optimizations()
    
    for result in results:
        if result.success:
            print(f"✓ Optimized {result.file_path}: {', '.join(result.changes_made)}")
        else:
            print(f"✗ Failed to optimize {result.file_path}: {result.error_message}")
    
    # Show optimized script
    if results:
        print("\nOptimized deployment script:")
        print("-" * 40)
        print((demo_dir / "deploy.sh").read_text())
    
    return results

def demonstrate_integrated_fixes(demo_dir: Path):
    """Demonstrate integrated analysis and fixes"""
    print("\n" + "="*60)
    print("DEMONSTRATING INTEGRATED ANALYSIS AND FIXES")
    print("="*60)
    
    # Create a fresh demo project for integrated demo
    fresh_demo_dir = create_demo_project()
    
    try:
        integration = AutomatedFixIntegration(str(fresh_demo_dir))
        
        print("\nRunning integrated analysis and fix process...")
        report = integration.analyze_and_fix()
        
        print(f"\nIntegrated Fix Results:")
        print(f"Total recommendations: {report['fix_recommendations']['total_recommendations']}")
        print(f"Auto-applicable: {report['fix_recommendations']['auto_applicable']}")
        print(f"Requiring review: {report['fix_recommendations']['requires_review']}")
        print(f"Fixes applied: {report['applied_fixes']['total_applied']}")
        print(f"Successful: {report['applied_fixes']['successful']}")
        print(f"Failed: {report['applied_fixes']['failed']}")
        
        print("\nRecommendations by risk level:")
        for risk_level, count in report['fix_recommendations']['by_risk_level'].items():
            print(f"  {risk_level}: {count}")
        
        print("\nApplied fixes by type:")
        for fix_type, count in report['applied_fixes']['by_type'].items():
            print(f"  {fix_type}: {count}")
        
        return report
    
    finally:
        # Clean up fresh demo directory
        shutil.rmtree(fresh_demo_dir)

def run_comprehensive_demo():
    """Run comprehensive demonstration of all fix capabilities"""
    print("AUTOMATED FIX SYSTEM COMPREHENSIVE DEMO")
    print("=" * 60)
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create demo project
    demo_dir = create_demo_project()
    
    try:
        all_results = []
        
        # Demonstrate each fix type
        formatting_results = demonstrate_code_formatting(demo_dir)
        all_results.extend(formatting_results)
        
        dependency_results = demonstrate_dependency_updates(demo_dir)
        all_results.extend(dependency_results)
        
        config_results = demonstrate_configuration_fixes(demo_dir)
        all_results.extend(config_results)
        
        ubuntu_results = demonstrate_ubuntu_optimizations(demo_dir)
        all_results.extend(ubuntu_results)
        
        # Demonstrate integrated fixes
        integrated_report = demonstrate_integrated_fixes(demo_dir)
        
        # Generate final summary
        print("\n" + "="*60)
        print("COMPREHENSIVE DEMO SUMMARY")
        print("="*60)
        
        successful_fixes = len([r for r in all_results if r.success])
        failed_fixes = len([r for r in all_results if not r.success])
        
        print(f"Standalone Fixes Applied: {len(all_results)}")
        print(f"  Successful: {successful_fixes}")
        print(f"  Failed: {failed_fixes}")
        
        if integrated_report:
            print(f"\nIntegrated Analysis Results:")
            print(f"  Recommendations: {integrated_report['fix_recommendations']['total_recommendations']}")
            print(f"  Applied: {integrated_report['applied_fixes']['total_applied']}")
            print(f"  Success Rate: {integrated_report['applied_fixes']['successful']}/{integrated_report['applied_fixes']['total_applied']}")
        
        # Show fix types breakdown
        fix_types = {}
        for result in all_results:
            fix_type = result.fix_type.value
            fix_types[fix_type] = fix_types.get(fix_type, 0) + 1
        
        print(f"\nFixes by Type:")
        for fix_type, count in fix_types.items():
            print(f"  {fix_type}: {count}")
        
        print(f"\nDemo project location: {demo_dir}")
        print("You can examine the fixed files to see the changes applied.")
        
        return {
            "demo_dir": str(demo_dir),
            "standalone_results": all_results,
            "integrated_report": integrated_report,
            "summary": {
                "total_fixes": len(all_results),
                "successful_fixes": successful_fixes,
                "failed_fixes": failed_fixes,
                "fix_types": fix_types
            }
        }
    
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Ask user if they want to keep the demo directory
        try:
            keep = input(f"\nKeep demo directory at {demo_dir}? (y/N): ").lower().strip()
            if keep != 'y':
                shutil.rmtree(demo_dir)
                print("Demo directory cleaned up.")
        except KeyboardInterrupt:
            print("\nDemo directory kept for inspection.")

def main():
    """Main demo function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Fix System Demo")
    parser.add_argument("--demo-type", choices=["formatting", "dependencies", "config", "ubuntu", "integrated", "all"],
                       default="all", help="Type of demo to run")
    parser.add_argument("--keep-demo-dir", action="store_true", help="Keep demo directory after completion")
    
    args = parser.parse_args()
    
    if args.demo_type == "all":
        result = run_comprehensive_demo()
    else:
        # Create demo project
        demo_dir = create_demo_project()
        
        try:
            if args.demo_type == "formatting":
                demonstrate_code_formatting(demo_dir)
            elif args.demo_type == "dependencies":
                demonstrate_dependency_updates(demo_dir)
            elif args.demo_type == "config":
                demonstrate_configuration_fixes(demo_dir)
            elif args.demo_type == "ubuntu":
                demonstrate_ubuntu_optimizations(demo_dir)
            elif args.demo_type == "integrated":
                demonstrate_integrated_fixes(demo_dir)
        
        finally:
            if not args.keep_demo_dir:
                shutil.rmtree(demo_dir)
                print(f"Demo directory cleaned up.")
            else:
                print(f"Demo directory kept at: {demo_dir}")


if __name__ == "__main__":
    main()