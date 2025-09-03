#!/usr/bin/env python3
"""
Script Consolidation Tool for AI Scholar
Organizes and consolidates the scattered analysis scripts into a unified structure.
"""

import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse

class ScriptConsolidator:
    """Handles consolidation of scattered scripts into organized structure"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.scripts_dir = self.project_root / "scripts"
        self.tools_dir = self.project_root / "tools"
        
        # Mapping of script patterns to new locations
        self.consolidation_map = {
            # Analysis tools
            "analysis": {
                "patterns": ["analyzer", "analysis", "scan", "security", "performance", "quality"],
                "target_dir": "tools/analysis",
                "unified_script": "unified_analyzer.py"
            },
            
            # Testing tools
            "testing": {
                "patterns": ["test", "verify", "validate"],
                "target_dir": "tools/testing", 
                "unified_script": "test_consolidator.py"
            },
            
            # Deployment tools
            "deployment": {
                "patterns": ["deploy", "docker", "ubuntu"],
                "target_dir": "tools/deployment",
                "unified_script": "deployment_manager.py"
            },
            
            # Maintenance tools
            "maintenance": {
                "patterns": ["fix", "update", "clean", "format", "maintenance"],
                "target_dir": "tools/maintenance",
                "unified_script": "maintenance_manager.py"
            },
            
            # Monitoring tools
            "monitoring": {
                "patterns": ["monitor", "dashboard", "alert", "metric"],
                "target_dir": "tools/monitoring",
                "unified_script": "monitoring_manager.py"
            }
        }
        
        # Scripts to deprecate (demos, basic versions, etc.)
        self.deprecated_patterns = [
            "demo_", "simple_", "basic_", "standalone_", "temp_", "old_"
        ]
    
    def analyze_scripts(self) -> Dict:
        """Analyze existing scripts and categorize them"""
        if not self.scripts_dir.exists():
            return {"error": "Scripts directory not found"}
        
        script_files = list(self.scripts_dir.glob("*.py"))
        
        analysis = {
            "total_scripts": len(script_files),
            "categories": {},
            "deprecated": [],
            "duplicates": [],
            "consolidation_opportunities": {}
        }
        
        # Categorize scripts
        for category, config in self.consolidation_map.items():
            analysis["categories"][category] = []
        
        for script in script_files:
            category = self._categorize_script(script)
            
            if category == "deprecated":
                analysis["deprecated"].append(str(script))
            else:
                analysis["categories"][category].append(str(script))
        
        # Find duplicates and consolidation opportunities
        analysis["duplicates"] = self._find_duplicate_scripts(script_files)
        analysis["consolidation_opportunities"] = self._find_consolidation_opportunities()
        
        return analysis
    
    def _categorize_script(self, script_path: Path) -> str:
        """Categorize a script based on its name and content"""
        name = script_path.name.lower()
        
        # Check for deprecated patterns first
        if any(pattern in name for pattern in self.deprecated_patterns):
            return "deprecated"
        
        # Categorize by patterns
        for category, config in self.consolidation_map.items():
            if any(pattern in name for pattern in config["patterns"]):
                return category
        
        return "maintenance"  # Default category
    
    def _find_duplicate_scripts(self, script_files: List[Path]) -> List[Dict]:
        """Find potentially duplicate scripts"""
        duplicates = []
        
        # Group by similar names
        name_groups = {}
        for script in script_files:
            # Remove common prefixes/suffixes to find similar names
            base_name = script.stem
            for prefix in ["test_", "run_", "demo_", "simple_"]:
                if base_name.startswith(prefix):
                    base_name = base_name[len(prefix):]
            
            for suffix in ["_test", "_demo", "_simple", "_basic"]:
                if base_name.endswith(suffix):
                    base_name = base_name[:-len(suffix)]
            
            if base_name not in name_groups:
                name_groups[base_name] = []
            name_groups[base_name].append(script)
        
        # Find groups with multiple scripts
        for base_name, scripts in name_groups.items():
            if len(scripts) > 1:
                duplicates.append({
                    "base_name": base_name,
                    "scripts": [str(s) for s in scripts],
                    "count": len(scripts)
                })
        
        return duplicates
    
    def _find_consolidation_opportunities(self) -> Dict:
        """Find opportunities for script consolidation"""
        opportunities = {}
        
        for category, config in self.consolidation_map.items():
            target_dir = Path(config["target_dir"])
            unified_script = target_dir / config["unified_script"]
            
            opportunities[category] = {
                "target_directory": str(target_dir),
                "unified_script": str(unified_script),
                "exists": unified_script.exists(),
                "recommendation": f"Consolidate {category} scripts into {config['unified_script']}"
            }
        
        return opportunities
    
    def consolidate_scripts(self, dry_run: bool = False) -> Dict:
        """Consolidate scripts into organized structure"""
        results = {
            "migrated": [],
            "deprecated": [],
            "errors": [],
            "summary": {}
        }
        
        if not self.scripts_dir.exists():
            results["errors"].append("Scripts directory not found")
            return results
        
        script_files = list(self.scripts_dir.glob("*.py"))
        
        # Create target directories
        for category, config in self.consolidation_map.items():
            target_dir = self.project_root / config["target_dir"]
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)
                # Create __init__.py if it doesn't exist
                init_file = target_dir / "__init__.py"
                if not init_file.exists():
                    init_file.write_text(f'"""AI Scholar {category.title()} Tools"""')
        
        # Process each script
        for script in script_files:
            try:
                category = self._categorize_script(script)
                
                if category == "deprecated":
                    # Move to deprecated folder or mark for deletion
                    deprecated_dir = self.tools_dir / "deprecated"
                    if not dry_run:
                        deprecated_dir.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(script), str(deprecated_dir / script.name))
                    
                    results["deprecated"].append({
                        "script": str(script),
                        "action": "moved_to_deprecated"
                    })
                
                else:
                    # Move to appropriate category
                    target_dir = self.project_root / self.consolidation_map[category]["target_dir"]
                    new_path = target_dir / script.name
                    
                    if not dry_run:
                        if new_path.exists():
                            # Handle naming conflict
                            counter = 1
                            while new_path.exists():
                                stem = script.stem
                                suffix = script.suffix
                                new_name = f"{stem}_{counter}{suffix}"
                                new_path = target_dir / new_name
                                counter += 1
                        
                        shutil.move(str(script), str(new_path))
                        self._update_imports(new_path)
                    
                    results["migrated"].append({
                        "script": str(script),
                        "new_location": str(new_path),
                        "category": category
                    })
            
            except Exception as e:
                results["errors"].append({
                    "script": str(script),
                    "error": str(e)
                })
        
        # Generate summary
        results["summary"] = {
            "total_processed": len(script_files),
            "migrated": len(results["migrated"]),
            "deprecated": len(results["deprecated"]),
            "errors": len(results["errors"])
        }
        
        return results
    
    def _update_imports(self, file_path: Path):
        """Update import statements in migrated files"""
        try:
            content = file_path.read_text()
            
            # Update relative imports from scripts to tools
            updated_content = content.replace(
                "from scripts.", "from tools."
            ).replace(
                "import scripts.", "import tools."
            )
            
            # Update sys.path modifications
            updated_content = updated_content.replace(
                'sys.path.append("scripts")',
                'sys.path.append("tools")'
            )
            
            if content != updated_content:
                file_path.write_text(updated_content)
        
        except Exception as e:
            print(f"Warning: Could not update imports in {file_path}: {e}")
    
    def create_unified_scripts(self) -> Dict:
        """Create unified scripts for each category"""
        created_scripts = {}
        
        for category, config in self.consolidation_map.items():
            target_dir = self.project_root / config["target_dir"]
            unified_script = target_dir / config["unified_script"]
            
            if not unified_script.exists():
                template = self._get_unified_script_template(category)
                
                target_dir.mkdir(parents=True, exist_ok=True)
                unified_script.write_text(template)
                unified_script.chmod(0o755)  # Make executable
                
                created_scripts[category] = str(unified_script)
        
        return created_scripts
    
    def _get_unified_script_template(self, category: str) -> str:
        """Get template for unified script"""
        templates = {
            "deployment": '''#!/usr/bin/env python3
"""
Unified Deployment Manager for AI Scholar
Consolidates Docker, Ubuntu, and deployment-related scripts.
"""

import argparse
import subprocess
from pathlib import Path
from typing import Dict, List

class DeploymentManager:
    """Unified deployment management"""
    
    def __init__(self):
        self.project_root = Path.cwd()
    
    def validate_docker_setup(self) -> Dict:
        """Validate Docker configuration"""
        return {"status": "Docker validation not implemented"}
    
    def check_ubuntu_compatibility(self) -> Dict:
        """Check Ubuntu compatibility"""
        return {"status": "Ubuntu compatibility check not implemented"}
    
    def deploy_application(self, environment: str = "development") -> Dict:
        """Deploy application to specified environment"""
        return {"status": f"Deployment to {environment} not implemented"}

def main():
    parser = argparse.ArgumentParser(description="AI Scholar Deployment Manager")
    parser.add_argument("--action", choices=["validate", "deploy", "check"], 
                       default="validate", help="Action to perform")
    parser.add_argument("--environment", default="development", 
                       help="Deployment environment")
    
    args = parser.parse_args()
    
    manager = DeploymentManager()
    
    if args.action == "validate":
        result = manager.validate_docker_setup()
    elif args.action == "check":
        result = manager.check_ubuntu_compatibility()
    elif args.action == "deploy":
        result = manager.deploy_application(args.environment)
    
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
''',
            
            "maintenance": '''#!/usr/bin/env python3
"""
Unified Maintenance Manager for AI Scholar
Consolidates maintenance, fixing, and update scripts.
"""

import argparse
import subprocess
from pathlib import Path
from typing import Dict, List

class MaintenanceManager:
    """Unified maintenance operations"""
    
    def __init__(self):
        self.project_root = Path.cwd()
    
    def run_code_formatting(self) -> Dict:
        """Run code formatting across the project"""
        return {"status": "Code formatting not implemented"}
    
    def update_dependencies(self) -> Dict:
        """Update project dependencies"""
        return {"status": "Dependency update not implemented"}
    
    def cleanup_project(self) -> Dict:
        """Clean up temporary files and caches"""
        return {"status": "Project cleanup not implemented"}
    
    def run_quality_fixes(self) -> Dict:
        """Run automated quality fixes"""
        return {"status": "Quality fixes not implemented"}

def main():
    parser = argparse.ArgumentParser(description="AI Scholar Maintenance Manager")
    parser.add_argument("--action", 
                       choices=["format", "update", "cleanup", "quality"], 
                       default="format", help="Maintenance action to perform")
    
    args = parser.parse_args()
    
    manager = MaintenanceManager()
    
    if args.action == "format":
        result = manager.run_code_formatting()
    elif args.action == "update":
        result = manager.update_dependencies()
    elif args.action == "cleanup":
        result = manager.cleanup_project()
    elif args.action == "quality":
        result = manager.run_quality_fixes()
    
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
''',
            
            "monitoring": '''#!/usr/bin/env python3
"""
Unified Monitoring Manager for AI Scholar
Consolidates monitoring, dashboard, and alerting scripts.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List

class MonitoringManager:
    """Unified monitoring operations"""
    
    def __init__(self):
        self.project_root = Path.cwd()
    
    def generate_dashboard(self) -> Dict:
        """Generate monitoring dashboard"""
        return {"status": "Dashboard generation not implemented"}
    
    def check_system_health(self) -> Dict:
        """Check system health metrics"""
        return {"status": "Health check not implemented"}
    
    def setup_alerts(self) -> Dict:
        """Set up monitoring alerts"""
        return {"status": "Alert setup not implemented"}
    
    def collect_metrics(self) -> Dict:
        """Collect system metrics"""
        return {"status": "Metrics collection not implemented"}

def main():
    parser = argparse.ArgumentParser(description="AI Scholar Monitoring Manager")
    parser.add_argument("--action", 
                       choices=["dashboard", "health", "alerts", "metrics"], 
                       default="health", help="Monitoring action to perform")
    
    args = parser.parse_args()
    
    manager = MonitoringManager()
    
    if args.action == "dashboard":
        result = manager.generate_dashboard()
    elif args.action == "health":
        result = manager.check_system_health()
    elif args.action == "alerts":
        result = manager.setup_alerts()
    elif args.action == "metrics":
        result = manager.collect_metrics()
    
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
'''
        }
        
        return templates.get(category, f'''#!/usr/bin/env python3
"""
Unified {category.title()} Manager for AI Scholar
"""

def main():
    print(f"{category.title()} manager - implementation needed")

if __name__ == "__main__":
    main()
''')
    
    def generate_consolidation_report(self) -> str:
        """Generate comprehensive consolidation report"""
        analysis = self.analyze_scripts()
        
        report = "# Script Consolidation Report\n\n"
        report += f"**Generated:** {Path.cwd()}\n"
        report += f"**Total Scripts:** {analysis['total_scripts']}\n\n"
        
        # Summary by category
        report += "## Scripts by Category\n"
        for category, scripts in analysis["categories"].items():
            report += f"- **{category.title()}:** {len(scripts)} scripts\n"
        
        report += f"- **Deprecated:** {len(analysis['deprecated'])} scripts\n\n"
        
        # Duplicates
        if analysis["duplicates"]:
            report += "## Duplicate Scripts\n"
            for duplicate in analysis["duplicates"]:
                report += f"### {duplicate['base_name']} ({duplicate['count']} versions)\n"
                for script in duplicate["scripts"]:
                    report += f"- `{script}`\n"
                report += "\n"
        
        # Consolidation opportunities
        report += "## Consolidation Opportunities\n"
        for category, opportunity in analysis["consolidation_opportunities"].items():
            status = "✅ Exists" if opportunity["exists"] else "❌ Missing"
            report += f"- **{category.title()}:** {status} - {opportunity['recommendation']}\n"
        
        report += "\n## Recommended Actions\n"
        report += "1. Run script consolidation: `python tools/maintenance/script_consolidator.py --consolidate`\n"
        report += "2. Review and test consolidated scripts\n"
        report += "3. Update documentation and references\n"
        report += "4. Remove deprecated scripts after verification\n"
        
        return report

def main():
    parser = argparse.ArgumentParser(description="AI Scholar Script Consolidator")
    parser.add_argument("--analyze", action="store_true", 
                       help="Analyze scripts without making changes")
    parser.add_argument("--consolidate", action="store_true",
                       help="Consolidate scripts into organized structure")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without making changes")
    parser.add_argument("--create-unified", action="store_true",
                       help="Create unified scripts for each category")
    
    args = parser.parse_args()
    
    consolidator = ScriptConsolidator()
    
    if args.analyze or not any([args.consolidate, args.create_unified]):
        # Default action: analyze
        analysis = consolidator.analyze_scripts()
        report = consolidator.generate_consolidation_report()
        
        # Save report
        report_file = Path("script_consolidation_report.md")
        report_file.write_text(report)
        
        print("📊 Script Analysis Complete!")
        print(f"Total scripts: {analysis['total_scripts']}")
        print(f"Deprecated scripts: {len(analysis['deprecated'])}")
        print(f"Duplicate groups: {len(analysis['duplicates'])}")
        print(f"📋 Report saved to: {report_file}")
    
    if args.create_unified:
        created = consolidator.create_unified_scripts()
        print(f"✅ Created {len(created)} unified scripts:")
        for category, script_path in created.items():
            print(f"  - {category}: {script_path}")
    
    if args.consolidate:
        results = consolidator.consolidate_scripts(dry_run=args.dry_run)
        
        action = "Would consolidate" if args.dry_run else "Consolidated"
        print(f"📦 {action} Scripts:")
        print(f"  Migrated: {results['summary']['migrated']}")
        print(f"  Deprecated: {results['summary']['deprecated']}")
        print(f"  Errors: {results['summary']['errors']}")
        
        if results["errors"]:
            print("\n❌ Errors:")
            for error in results["errors"]:
                print(f"  - {error}")

if __name__ == "__main__":
    main()